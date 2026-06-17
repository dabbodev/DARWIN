"""Simulator-local scoped lane registry helpers for RegistryHub."""

from __future__ import annotations

from darwin.models.hub import RegistryHub
from darwin.models.lane_signature import (
    LaneDefinition,
    LaneSignature,
    LaneTrustContext,
    LaneVisibilityTier,
    parse_lane_signature,
)


def register_lane_definition(
    registry_hub: RegistryHub,
    lane_definition: LaneDefinition,
) -> LaneDefinition:
    """Store or replace a scoped lane definition by compact lane signature."""
    if not isinstance(lane_definition, LaneDefinition):
        raise TypeError("lane_definition must be a LaneDefinition")
    registry_hub.lane_registry[lane_definition.lane_signature.signature] = (
        lane_definition
    )
    return lane_definition


def get_lane_definition(
    registry_hub: RegistryHub,
    lane_signature: LaneSignature | str,
) -> LaneDefinition | None:
    """Return a registered lane definition, if present."""
    signature = _lane_signature_key(lane_signature)
    return registry_hub.lane_registry.get(signature)


def list_lane_definitions(
    registry_hub: RegistryHub,
    *,
    visibility_tier: LaneVisibilityTier | int | None = None,
    status: str | None = None,
) -> list[LaneDefinition]:
    """Return lane definitions in deterministic lane-signature order."""
    tier = _visibility_tier_value(visibility_tier)
    definitions = [
        lane_definition
        for _, lane_definition in sorted(registry_hub.lane_registry.items())
        if (tier is None or lane_definition.visibility_tier.tier == tier)
        and (status is None or lane_definition.status.status == status)
    ]
    return definitions


def list_discoverable_lane_definitions(
    registry_hub: RegistryHub,
    trust_context: LaneTrustContext,
) -> list[LaneDefinition]:
    """Return lane definitions discoverable to a requester by visibility only."""
    return [
        lane_definition
        for lane_definition in list_lane_definitions(registry_hub)
        if can_discover_lane_definition(lane_definition, trust_context)
    ]


def can_discover_lane_definition(
    lane_definition: LaneDefinition,
    trust_context: LaneTrustContext,
) -> bool:
    """Return whether a requester can discover that a lane definition exists."""
    tier = lane_definition.visibility_tier.tier
    if tier == 0:
        return True
    if tier == 1:
        return trust_context.requester_scope == lane_definition.scope
    if tier == 2:
        return trust_context.authenticated
    if tier == 3:
        return lane_definition.scope in trust_context.trusted_scopes
    if tier == 4:
        return _has_delegated_trust_path(lane_definition, trust_context)
    if tier == 5:
        return _has_explicit_definition_permission(lane_definition, trust_context)
    return False


def _lane_signature_key(lane_signature: LaneSignature | str) -> str:
    if isinstance(lane_signature, LaneSignature):
        return lane_signature.signature
    if isinstance(lane_signature, str):
        return parse_lane_signature(lane_signature).signature
    raise TypeError("lane_signature must be a LaneSignature or string")


def _visibility_tier_value(visibility_tier: LaneVisibilityTier | int | None) -> int | None:
    if visibility_tier is None:
        return None
    if isinstance(visibility_tier, LaneVisibilityTier):
        return visibility_tier.tier
    return LaneVisibilityTier(visibility_tier).tier


def _has_delegated_trust_path(
    lane_definition: LaneDefinition,
    trust_context: LaneTrustContext,
) -> bool:
    signature = lane_definition.lane_signature.signature
    possible_paths = {
        lane_definition.scope,
        lane_definition.authority_scope,
        f"{trust_context.requester_scope}->{lane_definition.scope}",
        f"{trust_context.requester_scope}->{lane_definition.authority_scope}",
        f"{trust_context.requester_id}->{lane_definition.scope}",
        f"{trust_context.requester_id}->{lane_definition.authority_scope}",
        f"{trust_context.requester_id}->{signature}",
    }
    return any(path in trust_context.delegated_trust_paths for path in possible_paths)


def _has_explicit_definition_permission(
    lane_definition: LaneDefinition,
    trust_context: LaneTrustContext,
) -> bool:
    signature = lane_definition.lane_signature.signature
    explicit_targets = {
        signature,
        f"{lane_definition.scope}:{signature}",
        f"{lane_definition.authority_scope}:{signature}",
    }
    return any(permission in trust_context.explicit_permissions for permission in explicit_targets)
