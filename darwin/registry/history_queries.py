"""Read-only RegistryHub history query helpers."""

from __future__ import annotations

from dataclasses import dataclass

from darwin.models.alias import AliasRecord
from darwin.models.alias_authority import AliasAuthorityOutcomeRecord
from darwin.models.hub import ConflictRecord, RegistryHub
from darwin.models.security import QuarantineRecord, SecurityEvent


@dataclass(frozen=True, slots=True)
class AliasHistoryQueryResult:
    """Compact JSON-safe view of a retained alias record."""

    alias: str
    target_device_id: str | None
    target_identity_chain: str
    requested_by_device_id: str | None
    requested_through_hub: str | None
    approved_by_registry_hub: str
    authority_scope: str
    status: str
    visibility: str
    ttl: int | None
    conflict_id: str | None
    requested_alias: str | None
    granted_alias: str | None
    fallback_reason: str | None
    authority_ceiling: str | None
    fallback_from: str | None

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return {
            "alias": self.alias,
            "target_device_id": self.target_device_id,
            "target_identity_chain": self.target_identity_chain,
            "requested_by_device_id": self.requested_by_device_id,
            "requested_through_hub": self.requested_through_hub,
            "approved_by_registry_hub": self.approved_by_registry_hub,
            "authority_scope": self.authority_scope,
            "status": self.status,
            "visibility": self.visibility,
            "ttl": self.ttl,
            "conflict_id": self.conflict_id,
            "requested_alias": self.requested_alias,
            "granted_alias": self.granted_alias,
            "fallback_reason": self.fallback_reason,
            "authority_ceiling": self.authority_ceiling,
            "fallback_from": self.fallback_from,
        }


@dataclass(frozen=True, slots=True)
class AliasConflictQueryResult:
    """Compact JSON-safe view of an alias conflict record."""

    conflict_id: str
    alias: str
    existing_device_id: str
    requesting_device_id: str
    status: str

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return {
            "conflict_id": self.conflict_id,
            "alias": self.alias,
            "existing_device_id": self.existing_device_id,
            "requesting_device_id": self.requesting_device_id,
            "status": self.status,
        }


@dataclass(frozen=True, slots=True)
class AuthorityDecisionQueryResult:
    """Persisted alias authority provenance for a granted alias."""

    requested_alias: str
    granted_alias: str
    device_id: str | None
    final_status: str
    approved_by_registry_hub: str
    authority_scope: str
    authority_ceiling: str | None
    fallback_reason: str | None
    alias: str
    alias_status: str

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return {
            "requested_alias": self.requested_alias,
            "granted_alias": self.granted_alias,
            "device_id": self.device_id,
            "final_status": self.final_status,
            "approved_by_registry_hub": self.approved_by_registry_hub,
            "authority_scope": self.authority_scope,
            "authority_ceiling": self.authority_ceiling,
            "fallback_reason": self.fallback_reason,
            "alias": self.alias,
            "alias_status": self.alias_status,
        }


@dataclass(frozen=True, slots=True)
class QuarantineEventQueryResult:
    """Compact JSON-safe view of a persisted quarantine record."""

    quarantine_key: str
    device_id: str
    reason: str
    source_hub_id: str | None
    created_at: int | None
    status: str
    event_type: str | None
    severity: str | None
    action_taken: str | None

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return {
            "quarantine_key": self.quarantine_key,
            "device_id": self.device_id,
            "reason": self.reason,
            "source_hub_id": self.source_hub_id,
            "created_at": self.created_at,
            "status": self.status,
            "event_type": self.event_type,
            "severity": self.severity,
            "action_taken": self.action_taken,
        }


@dataclass(frozen=True, slots=True)
class AuthorityOutcomeQueryResult:
    """Compact JSON-safe view of a retained authority outcome."""

    record_id: str
    requested_alias: str
    granted_alias: str | None
    target_device: str | None
    requesting_hub: str | None
    authority_ceiling: str | None
    final_status: str
    status: str | None
    reason: str | None
    decision_count: int
    path_hubs: tuple[str, ...]
    decisions: tuple[dict[str, object], ...]
    fallback_used: bool
    conflict_detected: bool
    policy_denied: bool
    path_broken: bool

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return {
            "record_id": self.record_id,
            "requested_alias": self.requested_alias,
            "granted_alias": self.granted_alias,
            "target_device": self.target_device,
            "requesting_hub": self.requesting_hub,
            "authority_ceiling": self.authority_ceiling,
            "final_status": self.final_status,
            "status": self.status,
            "reason": self.reason,
            "decision_count": self.decision_count,
            "path_hubs": list(self.path_hubs),
            "decisions": [dict(decision) for decision in self.decisions],
            "fallback_used": self.fallback_used,
            "conflict_detected": self.conflict_detected,
            "policy_denied": self.policy_denied,
            "path_broken": self.path_broken,
        }


