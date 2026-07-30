from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from darwin.models import (
    RetainedAuditCompactionApplyResult,
    RetainedAuditCompactionBatchApplyResult,
)
from darwin.sim.runner import run_scenario
from darwin.sim.scenarios import list_scenario_files, validate_scenario_dict

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_DIR = PROJECT_ROOT / "scenarios"
V1_12_SCENARIO_NAMES = (
    "085_retained_audit_batch_apply_success.yaml",
    "086_retained_audit_batch_apply_stale_repeat.yaml",
    "087_retained_audit_batch_apply_isolation.yaml",
)


def test_v1_12_batch_scenarios_validate():
    for scenario_name in V1_12_SCENARIO_NAMES:
        validation = validate_scenario_dict(
            _load_yaml(SCENARIOS_DIR / scenario_name),
            path=scenario_name,
        )
        assert validation.valid, validation.errors


@pytest.mark.parametrize(
    ("field_name", "value", "expected_location"),
    [
        ("decision_policy_ids", "not-a-mapping", "steps[17].decision_policy_ids"),
        (
            "decision_policy_ids",
            {"message_delivery_result": "policy_message"},
            "steps[17].decision_policy_ids",
        ),
        (
            "decision_policy_ids",
            {
                "message_delivery_result": "policy_message",
                "unsupported_history": "policy_unsupported",
            },
            "steps[17].decision_policy_ids.unsupported_history",
        ),
        (
            "decision_policy_ids",
            [
                {"message_delivery_result": "policy_first"},
                {"message_delivery_result": "policy_duplicate"},
            ],
            "steps[17].decision_policy_ids",
        ),
        ("batch_id", "", "steps[17].batch_id"),
        (
            "decision_policy_ids",
            {
                "message_delivery_result": "",
                "authority_outcome": "policy_authority",
            },
            "steps[17].decision_policy_ids.message_delivery_result",
        ),
    ],
)
def test_v1_12_batch_step_validation_rejects_malformed_references(
    field_name,
    value,
    expected_location,
):
    invalid = _load_yaml(SCENARIOS_DIR / V1_12_SCENARIO_NAMES[0])
    batch_step = next(
        step
        for step in invalid["steps"]
        if step.get("action") == "apply_retained_audit_compaction_batch"
    )
    batch_step[field_name] = value

    validation = validate_scenario_dict(invalid)

    assert not validation.valid
    assert expected_location in {error.location for error in validation.errors}


def test_v1_12_batch_assertion_validation_rejects_invalid_counts_and_filters():
    invalid = _load_yaml(SCENARIOS_DIR / V1_12_SCENARIO_NAMES[0])
    assertion = invalid["assertions"][0]
    assertion["compacted_count"] = -1
    assertion["history_missing_count"] = -1
    assertion["policy_id"] = "policy_without_history"

    validation = validate_scenario_dict(invalid)

    assert not validation.valid
    locations = {error.location for error in validation.errors}
    assert {
        "assertions[0].compacted_count",
        "assertions[0].history_missing_count",
        "assertions[0].history_type",
    } <= locations


def test_v1_12_success_uses_canonical_aggregate_only_action_result():
    result = run_scenario(SCENARIOS_DIR / V1_12_SCENARIO_NAMES[0])
    batch_results = _results(result, RetainedAuditCompactionBatchApplyResult)
    child_results = _results(result, RetainedAuditCompactionApplyResult)

    assert result.passed
    assert len(batch_results) == 1
    assert not child_results
    batch = batch_results[0]
    assert batch.history_types == (
        "message_delivery_result",
        "authority_outcome",
    )
    assert [child.policy_id for child in batch.apply_results] == [
        "retained_audit_message_delivery_085",
        "retained_audit_authority_085",
    ]
    assert batch.metadata["caller_order"] == "reverse_canonical"
    assert batch.metadata["canonical_batch_order"] is True


def test_v1_12_stale_repeat_preserves_single_result_stream_contract():
    result = run_scenario(SCENARIOS_DIR / V1_12_SCENARIO_NAMES[1])
    batch_results = _results(result, RetainedAuditCompactionBatchApplyResult)
    child_results = _results(result, RetainedAuditCompactionApplyResult)

    assert result.passed
    assert len(child_results) == 1
    assert child_results[0].compacted_count == 1
    assert len(batch_results) == 2
    first, repeated = batch_results
    assert first.compacted_count == 1
    assert first.missing_count == 1
    assert first.apply_results[0].missing_count == 1
    assert first.apply_results[1].compacted_count == 1
    assert repeated.compacted_count == 0
    assert repeated.missing_count == 2
    assert repeated.metadata["registry_hub_mutated"] is False


