from __future__ import annotations

import json
from pathlib import Path

from darwin.models import (
    StreamOfferLifecycleExplanationPruningApplyResult,
    StreamOfferLifecycleExplanationPruningPlan,
    StreamOfferLifecycleExplanationRetentionDecision,
)
from darwin.sim.runner import run_scenario
from darwin.sim.world import World

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_DIR = PROJECT_ROOT / "scenarios"


def test_detailed_snapshot_exposes_retention_decision_action_results():
    result = run_scenario(
        SCENARIOS_DIR / "064_stream_offer_lifecycle_retention_classification.yaml"
    )
    compact = result.world.snapshot()
    detailed = result.final_snapshot

    json.dumps(detailed, sort_keys=True)
    assert compact == {
        "time": 9,
        "devices": [],
        "registry_hubs": ["registry_chat_001", "registry_remote_001"],
        "traffic_hubs": [],
        "lanes": [],
    }
    assert "stream_offer_lifecycle_retention_decisions" not in compact
    assert detailed["stream_offer_lifecycle_retention_decisions"] == [
        {
            "hub_id": "registry_chat_001",
            "policy_id": "retention_policy_064",
            "kept_explanation_keys": [
                (
                    "lifecycle_explanation:1:registry_chat_001:"
                    "offer_retention_terminal:terminal:"
                    "terminal_cleanup_candidate:cleanup_candidate:"
                    "lifecycle_plan:5"
                ),
                (
                    "lifecycle_explanation:2:registry_chat_001:"
                    "offer_retention_active:active:active_by_plan:"
                    "active:lifecycle_plan:5"
                ),
            ],
            "prune_candidate_explanation_keys": [
                (
                    "lifecycle_explanation:0:registry_chat_001:"
                    "offer_retention_expired:expired:expired_by_plan:"
                    "expired:lifecycle_plan:5"
                )
            ],
            "ignored_explanation_keys": [
                (
                    "lifecycle_explanation:3:registry_remote_001:"
                    "offer_retention_ignored:active:active_by_plan:"
                    "active:lifecycle_plan:5"
                )
            ],
            "by_decision_category": {
                "ignored": 1,
                "kept": 2,
                "prune_candidate": 1,
            },
            "metadata": {
                "simulator_local": True,
                "read_only": True,
                "retention_decision_only": True,
                "policy_decision": True,
                "registry_hub_mutated": False,
                "retained_history_mutated": False,
                "explanations_deleted": False,
                "offers_deleted": False,
                "delivery_behavior_changed": False,
                "traffic_hub_routing_changed": False,
                "networking": False,
                "filter_precedence": "retain_filters_before_prune_filters",
                "max_records_applied": False,
            },
        }
    ]


def test_detailed_snapshot_exposes_pruning_plan_action_results():
    result = run_scenario(
        SCENARIOS_DIR / "065_stream_offer_lifecycle_pruning_plan.yaml"
    )
    compact = result.world.snapshot()
    detailed = result.final_snapshot

    json.dumps(detailed, sort_keys=True)
    assert "stream_offer_lifecycle_pruning_plans" not in compact
    assert detailed["stream_offer_lifecycle_pruning_plans"] == [
        {
            "hub_id": "registry_chat_001",
            "policy_id": "retention_policy_065",
            "candidate_explanation_keys": [
                (
                    "lifecycle_explanation:0:registry_chat_001:"
                    "offer_pruning_plan_expired:expired:expired_by_plan:"
                    "expired:lifecycle_plan:5"
                )
            ],
            "retained_explanation_keys": [
                (
                    "lifecycle_explanation:1:registry_chat_001:"
                    "offer_pruning_plan_terminal:terminal:"
                    "terminal_cleanup_candidate:cleanup_candidate:"
                    "lifecycle_plan:5"
                ),
                (
                    "lifecycle_explanation:2:registry_chat_001:"
                    "offer_pruning_plan_active:active:active_by_plan:"
                    "active:lifecycle_plan:5"
                ),
            ],
            "ignored_explanation_keys": [
                (
                    "lifecycle_explanation:3:registry_remote_001:"
                    "offer_pruning_plan_ignored:active:active_by_plan:"
                    "active:lifecycle_plan:5"
                )
            ],
            "candidate_count": 1,
            "retained_count": 2,
            "ignored_count": 1,
            "by_decision_category": {
                "ignored": 1,
                "kept": 2,
                "prune_candidate": 1,
            },
            "candidate_by_category": {"expired": 1},
            "candidate_by_reason": {"expired_by_plan": 1},
            "candidate_by_source": {"lifecycle_plan": 1},
            "metadata": {
                "simulator_local": True,
                "read_only": True,
                "pruning_plan_only": True,
                "decision_source": "explicit_decision",
                "registry_hub_mutated": False,
                "retained_history_mutated": False,
                "explanations_deleted": False,
                "offers_deleted": False,
                "pruning_applied": False,
                "cleanup_scheduled": False,
                "background_worker": False,
                "retry_loop": False,
                "durable_queue": False,
                "live_timer": False,
                "delivery_behavior_changed": False,
                "traffic_hub_routing_changed": False,
                "networking": False,
                "dns_lookup": False,
                "external_services": False,
                "cryptography": False,
                "compact_snapshot_changed": False,
                "candidate_group_counts_included": True,
            },
        }
    ]


