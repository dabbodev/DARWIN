"""Simulator-local adapter endpoint and hub topology registry helpers."""

from __future__ import annotations

from darwin.models.adapter_endpoint import (
    AdapterEndpoint,
    AdapterEndpointKind,
    AdapterEndpointStatus,
    HubTopologyAdvertisement,
)
from darwin.models.hub import RegistryHub
from darwin.models.lane_signature import LaneSignature, LaneVisibilityTier, parse_lane_signature


def register_adapter_endpoint(
    registry_hub: RegistryHub,
    endpoint: AdapterEndpoint,
) -> AdapterEndpoint:
    """Store or replace an adapter endpoint by endpoint ID on a RegistryHub."""
    if not isinstance(endpoint, AdapterEndpoint):
        raise TypeError("endpoint must be an AdapterEndpoint")
    registry_hub.adapter_endpoints[endpoint.endpoint_id] = endpoint
    return endpoint


def get_adapter_endpoint(
    registry_hub: RegistryHub,
    endpoint_id: str,
) -> AdapterEndpoint | None:
    """Return a registered adapter endpoint, if present."""
    _validate_required_string(endpoint_id, "endpoint_id")
    return registry_hub.adapter_endpoints.get(endpoint_id)


def list_adapter_endpoints(
    registry_hub: RegistryHub,
    *,
    subject_id: str | None = None,
    subject_kind: str | None = None,
    adapter_kind: AdapterEndpointKind | str | None = None,
    status: AdapterEndpointStatus | str | None = None,
    lane_signature: LaneSignature | str | None = None,
    scope: str | None = None,
) -> list[AdapterEndpoint]:
    """Return adapter endpoints in deterministic endpoint ID order."""
    _validate_optional_string(subject_id, "subject_id")
    _validate_optional_string(subject_kind, "subject_kind")
    _validate_optional_string(scope, "scope")
    adapter_kind_key = _adapter_kind_key(adapter_kind)
    status_key = _status_key(status)
    lane_signature_key = _lane_signature_key(lane_signature)

    return [
        endpoint
        for _, endpoint in sorted(registry_hub.adapter_endpoints.items())
        if (subject_id is None or endpoint.subject_id == subject_id)
        and (subject_kind is None or endpoint.subject_kind == subject_kind)
        and (adapter_kind_key is None or endpoint.adapter_kind.kind == adapter_kind_key)
        and (status_key is None or endpoint.status.status == status_key)
        and (
            lane_signature_key is None
            or lane_signature_key in endpoint.lane_signatures
        )
        and (scope is None or endpoint.scope == scope)
    ]


def register_hub_topology_advertisement(
    registry_hub: RegistryHub,
    advertisement: HubTopologyAdvertisement,
) -> HubTopologyAdvertisement:
    """Store or replace a hub topology advertisement by advertisement ID."""
    if not isinstance(advertisement, HubTopologyAdvertisement):
        raise TypeError("advertisement must be a HubTopologyAdvertisement")
    registry_hub.hub_topology_advertisements[advertisement.advertisement_id] = (
        advertisement
    )
    return advertisement


def get_hub_topology_advertisement(
    registry_hub: RegistryHub,
    advertisement_id: str,
) -> HubTopologyAdvertisement | None:
    """Return a registered hub topology advertisement, if present."""
    _validate_required_string(advertisement_id, "advertisement_id")
    return registry_hub.hub_topology_advertisements.get(advertisement_id)


def list_hub_topology_advertisements(
    registry_hub: RegistryHub,
    *,
    hub_id: str | None = None,
    hub_kind: str | None = None,
    scope: str | None = None,
    adapter_kind: AdapterEndpointKind | str | None = None,
    status: AdapterEndpointStatus | str | None = None,
    visibility_tier: LaneVisibilityTier | int | None = None,
) -> list[HubTopologyAdvertisement]:
    """Return topology advertisements in deterministic advertisement ID order."""
    _validate_optional_string(hub_id, "hub_id")
    _validate_optional_string(hub_kind, "hub_kind")
    _validate_optional_string(scope, "scope")
    adapter_kind_key = _adapter_kind_key(adapter_kind)
    status_key = _status_key(status)
    tier = _visibility_tier_value(visibility_tier)

    return [
        advertisement
        for _, advertisement in sorted(registry_hub.hub_topology_advertisements.items())
        if (hub_id is None or advertisement.hub_id == hub_id)
        and (hub_kind is None or advertisement.hub_kind == hub_kind)
        and (scope is None or advertisement.scope == scope)
        and (
            adapter_kind_key is None
            or advertisement.adapter_kind.kind == adapter_kind_key
        )
        and (status_key is None or advertisement.status.status == status_key)
        and (tier is None or advertisement.visibility_tier.tier == tier)
    ]


def _adapter_kind_key(
    adapter_kind: AdapterEndpointKind | str | None,
) -> str | None:
    if adapter_kind is None:
        return None
    if isinstance(adapter_kind, AdapterEndpointKind):
        return adapter_kind.kind
    if isinstance(adapter_kind, str):
        return AdapterEndpointKind(adapter_kind).kind
    raise TypeError("adapter_kind must be an AdapterEndpointKind, string, or None")


def _status_key(status: AdapterEndpointStatus | str | None) -> str | None:
    if status is None:
        return None
    if isinstance(status, AdapterEndpointStatus):
        return status.status
    if isinstance(status, str):
        return AdapterEndpointStatus(status).status
    raise TypeError("status must be an AdapterEndpointStatus, string, or None")


def _lane_signature_key(lane_signature: LaneSignature | str | None) -> str | None:
    if lane_signature is None:
        return None
    if isinstance(lane_signature, LaneSignature):
        return lane_signature.signature
    if isinstance(lane_signature, str):
        return parse_lane_signature(lane_signature).signature
    raise TypeError("lane_signature must be a LaneSignature, string, or None")


def _visibility_tier_value(
    visibility_tier: LaneVisibilityTier | int | None,
) -> int | None:
    if visibility_tier is None:
        return None
    if isinstance(visibility_tier, LaneVisibilityTier):
        return visibility_tier.tier
    return LaneVisibilityTier(visibility_tier).tier


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
