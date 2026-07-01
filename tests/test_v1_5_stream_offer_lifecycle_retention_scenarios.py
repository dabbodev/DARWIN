from __future__ import annotations

from pathlib import Path

import yaml

from darwin.models import (
    StreamOfferLifecycleExplanationPruningApplyResult,
    StreamOfferLifecycleExplanationPruningPlan,
    StreamOfferLifecycleExplanationRetentionDecision,
)
from darwin.sim.runner import run_scenario
from darwin.sim.scenarios import list_scenario_files, validate_scenario_dict
from darwin.sim.validation import ASSERTION_REQUIRED_FIELDS, STEP_REQUIRED_FIELDS

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_DIR = PROJECT_ROOT / "scenarios"


def test_v1_5_lifecycle_retention_actions_and_assertions_are_validated():
    assert STEP_REQUIRED_FIELDS[
        "classify_stream_offer_lifecycle_explanations_for_retention"
    ] == ("registry_hub", "policy_id")
    assert STEP_REQUIRED_FIELDS[
        "plan_stream_offer_lifecycle_explanation_pruning"
    ] == ("registry_hub", "policy_id")
    assert STEP_REQUIRED_FIELDS[
        "apply_stream_offer_lifecycle_explanation_pruning_plan"
    ] == ("registry_hub", "policy_id")
    assert ASSERTION_REQUIRED_FIELDS[
        "stream_offer_lifecycle_retention_decision_contains"
    ] == ("registry_hub",)
    assert ASSERTION_REQUIRED_FIELDS[
        "stream_offer_lifecycle_pruning_plan_contains"
    ] == ("registry_hub",)
    assert ASSERTION_REQUIRED_FIELDS[
        "stream_offer_lifecycle_pruning_apply_result_contains"
    ] == ("registry_hub",)


def test_v1_5_lifecycle_retention_validation_rejects_bad_field_types():
    result = validate_scenario_dict(_minimal_invalid_v1_5_validation_scenario())

    assert not result.valid
    assert [error.location for error in result.errors] == [
        "steps[0].include_action_explanations",
        "steps[0].include_foreign_action_explanations",
        "steps[0].include_retained_explanations",
        "steps[0].checked_at",
        "steps[0].max_records",
        "steps[0].prune_categories[1]",
        "steps[1].candidate_explanation_keys[1]",
        "steps[2].candidate_explanation_keys[1]",
        "assertions[0].kept_explanation_keys[1]",
        "assertions[0].kept_count",
        "assertions[1].candidate_count",
        "assertions[1].category_count",
        "assertions[2].pruned_explanation_keys[1]",
        "assertions[2].missing_count",
    ]


def test_v1_5_retention_classification_scenario_is_read_only():
    result = run_scenario(
        SCENARIOS_DIR / "064_stream_offer_lifecycle_retention_classification.yaml"
    )
    hub = result.world.registry_hubs["registry_chat_001"]
    decisions = [
        item
        for item in result.world.action_results
        if isinstance(item, StreamOfferLifecycleExplanationRetentionDecision)
    ]

    assert result.passed
    assert len(decisions) == 1
    assert decisions[0].by_decision_category == {
        "ignored": 1,
        "kept": 2,
        "prune_candidate": 1,
    }
    assert len(hub.stream_offer_lifecycle_explanation_history) == 3
    assert hub.stream_offer_status_transition_history == []
    assert _status(hub, "offer_retention_expired") == "held"
    assert _status(hub, "offer_retention_terminal") == "accepted"


def test_v1_5_pruning_plan_scenario_does_not_prune_history():
    result = run_scenario(SCENARIOS_DIR / "065_stream_offer_lifecycle_pruning_plan.yaml")
    hub = result.world.registry_hubs["registry_chat_001"]
    plans = [
        item
        for item in result.world.action_results
        if isinstance(item, StreamOfferLifecycleExplanationPruningPlan)
    ]

    assert result.passed
    assert len(plans) == 1
    assert plans[0].candidate_count == 1
    assert plans[0].retained_count == 2
    assert plans[0].ignored_count == 1
    assert plans[0].candidate_by_category == {"expired": 1}
    assert [record.offer_id for record in hub.stream_offer_lifecycle_explanation_history] == [
        "offer_pruning_plan_expired",
        "offer_pruning_plan_terminal",
        "offer_pruning_plan_active",
    ]
    assert hub.stream_offer_status_transition_history == []


