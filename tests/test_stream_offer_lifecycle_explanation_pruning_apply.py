"""Tests for explicit lifecycle explanation pruning apply helpers."""

from __future__ import annotations

import json
from copy import deepcopy

from darwin.models import (
    RegistryHub,
    StreamOfferLifecycleExplanation,
    StreamOfferLifecycleExplanationPruningApplyResult,
    StreamOfferLifecycleExplanationPruningPlan,
    make_stream_offer,
    make_stream_offer_lifecycle_explanation_retention_policy,
)
from darwin.registry import (
    apply_stream_offer_lifecycle_explanation_pruning_plan,
    classify_stream_offer_lifecycle_explanations_for_retention,
    hold_stream_offer,
    plan_stream_offer_expiration,
    plan_stream_offer_lifecycle_explanation_pruning,
    record_stream_offer_lifecycle_explanations,
    summarize_stream_offer_lifecycle_explanation_history,
    summarize_stream_offer_lifecycle_explanation_pruning_apply_result,
)


def test_pruning_apply_removes_only_existing_candidate_records():
    hub = RegistryHub(hub_id="registry_chat_001", scope_path="global.chat")
    held_offer = make_stream_offer(
        offer_id="held_offer_001",
        requester_id="dev_A9F3",
        target_handle="alias:neo",
        lane_signature="basic_messaging:v1",
        expires_order=2,
    )
    hold_stream_offer(hub, held_offer)
    lifecycle_plan = plan_stream_offer_expiration(hub, checked_at=5)
    lifecycle_plan_before = lifecycle_plan.to_summary()
    explanations = (
        _explanation(offer_id="offer_keep", category="active"),
        _explanation(
            offer_id="offer_prune_existing",
            category="expired",
            reason="expired_by_plan",
            status="expired",
        ),
        _explanation(
            hub_id="registry_remote_001",
            offer_id="offer_ignored",
            category="active",
        ),
        _explanation(
            offer_id="offer_prune_missing",
            category="expired",
            reason="expired_by_plan",
            status="expired",
        ),
    )
    policy = make_stream_offer_lifecycle_explanation_retention_policy(
        policy_id="retention_policy_001",
        hub_id=hub.hub_id,
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
    decision_before = decision.to_summary()
    plan_before = plan.to_summary()
    held_before = deepcopy([offer.to_summary() for offer in hub.held_stream_offers])
    transitions_before = list(hub.stream_offer_status_transition_history)

    record_stream_offer_lifecycle_explanations(hub, explanations[:3])
    history_before_apply = summarize_stream_offer_lifecycle_explanation_history(hub)

    assert history_before_apply == [record.to_summary() for record in explanations[:3]]

    result = apply_stream_offer_lifecycle_explanation_pruning_plan(hub, plan)

    assert isinstance(result, StreamOfferLifecycleExplanationPruningApplyResult)
    assert result.pruned_explanation_keys == (_key(1, explanations[1]),)
    assert result.retained_explanation_keys == (_key(0, explanations[0]),)
    assert result.ignored_explanation_keys == (_key(2, explanations[2]),)
    assert result.missing_explanation_keys == (_key(3, explanations[3]),)
    assert result.pruned_count == 1
    assert result.retained_count == 1
    assert result.ignored_count == 1
    assert result.missing_count == 1
    assert summarize_stream_offer_lifecycle_explanation_history(hub) == [
        explanations[0].to_summary(),
        explanations[2].to_summary(),
    ]
    assert [offer.to_summary() for offer in hub.held_stream_offers] == held_before
    assert hub.stream_offer_status_transition_history == transitions_before
    assert lifecycle_plan.to_summary() == lifecycle_plan_before
    assert decision.to_summary() == decision_before
    assert plan.to_summary() == plan_before
    assert result.metadata["retained_history_mutated"] is True
    assert result.metadata["explanations_deleted"] is True
    assert result.metadata["held_offers_mutated"] is False
    assert result.metadata["transition_history_mutated"] is False
    assert result.metadata["delivery_behavior_changed"] is False
    assert result.metadata["traffic_hub_routing_changed"] is False
    assert result.metadata["compact_snapshot_changed"] is False
    assert result.metadata["automatic_cleanup"] is False
    assert result.metadata["background_worker"] is False
    assert result.metadata["retry_loop"] is False
    assert result.metadata["durable_queue"] is False
    assert result.metadata["live_timer"] is False
    assert result.metadata["networking"] is False


def test_empty_pruning_apply_is_deterministic_and_safe():
    hub = RegistryHub(hub_id="registry_chat_001", scope_path="global.chat")
    explanation = _explanation(offer_id="offer_keep", category="active")
    record_stream_offer_lifecycle_explanations(hub, (explanation,))
    history_before = summarize_stream_offer_lifecycle_explanation_history(hub)
    plan = StreamOfferLifecycleExplanationPruningPlan(
        hub_id=hub.hub_id,
        policy_id="retention_policy_001",
    )

    result = apply_stream_offer_lifecycle_explanation_pruning_plan(hub, plan)
    summary = summarize_stream_offer_lifecycle_explanation_pruning_apply_result(result)
    summary["metadata"]["explicit_apply"] = False

    assert summarize_stream_offer_lifecycle_explanation_history(hub) == history_before
    assert result.to_summary() == {
        "hub_id": "registry_chat_001",
        "policy_id": "retention_policy_001",
        "pruned_explanation_keys": [],
        "retained_explanation_keys": [],
        "ignored_explanation_keys": [],
        "missing_explanation_keys": [],
        "pruned_count": 0,
        "retained_count": 0,
        "ignored_count": 0,
        "missing_count": 0,
        "metadata": {
            "simulator_local": True,
            "explicit_apply": True,
            "read_only": False,
            "pruning_apply_result_only": True,
            "registry_hub_mutated": False,
            "retained_history_mutated": False,
            "explanations_deleted": False,
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
    json.dumps(result.to_summary(), sort_keys=True)


def test_pruning_plan_does_not_prune_until_explicit_apply_helper_is_called():
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
    history_before_plan = summarize_stream_offer_lifecycle_explanation_history(hub)
    policy = make_stream_offer_lifecycle_explanation_retention_policy(
        policy_id="retention_policy_001",
        hub_id=hub.hub_id,
        prune_categories=["expired"],
    )

    plan_stream_offer_lifecycle_explanation_pruning(
        explanations=tuple(hub.stream_offer_lifecycle_explanation_history),
        policy=policy,
    )

    assert summarize_stream_offer_lifecycle_explanation_history(hub) == history_before_plan


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