def query_alias_history(
    registry_hub: RegistryHub,
    *,
    alias: str | None = None,
    device_id: str | None = None,
    status: str | None = None,
) -> list[AliasHistoryQueryResult]:
    """Query retained alias records without mutating registry state."""
    results: list[AliasHistoryQueryResult] = []
    for alias_key in sorted(registry_hub.aliases):
        record = registry_hub.aliases[alias_key]
        if alias is not None and record.alias != alias:
            continue
        if device_id is not None and not _alias_record_matches_device(record, device_id):
            continue
        if status is not None and record.status != status:
            continue
        results.append(_alias_history_result(record))
    return results


def query_alias_conflicts(
    registry_hub: RegistryHub,
    *,
    alias: str | None = None,
    device_id: str | None = None,
) -> list[AliasConflictQueryResult]:
    """Query persisted alias conflict records without mutating registry state."""
    results: list[AliasConflictQueryResult] = []
    for conflict_id in sorted(registry_hub.conflicts):
        conflict = registry_hub.conflicts[conflict_id]
        if conflict.conflict_type != "alias_conflict":
            continue
        if alias is not None and conflict.requested_label != alias:
            continue
        if device_id is not None and not _conflict_matches_device(conflict, device_id):
            continue
        results.append(
            AliasConflictQueryResult(
                conflict_id=conflict.conflict_id,
                alias=conflict.requested_label,
                existing_device_id=conflict.existing_device_id,
                requesting_device_id=conflict.requesting_device_id,
                status=conflict.status,
            )
        )
    return results


def query_authority_decisions(
    registry_hub: RegistryHub,
    *,
    requested_alias: str | None = None,
    granted_alias: str | None = None,
    device_id: str | None = None,
    final_status: str | None = None,
) -> list[AuthorityDecisionQueryResult]:
    """Query persisted alias authority provenance from retained alias records."""
    results: list[AuthorityDecisionQueryResult] = []
    for alias_key in sorted(registry_hub.aliases):
        record = registry_hub.aliases[alias_key]
        result = _authority_result(record)
        if result is None:
            continue
        if requested_alias is not None and result.requested_alias != requested_alias:
            continue
        if granted_alias is not None and result.granted_alias != granted_alias:
            continue
        if device_id is not None and result.device_id != device_id:
            continue
        if final_status is not None and result.final_status != final_status:
            continue
        results.append(result)
    return results


def query_authority_outcomes(
    registry_hub: RegistryHub,
    *,
    requested_alias: str | None = None,
    granted_alias: str | None = None,
    device_id: str | None = None,
    requesting_hub: str | None = None,
    final_status: str | None = None,
    status: str | None = None,
    reason: str | None = None,
    authority_ceiling: str | None = None,
    fallback_used: bool | None = None,
    conflict_detected: bool | None = None,
    policy_denied: bool | None = None,
    path_broken: bool | None = None,
) -> list[AuthorityOutcomeQueryResult]:
    """Query retained authority outcomes without mutating registry state."""
    results: list[AuthorityOutcomeQueryResult] = []
    for record in registry_hub.authority_outcome_history:
        if requested_alias is not None and record.requested_alias != requested_alias:
            continue
        if granted_alias is not None and record.granted_alias != granted_alias:
            continue
        if device_id is not None and record.target_device != device_id:
            continue
        if requesting_hub is not None and record.requesting_hub != requesting_hub:
            continue
        if final_status is not None and record.final_status != final_status:
            continue
        if status is not None and record.status != status:
            continue
        if reason is not None and record.reason != reason:
            continue
        if authority_ceiling is not None and record.authority_ceiling != authority_ceiling:
            continue
        if fallback_used is not None and record.fallback_used != fallback_used:
            continue
        if (
            conflict_detected is not None
            and record.conflict_detected != conflict_detected
        ):
            continue
        if policy_denied is not None and record.policy_denied != policy_denied:
            continue
        if path_broken is not None and record.path_broken != path_broken:
            continue
        results.append(_authority_outcome_result(record))
    return results


