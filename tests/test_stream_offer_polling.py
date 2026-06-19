import inspect
import json
from copy import deepcopy

import pytest

import darwin.registry.stream_offers as stream_offer_registry
from darwin.models import (
    RegistryHub,
    RendezvousPollResult,
    RendezvousPollStatus,
    StreamOffer,
    TrafficHub,
    is_stream_offer_discoverable_to_request,
    make_rendezvous_request,
    make_stream_offer,
    stream_offer_matches_rendezvous_request,
)
from darwin.registry import (
    hold_stream_offer,
    mark_stream_offers_discoverable,
    poll_held_stream_offers,
)


def test_poll_empty_parent_hub_returns_empty_result():
    hub = _hub()
    request = _request()

    result = poll_held_stream_offers(hub, request)

    assert result == RendezvousPollResult(
        request_id="poll_req_001",
        polling_hub_id="hub_private_child",
        parent_hub_id="registry_chat_001",
        target_scope="global.chat",
        visibility_tier=1,
        matched_offer_ids=[],
        matched_offers=[],
        status=RendezvousPollStatus("empty"),
        reason="no_discoverable_offers",
        metadata={
            "simulator_local": True,
            "read_only": True,
            "delivery_behavior_changed": False,
            "networking": False,
        },
    )
    assert result.matched_count == 0


def test_poll_finds_held_offer_matching_target_scope():
    hub = _hub()
    stored = hold_stream_offer(hub, _offer(offer_id="offer_001"))

    result = poll_held_stream_offers(hub, _request(target_scope="global.chat"))

    assert result.status == RendezvousPollStatus("matched")
    assert result.reason == "offers_available"
    assert result.matched_offer_ids == ("offer_001",)
    assert result.matched_offers == (stored,)


def test_poll_preserves_held_offer_append_order():
    hub = _hub()
    for offer_id in ("offer_001", "offer_002", "offer_003"):
        hold_stream_offer(hub, _offer(offer_id=offer_id))

    result = poll_held_stream_offers(hub, _request())

    assert list(result.matched_offer_ids) == [
        "offer_001",
        "offer_002",
        "offer_003",
    ]


def test_poll_visibility_tier_matching_uses_request_tier_as_maximum():
    hub = _hub()
    hold_stream_offer(hub, _offer(offer_id="public_offer", visibility_tier=0))
    hold_stream_offer(hub, _offer(offer_id="authenticated_offer", visibility_tier=2))
    hold_stream_offer(hub, _offer(offer_id="trusted_offer", visibility_tier=3))

    result = poll_held_stream_offers(hub, _request(visibility_tier=2))

    assert list(result.matched_offer_ids) == [
        "public_offer",
        "authenticated_offer",
    ]


def test_poll_rendezvous_scope_matching_allows_unscoped_offers_only_as_wildcards():
    hub = _hub()
    hold_stream_offer(hub, _offer(offer_id="matching", rendezvous_scope="global.chat"))
    hold_stream_offer(hub, _offer(offer_id="unscoped", rendezvous_scope=None))
    hold_stream_offer(hub, _offer(offer_id="other", rendezvous_scope="global.remote"))

    result = poll_held_stream_offers(hub, _request(target_scope="global.chat"))

    assert list(result.matched_offer_ids) == ["matching", "unscoped"]


def test_poll_lane_signature_filter():
    hub = _hub()
    hold_stream_offer(hub, _offer(offer_id="message", lane_signature="basic_messaging:v1"))
    hold_stream_offer(hub, _offer(offer_id="control", lane_signature="control:v1"))

    result = poll_held_stream_offers(
        hub,
        _request(),
        lane_signature="control:v1",
    )

    assert list(result.matched_offer_ids) == ["control"]


def test_poll_requested_mode_filter():
    hub = _hub()
    hold_stream_offer(hub, _offer(offer_id="message", requested_mode="message"))
    hold_stream_offer(hub, _offer(offer_id="stream", requested_mode="stream"))

    result = poll_held_stream_offers(hub, _request(), requested_mode="stream")

    assert list(result.matched_offer_ids) == ["stream"]


def test_poll_active_only_excludes_terminal_offers():
    hub = _hub()
    hold_stream_offer(hub, _offer(offer_id="active", status="held"))
    hold_stream_offer(hub, _offer(offer_id="denied", status="denied"))

    result = poll_held_stream_offers(hub, _request())

    assert list(result.matched_offer_ids) == ["active"]


def test_poll_current_order_excludes_expired_offers_when_active_only():
    hub = _hub()
    hold_stream_offer(hub, _offer(offer_id="active", expires_order=20))
    hold_stream_offer(hub, _offer(offer_id="expired_by_order", expires_order=10))

    result = poll_held_stream_offers(hub, _request(), current_order=10)

    assert list(result.matched_offer_ids) == ["active"]


def test_poll_can_include_terminal_and_expired_offers_when_active_only_false():
    hub = _hub()
    hold_stream_offer(hub, _offer(offer_id="active", expires_order=20))
    hold_stream_offer(hub, _offer(offer_id="expired_by_order", expires_order=10))
    hold_stream_offer(hub, _offer(offer_id="denied", status="denied"))

    result = poll_held_stream_offers(
        hub,
        _request(),
        active_only=False,
        current_order=10,
    )

    assert list(result.matched_offer_ids) == [
        "active",
        "expired_by_order",
        "denied",
    ]


