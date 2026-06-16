"""Simulator-local message envelope and delivery result models for v0.9."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from darwin.models.lane_signature import LaneSignature, parse_lane_signature
from darwin.models.mailbox import parse_mailbox_address

MESSAGE_DELIVERY_STATUSES: tuple[str, ...] = (
    "delivered",
    "queued",
    "held",
    "bounced",
    "rejected",
    "failed",
)

MESSAGE_DELIVERY_FAILURE_REASONS: tuple[str, ...] = (
    "mailbox_not_found",
    "lane_not_registered",
    "mailbox_missing_capability",
    "capability_disabled",
    "endpoint_not_found",
    "endpoint_unavailable",
    "endpoint_lane_mismatch",
    "payload_kind_mismatch",
    "recipient_quarantined",
    "device_in_transit",
    "unknown",
)


@dataclass(frozen=True, slots=True)
class MessageDeliveryStatus:
    """Controlled simulator-local message delivery status."""

    status: str

    def __post_init__(self) -> None:
        if self.status not in MESSAGE_DELIVERY_STATUSES:
            raise ValueError(
                "message delivery status must be one of "
                f"{', '.join(MESSAGE_DELIVERY_STATUSES)}"
            )

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe delivery status summary."""
        return {"status": self.status}

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class MessageDeliveryFailureReason:
    """Controlled simulator-local message delivery failure reason."""

    reason: str

    def __post_init__(self) -> None:
        if self.reason not in MESSAGE_DELIVERY_FAILURE_REASONS:
            raise ValueError(
                "message delivery failure reason must be one of "
                f"{', '.join(MESSAGE_DELIVERY_FAILURE_REASONS)}"
            )

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe failure reason summary."""
        return {"reason": self.reason}

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class MessageEnvelope:
    """Simulator-local symbolic message envelope for mailbox delivery tests."""

    message_id: str
    sender_id: str
    recipient_address: str
    lane_signature: LaneSignature | str
    payload_kind: str
    payload: Any
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _validate_required_string(self.message_id, "message_id")
        _validate_required_string(self.sender_id, "sender_id")
        address = parse_mailbox_address(self.recipient_address)
        object.__setattr__(self, "recipient_address", address.raw)

        lane_signature = self.lane_signature
        if isinstance(lane_signature, LaneSignature):
            lane_signature = lane_signature.signature
        elif isinstance(lane_signature, str):
            lane_signature = parse_lane_signature(lane_signature).signature
        else:
            raise TypeError("lane_signature must be a LaneSignature or string")
        object.__setattr__(self, "lane_signature", lane_signature)

        _validate_required_string(self.payload_kind, "payload_kind")
        object.__setattr__(self, "payload", _json_safe_copy(self.payload))
        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata or {}))

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe message envelope summary."""
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "recipient_address": self.recipient_address,
            "lane_signature": self.lane_signature,
            "payload_kind": self.payload_kind,
            "payload": _json_safe_copy(self.payload),
            "metadata": _json_safe_copy(self.metadata or {}),
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class MessageDeliveryResult:
    """Simulator-local retained result for an attempted mailbox delivery."""

    message_id: str
    recipient_address: str
    resolved_mailbox_id: str | None
    target_device_id: str | None
    lane_signature: LaneSignature | str
    endpoint_id: str | None
    status: MessageDeliveryStatus | str
    reason: MessageDeliveryFailureReason | str | None = None
    fallback_action: str | None = None
    audit_path: tuple[str, ...] | list[str] = ()
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _validate_required_string(self.message_id, "message_id")
        address = parse_mailbox_address(self.recipient_address)
        object.__setattr__(self, "recipient_address", address.raw)
        _validate_optional_string(self.resolved_mailbox_id, "resolved_mailbox_id")
        _validate_optional_string(self.target_device_id, "target_device_id")
        _validate_optional_string(self.endpoint_id, "endpoint_id")
        _validate_optional_string(self.fallback_action, "fallback_action")

        lane_signature = self.lane_signature
        if isinstance(lane_signature, LaneSignature):
            lane_signature = lane_signature.signature
        elif isinstance(lane_signature, str):
            lane_signature = parse_lane_signature(lane_signature).signature
        else:
            raise TypeError("lane_signature must be a LaneSignature or string")
        object.__setattr__(self, "lane_signature", lane_signature)

        status = self.status
        if isinstance(status, str):
            status = MessageDeliveryStatus(status)
        if not isinstance(status, MessageDeliveryStatus):
            raise TypeError("status must be a MessageDeliveryStatus or string")
        object.__setattr__(self, "status", status)

        reason = self.reason
        if isinstance(reason, str):
            reason = MessageDeliveryFailureReason(reason)
        if reason is not None and not isinstance(reason, MessageDeliveryFailureReason):
            raise TypeError(
                "reason must be a MessageDeliveryFailureReason, string, or None"
            )
        object.__setattr__(self, "reason", reason)

        object.__setattr__(self, "audit_path", _string_tuple(self.audit_path))
        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata or {}))

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe delivery result summary."""
        return {
            "message_id": self.message_id,
            "recipient_address": self.recipient_address,
            "resolved_mailbox_id": self.resolved_mailbox_id,
            "target_device_id": self.target_device_id,
            "lane_signature": self.lane_signature,
            "endpoint_id": self.endpoint_id,
            "status": self.status.status,
            "reason": None if self.reason is None else self.reason.reason,
            "fallback_action": self.fallback_action,
            "audit_path": list(self.audit_path),
            "metadata": _json_safe_copy(self.metadata or {}),
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


def make_basic_message_envelope(
    *,
    message_id: str,
    sender_id: str,
    recipient_address: str,
    payload: str,
) -> MessageEnvelope:
    """Return a pure `basic_messaging:v1` symbolic text message envelope."""
    return MessageEnvelope(
        message_id=message_id,
        sender_id=sender_id,
        recipient_address=recipient_address,
        lane_signature="basic_messaging:v1",
        payload_kind="text",
        payload=payload,
        metadata={"simulator_local": True},
    )


def _string_tuple(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    if not isinstance(values, tuple | list):
        raise TypeError("audit_path must be a list or tuple of strings")
    for value in values:
        _validate_required_string(value, "audit_path entry")
    return tuple(values)


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


def _json_safe_copy(value: Any) -> object:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, tuple | list):
        return [_json_safe_copy(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe_copy(item) for key, item in value.items()}
    raise TypeError("message data must be JSON-safe simulator data")
