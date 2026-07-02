"""Tests for read-only lifecycle explanation pruning plan helpers."""

from __future__ import annotations

import json
from copy import deepcopy

from darwin.models import (
    RegistryHub,
    StreamOfferLifecycleExplanation,
    StreamOfferLifecycleExplanationPruningPlan,
    StreamOfferLifecycleExplanationRetentionDecision,
    make_stream_offer_lifecycle_explanation_retention_policy,
)
from darwin.registry import (
    classify_stream_offer_lifecycle_explanations_for_retention,
    plan_stream_offer_lifecycle_explanation_pruning,
    record_stream_offer_lifecycle_explanations,
    summarize_stream_offer_lifecycle_explanation_history,
    summarize_stream_offer_lifecycle_explanation_pruning_by_category,
    summarize_stream_offer_lifecycle_explanation_pruning_by_reason,
    summarize_stream_offer_lifecycle_explanation_pruning_plan,
)


def test_pruning_plan_candidate_keys_match_retention_prune_candidates():
    explanations = (
        _explanation(offer_id="offer_keep", category="active"),
        _explanation(
            offer_id="offer_prune",
            category="expired",
            reason="expired_by_plan",
            status="expired",
        ),
        _explanation(
            hub_id="registry_remote_001",
            offer_id="offer_ignored",
            category="active",
        ),
    )
    policy = make_stream_offer_lifecycle_explanation_retention_policy(
        policy_id="retention_policy_001",
        hub_id="registry_chat_001",
        prune_categories=["expired"],
    )
    decision = classify_stream_offer_lifecycle_explanations_for_retention(
        explanations,
        policy,
    )

    plan = plan_stream_offer_lifecycle_explanation_pruning(
        decision,
        explanations=explanations,
    )

    assert isinstance(plan, StreamOfferLifecycleExplanationPruningPlan)
    assert plan.candidate_explanation_keys == decision.prune_candidate_explanation_keys
    assert plan.retained_explanation_keys == decision.kept_explanation_keys
    assert plan.ignored_explanation_keys == decision.ignored_explanation_keys
    assert plan.candidate_explanation_keys == (_key(1, explanations[1]),)
    assert plan.retained_explanation_keys == (_key(0, explanations[0]),)
    assert plan.ignored_explanation_keys == (_key(2, explanations[2]),)
    assert plan.by_decision_category == {
        "ignored": 1,
        "kept": 1,
        "prune_candidate": 1,
    }


def test_pruning_plan_from_policy_preserves_retention_precedence_and_groups():
    explanations = (
        _explanation(
            offer_id="offer_retained_conflict",
            category="terminal",
            reason="terminal_cleanup_candidate",
            status="accepted",
            source="lifecycle_plan",
        ),
        _explanation(
            offer_id="offer_missing",
            category="missing",
            reason="missing_by_result",
            status="missing",
            source="lifecycle_apply_result",
        ),
        _explanation(
            offer_id="offer_applied",
            category="applied",
            reason="applied_by_result",
            status="applied",
            source=None,
        ),
    )
    policy = make_stream_offer_lifecycle_explanation_retention_policy(
        policy_id="retention_policy_001",
        hub_id="registry_chat_001",
        retain_reasons=["terminal_cleanup_candidate"],
        prune_categories=["terminal", "missing"],
        prune_sources=["lifecycle_apply_result"],
        max_records=1,
    )

    plan = plan_stream_offer_lifecycle_explanation_pruning(
        explanations=explanations,
        policy=policy,
    )

    assert plan.retained_explanation_keys == (_key(0, explanations[0]),)
    assert plan.candidate_explanation_keys == (
        _key(1, explanations[1]),
        _key(2, explanations[2]),
    )
    assert plan.ignored_explanation_keys == ()
    assert plan.candidate_count == 2
    assert plan.retained_count == 1
    assert plan.ignored_count == 0
    assert plan.candidate_by_category == {"applied": 1, "missing": 1}
    assert plan.candidate_by_reason == {
        "applied_by_result": 1,
        "missing_by_result": 1,
    }
    assert plan.candidate_by_source == {"lifecycle_apply_result": 1, "none": 1}
    assert summarize_stream_offer_lifecycle_explanation_pruning_by_category(
        plan
    ) == {"applied": 1, "missing": 1}
    assert summarize_stream_offer_lifecycle_explanation_pruning_by_reason(
        plan
    ) == {"applied_by_result": 1, "missing_by_result": 1}


