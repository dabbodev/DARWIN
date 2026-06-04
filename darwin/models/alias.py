"""Alias registry models for DARWIN v0.5 planning slices."""

from __future__ import annotations

from dataclasses import dataclass


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


@dataclass(slots=True)
class AliasClaimResult:
    """Outcome of a direct alias claim."""

    success: bool
    status: str
    reason: str | None
    alias_record: AliasRecord | None
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
