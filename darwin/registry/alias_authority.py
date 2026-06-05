"""Pure alias authority-step and chain evaluation helpers for RegistryHub."""

from __future__ import annotations

from darwin.models.alias_authority import (
    AliasAuthorityClaimResult,
    AliasAuthorityDecision,
    AliasAuthorityPath,
)
from darwin.models.hub import RegistryHub
from darwin.registry.aliases import claim_alias


def is_alias_within_scope(alias: str, scope_path: str) -> bool:
    """Return whether an alias is inside a scope segment boundary."""
    return alias == scope_path or alias.startswith(f"{scope_path}.")


def fallback_alias_for_scope(scope_path: str, local_name: str) -> str:
    """Return the deterministic fallback alias for a local name in a scope."""
    return f"{scope_path}.{local_name}"


def can_continue_alias_upward(registry_hub: RegistryHub) -> bool:
    """Return whether a hub has an explicit parent for future traversal."""
    return registry_hub.parent_hub_id is not None


def evaluate_alias_authority_step(
    registry_hub: RegistryHub,
    requested_alias: str,
    local_name: str,
    target_device_id: str,
    fallback_allowed: bool = True,
) -> AliasAuthorityDecision:
    """Evaluate one RegistryHub's read-only decision for an alias request."""
    target_record = registry_hub.devices.get(target_device_id)
    if target_record is None:
        return _decision(
            registry_hub,
            decision="device_blocked",
            reason="unknown_device",
            alias=requested_alias,
        )

    if target_record.current_state == "quarantined":
        return _decision(
            registry_hub,
            decision="device_blocked",
            reason="device_quarantined",
            alias=requested_alias,
        )

    if target_record.current_state == "revoked":
        return _decision(
            registry_hub,
            decision="device_blocked",
            reason="device_revoked",
            alias=requested_alias,
        )

    if _active_alias_exists(registry_hub, requested_alias):
        return _decision(
            registry_hub,
            decision="name_taken",
            reason="alias_conflict",
            alias=requested_alias,
        )

    if is_alias_within_scope(requested_alias, registry_hub.scope_path):
        return _decision(
            registry_hub,
            decision="approved_here",
            alias=requested_alias,
        )

    can_continue_upward = can_continue_alias_upward(registry_hub)
    if can_continue_upward:
        return _decision(
            registry_hub,
            decision="continue_upward",
            reason="insufficient_authority",
            alias=requested_alias,
            can_continue_upward=True,
        )

    if not fallback_allowed:
        return _decision(
            registry_hub,
            decision="insufficient_authority",
            reason="insufficient_authority",
            alias=requested_alias,
        )

    fallback_alias = fallback_alias_for_scope(registry_hub.scope_path, local_name)
    if _active_alias_exists(registry_hub, fallback_alias):
        return _decision(
            registry_hub,
            decision="name_taken",
            reason="fallback_alias_conflict",
            alias=requested_alias,
            fallback_alias=fallback_alias,
        )

    return _decision(
        registry_hub,
        decision="fallback_available",
        reason="insufficient_authority",
        alias=requested_alias,
        fallback_alias=fallback_alias,
    )


