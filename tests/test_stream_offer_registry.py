import inspect
import json
from copy import deepcopy

import pytest

import darwin.registry.stream_offers as stream_offer_registry
from darwin.models import (
    RegistryHub,
    StreamOffer,
    StreamOfferStatus,
    TrafficHub,
    make_stream_offer,
)
from darwin.registry import (
    get_held_stream_offer,
    hold_stream_offer,
    query_held_stream_offers,
    summarize_held_stream_offers,
    update_held_stream_offer_status,
)


def test_registry_hub_held_stream_offers_defaults_empty():
    hub = _hub()

    assert hub.held_stream_offers == []


def test_hold_stream_offer_appends_and_marks_created_offer_held():
    hub = _hub()
    offer = _offer(offer_id="offer_001", status="created")

    stored = hold_stream_offer(hub, offer)

    assert stored.status == StreamOfferStatus("held")
    assert stored.offer_id == "offer_001"
    assert hub.held_stream_offers == [stored]
    assert offer.status == StreamOfferStatus("created")


def test_hold_stream_offer_retains_non_created_status():
    hub = _hub()
    offer = _offer(offer_id="offer_001", status="discoverable")

    stored = hold_stream_offer(hub, offer)

    assert stored is offer
    assert stored.status == StreamOfferStatus("discoverable")


def test_duplicate_offer_id_is_rejected_by_default():
    hub = _hub()
    first = _offer(offer_id="offer_001")
    duplicate = _offer(offer_id="offer_001", requester_id="dev_B2C8")

    hold_stream_offer(hub, first)

    with pytest.raises(ValueError, match="already exists"):
        hold_stream_offer(hub, duplicate)

    assert [offer.requester_id for offer in hub.held_stream_offers] == ["dev_A9F3"]


def test_replace_existing_replaces_in_place_deterministically():
    hub = _hub()
    first = hold_stream_offer(hub, _offer(offer_id="offer_001"))
    second = hold_stream_offer(hub, _offer(offer_id="offer_002"))
    replacement = _offer(
        offer_id="offer_001",
        requester_id="dev_B2C8",
        status="discoverable",
        metadata={"replacement": True},
    )

    stored = hold_stream_offer(hub, replacement, replace_existing=True)

    assert stored == replacement
    assert hub.held_stream_offers == [replacement, second]
    assert first not in hub.held_stream_offers
    assert [offer.offer_id for offer in hub.held_stream_offers] == [
        "offer_001",
        "offer_002",
    ]


def test_get_held_stream_offer_returns_offer_or_none():
    hub = _hub()
    stored = hold_stream_offer(hub, _offer(offer_id="offer_001"))

    assert get_held_stream_offer(hub, "offer_001") == stored
    assert get_held_stream_offer(hub, "offer_missing") is None


def test_query_held_stream_offers_filters_by_offer_id():
    hub = _populated_hub()

    assert _ids(query_held_stream_offers(hub, offer_id="offer_002")) == ["offer_002"]
    assert query_held_stream_offers(hub, offer_id="offer_missing") == []


def test_query_held_stream_offers_filters_by_requester_id():
    hub = _populated_hub()

    assert _ids(query_held_stream_offers(hub, requester_id="dev_A9F3")) == [
        "offer_001",
        "offer_003",
    ]


def test_query_held_stream_offers_filters_by_target_handle():
    hub = _populated_hub()

    assert _ids(query_held_stream_offers(hub, target_handle="alias:trinity")) == [
        "offer_002"
    ]


def test_query_held_stream_offers_filters_by_lane_signature():
    hub = _populated_hub()

    assert _ids(query_held_stream_offers(hub, lane_signature="control:v1")) == [
        "offer_002"
    ]


def test_query_held_stream_offers_filters_by_requested_mode():
    hub = _populated_hub()

    assert _ids(query_held_stream_offers(hub, requested_mode="stream")) == [
        "offer_003"
    ]


def test_query_held_stream_offers_filters_by_visibility_tier():
    hub = _populated_hub()

    assert _ids(query_held_stream_offers(hub, visibility_tier=2)) == ["offer_002"]


def test_query_held_stream_offers_filters_by_status():
    hub = _populated_hub()

    assert _ids(query_held_stream_offers(hub, status="denied")) == ["offer_004"]


def test_query_held_stream_offers_filters_by_rendezvous_scope():
    hub = _populated_hub()

    assert _ids(query_held_stream_offers(hub, rendezvous_scope="global.remote")) == [
        "offer_002"
    ]


def test_query_held_stream_offers_uses_additive_filters():
    hub = _populated_hub()

    matches = query_held_stream_offers(
        hub,
        requester_id="dev_A9F3",
        target_handle="alias:neo",
        requested_mode="stream",
        visibility_tier=3,
        rendezvous_scope="global.chat",
        active_only=True,
    )

    assert _ids(matches) == ["offer_003"]
    assert (
        query_held_stream_offers(
            hub,
            requester_id="dev_A9F3",
            target_handle="alias:neo",
            requested_mode="control",
        )
        == []
    )


def test_query_held_stream_offers_active_only_filters_status_and_expiration():
    hub = _hub()
    active = hold_stream_offer(
        hub,
        _offer(offer_id="offer_active", status="held", expires_order=20),
    )
    expired_by_order = hold_stream_offer(
        hub,
        _offer(offer_id="offer_expired_by_order", status="held", expires_order=10),
    )
    terminal = hold_stream_offer(hub, _offer(offer_id="offer_denied", status="denied"))

    assert query_held_stream_offers(hub, active_only=True, current_order=10) == [
        active
    ]
    assert query_held_stream_offers(hub, active_only=False, current_order=10) == [
        expired_by_order,
        terminal,
    ]


