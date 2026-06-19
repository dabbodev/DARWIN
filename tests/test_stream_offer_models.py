import inspect
import json
from copy import deepcopy
from dataclasses import fields

import pytest

import darwin.models.stream_offer as stream_offer_models
from darwin.models import (
    RegistryHub,
    RendezvousRequest,
    StreamOffer,
    StreamOfferMode,
    StreamOfferStatus,
    StreamOfferVisibility,
    is_stream_offer_active,
    is_stream_offer_expired,
    is_stream_offer_terminal,
    make_basic_messaging_stream_offer,
    make_rendezvous_request,
    make_stream_offer,
    parse_lane_signature,
    stream_offer_matches_lane,
)


def test_create_generic_stream_offer():
    offer = make_stream_offer(
        offer_id="offer_001",
        requester_id="dev_A9F3",
        target_handle="darwin://global.chat.neo/inbox",
        lane_signature=parse_lane_signature("basic_messaging:v1"),
        requested_mode="stream",
        visibility_tier=2,
        rendezvous_scope="global.chat",
        created_order=10,
        expires_order=20,
        metadata={"labels": ("rendezvous", "demo")},
    )

    assert offer == StreamOffer(
        offer_id="offer_001",
        requester_id="dev_A9F3",
        target_handle="darwin://global.chat.neo/inbox",
        lane_signature="basic_messaging:v1",
        requested_mode=StreamOfferMode("stream"),
        visibility_tier=StreamOfferVisibility(2),
        status=StreamOfferStatus("created"),
        rendezvous_scope="global.chat",
        created_order=10,
        expires_order=20,
        metadata={"labels": ["rendezvous", "demo"]},
    )
    assert offer.lane_signature == "basic_messaging:v1"
    assert offer.requested_mode.mode == "stream"
    assert offer.visibility_tier.tier == 2
    assert offer.status.status == "created"


def test_create_basic_messaging_stream_offer():
    offer = make_basic_messaging_stream_offer(
        offer_id="offer_basic_001",
        requester_id="dev_A9F3",
        target_handle="darwin://global.chat.neo/inbox",
        rendezvous_scope="global.chat",
        created_order=3,
    )

    assert offer.lane_signature == "basic_messaging:v1"
    assert offer.requested_mode == StreamOfferMode("message")
    assert offer.visibility_tier == StreamOfferVisibility(0)
    assert offer.status == StreamOfferStatus("created")
    assert offer.rendezvous_scope == "global.chat"
    assert offer.created_order == 3
    assert offer.expires_order is None
    assert offer.metadata == {
        "simulator_local": True,
        "request_only": True,
        "delivery_behavior_changed": False,
        "networking": False,
    }


def test_create_rendezvous_request():
    request = make_rendezvous_request(
        request_id="poll_req_001",
        offer_id="offer_001",
        polling_hub_id="hub_private_child",
        requester_id="hub_private_child",
        target_scope="global.chat",
        visibility_tier=1,
        metadata={"reason": "private_poll"},
    )

    assert request == RendezvousRequest(
        request_id="poll_req_001",
        offer_id="offer_001",
        polling_hub_id="hub_private_child",
        requester_id="hub_private_child",
        target_scope="global.chat",
        visibility_tier=StreamOfferVisibility(1),
        metadata={"reason": "private_poll"},
    )


def test_stream_offer_summary_is_json_safe():
    offer = make_stream_offer(
        offer_id="offer_001",
        requester_id="dev_A9F3",
        target_handle="alias:neo",
        lane_signature="basic_messaging:v1",
        requested_mode="message",
        visibility_tier=5,
        rendezvous_scope="global.chat",
        created_order=1,
        expires_order=9,
        metadata={"labels": ("private",), "attempt": 1},
    )

    summary = offer.to_summary()

    assert summary == {
        "offer_id": "offer_001",
        "requester_id": "dev_A9F3",
        "target_handle": "alias:neo",
        "lane_signature": "basic_messaging:v1",
        "requested_mode": "message",
        "visibility_tier": 5,
        "status": "created",
        "rendezvous_scope": "global.chat",
        "created_order": 1,
        "expires_order": 9,
        "metadata": {"labels": ["private"], "attempt": 1},
    }
    assert offer.to_dict() == summary
    json.dumps(summary)


def test_rendezvous_request_summary_is_json_safe():
    request = make_rendezvous_request(
        request_id="poll_req_001",
        offer_id="offer_001",
        polling_hub_id="hub_private_child",
        requester_id="hub_private_child",
        target_scope="global.chat",
        visibility_tier=3,
        metadata={"labels": ("scoped",)},
    )

    summary = request.to_summary()

    assert summary == {
        "request_id": "poll_req_001",
        "offer_id": "offer_001",
        "polling_hub_id": "hub_private_child",
        "requester_id": "hub_private_child",
        "target_scope": "global.chat",
        "visibility_tier": 3,
        "metadata": {"labels": ["scoped"]},
    }
    assert request.to_dict() == summary
    json.dumps(summary)


def test_default_status_and_mode_are_deterministic():
    offer = StreamOffer(
        offer_id="offer_default",
        requester_id="dev_A9F3",
        target_handle="alias:neo",
        lane_signature="basic_messaging:v1",
    )

    assert offer.requested_mode == StreamOfferMode("message")
    assert offer.status == StreamOfferStatus("created")
    assert offer.visibility_tier == StreamOfferVisibility(0)
    assert offer.created_order == 0
    assert offer.metadata == {}


