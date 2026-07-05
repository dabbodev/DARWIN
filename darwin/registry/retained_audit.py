"""Read-only retained audit compaction classification helpers."""

from __future__ import annotations

from typing import Any

from darwin.models.retained_audit import (
    RetainedAuditCompactionDecision,
    RetainedAuditCompactionPolicy,
    make_retained_audit_compaction_policy,
)
from darwin.models.stream_offer import (
    StreamOfferLifecycleExplanation,
    StreamOfferStatusTransition,
)

SUPPORTED_RETAINED_AUDIT_HISTORY_TYPES: tuple[str, ...] = (
    "stream_offer_lifecycle_explanation",
    "stream_offer_status_transition",
)


def classify_retained_audit_records_for_compaction(
    records: list[object] | tuple[object, ...],
    policy: RetainedAuditCompactionPolicy,
    *,
    metadata: dict[str, object] | None = None,
) -> RetainedAuditCompactionDecision:
    """Classify explicit retained audit records under a read-only policy.

    Retain filters take precedence over compact filters. Records from another
    hub, records outside policy history_types, and unsupported records are
    ignored. This helper never mutates RegistryHub or any retained history.
    """
    record_entries = _record_tuple(records)
    _validate_compaction_policy(policy)
    if metadata is not None and not isinstance(metadata, dict):
        raise TypeError("metadata must be a JSON-safe dict")

    entries: list[tuple[_AuditRecordView, str]] = []
    retainable_keys: list[str] = []

    for index, record in enumerate(record_entries):
        view = _audit_record_view(index, record)
        if view.history_type not in SUPPORTED_RETAINED_AUDIT_HISTORY_TYPES:
            entries.append((view, "ignored"))
            continue

        if policy.history_types and view.history_type not in policy.history_types:
            entries.append((view, "ignored"))
            continue

        if view.hub_id != policy.hub_id:
            entries.append((view, "ignored"))
            continue

        if _matches_compaction_filters(
            view,
            reasons=policy.retain_reasons,
            statuses=policy.retain_statuses,
            sources=policy.retain_sources,
        ):
            entries.append((view, "retained"))
            retainable_keys.append(view.record_key)
            continue

        if _matches_compaction_filters(
            view,
            reasons=policy.compact_reasons,
            statuses=policy.compact_statuses,
            sources=policy.compact_sources,
        ):
            entries.append((view, "compaction_candidate"))
            continue

        entries.append((view, "retained"))
        retainable_keys.append(view.record_key)

    if policy.max_records is not None:
        retained_under_cap = set(retainable_keys[: policy.max_records])
        entries = [
            (
                view,
                (
                    "compaction_candidate"
                    if decision_category == "retained"
                    and view.record_key not in retained_under_cap
                    else decision_category
                ),
            )
            for view, decision_category in entries
        ]

    retained_record_keys = [
        view.record_key
        for view, decision_category in entries
        if decision_category == "retained"
    ]
    compaction_candidate_record_keys = [
        view.record_key
        for view, decision_category in entries
        if decision_category == "compaction_candidate"
    ]
    ignored_record_keys = [
        view.record_key
        for view, decision_category in entries
        if decision_category == "ignored"
    ]
    candidate_by_history_type: dict[str, int] = {}
    candidate_by_reason: dict[str, int] = {}
    candidate_by_status: dict[str, int] = {}
    candidate_by_source: dict[str, int] = {}

    for view, decision_category in entries:
        if decision_category != "compaction_candidate":
            continue
        _increment_count(candidate_by_history_type, view.history_type)
        _increment_count(candidate_by_reason, view.reason or "none")
        _increment_count(candidate_by_status, view.status or "none")
        _increment_count(candidate_by_source, view.source or "none")

    decision_metadata: dict[str, object] = {
        "simulator_local": True,
        "read_only": True,
        "compaction_decision_only": True,
        "policy_decision": True,
        "registry_hub_mutated": False,
        "retained_history_mutated": False,
        "records_deleted": False,
        "records_compacted": False,
        "records_rewritten": False,
        "cleanup_scheduled": False,
        "background_worker": False,
        "retry_loop": False,
        "durable_queue": False,
        "live_timer": False,
        "delivery_behavior_changed": False,
        "traffic_hub_routing_changed": False,
        "networking": False,
        "dns_lookup": False,
        "external_services": False,
        "cryptography": False,
        "compact_snapshot_changed": False,
        "filter_precedence": "retain_filters_before_compact_filters",
        "max_records_applied": policy.max_records is not None,
        "supported_history_types": list(SUPPORTED_RETAINED_AUDIT_HISTORY_TYPES),
        "unsupported_records_ignored": any(
            view.history_type not in SUPPORTED_RETAINED_AUDIT_HISTORY_TYPES
            for view, _decision_category in entries
        ),
    }
    if metadata is not None:
        decision_metadata.update(metadata)

    return RetainedAuditCompactionDecision(
        hub_id=policy.hub_id,
        policy_id=policy.policy_id,
        history_type=_decision_history_type(policy),
        retained_record_keys=retained_record_keys,
        compaction_candidate_record_keys=compaction_candidate_record_keys,
        ignored_record_keys=ignored_record_keys,
        by_decision_category={
            "compaction_candidate": len(compaction_candidate_record_keys),
            "ignored": len(ignored_record_keys),
            "retained": len(retained_record_keys),
        },
        candidate_by_history_type=_sorted_count_dict(candidate_by_history_type),
        candidate_by_reason=_sorted_count_dict(candidate_by_reason),
        candidate_by_status=_sorted_count_dict(candidate_by_status),
        candidate_by_source=_sorted_count_dict(candidate_by_source),
        metadata=decision_metadata,
    )


