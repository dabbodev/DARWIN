from __future__ import annotations

import json
from pathlib import Path

from darwin.models import (
    StreamOfferLifecycleAuditSummary,
    StreamOfferLifecycleExplanation,
)
from darwin.sim.runner import run_scenario
from darwin.sim.world import World

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_DIR = PROJECT_ROOT / "scenarios"


def test_detailed_snapshot_includes_retained_explanation_history_after_record_action():
    result = run_scenario(
        SCENARIOS_DIR / "062_stream_offer_lifecycle_apply_explanation_retained.yaml"
    )
    compact = result.world.snapshot()
    hub_snapshot = result.final_snapshot["registry_hubs"]["registry_chat_001"]

    json.dumps(result.final_snapshot, sort_keys=True)
    assert compact == {
        "time": 5,
        "devices": [],
        "registry_hubs": ["registry_chat_001"],
        "traffic_hubs": [],
        "lanes": [],
    }
    assert "stream_offer_lifecycle_explanation_history" not in compact
    assert [
        record["category"]
        for record in hub_snapshot["stream_offer_lifecycle_explanation_history"]
    ] == [
        "applied",
        "skipped",
        "skipped",
        "missing",
    ]
    assert hub_snapshot["stream_offer_lifecycle_explanation_history"][0] == {
        "hub_id": "registry_chat_001",
        "offer_id": "offer_apply_explained",
        "category": "applied",
        "reason": "applied_by_result",
        "status": "applied",
        "checked_at": 5,
        "source": "lifecycle_apply_result",
        "details": {
            "simulator_local": True,
            "policy_decision": False,
            "registry_hub_mutated": False,
            "offer_mutated": False,
            "transitions_recorded": False,
            "offers_deleted": False,
            "delivery_behavior_changed": False,
            "traffic_hub_routing_changed": False,
            "networking": False,
            "result_field": "applied_offer_ids",
            "recorded_transition_count": 0,
            "read_only": True,
        },
    }


def test_detailed_snapshot_exposes_explanation_action_results_without_retention():
    result = run_scenario(SCENARIOS_DIR / "061_stream_offer_lifecycle_plan_explained.yaml")
    compact = result.world.snapshot()
    detailed = result.final_snapshot
    hub_snapshot = detailed["registry_hubs"]["registry_chat_001"]

    assert compact == {
        "time": 6,
        "devices": [],
        "registry_hubs": ["registry_chat_001"],
        "traffic_hubs": [],
        "lanes": [],
    }
    assert "stream_offer_lifecycle_explanations" not in compact
    assert hub_snapshot["stream_offer_lifecycle_explanation_history"] == []
    assert [
        explanation["offer_id"]
        for explanation in detailed["stream_offer_lifecycle_explanations"]
    ] == [
        "offer_plan_expired",
        "offer_plan_terminal",
        "offer_plan_active",
        "offer_plan_skipped",
    ]
    assert detailed["stream_offer_lifecycle_explanations"][0]["details"] == {
        "simulator_local": True,
        "policy_decision": False,
        "registry_hub_mutated": False,
        "offer_mutated": False,
        "transitions_recorded": False,
        "offers_deleted": False,
        "delivery_behavior_changed": False,
        "traffic_hub_routing_changed": False,
        "networking": False,
        "plan_field": "expired_offer_ids",
        "cleanup_candidate": True,
        "read_only": True,
    }


def test_detailed_snapshot_exposes_audit_summary_action_results():
    result = run_scenario(SCENARIOS_DIR / "063_stream_offer_lifecycle_audit_summary.yaml")
    compact = result.world.snapshot()
    detailed = result.final_snapshot

    json.dumps(detailed, sort_keys=True)
    assert compact == {
        "time": 6,
        "devices": [],
        "registry_hubs": ["registry_chat_001"],
        "traffic_hubs": [],
        "lanes": [],
    }
    assert "stream_offer_lifecycle_audit_summaries" not in compact
    assert detailed["stream_offer_lifecycle_audit_summaries"] == [
        {
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
    ]


def test_lifecycle_explanation_snapshot_ordering_and_copies_are_stable():
    world = World()
    world.action_results.extend(
        [
            StreamOfferLifecycleExplanation(
                hub_id="registry_b",
                offer_id="offer_b",
                category="active",
                reason="active_by_plan",
                status="active",
                checked_at=2,
                source="lifecycle_plan",
                details={"labels": ("explain_b",)},
            ),
            StreamOfferLifecycleAuditSummary(
                hub_id="registry_b",
                by_offer_id={"offer_b": 1, "offer_a": 2},
                by_status={"held": 1},
                metadata={"labels": ("audit_b",)},
            ),
            StreamOfferLifecycleExplanation(
                hub_id="registry_a",
                offer_id="offer_a",
                category="applied",
                reason="applied_by_result",
                status="applied",
                checked_at=1,
                source="lifecycle_apply_result",
                details={"labels": ("explain_a",)},
            ),
            StreamOfferLifecycleAuditSummary(
                hub_id="registry_a",
                by_offer_id={"offer_a": 1},
                by_status={"applied": 1},
            ),
        ]
    )

    snapshot = world.snapshot(detailed=True)
    snapshot["stream_offer_lifecycle_explanations"][0]["details"]["labels"].append(
        "mutated"
    )
    snapshot["stream_offer_lifecycle_audit_summaries"][0]["metadata"][
        "labels"
    ].append("mutated")
    fresh = world.snapshot(detailed=True)

    assert [
        explanation["hub_id"]
        for explanation in fresh["stream_offer_lifecycle_explanations"]
    ] == ["registry_b", "registry_a"]
    assert [
        summary["hub_id"]
        for summary in fresh["stream_offer_lifecycle_audit_summaries"]
    ] == ["registry_b", "registry_a"]
    assert fresh["stream_offer_lifecycle_explanations"][0]["details"] == {
        "labels": ["explain_b"]
    }
    assert fresh["stream_offer_lifecycle_audit_summaries"][0]["by_offer_id"] == {
        "offer_a": 2,
        "offer_b": 1,
    }
    assert fresh["stream_offer_lifecycle_audit_summaries"][0]["metadata"] == {
        "labels": ["audit_b"]
    }
    assert "stream_offer_lifecycle_explanations" not in world.snapshot()
    assert "stream_offer_lifecycle_audit_summaries" not in world.snapshot()
