"""Retained audit compaction policy, replay, and apply result models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

RETAINED_AUDIT_COMPACTION_DECISION_CATEGORIES: tuple[str, ...] = (
    "retained",
    "compaction_candidate",
    "ignored",
)

SUPPORTED_RETAINED_AUDIT_HISTORY_TYPES: tuple[str, ...] = (
    "stream_offer_lifecycle_explanation",
    "stream_offer_status_transition",
    "rendezvous_poll_result",
    "lane_admission_decision",
    "encrypted_delivery_result",
    "encryption_policy_decision",
    "message_delivery_result",
    "authority_outcome",
)


@dataclass(frozen=True, slots=True)
class RetainedAuditCompactionPolicy:
    """Symbolic policy for classifying retained simulator audit records."""

    policy_id: str
    hub_id: str
    history_types: tuple[str, ...] | list[str] = ()
    retain_reasons: tuple[str, ...] | list[str] = ()
    compact_reasons: tuple[str, ...] | list[str] = ()
    retain_statuses: tuple[str, ...] | list[str] = ()
    compact_statuses: tuple[str, ...] | list[str] = ()
    retain_sources: tuple[str, ...] | list[str] = ()
    compact_sources: tuple[str, ...] | list[str] = ()
    max_records: int | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _validate_required_string(self.policy_id, "policy_id")
        _validate_required_string(self.hub_id, "hub_id")
        object.__setattr__(
            self,
            "history_types",
            _string_tuple(self.history_types, "history_types"),
        )
        object.__setattr__(
            self,
            "retain_reasons",
            _string_tuple(self.retain_reasons, "retain_reasons"),
        )
        object.__setattr__(
            self,
            "compact_reasons",
            _string_tuple(self.compact_reasons, "compact_reasons"),
        )
        object.__setattr__(
            self,
            "retain_statuses",
            _string_tuple(self.retain_statuses, "retain_statuses"),
        )
        object.__setattr__(
            self,
            "compact_statuses",
            _string_tuple(self.compact_statuses, "compact_statuses"),
        )
        object.__setattr__(
            self,
            "retain_sources",
            _string_tuple(self.retain_sources, "retain_sources"),
        )
        object.__setattr__(
            self,
            "compact_sources",
            _string_tuple(self.compact_sources, "compact_sources"),
        )
        _validate_optional_order(self.max_records, "max_records")
        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata or {}))

    def to_summary(self) -> dict[str, object]:
        """Return deterministic, JSON-safe policy metadata."""
        return {
            "policy_id": self.policy_id,
            "hub_id": self.hub_id,
            "history_types": list(self.history_types),
            "retain_reasons": list(self.retain_reasons),
            "compact_reasons": list(self.compact_reasons),
            "retain_statuses": list(self.retain_statuses),
            "compact_statuses": list(self.compact_statuses),
            "retain_sources": list(self.retain_sources),
            "compact_sources": list(self.compact_sources),
            "max_records": self.max_records,
            "metadata": _json_safe_copy(self.metadata or {}),
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class RetainedAuditCompactionDecision:
    """Read-only classification of explicit retained audit records."""

    hub_id: str
    policy_id: str
    history_type: str
    retained_record_keys: tuple[str, ...] | list[str] = ()
    compaction_candidate_record_keys: tuple[str, ...] | list[str] = ()
    ignored_record_keys: tuple[str, ...] | list[str] = ()
    by_decision_category: dict[str, int] | None = None
    candidate_by_history_type: dict[str, int] | None = None
    candidate_by_reason: dict[str, int] | None = None
    candidate_by_status: dict[str, int] | None = None
    candidate_by_source: dict[str, int] | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _validate_required_string(self.hub_id, "hub_id")
        _validate_required_string(self.policy_id, "policy_id")
        _validate_required_string(self.history_type, "history_type")
        object.__setattr__(
            self,
            "retained_record_keys",
            _string_tuple(self.retained_record_keys, "retained_record_keys"),
        )
        object.__setattr__(
            self,
            "compaction_candidate_record_keys",
            _string_tuple(
                self.compaction_candidate_record_keys,
                "compaction_candidate_record_keys",
            ),
        )
        object.__setattr__(
            self,
            "ignored_record_keys",
            _string_tuple(self.ignored_record_keys, "ignored_record_keys"),
        )
        object.__setattr__(
            self,
            "by_decision_category",
            _decision_count_dict(
                self.by_decision_category or {},
                "by_decision_category",
            ),
        )
        object.__setattr__(
            self,
            "candidate_by_history_type",
            _count_dict(self.candidate_by_history_type or {}, "candidate_by_history_type"),
        )
        object.__setattr__(
            self,
            "candidate_by_reason",
            _count_dict(self.candidate_by_reason or {}, "candidate_by_reason"),
        )
        object.__setattr__(
            self,
            "candidate_by_status",
            _count_dict(self.candidate_by_status or {}, "candidate_by_status"),
        )
        object.__setattr__(
            self,
            "candidate_by_source",
            _count_dict(self.candidate_by_source or {}, "candidate_by_source"),
        )
        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata or {}))

    def to_summary(self) -> dict[str, object]:
        """Return deterministic, JSON-safe compaction classification metadata."""
        return {
            "hub_id": self.hub_id,
            "policy_id": self.policy_id,
            "history_type": self.history_type,
            "retained_record_keys": list(self.retained_record_keys),
            "compaction_candidate_record_keys": list(
                self.compaction_candidate_record_keys
            ),
            "ignored_record_keys": list(self.ignored_record_keys),
            "by_decision_category": dict(self.by_decision_category or {}),
            "candidate_by_history_type": dict(self.candidate_by_history_type or {}),
            "candidate_by_reason": dict(self.candidate_by_reason or {}),
            "candidate_by_status": dict(self.candidate_by_status or {}),
            "candidate_by_source": dict(self.candidate_by_source or {}),
            "metadata": _json_safe_copy(self.metadata or {}),
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class RetainedAuditReplaySummary:
    """Read-only grouped replay metadata for explicit retained audit records."""

    hub_id: str
    history_type: str
    record_count: int = 0
    record_keys: tuple[str, ...] | list[str] = ()
    by_status: dict[str, int] | None = None
    by_reason: dict[str, int] | None = None
    by_source: dict[str, int] | None = None
    by_offer_id: dict[str, int] | None = None
    first_record_key: str | None = None
    last_record_key: str | None = None
    metadata: dict[str, Any] | None = None
    by_request_id: dict[str, int] | None = None
    by_message_id: dict[str, int] | None = None
    by_mailbox_id: dict[str, int] | None = None
    by_policy_id: dict[str, int] | None = None
    by_lane_signature: dict[str, int] | None = None
    by_requested_alias: dict[str, int] | None = None
    by_granted_alias: dict[str, int] | None = None
    by_target_device: dict[str, int] | None = None
    by_path_hub: dict[str, int] | None = None

    def __post_init__(self) -> None:
        _validate_required_string(self.hub_id, "hub_id")
        _validate_required_string(self.history_type, "history_type")
        _validate_order(self.record_count, "record_count")
        object.__setattr__(
            self,
            "record_keys",
            _string_tuple(self.record_keys, "record_keys"),
        )
        object.__setattr__(
            self,
            "by_status",
            _count_dict(self.by_status or {}, "by_status"),
        )
        object.__setattr__(
            self,
            "by_reason",
            _count_dict(self.by_reason or {}, "by_reason"),
        )
        object.__setattr__(
            self,
            "by_source",
            _count_dict(self.by_source or {}, "by_source"),
        )
        object.__setattr__(
            self,
            "by_offer_id",
            _count_dict(self.by_offer_id or {}, "by_offer_id"),
        )
        object.__setattr__(
            self,
            "by_request_id",
            _count_dict(self.by_request_id or {}, "by_request_id"),
        )
        object.__setattr__(
            self,
            "by_message_id",
            _count_dict(self.by_message_id or {}, "by_message_id"),
        )
        object.__setattr__(
            self,
            "by_mailbox_id",
            _count_dict(self.by_mailbox_id or {}, "by_mailbox_id"),
        )
        object.__setattr__(
            self,
            "by_policy_id",
            _count_dict(self.by_policy_id or {}, "by_policy_id"),
        )
        object.__setattr__(
            self,
            "by_lane_signature",
            _count_dict(self.by_lane_signature or {}, "by_lane_signature"),
        )
        object.__setattr__(
            self,
            "by_requested_alias",
            _count_dict(self.by_requested_alias or {}, "by_requested_alias"),
        )
        object.__setattr__(
            self,
            "by_granted_alias",
            _count_dict(self.by_granted_alias or {}, "by_granted_alias"),
        )
        object.__setattr__(
            self,
            "by_target_device",
            _count_dict(self.by_target_device or {}, "by_target_device"),
        )
        object.__setattr__(
            self,
            "by_path_hub",
            _count_dict(self.by_path_hub or {}, "by_path_hub"),
        )
        _validate_optional_string(self.first_record_key, "first_record_key")
        _validate_optional_string(self.last_record_key, "last_record_key")
        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata or {}))

    def to_summary(self) -> dict[str, object]:
        """Return deterministic, JSON-safe replay summary metadata."""
        return {
            "hub_id": self.hub_id,
            "history_type": self.history_type,
            "record_count": self.record_count,
            "record_keys": list(self.record_keys),
            "by_status": dict(self.by_status or {}),
            "by_reason": dict(self.by_reason or {}),
            "by_source": dict(self.by_source or {}),
            "by_offer_id": dict(self.by_offer_id or {}),
            "by_request_id": dict(self.by_request_id or {}),
            "by_message_id": dict(self.by_message_id or {}),
            "by_mailbox_id": dict(self.by_mailbox_id or {}),
            "by_policy_id": dict(self.by_policy_id or {}),
            "by_lane_signature": dict(self.by_lane_signature or {}),
            "first_record_key": self.first_record_key,
            "last_record_key": self.last_record_key,
            "metadata": _json_safe_copy(self.metadata or {}),
            "by_requested_alias": dict(self.by_requested_alias or {}),
            "by_granted_alias": dict(self.by_granted_alias or {}),
            "by_target_device": dict(self.by_target_device or {}),
            "by_path_hub": dict(self.by_path_hub or {}),
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class RetainedAuditCompactionApplyResult:
    """Result for explicitly applying a retained audit compaction decision."""

    hub_id: str
    policy_id: str
    history_type: str
    compacted_record_keys: tuple[str, ...] | list[str] = ()
    retained_record_keys: tuple[str, ...] | list[str] = ()
    ignored_record_keys: tuple[str, ...] | list[str] = ()
    missing_record_keys: tuple[str, ...] | list[str] = ()
    unsupported_record_keys: tuple[str, ...] | list[str] = ()
    compacted_count: int = 0
    retained_count: int = 0
    ignored_count: int = 0
    missing_count: int = 0
    unsupported_count: int = 0
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _validate_required_string(self.hub_id, "hub_id")
        _validate_required_string(self.policy_id, "policy_id")
        _validate_required_string(self.history_type, "history_type")
        object.__setattr__(
            self,
            "compacted_record_keys",
            _string_tuple(self.compacted_record_keys, "compacted_record_keys"),
        )
        object.__setattr__(
            self,
            "retained_record_keys",
            _string_tuple(self.retained_record_keys, "retained_record_keys"),
        )
        object.__setattr__(
            self,
            "ignored_record_keys",
            _string_tuple(self.ignored_record_keys, "ignored_record_keys"),
        )
        object.__setattr__(
            self,
            "missing_record_keys",
            _string_tuple(self.missing_record_keys, "missing_record_keys"),
        )
        object.__setattr__(
            self,
            "unsupported_record_keys",
            _string_tuple(self.unsupported_record_keys, "unsupported_record_keys"),
        )
        _validate_order(self.compacted_count, "compacted_count")
        _validate_order(self.retained_count, "retained_count")
        _validate_order(self.ignored_count, "ignored_count")
        _validate_order(self.missing_count, "missing_count")
        _validate_order(self.unsupported_count, "unsupported_count")
        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata or {}))

    def to_summary(self) -> dict[str, object]:
        """Return deterministic, JSON-safe compaction apply result metadata."""
        return {
            "hub_id": self.hub_id,
            "policy_id": self.policy_id,
            "history_type": self.history_type,
            "compacted_record_keys": list(self.compacted_record_keys),
            "retained_record_keys": list(self.retained_record_keys),
            "ignored_record_keys": list(self.ignored_record_keys),
            "missing_record_keys": list(self.missing_record_keys),
            "unsupported_record_keys": list(self.unsupported_record_keys),
            "compacted_count": self.compacted_count,
            "retained_count": self.retained_count,
            "ignored_count": self.ignored_count,
            "missing_count": self.missing_count,
            "unsupported_count": self.unsupported_count,
            "metadata": _json_safe_copy(self.metadata or {}),
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class RetainedAuditCompactionPreviewResult:
    """Read-only result for previewing one retained audit compaction decision."""

    hub_id: str
    policy_id: str
    history_type: str
    would_compact_record_keys: tuple[str, ...] | list[str] = ()
    retained_record_keys: tuple[str, ...] | list[str] = ()
    ignored_record_keys: tuple[str, ...] | list[str] = ()
    missing_record_keys: tuple[str, ...] | list[str] = ()
    unsupported_record_keys: tuple[str, ...] | list[str] = ()
    would_compact_count: int = 0
    retained_count: int = 0
    ignored_count: int = 0
    missing_count: int = 0
    unsupported_count: int = 0
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _validate_required_string(self.hub_id, "hub_id")
        _validate_required_string(self.policy_id, "policy_id")
        _validate_required_string(self.history_type, "history_type")
        object.__setattr__(
            self,
            "would_compact_record_keys",
            _string_tuple(
                self.would_compact_record_keys,
                "would_compact_record_keys",
            ),
        )
        object.__setattr__(
            self,
            "retained_record_keys",
            _string_tuple(self.retained_record_keys, "retained_record_keys"),
        )
        object.__setattr__(
            self,
            "ignored_record_keys",
            _string_tuple(self.ignored_record_keys, "ignored_record_keys"),
        )
        object.__setattr__(
            self,
            "missing_record_keys",
            _string_tuple(self.missing_record_keys, "missing_record_keys"),
        )
        object.__setattr__(
            self,
            "unsupported_record_keys",
            _string_tuple(self.unsupported_record_keys, "unsupported_record_keys"),
        )
        _validate_order(self.would_compact_count, "would_compact_count")
        _validate_order(self.retained_count, "retained_count")
        _validate_order(self.ignored_count, "ignored_count")
        _validate_order(self.missing_count, "missing_count")
        _validate_order(self.unsupported_count, "unsupported_count")
        if self.metadata is not None and not isinstance(self.metadata, dict):
            raise TypeError("metadata must be a JSON-safe dict")
        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata or {}))

    def to_summary(self) -> dict[str, object]:
        """Return deterministic, JSON-safe compaction preview metadata."""
        return {
            "hub_id": self.hub_id,
            "policy_id": self.policy_id,
            "history_type": self.history_type,
            "would_compact_record_keys": list(self.would_compact_record_keys),
            "retained_record_keys": list(self.retained_record_keys),
            "ignored_record_keys": list(self.ignored_record_keys),
            "missing_record_keys": list(self.missing_record_keys),
            "unsupported_record_keys": list(self.unsupported_record_keys),
            "would_compact_count": self.would_compact_count,
            "retained_count": self.retained_count,
            "ignored_count": self.ignored_count,
            "missing_count": self.missing_count,
            "unsupported_count": self.unsupported_count,
            "metadata": _json_safe_copy(self.metadata or {}),
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class RetainedAuditCompactionBatchPreviewResult:
    """Aggregate read-only preview for a canonical multi-history batch."""

    hub_id: str
    batch_id: str
    preview_results: (
        tuple[RetainedAuditCompactionPreviewResult, ...]
        | list[RetainedAuditCompactionPreviewResult]
    ) = ()
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _validate_required_string(self.hub_id, "hub_id")
        _validate_required_string(self.batch_id, "batch_id")
        if not isinstance(self.preview_results, tuple | list):
            raise TypeError("preview_results must be a list or tuple")
        if len(self.preview_results) < 2:
            raise ValueError("preview_results must contain at least two results")

        results: list[RetainedAuditCompactionPreviewResult] = []
        seen_history_types: set[str] = set()
        for result in self.preview_results:
            if not isinstance(result, RetainedAuditCompactionPreviewResult):
                raise TypeError(
                    "preview_results must contain "
                    "RetainedAuditCompactionPreviewResult values"
                )
            if result.hub_id != self.hub_id:
                raise ValueError("preview result hub_id must match batch hub_id")
            if result.history_type not in SUPPORTED_RETAINED_AUDIT_HISTORY_TYPES:
                raise ValueError(
                    "preview result history_type must be a supported retained audit "
                    "history"
                )
            if result.history_type in seen_history_types:
                raise ValueError("preview result history_types must be distinct")
            seen_history_types.add(result.history_type)
            results.append(result)

        history_order = {
            history_type: index
            for index, history_type in enumerate(SUPPORTED_RETAINED_AUDIT_HISTORY_TYPES)
        }
        results.sort(key=lambda result: history_order[result.history_type])
        object.__setattr__(self, "preview_results", tuple(results))
        if self.metadata is not None and not isinstance(self.metadata, dict):
            raise TypeError("metadata must be a JSON-safe dict")
        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata or {}))

    @property
    def history_types(self) -> tuple[str, ...]:
        """Return the canonical history order represented by this preview."""
        return tuple(result.history_type for result in self.preview_results)

    @property
    def would_compact_count(self) -> int:
        return sum(result.would_compact_count for result in self.preview_results)

    @property
    def retained_count(self) -> int:
        return sum(result.retained_count for result in self.preview_results)

    @property
    def ignored_count(self) -> int:
        return sum(result.ignored_count for result in self.preview_results)

    @property
    def missing_count(self) -> int:
        return sum(result.missing_count for result in self.preview_results)

    @property
    def unsupported_count(self) -> int:
        return sum(result.unsupported_count for result in self.preview_results)

    def to_summary(self) -> dict[str, object]:
        """Return deterministic aggregate and per-history preview metadata."""
        return {
            "hub_id": self.hub_id,
            "batch_id": self.batch_id,
            "history_types": list(self.history_types),
            "preview_results": [
                result.to_summary() for result in self.preview_results
            ],
            "would_compact_count": self.would_compact_count,
            "retained_count": self.retained_count,
            "ignored_count": self.ignored_count,
            "missing_count": self.missing_count,
            "unsupported_count": self.unsupported_count,
            "metadata": _json_safe_copy(self.metadata or {}),
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class RetainedAuditCompactionBatchApplyResult:
    """Aggregate result for a canonical multi-history compaction batch."""

    hub_id: str
    batch_id: str
    apply_results: (
        tuple[RetainedAuditCompactionApplyResult, ...]
        | list[RetainedAuditCompactionApplyResult]
    ) = ()
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _validate_required_string(self.hub_id, "hub_id")
        _validate_required_string(self.batch_id, "batch_id")
        if not isinstance(self.apply_results, tuple | list):
            raise TypeError("apply_results must be a list or tuple")
        if len(self.apply_results) < 2:
            raise ValueError("apply_results must contain at least two results")

        results: list[RetainedAuditCompactionApplyResult] = []
        seen_history_types: set[str] = set()
        for result in self.apply_results:
            if not isinstance(result, RetainedAuditCompactionApplyResult):
                raise TypeError(
                    "apply_results must contain RetainedAuditCompactionApplyResult values"
                )
            if result.hub_id != self.hub_id:
                raise ValueError("apply result hub_id must match batch hub_id")
            if result.history_type not in SUPPORTED_RETAINED_AUDIT_HISTORY_TYPES:
                raise ValueError(
                    "apply result history_type must be a supported retained audit history"
                )
            if result.history_type in seen_history_types:
                raise ValueError("apply result history_types must be distinct")
            seen_history_types.add(result.history_type)
            results.append(result)

        history_order = {
            history_type: index
            for index, history_type in enumerate(SUPPORTED_RETAINED_AUDIT_HISTORY_TYPES)
        }
        results.sort(key=lambda result: history_order[result.history_type])
        object.__setattr__(self, "apply_results", tuple(results))
        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata or {}))

    @property
    def history_types(self) -> tuple[str, ...]:
        """Return the canonical history order represented by this batch."""
        return tuple(result.history_type for result in self.apply_results)

    @property
    def compacted_count(self) -> int:
        return sum(result.compacted_count for result in self.apply_results)

    @property
    def retained_count(self) -> int:
        return sum(result.retained_count for result in self.apply_results)

    @property
    def ignored_count(self) -> int:
        return sum(result.ignored_count for result in self.apply_results)

    @property
    def missing_count(self) -> int:
        return sum(result.missing_count for result in self.apply_results)

    @property
    def unsupported_count(self) -> int:
        return sum(result.unsupported_count for result in self.apply_results)

    def to_summary(self) -> dict[str, object]:
        """Return deterministic aggregate and per-history batch metadata."""
        return {
            "hub_id": self.hub_id,
            "batch_id": self.batch_id,
            "history_types": list(self.history_types),
            "apply_results": [
                result.to_summary() for result in self.apply_results
            ],
            "compacted_count": self.compacted_count,
            "retained_count": self.retained_count,
            "ignored_count": self.ignored_count,
            "missing_count": self.missing_count,
            "unsupported_count": self.unsupported_count,
            "metadata": _json_safe_copy(self.metadata or {}),
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


def make_retained_audit_compaction_policy(
    *,
    policy_id: str,
    hub_id: str,
    history_types: list[str] | None = None,
    retain_reasons: list[str] | None = None,
    compact_reasons: list[str] | None = None,
    retain_statuses: list[str] | None = None,
    compact_statuses: list[str] | None = None,
    retain_sources: list[str] | None = None,
    compact_sources: list[str] | None = None,
    max_records: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> RetainedAuditCompactionPolicy:
    """Return a pure simulator-local retained audit compaction policy."""
    policy_metadata: dict[str, object] = {
        "simulator_local": True,
        "read_only": True,
        "compaction_policy_only": True,
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
    }
    if metadata is not None:
        safe_metadata = _json_safe_copy(metadata)
        if not isinstance(safe_metadata, dict):
            raise TypeError("metadata must be a JSON-safe dict")
        policy_metadata.update(safe_metadata)

    return RetainedAuditCompactionPolicy(
        policy_id=policy_id,
        hub_id=hub_id,
        history_types=history_types or [],
        retain_reasons=retain_reasons or [],
        compact_reasons=compact_reasons or [],
        retain_statuses=retain_statuses or [],
        compact_statuses=compact_statuses or [],
        retain_sources=retain_sources or [],
        compact_sources=compact_sources or [],
        max_records=max_records,
        metadata=policy_metadata,
    )


def _validate_required_string(value: str, field_name: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} is required")
    if value.strip() != value or any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")


def _validate_optional_string(value: str | None, field_name: str) -> None:
    if value is None:
        return
    _validate_required_string(value, field_name)


def _validate_order(value: int, field_name: str) -> None:
    if not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be greater than or equal to 0")


def _validate_optional_order(value: int | None, field_name: str) -> None:
    if value is None:
        return
    _validate_order(value, field_name)


def _string_tuple(values: tuple[str, ...] | list[str], field_name: str) -> tuple[str, ...]:
    if not isinstance(values, tuple | list):
        raise TypeError(f"{field_name} must be a list or tuple")
    for value in values:
        _validate_required_string(value, field_name)
    return tuple(values)


def _count_dict(values: dict[str, int], field_name: str) -> dict[str, int]:
    if not isinstance(values, dict):
        raise TypeError(f"{field_name} must be a dict")
    copied: dict[str, int] = {}
    for key, count in values.items():
        _validate_required_string(key, field_name)
        _validate_order(count, field_name)
        copied[key] = count
    return {key: copied[key] for key in sorted(copied)}


def _decision_count_dict(values: dict[str, int], field_name: str) -> dict[str, int]:
    if not isinstance(values, dict):
        raise TypeError(f"{field_name} must be a dict")
    copied: dict[str, int] = {}
    for key, count in values.items():
        _validate_required_string(key, field_name)
        if key not in RETAINED_AUDIT_COMPACTION_DECISION_CATEGORIES:
            raise ValueError(
                f"{field_name} keys must be one of "
                f"{', '.join(RETAINED_AUDIT_COMPACTION_DECISION_CATEGORIES)}"
            )
        _validate_order(count, field_name)
        copied[key] = count
    return {key: copied[key] for key in sorted(copied)}


def _json_safe_copy(value: Any) -> object:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, tuple | list):
        return [_json_safe_copy(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe_copy(item) for key, item in value.items()}
    raise TypeError("retained audit data must be JSON-safe simulator data")
