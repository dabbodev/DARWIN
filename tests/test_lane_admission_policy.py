import inspect
import json
from copy import deepcopy
from dataclasses import fields

import pytest

import darwin.registry.stream_offers as stream_offer_registry
from darwin.models import (
    LaneAdmissionDecision,
    LaneAdmissionPolicy,
    LaneAdmissionReason,
    LaneAdmissionStatus,
    RegistryHub,
    RendezvousPollResult,
    StreamOffer,
    TrafficHub,
    is_lane_admission_allowed,
    is_lane_admission_blocked,
    is_lane_admission_terminal,
    make_lane_admission_policy,
    make_rendezvous_request,
    make_stream_offer,
)
from darwin.registry import (
    evaluate_lane_admission_policy,
    hold_stream_offer,
    poll_held_stream_offers,
)


def test_create_lane_admission_policy_with_defaults():
    policy = make_lane_admission_policy(
        policy_id="policy_chat_001",
        hub_id="registry_chat_001",
    )

    assert policy == LaneAdmissionPolicy(
        policy_id="policy_chat_001",
        hub_id="registry_chat_001",
        allowed_lane_signatures=(),
        denied_lane_signatures=(),
        allowed_requester_ids=(),
        denied_requester_ids=(),
        allowed_target_scopes=(),
        denied_target_scopes=(),
        max_visibility_tier=None,
        require_discoverable=False,
        default_status=LaneAdmissionStatus("hold"),
        metadata={"simulator_local": True, "request_only": True},
    )


def test_policy_summary_is_json_safe():
    policy = make_lane_admission_policy(
        policy_id="policy_chat_001",
        hub_id="registry_chat_001",
        allowed_lane_signatures=["basic_messaging:v1"],
        denied_requester_ids=["dev_blocked"],
        allowed_target_scopes=["global.chat"],
        max_visibility_tier=2,
        require_discoverable=True,
        default_status="pass_down",
        metadata={"labels": ("lane", "admission")},
    )

    summary = policy.to_summary()

    assert summary == {
        "policy_id": "policy_chat_001",
        "hub_id": "registry_chat_001",
        "allowed_lane_signatures": ["basic_messaging:v1"],
        "denied_lane_signatures": [],
        "allowed_requester_ids": [],
        "denied_requester_ids": ["dev_blocked"],
        "allowed_target_scopes": ["global.chat"],
        "denied_target_scopes": [],
        "max_visibility_tier": 2,
        "require_discoverable": True,
        "default_status": "pass_down",
        "metadata": {"labels": ["lane", "admission"]},
    }
    assert policy.to_dict() == summary
    json.dumps(summary)


def test_decision_summary_is_json_safe():
    decision = LaneAdmissionDecision(
        decision_id="decision_001",
        policy_id="policy_chat_001",
        offer_id="offer_001",
        request_id="poll_req_001",
        hub_id="registry_chat_001",
        requester_id="dev_A9F3",
        target_handle="alias:neo",
        target_scope="global.chat",
        lane_signature="basic_messaging:v1",
        status="pass_down",
        reason="accepted",
        allowed=True,
        metadata={"labels": ("accepted",)},
    )

    summary = decision.to_summary()

    assert summary == {
        "decision_id": "decision_001",
        "policy_id": "policy_chat_001",
        "offer_id": "offer_001",
        "request_id": "poll_req_001",
        "hub_id": "registry_chat_001",
        "requester_id": "dev_A9F3",
        "target_handle": "alias:neo",
        "target_scope": "global.chat",
        "lane_signature": "basic_messaging:v1",
        "status": "pass_down",
        "reason": "accepted",
        "allowed": True,
        "metadata": {"labels": ["accepted"]},
    }
    assert decision.to_dict() == summary
    json.dumps(summary)


