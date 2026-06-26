"""Tests for RegistryHub-local stream offer lifecycle transition history."""

from __future__ import annotations

import json
from copy import deepcopy

from darwin.models.hub import RegistryHub, TrafficHub
from darwin.models.stream_offer import (
    StreamOffer,
    StreamOfferStatus,
    StreamOfferStatusTransition,
    make_stream_offer,
)
from darwin.registry.stream_offers import (
    hold_stream_offer,
    make_stream_offer_status_transition,
    query_stream_offer_status_transitions,
    record_stream_offer_status_transition,
    summarize_stream_offer_status_transitions,
    update_held_stream_offer_status,
)
from darwin.sim.world import World


def test_registry_hub_lifecycle_history_defaults_empty():
    hub = _hub()

    assert hub.stream_offer_status_transition_history == []


def test_transition_records_can_be_retained_on_registry_hub():
    hub = _hub()
    metadata = {"labels": ("manual",), "count": 1}

    transition = record_stream_offer_status_transition(
        hub,
        make_stream_offer_status_transition(
            offer_id="offer_001",
            previous_status="held",
            new_status="discoverable",
            reason="status_updated",
            hub_id=hub.hub_id,
            actor_id="ops_local",
            request_id="request_001",
            metadata=metadata,
            sequence=0,
        ),
    )

    assert hub.stream_offer_status_transition_history == [transition]
    assert transition.previous_status == StreamOfferStatus("held")
    assert transition.new_status == StreamOfferStatus("discoverable")
    assert transition.metadata == {"labels": ["manual"], "count": 1}
    assert metadata == {"labels": ("manual",), "count": 1}


def test_query_transition_history_uses_additive_filters():
    hub = _hub()
    first = _record_transition(
        hub,
        offer_id="offer_001",
        previous_status="held",
        new_status="discoverable",
        reason="status_updated",
        actor_id="ops_local",
        request_id="request_001",
        sequence=0,
    )
    second = _record_transition(
        hub,
        offer_id="offer_002",
        previous_status="discoverable",
        new_status="expired",
        reason="expired",
        sequence=1,
    )
    third = _record_transition(
        hub,
        offer_id="offer_001",
        previous_status="discoverable",
        new_status="denied",
        reason="manual_deny",
        hub_id="registry_remote_001",
        actor_id="ops_remote",
        sequence=2,
    )

    assert query_stream_offer_status_transitions(hub, offer_id="offer_001") == [
        first,
        third,
    ]
    assert query_stream_offer_status_transitions(hub, hub_id=hub.hub_id) == [
        first,
        second,
    ]
    assert query_stream_offer_status_transitions(hub, previous_status="held") == [
        first
    ]
    assert query_stream_offer_status_transitions(hub, new_status="expired") == [
        second
    ]
    assert query_stream_offer_status_transitions(hub, status="discoverable") == [
        first,
        second,
        third,
    ]
    assert query_stream_offer_status_transitions(hub, reason="manual_deny") == [
        third
    ]
    assert query_stream_offer_status_transitions(hub, actor_id="ops_local") == [
        first
    ]
    assert query_stream_offer_status_transitions(hub, request_id="request_001") == [
        first
    ]
    assert query_stream_offer_status_transitions(
        hub,
        offer_id="offer_001",
        reason="expired",
    ) == []


def test_transition_summaries_are_deterministic_json_safe_and_copied():
    hub = _hub()
    _record_transition(
        hub,
        offer_id="offer_001",
        previous_status="held",
        new_status="discoverable",
        reason="status_updated",
        metadata={"labels": ("demo",)},
        sequence=0,
    )

    summary = summarize_stream_offer_status_transitions(hub)
    summary[0]["metadata"]["labels"].append("mutated")

    assert summarize_stream_offer_status_transitions(hub) == [
        {
            "offer_id": "offer_001",
            "previous_status": "held",
            "new_status": "discoverable",
            "reason": "status_updated",
            "hub_id": "registry_chat_001",
            "actor_id": None,
            "request_id": None,
            "metadata": {"labels": ["demo"]},
            "sequence": 0,
        }
    ]
    json.dumps(summary, sort_keys=True)