def test_v1_5_pruning_apply_scenario_mutates_only_explanation_history():
    result = run_scenario(SCENARIOS_DIR / "066_stream_offer_lifecycle_pruning_apply.yaml")
    hub = result.world.registry_hubs["registry_chat_001"]
    apply_results = [
        item
        for item in result.world.action_results
        if isinstance(item, StreamOfferLifecycleExplanationPruningApplyResult)
    ]

    assert result.passed
    assert len(apply_results) == 1
    assert apply_results[0].pruned_count == 1
    assert apply_results[0].retained_count == 1
    assert apply_results[0].ignored_count == 1
    assert apply_results[0].missing_count == 1
    assert [record.offer_id for record in hub.stream_offer_lifecycle_explanation_history] == [
        "offer_pruning_apply_retained",
        "offer_pruning_apply_ignored",
    ]
    assert _status(hub, "offer_pruning_apply_pruned") == "held"
    assert hub.stream_offer_status_transition_history == []


def test_v1_5_lifecycle_retention_does_not_change_compact_snapshot():
    result = run_scenario(SCENARIOS_DIR / "066_stream_offer_lifecycle_pruning_apply.yaml")
    compact = result.world.snapshot()

    assert "stream_offer_lifecycle_retention_decisions" not in compact
    assert "stream_offer_lifecycle_pruning_plans" not in compact
    assert "stream_offer_lifecycle_pruning_apply_results" not in compact


def test_v1_5_checked_in_lifecycle_retention_scenarios_validate_and_run():
    scenario_files = [
        path
        for path in list_scenario_files(SCENARIOS_DIR)
        if path.name[:3] in {"064", "065", "066"}
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

    assert [path.name[:3] for path in scenario_files] == ["064", "065", "066"]
    assert not failures


def test_v1_5_scenario_sweep_remains_contiguous_001_through_066():
    scenario_numbers = sorted(
        int(path.name[:3])
        for path in list_scenario_files(SCENARIOS_DIR)
        if path.name[:3].isdigit()
    )

    assert scenario_numbers == list(range(1, 67))


def _minimal_invalid_v1_5_validation_scenario() -> dict[str, object]:
    return {
        "scenario_id": "v1_5_invalid_lifecycle_retention_validation",
        "name": "v1.5 invalid lifecycle retention validation",
        "category": "stream_offer",
        "setup": {
            "registry_hubs": [
                {"hub_id": "registry_chat_001", "scope_path": "global.chat"}
            ]
        },
        "steps": [
            {
                "action": "classify_stream_offer_lifecycle_explanations_for_retention",
                "registry_hub": "registry_chat_001",
                "policy_id": "retention_policy_invalid",
                "include_action_explanations": "true",
                "include_foreign_action_explanations": "true",
                "include_retained_explanations": "true",
                "checked_at": "later",
                "max_records": -1,
                "prune_categories": ["expired", 42],
            },
            {
                "action": "plan_stream_offer_lifecycle_explanation_pruning",
                "registry_hub": "registry_chat_001",
                "policy_id": "retention_policy_invalid",
                "candidate_explanation_keys": ["key_001", 42],
            },
            {
                "action": "apply_stream_offer_lifecycle_explanation_pruning_plan",
                "registry_hub": "registry_chat_001",
                "policy_id": "retention_policy_invalid",
                "candidate_explanation_keys": ["key_001", 42],
            },
        ],
        "assertions": [
            {
                "type": "stream_offer_lifecycle_retention_decision_contains",
                "registry_hub": "registry_chat_001",
                "kept_explanation_keys": ["key_001", 42],
                "kept_count": "many",
            },
            {
                "type": "stream_offer_lifecycle_pruning_plan_contains",
                "registry_hub": "registry_chat_001",
                "candidate_count": -1,
                "category_count": "many",
            },
            {
                "type": "stream_offer_lifecycle_pruning_apply_result_contains",
                "registry_hub": "registry_chat_001",
                "pruned_explanation_keys": ["key_001", 42],
                "missing_count": "many",
            },
        ],
    }


def _load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _status(hub, offer_id: str) -> str:
    for offer in hub.held_stream_offers:
        if offer.offer_id == offer_id:
            return offer.status.status
    raise AssertionError(f"missing offer: {offer_id}")