def test_detailed_snapshot_exposes_pruning_apply_result_action_outputs():
    result = run_scenario(
        SCENARIOS_DIR / "066_stream_offer_lifecycle_pruning_apply.yaml"
    )
    compact = result.world.snapshot()
    detailed = result.final_snapshot

    json.dumps(detailed, sort_keys=True)
    assert compact == {
        "time": 7,
        "devices": [],
        "registry_hubs": ["registry_chat_001"],
        "traffic_hubs": [],
        "lanes": [],
    }
    assert "stream_offer_lifecycle_pruning_apply_results" not in compact
    assert detailed["stream_offer_lifecycle_pruning_apply_results"] == [
        {
            "hub_id": "registry_chat_001",
            "policy_id": "retention_policy_066",
            "pruned_explanation_keys": [
                (
                    "lifecycle_explanation:0:registry_chat_001:"
                    "offer_pruning_apply_pruned:expired:expired_by_plan:"
                    "expired:lifecycle_plan:5"
                )
            ],
            "retained_explanation_keys": [
                (
                    "lifecycle_explanation:1:registry_chat_001:"
                    "offer_pruning_apply_retained:active:active_by_plan:"
                    "active:lifecycle_plan:5"
                )
            ],
            "ignored_explanation_keys": [
                (
                    "lifecycle_explanation:2:registry_chat_001:"
                    "offer_pruning_apply_ignored:active:active_by_plan:"
                    "active:lifecycle_plan:5"
                )
            ],
            "missing_explanation_keys": [
                (
                    "lifecycle_explanation:3:registry_chat_001:"
                    "offer_pruning_apply_missing:expired:expired_by_plan:"
                    "expired:lifecycle_plan:5"
                )
            ],
            "pruned_count": 1,
            "retained_count": 1,
            "ignored_count": 1,
            "missing_count": 1,
            "metadata": {
                "simulator_local": True,
                "explicit_apply": True,
                "read_only": False,
                "pruning_apply_result_only": True,
                "registry_hub_mutated": True,
                "retained_history_mutated": True,
                "explanations_deleted": True,
                "offers_deleted": False,
                "held_offers_mutated": False,
                "lifecycle_plans_mutated": False,
                "lifecycle_apply_results_mutated": False,
                "transition_history_mutated": False,
                "polling_history_mutated": False,
                "admission_history_mutated": False,
                "delivery_behavior_changed": False,
                "traffic_hub_state_changed": False,
                "traffic_hub_routing_changed": False,
                "compact_snapshot_changed": False,
                "automatic_cleanup": False,
                "cleanup_scheduled": False,
                "background_worker": False,
                "retry_loop": False,
                "durable_queue": False,
                "live_timer": False,
                "live_clock": False,
                "networking": False,
                "dns_lookup": False,
                "external_services": False,
                "cryptography": False,
                "canonical_identity_rewritten": False,
            },
        }
    ]


