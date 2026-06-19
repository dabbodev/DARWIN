"""RegistryHub-local held stream offer helpers for v1.2."""

from __future__ import annotations

from dataclasses import replace

from darwin.models.hub import RegistryHub
from darwin.models.lane_signature import (
    LaneSignature,
    LaneVisibilityTier,
    parse_lane_signature,
)
from darwin.models.stream_offer import (
    LaneAdmissionDecision,
    LaneAdmissionPolicy,
    RendezvousPollResult,
    RendezvousRequest,
    StreamOffer,
    StreamOfferMode,
    StreamOfferStatus,
    StreamOfferVisibility,
    is_stream_offer_active,
    is_stream_offer_discoverable_to_request,
    is_stream_offer_expired,
    is_stream_offer_terminal,
    stream_offer_matches_rendezvous_request,
)


def hold_stream_offer(
    registry_hub: RegistryHub,
    offer: StreamOffer,
    *,
    replace_existing: bool = False,
) -> StreamOffer:
    """Hold a stream offer on a RegistryHub-local in-memory queue."""
    _validate_registry_hub(registry_hub)
    _validate_offer(offer)

    stored = replace(offer, status="held") if offer.status.status == "created" else offer
    existing_index = _held_offer_index(registry_hub, stored.offer_id)

    if existing_index is None:
        registry_hub.held_stream_offers.append(stored)
        return stored

    if not replace_existing:
        raise ValueError(f"held stream offer already exists: {stored.offer_id}")

    registry_hub.held_stream_offers[existing_index] = stored
    return stored


def get_held_stream_offer(
    registry_hub: RegistryHub,
    offer_id: str,
) -> StreamOffer | None:
    """Return a held stream offer by ID, if present."""
    _validate_registry_hub(registry_hub)
    _validate_required_string(offer_id, "offer_id")
    for offer in registry_hub.held_stream_offers:
        if offer.offer_id == offer_id:
            return offer
    return None


def query_held_stream_offers(
    registry_hub: RegistryHub,
    *,
    offer_id: str | None = None,
    requester_id: str | None = None,
    target_handle: str | None = None,
    lane_signature: LaneSignature | str | None = None,
    requested_mode: StreamOfferMode | str | None = None,
    visibility_tier: StreamOfferVisibility | LaneVisibilityTier | int | None = None,
    status: StreamOfferStatus | str | None = None,
    rendezvous_scope: str | None = None,
    active_only: bool | None = None,
    current_order: int | None = None,
) -> list[StreamOffer]:
    """Return held stream offers matching additive filters in append order."""
    _validate_registry_hub(registry_hub)
    _validate_optional_string(offer_id, "offer_id")
    _validate_optional_string(requester_id, "requester_id")
    _validate_optional_string(target_handle, "target_handle")
    _validate_optional_string(rendezvous_scope, "rendezvous_scope")
    lane_signature_key = _lane_signature_key(lane_signature)
    mode_key = _requested_mode_key(requested_mode)
    visibility_key = _visibility_tier_key(visibility_tier)
    status_key = _status_key(status)
    if active_only is not None and not isinstance(active_only, bool):
        raise TypeError("active_only must be a bool or None")
    if current_order is not None:
        _validate_order(current_order, "current_order")

    return [
        offer
        for offer in registry_hub.held_stream_offers
        if (offer_id is None or offer.offer_id == offer_id)
        and (requester_id is None or offer.requester_id == requester_id)
        and (target_handle is None or offer.target_handle == target_handle)
        and (lane_signature_key is None or offer.lane_signature == lane_signature_key)
        and (mode_key is None or offer.requested_mode.mode == mode_key)
        and (visibility_key is None or offer.visibility_tier.tier == visibility_key)
        and (status_key is None or offer.status.status == status_key)
        and (
            rendezvous_scope is None
            or offer.rendezvous_scope == rendezvous_scope
        )
        and _matches_active_filter(
            offer,
            active_only=active_only,
            current_order=current_order,
        )
    ]


