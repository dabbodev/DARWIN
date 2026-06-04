"""Direct alias helpers for RegistryHub."""

from __future__ import annotations

from darwin.models.alias import (
    AliasClaimResult,
    AliasRecord,
    AliasReleaseResult,
    AliasResolutionResult,
)
from darwin.models.hub import ConflictRecord, RegistryHub


def claim_alias(
    registry_hub: RegistryHub,
    alias: str,
    target_device_id: str,
    requested_by_device_id: str | None = None,
    alias_type: str = "device_alias",
    visibility: str = "local",
    ttl: int | None = None,
) -> AliasClaimResult:
    """Claim a direct alias for an already registered local device."""
    target_record = registry_hub.devices.get(target_device_id)
    if target_record is None:
        return AliasClaimResult(
            success=False,
            status="not_found",
            reason="unknown_device",
            alias_record=None,
        )

    if target_record.current_state == "quarantined":
        return AliasClaimResult(
            success=False,
            status="rejected",
            reason="device_quarantined",
            alias_record=None,
        )

    if target_record.current_state == "revoked":
        return AliasClaimResult(
            success=False,
            status="rejected",
            reason="device_revoked",
            alias_record=None,
        )

    existing_alias = registry_hub.aliases.get(alias)
    if existing_alias is not None and existing_alias.status == "active":
        conflict_id = _record_alias_conflict(
            registry_hub=registry_hub,
            alias=alias,
            existing_device_id=existing_alias.target_device_id,
            requesting_device_id=target_device_id,
        )
        return AliasClaimResult(
            success=False,
            status="conflict",
            reason="alias_conflict",
            alias_record=existing_alias,
            conflict_id=conflict_id,
        )

    alias_record = AliasRecord(
        alias=alias,
        alias_type=alias_type,
        target_device_id=target_device_id,
        target_identity_chain=target_record.identity_chain,
        requested_by_device_id=requested_by_device_id,
        requested_through_hub=target_record.current_attachment,
        approved_by_registry_hub=registry_hub.hub_id,
        authority_scope=registry_hub.scope_path,
        visibility=visibility,
        ttl=ttl,
    )
    registry_hub.aliases[alias] = alias_record
    return AliasClaimResult(
        success=True,
        status="active",
        reason=None,
        alias_record=alias_record,
    )


def resolve_alias(registry_hub: RegistryHub, alias: str) -> AliasResolutionResult:
    """Resolve an active direct alias without changing canonical identity state."""
    alias_record = registry_hub.aliases.get(alias)
    if alias_record is None:
        return AliasResolutionResult(
            success=False,
            status="not_found",
            reason="alias_not_found",
            alias_record=None,
            target_device_id=None,
            target_identity_chain=None,
        )

    if alias_record.status != "active":
        return AliasResolutionResult(
            success=False,
            status=alias_record.status,
            reason="alias_not_active",
            alias_record=alias_record,
            target_device_id=None,
            target_identity_chain=None,
        )

    return AliasResolutionResult(
        success=True,
        status="active",
        reason=None,
        alias_record=alias_record,
        target_device_id=alias_record.target_device_id,
        target_identity_chain=alias_record.target_identity_chain,
    )


def release_alias(
    registry_hub: RegistryHub,
    alias: str,
    requested_by_device_id: str | None = None,
) -> AliasReleaseResult:
    """Release an active alias while preserving the alias record."""
    alias_record = registry_hub.aliases.get(alias)
    if alias_record is None:
        return AliasReleaseResult(
            success=False,
            status="not_found",
            reason="alias_not_found",
            alias=alias,
        )

    if alias_record.status != "active":
        return AliasReleaseResult(
            success=False,
            status=alias_record.status,
            reason="alias_not_active",
            alias=alias,
        )

    alias_record.status = "released"
    return AliasReleaseResult(
        success=True,
        status="released",
        reason=None,
        alias=alias,
    )


def alias_exists(registry_hub: RegistryHub, alias: str) -> bool:
    """Return whether an alias exists as an active registry shortcut."""
    alias_record = registry_hub.aliases.get(alias)
    return alias_record is not None and alias_record.status == "active"


def _record_alias_conflict(
    *,
    registry_hub: RegistryHub,
    alias: str,
    existing_device_id: str | None,
    requesting_device_id: str,
) -> str:
    conflict_id = f"alias_conflict:{alias}:{requesting_device_id}"
    registry_hub.conflicts[conflict_id] = ConflictRecord(
        conflict_id=conflict_id,
        conflict_type="alias_conflict",
        requested_label=alias,
        existing_device_id=existing_device_id or "",
        requesting_device_id=requesting_device_id,
        status="pending_resolution",
    )
    return conflict_id
