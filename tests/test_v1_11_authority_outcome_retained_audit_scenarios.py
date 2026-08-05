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
V1_11_SCENARIO_NAMES = (
    "082_retained_audit_authority_outcome_classification.yaml",
    "083_retained_audit_authority_outcome_replay.yaml",
    "084_retained_audit_authority_outcome_apply.yaml",
)


def test_v1_11_history_label_scenarios_validate():
    for scenario_name in V1_11_SCENARIO_NAMES:
        validation = validate_scenario_dict(
            _load_yaml(SCENARIOS_DIR / scenario_name),
            path=scenario_name,
        )
        assert validation.valid, validation.errors


def test_v1_11_replay_assertion_counts_must_be_non_negative():
    invalid = _load_yaml(SCENARIOS_DIR / V1_11_SCENARIO_NAMES[1])
    invalid["assertions"][0]["requested_alias_count"] = -1
    invalid["assertions"][0]["granted_alias_count"] = -1
    invalid["assertions"][0]["target_device_count"] = -1
    invalid["assertions"][0]["path_hub_count"] = -1

    validation = validate_scenario_dict(invalid)

    assert not validation.valid
    locations = {error.location for error in validation.errors}
    assert {
        "assertions[0].requested_alias_count",
        "assertions[0].granted_alias_count",
        "assertions[0].target_device_count",
        "assertions[0].path_hub_count",
    } <= locations


def test_v1_11_authority_classification_is_read_only_and_uses_final_status():
    scenario_path = SCENARIOS_DIR / V1_11_SCENARIO_NAMES[0]
    scenario = _load_yaml(scenario_path)
    before_data = dict(scenario)
    before_data["scenario_id"] = "082_before_authority_classification"
    before_data["steps"] = scenario["steps"][:-1]
    before_data["assertions"] = []

    before = run_scenario(before_data)
    result = run_scenario(scenario_path)
    before_hub = before.world.registry_hubs["registry_home_082"]
    hub = result.world.registry_hubs["registry_home_082"]
    decisions = _results(result, RetainedAuditCompactionDecision)

    assert result.passed
    assert len(decisions) == 1
    assert decisions[0].history_type == "authority_outcome"
    assert decisions[0].candidate_by_status == {"name_taken": 1}
    assert decisions[0].candidate_by_reason == {"fallback_alias_conflict": 1}
    assert decisions[0].metadata["scenario_record_history_types"] == [
        "authority_outcome"
    ]
    assert _summaries(hub.authority_outcome_history) == _summaries(
        before_hub.authority_outcome_history
    )
    assert not _results(result, RetainedAuditCompactionApplyResult)


def test_v1_11_replay_groups_authority_dimensions_through_decision_filters():
    result = run_scenario(SCENARIOS_DIR / V1_11_SCENARIO_NAMES[1])
    summaries = _results(result, RetainedAuditReplaySummary)

    assert result.passed
    assert len(summaries) == 3
    all_records, retained, candidate = summaries
    assert all_records.history_type == "authority_outcome"
    assert all_records.by_requested_alias == {"global.alpha": 2, "global.beta": 1}
    assert all_records.by_granted_alias == {
        "global.family.david.alpha": 1,
        "global.family.david.beta": 1,
    }
    assert all_records.by_target_device == {
        "dev_ALPHA_083": 1,
        "dev_BETA_083": 2,
    }
    assert all_records.by_path_hub == {
        "registry_family_083": 3,
        "registry_home_083": 3,
    }
    assert all_records.by_status == {"fallback_granted": 2, "name_taken": 1}
    assert retained.by_granted_alias == {
        "global.family.david.alpha": 1,
        "global.family.david.beta": 1,
    }
    assert retained.metadata["decision_category_filter"] == "retained"
    assert candidate.by_requested_alias == {"global.alpha": 1}
    assert candidate.by_granted_alias == {}
    assert candidate.by_target_device == {"dev_BETA_083": 1}
    assert candidate.metadata["decision_category_filter"] == "compaction_candidate"


