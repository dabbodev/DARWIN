from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from darwin.models import (
    RetainedAuditCompactionApplyResult,
    RetainedAuditCompactionDecision,
    RetainedAuditReplaySummary,
)
from darwin.sim.runner import run_scenario
from darwin.sim.scenarios import list_scenario_files, validate_scenario_dict
from darwin.sim.validation import ASSERTION_REQUIRED_FIELDS, STEP_REQUIRED_FIELDS

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_DIR = PROJECT_ROOT / "scenarios"


def test_v1_6_retained_audit_actions_and_assertions_are_validated():
    assert STEP_REQUIRED_FIELDS[
        "classify_retained_audit_records_for_compaction"
    ] == ("registry_hub", "policy_id")
    assert STEP_REQUIRED_FIELDS["summarize_retained_audit_replay"] == (
        "registry_hub",
    )
    assert STEP_REQUIRED_FIELDS["apply_retained_audit_compaction_decision"] == (
        "registry_hub",
        "decision_policy_id",
    )
    assert ASSERTION_REQUIRED_FIELDS[
        "retained_audit_compaction_decision_contains"
    ] == ("registry_hub",)
    assert ASSERTION_REQUIRED_FIELDS["retained_audit_replay_summary_contains"] == (
        "registry_hub",
    )
    assert ASSERTION_REQUIRED_FIELDS[
        "retained_audit_compaction_apply_result_contains"
    ] == ("registry_hub",)


def test_v1_6_retained_audit_validation_rejects_bad_field_types_and_filters():
    result = validate_scenario_dict(_minimal_invalid_v1_6_scenario())
    locations = {error.location for error in result.errors}

    assert not result.valid
    assert {
        "steps[0].max_records",
        "steps[0].retain_reasons[1]",
        "steps[0].record_history_types[0]",
        "steps[1].decision_category",
        "steps[1].decision_policy_id",
        "assertions[0].retained_record_keys[1]",
        "assertions[0].candidate_reason_count",
        "assertions[1].record_keys[1]",
        "assertions[1].record_count",
        "assertions[1].decision_category",
        "assertions[2].unsupported_record_keys[1]",
        "assertions[2].unsupported_count",
    }.issubset(locations)


def test_v1_6_compaction_classification_scenario_is_read_only():
    result = run_scenario(
        SCENARIOS_DIR / "067_retained_audit_compaction_classification.yaml"
    )
    hub = result.world.registry_hubs["registry_chat_001"]
    decisions = _results(result, RetainedAuditCompactionDecision)

    assert result.passed
    assert len(decisions) == 1
    assert decisions[0].by_decision_category == {
        "compaction_candidate": 1,
        "ignored": 1,
        "retained": 2,
    }
    assert decisions[0].metadata["filter_precedence"] == (
        "retain_filters_before_compact_filters"
    )
    assert [
        record.offer_id
        for record in hub.stream_offer_lifecycle_explanation_history
    ] == [
        "offer_audit_classify_candidate",
        "offer_audit_classify_precedence",
        "offer_audit_classify_default",
    ]
    assert len(hub.stream_offer_status_transition_history) == 1
    assert not _results(result, RetainedAuditCompactionApplyResult)


def test_v1_6_replay_summary_scenario_is_read_only_and_grouped():
    result = run_scenario(SCENARIOS_DIR / "068_retained_audit_replay_summary.yaml")
    hub = result.world.registry_hubs["registry_chat_001"]
    summaries = _results(result, RetainedAuditReplaySummary)

    assert result.passed
    assert len(summaries) == 3
    all_records, retained, candidate = summaries
    assert all_records.record_count == 2
    assert all_records.by_reason == {"applied_by_result": 1, "expired": 1}
    assert all_records.metadata["by_history_type"] == {
        "stream_offer_lifecycle_explanation": 1,
        "stream_offer_status_transition": 1,
    }
    assert retained.record_count == 1
    assert retained.metadata["decision_category_filter"] == "retained"
    assert candidate.record_count == 1
    assert candidate.metadata["decision_category_filter"] == (
        "compaction_candidate"
    )
    assert len(hub.stream_offer_lifecycle_explanation_history) == 1
    assert len(hub.stream_offer_status_transition_history) == 1
    assert not _results(result, RetainedAuditCompactionApplyResult)