def update_held_stream_offer_status(
    registry_hub: RegistryHub,
    offer_id: str,
    status: StreamOfferStatus | str,
    *,
    metadata: dict[str, object] | None = None,
) -> StreamOffer:
    """Update a held stream offer status and optionally merge JSON-safe metadata."""
    _validate_registry_hub(registry_hub)
    _validate_required_string(offer_id, "offer_id")
    status_value = _status_key(status)
    assert status_value is not None

    existing_index = _held_offer_index(registry_hub, offer_id)
    if existing_index is None:
        raise KeyError(f"held stream offer is not registered: {offer_id}")

    offer = registry_hub.held_stream_offers[existing_index]
    merged_metadata = dict(offer.metadata or {})
    if metadata is not None:
        if not isinstance(metadata, dict):
            raise TypeError("metadata must be a JSON-safe dict")
        merged_metadata.update(metadata)

    updated = replace(offer, status=status_value, metadata=merged_metadata)
    registry_hub.held_stream_offers[existing_index] = updated
    return updated


def summarize_held_stream_offers(registry_hub: RegistryHub) -> list[dict[str, object]]:
    """Return JSON-safe summaries for held stream offers in append order."""
    _validate_registry_hub(registry_hub)
    return [offer.to_summary() for offer in registry_hub.held_stream_offers]


def poll_held_stream_offers(
    parent_hub: RegistryHub | None,
    request: RendezvousRequest,
    *,
    lane_signature: LaneSignature | str | None = None,
    requested_mode: StreamOfferMode | str | None = None,
    active_only: bool = True,
    current_order: int | None = None,
) -> RendezvousPollResult:
    """Return discoverable held stream offers for one explicit poll request."""
    _validate_rendezvous_request(request)
    if parent_hub is None:
        return _poll_result(
            request,
            parent_hub_id="hub_missing",
            matched_offers=[],
            status="invalid_request",
            reason="hub_missing",
        )
    _validate_registry_hub(parent_hub)
    lane_signature_key = _lane_signature_key(lane_signature)
    mode_key = _requested_mode_key(requested_mode)
    if not isinstance(active_only, bool):
        raise TypeError("active_only must be a bool")
    if current_order is not None:
        _validate_order(current_order, "current_order")

    matches = [
        offer
        for offer in parent_hub.held_stream_offers
        if _poll_offer_matches(
            offer,
            request,
            lane_signature_key=lane_signature_key,
            mode_key=mode_key,
            active_only=active_only,
            current_order=current_order,
        )
    ]

    if matches:
        return _poll_result(
            request,
            parent_hub_id=parent_hub.hub_id,
            matched_offers=matches,
            status="matched",
            reason="offers_available",
        )

    reason = (
        "scope_mismatch"
        if _has_scope_visible_offer(parent_hub, request)
        else "no_discoverable_offers"
    )
    return _poll_result(
        request,
        parent_hub_id=parent_hub.hub_id,
        matched_offers=[],
        status="empty",
        reason=reason,
    )


def mark_stream_offers_discoverable(
    parent_hub: RegistryHub,
    offer_ids: list[str],
    *,
    metadata: dict[str, object] | None = None,
) -> list[StreamOffer]:
    """Mark selected held stream offers discoverable without delivery side effects."""
    _validate_registry_hub(parent_hub)
    if not isinstance(offer_ids, list):
        raise TypeError("offer_ids must be a list")
    for offer_id in offer_ids:
        _validate_required_string(offer_id, "offer_id")

    updated_offers: list[StreamOffer] = []
    requested_ids = set(offer_ids)
    for index, offer in enumerate(parent_hub.held_stream_offers):
        if offer.offer_id not in requested_ids:
            continue

        merged_metadata = dict(offer.metadata or {})
        if metadata is not None:
            if not isinstance(metadata, dict):
                raise TypeError("metadata must be a JSON-safe dict")
            merged_metadata.update(metadata)

        updated = replace(offer, status="discoverable", metadata=merged_metadata)
        parent_hub.held_stream_offers[index] = updated
        updated_offers.append(updated)

    return updated_offers


