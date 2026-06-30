"""Tests for stream offer lifecycle explanation helpers."""

from __future__ import annotations

import json
from copy import deepcopy

from darwin.models import (
    RegistryHub,
    StreamOffer,
    StreamOfferLifecycleApplyResult,
    StreamOfferLifecycleExplanation,
    StreamOfferLifecyclePlan,
    make_stream_offer,
)
from darwin.registry import (
    apply_stream_offer_lifecycle_plan,
    explain_stream_offer_lifecycle_apply_result,
    explain_stream_offer_lifecycle_plan,
    hold_stream_offer,
    plan_stream_offer_expiration,
    summarize_stream_offer_lifecycle_explanations,
)


def test_lifecycle_plan_explanations_classify_plan_fields_deterministically():
    plan = StreamOfferLifecyclePlan(
        hub_id="registry_chat_001",
        checked_at=8,
        expired_offer_ids=("offer_expired",),
        cleanup_candidate_offer_ids=("offer_terminal", "offer_expired"),
        active_offer_ids=("offer_active",),
        ignored_offer_ids=("offer_ignored",),
    )

    explanations = explain_stream_offer_lifecycle_plan(plan)

    assert [
        (item.offer_id, item.category, item.reason, item.status)
        for item in explanations
    ] == [
        ("offer_expired", "expired", "expired_by_plan", "expired"),
        (
            "offer_terminal",
            "terminal",
            "terminal_cleanup_candidate",
            "cleanup_candidate",
        ),
        ("offer_active", "active", "active_by_plan", "active"),
        ("offer_ignored", "skipped", "ignored_by_plan", "ignored"),
    ]
    assert explanations[0].checked_at == 8
    assert explanations[0].source == "lifecycle_plan"
    assert explanations[0].details["cleanup_candidate"] is True
    assert explanations[1].details["plan_field"] == "cleanup_candidate_offer_ids"


def test_lifecycle_apply_result_explanations_classify_result_fields_in_order():
    result = StreamOfferLifecycleApplyResult(
        hub_id="registry_chat_001",
        plan_checked_at=5,
        applied_offer_ids=("offer_applied",),
        skipped_offer_ids=("offer_skipped",),
        missing_offer_ids=("offer_missing",),
        recorded_transition_count=1,
    )

    explanations = explain_stream_offer_lifecycle_apply_result(result)

    assert [
        (item.offer_id, item.category, item.reason, item.status)
        for item in explanations
    ] == [
        ("offer_applied", "applied", "applied_by_result", "applied"),
        ("offer_skipped", "skipped", "skipped_by_result", "skipped"),
        ("offer_missing", "missing", "missing_by_result", "missing"),
    ]
    assert explanations[0].checked_at == 5
    assert explanations[0].source == "lifecycle_apply_result"
    assert explanations[0].details["recorded_transition_count"] == 1


def test_lifecycle_explanations_are_read_only():
    hub = _hub()
    hold_stream_offer(hub, _offer(offer_id="offer_expired", expires_order=1))
    hold_stream_offer(hub, _offer(offer_id="offer_active", expires_order=9))
    hold_stream_offer(hub, _offer(offer_id="offer_terminal", status="accepted"))
    held_before = deepcopy([offer.to_summary() for offer in hub.held_stream_offers])
    history_before = list(hub.stream_offer_status_transition_history)

    plan = plan_stream_offer_expiration(hub, checked_at=5)
    plan_explanations = explain_stream_offer_lifecycle_plan(plan)
    result = apply_stream_offer_lifecycle_plan(hub, plan, record_transition=False)
    held_after_apply = deepcopy([offer.to_summary() for offer in hub.held_stream_offers])
    apply_explanations = explain_stream_offer_lifecycle_apply_result(result)

    assert [offer.to_summary() for offer in hub.held_stream_offers] == held_after_apply
    assert plan_explanations[0].offer_id == "offer_expired"
    assert apply_explanations[0].offer_id == "offer_expired"
    assert held_before[0]["status"] == "held"
    assert held_after_apply[0]["status"] == "expired"
    assert hub.stream_offer_status_transition_history == history_before


def test_lifecycle_explanation_summary_is_deterministic_json_safe_and_copied():
    explanations = (
        StreamOfferLifecycleExplanation(
            hub_id="registry_chat_001",
            offer_id="offer_001",
            category="active",
            reason="active_by_plan",
            status="active",
            checked_at=3,
            source="lifecycle_plan",
            details={"labels": ("inspect",)},
        ),
    )

    summary = summarize_stream_offer_lifecycle_explanations(explanations)
    summary[0]["details"]["labels"].append("mutated")

    assert summarize_stream_offer_lifecycle_explanations(explanations) == [
        {
            "hub_id": "registry_chat_001",
            "offer_id": "offer_001",
            "category": "active",
            "reason": "active_by_plan",
            "status": "active",
            "checked_at": 3,
            "source": "lifecycle_plan",
            "details": {"labels": ["inspect"]},
        }
    ]
    json.dumps(summary, sort_keys=True)


def _hub() -> RegistryHub:
    return RegistryHub(hub_id="registry_chat_001", scope_path="global.chat")


def _offer(
    *,
    offer_id: str,
    status: str = "held",
    created_order: int = 0,
    expires_order: int | None = None,
) -> StreamOffer:
    offer = make_stream_offer(
        offer_id=offer_id,
        requester_id="dev_A9F3",
        target_handle="alias:neo",
        lane_signature="basic_messaging:v1",
        rendezvous_scope="global.chat",
        created_order=created_order,
        expires_order=expires_order,
    )
    return StreamOffer(
        offer_id=offer.offer_id,
        requester_id=offer.requester_id,
        target_handle=offer.target_handle,
        lane_signature=offer.lane_signature,
        requested_mode=offer.requested_mode,
        visibility_tier=offer.visibility_tier,
        status=status,
        rendezvous_scope=offer.rendezvous_scope,
        created_order=offer.created_order,
        expires_order=offer.expires_order,
        metadata=offer.metadata,
    )