def test_default_hold_decision():
    decision = evaluate_lane_admission_policy(_policy(), _offer())

    assert decision.decision_id == (
        "lane_admission:policy_chat_001:offer_001:no_request"
    )
    assert decision.status == LaneAdmissionStatus("hold")
    assert decision.reason == LaneAdmissionReason("default_hold")
    assert decision.allowed is False
    assert decision.metadata["read_only"] is True
    assert decision.metadata["delivery_behavior_changed"] is False


def test_allowed_lane_requester_and_scope_pass_down_behavior():
    offer = _offer(
        lane_signature="basic_messaging:v1",
        requester_id="dev_A9F3",
        rendezvous_scope="global.chat",
    )
    policy = _policy(
        allowed_lane_signatures=["basic_messaging:v1"],
        allowed_requester_ids=["dev_A9F3"],
        allowed_target_scopes=["global.chat"],
        default_status="pass_down",
    )

    decision = evaluate_lane_admission_policy(policy, offer)

    assert decision.status == LaneAdmissionStatus("pass_down")
    assert decision.reason == LaneAdmissionReason("accepted")
    assert decision.allowed is True


def test_denied_lane_behavior():
    policy = _policy(
        denied_lane_signatures=["basic_messaging:v1"],
        default_status="pass_down",
    )

    decision = evaluate_lane_admission_policy(policy, _offer())

    assert decision.status == LaneAdmissionStatus("deny")
    assert decision.reason == LaneAdmissionReason("explicit_lane_denied")
    assert decision.allowed is False


def test_denied_requester_behavior_precedes_denied_lane():
    policy = _policy(
        denied_lane_signatures=["basic_messaging:v1"],
        denied_requester_ids=["dev_A9F3"],
        default_status="pass_down",
    )

    decision = evaluate_lane_admission_policy(policy, _offer())

    assert decision.status == LaneAdmissionStatus("deny")
    assert decision.reason == LaneAdmissionReason("explicit_requester_denied")


def test_denied_target_scope_behavior():
    policy = _policy(
        denied_target_scopes=["global.chat"],
        default_status="pass_down",
    )

    decision = evaluate_lane_admission_policy(policy, _offer())

    assert decision.status == LaneAdmissionStatus("deny")
    assert decision.reason == LaneAdmissionReason("explicit_scope_denied")


@pytest.mark.parametrize(
    ("policy_kwargs", "expected_reason"),
    [
        (
            {"allowed_lane_signatures": ["control:v1"]},
            "lane_not_allowed",
        ),
        (
            {"allowed_requester_ids": ["dev_allowed"]},
            "requester_not_allowed",
        ),
        (
            {"allowed_target_scopes": ["global.remote"]},
            "scope_not_allowed",
        ),
    ],
)
def test_allowed_list_missing_lane_requester_or_scope_behavior(
    policy_kwargs,
    expected_reason,
):
    policy = _policy(default_status="pass_down", **policy_kwargs)

    decision = evaluate_lane_admission_policy(policy, _offer())

    assert decision.status == LaneAdmissionStatus("hold")
    assert decision.reason == LaneAdmissionReason(expected_reason)
    assert decision.allowed is False


def test_visibility_tier_exceeded_behavior():
    policy = _policy(max_visibility_tier=1, default_status="pass_down")
    offer = _offer(visibility_tier=2)

    decision = evaluate_lane_admission_policy(policy, offer)

    assert decision.status == LaneAdmissionStatus("deny")
    assert decision.reason == LaneAdmissionReason("visibility_tier_exceeded")


def test_require_discoverable_with_matching_poll_result_allows_normal_policy_flow():
    hub = _hub()
    offer = hold_stream_offer(hub, _offer())
    request = _request()
    poll_result = poll_held_stream_offers(hub, request)
    policy = _policy(require_discoverable=True, default_status="pass_down")

    decision = evaluate_lane_admission_policy(
        policy,
        offer,
        request=request,
        poll_result=poll_result,
    )

    assert poll_result == RendezvousPollResult(
        request_id="poll_req_001",
        polling_hub_id="hub_private_child",
        parent_hub_id="registry_chat_001",
        target_scope="global.chat",
        visibility_tier=1,
        matched_offer_ids=["offer_001"],
        matched_offers=[offer],
        status="matched",
        reason="offers_available",
        metadata={
            "simulator_local": True,
            "read_only": True,
            "delivery_behavior_changed": False,
            "networking": False,
        },
    )
    assert decision.status == LaneAdmissionStatus("pass_down")
    assert decision.reason == LaneAdmissionReason("accepted")
    assert decision.metadata["poll_result_status"] == "matched"