def evaluate_lane_admission_policy(
    policy: LaneAdmissionPolicy,
    offer: StreamOffer,
    *,
    request: RendezvousRequest | None = None,
    poll_result: RendezvousPollResult | None = None,
    decision_id: str | None = None,
    metadata: dict[str, object] | None = None,
) -> LaneAdmissionDecision:
    """Evaluate one stream offer against a simulator-local admission policy."""
    _validate_optional_rendezvous_request(request)
    _validate_optional_poll_result(poll_result)
    _validate_optional_string(decision_id, "decision_id")
    if metadata is not None and not isinstance(metadata, dict):
        raise TypeError("metadata must be a JSON-safe dict")

    if not isinstance(policy, LaneAdmissionPolicy):
        return _lane_admission_decision(
            policy=None,
            offer=offer if isinstance(offer, StreamOffer) else None,
            request=request,
            poll_result=poll_result,
            decision_id=decision_id,
            status="deny",
            reason="invalid_policy",
            metadata=metadata,
        )

    if not isinstance(offer, StreamOffer):
        return _lane_admission_decision(
            policy=policy,
            offer=None,
            request=request,
            poll_result=poll_result,
            decision_id=decision_id,
            status="deny",
            reason="invalid_offer",
            metadata=metadata,
        )

    if is_stream_offer_terminal(offer):
        return _lane_admission_decision(
            policy=policy,
            offer=offer,
            request=request,
            poll_result=poll_result,
            decision_id=decision_id,
            status="deny",
            reason="invalid_offer",
            metadata=metadata,
        )

    target_scope = _target_scope(offer, request, poll_result)

    if offer.requester_id in policy.denied_requester_ids:
        return _lane_admission_decision(
            policy=policy,
            offer=offer,
            request=request,
            poll_result=poll_result,
            decision_id=decision_id,
            status="deny",
            reason="explicit_requester_denied",
            metadata=metadata,
        )

    if offer.lane_signature in policy.denied_lane_signatures:
        return _lane_admission_decision(
            policy=policy,
            offer=offer,
            request=request,
            poll_result=poll_result,
            decision_id=decision_id,
            status="deny",
            reason="explicit_lane_denied",
            metadata=metadata,
        )

    if target_scope is not None and target_scope in policy.denied_target_scopes:
        return _lane_admission_decision(
            policy=policy,
            offer=offer,
            request=request,
            poll_result=poll_result,
            decision_id=decision_id,
            status="deny",
            reason="explicit_scope_denied",
            metadata=metadata,
        )

    if (
        policy.max_visibility_tier is not None
        and offer.visibility_tier.tier > policy.max_visibility_tier.tier
    ):
        return _lane_admission_decision(
            policy=policy,
            offer=offer,
            request=request,
            poll_result=poll_result,
            decision_id=decision_id,
            status="deny",
            reason="visibility_tier_exceeded",
            metadata=metadata,
        )

    if policy.require_discoverable and not _offer_in_poll_result(offer, poll_result):
        return _lane_admission_decision(
            policy=policy,
            offer=offer,
            request=request,
            poll_result=poll_result,
            decision_id=decision_id,
            status="requires_poll",
            reason="not_discoverable",
            metadata=metadata,
        )

    if (
        policy.allowed_lane_signatures
        and offer.lane_signature not in policy.allowed_lane_signatures
    ):
        return _lane_admission_decision(
            policy=policy,
            offer=offer,
            request=request,
            poll_result=poll_result,
            decision_id=decision_id,
            status="hold",
            reason="lane_not_allowed",
            metadata=metadata,
        )

    if (
        policy.allowed_requester_ids
        and offer.requester_id not in policy.allowed_requester_ids
    ):
        return _lane_admission_decision(
            policy=policy,
            offer=offer,
            request=request,
            poll_result=poll_result,
            decision_id=decision_id,
            status="hold",
            reason="requester_not_allowed",
            metadata=metadata,
        )

    if policy.allowed_target_scopes and (
        target_scope is None or target_scope not in policy.allowed_target_scopes
    ):
        return _lane_admission_decision(
            policy=policy,
            offer=offer,
            request=request,
            poll_result=poll_result,
            decision_id=decision_id,
            status="hold",
            reason="scope_not_allowed",
            metadata=metadata,
        )

    return _lane_admission_decision(
        policy=policy,
        offer=offer,
        request=request,
        poll_result=poll_result,
        decision_id=decision_id,
        status=policy.default_status.status,
        reason=_default_lane_admission_reason(policy.default_status.status),
        metadata=metadata,
    )