def test_lifecycle_history_helpers_do_not_mutate_held_offers_or_traffic_hub():
    registry_hub = _hub()
    traffic_hub = TrafficHub(hub_id="traffic_chat_001")
    traffic_before = deepcopy(traffic_hub)
    held = hold_stream_offer(registry_hub, _offer(offer_id="offer_001"))
    held_before = [offer.to_summary() for offer in registry_hub.held_stream_offers]

    record_stream_offer_status_transition(
        registry_hub,
        make_stream_offer_status_transition(
            offer_id=held.offer_id,
            previous_status=held.status,
            new_status="discoverable",
            reason="status_updated",
            hub_id=registry_hub.hub_id,
        ),
    )
    query_stream_offer_status_transitions(registry_hub)
    summarize_stream_offer_status_transitions(registry_hub)

    assert [offer.to_summary() for offer in registry_hub.held_stream_offers] == (
        held_before
    )
    assert registry_hub.message_inboxes == {}
    assert registry_hub.message_delivery_results == []
    assert traffic_hub == traffic_before


def test_update_held_stream_offer_status_remains_compatible_by_default():
    hub = _hub()
    hold_stream_offer(hub, _offer(offer_id="offer_001", status="held"))

    updated = update_held_stream_offer_status(
        hub,
        "offer_001",
        "accepted",
        metadata={"accepted_by": "ops_local"},
    )

    assert updated.status == StreamOfferStatus("accepted")
    assert updated.metadata["accepted_by"] == "ops_local"
    assert hub.held_stream_offers == [updated]
    assert hub.stream_offer_status_transition_history == []


def test_update_held_stream_offer_status_can_record_transition_when_requested():
    hub = _hub()
    hold_stream_offer(hub, _offer(offer_id="offer_001", status="held"))

    updated = update_held_stream_offer_status(
        hub,
        "offer_001",
        "denied",
        record_transition=True,
        transition_reason="manual_deny",
        actor_id="ops_local",
        request_id="request_001",
        transition_metadata={"source": "manual_review"},
        transition_sequence=3,
    )

    assert updated.status == StreamOfferStatus("denied")
    assert summarize_stream_offer_status_transitions(hub) == [
        {
            "offer_id": "offer_001",
            "previous_status": "held",
            "new_status": "denied",
            "reason": "manual_deny",
            "hub_id": "registry_chat_001",
            "actor_id": "ops_local",
            "request_id": "request_001",
            "metadata": {"source": "manual_review"},
            "sequence": 3,
        }
    ]


def test_compact_world_snapshot_remains_unchanged_and_detailed_history_is_copied():
    world = World()
    hub = world.create_registry_hub(
        hub_id="registry_chat_001",
        scope_path="global.chat",
    )
    hold_stream_offer(hub, _offer(offer_id="offer_001", status="held"))
    _record_transition(
        hub,
        offer_id="offer_001",
        previous_status="held",
        new_status="discoverable",
        reason="status_updated",
        metadata={"labels": ("demo",)},
        sequence=0,
    )

    compact = world.snapshot()
    detailed = world.snapshot(detailed=True)
    hub_snapshot = detailed["registry_hubs"]["registry_chat_001"]
    hub_snapshot["stream_offer_status_transition_history"][0]["metadata"][
        "labels"
    ].append("mutated")

    fresh = world.snapshot(detailed=True)["registry_hubs"]["registry_chat_001"]

    assert compact == {
        "time": 0,
        "devices": [],
        "registry_hubs": ["registry_chat_001"],
        "traffic_hubs": [],
        "lanes": [],
    }
    assert "stream_offer_status_transition_history" not in compact
    assert hub_snapshot["held_stream_offers"][0]["offer_id"] == "offer_001"
    assert fresh["stream_offer_status_transition_history"][0]["metadata"] == {
        "labels": ["demo"]
    }


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
    hub_id: str | None = None,
    actor_id: str | None = None,
    request_id: str | None = None,
    metadata: dict[str, object] | None = None,
    sequence: int | None = None,
) -> StreamOfferStatusTransition:
    return record_stream_offer_status_transition(
        hub,
        make_stream_offer_status_transition(
            offer_id=offer_id,
            previous_status=previous_status,
            new_status=new_status,
            reason=reason,
            hub_id=hub.hub_id if hub_id is None else hub_id,
            actor_id=actor_id,
            request_id=request_id,
            metadata=metadata,
            sequence=sequence,
        ),
    )