def evaluate_alias_authority_chain(
    registry_hubs: dict[str, RegistryHub],
    start_hub_id: str,
    requested_alias: str,
    local_name: str,
    target_device_id: str,
    fallback_allowed: bool = True,
) -> AliasAuthorityPath:
    """Walk explicit parent RegistryHub links and record read-only decisions."""
    path = AliasAuthorityPath(
        requested_alias=requested_alias,
        target_device_id=target_device_id,
        requesting_hub_id=start_hub_id,
    )
    current_hub_id = start_hub_id
    visited_hub_ids: set[str] = set()

    while True:
        registry_hub = registry_hubs.get(current_hub_id)
        if registry_hub is None:
            path.add_decision(
                AliasAuthorityDecision(
                    hub_id=current_hub_id,
                    scope_path="",
                    decision="authority_path_broken",
                    reason=(
                        "start_hub_not_found"
                        if current_hub_id == start_hub_id
                        else "parent_hub_not_found"
                    ),
                    alias=requested_alias,
                )
            )
            path.final_status = "authority_path_broken"
            return path

        if current_hub_id in visited_hub_ids:
            path.add_decision(
                _decision(
                    registry_hub,
                    decision="authority_path_broken",
                    reason="parent_cycle_detected",
                    alias=requested_alias,
                )
            )
            path.final_status = "authority_path_broken"
            path.authority_ceiling = registry_hub.scope_path
            return path
        visited_hub_ids.add(current_hub_id)

        decision = evaluate_alias_authority_step(
            registry_hub,
            requested_alias,
            local_name,
            target_device_id,
            fallback_allowed=fallback_allowed,
        )
        path.add_decision(decision)

        if decision.decision == "approved_here":
            path.final_status = "approved_here"
            path.granted_alias = requested_alias
            path.authority_ceiling = decision.authority_ceiling
            return path

        if decision.decision == "fallback_available":
            path.final_status = "fallback_granted"
            path.granted_alias = decision.fallback_alias
            path.authority_ceiling = decision.authority_ceiling
            return path

        if decision.decision == "continue_upward":
            parent_hub_id = registry_hub.parent_hub_id
            if parent_hub_id is None:
                path.final_status = "authority_path_broken"
                path.authority_ceiling = registry_hub.scope_path
                return path
            if parent_hub_id not in registry_hubs:
                path.add_decision(
                    AliasAuthorityDecision(
                        hub_id=parent_hub_id,
                        scope_path="",
                        decision="authority_path_broken",
                        reason="parent_hub_not_found",
                        alias=requested_alias,
                        authority_ceiling=registry_hub.scope_path,
                    )
                )
                path.final_status = "authority_path_broken"
                path.authority_ceiling = registry_hub.scope_path
                return path
            current_hub_id = parent_hub_id
            continue

        path.final_status = decision.decision
        path.authority_ceiling = decision.authority_ceiling
        return path


def claim_alias_through_authority_chain(
    registry_hubs: dict[str, RegistryHub],
    start_hub_id: str,
    requested_alias: str,
    local_name: str,
    target_device_id: str,
    requested_by_device_id: str | None = None,
    fallback_allowed: bool = True,
    visibility: str = "local",
    ttl: int | None = None,
) -> AliasAuthorityClaimResult:
    """Claim an alias only after read-only parent authority-chain approval."""
    authority_path = evaluate_alias_authority_chain(
        registry_hubs,
        start_hub_id,
        requested_alias,
        local_name,
        target_device_id,
        fallback_allowed=fallback_allowed,
    )

    if authority_path.final_status == "approved_here":
        return _claim_alias_from_authority_path(
            registry_hubs=registry_hubs,
            authority_path=authority_path,
            target_device_id=target_device_id,
            requested_by_device_id=requested_by_device_id,
            granted_alias=requested_alias,
            status="claimed",
            reason=None,
            fallback_reason=None,
            visibility=visibility,
            ttl=ttl,
        )

    if authority_path.final_status == "fallback_granted":
        return _claim_alias_from_authority_path(
            registry_hubs=registry_hubs,
            authority_path=authority_path,
            target_device_id=target_device_id,
            requested_by_device_id=requested_by_device_id,
            granted_alias=authority_path.granted_alias,
            status="fallback_granted",
            reason=_latest_reason(authority_path) or "insufficient_authority",
            fallback_reason=_latest_reason(authority_path) or "insufficient_authority",
            visibility=visibility,
            ttl=ttl,
        )

    return AliasAuthorityClaimResult(
        success=False,
        status=_failure_status(authority_path.final_status),
        reason=_latest_reason(authority_path) or authority_path.final_status,
        requested_alias=requested_alias,
        granted_alias=None,
        alias_record=None,
        authority_path=authority_path,
        authority_ceiling=authority_path.authority_ceiling,
    )


