"""Simulator-local adapter endpoint and hub topology records for v0.9."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from darwin.models.lane_signature import (
    LaneSignature,
    LaneVisibilityTier,
    parse_lane_signature,
)

ADAPTER_ENDPOINT_KINDS: tuple[str, ...] = (
    "in_memory",
    "loopback_placeholder",
    "websocket_placeholder",
    "domain_hint",
    "ipv4_placeholder",
    "ipv6_placeholder",
)

ADAPTER_ENDPOINT_STATUSES: tuple[str, ...] = (
    "available",
    "stale",
    "in_transit",
    "disabled",
    "unknown",
)

ADAPTER_ENDPOINT_SUBJECT_KINDS: tuple[str, ...] = (
    "mailbox",
    "registry_hub",
    "traffic_hub",
    "device",
    "resource",
)

HUB_TOPOLOGY_KINDS: tuple[str, ...] = (
    "registry_hub",
    "traffic_hub",
    "hybrid_hub",
)


@dataclass(frozen=True, slots=True)
class AdapterEndpointKind:
    """Controlled simulator-local adapter endpoint kind."""

    kind: str

    def __post_init__(self) -> None:
        if self.kind not in ADAPTER_ENDPOINT_KINDS:
            raise ValueError(
                "adapter endpoint kind must be one of "
                f"{', '.join(ADAPTER_ENDPOINT_KINDS)}"
            )

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe adapter kind summary."""
        return {"kind": self.kind}

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class AdapterEndpointStatus:
    """Controlled simulator-local adapter endpoint lifecycle status."""

    status: str = "unknown"

    def __post_init__(self) -> None:
        if self.status not in ADAPTER_ENDPOINT_STATUSES:
            raise ValueError(
                "adapter endpoint status must be one of "
                f"{', '.join(ADAPTER_ENDPOINT_STATUSES)}"
            )

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe status summary."""
        return {"status": self.status}

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class AdapterEndpoint:
    """Simulator-local descriptor for inert adapter-shaped availability."""

    endpoint_id: str
    subject_id: str
    subject_kind: str
    adapter_kind: AdapterEndpointKind | str
    status: AdapterEndpointStatus | str = "unknown"
    lane_signatures: tuple[LaneSignature | str, ...] | list[LaneSignature | str] = ()
    scope: str = ""
    host_hint: str | None = None
    port_hint: str | int | None = None
    path_hint: str | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _validate_required_string(self.endpoint_id, "endpoint_id")
        _validate_required_string(self.subject_id, "subject_id")
        _validate_choice(self.subject_kind, "subject_kind", ADAPTER_ENDPOINT_SUBJECT_KINDS)
        _validate_required_string(self.scope, "scope")

        adapter_kind = _adapter_kind(self.adapter_kind)
        object.__setattr__(self, "adapter_kind", adapter_kind)

        status = _adapter_status(self.status)
        object.__setattr__(self, "status", status)

        object.__setattr__(
            self,
            "lane_signatures",
            tuple(_lane_signature_key(signature) for signature in self.lane_signatures),
        )

        _validate_optional_string(self.host_hint, "host_hint")
        _validate_port_hint(self.port_hint)
        _validate_optional_string(self.path_hint, "path_hint")
        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata or {}))

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe adapter endpoint summary."""
        return {
            "endpoint_id": self.endpoint_id,
            "subject_id": self.subject_id,
            "subject_kind": self.subject_kind,
            "adapter_kind": self.adapter_kind.kind,
            "status": self.status.status,
            "lane_signatures": list(self.lane_signatures),
            "scope": self.scope,
            "host_hint": self.host_hint,
            "port_hint": self.port_hint,
            "path_hint": self.path_hint,
            "metadata": _json_safe_copy(self.metadata or {}),
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class HubTopologyAdvertisement:
    """Simulator-local statement that a hub has adapter-shaped reachability."""

    advertisement_id: str
    hub_id: str
    hub_kind: str
    scope: str
    parent_hub_id: str | None
    endpoint_id: str
    adapter_kind: AdapterEndpointKind | str
    host_hint: str | None = None
    visibility_tier: LaneVisibilityTier | int = 0
    status: AdapterEndpointStatus | str = "unknown"
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _validate_required_string(self.advertisement_id, "advertisement_id")
        _validate_required_string(self.hub_id, "hub_id")
        _validate_choice(self.hub_kind, "hub_kind", HUB_TOPOLOGY_KINDS)
        _validate_required_string(self.scope, "scope")
        _validate_optional_string(self.parent_hub_id, "parent_hub_id")
        _validate_required_string(self.endpoint_id, "endpoint_id")

        adapter_kind = _adapter_kind(self.adapter_kind)
        object.__setattr__(self, "adapter_kind", adapter_kind)

        _validate_optional_string(self.host_hint, "host_hint")

        visibility_tier = self.visibility_tier
        if isinstance(visibility_tier, int):
            visibility_tier = LaneVisibilityTier(visibility_tier)
        if not isinstance(visibility_tier, LaneVisibilityTier):
            raise TypeError("visibility_tier must be a LaneVisibilityTier or integer")
        object.__setattr__(self, "visibility_tier", visibility_tier)

        status = _adapter_status(self.status)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata or {}))

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe topology advertisement summary."""
        return {
            "advertisement_id": self.advertisement_id,
            "hub_id": self.hub_id,
            "hub_kind": self.hub_kind,
            "scope": self.scope,
            "parent_hub_id": self.parent_hub_id,
            "endpoint_id": self.endpoint_id,
            "adapter_kind": self.adapter_kind.kind,
            "host_hint": self.host_hint,
            "visibility_tier": self.visibility_tier.tier,
            "status": self.status.status,
            "metadata": _json_safe_copy(self.metadata or {}),
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


def make_in_memory_mailbox_endpoint(
    *,
    endpoint_id: str,
    mailbox_id: str,
    scope: str,
    lane_signatures: tuple[LaneSignature | str, ...] | list[LaneSignature | str] = (
        "basic_messaging:v1",
    ),
    status: AdapterEndpointStatus | str = "available",
) -> AdapterEndpoint:
    """Return an inert in-memory endpoint record for a mailbox."""
    return AdapterEndpoint(
        endpoint_id=endpoint_id,
        subject_id=mailbox_id,
        subject_kind="mailbox",
        adapter_kind="in_memory",
        status=status,
        lane_signatures=lane_signatures,
        scope=scope,
        metadata={"simulator_local": True},
    )


def make_domain_hint_hub_endpoint(
    *,
    endpoint_id: str,
    hub_id: str,
    hub_kind: str,
    scope: str,
    host_hint: str,
    path_hint: str | None = None,
    status: AdapterEndpointStatus | str = "unknown",
) -> AdapterEndpoint:
    """Return an inert domain-hint endpoint record for a hub."""
    return AdapterEndpoint(
        endpoint_id=endpoint_id,
        subject_id=hub_id,
        subject_kind=hub_kind,
        adapter_kind="domain_hint",
        status=status,
        scope=scope,
        host_hint=host_hint,
        path_hint=path_hint,
        metadata={"simulator_local": True, "hint_only": True},
    )


def _adapter_kind(value: AdapterEndpointKind | str) -> AdapterEndpointKind:
    if isinstance(value, AdapterEndpointKind):
        return value
    if isinstance(value, str):
        return AdapterEndpointKind(value)
    raise TypeError("adapter_kind must be an AdapterEndpointKind or string")


def _adapter_status(value: AdapterEndpointStatus | str) -> AdapterEndpointStatus:
    if isinstance(value, AdapterEndpointStatus):
        return value
    if isinstance(value, str):
        return AdapterEndpointStatus(value)
    raise TypeError("status must be an AdapterEndpointStatus or string")


def _lane_signature_key(lane_signature: LaneSignature | str) -> str:
    if isinstance(lane_signature, LaneSignature):
        return lane_signature.signature
    if isinstance(lane_signature, str):
        return parse_lane_signature(lane_signature).signature
    raise TypeError("lane_signatures must contain LaneSignature records or strings")


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


def _validate_choice(value: str, field_name: str, choices: tuple[str, ...]) -> None:
    _validate_required_string(value, field_name)
    if value not in choices:
        raise ValueError(f"{field_name} must be one of {', '.join(choices)}")


def _validate_port_hint(value: str | int | None) -> None:
    if value is None:
        return
    if isinstance(value, int):
        return
    if isinstance(value, str):
        _validate_required_string(value, "port_hint")
        return
    raise TypeError("port_hint must be a string, integer, or None")


def _json_safe_copy(value: Any) -> object:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, tuple | list):
        return [_json_safe_copy(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe_copy(item) for key, item in value.items()}
    raise TypeError("metadata must be JSON-safe simulator data")
