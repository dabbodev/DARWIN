"""Direct alias helpers for RegistryHub."""

from __future__ import annotations

from darwin.models.alias import (
    AliasClaimResult,
    AliasRecord,
    AliasReleaseResult,
    AliasResolutionResult,
    ProgressiveAliasClaimResult,
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
    target_result = _validate_alias_target(registry_hub, target_device_id)
    if target_result is not None:
        return target_result

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

    target_record = registry_hub.devices[target_device_id]
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
        requested_alias=alias,
        granted_alias=alias,
        authority_ceiling=registry_hub.scope_path,
    )
    registry_hub.aliases[alias] = alias_record
    return AliasClaimResult(
        success=True,
        status="active",
        reason=None,
        alias_record=alias_record,
    )


def claim_progressive_alias(
    registry_hub: RegistryHub,
    requested_alias: str,
    local_name: str,
    target_device_id: str,
    requested_by_device_id: str | None = None,
    allowed_authority_scope: str | None = None,
    fallback_allowed: bool = True,
    visibility: str = "local",
    ttl: int | None = None,
) -> ProgressiveAliasClaimResult:
    """Claim an alias, falling back to the highest locally authorized alias."""
    authority_ceiling = _authority_ceiling(
        registry_hub,
        allowed_authority_scope=allowed_authority_scope,
    )
    target_result = _validate_alias_target(registry_hub, target_device_id)
    if target_result is not None:
        return _progressive_result_from_direct(
            target_result,
            requested_alias=requested_alias,
            granted_alias=None,
            fallback_reason=None,
            authority_ceiling=authority_ceiling,
        )

    if _alias_in_scope(requested_alias, authority_ceiling):
        direct_result = claim_alias(
            registry_hub,
            requested_alias,
            target_device_id,
            requested_by_device_id=requested_by_device_id,
            visibility=visibility,
            ttl=ttl,
        )
        if direct_result.success:
            alias_record = direct_result.alias_record
            if alias_record is not None:
                alias_record.requested_alias = requested_alias
                alias_record.granted_alias = requested_alias
                alias_record.authority_ceiling = authority_ceiling
            return ProgressiveAliasClaimResult(
                success=True,
                status="claimed",
                reason=None,
                requested_alias=requested_alias,
                granted_alias=requested_alias,
                alias_record=alias_record,
                fallback_reason=None,
                authority_ceiling=authority_ceiling,
            )

        return _progressive_result_from_direct(
            direct_result,
            requested_alias=requested_alias,
            granted_alias=None,
            fallback_reason=direct_result.reason,
            authority_ceiling=authority_ceiling,
        )
    else:
        if not fallback_allowed:
            return ProgressiveAliasClaimResult(
                success=False,
                status="rejected",
                reason="insufficient_authority",
                requested_alias=requested_alias,
                granted_alias=None,
                alias_record=None,
                fallback_reason=None,
                authority_ceiling=authority_ceiling,
            )
        fallback_reason = "insufficient_authority"

    fallback_alias = highest_authorized_alias(
        registry_hub,
        requested_alias,
        local_name,
        allowed_authority_scope=authority_ceiling,
    )
    if fallback_alias == requested_alias:
        existing_alias = registry_hub.aliases.get(requested_alias)
        return ProgressiveAliasClaimResult(
            success=False,
            status="conflict",
            reason="alias_conflict",
            requested_alias=requested_alias,
            granted_alias=None,
            alias_record=existing_alias,
            fallback_reason=fallback_reason,
            authority_ceiling=authority_ceiling,
            conflict_id=None,
        )

    fallback_result = claim_alias(
        registry_hub,
        fallback_alias,
        target_device_id,
        requested_by_device_id=requested_by_device_id,
        visibility=visibility,
        ttl=ttl,
    )
    if not fallback_result.success:
        return _progressive_result_from_direct(
            fallback_result,
            requested_alias=requested_alias,
            granted_alias=None,
            fallback_reason=fallback_result.reason,
            authority_ceiling=authority_ceiling,
        )

    alias_record = fallback_result.alias_record
    if alias_record is not None:
        alias_record.requested_alias = requested_alias
        alias_record.granted_alias = fallback_alias
        alias_record.fallback_reason = fallback_reason
        alias_record.authority_ceiling = authority_ceiling
        alias_record.fallback_from = requested_alias

    return ProgressiveAliasClaimResult(
        success=True,
        status="fallback_granted",
        reason=fallback_reason,
        requested_alias=requested_alias,
        granted_alias=fallback_alias,
        alias_record=alias_record,
        fallback_reason=fallback_reason,
        authority_ceiling=authority_ceiling,
    )


def suggest_alias_fallbacks(
    registry_hub: RegistryHub,
    requested_alias: str,
    local_name: str,
    allowed_authority_scope: str | None = None,
) -> list[str]:
    """Return deterministic fallback candidates inside local hub authority."""
    authority_ceiling = _authority_ceiling(
        registry_hub,
        allowed_authority_scope=allowed_authority_scope,
    )
    if _alias_in_scope(requested_alias, authority_ceiling):
        return []
    fallback_alias = f"{authority_ceiling}.{local_name}"
    return [] if fallback_alias == requested_alias else [fallback_alias]


def highest_authorized_alias(
    registry_hub: RegistryHub,
    requested_alias: str,
    local_name: str,
    allowed_authority_scope: str | None = None,
) -> str:
    """Return the requested alias when authorized, otherwise the local fallback."""
    authority_ceiling = _authority_ceiling(
        registry_hub,
        allowed_authority_scope=allowed_authority_scope,
    )
    if _alias_in_scope(requested_alias, authority_ceiling):
        return requested_alias
    return f"{authority_ceiling}.{local_name}"


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


def _validate_alias_target(
    registry_hub: RegistryHub,
    target_device_id: str,
) -> AliasClaimResult | None:
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

    return None


def _progressive_result_from_direct(
    result: AliasClaimResult,
    *,
    requested_alias: str,
    granted_alias: str | None,
    fallback_reason: str | None,
    authority_ceiling: str,
) -> ProgressiveAliasClaimResult:
    return ProgressiveAliasClaimResult(
        success=result.success,
        status=result.status,
        reason=result.reason,
        requested_alias=requested_alias,
        granted_alias=granted_alias,
        alias_record=result.alias_record,
        fallback_reason=fallback_reason,
        authority_ceiling=authority_ceiling,
        conflict_id=result.conflict_id,
    )


def _authority_ceiling(
    registry_hub: RegistryHub,
    *,
    allowed_authority_scope: str | None,
) -> str:
    if allowed_authority_scope is None:
        return registry_hub.scope_path
    if _alias_in_scope(allowed_authority_scope, registry_hub.scope_path):
        return allowed_authority_scope
    return registry_hub.scope_path


def _alias_in_scope(alias: str, scope_path: str) -> bool:
    return alias == scope_path or alias.startswith(f"{scope_path}.")


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