def summarize_retained_audit_compaction_decision(
    decision: RetainedAuditCompactionDecision,
) -> dict[str, object]:
    """Return a copied JSON-safe retained audit compaction decision summary."""
    if not isinstance(decision, RetainedAuditCompactionDecision):
        raise TypeError("decision must be a RetainedAuditCompactionDecision")
    return decision.to_summary()


class _AuditRecordView:
    def __init__(
        self,
        *,
        history_type: str,
        record_key: str,
        hub_id: str | None,
        reason: str | None,
        status: str | None,
        source: str | None,
    ) -> None:
        self.history_type = history_type
        self.record_key = record_key
        self.hub_id = hub_id
        self.reason = reason
        self.status = status
        self.source = source


def _record_tuple(records: list[object] | tuple[object, ...]) -> tuple[object, ...]:
    if not isinstance(records, list | tuple):
        raise TypeError("records must be a list or tuple")
    return tuple(records)


def _validate_compaction_policy(policy: RetainedAuditCompactionPolicy) -> None:
    if not isinstance(policy, RetainedAuditCompactionPolicy):
        raise TypeError("policy must be a RetainedAuditCompactionPolicy")


def _audit_record_view(index: int, record: object) -> _AuditRecordView:
    if isinstance(record, StreamOfferLifecycleExplanation):
        return _AuditRecordView(
            history_type="stream_offer_lifecycle_explanation",
            record_key=_lifecycle_explanation_key(index, record),
            hub_id=record.hub_id,
            reason=record.reason,
            status=record.status,
            source=record.source,
        )
    if isinstance(record, StreamOfferStatusTransition):
        return _AuditRecordView(
            history_type="stream_offer_status_transition",
            record_key=_status_transition_key(index, record),
            hub_id=record.hub_id,
            reason=record.reason.reason,
            status=record.new_status.status,
            source=_metadata_source(record.metadata),
        )
    return _AuditRecordView(
        history_type=f"unsupported:{record.__class__.__name__}",
        record_key=f"unsupported:{index}:{record.__class__.__name__}",
        hub_id=None,
        reason=None,
        status=None,
        source=None,
    )


def _matches_compaction_filters(
    view: _AuditRecordView,
    *,
    reasons: tuple[str, ...],
    statuses: tuple[str, ...],
    sources: tuple[str, ...],
) -> bool:
    return (
        (bool(reasons) and view.reason in reasons)
        or (bool(statuses) and view.status in statuses)
        or (bool(sources) and view.source in sources)
    )


def _decision_history_type(policy: RetainedAuditCompactionPolicy) -> str:
    if len(policy.history_types) == 1:
        return policy.history_types[0]
    return "mixed"


def _lifecycle_explanation_key(
    index: int,
    explanation: StreamOfferLifecycleExplanation,
) -> str:
    checked_at = "none" if explanation.checked_at is None else str(explanation.checked_at)
    source = "none" if explanation.source is None else explanation.source
    return (
        f"lifecycle_explanation:{index}:{explanation.hub_id}:"
        f"{explanation.offer_id}:{explanation.category}:{explanation.reason}:"
        f"{explanation.status}:{source}:{checked_at}"
    )


def _status_transition_key(index: int, transition: StreamOfferStatusTransition) -> str:
    sequence = "none" if transition.sequence is None else str(transition.sequence)
    actor_id = "none" if transition.actor_id is None else transition.actor_id
    request_id = "none" if transition.request_id is None else transition.request_id
    return (
        f"status_transition:{index}:{transition.hub_id}:{transition.offer_id}:"
        f"{transition.previous_status.status}:{transition.new_status.status}:"
        f"{transition.reason.reason}:{actor_id}:{request_id}:{sequence}"
    )


def _metadata_source(metadata: dict[str, Any] | None) -> str | None:
    if not isinstance(metadata, dict):
        return None
    source = metadata.get("source")
    return source if isinstance(source, str) else None


def _increment_count(counts: dict[str, int], key: str) -> None:
    counts[key] = counts.get(key, 0) + 1


def _sorted_count_dict(counts: dict[str, int]) -> dict[str, int]:
    return {key: counts[key] for key in sorted(counts)}


__all__ = [
    "SUPPORTED_RETAINED_AUDIT_HISTORY_TYPES",
    "classify_retained_audit_records_for_compaction",
    "make_retained_audit_compaction_policy",
    "summarize_retained_audit_compaction_decision",
]
