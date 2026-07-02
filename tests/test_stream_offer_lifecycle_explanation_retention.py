"""Tests for lifecycle explanation retention policy classification helpers."""

from __future__ import annotations

import json
from copy import deepcopy

from darwin.models import (
    RegistryHub,
    StreamOfferLifecycleExplanation,
    StreamOfferLifecycleExplanationRetentionDecision,
    StreamOfferLifecycleExplanationRetentionPolicy,
    make_stream_offer_lifecycle_explanation_retention_policy,
)
from darwin.registry import (
    classify_stream_offer_lifecycle_explanations_for_retention,
    record_stream_offer_lifecycle_explanations,
    summarize_stream_offer_lifecycle_explanation_history,
    summarize_stream_offer_lifecycle_explanation_retention_decision,
)


def test_retention_policy_classifies_kept_prune_candidate_and_ignored():
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

    assert isinstance(policy, StreamOfferLifecycleExplanationRetentionPolicy)
    assert isinstance(decision, StreamOfferLifecycleExplanationRetentionDecision)
    assert decision.kept_explanation_keys == (
        _key(0, explanations[0]),
    )
    assert decision.prune_candidate_explanation_keys == (
        _key(1, explanations[1]),
    )
    assert decision.ignored_explanation_keys == (
        _key(2, explanations[2]),
    )
    assert decision.by_decision_category == {
        "ignored": 1,
        "kept": 1,
        "prune_candidate": 1,
    }


def test_retention_category_reason_and_source_filters_are_deterministic():
    explanations = (
        _explanation(
            offer_id="offer_active",
            category="active",
            reason="active_by_plan",
            source="lifecycle_plan",
        ),
        _explanation(
            offer_id="offer_applied",
            category="applied",
            reason="applied_by_result",
            status="applied",
            source="lifecycle_apply_result",
        ),
        _explanation(
            offer_id="offer_missing",
            category="missing",
            reason="missing_by_result",
            status="missing",
            source="lifecycle_apply_result",
        ),
    )
    policy = make_stream_offer_lifecycle_explanation_retention_policy(
        policy_id="retention_policy_001",
        hub_id="registry_chat_001",
        retain_reasons=["active_by_plan"],
        prune_categories=["missing"],
        prune_sources=["lifecycle_apply_result"],
    )

    decision = classify_stream_offer_lifecycle_explanations_for_retention(
        explanations,
        policy,
    )

    assert decision.kept_explanation_keys == (
        _key(0, explanations[0]),
    )
    assert decision.prune_candidate_explanation_keys == (
        _key(1, explanations[1]),
        _key(2, explanations[2]),
    )
    assert decision.ignored_explanation_keys == ()


def test_retention_conflicting_filters_keep_by_documented_precedence():
    explanation = _explanation(
        offer_id="offer_conflict",
        category="active",
        reason="active_by_plan",
        source="lifecycle_plan",
    )
    policy = make_stream_offer_lifecycle_explanation_retention_policy(
        policy_id="retention_policy_001",
        hub_id="registry_chat_001",
        retain_categories=["active"],
        prune_reasons=["active_by_plan"],
        prune_sources=["lifecycle_plan"],
    )

    decision = classify_stream_offer_lifecycle_explanations_for_retention(
        (explanation,),
        policy,
    )

    assert decision.kept_explanation_keys == (_key(0, explanation),)
    assert decision.prune_candidate_explanation_keys == ()
    assert decision.metadata["filter_precedence"] == (
        "retain_filters_before_prune_filters"
    )


def test_retention_max_records_caps_kept_records_deterministically():
    explanations = (
        _explanation(offer_id="offer_001", category="active"),
        _explanation(offer_id="offer_002", category="terminal"),
        _explanation(offer_id="offer_003", category="applied", status="applied"),
    )
    policy = make_stream_offer_lifecycle_explanation_retention_policy(
        policy_id="retention_policy_001",
        hub_id="registry_chat_001",
        max_records=1,
    )

    decision = classify_stream_offer_lifecycle_explanations_for_retention(
        explanations,
        policy,
    )

    assert decision.kept_explanation_keys == (_key(0, explanations[0]),)
    assert decision.prune_candidate_explanation_keys == (
        _key(1, explanations[1]),
        _key(2, explanations[2]),
    )
    assert decision.metadata["max_records_applied"] is True


def test_retention_empty_inputs_produce_deterministic_empty_decision():
    policy = make_stream_offer_lifecycle_explanation_retention_policy(
        policy_id="retention_policy_001",
        hub_id="registry_chat_001",
        metadata={"labels": ("retention",)},
    )

    decision = classify_stream_offer_lifecycle_explanations_for_retention(
        (),
        policy,
    )
    summary = summarize_stream_offer_lifecycle_explanation_retention_decision(
        decision,
    )
    summary["metadata"]["filter_precedence"] = "mutated"

    assert policy.metadata["labels"] == ["retention"]
    assert decision.to_summary() == {
        "hub_id": "registry_chat_001",
        "policy_id": "retention_policy_001",
        "kept_explanation_keys": [],
        "prune_candidate_explanation_keys": [],
        "ignored_explanation_keys": [],
        "by_decision_category": {
            "ignored": 0,
            "kept": 0,
            "prune_candidate": 0,
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
    json.dumps(summary, sort_keys=True)


def test_retention_classification_reads_explicit_history_without_mutating_it():
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

    decision = classify_stream_offer_lifecycle_explanations_for_retention(
        tuple(hub.stream_offer_lifecycle_explanation_history),
        policy,
    )

    assert decision.kept_explanation_keys == (_key(0, explanations[0]),)
    assert decision.prune_candidate_explanation_keys == (_key(1, explanations[1]),)
    assert summarize_stream_offer_lifecycle_explanation_history(hub) == history_before
    assert hub.stream_offer_lifecycle_explanation_history == list(explanations)


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