def test_require_discoverable_without_matching_poll_result_requires_poll():
    policy = _policy(require_discoverable=True, default_status="pass_down")

    decision = evaluate_lane_admission_policy(policy, _offer(), request=_request())

    assert decision.status == LaneAdmissionStatus("requires_poll")
    assert decision.reason == LaneAdmissionReason("not_discoverable")
    assert decision.allowed is False


@pytest.mark.parametrize(
    ("default_status", "expected_reason"),
    [
        ("rate_limited", "rate_limited"),
        ("quarantined", "quarantined"),
    ],
)
def test_rate_limited_and_quarantined_defaults_are_deterministic(
    default_status,
    expected_reason,
):
    decision = evaluate_lane_admission_policy(
        _policy(default_status=default_status),
        _offer(),
    )

    assert decision.status == LaneAdmissionStatus(default_status)
    assert decision.reason == LaneAdmissionReason(expected_reason)
    assert decision.allowed is False


def test_decision_predicates():
    allowed = _decision(status="pass_down", reason="accepted", allowed=True)
    held = _decision(status="hold", reason="default_hold", allowed=False)
    denied = _decision(status="deny", reason="explicit_lane_denied", allowed=False)
    rate_limited = _decision(
        status="rate_limited",
        reason="rate_limited",
        allowed=False,
    )
    quarantined = _decision(
        status="quarantined",
        reason="quarantined",
        allowed=False,
    )
    requires_poll = _decision(
        status="requires_poll",
        reason="not_discoverable",
        allowed=False,
    )

    assert is_lane_admission_allowed(allowed) is True
    assert is_lane_admission_allowed(held) is False
    assert is_lane_admission_blocked(denied) is True
    assert is_lane_admission_blocked(rate_limited) is True
    assert is_lane_admission_blocked(quarantined) is True
    assert is_lane_admission_blocked(requires_poll) is False
    assert is_lane_admission_terminal(allowed) is True
    assert is_lane_admission_terminal(denied) is True
    assert is_lane_admission_terminal(held) is False
    assert is_lane_admission_terminal(requires_poll) is False


def test_evaluation_is_read_only_and_does_not_mutate_inputs():
    hub = _hub()
    offer = hold_stream_offer(hub, _offer(metadata={"labels": ("demo",)}))
    policy = _policy(default_status="pass_down")
    request = _request()
    poll_result = poll_held_stream_offers(hub, request)
    before_hub = _hub_state(hub)
    before_offer = offer.to_summary()
    before_policy = policy.to_summary()
    before_request = request.to_summary()

    decision = evaluate_lane_admission_policy(
        policy,
        offer,
        request=request,
        poll_result=poll_result,
        metadata={"caller": "test"},
    )
    decision.to_summary()["metadata"]["caller"] = "mutated"

    assert _hub_state(hub) == before_hub
    assert offer.to_summary() == before_offer
    assert policy.to_summary() == before_policy
    assert request.to_summary() == before_request


def test_no_delivery_occurs_and_traffic_hub_routing_is_unchanged():
    registry_hub = _hub()
    traffic_hub = TrafficHub(hub_id="traffic_chat_001")
    traffic_before = deepcopy(traffic_hub)

    evaluate_lane_admission_policy(
        _policy(default_status="pass_down"),
        _offer(),
    )

    assert registry_hub.message_inboxes == {}
    assert registry_hub.message_delivery_results == []
    assert traffic_hub == traffic_before


