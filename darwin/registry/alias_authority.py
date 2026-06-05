"""Pure alias authority-step and chain evaluation helpers for RegistryHub."""

from __future__ import annotations

from darwin.models.alias_authority import AliasAuthorityDecision, AliasAuthorityPath
from darwin.models.hub import RegistryHub


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
