"""Read-only retained audit compaction classification helpers."""

from __future__ import annotations

from typing import Any

from darwin.models.hub import RegistryHub
from darwin.models.retained_audit import (
    RetainedAuditCompactionApplyResult,
    RetainedAuditCompactionDecision,
    RetainedAuditCompactionPolicy,
    RetainedAuditReplaySummary,
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

RETAINED_AUDIT_REPLAY_DECISION_CATEGORY_FILTERS: tuple[str, ...] = (
    "all",
    "retained",
    "compaction_candidate",
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


def summarize_retained_audit_replay(
    records: list[object] | tuple[object, ...],
    *,
    hub_id: str,
    history_type: str | None = None,
    decision: RetainedAuditCompactionDecision | None = None,
    decision_category: str = "all",
    metadata: dict[str, object] | None = None,
) -> RetainedAuditReplaySummary:
    """Return a read-only replay summary for explicit retained audit records."""
    views, ignored_record_keys, filtered_record_keys = _replay_record_views(
        records,
        hub_id=hub_id,
        history_type=history_type,
        decision=decision,
        decision_category=decision_category,
    )
    if metadata is not None and not isinstance(metadata, dict):
        raise TypeError("metadata must be a JSON-safe dict")

    record_keys: list[str] = []
    by_status: dict[str, int] = {}
    by_reason: dict[str, int] = {}
    by_source: dict[str, int] = {}
    by_offer_id: dict[str, int] = {}

    for view in views:
        record_keys.append(view.record_key)
        _increment_count(by_status, view.status or "none")
        _increment_count(by_reason, view.reason or "none")
        _increment_count(by_source, view.source or "none")
        if view.offer_id is not None:
            _increment_count(by_offer_id, view.offer_id)

    summary_metadata: dict[str, object] = {
        "simulator_local": True,
        "read_only": True,
        "replay_summary_only": True,
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
        "supported_history_types": list(SUPPORTED_RETAINED_AUDIT_HISTORY_TYPES),
        "history_type_filter": history_type,
        "decision_category_filter": decision_category,
        "ignored_record_keys": ignored_record_keys,
        "filtered_record_keys": filtered_record_keys,
        "unsupported_records_ignored": any(
            key.startswith("unsupported:") for key in ignored_record_keys
        ),
        "wrong_hub_records_ignored": any(
            not key.startswith("unsupported:") for key in ignored_record_keys
        ),
        "filtered_records_ignored": bool(filtered_record_keys),
    }
    if metadata is not None:
        summary_metadata.update(metadata)

    return RetainedAuditReplaySummary(
        hub_id=hub_id,
        history_type=_summary_history_type(views, history_type),
        record_count=len(record_keys),
        record_keys=record_keys,
        by_status=_sorted_count_dict(by_status),
        by_reason=_sorted_count_dict(by_reason),
        by_source=_sorted_count_dict(by_source),
        by_offer_id=_sorted_count_dict(by_offer_id),
        first_record_key=record_keys[0] if record_keys else None,
        last_record_key=record_keys[-1] if record_keys else None,
        metadata=summary_metadata,
    )


def summarize_retained_audit_replay_by_history_type(
    records: list[object] | tuple[object, ...],
    *,
    hub_id: str,
    decision: RetainedAuditCompactionDecision | None = None,
    decision_category: str = "all",
) -> dict[str, int]:
    """Return replay counts grouped by retained audit history type."""
    views, _ignored_record_keys, _filtered_record_keys = _replay_record_views(
        records,
        hub_id=hub_id,
        history_type=None,
        decision=decision,
        decision_category=decision_category,
    )
    by_history_type: dict[str, int] = {}
    for view in views:
        _increment_count(by_history_type, view.history_type)
    return _sorted_count_dict(by_history_type)


def summarize_retained_audit_replay_by_reason(
    records: list[object] | tuple[object, ...],
    *,
    hub_id: str,
    history_type: str | None = None,
    decision: RetainedAuditCompactionDecision | None = None,
    decision_category: str = "all",
) -> dict[str, int]:
    """Return replay counts grouped by retained audit reason."""
    return dict(
        summarize_retained_audit_replay(
            records,
            hub_id=hub_id,
            history_type=history_type,
            decision=decision,
            decision_category=decision_category,
        ).by_reason
        or {}
    )


def apply_retained_audit_compaction_decision(
    registry_hub: RegistryHub,
    decision: RetainedAuditCompactionDecision,
    *,
    metadata: dict[str, object] | None = None,
) -> RetainedAuditCompactionApplyResult:
    """Explicitly remove selected compaction-candidate retained audit records."""
    _validate_registry_hub(registry_hub)
    _validate_compaction_decision(decision)
    if registry_hub.hub_id != decision.hub_id:
        raise ValueError("decision hub_id must match registry_hub.hub_id")
    if metadata is not None and not isinstance(metadata, dict):
        raise TypeError("metadata must be a JSON-safe dict")

    if decision.history_type not in SUPPORTED_RETAINED_AUDIT_HISTORY_TYPES:
        unsupported_record_keys = _ordered_unique(
            (
                *decision.compaction_candidate_record_keys,
                *decision.retained_record_keys,
                *decision.ignored_record_keys,
            )
        )
        result_metadata = _compaction_apply_metadata(
            compacted_record_keys=[],
            history_type=decision.history_type,
            selected_history_mutated=False,
            unsupported_history_type=True,
            metadata=metadata,
        )
        return RetainedAuditCompactionApplyResult(
            hub_id=registry_hub.hub_id,
            policy_id=decision.policy_id,
            history_type=decision.history_type,
            unsupported_record_keys=unsupported_record_keys,
            unsupported_count=len(unsupported_record_keys),
            metadata=result_metadata,
        )

    candidate_key_set = set(decision.compaction_candidate_record_keys)
    retained_key_set = set(decision.retained_record_keys)
    ignored_key_set = set(decision.ignored_record_keys)
    compacted_record_keys: list[str] = []
    retained_record_keys: list[str] = []
    ignored_record_keys: list[str] = []
    remaining_records: list[object] = []

    selected_history = _selected_retained_history(registry_hub, decision.history_type)
    for index, record in enumerate(selected_history):
        view = _audit_record_view(index, record)
        if view.record_key in candidate_key_set:
            compacted_record_keys.append(view.record_key)
            continue

        remaining_records.append(record)
        if view.record_key in retained_key_set:
            retained_record_keys.append(view.record_key)
        if view.record_key in ignored_key_set:
            ignored_record_keys.append(view.record_key)

    compacted_key_set = set(compacted_record_keys)
    missing_record_keys = [
        record_key
        for record_key in decision.compaction_candidate_record_keys
        if record_key not in compacted_key_set
    ]
    if compacted_record_keys:
        selected_history[:] = remaining_records

    result_metadata = _compaction_apply_metadata(
        compacted_record_keys=compacted_record_keys,
        history_type=decision.history_type,
        selected_history_mutated=bool(compacted_record_keys),
        unsupported_history_type=False,
        metadata=metadata,
    )

    return RetainedAuditCompactionApplyResult(
        hub_id=registry_hub.hub_id,
        policy_id=decision.policy_id,
        history_type=decision.history_type,
        compacted_record_keys=compacted_record_keys,
        retained_record_keys=retained_record_keys,
        ignored_record_keys=ignored_record_keys,
        missing_record_keys=missing_record_keys,
        compacted_count=len(compacted_record_keys),
        retained_count=len(retained_record_keys),
        ignored_count=len(ignored_record_keys),
        missing_count=len(missing_record_keys),
        metadata=result_metadata,
    )


def summarize_retained_audit_compaction_apply_result(
    result: RetainedAuditCompactionApplyResult,
) -> dict[str, object]:
    """Return a copied JSON-safe retained audit compaction apply result summary."""
    if not isinstance(result, RetainedAuditCompactionApplyResult):
        raise TypeError("result must be a RetainedAuditCompactionApplyResult")
    return result.to_summary()


class _AuditRecordView:
    def __init__(
        self,
        *,
        history_type: str,
        record_key: str,
        hub_id: str | None,
        offer_id: str | None,
        reason: str | None,
        status: str | None,
        source: str | None,
    ) -> None:
        self.history_type = history_type
        self.record_key = record_key
        self.hub_id = hub_id
        self.offer_id = offer_id
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


def _validate_compaction_decision(decision: RetainedAuditCompactionDecision) -> None:
    if not isinstance(decision, RetainedAuditCompactionDecision):
        raise TypeError("decision must be a RetainedAuditCompactionDecision")


def _validate_registry_hub(registry_hub: RegistryHub) -> None:
    if not isinstance(registry_hub, RegistryHub):
        raise TypeError("registry_hub must be a RegistryHub")


def _audit_record_view(index: int, record: object) -> _AuditRecordView:
    if isinstance(record, StreamOfferLifecycleExplanation):
        return _AuditRecordView(
            history_type="stream_offer_lifecycle_explanation",
            record_key=_lifecycle_explanation_key(index, record),
            hub_id=record.hub_id,
            offer_id=record.offer_id,
            reason=record.reason,
            status=record.status,
            source=record.source,
        )
    if isinstance(record, StreamOfferStatusTransition):
        return _AuditRecordView(
            history_type="stream_offer_status_transition",
            record_key=_status_transition_key(index, record),
            hub_id=record.hub_id,
            offer_id=record.offer_id,
            reason=record.reason.reason,
            status=record.new_status.status,
            source=_metadata_source(record.metadata),
        )
    return _AuditRecordView(
        history_type=f"unsupported:{record.__class__.__name__}",
        record_key=f"unsupported:{index}:{record.__class__.__name__}",
        hub_id=None,
        offer_id=None,
        reason=None,
        status=None,
        source=None,
    )


def _replay_record_views(
    records: list[object] | tuple[object, ...],
    *,
    hub_id: str,
    history_type: str | None,
    decision: RetainedAuditCompactionDecision | None,
    decision_category: str,
) -> tuple[list[_AuditRecordView], list[str], list[str]]:
    record_entries = _record_tuple(records)
    _validate_replay_decision_filter(decision, decision_category, hub_id)
    allowed_record_keys = _decision_record_key_filter(decision, decision_category)

    views: list[_AuditRecordView] = []
    ignored_record_keys: list[str] = []
    filtered_record_keys: list[str] = []

    for index, record in enumerate(record_entries):
        view = _audit_record_view(index, record)
        if view.history_type not in SUPPORTED_RETAINED_AUDIT_HISTORY_TYPES:
            ignored_record_keys.append(view.record_key)
            continue

        if view.hub_id != hub_id:
            ignored_record_keys.append(view.record_key)
            continue

        if history_type is not None and view.history_type != history_type:
            filtered_record_keys.append(view.record_key)
            continue

        if allowed_record_keys is not None and view.record_key not in allowed_record_keys:
            filtered_record_keys.append(view.record_key)
            continue

        views.append(view)

    return views, ignored_record_keys, filtered_record_keys


def _validate_replay_decision_filter(
    decision: RetainedAuditCompactionDecision | None,
    decision_category: str,
    hub_id: str,
) -> None:
    if decision_category not in RETAINED_AUDIT_REPLAY_DECISION_CATEGORY_FILTERS:
        raise ValueError(
            "decision_category must be one of "
            f"{', '.join(RETAINED_AUDIT_REPLAY_DECISION_CATEGORY_FILTERS)}"
        )
    if decision is None:
        if decision_category != "all":
            raise ValueError("decision is required for decision_category filtering")
        return
    if not isinstance(decision, RetainedAuditCompactionDecision):
        raise TypeError("decision must be a RetainedAuditCompactionDecision")
    if decision.hub_id != hub_id:
        raise ValueError("decision hub_id must match hub_id")


def _decision_record_key_filter(
    decision: RetainedAuditCompactionDecision | None,
    decision_category: str,
) -> set[str] | None:
    if decision is None or decision_category == "all":
        return None
    if decision_category == "retained":
        return set(decision.retained_record_keys)
    return set(decision.compaction_candidate_record_keys)


def _selected_retained_history(
    registry_hub: RegistryHub,
    history_type: str,
) -> list[object]:
    if history_type == "stream_offer_lifecycle_explanation":
        return registry_hub.stream_offer_lifecycle_explanation_history
    if history_type == "stream_offer_status_transition":
        return registry_hub.stream_offer_status_transition_history
    raise ValueError(f"unsupported retained audit history_type: {history_type}")


def _summary_history_type(
    views: list[_AuditRecordView],
    history_type: str | None,
) -> str:
    if history_type is not None:
        return history_type
    history_types = sorted({view.history_type for view in views})
    if len(history_types) == 1:
        return history_types[0]
    return "mixed"


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


def _ordered_unique(record_keys: tuple[str, ...]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for record_key in record_keys:
        if record_key in seen:
            continue
        seen.add(record_key)
        ordered.append(record_key)
    return ordered


def _compaction_apply_metadata(
    *,
    compacted_record_keys: list[str],
    history_type: str,
    selected_history_mutated: bool,
    unsupported_history_type: bool,
    metadata: dict[str, object] | None,
) -> dict[str, object]:
    result_metadata: dict[str, object] = {
        "simulator_local": True,
        "explicit_apply": True,
        "read_only": False,
        "compaction_apply_result_only": True,
        "registry_hub_mutated": selected_history_mutated,
        "retained_history_mutated": selected_history_mutated,
        "selected_history_type": history_type,
        "selected_history_mutated": selected_history_mutated,
        "records_compacted": bool(compacted_record_keys),
        "records_deleted": bool(compacted_record_keys),
        "records_rewritten": False,
        "unsupported_history_type": unsupported_history_type,
        "held_offers_mutated": False,
        "stream_offers_mutated": False,
        "lifecycle_plans_mutated": False,
        "lifecycle_apply_results_mutated": False,
        "polling_history_mutated": False,
        "admission_history_mutated": False,
        "encrypted_delivery_history_mutated": False,
        "alias_history_mutated": False,
        "authority_history_mutated": False,
        "delivery_state_mutated": False,
        "delivery_behavior_changed": False,
        "traffic_hub_state_changed": False,
        "traffic_hub_routing_changed": False,
        "snapshot_changed": False,
        "compact_snapshot_changed": False,
        "canonical_identity_rewritten": False,
        "automatic_cleanup": False,
        "cleanup_scheduled": False,
        "background_worker": False,
        "retry_loop": False,
        "durable_queue": False,
        "live_timer": False,
        "live_clock": False,
        "scenario_context_required": False,
        "networking": False,
        "dns_lookup": False,
        "external_services": False,
        "cryptography": False,
        "supported_history_types": list(SUPPORTED_RETAINED_AUDIT_HISTORY_TYPES),
    }
    if metadata is not None:
        result_metadata.update(metadata)
    return result_metadata


__all__ = [
    "RETAINED_AUDIT_REPLAY_DECISION_CATEGORY_FILTERS",
    "SUPPORTED_RETAINED_AUDIT_HISTORY_TYPES",
    "apply_retained_audit_compaction_decision",
    "classify_retained_audit_records_for_compaction",
    "make_retained_audit_compaction_policy",
    "summarize_retained_audit_compaction_apply_result",
    "summarize_retained_audit_compaction_decision",
    "summarize_retained_audit_replay",
    "summarize_retained_audit_replay_by_history_type",
    "summarize_retained_audit_replay_by_reason",
]