def test_active_offer_predicate():
    for status in ("created", "held", "discoverable", "passed_down"):
        offer = _offer(status=status)
        assert is_stream_offer_active(offer) is True

    assert is_stream_offer_active(_offer(status="denied")) is False


def test_terminal_offer_predicate():
    for status in ("accepted", "denied", "expired", "rate_limited", "quarantined"):
        offer = _offer(status=status)
        assert is_stream_offer_terminal(offer) is True

    assert is_stream_offer_terminal(_offer(status="held")) is False


def test_expired_offer_predicate_uses_deterministic_order():
    offer = _offer(created_order=5, expires_order=10)

    assert is_stream_offer_expired(offer, current_order=9) is False
    assert is_stream_offer_expired(offer, current_order=10) is True
    assert is_stream_offer_expired(_offer(status="expired"), current_order=0) is True


def test_lane_match_predicate():
    offer = _offer(lane_signature="basic_messaging:v1")

    assert stream_offer_matches_lane(offer, "basic_messaging:v1") is True
    assert (
        stream_offer_matches_lane(offer, parse_lane_signature("basic_messaging:v1"))
        is True
    )
    assert stream_offer_matches_lane(offer, "control:v1") is False


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "basic_messaging",
        "basic:messaging:v1",
        "basic messaging:v1",
    ],
)
def test_malformed_lane_signatures_are_rejected(raw):
    with pytest.raises(ValueError):
        _offer(lane_signature=raw)


def test_visibility_tier_is_retained_as_simulator_metadata():
    offer = _offer(visibility_tier=4)
    request = make_rendezvous_request(
        request_id="poll_req_001",
        offer_id=offer.offer_id,
        polling_hub_id="hub_private_child",
        requester_id="hub_private_child",
        target_scope="global.chat",
        visibility_tier=4,
    )

    assert offer.visibility_tier.tier == 4
    assert offer.visibility_tier.label == "delegated_trusted"
    assert offer.to_summary()["visibility_tier"] == 4
    assert request.to_summary()["visibility_tier"] == 4


def test_helper_construction_is_pure_and_deterministic():
    metadata = {"labels": ["demo"]}
    offer = _offer(metadata=metadata)
    before = deepcopy(offer.to_summary())

    first = make_stream_offer(
        offer_id="offer_repeat",
        requester_id="dev_A9F3",
        target_handle="alias:neo",
        lane_signature="basic_messaging:v1",
        created_order=1,
        metadata=metadata,
    )
    second = make_stream_offer(
        offer_id="offer_repeat",
        requester_id="dev_A9F3",
        target_handle="alias:neo",
        lane_signature="basic_messaging:v1",
        created_order=1,
        metadata=metadata,
    )

    assert first == second
    assert offer.to_summary() == before
    assert metadata == {"labels": ["demo"]}


def test_construction_does_not_mutate_registry_hub_or_deliver_messages():
    hub = RegistryHub(hub_id="hub_chat_001", scope_path="global.chat")
    before = _hub_state(hub)

    make_basic_messaging_stream_offer(
        offer_id="offer_basic_001",
        requester_id="dev_A9F3",
        target_handle="darwin://global.chat.neo/inbox",
        rendezvous_scope="global.chat",
    )
    make_rendezvous_request(
        request_id="poll_req_001",
        offer_id="offer_basic_001",
        polling_hub_id="hub_private_child",
        requester_id="hub_private_child",
        target_scope="global.chat",
    )

    assert _hub_state(hub) == before
    assert hub.message_inboxes == {}
    assert hub.message_delivery_results == []


def test_stream_offer_models_do_not_import_networking_dns_or_socket_libraries():
    source = inspect.getsource(stream_offer_models)

    assert "import socket" not in source
    assert "import http" not in source
    assert "import urllib" not in source
    assert "import requests" not in source
    assert "getaddrinfo" not in source
    assert "websocket" not in source.lower()


def test_stream_offer_models_reject_non_json_safe_metadata():
    with pytest.raises(TypeError):
        _offer(metadata={"bad": object()})

    with pytest.raises(TypeError):
        make_rendezvous_request(
            request_id="poll_req_bad",
            offer_id="offer_bad",
            polling_hub_id="hub_private_child",
            requester_id="hub_private_child",
            target_scope="global.chat",
            metadata={"bad": object()},
        )


def test_stream_offer_rejects_invalid_order_bounds():
    with pytest.raises(ValueError, match="expires_order"):
        _offer(created_order=10, expires_order=9)

    with pytest.raises(ValueError, match="current_order"):
        is_stream_offer_expired(_offer(), current_order=-1)


def _offer(
    *,
    lane_signature: str = "basic_messaging:v1",
    status: str = "created",
    visibility_tier: int = 0,
    created_order: int = 0,
    expires_order: int | None = None,
    metadata: dict[str, object] | None = None,
) -> StreamOffer:
    return StreamOffer(
        offer_id="offer_001",
        requester_id="dev_A9F3",
        target_handle="alias:neo",
        lane_signature=lane_signature,
        requested_mode="message",
        visibility_tier=visibility_tier,
        status=status,
        rendezvous_scope="global.chat",
        created_order=created_order,
        expires_order=expires_order,
        metadata=metadata,
    )


def _hub_state(hub: RegistryHub) -> dict[str, object]:
    return {field.name: deepcopy(getattr(hub, field.name)) for field in fields(hub)}