def test_lifecycle_retention_snapshot_ordering_and_copies_are_stable():
    world = World()
    world.action_results.extend(
        [
            StreamOfferLifecycleExplanationRetentionDecision(
                hub_id="registry_b",
                policy_id="retention_policy_b",
                kept_explanation_keys=("kept_b",),
                metadata={"labels": ("decision_b",)},
            ),
            StreamOfferLifecycleExplanationPruningPlan(
                hub_id="registry_a",
                policy_id="retention_policy_a",
                candidate_explanation_keys=("candidate_a",),
                candidate_count=1,
                candidate_by_category={"expired": 1},
                metadata={"labels": ("plan_a",)},
            ),
            StreamOfferLifecycleExplanationPruningApplyResult(
                hub_id="registry_b",
                policy_id="retention_policy_b",
                pruned_explanation_keys=("pruned_b",),
                pruned_count=1,
                metadata={"labels": ("apply_b",)},
            ),
            StreamOfferLifecycleExplanationRetentionDecision(
                hub_id="registry_a",
                policy_id="retention_policy_a",
                prune_candidate_explanation_keys=("candidate_a",),
            ),
            StreamOfferLifecycleExplanationPruningPlan(
                hub_id="registry_b",
                policy_id="retention_policy_b",
                retained_explanation_keys=("retained_b",),
                retained_count=1,
            ),
            StreamOfferLifecycleExplanationPruningApplyResult(
                hub_id="registry_a",
                policy_id="retention_policy_a",
                retained_explanation_keys=("retained_a",),
                retained_count=1,
            ),
        ]
    )

    snapshot = world.snapshot(detailed=True)
    snapshot["stream_offer_lifecycle_retention_decisions"][0][
        "kept_explanation_keys"
    ].append("mutated")
    snapshot["stream_offer_lifecycle_retention_decisions"][0]["metadata"][
        "labels"
    ].append("mutated")
    snapshot["stream_offer_lifecycle_pruning_plans"][0][
        "candidate_explanation_keys"
    ].append("mutated")
    snapshot["stream_offer_lifecycle_pruning_plans"][0]["metadata"][
        "labels"
    ].append("mutated")
    snapshot["stream_offer_lifecycle_pruning_apply_results"][0][
        "pruned_explanation_keys"
    ].append("mutated")
    snapshot["stream_offer_lifecycle_pruning_apply_results"][0]["metadata"][
        "labels"
    ].append("mutated")
    fresh = world.snapshot(detailed=True)

    assert [
        decision["hub_id"]
        for decision in fresh["stream_offer_lifecycle_retention_decisions"]
    ] == ["registry_b", "registry_a"]
    assert [plan["hub_id"] for plan in fresh["stream_offer_lifecycle_pruning_plans"]] == [
        "registry_a",
        "registry_b",
    ]
    assert [
        apply_result["hub_id"]
        for apply_result in fresh["stream_offer_lifecycle_pruning_apply_results"]
    ] == ["registry_b", "registry_a"]
    assert fresh["stream_offer_lifecycle_retention_decisions"][0][
        "kept_explanation_keys"
    ] == ["kept_b"]
    assert fresh["stream_offer_lifecycle_retention_decisions"][0]["metadata"] == {
        "labels": ["decision_b"]
    }
    assert fresh["stream_offer_lifecycle_pruning_plans"][0][
        "candidate_explanation_keys"
    ] == ["candidate_a"]
    assert fresh["stream_offer_lifecycle_pruning_plans"][0][
        "candidate_by_category"
    ] == {"expired": 1}
    assert fresh["stream_offer_lifecycle_pruning_plans"][0]["metadata"] == {
        "labels": ["plan_a"]
    }
    assert fresh["stream_offer_lifecycle_pruning_apply_results"][0][
        "pruned_explanation_keys"
    ] == ["pruned_b"]
    assert fresh["stream_offer_lifecycle_pruning_apply_results"][0]["metadata"] == {
        "labels": ["apply_b"]
    }
    compact = world.snapshot()
    assert "stream_offer_lifecycle_retention_decisions" not in compact
    assert "stream_offer_lifecycle_pruning_plans" not in compact
    assert "stream_offer_lifecycle_pruning_apply_results" not in compact