def _lane_admission_decision(
    *,
    policy: LaneAdmissionPolicy | None,
    offer: StreamOffer | None,
    request: RendezvousRequest | None,
    poll_result: RendezvousPollResult | None,
    decision_id: str | None,
    status: str,
    reason: str,
    metadata: dict[str, object] | None,
) -> LaneAdmissionDecision:
    decision_metadata: dict[str, object] = {
        "simulator_local": True,
        "policy_only": True,
        "read_only": True,
        "registry_hub_mutated": False,
        "offer_mutated": False,
        "message_mutated": False,
        "inbox_mutated": False,
        "delivery_result_created": False,
        "delivery_behavior_changed": False,
        "traffic_hub_routing_changed": False,
        "networking": False,
    }
    if poll_result is not None:
        decision_metadata["poll_result_status"] = poll_result.status.status
        decision_metadata["poll_result_reason"] = poll_result.reason
    if metadata is not None:
        decision_metadata.update(metadata)

    target_scope = _target_scope(offer, request, poll_result)
    if decision_id is None:
        decision_id = _lane_admission_decision_id(policy, offer, request)

    return LaneAdmissionDecision(
        decision_id=decision_id,
        policy_id=None if policy is None else policy.policy_id,
        offer_id=None if offer is None else offer.offer_id,
        request_id=None if request is None else request.request_id,
        hub_id=None if policy is None else policy.hub_id,
        requester_id=None if offer is None else offer.requester_id,
        target_handle=None if offer is None else offer.target_handle,
        target_scope=target_scope,
        lane_signature=None if offer is None else offer.lane_signature,
        status=status,
        reason=reason,
        allowed=status == "pass_down",
        metadata=decision_metadata,
    )


def _lane_admission_decision_id(
    policy: LaneAdmissionPolicy | None,
    offer: StreamOffer | None,
    request: RendezvousRequest | None,
) -> str:
    policy_id = "invalid_policy" if policy is None else policy.policy_id
    offer_id = "invalid_offer" if offer is None else offer.offer_id
    request_id = "no_request" if request is None else request.request_id
    return f"lane_admission:{policy_id}:{offer_id}:{request_id}"


def _default_lane_admission_reason(status: str) -> str:
    if status == "pass_down":
        return "accepted"
    if status == "rate_limited":
        return "rate_limited"
    if status == "quarantined":
        return "quarantined"
    if status == "deny":
        return "default_hold"
    if status == "requires_poll":
        return "not_discoverable"
    return "default_hold"


def _target_scope(
    offer: StreamOffer | None,
    request: RendezvousRequest | None,
    poll_result: RendezvousPollResult | None,
) -> str | None:
    if request is not None:
        return request.target_scope
    if poll_result is not None:
        return poll_result.target_scope
    if offer is not None:
        return offer.rendezvous_scope
    return None


def _offer_in_poll_result(
    offer: StreamOffer,
    poll_result: RendezvousPollResult | None,
) -> bool:
    if poll_result is None:
        return False
    return (
        poll_result.status.status == "matched"
        and offer.offer_id in poll_result.matched_offer_ids
    )


def _poll_offer_matches(
    offer: StreamOffer,
    request: RendezvousRequest,
    *,
    lane_signature_key: str | None,
    mode_key: str | None,
    active_only: bool,
    current_order: int | None,
) -> bool:
    if lane_signature_key is not None and offer.lane_signature != lane_signature_key:
        return False
    if mode_key is not None and offer.requested_mode.mode != mode_key:
        return False
    if active_only:
        return is_stream_offer_discoverable_to_request(
            offer,
            request,
            current_order=current_order,
        )
    return stream_offer_matches_rendezvous_request(offer, request)


def _poll_result(
    request: RendezvousRequest,
    *,
    parent_hub_id: str,
    matched_offers: list[StreamOffer],
    status: str,
    reason: str,
) -> RendezvousPollResult:
    return RendezvousPollResult(
        request_id=request.request_id,
        polling_hub_id=request.polling_hub_id,
        parent_hub_id=parent_hub_id,
        target_scope=request.target_scope,
        visibility_tier=request.visibility_tier,
        matched_offer_ids=[offer.offer_id for offer in matched_offers],
        matched_offers=matched_offers,
        status=status,
        reason=reason,
        metadata={
            "simulator_local": True,
            "read_only": True,
            "delivery_behavior_changed": False,
            "networking": False,
        },
    )


