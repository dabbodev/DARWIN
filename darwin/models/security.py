"""Symbolic security models for DARWIN v0.1 trust simulation."""

from __future__ import annotations

from dataclasses import dataclass, field

DEFAULT_QUARANTINE_ALLOWED_ACTIONS = [
    "present_passport",
    "request_recovery",
    "sync_time",
]
DEFAULT_QUARANTINE_DENIED_ACTIONS = [
    "send_normal_traffic",
    "act_as_parent_hub",
    "host_services",
    "open_new_lane",
]


@dataclass(slots=True)
class AuthState:
    """Symbolic trust inputs without real cryptographic material."""

    passport_valid: bool = True
    issuer_trusted: bool = True
    revoked: bool = False
    rolling_proof_valid: bool = True
    packet_auth_tag_valid: bool = True

    @property
    def all_valid(self) -> bool:
        return all((
            self.passport_valid,
            self.issuer_trusted,
            not self.revoked,
            self.rolling_proof_valid,
            self.packet_auth_tag_valid,
        ))


@dataclass(slots=True)
class SecurityEvent:
    """A deterministic security event emitted by a simulator hub."""

    event_type: str
    claimed_device_id: str | None
    hub_id: str
    severity: str
    action_taken: str
    timestamp: int | None = None
    reason: str | None = None

    @property
    def device_id(self) -> str | None:
        """Alias for callers that use device-centric terminology."""
        return self.claimed_device_id


@dataclass(slots=True)
class QuarantineRecord:
    """Symbolic quarantine state for a suspicious claimed identity."""

    claimed_device_id: str
    reason: str
    source_hub_id: str | None = None
    created_at: int | None = None
    allowed_actions: list[str] = field(
        default_factory=lambda: list(DEFAULT_QUARANTINE_ALLOWED_ACTIONS)
    )
    denied_actions: list[str] = field(
        default_factory=lambda: list(DEFAULT_QUARANTINE_DENIED_ACTIONS)
    )
    status: str = "active"


@dataclass(slots=True)
class TrustCheckResult:
    """Generic symbolic trust-check result."""

    action: str
    success: bool
    claimed_device_id: str | None = None
    reason: str | None = None
    security_event: SecurityEvent | None = None
    quarantine: QuarantineRecord | None = None


@dataclass(slots=True)
class QuarantineResult:
    """Outcome of creating or reusing a quarantine record."""

    action: str
    claimed_device_id: str
    record: QuarantineRecord
    security_event: SecurityEvent | None = None

    @property
    def success(self) -> bool:
        return self.action in {"quarantined", "already_quarantined"}


@dataclass(slots=True)
class DuplicateIdentityConflict:
    """Outcome for duplicate active durable-ID claims."""

    action: str
    device_id: str
    existing_attachment: str | None = None
    claiming_attachment: str | None = None
    conflict_id: str | None = None
    quarantine: QuarantineRecord | None = None
    security_event: SecurityEvent | None = None
    reason: str | None = None

    @property
    def success(self) -> bool:
        return self.action == "no_conflict"


@dataclass(slots=True)
class PacketAuthResult:
    """Symbolic packet-auth validation result."""

    action: str
    packet_id: str
    success: bool
    claimed_device_id: str | None = None
    security_event: SecurityEvent | None = None
    quarantine: QuarantineRecord | None = None
    reason: str | None = None


@dataclass(slots=True)
class RollingProofResult:
    """Symbolic rolling-proof validation result."""

    action: str
    device_id: str
    success: bool
    quarantine: QuarantineRecord | None = None
    security_event: SecurityEvent | None = None
    reason: str | None = None
