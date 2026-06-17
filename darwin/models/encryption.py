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

ENCRYPTION_POLICY_DECISION_STATUSES: tuple[str, ...] = (
    "accepted",
    "plaintext_allowed",
    "rejected",
    "needs_encryption",
    "missing_envelope",
    "missing_identity",
    "missing_key_bundle",
    "unsupported_profile",
    "identity_inactive",
    "key_bundle_unusable",
    "envelope_not_ready",
)

ENCRYPTION_POLICY_FAILURE_REASONS: tuple[str, ...] = (
    "plaintext_fallback_allowed",
    "needs_encryption",
    "missing_envelope",
    "missing_identity",
    "missing_key_bundle",
    "unsupported_profile",
    "identity_inactive",
    "key_bundle_unusable",
    "envelope_not_ready",
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
class EncryptionPolicyDecisionStatus:
    """Controlled simulator-local mailbox encryption policy decision status."""

    status: str

    def __post_init__(self) -> None:
        _validate_policy_decision_status(self.status)

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe decision status summary."""
        return {"status": self.status}

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class EncryptionPolicyFailureReason:
    """Controlled simulator-local mailbox encryption policy failure reason."""

    reason: str

    def __post_init__(self) -> None:
        _validate_policy_failure_reason(self.reason)

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe policy failure reason summary."""
        return {"reason": self.reason}

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


@dataclass(frozen=True, slots=True)
class MailboxEncryptionPolicy:
    """Simulator-local policy for lane-specific symbolic encryption checks."""

    policy_id: str
    mailbox_id: str
    required_for_lanes: tuple[str, ...] | list[str] = ("basic_messaging:v1",)
    allowed_profiles: tuple[str, ...] | list[str] = (DEFAULT_ENCRYPTION_PROFILE,)
    require_active_identity: bool = True
    require_usable_key_bundle: bool = True
    allow_plaintext_fallback: bool = False
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _validate_required_string(self.policy_id, "policy_id")
        _validate_required_string(self.mailbox_id, "mailbox_id")
        object.__setattr__(
            self,
            "required_for_lanes",
            _lane_signature_tuple(self.required_for_lanes),
        )
        object.__setattr__(
            self,
            "allowed_profiles",
            _profile_label_tuple(self.allowed_profiles),
        )
        if not isinstance(self.require_active_identity, bool):
            raise TypeError("require_active_identity must be a boolean")
        if not isinstance(self.require_usable_key_bundle, bool):
            raise TypeError("require_usable_key_bundle must be a boolean")
        if not isinstance(self.allow_plaintext_fallback, bool):
            raise TypeError("allow_plaintext_fallback must be a boolean")
        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata or {}))

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe mailbox encryption policy summary."""
        return {
            "policy_id": self.policy_id,
            "mailbox_id": self.mailbox_id,
            "required_for_lanes": list(self.required_for_lanes),
            "allowed_profiles": list(self.allowed_profiles),
            "require_active_identity": self.require_active_identity,
            "require_usable_key_bundle": self.require_usable_key_bundle,
            "allow_plaintext_fallback": self.allow_plaintext_fallback,
            "metadata": _json_safe_copy(self.metadata or {}),
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class EncryptionPolicyDecision:
    """Result of a pure symbolic mailbox encryption policy evaluation."""

    policy_id: str
    mailbox_id: str
    lane_signature: str
    message_id: str | None
    status: EncryptionPolicyDecisionStatus | str
    reason: EncryptionPolicyFailureReason | str | None
    encryption_required: bool
    envelope_accepted: bool
    profile: EncryptionProfile | str | None = None
    encryption_identity_id: str | None = None
    key_bundle_id: str | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _validate_required_string(self.policy_id, "policy_id")
        _validate_required_string(self.mailbox_id, "mailbox_id")
        object.__setattr__(
            self,
            "lane_signature",
            _lane_signature_key(self.lane_signature),
        )
        _validate_optional_string(self.message_id, "message_id")

        status = self.status
        if isinstance(status, str):
            status = EncryptionPolicyDecisionStatus(status)
        if not isinstance(status, EncryptionPolicyDecisionStatus):
            raise TypeError("status must be an EncryptionPolicyDecisionStatus or string")
        object.__setattr__(self, "status", status)

        reason = self.reason
        if isinstance(reason, str):
            reason = EncryptionPolicyFailureReason(reason)
        if reason is not None and not isinstance(reason, EncryptionPolicyFailureReason):
            raise TypeError(
                "reason must be an EncryptionPolicyFailureReason, string, or None"
            )
        object.__setattr__(self, "reason", reason)

        if not isinstance(self.encryption_required, bool):
            raise TypeError("encryption_required must be a boolean")
        if not isinstance(self.envelope_accepted, bool):
            raise TypeError("envelope_accepted must be a boolean")
        if self.profile is not None:
            object.__setattr__(self, "profile", _profile_label(self.profile))
        _validate_optional_string(
            self.encryption_identity_id,
            "encryption_identity_id",
        )
        _validate_optional_string(self.key_bundle_id, "key_bundle_id")
        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata or {}))

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe policy decision summary."""
        return {
            "policy_id": self.policy_id,
            "mailbox_id": self.mailbox_id,
            "lane_signature": self.lane_signature,
            "message_id": self.message_id,
            "status": self.status.status,
            "reason": None if self.reason is None else self.reason.reason,
            "encryption_required": self.encryption_required,
            "envelope_accepted": self.envelope_accepted,
            "profile": self.profile,
            "encryption_identity_id": self.encryption_identity_id,
            "key_bundle_id": self.key_bundle_id,
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


def make_mailbox_encryption_policy(
    *,
    policy_id: str,
    mailbox_id: str,
    required_for_lanes: tuple[str, ...] = ("basic_messaging:v1",),
    allowed_profiles: tuple[str, ...] = (DEFAULT_ENCRYPTION_PROFILE,),
    require_active_identity: bool = True,
    require_usable_key_bundle: bool = True,
    allow_plaintext_fallback: bool = False,
) -> MailboxEncryptionPolicy:
    """Return a pure simulator-local mailbox encryption policy record."""
    return MailboxEncryptionPolicy(
        policy_id=policy_id,
        mailbox_id=mailbox_id,
        required_for_lanes=required_for_lanes,
        allowed_profiles=allowed_profiles,
        require_active_identity=require_active_identity,
        require_usable_key_bundle=require_usable_key_bundle,
        allow_plaintext_fallback=allow_plaintext_fallback,
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


def evaluate_mailbox_encryption_policy(
    policy: MailboxEncryptionPolicy,
    *,
    lane_signature: str,
    message_id: str | None = None,
    envelope_metadata: (
        EncryptedEnvelopeMetadata | SymbolicEncryptedMessageEnvelope | None
    ) = None,
    encryption_identity: EncryptionIdentity | None = None,
    key_bundle: KeyBundleReference | None = None,
) -> EncryptionPolicyDecision:
    """Evaluate a pure symbolic mailbox encryption policy decision."""
    if not isinstance(policy, MailboxEncryptionPolicy):
        raise TypeError("policy must be a MailboxEncryptionPolicy")
    lane_signature = _lane_signature_key(lane_signature)
    _validate_optional_string(message_id, "message_id")

    metadata = envelope_metadata
    if isinstance(metadata, SymbolicEncryptedMessageEnvelope):
        metadata = metadata.encryption_metadata
    if metadata is not None and not isinstance(metadata, EncryptedEnvelopeMetadata):
        raise TypeError(
            "envelope_metadata must be encrypted metadata, a symbolic envelope, or None"
        )
    if metadata is not None:
        if message_id is None:
            message_id = metadata.message_id
        elif message_id != metadata.message_id:
            raise ValueError("message_id must match envelope metadata")

    encryption_required = is_lane_encryption_required(policy, lane_signature)
    if not encryption_required:
        return _make_policy_decision(
            policy,
            lane_signature=lane_signature,
            message_id=message_id,
            status="plaintext_allowed",
            reason=None,
            encryption_required=False,
            envelope_accepted=False,
            envelope_metadata=metadata,
            note="lane_not_required",
        )

    if metadata is None:
        if policy.allow_plaintext_fallback:
            return _make_policy_decision(
                policy,
                lane_signature=lane_signature,
                message_id=message_id,
                status="plaintext_allowed",
                reason="plaintext_fallback_allowed",
                encryption_required=True,
                envelope_accepted=False,
                note="plaintext_fallback_allowed",
            )
        return _make_policy_decision(
            policy,
            lane_signature=lane_signature,
            message_id=message_id,
            status="missing_envelope",
            reason="missing_envelope",
            encryption_required=True,
            envelope_accepted=False,
        )

    if metadata.profile not in policy.allowed_profiles:
        return _make_policy_decision(
            policy,
            lane_signature=lane_signature,
            message_id=message_id,
            status="unsupported_profile",
            reason="unsupported_profile",
            encryption_required=True,
            envelope_accepted=False,
            envelope_metadata=metadata,
        )

    if not is_envelope_symbolically_encrypted(metadata):
        return _make_policy_decision(
            policy,
            lane_signature=lane_signature,
            message_id=message_id,
            status="needs_encryption",
            reason="needs_encryption",
            encryption_required=True,
            envelope_accepted=False,
            envelope_metadata=metadata,
        )

    if policy.require_active_identity:
        if encryption_identity is None:
            return _make_policy_decision(
                policy,
                lane_signature=lane_signature,
                message_id=message_id,
                status="missing_identity",
                reason="missing_identity",
                encryption_required=True,
                envelope_accepted=False,
                envelope_metadata=metadata,
            )
        if not isinstance(encryption_identity, EncryptionIdentity):
            raise TypeError("encryption_identity must be an EncryptionIdentity or None")
        if not is_encryption_identity_active(encryption_identity):
            return _make_policy_decision(
                policy,
                lane_signature=lane_signature,
                message_id=message_id,
                status="identity_inactive",
                reason="identity_inactive",
                encryption_required=True,
                envelope_accepted=False,
                envelope_metadata=metadata,
                encryption_identity=encryption_identity,
            )

    if policy.require_usable_key_bundle:
        if key_bundle is None:
            return _make_policy_decision(
                policy,
                lane_signature=lane_signature,
                message_id=message_id,
                status="missing_key_bundle",
                reason="missing_key_bundle",
                encryption_required=True,
                envelope_accepted=False,
                envelope_metadata=metadata,
                encryption_identity=encryption_identity,
            )
        if not isinstance(key_bundle, KeyBundleReference):
            raise TypeError("key_bundle must be a KeyBundleReference or None")
        if not is_key_bundle_usable(key_bundle):
            return _make_policy_decision(
                policy,
                lane_signature=lane_signature,
                message_id=message_id,
                status="key_bundle_unusable",
                reason="key_bundle_unusable",
                encryption_required=True,
                envelope_accepted=False,
                envelope_metadata=metadata,
                encryption_identity=encryption_identity,
                key_bundle=key_bundle,
            )

    if not is_envelope_ready_for_delivery(metadata):
        return _make_policy_decision(
            policy,
            lane_signature=lane_signature,
            message_id=message_id,
            status="envelope_not_ready",
            reason="envelope_not_ready",
            encryption_required=True,
            envelope_accepted=False,
            envelope_metadata=metadata,
            encryption_identity=encryption_identity,
            key_bundle=key_bundle,
        )

    return _make_policy_decision(
        policy,
        lane_signature=lane_signature,
        message_id=message_id,
        status="accepted",
        reason=None,
        encryption_required=True,
        envelope_accepted=True,
        envelope_metadata=metadata,
        encryption_identity=encryption_identity,
        key_bundle=key_bundle,
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


def is_lane_encryption_required(
    policy: MailboxEncryptionPolicy,
    lane_signature: str,
) -> bool:
    """Return whether a policy requires symbolic encryption for a lane."""
    if not isinstance(policy, MailboxEncryptionPolicy):
        raise TypeError("policy must be a MailboxEncryptionPolicy")
    return _lane_signature_key(lane_signature) in policy.required_for_lanes


def is_encryption_policy_decision_accepted(
    decision: EncryptionPolicyDecision,
) -> bool:
    """Return whether a policy decision allows the message path to proceed."""
    if not isinstance(decision, EncryptionPolicyDecision):
        raise TypeError("decision must be an EncryptionPolicyDecision")
    return decision.status.status in {"accepted", "plaintext_allowed"}


def _make_policy_decision(
    policy: MailboxEncryptionPolicy,
    *,
    lane_signature: str,
    message_id: str | None,
    status: str,
    reason: str | None,
    encryption_required: bool,
    envelope_accepted: bool,
    envelope_metadata: EncryptedEnvelopeMetadata | None = None,
    encryption_identity: EncryptionIdentity | None = None,
    key_bundle: KeyBundleReference | None = None,
    note: str | None = None,
) -> EncryptionPolicyDecision:
    if encryption_identity is not None and not isinstance(
        encryption_identity,
        EncryptionIdentity,
    ):
        raise TypeError("encryption_identity must be an EncryptionIdentity or None")
    if key_bundle is not None and not isinstance(key_bundle, KeyBundleReference):
        raise TypeError("key_bundle must be a KeyBundleReference or None")
    decision_metadata: dict[str, Any] = {
        "simulator_local": True,
        "message_mutated": False,
        "registry_hub_mutated": False,
        "delivery_behavior_changed": False,
    }
    if note is not None:
        decision_metadata["note"] = note
    return EncryptionPolicyDecision(
        policy_id=policy.policy_id,
        mailbox_id=policy.mailbox_id,
        lane_signature=lane_signature,
        message_id=message_id,
        status=status,
        reason=reason,
        encryption_required=encryption_required,
        envelope_accepted=envelope_accepted,
        profile=None if envelope_metadata is None else envelope_metadata.profile,
        encryption_identity_id=_decision_identity_id(
            envelope_metadata,
            encryption_identity,
        ),
        key_bundle_id=_decision_key_bundle_id(envelope_metadata, key_bundle),
        metadata=decision_metadata,
    )


def _decision_identity_id(
    envelope_metadata: EncryptedEnvelopeMetadata | None,
    encryption_identity: EncryptionIdentity | None,
) -> str | None:
    if envelope_metadata is not None and envelope_metadata.encryption_identity_id:
        return envelope_metadata.encryption_identity_id
    if encryption_identity is not None:
        return encryption_identity.encryption_identity_id
    return None


def _decision_key_bundle_id(
    envelope_metadata: EncryptedEnvelopeMetadata | None,
    key_bundle: KeyBundleReference | None,
) -> str | None:
    if envelope_metadata is not None and envelope_metadata.key_bundle_id:
        return envelope_metadata.key_bundle_id
    if key_bundle is not None:
        return key_bundle.key_bundle_id
    return None


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


def _validate_policy_decision_status(value: str) -> None:
    _validate_required_string(value, "encryption policy decision status")
    if value not in ENCRYPTION_POLICY_DECISION_STATUSES:
        raise ValueError(
            "encryption policy decision status must be one of "
            f"{', '.join(ENCRYPTION_POLICY_DECISION_STATUSES)}"
        )


def _validate_policy_failure_reason(value: str) -> None:
    _validate_required_string(value, "encryption policy failure reason")
    if value not in ENCRYPTION_POLICY_FAILURE_REASONS:
        raise ValueError(
            "encryption policy failure reason must be one of "
            f"{', '.join(ENCRYPTION_POLICY_FAILURE_REASONS)}"
        )


def _profile_label(profile: EncryptionProfile | str) -> str:
    if isinstance(profile, str):
        return EncryptionProfile(profile).profile
    if not isinstance(profile, EncryptionProfile):
        raise TypeError("profile must be an EncryptionProfile or string")
    return profile.profile


def _profile_label_tuple(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    if not isinstance(values, tuple | list):
        raise TypeError("allowed_profiles must be a list or tuple of profile labels")
    profiles = tuple(_profile_label(value) for value in values)
    if not profiles:
        raise ValueError("allowed_profiles must contain at least one profile")
    return profiles


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


def _lane_signature_key(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("lane_signature must be a string")
    if not is_lane_signature(value):
        raise ValueError("lane_signature must use the form lane_id:version")
    return value


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
