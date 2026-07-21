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
V1_7_SCENARIO_NAMES = (
    "070_retained_audit_poll_admission_classification.yaml",
    "071_retained_audit_poll_admission_replay.yaml",
    "072_retained_audit_poll_admission_apply.yaml",
)


def test_v1_7_poll_and_admission_history_labels_and_request_counts_validate():
    for scenario_name in V1_7_SCENARIO_NAMES:
        validation = validate_scenario_dict(
            _load_yaml(SCENARIOS_DIR / scenario_name),
            path=scenario_name,
        )
        assert validation.valid, validation.errors

    invalid = _load_yaml(
        SCENARIOS_DIR / "071_retained_audit_poll_admission_replay.yaml"
    )
    invalid["scenario_id"] = "071_invalid_request_count"
    invalid["assertions"][0]["request_count"] = -1

    validation = validate_scenario_dict(invalid)

    assert not validation.valid
    assert "assertions[0].request_count" in {
        error.location for error in validation.errors
    }


def test_v1_7_mixed_poll_admission_classification_is_read_only():
    scenario_path = (
        SCENARIOS_DIR / "070_retained_audit_poll_admission_classification.yaml"
    )
    scenario = _load_yaml(scenario_path)
    before_data = dict(scenario)
    before_data["scenario_id"] = "070_before_retained_audit_classification"
    before_data["steps"] = scenario["steps"][:-1]
    before_data["assertions"] = []

    before = run_scenario(before_data)
    result = run_scenario(scenario_path)
    before_hub = before.world.registry_hubs["registry_chat_001"]
    hub = result.world.registry_hubs["registry_chat_001"]
    decisions = _results(result, RetainedAuditCompactionDecision)

    assert result.passed
    assert len(decisions) == 1
    assert decisions[0].history_type == "mixed"
    assert decisions[0].by_decision_category == {
        "compaction_candidate": 2,
        "ignored": 0,
        "retained": 0,
    }
    assert decisions[0].candidate_by_history_type == {
        "lane_admission_decision": 1,
        "rendezvous_poll_result": 1,
    }
    assert decisions[0].metadata["scenario_record_history_types"] == [
        "rendezvous_poll_result",
        "lane_admission_decision",
    ]
    assert _summaries(hub.rendezvous_poll_result_history) == _summaries(
        before_hub.rendezvous_poll_result_history
    )
    assert _summaries(hub.lane_admission_decision_history) == _summaries(
        before_hub.lane_admission_decision_history
    )
    assert _summaries(hub.held_stream_offers) == _summaries(
        before_hub.held_stream_offers
    )
    assert not _results(result, RetainedAuditCompactionApplyResult)


def test_v1_7_mixed_replay_groups_shared_request_and_admission_offer_only():
    result = run_scenario(
        SCENARIOS_DIR / "071_retained_audit_poll_admission_replay.yaml"
    )
    hub = result.world.registry_hubs["registry_chat_001"]
    summaries = _results(result, RetainedAuditReplaySummary)

    assert result.passed
    assert len(summaries) == 3
    all_records, retained, candidate = summaries
    assert all_records.history_type == "mixed"
    assert all_records.record_count == 2
    assert all_records.by_request_id == {"shared_request_071": 2}
    assert all_records.by_offer_id == {"offer_audit_replay_071": 1}
    assert all_records.metadata["by_history_type"] == {
        "lane_admission_decision": 1,
        "rendezvous_poll_result": 1,
    }
    assert list(all_records.record_keys) == [
        "rendezvous_poll:0:registry_chat_001:hub_private_child:"
        "shared_request_071:global.chat:1:matched:offers_available:"
        "offer_audit_replay_071",
        "lane_admission:1:registry_chat_001:lane_admission_decision_071:"
        "lane_admission_policy_071:offer_audit_replay_071:shared_request_071:"
        "pass_down:accepted",
    ]
    assert retained.history_type == "lane_admission_decision"
    assert retained.by_request_id == {"shared_request_071": 1}
    assert retained.by_offer_id == {"offer_audit_replay_071": 1}
    assert retained.metadata["decision_category_filter"] == "retained"
    assert candidate.history_type == "rendezvous_poll_result"
    assert candidate.by_request_id == {"shared_request_071": 1}
    assert candidate.by_offer_id == {}
    assert candidate.metadata["decision_category_filter"] == (
        "compaction_candidate"
    )
    assert len(hub.rendezvous_poll_result_history) == 1
    assert len(hub.lane_admission_decision_history) == 1