def test_poll_is_read_only_and_does_not_mutate_held_offers():
    hub = _hub()
    hold_stream_offer(hub, _offer(offer_id="offer_001", status="held"))
    before = deepcopy([offer.to_summary() for offer in hub.held_stream_offers])

    result = poll_held_stream_offers(hub, _request())
    result.to_summary()["matched_offers"][0]["metadata"]["polled"] = True

    assert [offer.to_summary() for offer in hub.held_stream_offers] == before


def test_poll_result_summary_is_json_safe():
    hub = _hub()
    hold_stream_offer(
        hub,
        _offer(offer_id="offer_001", metadata={"labels": ("demo",)}),
    )

    summary = poll_held_stream_offers(hub, _request()).to_summary()

    assert summary["matched_count"] == 1
    assert summary["matched_offers"][0]["metadata"] == {"labels": ["demo"]}
    json.dumps(summary)


def test_poll_missing_parent_hub_returns_invalid_request_result():
    result = poll_held_stream_offers(None, _request())

    assert result.status == RendezvousPollStatus("invalid_request")
    assert result.reason == "hub_missing"
    assert result.parent_hub_id == "hub_missing"
    assert result.matched_offer_ids == ()


def test_poll_rejects_non_rendezvous_request():
    with pytest.raises(TypeError, match="RendezvousRequest"):
        poll_held_stream_offers(_hub(), object())  # type: ignore[arg-type]


def test_poll_reports_scope_mismatch_when_visible_offers_exist_elsewhere():
    hub = _hub()
    hold_stream_offer(hub, _offer(offer_id="remote", rendezvous_scope="global.remote"))

    result = poll_held_stream_offers(hub, _request(target_scope="global.chat"))

    assert result.status == RendezvousPollStatus("empty")
    assert result.reason == "scope_mismatch"


def test_pure_predicates_match_request_scope_visibility_and_activity():
    request = _request(target_scope="global.chat", visibility_tier=2)
    matching = _offer(offer_id="matching", visibility_tier=2)
    too_private = _offer(offer_id="private", visibility_tier=3)
    wrong_scope = _offer(offer_id="wrong_scope", rendezvous_scope="global.remote")
    terminal = _offer(offer_id="terminal", status="denied")

    assert stream_offer_matches_rendezvous_request(matching, request) is True
    assert is_stream_offer_discoverable_to_request(matching, request) is True
    assert stream_offer_matches_rendezvous_request(too_private, request) is False
    assert stream_offer_matches_rendezvous_request(wrong_scope, request) is False
    assert stream_offer_matches_rendezvous_request(terminal, request) is True
    assert is_stream_offer_discoverable_to_request(terminal, request) is False


def test_mark_stream_offers_discoverable_updates_selected_offers_in_order():
    hub = _hub()
    hold_stream_offer(hub, _offer(offer_id="offer_001", metadata={"count": 1}))
    hold_stream_offer(hub, _offer(offer_id="offer_002"))
    hold_stream_offer(hub, _offer(offer_id="offer_003"))

    updated = mark_stream_offers_discoverable(
        hub,
        ["offer_003", "offer_001"],
        metadata={"marked": True, "labels": ("pollable",)},
    )

    assert [offer.offer_id for offer in updated] == ["offer_001", "offer_003"]
    assert [offer.status.status for offer in updated] == [
        "discoverable",
        "discoverable",
    ]
    assert updated[0].metadata == {
        "count": 1,
        "marked": True,
        "labels": ["pollable"],
    }
    assert [offer.offer_id for offer in hub.held_stream_offers] == [
        "offer_001",
        "offer_002",
        "offer_003",
    ]


def test_poll_and_discoverable_marking_do_not_deliver_or_mutate_traffic_hub():
    registry_hub = _hub()
    traffic_hub = TrafficHub(hub_id="traffic_chat_001")
    traffic_before = deepcopy(traffic_hub)
    hold_stream_offer(registry_hub, _offer(offer_id="offer_001"))

    poll_held_stream_offers(registry_hub, _request())
    mark_stream_offers_discoverable(registry_hub, ["offer_001"])

    assert registry_hub.message_inboxes == {}
    assert registry_hub.message_delivery_results == []
    assert traffic_hub == traffic_before


def test_stream_offer_polling_does_not_import_networking_dns_or_socket_libraries():
    source = inspect.getsource(stream_offer_registry)

    assert "import socket" not in source
    assert "import http" not in source
    assert "import urllib" not in source
    assert "import requests" not in source
    assert "getaddrinfo" not in source
    assert "websocket" not in source.lower()


def _hub() -> RegistryHub:
    return RegistryHub(hub_id="registry_chat_001", scope_path="global.chat")


def _request(
    *,
    target_scope: str = "global.chat",
    visibility_tier: int = 1,
):
    return make_rendezvous_request(
        request_id="poll_req_001",
        offer_id="offer_probe",
        polling_hub_id="hub_private_child",
        requester_id="hub_private_child",
        target_scope=target_scope,
        visibility_tier=visibility_tier,
        metadata={"reason": "private_poll"},
    )


def _offer(
    *,
    offer_id: str,
    requester_id: str = "dev_A9F3",
    target_handle: str = "alias:neo",
    lane_signature: str = "basic_messaging:v1",
    requested_mode: str = "message",
    visibility_tier: int = 1,
    status: str = "created",
    rendezvous_scope: str | None = "global.chat",
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