def test_v1_6_decision_filtered_replay_reuses_classification_record_universe():
    scenario_data = _load_yaml(
        SCENARIOS_DIR / "068_retained_audit_replay_summary.yaml"
    )
    classification_index = next(
        index
        for index, step in enumerate(scenario_data["steps"])
        if step.get("action")
        == "classify_retained_audit_records_for_compaction"
    )
    classification = dict(scenario_data["steps"][classification_index])
    classification["record_history_types"] = [
        "stream_offer_status_transition"
    ]
    replay = {
        "action": "summarize_retained_audit_replay",
        "registry_hub": "registry_chat_001",
        "decision_policy_id": "retained_audit_policy_068",
        "decision_category": "compaction_candidate",
    }
    steps = [
        *scenario_data["steps"][:classification_index],
        classification,
        replay,
    ]
    replay_data = dict(scenario_data)
    replay_data["scenario_id"] = "068_replay_uses_decision_record_universe"
    replay_data["steps"] = steps
    replay_data["assertions"] = []

    result = run_scenario(replay_data)
    decision = _results(result, RetainedAuditCompactionDecision)[0]
    summary = _results(result, RetainedAuditReplaySummary)[0]

    assert decision.metadata["scenario_record_history_types"] == [
        "stream_offer_status_transition"
    ]
    assert summary.record_count == 1
    assert summary.record_keys[0].startswith("status_transition:0:")

    mismatched_data = dict(replay_data)
    mismatched_data["scenario_id"] = "068_replay_rejects_shifted_record_universe"
    mismatched_replay = dict(replay)
    mismatched_replay["record_history_types"] = [
        "stream_offer_lifecycle_explanation",
        "stream_offer_status_transition",
    ]
    mismatched_data["steps"] = [*steps[:-1], mismatched_replay]

    with pytest.raises(ValueError, match="same record_history_types ordering"):
        run_scenario(mismatched_data)


def test_v1_6_decision_filtered_replay_rejects_post_classification_mutation():
    scenario_data = _load_yaml(
        SCENARIOS_DIR / "069_retained_audit_compaction_apply.yaml"
    )
    supported_apply_index = next(
        index
        for index, step in enumerate(scenario_data["steps"])
        if step.get("action") == "apply_retained_audit_compaction_decision"
        and step.get("decision_policy_id") == "retained_audit_apply_policy_069"
    )
    replay_after_apply = {
        "action": "summarize_retained_audit_replay",
        "registry_hub": "registry_chat_001",
        "decision_policy_id": "retained_audit_apply_policy_069",
        "decision_category": "retained",
    }
    replay_data = dict(scenario_data)
    replay_data["scenario_id"] = "069_replay_rejects_changed_record_universe"
    replay_data["steps"] = [
        *scenario_data["steps"][: supported_apply_index + 1],
        replay_after_apply,
    ]
    replay_data["assertions"] = []

    with pytest.raises(ValueError, match="unchanged record universe"):
        run_scenario(replay_data)


def test_v1_6_compaction_apply_mutates_only_the_selected_retained_history():
    scenario_data = _load_yaml(
        SCENARIOS_DIR / "069_retained_audit_compaction_apply.yaml"
    )
    supported_apply_index = next(
        index
        for index, step in enumerate(scenario_data["steps"])
        if step.get("action") == "apply_retained_audit_compaction_decision"
        and step.get("decision_policy_id") == "retained_audit_apply_policy_069"
    )
    before_data = dict(scenario_data)
    before_data["scenario_id"] = "069_before_supported_retained_audit_apply"
    before_data["steps"] = scenario_data["steps"][:supported_apply_index]
    before_data["assertions"] = []
    before = run_scenario(before_data)
    result = run_scenario(
        SCENARIOS_DIR / "069_retained_audit_compaction_apply.yaml"
    )
    before_hub = before.world.registry_hubs["registry_chat_001"]
    hub = result.world.registry_hubs["registry_chat_001"]
    apply_results = _results(result, RetainedAuditCompactionApplyResult)

    assert result.passed
    assert len(apply_results) == 3
    unsupported, applied, reapplied = apply_results
    assert unsupported.history_type == "mixed"
    assert unsupported.unsupported_count == 3
    assert unsupported.compacted_count == 0
    assert applied.history_type == "stream_offer_lifecycle_explanation"
    assert applied.compacted_count == 1
    assert applied.retained_count == 1
    assert reapplied.compacted_count == 0
    assert reapplied.missing_count == 1
    assert [
        record.offer_id
        for record in before_hub.stream_offer_lifecycle_explanation_history
    ] == ["offer_audit_apply_candidate", "offer_audit_apply_retained"]
    assert [
        record.offer_id
        for record in hub.stream_offer_lifecycle_explanation_history
    ] == ["offer_audit_apply_retained"]
    assert _summaries(before_hub.stream_offer_status_transition_history) == _summaries(
        hub.stream_offer_status_transition_history
    )
    assert _summaries(before_hub.held_stream_offers) == _summaries(
        hub.held_stream_offers
    )
    assert applied.metadata["selected_history_type"] == (
        "stream_offer_lifecycle_explanation"
    )
    assert applied.metadata["polling_history_mutated"] is False
    assert applied.metadata["admission_history_mutated"] is False
    assert applied.metadata["encrypted_delivery_history_mutated"] is False
    assert applied.metadata["traffic_hub_routing_changed"] is False
    assert applied.metadata["canonical_identity_rewritten"] is False


