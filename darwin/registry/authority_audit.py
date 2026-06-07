"""Read-only authority audit trace summary helpers."""

from __future__ import annotations

from darwin.models.alias_authority import AliasAuthorityDecision, AliasAuthorityPath
from darwin.models.hub import RegistryHub
from darwin.registry.history_queries import query_authority_decisions


def summarize_authority_decision(
    decision: AliasAuthorityDecision,
) -> dict[str, object]:
    """Return a compact JSON-safe summary of one authority decision."""
    return {
        "hub_id": decision.hub_id,
        "scope_path": decision.scope_path,
        "status": decision.decision,
        "reason": decision.reason,
        "alias": decision.alias,
        "fallback_alias": decision.fallback_alias,
        "authority_ceiling": decision.authority_ceiling,
        "can_continue_upward": decision.can_continue_upward,
        "fallback_used": decision.decision == "fallback_available",
        "conflict_detected": decision.decision == "name_taken",
        "policy_denied": decision.decision == "policy_denied",
        "path_broken": decision.decision == "authority_path_broken",
        "summary": _decision_summary(decision),
    }


def summarize_authority_path(authority_path: AliasAuthorityPath) -> dict[str, object]:
    """Return a compact JSON-safe summary of an in-memory authority path."""
    decisions = [summarize_authority_decision(decision) for decision in authority_path.decisions]
    latest_decision = authority_path.latest_decision()
    final_status = authority_path.final_status
    return {
        "requested_alias": authority_path.requested_alias,
        "granted_alias": authority_path.granted_alias,
        "target_device": authority_path.target_device_id,
        "final_status": final_status,
        "status": final_status,
        "reason": latest_decision.reason if latest_decision is not None else None,
        "authority_ceiling": authority_path.authority_ceiling,
        "decision_count": len(authority_path.decisions),
        "path_hubs": [decision.hub_id for decision in authority_path.decisions],
        "decisions": decisions,
        "fallback_used": final_status == "fallback_granted",
        "conflict_detected": _path_has_decision(authority_path, "name_taken"),
        "policy_denied": _path_has_decision(authority_path, "policy_denied"),
        "path_broken": final_status == "authority_path_broken",
        "summary": _path_summary(authority_path),
    }


def build_authority_audit_trace(
    registry_hub: RegistryHub,
    *,
    requested_alias: str | None = None,
    granted_alias: str | None = None,
    device_id: str | None = None,
    final_status: str | None = None,
) -> list[dict[str, object]]:
    """Build read-only audit trace summaries from retained RegistryHub data."""
    traces: list[dict[str, object]] = []
    for decision in query_authority_decisions(
        registry_hub,
        requested_alias=requested_alias,
        granted_alias=granted_alias,
        device_id=device_id,
        final_status=final_status,
    ):
        traces.append(
            {
                "requested_alias": decision.requested_alias,
                "granted_alias": decision.granted_alias,
                "target_device": decision.device_id,
                "final_status": decision.final_status,
                "status": decision.alias_status,
                "reason": decision.fallback_reason,
                "authority_ceiling": decision.authority_ceiling,
                "decision_count": 1,
                "path_hubs": [decision.approved_by_registry_hub],
                "decisions": [
                    {
                        "hub_id": decision.approved_by_registry_hub,
                        "scope_path": decision.authority_scope,
                        "status": decision.final_status,
                        "reason": decision.fallback_reason,
                        "alias": decision.requested_alias,
                        "fallback_alias": (
                            decision.granted_alias
                            if decision.final_status == "fallback_granted"
                            else None
                        ),
                        "authority_ceiling": decision.authority_ceiling,
                    }
                ],
                "fallback_used": decision.final_status == "fallback_granted",
                "conflict_detected": False,
                "policy_denied": False,
                "path_broken": False,
                "summary": _retained_trace_summary(
                    decision.final_status,
                    decision.approved_by_registry_hub,
                ),
            }
        )
    return traces


def _path_has_decision(authority_path: AliasAuthorityPath, decision: str) -> bool:
    return any(path_decision.decision == decision for path_decision in authority_path.decisions)


def _decision_summary(decision: AliasAuthorityDecision) -> str:
    if decision.decision == "approved_here":
        return f"approved at {decision.hub_id}"
    if decision.decision == "fallback_available":
        return f"fallback available at {decision.hub_id}"
    if decision.decision == "continue_upward":
        return f"continued upward from {decision.hub_id}"
    if decision.decision == "name_taken":
        return "denied because alias was already taken"
    if decision.decision == "policy_denied":
        return "denied by simulator-local policy"
    if decision.decision == "authority_path_broken":
        return f"authority path broken at {decision.hub_id}"
    if decision.decision == "device_blocked":
        return "denied because target device was blocked"
    if decision.decision == "insufficient_authority":
        return "denied because authority was insufficient"
    return decision.decision


def _path_summary(authority_path: AliasAuthorityPath) -> str:
    latest_decision = authority_path.latest_decision()
    hub_id = (
        latest_decision.hub_id
        if latest_decision is not None
        else authority_path.requesting_hub_id
    )
    if authority_path.final_status == "approved_here":
        return f"approved at {hub_id}"
    if authority_path.final_status == "fallback_granted":
        return f"fallback granted at {hub_id}"
    if authority_path.final_status == "name_taken":
        return "denied because alias was already taken"
    if authority_path.final_status == "policy_denied":
        return "denied by simulator-local policy"
    if authority_path.final_status == "authority_path_broken":
        return f"authority path broken at {hub_id}"
    if authority_path.final_status == "device_blocked":
        return "denied because target device was blocked"
    if authority_path.final_status == "insufficient_authority":
        return "denied because authority was insufficient"
    return authority_path.final_status


def _retained_trace_summary(final_status: str, hub_id: str) -> str:
    if final_status == "approved_here":
        return f"approved at {hub_id}"
    if final_status == "fallback_granted":
        return f"fallback granted at {hub_id}"
    return final_status