def _decision(
    registry_hub: RegistryHub,
    *,
    decision: str,
    reason: str | None = None,
    alias: str | None = None,
    fallback_alias: str | None = None,
    can_continue_upward: bool = False,
) -> AliasAuthorityDecision:
    return AliasAuthorityDecision(
        hub_id=registry_hub.hub_id,
        scope_path=registry_hub.scope_path,
        decision=decision,
        reason=reason,
        alias=alias,
        fallback_alias=fallback_alias,
        authority_ceiling=registry_hub.scope_path,
        can_continue_upward=can_continue_upward,
    )


def _active_alias_exists(registry_hub: RegistryHub, alias: str) -> bool:
    alias_record = registry_hub.aliases.get(alias)
    return alias_record is not None and alias_record.status == "active"


def _claim_alias_from_authority_path(
    *,
    registry_hubs: dict[str, RegistryHub],
    authority_path: AliasAuthorityPath,
    target_device_id: str,
    requested_by_device_id: str | None,
    granted_alias: str | None,
    status: str,
    reason: str | None,
    fallback_reason: str | None,
    visibility: str,
    ttl: int | None,
) -> AliasAuthorityClaimResult:
    terminal_decision = authority_path.latest_decision()
    if terminal_decision is None or granted_alias is None:
        return AliasAuthorityClaimResult(
            success=False,
            status="authority_path_broken",
            reason="missing_authority_decision",
            requested_alias=authority_path.requested_alias,
            granted_alias=None,
            alias_record=None,
            authority_path=authority_path,
            authority_ceiling=authority_path.authority_ceiling,
        )

    approving_hub = registry_hubs.get(terminal_decision.hub_id)
    if approving_hub is None:
        return AliasAuthorityClaimResult(
            success=False,
            status="authority_path_broken",
            reason="approval_hub_not_found",
            requested_alias=authority_path.requested_alias,
            granted_alias=None,
            alias_record=None,
            authority_path=authority_path,
            authority_ceiling=authority_path.authority_ceiling,
        )

    claim_result = claim_alias(
        approving_hub,
        granted_alias,
        target_device_id,
        requested_by_device_id=requested_by_device_id,
        visibility=visibility,
        ttl=ttl,
    )
    if not claim_result.success:
        return AliasAuthorityClaimResult(
            success=False,
            status=_failure_status(claim_result.status),
            reason=claim_result.reason,
            requested_alias=authority_path.requested_alias,
            granted_alias=None,
            alias_record=claim_result.alias_record,
            authority_path=authority_path,
            authority_ceiling=authority_path.authority_ceiling,
        )

    alias_record = claim_result.alias_record
    if alias_record is not None:
        alias_record.requested_alias = authority_path.requested_alias
        alias_record.granted_alias = granted_alias
        alias_record.fallback_reason = fallback_reason
        alias_record.authority_ceiling = authority_path.authority_ceiling
        alias_record.authority_scope = terminal_decision.scope_path
        alias_record.approved_by_registry_hub = terminal_decision.hub_id
        if fallback_reason is not None:
            alias_record.fallback_from = authority_path.requested_alias

    return AliasAuthorityClaimResult(
        success=True,
        status=status,
        reason=reason,
        requested_alias=authority_path.requested_alias,
        granted_alias=granted_alias,
        alias_record=alias_record,
        authority_path=authority_path,
        authority_ceiling=authority_path.authority_ceiling,
    )


def _latest_reason(authority_path: AliasAuthorityPath) -> str | None:
    latest_decision = authority_path.latest_decision()
    if latest_decision is None:
        return None
    return latest_decision.reason


def _failure_status(final_status: str) -> str:
    if final_status == "name_taken":
        return "conflict"
    if final_status in {"device_blocked", "insufficient_authority", "policy_denied"}:
        return "rejected"
    return final_status