def test_v1_6_apply_requires_a_prior_compaction_decision_result():
    scenario = {
        "scenario_id": "v1_6_missing_compaction_decision",
        "name": "v1.6 missing compaction decision",
        "category": "stream_offer",
        "setup": {
            "registry_hubs": [
                {"hub_id": "registry_chat_001", "scope_path": "global.chat"}
            ]
        },
        "steps": [
            {
                "action": "apply_retained_audit_compaction_decision",
                "registry_hub": "registry_chat_001",
                "decision_policy_id": "missing_policy",
            }
        ],
        "assertions": [],
    }

    with pytest.raises(KeyError, match="prior compaction decision result"):
        run_scenario(scenario)


def test_v1_6_retained_audit_actions_add_detailed_snapshot_sections_only():
    result = run_scenario(
        SCENARIOS_DIR / "069_retained_audit_compaction_apply.yaml"
    )
    compact = result.world.snapshot()
    detailed = result.world.detailed_snapshot()
    new_sections = {
        "retained_audit_compaction_decisions",
        "retained_audit_replay_summaries",
        "retained_audit_compaction_apply_results",
    }

    assert new_sections.isdisjoint(compact)
    assert new_sections.issubset(detailed)


def test_v1_6_checked_in_retained_audit_scenarios_validate_and_run():
    scenario_files = [
        path
        for path in list_scenario_files(SCENARIOS_DIR)
        if path.name[:3] in {"067", "068", "069"}
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

    assert [path.name[:3] for path in scenario_files] == ["067", "068", "069"]
    assert not failures


def test_v1_6_scenario_sweep_remains_contiguous_001_through_069():
    scenario_numbers = sorted(
        int(path.name[:3])
        for path in list_scenario_files(SCENARIOS_DIR)
        if path.name[:3].isdigit()
    )

    assert scenario_numbers == list(range(1, 70))


def _minimal_invalid_v1_6_scenario() -> dict[str, object]:
    return {
        "scenario_id": "v1_6_invalid_retained_audit_validation",
        "name": "v1.6 invalid retained audit validation",
        "category": "stream_offer",
        "setup": {
            "registry_hubs": [
                {"hub_id": "registry_chat_001", "scope_path": "global.chat"}
            ]
        },
        "steps": [
            {
                "action": "classify_retained_audit_records_for_compaction",
                "registry_hub": "registry_chat_001",
                "policy_id": "invalid_policy",
                "record_history_types": ["rendezvous_poll_result"],
                "retain_reasons": ["active_by_plan", 42],
                "max_records": -1,
            },
            {
                "action": "summarize_retained_audit_replay",
                "registry_hub": "registry_chat_001",
                "decision_category": "ignored",
            },
        ],
        "assertions": [
            {
                "type": "retained_audit_compaction_decision_contains",
                "registry_hub": "registry_chat_001",
                "retained_record_keys": ["key_001", 42],
                "candidate_reason_count": "many",
            },
            {
                "type": "retained_audit_replay_summary_contains",
                "registry_hub": "registry_chat_001",
                "record_keys": ["key_001", 42],
                "record_count": -1,
                "decision_category": "ignored",
            },
            {
                "type": "retained_audit_compaction_apply_result_contains",
                "registry_hub": "registry_chat_001",
                "unsupported_record_keys": ["key_001", 42],
                "unsupported_count": "many",
            },
        ],
    }


def _load_yaml(path: Path) -> dict[str, object]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _results(result, result_type):
    return [item for item in result.world.action_results if isinstance(item, result_type)]


def _summaries(records):
    return [record.to_summary() for record in records]
