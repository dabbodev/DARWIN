"""Simulator-local lane signature and discovery intent models for v0.9."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

LANE_VISIBILITY_TIERS: dict[int, str] = {
    0: "public",
    1: "local_scope",
    2: "authenticated",
    3: "scoped_trusted",
    4: "delegated_trusted",
    5: "explicit_private",
}

LANE_REGISTRY_STATUSES: tuple[str, ...] = (
    "draft",
    "active",
    "deprecated",
    "disabled",
)

LANE_FALLBACK_ACTIONS: tuple[str, ...] = (
    "reject",
    "bounce",
    "queue",
    "queue_with_expiry",
    "hold_until_relocation_resolves",
    "queue_with_retry",
    "manual_resolution_required",
)


@dataclass(frozen=True, slots=True)
class LaneSignature:
    """Simulator-local descriptor for what a lane is intended to carry."""

    lane_id: str
    version: str
    direction: str = "receive"
    payload_kind: str = "symbolic_message_envelope"
    recipient_kind: str = "mailbox"
    required_capability: str = "basic_messaging"
    auth_policy: str = "authorization_required"
    adapter_kind: str = "mailbox_adapter"

    def __post_init__(self) -> None:
        _validate_signature_part(self.lane_id, "lane_id")
        _validate_signature_part(self.version, "version")

    @property
    def signature(self) -> str:
        """Return the compact lane signature string."""
        return format_lane_signature(self.lane_id, self.version)

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe lane signature summary."""
        return {
            "lane_id": self.lane_id,
            "version": self.version,
            "signature": self.signature,
            "direction": self.direction,
            "payload_kind": self.payload_kind,
            "recipient_kind": self.recipient_kind,
            "required_capability": self.required_capability,
            "auth_policy": self.auth_policy,
            "adapter_kind": self.adapter_kind,
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class LaneDeliveryFallbackPolicy:
    """Simulator-local fallback actions for future lane delivery planning."""

    unknown_recipient: str = "bounce"
    stale_device: str = "queue_with_expiry"
    in_transit: str = "hold_until_relocation_resolves"
    quarantined: str = "reject"
    missing_lane_capability: str = "reject"
    adapter_unavailable: str = "queue_with_retry"
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "unknown_recipient",
            "stale_device",
            "in_transit",
            "quarantined",
            "missing_lane_capability",
            "adapter_unavailable",
        ):
            _validate_fallback_action(getattr(self, field_name), field_name)
        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata or {}))

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe fallback policy summary."""
        return {
            "unknown_recipient": self.unknown_recipient,
            "stale_device": self.stale_device,
            "in_transit": self.in_transit,
            "quarantined": self.quarantined,
            "missing_lane_capability": self.missing_lane_capability,
            "adapter_unavailable": self.adapter_unavailable,
            "metadata": _json_safe_copy(self.metadata or {}),
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class LaneRegistryStatus:
    """Controlled simulator-local lifecycle status for a lane definition."""

    status: str = "active"

    def __post_init__(self) -> None:
        if self.status not in LANE_REGISTRY_STATUSES:
            raise ValueError(
                "lane registry status must be one of "
                f"{', '.join(LANE_REGISTRY_STATUSES)}"
            )

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe status summary."""
        return {"status": self.status}

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class LaneDefinition:
    """Scoped simulator-local definition for an available lane signature."""

    lane_signature: LaneSignature | str
    scope: str
    description: str = ""
    payload_kind: str | None = None
    schema_ref: str | None = None
    protocol_ref: str | None = None
    visibility_tier: LaneVisibilityTier | int = 0
    authority_scope: str | None = None
    adapter_kinds: tuple[str, ...] | list[str] = field(default_factory=tuple)
    status: LaneRegistryStatus | str = "active"
    fallback_policy: LaneDeliveryFallbackPolicy | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        lane_signature = self.lane_signature
        if isinstance(lane_signature, str):
            lane_signature = parse_lane_signature(lane_signature)
        if not isinstance(lane_signature, LaneSignature):
            raise TypeError("lane_signature must be a LaneSignature or string")
        object.__setattr__(self, "lane_signature", lane_signature)

        _validate_required_string(self.scope, "scope")
        if self.description is None:
            object.__setattr__(self, "description", "")
        elif not isinstance(self.description, str):
            raise TypeError("description must be a string")

        payload_kind = self.payload_kind or lane_signature.payload_kind
        _validate_required_string(payload_kind, "payload_kind")
        object.__setattr__(self, "payload_kind", payload_kind)

        _validate_optional_string(self.schema_ref, "schema_ref")
        _validate_optional_string(self.protocol_ref, "protocol_ref")

        visibility_tier = self.visibility_tier
        if isinstance(visibility_tier, int):
            visibility_tier = LaneVisibilityTier(visibility_tier)
        if not isinstance(visibility_tier, LaneVisibilityTier):
            raise TypeError("visibility_tier must be a LaneVisibilityTier or integer")
        object.__setattr__(self, "visibility_tier", visibility_tier)

        authority_scope = self.authority_scope or self.scope
        _validate_required_string(authority_scope, "authority_scope")
        object.__setattr__(self, "authority_scope", authority_scope)

        adapter_kinds = tuple(self.adapter_kinds or (lane_signature.adapter_kind,))
        if not adapter_kinds:
            raise ValueError("adapter_kinds must contain at least one adapter kind")
        for adapter_kind in adapter_kinds:
            _validate_required_string(adapter_kind, "adapter_kind")
        object.__setattr__(self, "adapter_kinds", adapter_kinds)

        status = self.status
        if isinstance(status, str):
            status = LaneRegistryStatus(status)
        if not isinstance(status, LaneRegistryStatus):
            raise TypeError("status must be a LaneRegistryStatus or string")
        object.__setattr__(self, "status", status)

        fallback_policy = self.fallback_policy or LaneDeliveryFallbackPolicy()
        if not isinstance(fallback_policy, LaneDeliveryFallbackPolicy):
            raise TypeError("fallback_policy must be a LaneDeliveryFallbackPolicy")
        object.__setattr__(self, "fallback_policy", fallback_policy)

        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata or {}))

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe lane definition summary."""
        return {
            "lane_signature": self.lane_signature.signature,
            "scope": self.scope,
            "description": self.description,
            "payload_kind": self.payload_kind,
            "schema_ref": self.schema_ref,
            "protocol_ref": self.protocol_ref,
            "visibility_tier": self.visibility_tier.tier,
            "authority_scope": self.authority_scope,
            "adapter_kinds": list(self.adapter_kinds),
            "status": self.status.status,
            "fallback_policy": self.fallback_policy.to_summary(),
            "metadata": _json_safe_copy(self.metadata or {}),
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class LaneVisibilityTier:
    """Discovery visibility tier for a lane intent advertisement."""

    tier: int

    def __post_init__(self) -> None:
        if self.tier not in LANE_VISIBILITY_TIERS:
            raise ValueError("visibility tier must be an integer from 0 through 5")

    @property
    def label(self) -> str:
        """Return the stable label for this visibility tier."""
        return LANE_VISIBILITY_TIERS[self.tier]

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe visibility summary."""
        return {"tier": self.tier, "label": self.label}

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class LaneIntentAdvertisement:
    """Simulator-local statement that a subject can expose a lane intent."""

    advertisement_id: str
    subject_id: str
    subject_kind: str
    lane_signature: LaneSignature
    visibility_tier: LaneVisibilityTier | int
    scope: str
    authorized_observers: tuple[str, ...] | list[str] = field(default_factory=tuple)
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.advertisement_id:
            raise ValueError("advertisement_id is required")
        if not self.subject_id:
            raise ValueError("subject_id is required")
        if not self.subject_kind:
            raise ValueError("subject_kind is required")
        if not self.scope:
            raise ValueError("scope is required")
        if not isinstance(self.lane_signature, LaneSignature):
            raise TypeError("lane_signature must be a LaneSignature")

        visibility_tier = self.visibility_tier
        if isinstance(visibility_tier, int):
            visibility_tier = LaneVisibilityTier(visibility_tier)
        if not isinstance(visibility_tier, LaneVisibilityTier):
            raise TypeError("visibility_tier must be a LaneVisibilityTier or integer")
        object.__setattr__(self, "visibility_tier", visibility_tier)

        object.__setattr__(self, "authorized_observers", tuple(self.authorized_observers))
        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata or {}))

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe lane intent summary."""
        return {
            "advertisement_id": self.advertisement_id,
            "subject_id": self.subject_id,
            "subject_kind": self.subject_kind,
            "lane_signature": self.lane_signature.to_summary(),
            "visibility_tier": self.visibility_tier.tier,
            "scope": self.scope,
            "authorized_observers": list(self.authorized_observers),
            "metadata": _json_safe_copy(self.metadata or {}),
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class LaneTrustContext:
    """Simulator-local discovery context for a lane intent requester."""

    requester_id: str
    requester_scope: str | None = None
    authenticated: bool = False
    trusted_scopes: tuple[str, ...] | list[str] = field(default_factory=tuple)
    delegated_trust_paths: tuple[str, ...] | list[str] = field(default_factory=tuple)
    explicit_permissions: tuple[str, ...] | list[str] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.requester_id:
            raise ValueError("requester_id is required")
        object.__setattr__(self, "trusted_scopes", tuple(self.trusted_scopes))
        object.__setattr__(self, "delegated_trust_paths", tuple(self.delegated_trust_paths))
        object.__setattr__(self, "explicit_permissions", tuple(self.explicit_permissions))


def format_lane_signature(lane_id: str, version: str) -> str:
    """Return the compact `lane_id:version` signature string."""
    _validate_signature_part(lane_id, "lane_id")
    _validate_signature_part(version, "version")
    return f"{lane_id}:{version}"


def parse_lane_signature(raw: str) -> LaneSignature:
    """Parse a compact lane signature string into a LaneSignature."""
    if not isinstance(raw, str):
        raise TypeError("lane signature must be a string")
    if raw.count(":") != 1:
        raise ValueError("lane signature must use the form lane_id:version")
    lane_id, version = raw.split(":", 1)
    return LaneSignature(lane_id=lane_id, version=version)


def is_lane_signature(raw: str) -> bool:
    """Return whether a value is a valid compact lane signature string."""
    try:
        parse_lane_signature(raw)
    except (TypeError, ValueError):
        return False
    return True


def can_discover_lane_intent(
    advertisement: LaneIntentAdvertisement,
    trust_context: LaneTrustContext,
) -> bool:
    """Return whether the requester can discover that a lane intent exists."""
    tier = advertisement.visibility_tier.tier
    if tier == 0:
        return True
    if tier == 1:
        return trust_context.requester_scope == advertisement.scope
    if tier == 2:
        return trust_context.authenticated
    if tier == 3:
        return advertisement.scope in trust_context.trusted_scopes
    if tier == 4:
        return _has_delegated_trust_path(advertisement, trust_context)
    if tier == 5:
        return _has_explicit_observer_permission(advertisement, trust_context)
    return False


def filter_discoverable_lane_intents(
    advertisements: list[LaneIntentAdvertisement] | tuple[LaneIntentAdvertisement, ...],
    trust_context: LaneTrustContext,
) -> list[LaneIntentAdvertisement]:
    """Return discoverable advertisements in their original deterministic order."""
    return [
        advertisement
        for advertisement in advertisements
        if can_discover_lane_intent(advertisement, trust_context)
    ]


def make_basic_messaging_lane_definition(
    scope: str,
    *,
    authority_scope: str | None = None,
) -> LaneDefinition:
    """Return the deterministic simulator-local `basic_messaging:v1` definition."""
    _validate_required_string(scope, "scope")
    if authority_scope is not None:
        _validate_required_string(authority_scope, "authority_scope")
    return LaneDefinition(
        lane_signature=LaneSignature(
            lane_id="basic_messaging",
            version="v1",
            direction="receive",
            payload_kind="symbolic_message_envelope",
            recipient_kind="mailbox",
            required_capability="basic_messaging",
            auth_policy="authorization_required",
            adapter_kind="mailbox_adapter",
        ),
        scope=scope,
        description="Simulator-local symbolic mailbox messaging lane.",
        payload_kind="symbolic_message_envelope",
        schema_ref="darwin://schemas/basic_messaging/v1",
        protocol_ref="darwin://protocols/basic_messaging/v1",
        visibility_tier=0,
        authority_scope=authority_scope or scope,
        adapter_kinds=("mailbox_adapter",),
        status="active",
        fallback_policy=LaneDeliveryFallbackPolicy(),
        metadata={"simulator_local": True},
    )


def _validate_signature_part(value: str, field_name: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} is required")
    if value.strip() != value or any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    if ":" in value:
        raise ValueError(f"{field_name} must not contain ':'")


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


def _validate_fallback_action(value: str, field_name: str) -> None:
    _validate_required_string(value, field_name)
    if value not in LANE_FALLBACK_ACTIONS:
        raise ValueError(
            f"{field_name} must be one of {', '.join(LANE_FALLBACK_ACTIONS)}"
        )


def _has_delegated_trust_path(
    advertisement: LaneIntentAdvertisement,
    trust_context: LaneTrustContext,
) -> bool:
    possible_paths = {
        advertisement.scope,
        f"{trust_context.requester_scope}->{advertisement.scope}",
        f"{trust_context.requester_id}->{advertisement.scope}",
        f"{trust_context.requester_id}->{advertisement.subject_id}",
    }
    return any(path in trust_context.delegated_trust_paths for path in possible_paths)


def _has_explicit_observer_permission(
    advertisement: LaneIntentAdvertisement,
    trust_context: LaneTrustContext,
) -> bool:
    if trust_context.requester_id in advertisement.authorized_observers:
        return True

    explicit_targets = {
        advertisement.advertisement_id,
        advertisement.subject_id,
        advertisement.lane_signature.signature,
    }
    return any(permission in trust_context.explicit_permissions for permission in explicit_targets)


def _json_safe_copy(value: Any) -> object:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, tuple | list):
        return [_json_safe_copy(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe_copy(item) for key, item in value.items()}
    raise TypeError("metadata must be JSON-safe simulator data")
