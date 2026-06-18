"""Simulator-local symbolic encrypted delivery request models for v1.1."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from darwin.models.encryption import EncryptedEnvelopeMetadata
from darwin.models.lane_signature import LaneSignature, parse_lane_signature
from darwin.models.message import MessageEnvelope

ENCRYPTED_DELIVERY_REQUEST_MODES: tuple[str, ...] = (
    "plaintext",
    "symbolic_encrypted",
    "policy_check_only",
)

ENCRYPTED_DELIVERY_REQUEST_STATUSES: tuple[str, ...] = (
    "plaintext",
    "symbolic_encrypted",
    "missing_envelope",
    "policy_check_only",
    "invalid",
)


@dataclass(frozen=True, slots=True)
class EncryptedDeliveryRequestMode:
    """Controlled simulator-local encrypted delivery request mode."""

    mode: str

    def __post_init__(self) -> None:
        _validate_request_mode(self.mode)

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe request mode summary."""
        return {"mode": self.mode}

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class EncryptedDeliveryRequestStatus:
    """Controlled symbolic status for an encrypted delivery request record."""

    status: str

    def __post_init__(self) -> None:
        _validate_request_status(self.status)

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe request status summary."""
        return {"status": self.status}

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class EncryptedDeliveryRequest:
    """Symbolic request record for future encrypted delivery policy gates."""

    request_id: str
    message_envelope: MessageEnvelope | dict[str, Any] | None = None
    encryption_metadata: EncryptedEnvelopeMetadata | dict[str, Any] | None = None
    mode: EncryptedDeliveryRequestMode | str = "plaintext"
    policy_required: bool = False
    policy_id: str | None = None
    mailbox_id: str | None = None
    lane_signature: LaneSignature | str | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _validate_required_string(self.request_id, "request_id")

        message_envelope = self.message_envelope
        if message_envelope is not None and not isinstance(
            message_envelope,
            MessageEnvelope | dict,
        ):
            raise TypeError("message_envelope must be a MessageEnvelope, dict, or None")
        if isinstance(message_envelope, dict):
            message_envelope = _json_safe_dict(message_envelope, "message_envelope")
        object.__setattr__(self, "message_envelope", message_envelope)

        encryption_metadata = self.encryption_metadata
        if encryption_metadata is not None and not isinstance(
            encryption_metadata,
            EncryptedEnvelopeMetadata | dict,
        ):
            raise TypeError(
                "encryption_metadata must be an EncryptedEnvelopeMetadata, dict, or None"
            )
        if isinstance(encryption_metadata, dict):
            encryption_metadata = _json_safe_dict(
                encryption_metadata,
                "encryption_metadata",
            )
        object.__setattr__(self, "encryption_metadata", encryption_metadata)

        mode = self.mode
        if isinstance(mode, str):
            mode = EncryptedDeliveryRequestMode(mode)
        if not isinstance(mode, EncryptedDeliveryRequestMode):
            raise TypeError("mode must be an EncryptedDeliveryRequestMode or string")
        object.__setattr__(self, "mode", mode)

        if not isinstance(self.policy_required, bool):
            raise TypeError("policy_required must be a boolean")
        _validate_optional_string(self.policy_id, "policy_id")
        _validate_optional_string(self.mailbox_id, "mailbox_id")

        lane_signature = self.lane_signature
        if lane_signature is None:
            lane_signature = _message_lane_signature(message_envelope)
        else:
            lane_signature = _lane_signature_key(lane_signature)
        object.__setattr__(self, "lane_signature", lane_signature)

        _validate_message_ids_match(message_envelope, encryption_metadata)
        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata or {}))

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe encrypted delivery request summary."""
        return {
            "request_id": self.request_id,
            "message_envelope": _request_message_summary(self.message_envelope),
            "encryption_metadata": _request_encryption_metadata_summary(
                self.encryption_metadata,
            ),
            "mode": self.mode.mode,
            "policy_required": self.policy_required,
            "policy_id": self.policy_id,
            "mailbox_id": self.mailbox_id,
            "lane_signature": self.lane_signature,
            "metadata": _json_safe_copy(self.metadata or {}),
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


def make_plaintext_delivery_request(
    *,
    request_id: str,
    message_envelope: MessageEnvelope | dict[str, Any],
    mailbox_id: str | None = None,
    policy_id: str | None = None,
) -> EncryptedDeliveryRequest:
    """Return a pure plaintext symbolic delivery request record."""
    return EncryptedDeliveryRequest(
        request_id=request_id,
        message_envelope=message_envelope,
        encryption_metadata=None,
        mode="plaintext",
        policy_required=policy_id is not None,
        policy_id=policy_id,
        mailbox_id=mailbox_id,
        metadata={
            "simulator_local": True,
            "request_only": True,
            "delivery_behavior_changed": False,
        },
    )


def make_symbolic_encrypted_delivery_request(
    *,
    request_id: str,
    message_envelope: MessageEnvelope | dict[str, Any],
    encryption_metadata: EncryptedEnvelopeMetadata | dict[str, Any],
    mailbox_id: str | None = None,
    policy_id: str | None = None,
) -> EncryptedDeliveryRequest:
    """Return a pure symbolic encrypted delivery request record."""
    return EncryptedDeliveryRequest(
        request_id=request_id,
        message_envelope=message_envelope,
        encryption_metadata=encryption_metadata,
        mode="symbolic_encrypted",
        policy_required=policy_id is not None,
        policy_id=policy_id,
        mailbox_id=mailbox_id,
        metadata={
            "simulator_local": True,
            "request_only": True,
            "delivery_behavior_changed": False,
            "real_ciphertext": False,
        },
    )


def make_policy_check_only_delivery_request(
    *,
    request_id: str,
    lane_signature: LaneSignature | str = "basic_messaging:v1",
    mailbox_id: str | None = None,
    policy_id: str | None = None,
) -> EncryptedDeliveryRequest:
    """Return a pure request record for a future policy check without delivery."""
    return EncryptedDeliveryRequest(
        request_id=request_id,
        message_envelope=None,
        encryption_metadata=None,
        mode="policy_check_only",
        policy_required=True,
        policy_id=policy_id,
        mailbox_id=mailbox_id,
        lane_signature=lane_signature,
        metadata={
            "simulator_local": True,
            "request_only": True,
            "delivery_behavior_changed": False,
        },
    )


def is_delivery_request_symbolically_encrypted(
    request: EncryptedDeliveryRequest,
) -> bool:
    """Return whether a request carries symbolic encrypted envelope metadata."""
    _validate_request(request)
    return (
        request.mode.mode == "symbolic_encrypted"
        and request.encryption_metadata is not None
    )


def is_delivery_request_plaintext(request: EncryptedDeliveryRequest) -> bool:
    """Return whether a request is explicitly plaintext."""
    _validate_request(request)
    return request.mode.mode == "plaintext" and request.encryption_metadata is None


def delivery_request_requires_policy(request: EncryptedDeliveryRequest) -> bool:
    """Return whether the request records future policy-gate intent."""
    _validate_request(request)
    return request.policy_required


def delivery_request_status(
    request: EncryptedDeliveryRequest,
) -> EncryptedDeliveryRequestStatus:
    """Return a symbolic structural status without evaluating policy or delivery."""
    _validate_request(request)
    if request.mode.mode == "policy_check_only":
        return EncryptedDeliveryRequestStatus("policy_check_only")
    if request.message_envelope is None:
        return EncryptedDeliveryRequestStatus("missing_envelope")
    if request.mode.mode == "plaintext":
        if request.encryption_metadata is None:
            return EncryptedDeliveryRequestStatus("plaintext")
        return EncryptedDeliveryRequestStatus("invalid")
    if request.mode.mode == "symbolic_encrypted":
        if request.encryption_metadata is not None:
            return EncryptedDeliveryRequestStatus("symbolic_encrypted")
        return EncryptedDeliveryRequestStatus("missing_envelope")
    return EncryptedDeliveryRequestStatus("invalid")


def _validate_request(request: EncryptedDeliveryRequest) -> None:
    if not isinstance(request, EncryptedDeliveryRequest):
        raise TypeError("request must be an EncryptedDeliveryRequest")


def _request_message_summary(
    message_envelope: MessageEnvelope | dict[str, Any] | None,
) -> dict[str, object] | None:
    if message_envelope is None:
        return None
    if isinstance(message_envelope, MessageEnvelope):
        return message_envelope.to_summary()
    return _json_safe_dict(message_envelope, "message_envelope")


def _request_encryption_metadata_summary(
    encryption_metadata: EncryptedEnvelopeMetadata | dict[str, Any] | None,
) -> dict[str, object] | None:
    if encryption_metadata is None:
        return None
    if isinstance(encryption_metadata, EncryptedEnvelopeMetadata):
        return encryption_metadata.to_summary()
    return _json_safe_dict(encryption_metadata, "encryption_metadata")


def _message_lane_signature(
    message_envelope: MessageEnvelope | dict[str, Any] | None,
) -> str | None:
    if isinstance(message_envelope, MessageEnvelope):
        return _lane_signature_key(message_envelope.lane_signature)
    if isinstance(message_envelope, dict):
        value = message_envelope.get("lane_signature")
        if value is None:
            return None
        if not isinstance(value, str):
            raise TypeError("message_envelope lane_signature must be a string")
        return _lane_signature_key(value)
    return None


def _validate_message_ids_match(
    message_envelope: MessageEnvelope | dict[str, Any] | None,
    encryption_metadata: EncryptedEnvelopeMetadata | dict[str, Any] | None,
) -> None:
    message_id = _message_id(message_envelope)
    encryption_message_id = _encryption_message_id(encryption_metadata)
    if (
        message_id is not None
        and encryption_message_id is not None
        and message_id != encryption_message_id
    ):
        raise ValueError("message_envelope message_id must match encryption_metadata")


def _message_id(message_envelope: MessageEnvelope | dict[str, Any] | None) -> str | None:
    if isinstance(message_envelope, MessageEnvelope):
        return message_envelope.message_id
    if isinstance(message_envelope, dict):
        value = message_envelope.get("message_id")
        if value is not None and not isinstance(value, str):
            raise TypeError("message_envelope message_id must be a string")
        return value
    return None


def _encryption_message_id(
    encryption_metadata: EncryptedEnvelopeMetadata | dict[str, Any] | None,
) -> str | None:
    if isinstance(encryption_metadata, EncryptedEnvelopeMetadata):
        return encryption_metadata.message_id
    if isinstance(encryption_metadata, dict):
        value = encryption_metadata.get("message_id")
        if value is not None and not isinstance(value, str):
            raise TypeError("encryption_metadata message_id must be a string")
        return value
    return None


def _lane_signature_key(lane_signature: LaneSignature | str) -> str:
    if isinstance(lane_signature, LaneSignature):
        return lane_signature.signature
    if isinstance(lane_signature, str):
        return parse_lane_signature(lane_signature).signature
    raise TypeError("lane_signature must be a LaneSignature or string")


def _validate_request_mode(value: str) -> None:
    _validate_required_string(value, "encrypted delivery request mode")
    if value not in ENCRYPTED_DELIVERY_REQUEST_MODES:
        raise ValueError(
            "encrypted delivery request mode must be one of "
            f"{', '.join(ENCRYPTED_DELIVERY_REQUEST_MODES)}"
        )


def _validate_request_status(value: str) -> None:
    _validate_required_string(value, "encrypted delivery request status")
    if value not in ENCRYPTED_DELIVERY_REQUEST_STATUSES:
        raise ValueError(
            "encrypted delivery request status must be one of "
            f"{', '.join(ENCRYPTED_DELIVERY_REQUEST_STATUSES)}"
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


def _json_safe_dict(value: dict[str, Any], field_name: str) -> dict[str, object]:
    safe_value = _json_safe_copy(value)
    if not isinstance(safe_value, dict):
        raise TypeError(f"{field_name} must be a JSON-safe dict")
    return safe_value


def _json_safe_copy(value: Any) -> object:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, tuple | list):
        return [_json_safe_copy(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe_copy(item) for key, item in value.items()}
    raise TypeError("request data must be JSON-safe simulator data")

