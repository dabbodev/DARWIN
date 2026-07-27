from __future__ import annotations

from pathlib import Path

import yaml

from darwin.models import (
    RetainedAuditCompactionApplyResult,
    RetainedAuditCompactionDecision,
    RetainedAuditReplaySummary,
)
from darwin.sim.runner import run_scenario
from darwin.sim.scenarios import list_scenario_files, validate_scenario_dict

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_DIR = PROJECT_ROOT / "scenarios"
V1_10_SCENARIO_NAMES = (
    "079_retained_audit_message_delivery_classification.yaml",
    "080_retained_audit_message_delivery_replay.yaml",
    "081_retained_audit_message_delivery_apply.yaml",
)


def test_v1_10_history_label_scenarios_validate():
    for scenario_name in V1_10_SCENARIO_NAMES:
        validation = validate_scenario_dict(
            _load_yaml(SCENARIOS_DIR / scenario_name),
            path=scenario_name,
        )
        assert validation.valid, validation.errors


def test_v1_10_message_delivery_classification_is_read_only():
    scenario_path = SCENARIOS_DIR / V1_10_SCENARIO_NAMES[0]
    scenario = _load_yaml(scenario_path)
    before_data = dict(scenario)
    before_data["scenario_id"] = "079_before_message_delivery_classification"
    before_data["steps"] = scenario["steps"][:-1]
    before_data["assertions"] = []

    before = run_scenario(before_data)
    result = run_scenario(scenario_path)
    before_hub = before.world.registry_hubs["registry_chat_001"]
    hub = result.world.registry_hubs["registry_chat_001"]
    decisions = _results(result, RetainedAuditCompactionDecision)

    assert result.passed
    assert len(decisions) == 1
    assert decisions[0].history_type == "message_delivery_result"
    assert decisions[0].candidate_by_status == {"bounced": 1, "delivered": 1}
    assert decisions[0].metadata["scenario_record_history_types"] == [
        "message_delivery_result"
    ]
    assert _summaries(hub.message_delivery_results) == _summaries(
        before_hub.message_delivery_results
    )
    assert not _results(result, RetainedAuditCompactionApplyResult)


def test_v1_10_replay_reuses_existing_dimensions_without_inference():
    result = run_scenario(SCENARIOS_DIR / V1_10_SCENARIO_NAMES[1])
    summaries = _results(result, RetainedAuditReplaySummary)

    assert result.passed
    assert len(summaries) == 3
    all_records, retained, candidate = summaries
    assert all_records.history_type == "message_delivery_result"
    assert all_records.by_message_id == {
        "message_alpha_080": 1,
        "message_missing_080": 1,
        "message_zeta_080": 1,
    }
    assert all_records.by_mailbox_id == {"mailbox_alpha": 1, "mailbox_zeta": 1}
    assert all_records.by_lane_signature == {
        "basic_messaging:v1": 2,
        "file_transfer:v1": 1,
    }
    assert all_records.by_request_id == {}
    assert all_records.by_offer_id == {}
    assert all_records.by_policy_id == {}
    assert retained.by_status == {"delivered": 2}
    assert retained.metadata["decision_category_filter"] == "retained"
    assert candidate.by_reason == {"mailbox_not_found": 1}
    assert candidate.metadata["decision_category_filter"] == "compaction_candidate"


def test_v1_10_apply_isolates_history_from_delivery_and_encryption_state():
    scenario_path = SCENARIOS_DIR / V1_10_SCENARIO_NAMES[2]
    scenario = _load_yaml(scenario_path)
    first_apply_index = next(
        index
        for index, step in enumerate(scenario["steps"])
        if step.get("action") == "apply_retained_audit_compaction_decision"
    )
    before_data = dict(scenario)
    before_data["scenario_id"] = "081_before_message_delivery_apply"
    before_data["steps"] = scenario["steps"][:first_apply_index]
    before_data["assertions"] = []

    before = run_scenario(before_data)
    result = run_scenario(scenario_path)
    before_hub = before.world.registry_hubs["registry_chat_001"]
    hub = result.world.registry_hubs["registry_chat_001"]
    apply_results = _results(result, RetainedAuditCompactionApplyResult)

    assert result.passed
    assert len(apply_results) == 2
    applied, repeated = apply_results
    assert applied.compacted_count == 1
    assert applied.metadata["message_delivery_history_mutated"] is True
    assert applied.metadata["delivery_state_mutated"] is False
    assert repeated.compacted_count == 0
    assert repeated.missing_count == 1
    assert repeated.metadata["message_delivery_history_mutated"] is False
    assert [item.message_id for item in before_hub.message_delivery_results] == [
        "message_encrypted_081",
        "message_keep_081",
        "message_compact_081",
    ]
    assert [item.message_id for item in hub.message_delivery_results] == [
        "message_encrypted_081",
        "message_keep_081",
    ]
    assert hub.message_inboxes == before_hub.message_inboxes
    assert _summaries(hub.encrypted_delivery_result_history) == _summaries(
        before_hub.encrypted_delivery_result_history
    )
    assert _summaries(hub.encryption_policy_decision_history) == _summaries(
        before_hub.encryption_policy_decision_history
    )
    assert result.world.snapshot()["traffic_hubs"] == before.world.snapshot()[
        "traffic_hubs"
    ]


def test_v1_10_detailed_snapshot_is_copied_and_compact_shape_is_unchanged():
    result = run_scenario(SCENARIOS_DIR / V1_10_SCENARIO_NAMES[1])
    compact = result.world.snapshot()
    detailed = result.world.detailed_snapshot()
    hub_snapshot = detailed["registry_hubs"]["registry_chat_001"]

    assert "message_delivery_results" not in compact
    assert "retained_audit_replay_summaries" not in compact
    assert hub_snapshot["message_delivery_results"][0]["metadata"][
        "registry_hub"
    ] == "registry_chat_001"
    assert detailed["retained_audit_replay_summaries"][0][
        "by_message_id"
    ] == {
        "message_alpha_080": 1,
        "message_missing_080": 1,
        "message_zeta_080": 1,
    }

    hub_snapshot["message_delivery_results"][0]["metadata"]["registry_hub"] = "mutated"
    detailed["retained_audit_replay_summaries"][0]["by_message_id"][
        "message_alpha_080"
    ] = 99
    fresh = result.world.detailed_snapshot()

    assert fresh["registry_hubs"]["registry_chat_001"]["message_delivery_results"][0][
        "metadata"
    ]["registry_hub"] == "registry_chat_001"
    assert fresh["retained_audit_replay_summaries"][0]["by_message_id"][
        "message_alpha_080"
    ] == 1


def test_v1_10_checked_in_scenarios_run_and_extend_contiguous_sweep():
    scenario_files = [
        path
        for path in list_scenario_files(SCENARIOS_DIR)
        if path.name[:3] in {"079", "080", "081"}
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
    assert [path.name[:3] for path in scenario_files] == ["079", "080", "081"]
    assert scenario_numbers == list(range(1, 82))
    assert not failures


def _load_yaml(path: Path) -> dict[str, object]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _results(result: object, result_type: type) -> list[object]:
    return [
        item
        for item in result.world.action_results
        if isinstance(item, result_type)
    ]


def _summaries(values: list[object]) -> list[dict[str, object]]:
    return [value.to_summary() for value in values]
