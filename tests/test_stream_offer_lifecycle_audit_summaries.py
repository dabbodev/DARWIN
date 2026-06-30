"""Tests for grouped stream offer lifecycle audit summary helpers."""

from __future__ import annotations

import json
from copy import deepcopy

from darwin.models import (
    RegistryHub,
    StreamOffer,
    StreamOfferLifecycleAuditSummary,
    StreamOfferLifecycleExplanation,
    StreamOfferStatusTransition,
    make_stream_offer,
)
from darwin.registry import (
    hold_stream_offer,
    make_stream_offer_status_transition,
    record_stream_offer_status_transition,
    summarize_stream_offer_lifecycle_audit,
    summarize_stream_offer_lifecycle_audit_by_offer,
    summarize_stream_offer_lifecycle_audit_by_reason,
    summarize_stream_offer_status_transitions,
)


def test_lifecycle_audit_groups_transition_history():
    hub = _hub()
    _record_transition(
        hub,
        offer_id="offer_b",
        previous_status="held",
        new_status="expired",
        reason="expired",
    )
    _record_transition(
        hub,
        offer_id="offer_a",
        previous_status="held",
        new_status="denied",
        reason="manual_deny",
    )
    _record_transition(
        hub,
        offer_id="offer_a",
        previous_status="denied",
        new_status="quarantined",
        reason="manual_quarantine",
    )

    summary = summarize_stream_offer_lifecycle_audit(hub)

    assert isinstance(summary, StreamOfferLifecycleAuditSummary)
    assert summary.total_transitions == 3
    assert summary.explanation_count == 0
    assert summary.by_offer_id == {"offer_a": 2, "offer_b": 1}
    assert summary.by_status == {"denied": 1, "expired": 1, "quarantined": 1}
    assert summary.by_reason == {
        "expired": 1,
        "manual_deny": 1,
        "manual_quarantine": 1,
    }
    assert summary.by_category == {}
    assert summarize_stream_offer_lifecycle_audit_by_offer(hub) == {
        "offer_a": 2,
        "offer_b": 1,
    }
    assert summarize_stream_offer_lifecycle_audit_by_reason(hub) == {
        "expired": 1,
        "manual_deny": 1,
        "manual_quarantine": 1,
    }


def test_lifecycle_audit_can_include_explanation_grouping():
    hub = _hub()
    _record_transition(
        hub,
        offer_id="offer_x",
        previous_status="held",
        new_status="expired",
        reason="expired",
    )
    explanations = (
        StreamOfferLifecycleExplanation(
            hub_id=hub.hub_id,
            offer_id="offer_x",
            category="active",
            reason="active_by_plan",
            status="active",
            checked_at=4,
            source="lifecycle_plan",
        ),
        StreamOfferLifecycleExplanation(
            hub_id=hub.hub_id,
            offer_id="offer_y",
            category="skipped",
            reason="skipped_by_result",
            status="skipped",
            checked_at=4,
            source="lifecycle_apply_result",
        ),
    )

    summary = summarize_stream_offer_lifecycle_audit(
        hub,
        explanations=explanations,
    )

    assert summary.total_transitions == 1
    assert summary.explanation_count == 2
    assert summary.by_offer_id == {"offer_x": 2, "offer_y": 1}
    assert summary.by_status == {"active": 1, "expired": 1, "skipped": 1}
    assert summary.by_reason == {
        "active_by_plan": 1,
        "expired": 1,
        "skipped_by_result": 1,
    }
    assert summary.by_category == {"active": 1, "skipped": 1}
    assert summary.metadata["included_explanations"] is True