def query_quarantine_events(
    registry_hub: RegistryHub,
    *,
    device_id: str | None = None,
    reason: str | None = None,
) -> list[QuarantineEventQueryResult]:
    """Query persisted quarantine records without mutating registry state."""
    results: list[QuarantineEventQueryResult] = []
    for quarantine_key in sorted(
        registry_hub.quarantines,
        key=lambda key: _quarantine_sort_key(key, registry_hub.quarantines[key]),
    ):
        record = registry_hub.quarantines[quarantine_key]
        if device_id is not None and record.claimed_device_id != device_id:
            continue
        if reason is not None and record.reason != reason:
            continue
        event = _matching_quarantine_event(registry_hub, record)
        results.append(
            QuarantineEventQueryResult(
                quarantine_key=quarantine_key,
                device_id=record.claimed_device_id,
                reason=record.reason,
                source_hub_id=record.source_hub_id,
                created_at=record.created_at,
                status=record.status,
                event_type=event.event_type if event is not None else None,
                severity=event.severity if event is not None else None,
                action_taken=event.action_taken if event is not None else None,
            )
        )
    return results


def _alias_history_result(record: AliasRecord) -> AliasHistoryQueryResult:
    return AliasHistoryQueryResult(
        alias=record.alias,
        target_device_id=record.target_device_id,
        target_identity_chain=record.target_identity_chain,
        requested_by_device_id=record.requested_by_device_id,
        requested_through_hub=record.requested_through_hub,
        approved_by_registry_hub=record.approved_by_registry_hub,
        authority_scope=record.authority_scope,
        status=record.status,
        visibility=record.visibility,
        ttl=record.ttl,
        conflict_id=record.conflict_id,
        requested_alias=record.requested_alias,
        granted_alias=record.granted_alias,
        fallback_reason=record.fallback_reason,
        authority_ceiling=record.authority_ceiling,
        fallback_from=record.fallback_from,
    )


def _authority_outcome_result(
    record: AliasAuthorityOutcomeRecord,
) -> AuthorityOutcomeQueryResult:
    return AuthorityOutcomeQueryResult(
        record_id=record.record_id,
        requested_alias=record.requested_alias,
        granted_alias=record.granted_alias,
        target_device=record.target_device,
        requesting_hub=record.requesting_hub,
        authority_ceiling=record.authority_ceiling,
        final_status=record.final_status,
        status=record.status,
        reason=record.reason,
        decision_count=record.decision_count,
        path_hubs=tuple(record.path_hubs),
        decisions=tuple(dict(decision) for decision in record.decisions),
        fallback_used=record.fallback_used,
        conflict_detected=record.conflict_detected,
        policy_denied=record.policy_denied,
        path_broken=record.path_broken,
    )


def _authority_result(record: AliasRecord) -> AuthorityDecisionQueryResult | None:
    if record.requested_alias is None or record.granted_alias is None:
        return None
    final_status = "fallback_granted" if record.fallback_reason is not None else "approved_here"
    return AuthorityDecisionQueryResult(
        requested_alias=record.requested_alias,
        granted_alias=record.granted_alias,
        device_id=record.target_device_id,
        final_status=final_status,
        approved_by_registry_hub=record.approved_by_registry_hub,
        authority_scope=record.authority_scope,
        authority_ceiling=record.authority_ceiling,
        fallback_reason=record.fallback_reason,
        alias=record.alias,
        alias_status=record.status,
    )


def _alias_record_matches_device(record: AliasRecord, device_id: str) -> bool:
    return device_id in {
        record.target_device_id,
        record.requested_by_device_id,
    }


def _conflict_matches_device(conflict: ConflictRecord, device_id: str) -> bool:
    return device_id in {
        conflict.existing_device_id,
        conflict.requesting_device_id,
    }


def _matching_quarantine_event(
    registry_hub: RegistryHub,
    quarantine: QuarantineRecord,
) -> SecurityEvent | None:
    for event in registry_hub.security_events:
        if event.claimed_device_id != quarantine.claimed_device_id:
            continue
        if event.reason != quarantine.reason:
            continue
        if event.action_taken.endswith("quarantined") or "quarantine" in event.event_type:
            return event
    return None


def _quarantine_sort_key(
    quarantine_key: str,
    quarantine: QuarantineRecord,
) -> tuple[int, int, str, str]:
    missing_timestamp = 1 if quarantine.created_at is None else 0
    return (
        missing_timestamp,
        quarantine.created_at or 0,
        quarantine.claimed_device_id,
        quarantine_key,
    )
