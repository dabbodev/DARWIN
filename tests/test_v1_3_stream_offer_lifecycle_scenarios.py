from __future__ import annotations

from pathlib import Path

import yaml

from darwin.models import (
    StreamOfferLifecycleApplyResult,
    StreamOfferLifecyclePlan,
)
from darwin.sim.runner import run_scenario
from darwin.sim.scenarios import list_scenario_files, validate_scenario_dict
from darwin.sim.validation import ASSERTION_REQUIRED_FIELDS, STEP_REQUIRED_FIELDS

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_DIR = PROJECT_ROOT / "scenarios"


def test_v1_3_stream_offer_lifecycle_actions_and_assertions_are_validated():
    assert STEP_REQUIRED_FIELDS["plan_stream_offer_expiration"] == (
        "registry_hub",
        "checked_at",
    )
    assert STEP_REQUIRED_FIELDS["apply_stream_offer_lifecycle_plan"] == (
        "registry_hub",
    )
    assert ASSERTION_REQUIRED_FIELDS["stream_offer_lifecycle_plan_contains"] == (
        "registry_hub",
    )
    assert ASSERTION_REQUIRED_FIELDS[
        "stream_offer_lifecycle_apply_result_contains"
    ] == ("registry_hub",)
    assert ASSERTION_REQUIRED_FIELDS["stream_offer_status_transition_contains"] == (
        "registry_hub",
    )


def test_v1_3_lifecycle_scenario_validation_rejects_bad_field_types():
    result = validate_scenario_dict(_minimal_invalid_lifecycle_validation_scenario())

    assert not result.valid
    assert [error.location for error in result.errors] == [
        "steps[0].checked_at",
        "steps[1].record_transition",
        "steps[1].plan_checked_at",
        "steps[1].expired_offer_ids[1]",
        "assertions[0].checked_at",
        "assertions[1].recorded_transition_count",
        "assertions[1].applied_offer_ids[1]",
    ]


def test_v1_3_planning_scenario_is_read_only():
    result = run_scenario(
        SCENARIOS_DIR / "058_stream_offer_lifecycle_expiration_plan.yaml"
    )
    hub = result.world.registry_hubs["registry_chat_001"]
    plans = [
        item
        for item in result.world.action_results
        if isinstance(item, StreamOfferLifecyclePlan)
    ]

    assert result.passed
    assert plans[0].checked_at == 5
    assert plans[0].expired_offer_ids == ("offer_lifecycle_expired",)
    assert _status(hub, "offer_lifecycle_expired") == "held"
    assert _status(hub, "offer_lifecycle_active") == "held"
    assert _status(hub, "offer_lifecycle_terminal") == "accepted"
    assert hub.stream_offer_status_transition_history == []
    assert hub.message_delivery_results == []
    assert hub.message_inboxes == {}


def test_v1_3_apply_with_transition_scenario_records_retained_history():
    result = run_scenario(
        SCENARIOS_DIR / "059_stream_offer_lifecycle_apply_records_transition.yaml"
    )
    hub = result.world.registry_hubs["registry_chat_001"]
    apply_results = [
        item
        for item in result.world.action_results
        if isinstance(item, StreamOfferLifecycleApplyResult)
    ]

    assert result.passed
    assert apply_results[0].applied_offer_ids == (
        "offer_lifecycle_apply_recorded",
    )
    assert apply_results[0].recorded_transition_count == 1
    assert _status(hub, "offer_lifecycle_apply_recorded") == "expired"
    assert _status(hub, "offer_lifecycle_apply_active") == "held"
    transitions = [
        transition.to_summary()
        for transition in hub.stream_offer_status_transition_history
    ]
    assert transitions == [
        {
            "offer_id": "offer_lifecycle_apply_recorded",
            "previous_status": "held",
            "new_status": "expired",
            "reason": "expired",
            "hub_id": "registry_chat_001",
            "actor_id": "ops_local",
            "request_id": "lifecycle_apply_001",
            "metadata": {"source": "scenario_059"},
            "sequence": None,
        }
    ]


def test_v1_3_apply_without_transition_scenario_reports_skipped_and_missing_ids():
    result = run_scenario(
        SCENARIOS_DIR / "060_stream_offer_lifecycle_apply_without_transition.yaml"
    )
    hub = result.world.registry_hubs["registry_chat_001"]
    apply_results = [
        item
        for item in result.world.action_results
        if isinstance(item, StreamOfferLifecycleApplyResult)
    ]

    assert result.passed
    assert apply_results[0].applied_offer_ids == ("offer_lifecycle_no_transition",)
    assert apply_results[0].skipped_offer_ids == (
        "offer_lifecycle_terminal",
        "offer_lifecycle_stale",
    )
    assert apply_results[0].missing_offer_ids == ("offer_lifecycle_missing",)
    assert apply_results[0].recorded_transition_count == 0
    assert _status(hub, "offer_lifecycle_no_transition") == "expired"
    assert _status(hub, "offer_lifecycle_terminal") == "accepted"
    assert _status(hub, "offer_lifecycle_stale") == "held"
    assert hub.stream_offer_status_transition_history == []


def test_v1_3_checked_in_stream_offer_lifecycle_scenarios_validate_and_run():
    scenario_files = [
        path
        for path in list_scenario_files(SCENARIOS_DIR)
        if path.name[:3] in {"058", "059", "060"}
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

    assert [path.name[:3] for path in scenario_files] == ["058", "059", "060"]
    assert not failures


def test_v1_3_scenario_sweep_remains_contiguous_001_through_060():
    scenario_numbers = sorted(
        int(path.name[:3])
        for path in list_scenario_files(SCENARIOS_DIR)
        if path.name[:3].isdigit()
    )

    assert scenario_numbers == list(range(1, 61))


def _minimal_invalid_lifecycle_validation_scenario() -> dict[str, object]:
    return {
        "scenario_id": "v1_3_invalid_lifecycle_validation",
        "name": "v1.3 invalid lifecycle validation",
        "category": "stream_offer",
        "setup": {
            "registry_hubs": [
                {"hub_id": "registry_chat_001", "scope_path": "global.chat"}
            ]
        },
        "steps": [
            {
                "action": "plan_stream_offer_expiration",
                "registry_hub": "registry_chat_001",
                "checked_at": "later",
            },
            {
                "action": "apply_stream_offer_lifecycle_plan",
                "registry_hub": "registry_chat_001",
                "record_transition": "false",
                "plan_checked_at": -1,
                "expired_offer_ids": ["offer_invalid", 42],
            },
        ],
        "assertions": [
            {
                "type": "stream_offer_lifecycle_plan_contains",
                "registry_hub": "registry_chat_001",
                "checked_at": "later",
            },
            {
                "type": "stream_offer_lifecycle_apply_result_contains",
                "registry_hub": "registry_chat_001",
                "recorded_transition_count": -1,
                "applied_offer_ids": ["offer_invalid", 42],
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
