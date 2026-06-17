"""Simulator-local encryption identity, key, and envelope models for v1.0."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from darwin.models.lane_signature import is_lane_signature
from darwin.models.message import MessageEnvelope

DEFAULT_ENCRYPTION_PROFILE = "symbolic_e2ee_v1"
DEFAULT_SYMBOLIC_ENVELOPE_ALGORITHM_REF = "symbolic-envelope"

ENCRYPTION_SUBJECT_KINDS: tuple[str, ...] = (
    "mailbox",
    "device",
    "resource",
)

ENCRYPTION_RECORD_STATUSES: tuple[str, ...] = (
    "active",
    "stale",
    "revoked",
    "disabled",
)

ENCRYPTION_STATES: tuple[str, ...] = (
    "plaintext",
    "symbolically_encrypted",
    "encryption_required",
    "encryption_failed",
)

ENCRYPTION_ENVELOPE_STATUSES: tuple[str, ...] = (
    "ready",
    "missing_key_bundle",
    "unsupported_profile",
    "stale_key_bundle",
    "disabled_identity",
)


@dataclass(frozen=True, slots=True)
class EncryptionProfile:
    """Symbolic simulator-local encryption profile label."""

    profile: str = DEFAULT_ENCRYPTION_PROFILE

    def __post_init__(self) -> None:
        _validate_required_string(self.profile, "profile")

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe profile summary."""
        return {"profile": self.profile}

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class EncryptionState:
    """Controlled simulator-local encrypted envelope state."""

    state: str = "plaintext"

    def __post_init__(self) -> None:
        _validate_encryption_state(self.state)

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe state summary."""
        return {"state": self.state}

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class EncryptionEnvelopeStatus:
    """Controlled simulator-local encrypted envelope readiness status."""

    status: str = "ready"

    def __post_init__(self) -> None:
        _validate_envelope_status(self.status)

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe status summary."""
        return {"status": self.status}

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class KeyBundleStatus:
    """Controlled simulator-local key bundle lifecycle status."""

    status: str = "active"

    def __post_init__(self) -> None:
        _validate_status(self.status, "key bundle status")

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe status summary."""
        return {"status": self.status}

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class EncryptedEnvelopeMetadata:
    """Symbolic metadata for plaintext or simulator-local encrypted envelopes."""

    envelope_id: str
    message_id: str
    encryption_identity_id: str | None = None
    key_bundle_id: str | None = None
    profile: EncryptionProfile | str = DEFAULT_ENCRYPTION_PROFILE
    state: EncryptionState | str = "plaintext"
    status: EncryptionEnvelopeStatus | str = "ready"
    algorithm_ref: str | None = None
    ciphertext_ref: str | None = None
    plaintext_ref: str | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _validate_required_string(self.envelope_id, "envelope_id")
        _validate_required_string(self.message_id, "message_id")
        _validate_optional_string(
            self.encryption_identity_id,
            "encryption_identity_id",
        )
        _validate_optional_string(self.key_bundle_id, "key_bundle_id")
        object.__setattr__(self, "profile", _profile_label(self.profile))

        state = self.state
        if isinstance(state, str):
            state = EncryptionState(state)
        if not isinstance(state, EncryptionState):
            raise TypeError("state must be an EncryptionState or string")
        object.__setattr__(self, "state", state)

        status = self.status
        if isinstance(status, str):
            status = EncryptionEnvelopeStatus(status)
        if not isinstance(status, EncryptionEnvelopeStatus):
            raise TypeError("status must be an EncryptionEnvelopeStatus or string")
        object.__setattr__(self, "status", status)

        _validate_optional_string(self.algorithm_ref, "algorithm_ref")
        _validate_optional_string(self.ciphertext_ref, "ciphertext_ref")
        _validate_optional_string(self.plaintext_ref, "plaintext_ref")
        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata or {}))

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe encrypted envelope metadata summary."""
        return {
            "envelope_id": self.envelope_id,
            "message_id": self.message_id,
            "encryption_identity_id": self.encryption_identity_id,
            "key_bundle_id": self.key_bundle_id,
            "profile": self.profile,
            "state": self.state.state,
            "status": self.status.status,
            "algorithm_ref": self.algorithm_ref,
            "ciphertext_ref": self.ciphertext_ref,
            "plaintext_ref": self.plaintext_ref,
            "metadata": _json_safe_copy(self.metadata or {}),
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class SymbolicEncryptedMessageEnvelope:
    """A message envelope wrapped with symbolic encrypted-envelope metadata."""

    message_id: str
    base_message: MessageEnvelope | dict[str, Any]
    encryption_metadata: EncryptedEnvelopeMetadata
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _validate_required_string(self.message_id, "message_id")
        if not isinstance(self.base_message, MessageEnvelope | dict):
            raise TypeError("base_message must be a MessageEnvelope or dict")
        if isinstance(self.base_message, dict):
            object.__setattr__(
                self,
                "base_message",
                _json_safe_copy(self.base_message),
            )
        if not isinstance(self.encryption_metadata, EncryptedEnvelopeMetadata):
            raise TypeError(
                "encryption_metadata must be an EncryptedEnvelopeMetadata"
            )
        if self.encryption_metadata.message_id != self.message_id:
            raise ValueError("encryption_metadata message_id must match message_id")
        if isinstance(self.base_message, MessageEnvelope):
            if self.base_message.message_id != self.message_id:
                raise ValueError("base_message message_id must match message_id")
        elif self.base_message.get("message_id") != self.message_id:
            raise ValueError("base_message message_id must match message_id")
        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata or {}))

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe symbolic envelope summary."""
        base_message = self.base_message
        if isinstance(base_message, MessageEnvelope):
            base_message = base_message.to_summary()
        else:
            base_message = _json_safe_copy(base_message)
        return {
            "message_id": self.message_id,
            "base_message": base_message,
            "encryption_metadata": self.encryption_metadata.to_summary(),
            "metadata": _json_safe_copy(self.metadata or {}),
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class EncryptionIdentity:
    """Simulator-local subject identity used for symbolic encryption planning."""

    encryption_identity_id: str
    subject_id: str
    subject_kind: str
    profile: EncryptionProfile | str = DEFAULT_ENCRYPTION_PROFILE
    status: str = "active"
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _validate_required_string(
            self.encryption_identity_id,
            "encryption_identity_id",
        )
        _validate_required_string(self.subject_id, "subject_id")
        _validate_subject_kind(self.subject_kind)
        object.__setattr__(self, "profile", _profile_label(self.profile))
        _validate_status(self.status, "encryption identity status")
        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata or {}))

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe encryption identity summary."""
        return {
            "encryption_identity_id": self.encryption_identity_id,
            "subject_id": self.subject_id,
            "subject_kind": self.subject_kind,
            "profile": self.profile,
            "status": self.status,
            "metadata": _json_safe_copy(self.metadata or {}),
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class KeyBundleReference:
    """Symbolic public key bundle reference with no private key material."""

    key_bundle_id: str
    encryption_identity_id: str
    profile: EncryptionProfile | str = DEFAULT_ENCRYPTION_PROFILE
    status: KeyBundleStatus | str = "active"
    public_ref: str | None = None
    created_order: int = 0
    rotated_from: str | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _validate_required_string(self.key_bundle_id, "key_bundle_id")
        _validate_required_string(
            self.encryption_identity_id,
            "encryption_identity_id",
        )
        object.__setattr__(self, "profile", _profile_label(self.profile))

        status = self.status
        if isinstance(status, str):
            status = KeyBundleStatus(status)
        if not isinstance(status, KeyBundleStatus):
            raise TypeError("status must be a KeyBundleStatus or string")
        object.__setattr__(self, "status", status)

        _validate_optional_string(self.public_ref, "public_ref")
        if not isinstance(self.created_order, int):
            raise TypeError("created_order must be an integer")
        if self.created_order < 0:
            raise ValueError("created_order must be greater than or equal to zero")
        _validate_optional_string(self.rotated_from, "rotated_from")
        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata or {}))

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe key bundle reference summary."""
        return {
            "key_bundle_id": self.key_bundle_id,
            "encryption_identity_id": self.encryption_identity_id,
            "profile": self.profile,
            "status": self.status.status,
            "public_ref": self.public_ref,
            "created_order": self.created_order,
            "rotated_from": self.rotated_from,
            "metadata": _json_safe_copy(self.metadata or {}),
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class MailboxEncryptionBinding:
    """Symbolic binding from a mailbox to encryption identity/key references."""

    mailbox_id: str
    encryption_identity_id: str
    key_bundle_id: str
    required_for_lanes: tuple[str, ...] | list[str] = field(default_factory=tuple)
    profile: EncryptionProfile | str = DEFAULT_ENCRYPTION_PROFILE
    status: str = "active"
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _validate_required_string(self.mailbox_id, "mailbox_id")
        _validate_required_string(
            self.encryption_identity_id,
            "encryption_identity_id",
        )
        _validate_required_string(self.key_bundle_id, "key_bundle_id")
        object.__setattr__(
            self,
            "required_for_lanes",
            _lane_signature_tuple(self.required_for_lanes),
        )
        object.__setattr__(self, "profile", _profile_label(self.profile))
        _validate_status(self.status, "mailbox encryption binding status")
        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata or {}))

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe mailbox encryption binding summary."""
        return {
            "mailbox_id": self.mailbox_id,
            "encryption_identity_id": self.encryption_identity_id,
            "key_bundle_id": self.key_bundle_id,
            "required_for_lanes": list(self.required_for_lanes),
            "profile": self.profile,
            "status": self.status,
            "metadata": _json_safe_copy(self.metadata or {}),
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


def make_symbolic_encryption_identity(
    *,
    encryption_identity_id: str,
    subject_id: str,
    subject_kind: str,
    profile: str = DEFAULT_ENCRYPTION_PROFILE,
) -> EncryptionIdentity:
    """Return a pure symbolic encryption identity record."""
    return EncryptionIdentity(
        encryption_identity_id=encryption_identity_id,
        subject_id=subject_id,
        subject_kind=subject_kind,
        profile=profile,
        status="active",
        metadata={"simulator_local": True},
    )


def make_symbolic_key_bundle_reference(
    *,
    key_bundle_id: str,
    encryption_identity_id: str,
    profile: str = DEFAULT_ENCRYPTION_PROFILE,
    public_ref: str | None = None,
) -> KeyBundleReference:
    """Return a pure symbolic public key bundle reference."""
    return KeyBundleReference(
        key_bundle_id=key_bundle_id,
        encryption_identity_id=encryption_identity_id,
        profile=profile,
        status="active",
        public_ref=public_ref,
        metadata={"simulator_local": True, "symbolic_public_ref": True},
    )


def bind_mailbox_encryption_identity(
    *,
    mailbox_id: str,
    encryption_identity_id: str,
    key_bundle_id: str,
    required_for_lanes: tuple[str, ...] = (),
    profile: str = DEFAULT_ENCRYPTION_PROFILE,
) -> MailboxEncryptionBinding:
    """Return a pure symbolic mailbox-to-encryption-reference binding."""
    return MailboxEncryptionBinding(
        mailbox_id=mailbox_id,
        encryption_identity_id=encryption_identity_id,
        key_bundle_id=key_bundle_id,
        required_for_lanes=required_for_lanes,
        profile=profile,
        status="active",
        metadata={"simulator_local": True},
    )


def make_symbolic_encrypted_envelope_metadata(
    *,
    envelope_id: str,
    message_id: str,
    encryption_identity_id: str,
    key_bundle_id: str,
    profile: str = DEFAULT_ENCRYPTION_PROFILE,
    algorithm_ref: str = DEFAULT_SYMBOLIC_ENVELOPE_ALGORITHM_REF,
    ciphertext_ref: str | None = None,
) -> EncryptedEnvelopeMetadata:
    """Return pure symbolic encrypted-envelope metadata without encryption."""
    if ciphertext_ref is None:
        ciphertext_ref = f"symbolic://ciphertext/{envelope_id}"
    return EncryptedEnvelopeMetadata(
        envelope_id=envelope_id,
        message_id=message_id,
        encryption_identity_id=encryption_identity_id,
        key_bundle_id=key_bundle_id,
        profile=profile,
        state="symbolically_encrypted",
        status=(
            "ready"
            if is_encryption_profile_supported(profile)
            else "unsupported_profile"
        ),
        algorithm_ref=algorithm_ref,
        ciphertext_ref=ciphertext_ref,
        plaintext_ref=None,
        metadata={
            "simulator_local": True,
            "symbolic_envelope": True,
            "real_ciphertext": False,
        },
    )


def wrap_message_symbolically(
    message_envelope: MessageEnvelope,
    encryption_metadata: EncryptedEnvelopeMetadata,
) -> SymbolicEncryptedMessageEnvelope:
    """Wrap a message envelope with symbolic metadata without mutating it."""
    if not isinstance(message_envelope, MessageEnvelope):
        raise TypeError("message_envelope must be a MessageEnvelope")
    if not isinstance(encryption_metadata, EncryptedEnvelopeMetadata):
        raise TypeError("encryption_metadata must be an EncryptedEnvelopeMetadata")
    if encryption_metadata.message_id != message_envelope.message_id:
        raise ValueError("encryption_metadata message_id must match message envelope")
    return SymbolicEncryptedMessageEnvelope(
        message_id=message_envelope.message_id,
        base_message=message_envelope,
        encryption_metadata=encryption_metadata,
        metadata={"simulator_local": True, "message_mutated": False},
    )


def is_envelope_symbolically_encrypted(
    envelope_or_metadata: (
        SymbolicEncryptedMessageEnvelope | EncryptedEnvelopeMetadata
    ),
) -> bool:
    """Return whether an envelope carries symbolic encrypted state."""
    if isinstance(envelope_or_metadata, SymbolicEncryptedMessageEnvelope):
        envelope_or_metadata = envelope_or_metadata.encryption_metadata
    if not isinstance(envelope_or_metadata, EncryptedEnvelopeMetadata):
        raise TypeError(
            "envelope_or_metadata must be an encrypted envelope or metadata"
        )
    return envelope_or_metadata.state.state == "symbolically_encrypted"


def is_encryption_profile_supported(profile: EncryptionProfile | str) -> bool:
    """Return whether a symbolic encryption profile is supported locally."""
    return _profile_label(profile) == DEFAULT_ENCRYPTION_PROFILE


def is_envelope_ready_for_delivery(
    metadata: EncryptedEnvelopeMetadata,
) -> bool:
    """Return whether symbolic envelope metadata is ready for future policy use."""
    if not isinstance(metadata, EncryptedEnvelopeMetadata):
        raise TypeError("metadata must be an EncryptedEnvelopeMetadata")
    return (
        metadata.status.status == "ready"
        and metadata.state.state in {"plaintext", "symbolically_encrypted"}
        and is_encryption_profile_supported(metadata.profile)
    )


def is_encryption_identity_active(identity: EncryptionIdentity) -> bool:
    """Return whether a symbolic encryption identity is active."""
    if not isinstance(identity, EncryptionIdentity):
        raise TypeError("identity must be an EncryptionIdentity")
    return identity.status == "active"


def is_key_bundle_usable(key_bundle: KeyBundleReference) -> bool:
    """Return whether a symbolic key bundle reference is usable."""
    if not isinstance(key_bundle, KeyBundleReference):
        raise TypeError("key_bundle must be a KeyBundleReference")
    return key_bundle.status.status == "active"


def _validate_encryption_state(value: str) -> None:
    _validate_required_string(value, "encryption state")
    if value not in ENCRYPTION_STATES:
        raise ValueError(
            f"encryption state must be one of {', '.join(ENCRYPTION_STATES)}"
        )


def _validate_envelope_status(value: str) -> None:
    _validate_required_string(value, "encryption envelope status")
    if value not in ENCRYPTION_ENVELOPE_STATUSES:
        raise ValueError(
            "encryption envelope status must be one of "
            f"{', '.join(ENCRYPTION_ENVELOPE_STATUSES)}"
        )


def _profile_label(profile: EncryptionProfile | str) -> str:
    if isinstance(profile, str):
        return EncryptionProfile(profile).profile
    if not isinstance(profile, EncryptionProfile):
        raise TypeError("profile must be an EncryptionProfile or string")
    return profile.profile


def _validate_subject_kind(value: str) -> None:
    _validate_required_string(value, "subject_kind")
    if value not in ENCRYPTION_SUBJECT_KINDS:
        raise ValueError(
            f"subject_kind must be one of {', '.join(ENCRYPTION_SUBJECT_KINDS)}"
        )


def _validate_status(value: str, field_name: str) -> None:
    _validate_required_string(value, field_name)
    if value not in ENCRYPTION_RECORD_STATUSES:
        raise ValueError(
            f"{field_name} must be one of {', '.join(ENCRYPTION_RECORD_STATUSES)}"
        )


def _lane_signature_tuple(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    if not isinstance(values, tuple | list):
        raise TypeError("required_for_lanes must be a list or tuple of lane signatures")
    for value in values:
        if not is_lane_signature(value):
            raise ValueError("required_for_lanes entries must use the form lane_id:version")
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
    raise TypeError("metadata must be JSON-safe simulator data")