def test_current_order_does_not_filter_without_active_only():
    hub = _hub()
    held = hold_stream_offer(
        hub,
        _offer(offer_id="offer_expired_by_order", status="held", expires_order=10),
    )

    assert query_held_stream_offers(hub, current_order=10) == [held]


def test_update_held_stream_offer_status_replaces_record_and_merges_metadata():
    hub = _hub()
    original = hold_stream_offer(
        hub,
        _offer(
            offer_id="offer_001",
            status="held",
            metadata={"labels": ("initial",), "count": 1},
        ),
    )
    metadata = {"labels": ("updated",), "extra": {"scope": "global.chat"}}

    updated = update_held_stream_offer_status(
        hub,
        "offer_001",
        "accepted",
        metadata=metadata,
    )

    assert updated.status == StreamOfferStatus("accepted")
    assert updated.metadata == {
        "labels": ["updated"],
        "count": 1,
        "extra": {"scope": "global.chat"},
    }
    assert hub.held_stream_offers == [updated]
    assert original.status == StreamOfferStatus("held")
    assert metadata == {"labels": ("updated",), "extra": {"scope": "global.chat"}}


def test_update_held_stream_offer_status_rejects_missing_and_invalid_status():
    hub = _hub()

    with pytest.raises(KeyError, match="not registered"):
        update_held_stream_offer_status(hub, "offer_missing", "accepted")

    hold_stream_offer(hub, _offer(offer_id="offer_001"))
    with pytest.raises(ValueError, match="stream offer status"):
        update_held_stream_offer_status(hub, "offer_001", "withdrawn")


def test_update_held_stream_offer_status_rejects_non_json_safe_metadata():
    hub = _hub()
    hold_stream_offer(hub, _offer(offer_id="offer_001"))

    with pytest.raises(TypeError, match="JSON-safe"):
        update_held_stream_offer_status(
            hub,
            "offer_001",
            "accepted",
            metadata={"bad": object()},
        )


def test_query_helpers_are_read_only():
    hub = _populated_hub()
    before = deepcopy([offer.to_summary() for offer in hub.held_stream_offers])

    result = query_held_stream_offers(hub, requester_id="dev_A9F3")
    result.clear()

    assert [offer.to_summary() for offer in hub.held_stream_offers] == before


def test_summarize_held_stream_offers_is_json_safe_and_copied():
    hub = _hub()
    hold_stream_offer(
        hub,
        _offer(offer_id="offer_001", metadata={"labels": ("demo",)}),
    )

    summary = summarize_held_stream_offers(hub)
    summary[0]["metadata"]["labels"].append("mutated")

    assert summarize_held_stream_offers(hub)[0]["metadata"] == {"labels": ["demo"]}
    json.dumps(summary)


def test_hold_and_query_do_not_deliver_or_mutate_traffic_hub():
    registry_hub = _hub()
    traffic_hub = TrafficHub(hub_id="traffic_chat_001")
    traffic_before = deepcopy(traffic_hub)

    hold_stream_offer(registry_hub, _offer(offer_id="offer_001"))
    query_held_stream_offers(registry_hub)
    update_held_stream_offer_status(registry_hub, "offer_001", "accepted")

    assert registry_hub.message_inboxes == {}
    assert registry_hub.message_delivery_results == []
    assert traffic_hub == traffic_before


def test_stream_offer_registry_does_not_import_networking_dns_or_socket_libraries():
    source = inspect.getsource(stream_offer_registry)

    assert "import socket" not in source
    assert "import http" not in source
    assert "import urllib" not in source
    assert "import requests" not in source
    assert "getaddrinfo" not in source
    assert "websocket" not in source.lower()


def _hub() -> RegistryHub:
    return RegistryHub(hub_id="registry_chat_001", scope_path="global.chat")


def _populated_hub() -> RegistryHub:
    hub = _hub()
    for offer in (
        _offer(offer_id="offer_001"),
        _offer(
            offer_id="offer_002",
            requester_id="dev_B2C8",
            target_handle="alias:trinity",
            lane_signature="control:v1",
            requested_mode="control",
            visibility_tier=2,
            rendezvous_scope="global.remote",
        ),
        _offer(
            offer_id="offer_003",
            requested_mode="stream",
            visibility_tier=3,
            expires_order=20,
        ),
        _offer(offer_id="offer_004", requester_id="dev_C7D1", status="denied"),
    ):
        hold_stream_offer(hub, offer)
    return hub


def _offer(
    *,
    offer_id: str,
    requester_id: str = "dev_A9F3",
    target_handle: str = "alias:neo",
    lane_signature: str = "basic_messaging:v1",
    requested_mode: str = "message",
    visibility_tier: int = 0,
    status: str = "created",
    rendezvous_scope: str = "global.chat",
    created_order: int = 0,
    expires_order: int | None = None,
    metadata: dict[str, object] | None = None,
) -> StreamOffer:
    offer = make_stream_offer(
        offer_id=offer_id,
        requester_id=requester_id,
        target_handle=target_handle,
        lane_signature=lane_signature,
        requested_mode=requested_mode,
        visibility_tier=visibility_tier,
        rendezvous_scope=rendezvous_scope,
        created_order=created_order,
        expires_order=expires_order,
        metadata=metadata,
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


def _ids(offers: list[StreamOffer]) -> list[str]:
    return [offer.offer_id for offer in offers]