def test_v1_12_isolation_preserves_unselected_registry_and_traffic_state():
    scenario = _load_yaml(SCENARIOS_DIR / V1_12_SCENARIO_NAMES[2])
    batch_index = next(
        index
        for index, step in enumerate(scenario["steps"])
        if step.get("action") == "apply_retained_audit_compaction_batch"
    )
    before_data = deepcopy(scenario)
    before_data["scenario_id"] = "087_before_retained_audit_batch_apply"
    before_data["steps"] = before_data["steps"][:batch_index]
    before_data["assertions"] = []

    before = run_scenario(before_data)
    result = run_scenario(SCENARIOS_DIR / V1_12_SCENARIO_NAMES[2])
    before_home = before.world.registry_hubs["registry_home_087"]
    home = result.world.registry_hubs["registry_home_087"]

    assert result.passed
    assert [item.message_id for item in before_home.message_delivery_results] == [
        "message_keep_087",
        "message_compact_087",
    ]
    assert [item.message_id for item in home.message_delivery_results] == [
        "message_keep_087"
    ]
    assert [item.final_status for item in before_home.authority_outcome_history] == [
        "fallback_granted",
        "name_taken",
    ]
    assert [item.final_status for item in home.authority_outcome_history] == [
        "fallback_granted"
    ]
    for field_name in (
        "aliases",
        "conflicts",
        "security_events",
        "quarantines",
        "mailboxes",
        "mailbox_address_index",
        "lane_registry",
        "message_inboxes",
        "encrypted_delivery_result_history",
        "encryption_policy_decision_history",
        "stream_offer_lifecycle_explanation_history",
        "stream_offer_status_transition_history",
        "rendezvous_poll_result_history",
        "lane_admission_decision_history",
    ):
        assert getattr(home, field_name) == getattr(before_home, field_name)
    assert result.world.devices == before.world.devices
    assert result.world.traffic_hubs == before.world.traffic_hubs
    assert result.world.lanes == before.world.lanes
    compact_before = before.world.snapshot()
    compact_after = result.world.snapshot()
    assert compact_after["time"] == compact_before["time"] + 1
    assert {key: value for key, value in compact_after.items() if key != "time"} == {
        key: value for key, value in compact_before.items() if key != "time"
    }


def test_v1_12_detailed_snapshot_adds_only_copied_batch_results():
    result = run_scenario(SCENARIOS_DIR / V1_12_SCENARIO_NAMES[0])
    compact = result.world.snapshot()
    detailed = result.world.detailed_snapshot()

    assert "retained_audit_compaction_batch_apply_results" not in compact
    assert detailed["retained_audit_compaction_apply_results"] == []
    assert len(detailed["retained_audit_compaction_batch_apply_results"]) == 1
    snapshot = detailed["retained_audit_compaction_batch_apply_results"][0]
    assert snapshot["history_types"] == [
        "message_delivery_result",
        "authority_outcome",
    ]
    snapshot["history_types"].reverse()
    snapshot["apply_results"][0]["compacted_record_keys"].append("mutated")

    fresh = result.world.detailed_snapshot()
    assert fresh["retained_audit_compaction_batch_apply_results"][0][
        "history_types"
    ] == ["message_delivery_result", "authority_outcome"]
    assert "mutated" not in fresh["retained_audit_compaction_batch_apply_results"][0][
        "apply_results"
    ][0]["compacted_record_keys"]


def test_v1_12_checked_in_scenarios_run_and_extend_contiguous_sweep():
    scenario_files = [
        path
        for path in list_scenario_files(SCENARIOS_DIR)
        if path.name[:3] in {"085", "086", "087"}
    ]

    failures = []
    for scenario_file in scenario_files:
        validation = validate_scenario_dict(
            _load_yaml(scenario_file),
            path=str(scenario_file),
        )
        if not validation.valid:
            failures.append(f"{scenario_file}: {validation.errors}")
            continue
        scenario_result = run_scenario(scenario_file)
        if not scenario_result.passed:
            failures.append(f"{scenario_file}: {scenario_result.assertion_results}")

    scenario_numbers = sorted(
        int(path.name[:3])
        for path in list_scenario_files(SCENARIOS_DIR)
        if path.name[:3].isdigit()
    )
    assert [path.name[:3] for path in scenario_files] == ["085", "086", "087"]
    assert scenario_numbers == list(range(1, 88))
    assert not failures


def _load_yaml(path: Path) -> dict[str, object]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _results(result: object, result_type: type) -> list[object]:
    return [
        item
        for item in result.world.action_results
        if isinstance(item, result_type)
    ]