def _has_scope_visible_offer(
    parent_hub: RegistryHub,
    request: RendezvousRequest,
) -> bool:
    return any(
        offer.rendezvous_scope is not None
        and offer.rendezvous_scope != request.target_scope
        and offer.visibility_tier.tier <= request.visibility_tier.tier
        for offer in parent_hub.held_stream_offers
    )


def _matches_active_filter(
    offer: StreamOffer,
    *,
    active_only: bool | None,
    current_order: int | None,
) -> bool:
    if active_only is None:
        return True

    expired_by_order = (
        False
        if current_order is None
        else is_stream_offer_expired(offer, current_order=current_order)
    )
    active = is_stream_offer_active(offer) and not expired_by_order
    return active if active_only else not active


def _held_offer_index(registry_hub: RegistryHub, offer_id: str) -> int | None:
    for index, existing in enumerate(registry_hub.held_stream_offers):
        if existing.offer_id == offer_id:
            return index
    return None


def _lane_signature_key(lane_signature: LaneSignature | str | None) -> str | None:
    if lane_signature is None:
        return None
    if isinstance(lane_signature, LaneSignature):
        return lane_signature.signature
    if isinstance(lane_signature, str):
        return parse_lane_signature(lane_signature).signature
    raise TypeError("lane_signature must be a LaneSignature, string, or None")


def _requested_mode_key(requested_mode: StreamOfferMode | str | None) -> str | None:
    if requested_mode is None:
        return None
    if isinstance(requested_mode, StreamOfferMode):
        return requested_mode.mode
    if isinstance(requested_mode, str):
        return StreamOfferMode(requested_mode).mode
    raise TypeError("requested_mode must be a StreamOfferMode, string, or None")


def _visibility_tier_key(
    visibility_tier: StreamOfferVisibility | LaneVisibilityTier | int | None,
) -> int | None:
    if visibility_tier is None:
        return None
    if isinstance(visibility_tier, StreamOfferVisibility | LaneVisibilityTier):
        return visibility_tier.tier
    if isinstance(visibility_tier, int):
        return StreamOfferVisibility(visibility_tier).tier
    raise TypeError(
        "visibility_tier must be a StreamOfferVisibility, LaneVisibilityTier, "
        "integer, or None"
    )


def _status_key(status: StreamOfferStatus | str | None) -> str | None:
    if status is None:
        return None
    if isinstance(status, StreamOfferStatus):
        return status.status
    if isinstance(status, str):
        return StreamOfferStatus(status).status
    raise TypeError("status must be a StreamOfferStatus, string, or None")


def _validate_offer(offer: StreamOffer) -> None:
    if not isinstance(offer, StreamOffer):
        raise TypeError("offer must be a StreamOffer")


def _validate_rendezvous_request(request: RendezvousRequest) -> None:
    if not isinstance(request, RendezvousRequest):
        raise TypeError("request must be a RendezvousRequest")


def _validate_optional_rendezvous_request(request: RendezvousRequest | None) -> None:
    if request is None:
        return
    _validate_rendezvous_request(request)


def _validate_optional_poll_result(poll_result: RendezvousPollResult | None) -> None:
    if poll_result is None:
        return
    if not isinstance(poll_result, RendezvousPollResult):
        raise TypeError("poll_result must be a RendezvousPollResult or None")


def _validate_registry_hub(registry_hub: RegistryHub) -> None:
    if not isinstance(registry_hub, RegistryHub):
        raise TypeError("registry_hub must be a RegistryHub")


def _validate_required_string(value: str, field_name: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} is required")
    if value.strip() != value or any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")


def _validate_optional_string(value: str | None, field_name: str) -> None:
    if value is None:
        return
    _validate_required_string(value, field_name)


def _validate_order(value: int, field_name: str) -> None:
    if not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be greater than or equal to 0")