def test_invalid_policy_or_offer_returns_deterministic_decision():
    offer = _offer()
    invalid_policy = evaluate_lane_admission_policy(object(), offer)  # type: ignore[arg-type]
    invalid_offer = evaluate_lane_admission_policy(_policy(), object())  # type: ignore[arg-type]

    assert invalid_policy.status == LaneAdmissionStatus("deny")
    assert invalid_policy.reason == LaneAdmissionReason("invalid_policy")
    assert invalid_policy.policy_id is None
    assert invalid_policy.offer_id == "offer_001"
    assert invalid_offer.status == LaneAdmissionStatus("deny")
    assert invalid_offer.reason == LaneAdmissionReason("invalid_offer")
    assert invalid_offer.policy_id == "policy_chat_001"
    assert invalid_offer.offer_id is None


def test_lane_admission_policy_rejects_non_json_safe_metadata():
    with pytest.raises(TypeError, match="JSON-safe"):
        make_lane_admission_policy(
            policy_id="policy_bad",
            hub_id="registry_chat_001",
            metadata={"bad": object()},
        )

    with pytest.raises(TypeError, match="JSON-safe"):
        LaneAdmissionDecision(
            decision_id="decision_bad",
            policy_id="policy_chat_001",
            offer_id="offer_001",
            request_id=None,
            hub_id="registry_chat_001",
            requester_id="dev_A9F3",
            target_handle="alias:neo",
            target_scope="global.chat",
            lane_signature="basic_messaging:v1",
            status="hold",
            reason="default_hold",
            allowed=False,
            metadata={"bad": object()},
        )


def test_lane_admission_registry_does_not_import_networking_dns_or_socket_libraries():
    source = inspect.getsource(stream_offer_registry)

    assert "import socket" not in source
    assert "import http" not in source
    assert "import urllib" not in source
    assert "import requests" not in source
    assert "getaddrinfo" not in source
    assert "websocket" not in source.lower()


def _policy(**overrides) -> LaneAdmissionPolicy:
    values = {
        "policy_id": "policy_chat_001",
        "hub_id": "registry_chat_001",
    }
    values.update(overrides)
    return make_lane_admission_policy(**values)


def _hub() -> RegistryHub:
    return RegistryHub(hub_id="registry_chat_001", scope_path="global.chat")


def _request():
    return make_rendezvous_request(
        request_id="poll_req_001",
        offer_id="offer_001",
        polling_hub_id="hub_private_child",
        requester_id="hub_private_child",
        target_scope="global.chat",
        visibility_tier=1,
    )


def _offer(
    *,
    offer_id: str = "offer_001",
    requester_id: str = "dev_A9F3",
    target_handle: str = "alias:neo",
    lane_signature: str = "basic_messaging:v1",
    visibility_tier: int = 1,
    rendezvous_scope: str | None = "global.chat",
    metadata: dict[str, object] | None = None,
) -> StreamOffer:
    return make_stream_offer(
        offer_id=offer_id,
        requester_id=requester_id,
        target_handle=target_handle,
        lane_signature=lane_signature,
        visibility_tier=visibility_tier,
        rendezvous_scope=rendezvous_scope,
        metadata=metadata,
    )


def _decision(
    *,
    status: str,
    reason: str,
    allowed: bool,
) -> LaneAdmissionDecision:
    return LaneAdmissionDecision(
        decision_id=f"decision_{status}",
        policy_id="policy_chat_001",
        offer_id="offer_001",
        request_id=None,
        hub_id="registry_chat_001",
        requester_id="dev_A9F3",
        target_handle="alias:neo",
        target_scope="global.chat",
        lane_signature="basic_messaging:v1",
        status=status,
        reason=reason,
        allowed=allowed,
    )


def _hub_state(hub: RegistryHub) -> dict[str, object]:
    return {field.name: deepcopy(getattr(hub, field.name)) for field in fields(hub)}