def test_v1_11_apply_isolates_authority_history_from_alias_and_traffic_state():
    scenario_path = SCENARIOS_DIR / V1_11_SCENARIO_NAMES[2]
    scenario = _load_yaml(scenario_path)
    first_apply_index = next(
        index
        for index, step in enumerate(scenario["steps"])
        if step.get("action") == "apply_retained_audit_compaction_decision"
    )
    before_data = dict(scenario)
    before_data["scenario_id"] = "084_before_authority_apply"
    before_data["steps"] = scenario["steps"][:first_apply_index]
    before_data["assertions"] = []

    before = run_scenario(before_data)
    result = run_scenario(scenario_path)
    before_home = before.world.registry_hubs["registry_home_084"]
    home = result.world.registry_hubs["registry_home_084"]
    before_family = before.world.registry_hubs["registry_family_084"]
    family = result.world.registry_hubs["registry_family_084"]
    apply_results = _results(result, RetainedAuditCompactionApplyResult)

    assert result.passed
    assert len(apply_results) == 2
    applied, repeated = apply_results
    assert applied.compacted_count == 1
    assert applied.metadata["authority_history_mutated"] is True
    assert applied.metadata["alias_history_mutated"] is False
    assert repeated.compacted_count == 0
    assert repeated.missing_count == 1
    assert repeated.metadata["authority_history_mutated"] is False
    assert applied.metadata["canonical_identity_rewritten"] is False
    assert [item.final_status for item in before_home.authority_outcome_history] == [
        "fallback_granted",
        "name_taken",
    ]
    assert [item.final_status for item in home.authority_outcome_history] == [
        "fallback_granted"
    ]
    assert home.aliases == before_home.aliases
    assert home.conflicts == before_home.conflicts
    assert home.security_events == before_home.security_events
    assert family.aliases == before_family.aliases
    assert family.conflicts == before_family.conflicts
    assert family.security_events == before_family.security_events
    for history_name in (
        "stream_offer_lifecycle_explanation_history",
        "stream_offer_status_transition_history",
        "rendezvous_poll_result_history",
        "lane_admission_decision_history",
        "encrypted_delivery_result_history",
        "encryption_policy_decision_history",
        "message_delivery_results",
    ):
        assert getattr(home, history_name) == getattr(before_home, history_name)
    assert result.world.action_results[: len(before.world.action_results)] == (
        before.world.action_results
    )
    compact_before = before.world.snapshot()
    compact_after = result.world.snapshot()
    assert compact_after["time"] == compact_before["time"] + 2
    assert {key: value for key, value in compact_after.items() if key != "time"} == {
        key: value for key, value in compact_before.items() if key != "time"
    }


def test_v1_11_detailed_snapshot_is_copied_and_compact_shape_is_unchanged():
    result = run_scenario(SCENARIOS_DIR / V1_11_SCENARIO_NAMES[1])
    compact = result.world.snapshot()
    detailed = result.world.detailed_snapshot()
    home_snapshot = detailed["registry_hubs"]["registry_home_083"]

    assert "authority_outcome_history" not in compact
    assert "retained_audit_replay_summaries" not in compact
    assert home_snapshot["authority_outcome_history"][0]["requesting_hub"] == (
        "registry_home_083"
    )
    assert detailed["retained_audit_replay_summaries"][0][
        "by_requested_alias"
    ] == {"global.alpha": 2, "global.beta": 1}
    assert detailed["retained_audit_replay_summaries"][0]["by_path_hub"] == {
        "registry_family_083": 3,
        "registry_home_083": 3,
    }

    home_snapshot["authority_outcome_history"][0]["requesting_hub"] = "mutated"
    detailed["retained_audit_replay_summaries"][0]["by_requested_alias"][
        "global.alpha"
    ] = 99
    fresh = result.world.detailed_snapshot()

    assert fresh["registry_hubs"]["registry_home_083"][
        "authority_outcome_history"
    ][0]["requesting_hub"] == "registry_home_083"
    assert fresh["retained_audit_replay_summaries"][0]["by_requested_alias"][
        "global.alpha"
    ] == 2


def test_v1_11_checked_in_scenarios_run_and_extend_contiguous_sweep():
    scenario_files = [
        path
        for path in list_scenario_files(SCENARIOS_DIR)
        if path.name[:3] in {"082", "083", "084"}
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
    assert [path.name[:3] for path in scenario_files] == ["082", "083", "084"]
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


def _summaries(values: list[object]) -> list[dict[str, object]]:
    return [value.to_summary() for value in values]
