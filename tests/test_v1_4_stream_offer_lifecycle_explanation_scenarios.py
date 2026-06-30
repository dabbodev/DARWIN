from __future__ import annotations

from pathlib import Path

import yaml

from darwin.models import (
    StreamOfferLifecycleAuditSummary,
    StreamOfferLifecycleExplanation,
)
from darwin.sim.runner import run_scenario
from darwin.sim.scenarios import list_scenario_files, validate_scenario_dict
from darwin.sim.validation import ASSERTION_REQUIRED_FIELDS, STEP_REQUIRED_FIELDS

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_DIR = PROJECT_ROOT / "scenarios"


def test_v1_4_lifecycle_explanation_actions_and_assertions_are_validated():
    assert STEP_REQUIRED_FIELDS["explain_stream_offer_lifecycle_plan"] == (
        "registry_hub",
    )
    assert STEP_REQUIRED_FIELDS["explain_stream_offer_lifecycle_apply_result"] == (
        "registry_hub",
    )
    assert STEP_REQUIRED_FIELDS["record_stream_offer_lifecycle_explanations"] == (
        "registry_hub",
    )
    assert STEP_REQUIRED_FIELDS["summarize_stream_offer_lifecycle_audit"] == (
        "registry_hub",
    )
    assert ASSERTION_REQUIRED_FIELDS[
        "stream_offer_lifecycle_explanation_contains"
    ] == ("registry_hub",)
    assert ASSERTION_REQUIRED_FIELDS[
        "stream_offer_lifecycle_explanation_history_contains"
    ] == ("registry_hub",)
    assert ASSERTION_REQUIRED_FIELDS[
        "stream_offer_lifecycle_audit_summary_contains"
    ] == ("registry_hub",)


def test_v1_4_lifecycle_explanation_validation_rejects_bad_field_types():
    result = validate_scenario_dict(_minimal_invalid_v1_4_validation_scenario())

    assert not result.valid
    assert [error.location for error in result.errors] == [
        "steps[0].record_explanations",
        "steps[0].plan_checked_at",
        "steps[0].ignored_offer_ids[1]",
        "steps[1].record_explanations",
        "steps[1].checked_at",
        "steps[2].checked_at",
        "steps[3].include_action_explanations",
        "steps[3].include_retained_explanations",
        "assertions[0].checked_at",
        "assertions[1].checked_at",
        "assertions[2].total_transitions",
        "assertions[2].offer_count",
    ]


def test_v1_4_plan_explanation_scenario_is_read_only_and_not_retained():
    result = run_scenario(SCENARIOS_DIR / "061_stream_offer_lifecycle_plan_explained.yaml")
    hub = result.world.registry_hubs["registry_chat_001"]
    explanations = [
        item
        for item in result.world.action_results
        if isinstance(item, StreamOfferLifecycleExplanation)
    ]

    assert result.passed
    assert [explanation.category for explanation in explanations] == [
        "expired",
        "terminal",
        "active",
        "skipped",
    ]
    assert hub.stream_offer_lifecycle_explanation_history == []
    assert hub.stream_offer_status_transition_history == []
    assert _status(hub, "offer_plan_expired") == "held"
    assert _status(hub, "offer_plan_active") == "held"
    assert _status(hub, "offer_plan_terminal") == "accepted"


def test_v1_4_apply_explanation_scenario_retains_only_when_requested():
    result = run_scenario(
        SCENARIOS_DIR / "062_stream_offer_lifecycle_apply_explanation_retained.yaml"
    )
    hub = result.world.registry_hubs["registry_chat_001"]

    assert result.passed
    assert [record.category for record in hub.stream_offer_lifecycle_explanation_history] == [
        "applied",
        "skipped",
        "skipped",
        "missing",
    ]
    assert hub.stream_offer_status_transition_history == []
    assert _status(hub, "offer_apply_explained") == "expired"
    assert _status(hub, "offer_apply_terminal") == "accepted"
    assert _status(hub, "offer_apply_stale") == "held"