def test_v1_7_separate_apply_isolates_histories_offers_delivery_and_routing():
    scenario_path = SCENARIOS_DIR / "072_retained_audit_poll_admission_apply.yaml"
    scenario = _load_yaml(scenario_path)
    first_apply_index = next(
        index
        for index, step in enumerate(scenario["steps"])
        if step.get("action") == "apply_retained_audit_compaction_decision"
    )
    before_data = dict(scenario)
    before_data["scenario_id"] = "072_before_poll_admission_apply"
    before_data["steps"] = scenario["steps"][:first_apply_index]
    before_data["assertions"] = []

    before = run_scenario(before_data)
    result = run_scenario(scenario_path)
    before_hub = before.world.registry_hubs["registry_chat_001"]
    hub = result.world.registry_hubs["registry_chat_001"]
    apply_results = _results(result, RetainedAuditCompactionApplyResult)

    assert result.passed
    assert len(apply_results) == 2
    poll_apply, admission_apply = apply_results
    assert poll_apply.history_type == "rendezvous_poll_result"
    assert poll_apply.compacted_count == 1
    assert poll_apply.retained_count == 1
    assert poll_apply.metadata["polling_history_mutated"] is True
    assert poll_apply.metadata["admission_history_mutated"] is False
    assert admission_apply.history_type == "lane_admission_decision"
    assert admission_apply.compacted_count == 1
    assert admission_apply.retained_count == 1
    assert admission_apply.metadata["polling_history_mutated"] is False
    assert admission_apply.metadata["admission_history_mutated"] is True
    assert [
        record.request_id for record in before_hub.rendezvous_poll_result_history
    ] == ["poll_candidate_072", "poll_retained_072"]
    assert [record.request_id for record in hub.rendezvous_poll_result_history] == [
        "poll_retained_072"
    ]
    assert [
        decision.decision_id
        for decision in before_hub.lane_admission_decision_history
    ] == ["lane_admission_candidate_072", "lane_admission_retained_072"]
    assert [
        decision.decision_id for decision in hub.lane_admission_decision_history
    ] == ["lane_admission_retained_072"]
    assert _summaries(hub.held_stream_offers) == _summaries(
        before_hub.held_stream_offers
    )
    assert _summaries(hub.message_delivery_results) == _summaries(
        before_hub.message_delivery_results
    )
    assert result.world.snapshot()["traffic_hubs"] == before.world.snapshot()[
        "traffic_hubs"
    ]
    assert all(
        apply_result.metadata["delivery_behavior_changed"] is False
        and apply_result.metadata["traffic_hub_routing_changed"] is False
        for apply_result in apply_results
    )


def test_v1_7_replay_detailed_snapshot_is_copied_and_compact_shape_is_unchanged():
    result = run_scenario(
        SCENARIOS_DIR / "071_retained_audit_poll_admission_replay.yaml"
    )
    compact = result.world.snapshot()
    detailed = result.world.detailed_snapshot()

    assert "retained_audit_compaction_decisions" not in compact
    assert "retained_audit_replay_summaries" not in compact
    assert "retained_audit_compaction_apply_results" not in compact
    assert detailed["retained_audit_replay_summaries"][0]["by_request_id"] == {
        "shared_request_071": 2
    }

    detailed["retained_audit_replay_summaries"][0]["by_request_id"][
        "shared_request_071"
    ] = 99
    detailed["retained_audit_replay_summaries"][0]["record_keys"].append(
        "mutated"
    )
    fresh = result.world.detailed_snapshot()

    assert fresh["retained_audit_replay_summaries"][0]["by_request_id"] == {
        "shared_request_071": 2
    }
    assert "mutated" not in fresh["retained_audit_replay_summaries"][0][
        "record_keys"
    ]


def test_v1_7_checked_in_scenarios_validate_run_and_extend_contiguous_sweep():
    scenario_files = [
        path
        for path in list_scenario_files(SCENARIOS_DIR)
        if path.name[:3] in {"070", "071", "072"}
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
        result = run_scenario(scenario_file)
        if not result.passed:
            failures.append(f"{scenario_file}: {result.assertion_results}")

    scenario_numbers = sorted(
        int(path.name[:3])
        for path in list_scenario_files(SCENARIOS_DIR)
        if path.name[:3].isdigit()
    )
    assert [path.name[:3] for path in scenario_files] == ["070", "071", "072"]
    assert scenario_numbers == list(range(1, 76))
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
