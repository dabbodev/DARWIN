"""Tests for read-only stream offer lifecycle planning helpers."""

from __future__ import annotations

import json
from copy import deepcopy

import pytest

from darwin.models import (
    RegistryHub,
    StreamOffer,
    StreamOfferLifecyclePlan,
    make_stream_offer,
)
from darwin.registry import (
    hold_stream_offer,
    plan_stream_offer_expiration,
    query_expired_held_stream_offers,
    summarize_stream_offer_lifecycle_plan,
)
from darwin.sim.world import World


def test_expired_offers_are_identified_from_explicit_order():
    hub = _hub()
    expired = hold_stream_offer(
        hub,
        _offer(offer_id="offer_expired_by_order", status="held", expires_order=10),
    )
    hold_stream_offer(
        hub,
        _offer(offer_id="offer_active", status="discoverable", expires_order=11),
    )

    assert query_expired_held_stream_offers(hub, checked_at=10) == [expired]

    plan = plan_stream_offer_expiration(hub, checked_at=10)

    assert plan == StreamOfferLifecyclePlan(
        hub_id="registry_chat_001",
        checked_at=10,
        expired_offer_ids=("offer_expired_by_order",),
        cleanup_candidate_offer_ids=("offer_expired_by_order",),
        active_offer_ids=("offer_active",),
        metadata={
            "simulator_local": True,
            "read_only": True,
            "planning_only": True,
            "registry_hub_mutated": False,
            "offer_mutated": False,
            "transitions_recorded": False,
            "offers_deleted": False,
            "delivery_behavior_changed": False,
            "traffic_hub_routing_changed": False,
            "networking": False,
        },
    )


def test_terminal_offers_are_cleanup_candidates_not_fresh_expirations():
    hub = _hub()
    hold_stream_offer(hub, _offer(offer_id="offer_accepted", status="accepted"))
    hold_stream_offer(hub, _offer(offer_id="offer_already_expired", status="expired"))
    hold_stream_offer(
        hub,
        _offer(offer_id="offer_active_expired", status="held", expires_order=4),
    )

    plan = plan_stream_offer_expiration(hub, checked_at=5)

    assert plan.expired_offer_ids == ("offer_active_expired",)
    assert plan.cleanup_candidate_offer_ids == (
        "offer_accepted",
        "offer_already_expired",
        "offer_active_expired",
    )
    assert query_expired_held_stream_offers(hub, checked_at=5) == [
        hub.held_stream_offers[2]
    ]


def test_lifecycle_planning_is_read_only_by_default():
    world = World()
    hub = world.create_registry_hub(
        hub_id="registry_chat_001",
        scope_path="global.chat",
    )
    hold_stream_offer(hub, _offer(offer_id="offer_001", status="held", expires_order=1))
    held_before = deepcopy([offer.to_summary() for offer in hub.held_stream_offers])
    compact_before = world.snapshot()

    query_expired_held_stream_offers(hub, checked_at=1)
    plan_stream_offer_expiration(hub, checked_at=1)

    assert [offer.to_summary() for offer in hub.held_stream_offers] == held_before
    assert hub.stream_offer_status_transition_history == []
    assert hub.message_inboxes == {}
    assert hub.message_delivery_results == []
    assert world.snapshot() == compact_before
    assert "stream_offer_lifecycle_plan" not in world.snapshot()


def test_lifecycle_plan_summary_is_deterministic_json_safe_and_copied():
    hub = _hub()
    hold_stream_offer(hub, _offer(offer_id="offer_001", status="held", expires_order=2))

    plan = plan_stream_offer_expiration(
        hub,
        checked_at=3,
        metadata={"labels": ("cleanup",), "count": 1},
    )
    summary = summarize_stream_offer_lifecycle_plan(plan)
    summary["metadata"]["labels"].append("mutated")

    assert summarize_stream_offer_lifecycle_plan(plan) == {
        "hub_id": "registry_chat_001",
        "checked_at": 3,
        "expired_offer_ids": ["offer_001"],
        "cleanup_candidate_offer_ids": ["offer_001"],
        "active_offer_ids": [],
        "ignored_offer_ids": [],
        "metadata": {
            "simulator_local": True,
            "read_only": True,
            "planning_only": True,
            "registry_hub_mutated": False,
            "offer_mutated": False,
            "transitions_recorded": False,
            "offers_deleted": False,
            "delivery_behavior_changed": False,
            "traffic_hub_routing_changed": False,
            "networking": False,
            "labels": ["cleanup"],
            "count": 1,
        },
    }
    json.dumps(summary, sort_keys=True)


def test_lifecycle_planning_rejects_invalid_explicit_order_and_metadata():
    hub = _hub()

    with pytest.raises(ValueError, match="checked_at"):
        plan_stream_offer_expiration(hub, checked_at=-1)

    with pytest.raises(TypeError, match="JSON-safe"):
        plan_stream_offer_expiration(
            hub,
            checked_at=0,
            metadata={"bad": object()},
        )


def _hub() -> RegistryHub:
    return RegistryHub(hub_id="registry_chat_001", scope_path="global.chat")


def _offer(
    *,
    offer_id: str,
    status: str = "created",
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
