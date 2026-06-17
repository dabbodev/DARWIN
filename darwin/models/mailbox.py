"""Simulator-local mailbox identity and address models for v0.9."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from darwin.models.lane_signature import LaneSignature, is_lane_signature

MAILBOX_ADDRESS_SCHEME = "darwin"
MAILBOX_ADDRESS_PREFIX = f"{MAILBOX_ADDRESS_SCHEME}://"


@dataclass(frozen=True, slots=True)
class DarwinMailboxAddress:
    """Simulator-local mailbox address parsed from a compact DARWIN string."""

    raw: str
    scheme: str
    scope: str
    mailbox: str
    resource: str

    def __post_init__(self) -> None:
        if self.scheme != MAILBOX_ADDRESS_SCHEME:
            raise ValueError("mailbox address scheme must be 'darwin'")
        _validate_scope(self.scope)
        _validate_mailbox(self.mailbox)
        _validate_resource(self.resource)
        expected_raw = format_mailbox_address(
            scope=self.scope,
            mailbox=self.mailbox,
            resource=self.resource,
        )
        if self.raw != expected_raw:
            raise ValueError("raw mailbox address must match parsed fields")

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe mailbox address summary."""
        return {
            "raw": self.raw,
            "scheme": self.scheme,
            "scope": self.scope,
            "mailbox": self.mailbox,
            "resource": self.resource,
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class MailboxCapability:
    """Simulator-local capability reference for a future mailbox lane binding."""

    capability_id: str
    lane_signature: str | LaneSignature
    direction: str = "receive"
    enabled: bool = True
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _validate_required_string(self.capability_id, "capability_id")
        _validate_required_string(self.direction, "direction")

        lane_signature = self.lane_signature
        if isinstance(lane_signature, LaneSignature):
            lane_signature = lane_signature.signature
        if not isinstance(lane_signature, str):
            raise TypeError("lane_signature must be a string or LaneSignature")
        if not is_lane_signature(lane_signature):
            raise ValueError("lane_signature must use the form lane_id:version")
        object.__setattr__(self, "lane_signature", lane_signature)

        if not isinstance(self.enabled, bool):
            raise TypeError("enabled must be a boolean")
        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata or {}))

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe mailbox capability summary."""
        return {
            "capability_id": self.capability_id,
            "lane_signature": self.lane_signature,
            "direction": self.direction,
            "enabled": self.enabled,
            "metadata": _json_safe_copy(self.metadata or {}),
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class MailboxIdentity:
    """Simulator-local mailbox identity record for future adapter demos."""

    mailbox_id: str
    canonical_device_id: str
    local_name: str
    scope: str
    address: DarwinMailboxAddress | str
    capabilities: tuple[MailboxCapability, ...] | list[MailboxCapability] = field(
        default_factory=tuple
    )
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _validate_required_string(self.mailbox_id, "mailbox_id")
        _validate_required_string(self.canonical_device_id, "canonical_device_id")
        _validate_mailbox(self.local_name)
        _validate_scope(self.scope)

        address = self.address
        if isinstance(address, str):
            address = parse_mailbox_address(address)
        if not isinstance(address, DarwinMailboxAddress):
            raise TypeError("address must be a DarwinMailboxAddress or string")
        if address.scope != self.scope:
            raise ValueError("address scope must match mailbox identity scope")
        if address.mailbox != self.local_name:
            raise ValueError("address mailbox must match mailbox identity local_name")
        object.__setattr__(self, "address", address)

        capabilities = tuple(self.capabilities)
        if not all(isinstance(capability, MailboxCapability) for capability in capabilities):
            raise TypeError("capabilities must contain MailboxCapability records")
        object.__setattr__(self, "capabilities", capabilities)
        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata or {}))

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe mailbox identity summary."""
        return {
            "mailbox_id": self.mailbox_id,
            "canonical_device_id": self.canonical_device_id,
            "local_name": self.local_name,
            "scope": self.scope,
            "address": self.address.to_summary(),
            "capabilities": [
                capability.to_summary() for capability in self.capabilities
            ],
            "metadata": _json_safe_copy(self.metadata or {}),
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


def parse_mailbox_address(raw: str) -> DarwinMailboxAddress:
    """Parse a compact simulator-local DARWIN mailbox address."""
    if not isinstance(raw, str):
        raise TypeError("mailbox address must be a string")
    if not raw.startswith(MAILBOX_ADDRESS_PREFIX):
        raise ValueError("mailbox address must start with darwin://")

    remainder = raw.removeprefix(MAILBOX_ADDRESS_PREFIX)
    if remainder.count("/") != 1:
        raise ValueError("mailbox address must use the form darwin://scope.mailbox/resource")
    authority, resource = remainder.split("/", 1)
    if "." not in authority:
        raise ValueError("mailbox address authority must include scope and mailbox")

    scope, mailbox = authority.rsplit(".", 1)
    return DarwinMailboxAddress(
        raw=raw,
        scheme=MAILBOX_ADDRESS_SCHEME,
        scope=scope,
        mailbox=mailbox,
        resource=resource,
    )


def format_mailbox_address(
    scope: str,
    mailbox: str,
    resource: str = "inbox",
) -> str:
    """Return a compact simulator-local DARWIN mailbox address string."""
    _validate_scope(scope)
    _validate_mailbox(mailbox)
    _validate_resource(resource)
    return f"{MAILBOX_ADDRESS_PREFIX}{scope}.{mailbox}/{resource}"


def is_mailbox_address(raw: str) -> bool:
    """Return whether a value is a valid simulator-local mailbox address."""
    try:
        parse_mailbox_address(raw)
    except (TypeError, ValueError):
        return False
    return True


def _validate_required_string(value: str, field_name: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} is required")
    if value.strip() != value or any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")


def _validate_scope(value: str) -> None:
    _validate_required_string(value, "scope")
    if any(character in value for character in "/:?#"):
        raise ValueError("scope must not contain URL separator characters")
    if any(not segment for segment in value.split(".")):
        raise ValueError("scope segments must be non-empty")


def _validate_mailbox(value: str) -> None:
    _validate_required_string(value, "mailbox")
    if any(character in value for character in ". /:?#"):
        raise ValueError("mailbox must be one non-empty address segment")


def _validate_resource(value: str) -> None:
    _validate_required_string(value, "resource")
    if any(character in value for character in "./:?#"):
        raise ValueError("resource must be one non-empty address segment")


def _json_safe_copy(value: Any) -> object:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, tuple | list):
        return [_json_safe_copy(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe_copy(item) for key, item in value.items()}
    raise TypeError("metadata must be JSON-safe simulator data")
