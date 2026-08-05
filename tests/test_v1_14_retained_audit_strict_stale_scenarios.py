from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from darwin.models import (
    RetainedAuditCompactionApplyResult,
    RetainedAuditCompactionBatchApplyResult,
    RetainedAuditCompactionBatchPreviewResult,
    RetainedAuditCompactionPreviewResult,
)
from darwin.sim.runner import run_scenario
from darwin.sim.scenarios import list_scenario_files, validate_scenario_dict

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_DIR = PROJECT_ROOT / "scenarios"
V1_14_SCENARIO_NAMES = (
    "091_retained_audit_strict_stale_batch_success.yaml",
    "092_retained_audit_strict_stale_batch_default_compatibility.yaml",
    "093_retained_audit_strict_stale_batch_isolation.yaml",
)


def test_v1_14_strict_stale_batch_scenarios_validate():
    for scenario_name in V1_14_SCENARIO_NAMES:
        validation = validate_scenario_dict(
            _load_yaml(SCENARIOS_DIR / scenario_name),
            path=scenario_name,
        )
        assert validation.valid, validation.errors


@pytest.mark.parametrize("invalid_value", [None, 0, 1, "true", [], {}])
def test_v1_14_strict_stale_action_validation_requires_a_boolean(invalid_value):
    invalid = _load_yaml(SCENARIOS_DIR / V1_14_SCENARIO_NAMES[0])
    apply_index, apply_step = next(
        (index, step)
        for index, step in enumerate(invalid["steps"])
        if step.get("action") == "apply_retained_audit_compaction_batch"
    )
    apply_step["strict_stale_abort"] = invalid_value

    validation = validate_scenario_dict(invalid)

    assert not validation.valid
    assert f"steps[{apply_index}].strict_stale_abort" in {
        error.location for error in validation.errors
    }


@pytest.mark.parametrize("invalid_value", [None, 0, 1, "false", [], {}])
def test_v1_14_strict_stale_assertion_filter_requires_a_boolean(invalid_value):
    invalid = _load_yaml(SCENARIOS_DIR / V1_14_SCENARIO_NAMES[0])
    assertion_index, assertion = next(
        (index, item)
        for index, item in enumerate(invalid["assertions"])
        if item.get("type")
        == "retained_audit_compaction_batch_apply_result_contains"
    )
    assertion["strict_stale_abort"] = invalid_value

    validation = validate_scenario_dict(invalid)

    assert not validation.valid
    assert f"assertions[{assertion_index}].strict_stale_abort" in {
        error.location for error in validation.errors
    }


def test_v1_14_strict_success_keeps_preview_point_in_time_and_correlation_only():
    result = run_scenario(SCENARIOS_DIR / V1_14_SCENARIO_NAMES[0])
    previews = _results(result, RetainedAuditCompactionBatchPreviewResult)
    applies = _results(result, RetainedAuditCompactionBatchApplyResult)

    assert result.passed
    assert len(previews) == 1
    assert len(applies) == 1
    assert not _results(result, RetainedAuditCompactionPreviewResult)
    assert not _results(result, RetainedAuditCompactionApplyResult)
    preview = previews[0]
    applied = applies[0]
    assert preview.batch_id == applied.batch_id == "retained_audit_batch_091"
    assert preview.history_types == applied.history_types == (
        "message_delivery_result",
        "authority_outcome",
    )
    assert preview.metadata["point_in_time_preview"] is True
    assert preview.metadata["batch_id_correlation_only"] is True
    assert preview.metadata["apply_parity_requires_unchanged_state"] is True
    assert preview.metadata["apply_parity_runtime_confirmed"] is False
    assert preview.metadata["registry_hub_mutated"] is False
    assert applied.metadata["strict_stale_abort"] is True
    assert applied.metadata["caller_order"] == "reverse_canonical"
    assert applied.missing_count == 0
    for preview_result, apply_result in zip(
        preview.preview_results,
        applied.apply_results,
        strict=True,
    ):
        assert (
            preview_result.would_compact_record_keys
            == apply_result.compacted_record_keys
        )
        assert preview_result.missing_record_keys == apply_result.missing_record_keys


def test_v1_14_explicit_false_preserves_legacy_partial_stale_apply():
    result = run_scenario(SCENARIOS_DIR / V1_14_SCENARIO_NAMES[1])
    batches = _results(result, RetainedAuditCompactionBatchApplyResult)
    child_actions = _results(result, RetainedAuditCompactionApplyResult)

    assert result.passed
    assert len(child_actions) == 1
    assert len(batches) == 1
    batch = batches[0]
    assert batch.metadata["strict_stale_abort"] is False
    assert batch.compacted_count == 1
    assert batch.missing_count == 1
    assert batch.apply_results[0].history_type == "message_delivery_result"
    assert batch.apply_results[0].compacted_count == 0
    assert batch.apply_results[0].missing_count == 1
    assert batch.apply_results[1].history_type == "authority_outcome"
    assert batch.apply_results[1].compacted_count == 1
    assert batch.apply_results[1].missing_count == 0


def test_v1_14_strict_isolation_preserves_unselected_state_and_snapshots():
    scenario = _load_yaml(SCENARIOS_DIR / V1_14_SCENARIO_NAMES[2])
    batch_index = next(
        index
        for index, step in enumerate(scenario["steps"])
        if step.get("action") == "apply_retained_audit_compaction_batch"
    )
    before_data = deepcopy(scenario)
    before_data["scenario_id"] = "093_before_retained_audit_strict_batch_apply"
    before_data["steps"] = before_data["steps"][:batch_index]
    before_data["assertions"] = []

    before = run_scenario(before_data)
    result = run_scenario(SCENARIOS_DIR / V1_14_SCENARIO_NAMES[2])
    before_home = before.world.registry_hubs["registry_home_093"]
    home = result.world.registry_hubs["registry_home_093"]

    assert result.passed
    assert [item.message_id for item in before_home.message_delivery_results] == [
        "message_keep_093",
        "message_compact_093",
    ]
    assert [item.message_id for item in home.message_delivery_results] == [
        "message_keep_093"
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
    batches = _results(result, RetainedAuditCompactionBatchApplyResult)
    assert len(batches) == 1
    assert batches[0].metadata["strict_stale_abort"] is True
    assert "retained_audit_compaction_batch_apply_results" not in compact_after
    assert len(
        result.world.detailed_snapshot()[
            "retained_audit_compaction_batch_apply_results"
        ]
    ) == 1


def test_v1_14_checked_in_scenarios_run_and_extend_contiguous_sweep():
    scenario_files = [
        path
        for path in list_scenario_files(SCENARIOS_DIR)
        if path.name[:3] in {"091", "092", "093"}
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
    assert [path.name[:3] for path in scenario_files] == ["091", "092", "093"]
    assert scenario_numbers == list(range(1, 94))
    assert not failures


def _load_yaml(path: Path) -> dict[str, object]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _results(result: object, result_type: type) -> list[object]:
    return [
        item
        for item in result.world.action_results
        if isinstance(item, result_type)
    ]