def test_lifecycle_audit_empty_inputs_return_deterministic_summary():
    hub = _hub()

    summary = summarize_stream_offer_lifecycle_audit(hub)

    assert summary.to_summary() == {
        "hub_id": "registry_chat_001",
        "total_transitions": 0,
        "by_offer_id": {},
        "by_status": {},
        "by_reason": {},
        "by_category": {},
        "explanation_count": 0,
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
            "included_explanations": False,
        },
    }
    assert summarize_stream_offer_lifecycle_audit_by_offer(hub) == {}
    assert summarize_stream_offer_lifecycle_audit_by_reason(hub) == {}
    json.dumps(summary.to_summary(), sort_keys=True)


def test_lifecycle_audit_group_ordering_is_deterministic():
    hub = _hub()
    _record_transition(
        hub,
        offer_id="offer_z",
        previous_status="held",
        new_status="quarantined",
        reason="manual_quarantine",
    )
    _record_transition(
        hub,
        offer_id="offer_a",
        previous_status="held",
        new_status="accepted",
        reason="status_updated",
    )
    explanations = (
        StreamOfferLifecycleExplanation(
            hub_id=hub.hub_id,
            offer_id="offer_m",
            category="terminal",
            reason="terminal_cleanup_candidate",
            status="cleanup_candidate",
        ),
        StreamOfferLifecycleExplanation(
            hub_id=hub.hub_id,
            offer_id="offer_b",
            category="applied",
            reason="applied_by_result",
            status="applied",
        ),
    )

    summary = summarize_stream_offer_lifecycle_audit(
        hub,
        explanations=explanations,
    )

    assert list(summary.by_offer_id or {}) == ["offer_a", "offer_b", "offer_m", "offer_z"]
    assert list(summary.by_status or {}) == [
        "accepted",
        "applied",
        "cleanup_candidate",
        "quarantined",
    ]
    assert list(summary.by_reason or {}) == [
        "applied_by_result",
        "manual_quarantine",
        "status_updated",
        "terminal_cleanup_candidate",
    ]
    assert list(summary.by_category or {}) == ["applied", "terminal"]


def test_lifecycle_audit_helpers_are_read_only_and_copied():
    hub = _hub()
    hold_stream_offer(hub, _offer(offer_id="offer_read_only", status="held"))
    _record_transition(
        hub,
        offer_id="offer_read_only",
        previous_status="held",
        new_status="expired",
        reason="expired",
        metadata={"labels": ("history",)},
    )
    held_before = deepcopy([offer.to_summary() for offer in hub.held_stream_offers])
    history_before = summarize_stream_offer_status_transitions(hub)

    summary = summarize_stream_offer_lifecycle_audit(
        hub,
        metadata={"labels": ("audit",)},
    )
    summary_dict = summary.to_summary()
    summary_dict["metadata"]["labels"].append("mutated")

    assert [offer.to_summary() for offer in hub.held_stream_offers] == held_before
    assert summarize_stream_offer_status_transitions(hub) == history_before
    assert len(hub.stream_offer_status_transition_history) == 1
    assert summarize_stream_offer_lifecycle_audit(
        hub,
        metadata={"labels": ("audit",)},
    ).metadata["labels"] == ["audit"]


def _hub() -> RegistryHub:
    return RegistryHub(hub_id="registry_chat_001", scope_path="global.chat")


def _offer(
    *,
    offer_id: str,
    status: str = "created",
) -> StreamOffer:
    offer = make_stream_offer(
        offer_id=offer_id,
        requester_id="dev_A9F3",
        target_handle="alias:neo",
        lane_signature="basic_messaging:v1",
        rendezvous_scope="global.chat",
    )
    if status == "created":
        return offer
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


def _record_transition(
    hub: RegistryHub,
    *,
    offer_id: str,
    previous_status: str,
    new_status: str,
    reason: str,
    metadata: dict[str, object] | None = None,
) -> StreamOfferStatusTransition:
    return record_stream_offer_status_transition(
        hub,
        make_stream_offer_status_transition(
            offer_id=offer_id,
            previous_status=previous_status,
            new_status=new_status,
            reason=reason,
            hub_id=hub.hub_id,
            metadata=metadata,
        ),
    )
