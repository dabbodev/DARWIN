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
    StreamOffer,
    StreamOfferMode,
    StreamOfferStatus,
    StreamOfferVisibility,
    is_stream_offer_active,
    is_stream_offer_expired,
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