def test_empty_retention_decision_produces_deterministic_empty_pruning_plan():
    decision = StreamOfferLifecycleExplanationRetentionDecision(
        hub_id="registry_chat_001",
        policy_id="retention_policy_001",
    )

    plan = plan_stream_offer_lifecycle_explanation_pruning(decision)
    summary = summarize_stream_offer_lifecycle_explanation_pruning_plan(plan)
    summary["metadata"]["read_only"] = False

    assert plan.to_summary() == {
        "hub_id": "registry_chat_001",
        "policy_id": "retention_policy_001",
        "candidate_explanation_keys": [],
        "retained_explanation_keys": [],
        "ignored_explanation_keys": [],
        "candidate_count": 0,
        "retained_count": 0,
        "ignored_count": 0,
        "by_decision_category": {
            "ignored": 0,
            "kept": 0,
            "prune_candidate": 0,
        },
        "candidate_by_category": {},
        "candidate_by_reason": {},
        "candidate_by_source": {},
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
            "candidate_group_counts_included": False,
        },
    }
    json.dumps(summary, sort_keys=True)


def test_pruning_plan_reads_history_without_mutating_or_pruning_it():
    hub = RegistryHub(hub_id="registry_chat_001", scope_path="global.chat")
    explanations = (
        _explanation(offer_id="offer_keep", category="active"),
        _explanation(
            offer_id="offer_prune",
            category="expired",
            reason="expired_by_plan",
            status="expired",
        ),
    )
    record_stream_offer_lifecycle_explanations(hub, explanations)
    history_before = deepcopy(summarize_stream_offer_lifecycle_explanation_history(hub))
    policy = make_stream_offer_lifecycle_explanation_retention_policy(
        policy_id="retention_policy_001",
        hub_id=hub.hub_id,
        prune_categories=["expired"],
    )

    plan = plan_stream_offer_lifecycle_explanation_pruning(
        explanations=tuple(hub.stream_offer_lifecycle_explanation_history),
        policy=policy,
    )

    assert plan.candidate_explanation_keys == (_key(1, explanations[1]),)
    assert summarize_stream_offer_lifecycle_explanation_history(hub) == history_before
    assert hub.stream_offer_lifecycle_explanation_history == list(explanations)
    assert plan.metadata["retained_history_mutated"] is False
    assert plan.metadata["explanations_deleted"] is False
    assert plan.metadata["pruning_applied"] is False
    assert plan.metadata["cleanup_scheduled"] is False
    assert plan.metadata["delivery_behavior_changed"] is False
    assert plan.metadata["traffic_hub_routing_changed"] is False
    assert plan.metadata["networking"] is False


def _explanation(
    *,
    offer_id: str,
    category: str,
    reason: str | None = None,
    status: str | None = None,
    hub_id: str = "registry_chat_001",
    checked_at: int | None = 5,
    source: str | None = "lifecycle_plan",
) -> StreamOfferLifecycleExplanation:
    if reason is None:
        reason = {
            "active": "active_by_plan",
            "applied": "applied_by_result",
            "expired": "expired_by_plan",
            "missing": "missing_by_result",
            "skipped": "skipped_by_result",
            "terminal": "terminal_cleanup_candidate",
        }[category]
    return StreamOfferLifecycleExplanation(
        hub_id=hub_id,
        offer_id=offer_id,
        category=category,
        reason=reason,
        status=status or category,
        checked_at=checked_at,
        source=source,
    )


def _key(index: int, explanation: StreamOfferLifecycleExplanation) -> str:
    checked_at = "none" if explanation.checked_at is None else str(explanation.checked_at)
    source = "none" if explanation.source is None else explanation.source
    return (
        f"lifecycle_explanation:{index}:{explanation.hub_id}:"
        f"{explanation.offer_id}:{explanation.category}:{explanation.reason}:"
        f"{explanation.status}:{source}:{checked_at}"
    )
