"""Alias registry models for DARWIN v0.5 planning slices."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class AliasRecord:
    """Registry-local alias that points to durable identity truth."""

    alias: str
    target_identity_chain: str
    alias_type: str = "device_alias"
    target_device_id: str | None = None
    target_service_id: str | None = None
    requested_by_device_id: str | None = None
    requested_through_hub: str | None = None
    approved_by_registry_hub: str = ""
    authority_scope: str = ""
    status: str = "active"
    visibility: str = "local"
    ttl: int | None = None
    conflict_id: str | None = None
    requested_alias: str | None = None
    granted_alias: str | None = None
    fallback_reason: str | None = None
    authority_ceiling: str | None = None
    fallback_from: str | None = None


@dataclass(slots=True)
class AliasBundle:
    """Registry-local delegated namespace for child alias records."""

    bundle_path: str
    delegated_to_registry_hub: str
    authority_scope: str
    approved_by_registry_hub: str
    bundle_type: str = "alias_zone"
    status: str = "active"
    visibility: str = "local"
    allowed_record_types: list[str] = field(default_factory=lambda: ["device_alias"])
    policy: dict[str, object] = field(default_factory=dict)
    created_by_device_id: str | None = None


@dataclass(slots=True)
class AliasClaimResult:
    """Outcome of a direct alias claim."""

    success: bool
    status: str
    reason: str | None
    alias_record: AliasRecord | None
    conflict_id: str | None = None


@dataclass(slots=True)
class AliasBundleClaimResult:
    """Outcome of creating a delegated alias bundle."""

    success: bool
    status: str
    reason: str | None
    bundle: AliasBundle | None


@dataclass(slots=True)
class BundleAliasClaimResult:
    """Outcome of claiming a child alias inside an alias bundle."""

    success: bool
    status: str
    reason: str | None
    alias_record: AliasRecord | None
    bundle_path: str | None


@dataclass(slots=True)
class ProgressiveAliasClaimResult:
    """Outcome of an alias claim that may fall back within hub authority."""

    success: bool
    status: str
    reason: str | None
    requested_alias: str
    granted_alias: str | None
    alias_record: AliasRecord | None
    fallback_reason: str | None = None
    authority_ceiling: str | None = None
    conflict_id: str | None = None


@dataclass(slots=True)
class AliasResolutionResult:
    """Outcome of resolving a direct alias."""

    success: bool
    status: str
    reason: str | None
    alias_record: AliasRecord | None
    target_device_id: str | None
    target_identity_chain: str | None


@dataclass(slots=True)
class AliasReleaseResult:
    """Outcome of releasing an active alias."""

    success: bool
    status: str
    reason: str | None
    alias: str
