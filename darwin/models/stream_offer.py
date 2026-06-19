"""Simulator-local stream offer and rendezvous request models for v1.2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from darwin.models.lane_signature import (
    LANE_VISIBILITY_TIERS,
    LaneSignature,
    LaneVisibilityTier,
    parse_lane_signature,
)

STREAM_OFFER_MODES: tuple[str, ...] = (
    "message",
    "stream",
    "poll",
    "control",
)

STREAM_OFFER_STATUSES: tuple[str, ...] = (
    "created",
    "held",
    "discoverable",
    "passed_down",
    "accepted",
    "denied",
    "expired",
    "rate_limited",
    "quarantined",
)

STREAM_OFFER_ACTIVE_STATUSES: tuple[str, ...] = (
    "created",
    "held",
    "discoverable",
    "passed_down",
)

STREAM_OFFER_TERMINAL_STATUSES: tuple[str, ...] = (
    "accepted",
    "denied",
    "expired",
    "rate_limited",
    "quarantined",
)

RENDEZVOUS_POLL_STATUSES: tuple[str, ...] = (
    "matched",
    "empty",
    "invalid_request",
)

RENDEZVOUS_POLL_REASONS: tuple[str, ...] = (
    "offers_available",
    "no_discoverable_offers",
    "invalid_request",
    "hub_missing",
    "scope_mismatch",
)


@dataclass(frozen=True, slots=True)
class StreamOfferMode:
    """Controlled simulator-local stream offer request mode."""

    mode: str = "message"

    def __post_init__(self) -> None:
        _validate_mode(self.mode)

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe mode summary."""
        return {"mode": self.mode}

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class StreamOfferStatus:
    """Controlled simulator-local stream offer lifecycle status."""

    status: str = "created"

    def __post_init__(self) -> None:
        _validate_status(self.status)

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe status summary."""
        return {"status": self.status}

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class RendezvousPollStatus:
    """Controlled simulator-local rendezvous poll result status."""

    status: str = "empty"

    def __post_init__(self) -> None:
        _validate_poll_status(self.status)

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe status summary."""
        return {"status": self.status}

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class StreamOfferVisibility:
    """Discovery visibility tier for a simulator-local stream offer."""

    tier: int = 0

    def __post_init__(self) -> None:
        if self.tier not in LANE_VISIBILITY_TIERS:
            raise ValueError("visibility tier must be an integer from 0 through 5")

    @property
    def label(self) -> str:
        """Return the stable label for this stream offer visibility tier."""
        return LANE_VISIBILITY_TIERS[self.tier]

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe visibility summary."""
        return {"tier": self.tier, "label": self.label}

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class StreamOffer:
    """Simulator-local request to establish or deliver over a lane later."""

    offer_id: str
    requester_id: str
    target_handle: str
    lane_signature: LaneSignature | str
    requested_mode: StreamOfferMode | str = "message"
    visibility_tier: StreamOfferVisibility | LaneVisibilityTier | int = 0
    status: StreamOfferStatus | str = "created"
    rendezvous_scope: str | None = None
    created_order: int = 0
    expires_order: int | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _validate_required_string(self.offer_id, "offer_id")
        _validate_required_string(self.requester_id, "requester_id")
        _validate_required_string(self.target_handle, "target_handle")

        lane_signature = self.lane_signature
        if isinstance(lane_signature, LaneSignature):
            lane_signature = lane_signature.signature
        elif isinstance(lane_signature, str):
            lane_signature = parse_lane_signature(lane_signature).signature
        else:
            raise TypeError("lane_signature must be a LaneSignature or string")
        object.__setattr__(self, "lane_signature", lane_signature)

        requested_mode = self.requested_mode
        if isinstance(requested_mode, str):
            requested_mode = StreamOfferMode(requested_mode)
        if not isinstance(requested_mode, StreamOfferMode):
            raise TypeError("requested_mode must be a StreamOfferMode or string")
        object.__setattr__(self, "requested_mode", requested_mode)

        visibility_tier = self.visibility_tier
        if isinstance(visibility_tier, LaneVisibilityTier):
            visibility_tier = visibility_tier.tier
        if isinstance(visibility_tier, int):
            visibility_tier = StreamOfferVisibility(visibility_tier)
        if not isinstance(visibility_tier, StreamOfferVisibility):
            raise TypeError(
                "visibility_tier must be a StreamOfferVisibility, "
                "LaneVisibilityTier, or integer"
            )
        object.__setattr__(self, "visibility_tier", visibility_tier)

        status = self.status
        if isinstance(status, str):
            status = StreamOfferStatus(status)
        if not isinstance(status, StreamOfferStatus):
            raise TypeError("status must be a StreamOfferStatus or string")
        object.__setattr__(self, "status", status)

        _validate_optional_string(self.rendezvous_scope, "rendezvous_scope")
        _validate_order(self.created_order, "created_order")
        _validate_optional_order(self.expires_order, "expires_order")
        if self.expires_order is not None and self.expires_order < self.created_order:
            raise ValueError("expires_order must be greater than or equal to created_order")

        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata or {}))

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe stream offer summary."""
        return {
            "offer_id": self.offer_id,
            "requester_id": self.requester_id,
            "target_handle": self.target_handle,
            "lane_signature": self.lane_signature,
            "requested_mode": self.requested_mode.mode,
            "visibility_tier": self.visibility_tier.tier,
            "status": self.status.status,
            "rendezvous_scope": self.rendezvous_scope,
            "created_order": self.created_order,
            "expires_order": self.expires_order,
            "metadata": _json_safe_copy(self.metadata or {}),
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class RendezvousRequest:
    """Simulator-local metadata for a future private hub poll request."""

    request_id: str
    offer_id: str
    polling_hub_id: str
    requester_id: str
    target_scope: str
    visibility_tier: StreamOfferVisibility | LaneVisibilityTier | int = 0
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _validate_required_string(self.request_id, "request_id")
        _validate_required_string(self.offer_id, "offer_id")
        _validate_required_string(self.polling_hub_id, "polling_hub_id")
        _validate_required_string(self.requester_id, "requester_id")
        _validate_required_string(self.target_scope, "target_scope")

        visibility_tier = self.visibility_tier
        if isinstance(visibility_tier, LaneVisibilityTier):
            visibility_tier = visibility_tier.tier
        if isinstance(visibility_tier, int):
            visibility_tier = StreamOfferVisibility(visibility_tier)
        if not isinstance(visibility_tier, StreamOfferVisibility):
            raise TypeError(
                "visibility_tier must be a StreamOfferVisibility, "
                "LaneVisibilityTier, or integer"
            )
        object.__setattr__(self, "visibility_tier", visibility_tier)
        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata or {}))

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe rendezvous request summary."""
        return {
            "request_id": self.request_id,
            "offer_id": self.offer_id,
            "polling_hub_id": self.polling_hub_id,
            "requester_id": self.requester_id,
            "target_scope": self.target_scope,
            "visibility_tier": self.visibility_tier.tier,
            "metadata": _json_safe_copy(self.metadata or {}),
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class RendezvousPollResult:
    """Simulator-local result for one explicit private polling helper call."""

    request_id: str
    polling_hub_id: str
    parent_hub_id: str
    target_scope: str
    visibility_tier: StreamOfferVisibility | LaneVisibilityTier | int = 0
    matched_offer_ids: tuple[str, ...] | list[str] = ()
    matched_offers: tuple[StreamOffer, ...] | list[StreamOffer] = ()
    status: RendezvousPollStatus | str = "empty"
    reason: str = "no_discoverable_offers"
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _validate_required_string(self.request_id, "request_id")
        _validate_required_string(self.polling_hub_id, "polling_hub_id")
        _validate_required_string(self.parent_hub_id, "parent_hub_id")
        _validate_required_string(self.target_scope, "target_scope")

        visibility_tier = self.visibility_tier
        if isinstance(visibility_tier, LaneVisibilityTier):
            visibility_tier = visibility_tier.tier
        if isinstance(visibility_tier, int):
            visibility_tier = StreamOfferVisibility(visibility_tier)
        if not isinstance(visibility_tier, StreamOfferVisibility):
            raise TypeError(
                "visibility_tier must be a StreamOfferVisibility, "
                "LaneVisibilityTier, or integer"
            )
        object.__setattr__(self, "visibility_tier", visibility_tier)

        matched_offer_ids = tuple(self.matched_offer_ids)
        for offer_id in matched_offer_ids:
            _validate_required_string(offer_id, "matched_offer_id")
        object.__setattr__(self, "matched_offer_ids", matched_offer_ids)

        matched_offers = tuple(self.matched_offers)
        for offer in matched_offers:
            _validate_offer(offer)
        object.__setattr__(self, "matched_offers", matched_offers)

        status = self.status
        if isinstance(status, str):
            status = RendezvousPollStatus(status)
        if not isinstance(status, RendezvousPollStatus):
            raise TypeError("status must be a RendezvousPollStatus or string")
        object.__setattr__(self, "status", status)

        _validate_poll_reason(self.reason)
        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata or {}))

    @property
    def matched_count(self) -> int:
        """Return the number of discoverable offers in this result."""
        return len(self.matched_offer_ids)

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe rendezvous poll summary."""
        return {
            "request_id": self.request_id,
            "polling_hub_id": self.polling_hub_id,
            "parent_hub_id": self.parent_hub_id,
            "target_scope": self.target_scope,
            "visibility_tier": self.visibility_tier.tier,
            "matched_offer_ids": list(self.matched_offer_ids),
            "matched_count": self.matched_count,
            "matched_offers": [offer.to_summary() for offer in self.matched_offers],
            "status": self.status.status,
            "reason": self.reason,
            "metadata": _json_safe_copy(self.metadata or {}),
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


def make_stream_offer(
    *,
    offer_id: str,
    requester_id: str,
    target_handle: str,
    lane_signature: LaneSignature | str,
    requested_mode: str = "message",
    visibility_tier: int = 0,
    rendezvous_scope: str | None = None,
    created_order: int = 0,
    expires_order: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> StreamOffer:
    """Return a pure simulator-local stream offer record."""
    return StreamOffer(
        offer_id=offer_id,
        requester_id=requester_id,
        target_handle=target_handle,
        lane_signature=lane_signature,
        requested_mode=requested_mode,
        visibility_tier=visibility_tier,
        status="created",
        rendezvous_scope=rendezvous_scope,
        created_order=created_order,
        expires_order=expires_order,
        metadata=_helper_metadata(metadata),
    )


def make_basic_messaging_stream_offer(
    *,
    offer_id: str,
    requester_id: str,
    target_handle: str,
    rendezvous_scope: str | None = None,
    created_order: int = 0,
) -> StreamOffer:
    """Return a pure `basic_messaging:v1` stream offer record."""
    return make_stream_offer(
        offer_id=offer_id,
        requester_id=requester_id,
        target_handle=target_handle,
        lane_signature="basic_messaging:v1",
        requested_mode="message",
        visibility_tier=0,
        rendezvous_scope=rendezvous_scope,
        created_order=created_order,
        expires_order=None,
        metadata={
            "simulator_local": True,
            "request_only": True,
            "delivery_behavior_changed": False,
            "networking": False,
        },
    )


def make_rendezvous_request(
    *,
    request_id: str,
    offer_id: str,
    polling_hub_id: str,
    requester_id: str,
    target_scope: str,
    visibility_tier: int = 0,
    metadata: dict[str, Any] | None = None,
) -> RendezvousRequest:
    """Return pure metadata for a future rendezvous polling request."""
    return RendezvousRequest(
        request_id=request_id,
        offer_id=offer_id,
        polling_hub_id=polling_hub_id,
        requester_id=requester_id,
        target_scope=target_scope,
        visibility_tier=visibility_tier,
        metadata=_helper_metadata(metadata),
    )


def is_stream_offer_active(offer: StreamOffer) -> bool:
    """Return whether an offer has a non-terminal structural status."""
    _validate_offer(offer)
    return offer.status.status in STREAM_OFFER_ACTIVE_STATUSES


def is_stream_offer_terminal(offer: StreamOffer) -> bool:
    """Return whether an offer has a terminal structural status."""
    _validate_offer(offer)
    return offer.status.status in STREAM_OFFER_TERMINAL_STATUSES


def is_stream_offer_expired(offer: StreamOffer, *, current_order: int) -> bool:
    """Return whether an offer is expired by status or simulator order."""
    _validate_offer(offer)
    _validate_order(current_order, "current_order")
    return offer.status.status == "expired" or (
        offer.expires_order is not None and current_order >= offer.expires_order
    )


def stream_offer_matches_rendezvous_request(
    offer: StreamOffer,
    request: RendezvousRequest,
) -> bool:
    """Return whether an offer structurally matches a rendezvous request."""
    _validate_offer(offer)
    _validate_rendezvous_request(request)
    return (
        _stream_offer_visibility_compatible(offer, request)
        and (
            offer.rendezvous_scope is None
            or offer.rendezvous_scope == request.target_scope
        )
    )


def is_stream_offer_discoverable_to_request(
    offer: StreamOffer,
    request: RendezvousRequest,
    *,
    current_order: int | None = None,
) -> bool:
    """Return whether an active offer is discoverable for a request."""
    _validate_offer(offer)
    _validate_rendezvous_request(request)
    if current_order is not None:
        _validate_order(current_order, "current_order")
    if not stream_offer_matches_rendezvous_request(offer, request):
        return False
    if not is_stream_offer_active(offer):
        return False
    return not (
        current_order is not None
        and is_stream_offer_expired(
            offer,
            current_order=current_order,
        )
    )


def stream_offer_matches_lane(
    offer: StreamOffer,
    lane_signature: LaneSignature | str,
) -> bool:
    """Return whether the offer references the same compact lane signature."""
    _validate_offer(offer)
    if isinstance(lane_signature, LaneSignature):
        lane_signature = lane_signature.signature
    elif isinstance(lane_signature, str):
        lane_signature = parse_lane_signature(lane_signature).signature
    else:
        raise TypeError("lane_signature must be a LaneSignature or string")
    return offer.lane_signature == lane_signature


def _validate_offer(offer: StreamOffer) -> None:
    if not isinstance(offer, StreamOffer):
        raise TypeError("offer must be a StreamOffer")


def _validate_rendezvous_request(request: RendezvousRequest) -> None:
    if not isinstance(request, RendezvousRequest):
        raise TypeError("request must be a RendezvousRequest")


def _stream_offer_visibility_compatible(
    offer: StreamOffer,
    request: RendezvousRequest,
) -> bool:
    return offer.visibility_tier.tier <= request.visibility_tier.tier


def _helper_metadata(metadata: dict[str, Any] | None) -> dict[str, object]:
    if metadata is None:
        return {"simulator_local": True, "request_only": True}
    safe_metadata = _json_safe_copy(metadata)
    if not isinstance(safe_metadata, dict):
        raise TypeError("metadata must be a JSON-safe dict")
    return safe_metadata


def _validate_mode(value: str) -> None:
    _validate_required_string(value, "stream offer mode")
    if value not in STREAM_OFFER_MODES:
        raise ValueError(
            "stream offer mode must be one of " f"{', '.join(STREAM_OFFER_MODES)}"
        )


def _validate_status(value: str) -> None:
    _validate_required_string(value, "stream offer status")
    if value not in STREAM_OFFER_STATUSES:
        raise ValueError(
            "stream offer status must be one of " f"{', '.join(STREAM_OFFER_STATUSES)}"
        )


def _validate_poll_status(value: str) -> None:
    _validate_required_string(value, "rendezvous poll status")
    if value not in RENDEZVOUS_POLL_STATUSES:
        raise ValueError(
            "rendezvous poll status must be one of "
            f"{', '.join(RENDEZVOUS_POLL_STATUSES)}"
        )


def _validate_poll_reason(value: str) -> None:
    _validate_required_string(value, "rendezvous poll reason")
    if value not in RENDEZVOUS_POLL_REASONS:
        raise ValueError(
            "rendezvous poll reason must be one of "
            f"{', '.join(RENDEZVOUS_POLL_REASONS)}"
        )


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


def _validate_optional_order(value: int | None, field_name: str) -> None:
    if value is None:
        return
    _validate_order(value, field_name)


def _json_safe_copy(value: Any) -> object:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, tuple | list):
        return [_json_safe_copy(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe_copy(item) for key, item in value.items()}
    raise TypeError("stream offer data must be JSON-safe simulator data")