def test_v1_4_audit_summary_scenario_groups_transition_and_explanation_history():
    result = run_scenario(SCENARIOS_DIR / "063_stream_offer_lifecycle_audit_summary.yaml")
    hub = result.world.registry_hubs["registry_chat_001"]
    summaries = [
        item
        for item in result.world.action_results
        if isinstance(item, StreamOfferLifecycleAuditSummary)
    ]

    assert result.passed
    assert len(summaries) == 1
    assert summaries[0].to_summary() == {
        "hub_id": "registry_chat_001",
        "total_transitions": 1,
        "by_offer_id": {"offer_audit_expired": 2},
        "by_status": {"applied": 1, "expired": 1},
        "by_reason": {"applied_by_result": 1, "expired": 1},
        "by_category": {"applied": 1},
        "explanation_count": 1,
        "metadata": {
            "simulator_local": True,
            "read_only": True,
            "audit_summary_only": True,
            "policy_decision": False,
            "registry_hub_mutated": False,
            "offer_mutated": False,
            "transitions_recorded": False,
            "offers_deleted": False,
            "delivery_behavior_changed": False,
            "traffic_hub_routing_changed": False,
            "networking": False,
            "included_explanations": True,
        },
    }
    assert len(hub.stream_offer_status_transition_history) == 1
    assert len(hub.stream_offer_lifecycle_explanation_history) == 1
    assert _status(hub, "offer_audit_expired") == "expired"
    assert _status(hub, "offer_audit_active") == "held"


def test_v1_4_lifecycle_explanation_detailed_snapshots_do_not_change_compact_snapshot():
    result = run_scenario(
        SCENARIOS_DIR / "063_stream_offer_lifecycle_audit_summary.yaml"
    )
    compact = result.world.snapshot()
    detailed = result.final_snapshot

    assert "stream_offer_lifecycle_explanations" not in compact
    assert "stream_offer_lifecycle_audit_summaries" not in compact
    assert detailed["stream_offer_lifecycle_explanations"][0]["offer_id"] == (
        "offer_audit_expired"
    )
    assert detailed["stream_offer_lifecycle_audit_summaries"][0][
        "by_reason"
    ] == {
        "applied_by_result": 1,
        "expired": 1,
    }


def test_v1_4_checked_in_lifecycle_explanation_scenarios_validate_and_run():
    scenario_files = [
        path
        for path in list_scenario_files(SCENARIOS_DIR)
        if path.name[:3] in {"061", "062", "063"}
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

    assert [path.name[:3] for path in scenario_files] == ["061", "062", "063"]
    assert not failures


def test_v1_4_scenario_sweep_remains_contiguous_001_through_063():
    scenario_numbers = sorted(
        int(path.name[:3])
        for path in list_scenario_files(SCENARIOS_DIR)
        if path.name[:3].isdigit()
    )

    assert scenario_numbers == list(range(1, 64))


def _minimal_invalid_v1_4_validation_scenario() -> dict[str, object]:
    return {
        "scenario_id": "v1_4_invalid_lifecycle_explanation_validation",
        "name": "v1.4 invalid lifecycle explanation validation",
        "category": "stream_offer",
        "setup": {
            "registry_hubs": [
                {"hub_id": "registry_chat_001", "scope_path": "global.chat"}
            ]
        },
        "steps": [
            {
                "action": "explain_stream_offer_lifecycle_plan",
                "registry_hub": "registry_chat_001",
                "record_explanations": "true",
                "plan_checked_at": "later",
                "ignored_offer_ids": ["offer_invalid", 42],
            },
            {
                "action": "explain_stream_offer_lifecycle_apply_result",
                "registry_hub": "registry_chat_001",
                "record_explanations": "true",
                "checked_at": -1,
            },
            {
                "action": "record_stream_offer_lifecycle_explanations",
                "registry_hub": "registry_chat_001",
                "checked_at": "later",
            },
            {
                "action": "summarize_stream_offer_lifecycle_audit",
                "registry_hub": "registry_chat_001",
                "include_action_explanations": "true",
                "include_retained_explanations": "true",
            },
        ],
        "assertions": [
            {
                "type": "stream_offer_lifecycle_explanation_contains",
                "registry_hub": "registry_chat_001",
                "checked_at": "later",
            },
            {
                "type": "stream_offer_lifecycle_explanation_history_contains",
                "registry_hub": "registry_chat_001",
                "checked_at": -1,
            },
            {
                "type": "stream_offer_lifecycle_audit_summary_contains",
                "registry_hub": "registry_chat_001",
                "total_transitions": -1,
                "offer_count": "many",
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
