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
V1_8_SCENARIO_NAMES = (
    "073_retained_audit_encrypted_delivery_classification.yaml",
    "074_retained_audit_encrypted_delivery_replay.yaml",
    "075_retained_audit_encrypted_delivery_apply.yaml",
)


def test_v1_8_history_label_and_message_mailbox_counts_validate():
    for scenario_name in V1_8_SCENARIO_NAMES:
        validation = validate_scenario_dict(
            _load_yaml(SCENARIOS_DIR / scenario_name),
            path=scenario_name,
        )
        assert validation.valid, validation.errors

    invalid = _load_yaml(SCENARIOS_DIR / V1_8_SCENARIO_NAMES[1])
    invalid["scenario_id"] = "074_invalid_group_counts"
    invalid["assertions"][0]["message_count"] = -1
    invalid["assertions"][0]["mailbox_count"] = -1

    validation = validate_scenario_dict(invalid)

    assert not validation.valid
    assert {
        "assertions[0].message_count",
        "assertions[0].mailbox_count",
    }.issubset({error.location for error in validation.errors})


def test_v1_8_encrypted_classification_is_read_only_and_source_aware():
    scenario_path = SCENARIOS_DIR / V1_8_SCENARIO_NAMES[0]
    scenario = _load_yaml(scenario_path)
    before_data = dict(scenario)
    before_data["scenario_id"] = "073_before_encrypted_classification"
    before_data["steps"] = scenario["steps"][:-1]
    before_data["assertions"] = []

    before = run_scenario(before_data)
    result = run_scenario(scenario_path)
    before_hub = before.world.registry_hubs["registry_chat_001"]
    hub = result.world.registry_hubs["registry_chat_001"]
    decisions = _results(result, RetainedAuditCompactionDecision)

    assert result.passed
    assert len(decisions) == 1
    assert decisions[0].history_type == "encrypted_delivery_result"
    assert decisions[0].candidate_by_source == {"delivery_deferred": 1}
    assert decisions[0].metadata["scenario_record_history_types"] == [
        "encrypted_delivery_result"
    ]
    assert _summaries(hub.encrypted_delivery_result_history) == _summaries(
        before_hub.encrypted_delivery_result_history
    )
    assert not _results(result, RetainedAuditCompactionApplyResult)


def test_v1_8_replay_groups_message_mailbox_and_decision_categories():
    result = run_scenario(SCENARIOS_DIR / V1_8_SCENARIO_NAMES[1])
    summaries = _results(result, RetainedAuditReplaySummary)

    assert result.passed
    assert len(summaries) == 3
    all_records, retained, candidate = summaries
    assert all_records.history_type == "encrypted_delivery_result"
    assert all_records.by_request_id == {
        "request_alpha_074": 1,
        "request_zeta_074": 1,
    }
    assert all_records.by_message_id == {
        "message_alpha_074": 1,
        "message_zeta_074": 1,
    }
    assert all_records.by_mailbox_id == {"mailbox_neo": 2}
    assert all_records.by_source == {"alpha_source": 1, "zeta_source": 1}
    assert retained.by_message_id == {"message_zeta_074": 1}
    assert retained.metadata["decision_category_filter"] == "retained"
    assert candidate.by_message_id == {"message_alpha_074": 1}
    assert candidate.metadata["decision_category_filter"] == "compaction_candidate"


def test_v1_8_apply_isolates_audit_history_from_delivery_and_policy_state():
    scenario_path = SCENARIOS_DIR / V1_8_SCENARIO_NAMES[2]
    scenario = _load_yaml(scenario_path)
    first_apply_index = next(
        index
        for index, step in enumerate(scenario["steps"])
        if step.get("action") == "apply_retained_audit_compaction_decision"
    )
    before_data = dict(scenario)
    before_data["scenario_id"] = "075_before_encrypted_apply"
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
    assert applied.metadata["encrypted_delivery_history_mutated"] is True
    assert applied.metadata["delivery_state_mutated"] is False
    assert repeated.compacted_count == 0
    assert repeated.missing_count == 1
    assert repeated.metadata["encrypted_delivery_history_mutated"] is False
    assert [record.request_id for record in before_hub.encrypted_delivery_result_history] == [
        "request_keep_075",
        "request_compact_075",
    ]
    assert [record.request_id for record in hub.encrypted_delivery_result_history] == [
        "request_keep_075"
    ]
    assert _summaries(hub.encryption_policy_decision_history) == _summaries(
        before_hub.encryption_policy_decision_history
    )
    assert _summaries(hub.message_delivery_results) == _summaries(
        before_hub.message_delivery_results
    )
    assert hub.message_inboxes == before_hub.message_inboxes
    assert result.world.snapshot()["traffic_hubs"] == before.world.snapshot()[
        "traffic_hubs"
    ]


def test_v1_8_replay_detailed_snapshot_is_copied_and_compact_shape_is_unchanged():
    result = run_scenario(SCENARIOS_DIR / V1_8_SCENARIO_NAMES[1])
    compact = result.world.snapshot()
    detailed = result.world.detailed_snapshot()

    assert "retained_audit_replay_summaries" not in compact
    assert detailed["retained_audit_replay_summaries"][0]["by_message_id"] == {
        "message_alpha_074": 1,
        "message_zeta_074": 1,
    }
    assert detailed["retained_audit_replay_summaries"][0]["by_mailbox_id"] == {
        "mailbox_neo": 2
    }

    detailed["retained_audit_replay_summaries"][0]["by_message_id"][
        "message_alpha_074"
    ] = 99
    detailed["retained_audit_replay_summaries"][0]["by_mailbox_id"][
        "mailbox_neo"
    ] = 99
    fresh = result.world.detailed_snapshot()

    assert fresh["retained_audit_replay_summaries"][0]["by_message_id"] == {
        "message_alpha_074": 1,
        "message_zeta_074": 1,
    }
    assert fresh["retained_audit_replay_summaries"][0]["by_mailbox_id"] == {
        "mailbox_neo": 2
    }


def test_v1_8_checked_in_scenarios_validate_run_and_extend_contiguous_sweep():
    scenario_files = [
        path
        for path in list_scenario_files(SCENARIOS_DIR)
        if path.name[:3] in {"073", "074", "075"}
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
    assert [path.name[:3] for path in scenario_files] == ["073", "074", "075"]
    assert scenario_numbers == list(range(1, 91))
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
