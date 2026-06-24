"""Tests for explicit stream offer lifecycle plan application."""

from __future__ import annotations

import json
from copy import deepcopy

import pytest

from darwin.models import (
    RegistryHub,
    StreamOffer,
    StreamOfferLifecycleApplyResult,
    StreamOfferLifecyclePlan,
    make_stream_offer,
)
from darwin.registry import (
    apply_stream_offer_lifecycle_plan,
    hold_stream_offer,
    plan_stream_offer_expiration,
    summarize_stream_offer_lifecycle_apply_result,
    summarize_stream_offer_status_transitions,
)
from darwin.sim.world import World


def test_applying_plan_is_explicit_and_mutates_only_eligible_planned_offers():
    hub = _hub()
    hold_stream_offer(hub, _offer(offer_id="offer_planned", expires_order=2))
    hold_stream_offer(hub, _offer(offer_id="offer_unplanned", expires_order=2))
    hold_stream_offer(hub, _offer(offer_id="offer_terminal", status="accepted"))
    hold_stream_offer(hub, _offer(offer_id="offer_not_expired", expires_order=9))
    held_before = [offer.to_summary() for offer in hub.held_stream_offers]

    plan = StreamOfferLifecyclePlan(
        hub_id=hub.hub_id,
        checked_at=5,
        expired_offer_ids=(
            "offer_planned",
            "offer_terminal",
            "offer_missing",
            "offer_not_expired",
        ),
    )

    assert [offer.to_summary() for offer in hub.held_stream_offers] == held_before

    result = apply_stream_offer_lifecycle_plan(
        hub,
        plan,
        record_transition=False,
    )

    assert result == StreamOfferLifecycleApplyResult(
        hub_id=hub.hub_id,
        plan_checked_at=5,
        applied_offer_ids=("offer_planned",),
        skipped_offer_ids=("offer_terminal", "offer_not_expired"),
        missing_offer_ids=("offer_missing",),
        recorded_transition_count=0,
        metadata={
            "simulator_local": True,
            "explicit_apply": True,
            "planning_only": False,
            "registry_hub_mutated": True,
            "offer_statuses_mutated": True,
            "transitions_recorded": False,
            "offers_deleted": False,
            "delivery_behavior_changed": False,
            "traffic_hub_routing_changed": False,
            "networking": False,
        },
    )
    assert _status(hub, "offer_planned") == "expired"
    assert _status(hub, "offer_unplanned") == "held"
    assert _status(hub, "offer_terminal") == "accepted"
    assert _status(hub, "offer_not_expired") == "held"
    assert [offer.offer_id for offer in hub.held_stream_offers] == [
        "offer_planned",
        "offer_unplanned",
        "offer_terminal",
        "offer_not_expired",
    ]
    assert hub.stream_offer_status_transition_history == []


def test_read_only_planning_stays_read_only_until_apply_is_called():
    hub = _hub()
    hold_stream_offer(hub, _offer(offer_id="offer_001", expires_order=1))
    held_before = deepcopy([offer.to_summary() for offer in hub.held_stream_offers])

    plan = plan_stream_offer_expiration(hub, checked_at=1)

    assert [offer.to_summary() for offer in hub.held_stream_offers] == held_before
    assert hub.stream_offer_status_transition_history == []

    apply_stream_offer_lifecycle_plan(hub, plan, record_transition=False)

    assert _status(hub, "offer_001") == "expired"
    assert hub.stream_offer_status_transition_history == []


def test_applying_with_transition_recording_creates_expired_transition():
    hub = _hub()
    hold_stream_offer(hub, _offer(offer_id="offer_001", expires_order=3))
    plan = plan_stream_offer_expiration(hub, checked_at=4)

    result = apply_stream_offer_lifecycle_plan(
        hub,
        plan,
        actor_id="ops_local",
        request_id="request_001",
        transition_metadata={"source": "lifecycle_apply"},
    )

    assert result.applied_offer_ids == ("offer_001",)
    assert result.recorded_transition_count == 1
    assert summarize_stream_offer_status_transitions(hub) == [
        {
            "offer_id": "offer_001",
            "previous_status": "held",
            "new_status": "expired",
            "reason": "expired",
            "hub_id": hub.hub_id,
            "actor_id": "ops_local",
            "request_id": "request_001",
            "metadata": {"source": "lifecycle_apply"},
            "sequence": None,
        }
    ]


def test_applying_without_transition_recording_does_not_create_history():
    hub = _hub()
    hold_stream_offer(hub, _offer(offer_id="offer_001", expires_order=3))
    plan = plan_stream_offer_expiration(hub, checked_at=4)

    result = apply_stream_offer_lifecycle_plan(
        hub,
        plan,
        record_transition=False,
    )

    assert _status(hub, "offer_001") == "expired"
    assert result.recorded_transition_count == 0
    assert hub.stream_offer_status_transition_history == []


def test_apply_result_summary_is_deterministic_json_safe_and_copied():
    result = StreamOfferLifecycleApplyResult(
        hub_id="registry_chat_001",
        plan_checked_at=5,
        applied_offer_ids=("offer_001",),
        skipped_offer_ids=("offer_terminal",),
        missing_offer_ids=("offer_missing",),
        recorded_transition_count=1,
        metadata={"labels": ("apply",), "count": 1},
    )

    summary = summarize_stream_offer_lifecycle_apply_result(result)
    summary["metadata"]["labels"].append("mutated")

    assert summarize_stream_offer_lifecycle_apply_result(result) == {
        "hub_id": "registry_chat_001",
        "plan_checked_at": 5,
        "applied_offer_ids": ["offer_001"],
        "skipped_offer_ids": ["offer_terminal"],
        "missing_offer_ids": ["offer_missing"],
        "recorded_transition_count": 1,
        "metadata": {"labels": ["apply"], "count": 1},
    }
    json.dumps(summary, sort_keys=True)


def test_apply_rejects_wrong_hub_plan_and_invalid_metadata():
    hub = _hub()
    plan = StreamOfferLifecyclePlan(hub_id="registry_other", checked_at=0)

    with pytest.raises(ValueError, match="hub_id"):
        apply_stream_offer_lifecycle_plan(hub, plan)

    matching_plan = StreamOfferLifecyclePlan(hub_id=hub.hub_id, checked_at=0)
    with pytest.raises(TypeError, match="JSON-safe"):
        apply_stream_offer_lifecycle_plan(hub, matching_plan, metadata={"bad": object()})


def test_applying_plan_does_not_change_compact_world_snapshot_or_delivery_state():
    world = World()
    hub = world.create_registry_hub(
        hub_id="registry_chat_001",
        scope_path="global.chat",
    )
    hold_stream_offer(hub, _offer(offer_id="offer_001", expires_order=1))
    compact_before = world.snapshot()
    plan = plan_stream_offer_expiration(hub, checked_at=1)

    apply_stream_offer_lifecycle_plan(hub, plan)

    assert world.snapshot() == compact_before
    assert _status(hub, "offer_001") == "expired"
    assert len(hub.held_stream_offers) == 1
    assert hub.message_inboxes == {}
    assert hub.message_delivery_results == []


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


def _status(hub: RegistryHub, offer_id: str) -> str:
    for offer in hub.held_stream_offers:
        if offer.offer_id == offer_id:
            return offer.status.status
    raise AssertionError(f"missing offer: {offer_id}")
