"""Simulator-local stream offer and rendezvous request models for v1.2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from darwin.models.lane_signature import (
    LANE_VISIBILITY_TIERS,
    LaneSignature,
    LaneVisibilityTier,
    parse_lane_signature,
)

STREAM_OFFER_MODES: tuple[str, ...] = (
    "message",
    "stream",
    "poll",
    "control",
)

STREAM_OFFER_STATUSES: tuple[str, ...] = (
    "created",
    "held",
    "discoverable",
    "passed_down",
    "accepted",
    "denied",
    "expired",
    "rate_limited",
    "quarantined",
)

STREAM_OFFER_ACTIVE_STATUSES: tuple[str, ...] = (
    "created",
    "held",
    "discoverable",
    "passed_down",
)

STREAM_OFFER_TERMINAL_STATUSES: tuple[str, ...] = (
    "accepted",
    "denied",
    "expired",
    "rate_limited",
    "quarantined",
)

STREAM_OFFER_STATUS_TRANSITION_REASONS: tuple[str, ...] = (
    "status_updated",
    "expired",
    "manual_hold",
    "manual_deny",
    "manual_quarantine",
)

STREAM_OFFER_LIFECYCLE_EXPLANATION_CATEGORIES: tuple[str, ...] = (
    "expired",
    "active",
    "applied",
    "skipped",
    "missing",
    "terminal",
)

STREAM_OFFER_LIFECYCLE_EXPLANATION_REASONS: tuple[str, ...] = (
    "expired_by_plan",
    "active_by_plan",
    "terminal_cleanup_candidate",
    "ignored_by_plan",
    "applied_by_result",
    "skipped_by_result",
    "missing_by_result",
)

STREAM_OFFER_LIFECYCLE_RETENTION_DECISION_CATEGORIES: tuple[str, ...] = (
    "kept",
    "prune_candidate",
    "ignored",
)

RENDEZVOUS_POLL_STATUSES: tuple[str, ...] = (
    "matched",
    "empty",
    "invalid_request",
)

RENDEZVOUS_POLL_REASONS: tuple[str, ...] = (
    "offers_available",
    "no_discoverable_offers",
    "invalid_request",
    "hub_missing",
    "scope_mismatch",
)

LANE_ADMISSION_STATUSES: tuple[str, ...] = (
    "pass_down",
    "hold",
    "deny",
    "rate_limited",
    "quarantined",
    "requires_poll",
)

LANE_ADMISSION_REASONS: tuple[str, ...] = (
    "accepted",
    "default_hold",
    "explicit_lane_denied",
    "explicit_requester_denied",
    "explicit_scope_denied",
    "lane_not_allowed",
    "requester_not_allowed",
    "scope_not_allowed",
    "visibility_tier_exceeded",
    "not_discoverable",
    "rate_limited",
    "quarantined",
    "invalid_offer",
    "invalid_policy",
)

LANE_ADMISSION_BLOCKED_STATUSES: tuple[str, ...] = (
    "deny",
    "rate_limited",
    "quarantined",
)

LANE_ADMISSION_TERMINAL_STATUSES: tuple[str, ...] = (
    "pass_down",
    "deny",
    "rate_limited",
    "quarantined",
)


@dataclass(frozen=True, slots=True)
class StreamOfferMode:
    """Controlled simulator-local stream offer request mode."""

    mode: str = "message"

    def __post_init__(self) -> None:
        _validate_mode(self.mode)

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe mode summary."""
        return {"mode": self.mode}

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class StreamOfferStatus:
    """Controlled simulator-local stream offer lifecycle status."""

    status: str = "created"

    def __post_init__(self) -> None:
        _validate_status(self.status)

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe status summary."""
        return {"status": self.status}

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class StreamOfferStatusTransitionReason:
    """Controlled reason for simulator-local stream offer status transitions."""

    reason: str = "status_updated"

    def __post_init__(self) -> None:
        _validate_status_transition_reason(self.reason)

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe reason summary."""
        return {"reason": self.reason}

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class RendezvousPollStatus:
    """Controlled simulator-local rendezvous poll result status."""

    status: str = "empty"

    def __post_init__(self) -> None:
        _validate_poll_status(self.status)

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe status summary."""
        return {"status": self.status}

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class LaneAdmissionStatus:
    """Controlled simulator-local lane admission decision status."""

    status: str = "hold"

    def __post_init__(self) -> None:
        _validate_lane_admission_status(self.status)

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe status summary."""
        return {"status": self.status}

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class LaneAdmissionReason:
    """Controlled simulator-local lane admission decision reason."""

    reason: str = "default_hold"

    def __post_init__(self) -> None:
        _validate_lane_admission_reason(self.reason)

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe reason summary."""
        return {"reason": self.reason}

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class StreamOfferVisibility:
    """Discovery visibility tier for a simulator-local stream offer."""

    tier: int = 0

    def __post_init__(self) -> None:
        if self.tier not in LANE_VISIBILITY_TIERS:
            raise ValueError("visibility tier must be an integer from 0 through 5")

    @property
    def label(self) -> str:
        """Return the stable label for this stream offer visibility tier."""
        return LANE_VISIBILITY_TIERS[self.tier]

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe visibility summary."""
        return {"tier": self.tier, "label": self.label}

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class StreamOffer:
    """Simulator-local request to establish or deliver over a lane later."""

    offer_id: str
    requester_id: str
    target_handle: str
    lane_signature: LaneSignature | str
    requested_mode: StreamOfferMode | str = "message"
    visibility_tier: StreamOfferVisibility | LaneVisibilityTier | int = 0
    status: StreamOfferStatus | str = "created"
    rendezvous_scope: str | None = None
    created_order: int = 0
    expires_order: int | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _validate_required_string(self.offer_id, "offer_id")
        _validate_required_string(self.requester_id, "requester_id")
        _validate_required_string(self.target_handle, "target_handle")

        lane_signature = self.lane_signature
        if isinstance(lane_signature, LaneSignature):
            lane_signature = lane_signature.signature
        elif isinstance(lane_signature, str):
            lane_signature = parse_lane_signature(lane_signature).signature
        else:
            raise TypeError("lane_signature must be a LaneSignature or string")
        object.__setattr__(self, "lane_signature", lane_signature)

        requested_mode = self.requested_mode
        if isinstance(requested_mode, str):
            requested_mode = StreamOfferMode(requested_mode)
        if not isinstance(requested_mode, StreamOfferMode):
            raise TypeError("requested_mode must be a StreamOfferMode or string")
        object.__setattr__(self, "requested_mode", requested_mode)

        visibility_tier = self.visibility_tier
        if isinstance(visibility_tier, LaneVisibilityTier):
            visibility_tier = visibility_tier.tier
        if isinstance(visibility_tier, int):
            visibility_tier = StreamOfferVisibility(visibility_tier)
        if not isinstance(visibility_tier, StreamOfferVisibility):
            raise TypeError(
                "visibility_tier must be a StreamOfferVisibility, "
                "LaneVisibilityTier, or integer"
            )
        object.__setattr__(self, "visibility_tier", visibility_tier)

        status = self.status
        if isinstance(status, str):
            status = StreamOfferStatus(status)
        if not isinstance(status, StreamOfferStatus):
            raise TypeError("status must be a StreamOfferStatus or string")
        object.__setattr__(self, "status", status)

        _validate_optional_string(self.rendezvous_scope, "rendezvous_scope")
        _validate_order(self.created_order, "created_order")
        _validate_optional_order(self.expires_order, "expires_order")
        if self.expires_order is not None and self.expires_order < self.created_order:
            raise ValueError("expires_order must be greater than or equal to created_order")

        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata or {}))

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe stream offer summary."""
        return {
            "offer_id": self.offer_id,
            "requester_id": self.requester_id,
            "target_handle": self.target_handle,
            "lane_signature": self.lane_signature,
            "requested_mode": self.requested_mode.mode,
            "visibility_tier": self.visibility_tier.tier,
            "status": self.status.status,
            "rendezvous_scope": self.rendezvous_scope,
            "created_order": self.created_order,
            "expires_order": self.expires_order,
            "metadata": _json_safe_copy(self.metadata or {}),
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class StreamOfferStatusTransition:
    """RegistryHub-local symbolic stream offer lifecycle transition metadata."""

    offer_id: str
    previous_status: StreamOfferStatus | str
    new_status: StreamOfferStatus | str
    reason: StreamOfferStatusTransitionReason | str
    hub_id: str
    actor_id: str | None = None
    request_id: str | None = None
    metadata: dict[str, Any] | None = None
    sequence: int | None = None

    def __post_init__(self) -> None:
        _validate_required_string(self.offer_id, "offer_id")
        _validate_required_string(self.hub_id, "hub_id")
        _validate_optional_string(self.actor_id, "actor_id")
        _validate_optional_string(self.request_id, "request_id")
        _validate_optional_order(self.sequence, "sequence")

        previous_status = self.previous_status
        if isinstance(previous_status, str):
            previous_status = StreamOfferStatus(previous_status)
        if not isinstance(previous_status, StreamOfferStatus):
            raise TypeError("previous_status must be a StreamOfferStatus or string")
        object.__setattr__(self, "previous_status", previous_status)

        new_status = self.new_status
        if isinstance(new_status, str):
            new_status = StreamOfferStatus(new_status)
        if not isinstance(new_status, StreamOfferStatus):
            raise TypeError("new_status must be a StreamOfferStatus or string")
        object.__setattr__(self, "new_status", new_status)

        reason = self.reason
        if isinstance(reason, str):
            reason = StreamOfferStatusTransitionReason(reason)
        if not isinstance(reason, StreamOfferStatusTransitionReason):
            raise TypeError(
                "reason must be a StreamOfferStatusTransitionReason or string"
            )
        object.__setattr__(self, "reason", reason)
        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata or {}))

    def to_summary(self) -> dict[str, object]:
        """Return deterministic, JSON-safe transition metadata."""
        return {
            "offer_id": self.offer_id,
            "previous_status": self.previous_status.status,
            "new_status": self.new_status.status,
            "reason": self.reason.reason,
            "hub_id": self.hub_id,
            "actor_id": self.actor_id,
            "request_id": self.request_id,
            "metadata": _json_safe_copy(self.metadata or {}),
            "sequence": self.sequence,
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class StreamOfferLifecyclePlan:
    """RegistryHub-local read-only stream offer lifecycle planning metadata."""

    hub_id: str
    checked_at: int
    expired_offer_ids: tuple[str, ...] | list[str] = ()
    cleanup_candidate_offer_ids: tuple[str, ...] | list[str] = ()
    active_offer_ids: tuple[str, ...] | list[str] = ()
    ignored_offer_ids: tuple[str, ...] | list[str] = ()
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _validate_required_string(self.hub_id, "hub_id")
        _validate_order(self.checked_at, "checked_at")
        object.__setattr__(
            self,
            "expired_offer_ids",
            _string_tuple(self.expired_offer_ids, "expired_offer_ids"),
        )
        object.__setattr__(
            self,
            "cleanup_candidate_offer_ids",
            _string_tuple(
                self.cleanup_candidate_offer_ids,
                "cleanup_candidate_offer_ids",
            ),
        )
        object.__setattr__(
            self,
            "active_offer_ids",
            _string_tuple(self.active_offer_ids, "active_offer_ids"),
        )
        object.__setattr__(
            self,
            "ignored_offer_ids",
            _string_tuple(self.ignored_offer_ids, "ignored_offer_ids"),
        )
        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata or {}))

    def to_summary(self) -> dict[str, object]:
        """Return deterministic, JSON-safe lifecycle planning metadata."""
        return {
            "hub_id": self.hub_id,
            "checked_at": self.checked_at,
            "expired_offer_ids": list(self.expired_offer_ids),
            "cleanup_candidate_offer_ids": list(self.cleanup_candidate_offer_ids),
            "active_offer_ids": list(self.active_offer_ids),
            "ignored_offer_ids": list(self.ignored_offer_ids),
            "metadata": _json_safe_copy(self.metadata or {}),
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class StreamOfferLifecycleApplyResult:
    """RegistryHub-local result for explicitly applying a lifecycle plan."""

    hub_id: str
    plan_checked_at: int
    applied_offer_ids: tuple[str, ...] | list[str] = ()
    skipped_offer_ids: tuple[str, ...] | list[str] = ()
    missing_offer_ids: tuple[str, ...] | list[str] = ()
    recorded_transition_count: int = 0
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _validate_required_string(self.hub_id, "hub_id")
        _validate_order(self.plan_checked_at, "plan_checked_at")
        object.__setattr__(
            self,
            "applied_offer_ids",
            _string_tuple(self.applied_offer_ids, "applied_offer_ids"),
        )
        object.__setattr__(
            self,
            "skipped_offer_ids",
            _string_tuple(self.skipped_offer_ids, "skipped_offer_ids"),
        )
        object.__setattr__(
            self,
            "missing_offer_ids",
            _string_tuple(self.missing_offer_ids, "missing_offer_ids"),
        )
        _validate_order(self.recorded_transition_count, "recorded_transition_count")
        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata or {}))

    def to_summary(self) -> dict[str, object]:
        """Return deterministic, JSON-safe lifecycle apply result metadata."""
        return {
            "hub_id": self.hub_id,
            "plan_checked_at": self.plan_checked_at,
            "applied_offer_ids": list(self.applied_offer_ids),
            "skipped_offer_ids": list(self.skipped_offer_ids),
            "missing_offer_ids": list(self.missing_offer_ids),
            "recorded_transition_count": self.recorded_transition_count,
            "metadata": _json_safe_copy(self.metadata or {}),
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class StreamOfferLifecycleExplanation:
    """Read-only simulator-local explanation for a lifecycle plan or result."""

    hub_id: str
    offer_id: str
    category: str
    reason: str
    status: str
    checked_at: int | None = None
    source: str | None = None
    details: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _validate_required_string(self.hub_id, "hub_id")
        _validate_required_string(self.offer_id, "offer_id")
        _validate_lifecycle_explanation_category(self.category)
        _validate_lifecycle_explanation_reason(self.reason)
        _validate_required_string(self.status, "status")
        _validate_optional_order(self.checked_at, "checked_at")
        _validate_optional_string(self.source, "source")
        object.__setattr__(self, "details", _json_safe_copy(self.details or {}))

    def to_summary(self) -> dict[str, object]:
        """Return deterministic, JSON-safe lifecycle explanation metadata."""
        return {
            "hub_id": self.hub_id,
            "offer_id": self.offer_id,
            "category": self.category,
            "reason": self.reason,
            "status": self.status,
            "checked_at": self.checked_at,
            "source": self.source,
            "details": _json_safe_copy(self.details or {}),
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class StreamOfferLifecycleExplanationRetentionPolicy:
    """Read-only policy metadata for classifying lifecycle explanations."""

    policy_id: str
    hub_id: str
    retain_categories: tuple[str, ...] | list[str] = ()
    retain_reasons: tuple[str, ...] | list[str] = ()
    prune_categories: tuple[str, ...] | list[str] = ()
    prune_reasons: tuple[str, ...] | list[str] = ()
    retain_sources: tuple[str, ...] | list[str] = ()
    prune_sources: tuple[str, ...] | list[str] = ()
    max_records: int | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _validate_required_string(self.policy_id, "policy_id")
        _validate_required_string(self.hub_id, "hub_id")
        object.__setattr__(
            self,
            "retain_categories",
            _lifecycle_explanation_category_tuple(
                self.retain_categories,
                "retain_categories",
            ),
        )
        object.__setattr__(
            self,
            "retain_reasons",
            _lifecycle_explanation_reason_tuple(
                self.retain_reasons,
                "retain_reasons",
            ),
        )
        object.__setattr__(
            self,
            "prune_categories",
            _lifecycle_explanation_category_tuple(
                self.prune_categories,
                "prune_categories",
            ),
        )
        object.__setattr__(
            self,
            "prune_reasons",
            _lifecycle_explanation_reason_tuple(
                self.prune_reasons,
                "prune_reasons",
            ),
        )
        object.__setattr__(
            self,
            "retain_sources",
            _string_tuple(self.retain_sources, "retain_sources"),
        )
        object.__setattr__(
            self,
            "prune_sources",
            _string_tuple(self.prune_sources, "prune_sources"),
        )
        _validate_optional_order(self.max_records, "max_records")
        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata or {}))

    def to_summary(self) -> dict[str, object]:
        """Return deterministic, JSON-safe retention policy metadata."""
        return {
            "policy_id": self.policy_id,
            "hub_id": self.hub_id,
            "retain_categories": list(self.retain_categories),
            "retain_reasons": list(self.retain_reasons),
            "prune_categories": list(self.prune_categories),
            "prune_reasons": list(self.prune_reasons),
            "retain_sources": list(self.retain_sources),
            "prune_sources": list(self.prune_sources),
            "max_records": self.max_records,
            "metadata": _json_safe_copy(self.metadata or {}),
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class StreamOfferLifecycleExplanationRetentionDecision:
    """Read-only classification result for lifecycle explanation retention."""

    hub_id: str
    policy_id: str
    kept_explanation_keys: tuple[str, ...] | list[str] = ()
    prune_candidate_explanation_keys: tuple[str, ...] | list[str] = ()
    ignored_explanation_keys: tuple[str, ...] | list[str] = ()
    by_decision_category: dict[str, int] | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _validate_required_string(self.hub_id, "hub_id")
        _validate_required_string(self.policy_id, "policy_id")
        object.__setattr__(
            self,
            "kept_explanation_keys",
            _string_tuple(self.kept_explanation_keys, "kept_explanation_keys"),
        )
        object.__setattr__(
            self,
            "prune_candidate_explanation_keys",
            _string_tuple(
                self.prune_candidate_explanation_keys,
                "prune_candidate_explanation_keys",
            ),
        )
        object.__setattr__(
            self,
            "ignored_explanation_keys",
            _string_tuple(self.ignored_explanation_keys, "ignored_explanation_keys"),
        )
        object.__setattr__(
            self,
            "by_decision_category",
            _retention_decision_count_dict(
                self.by_decision_category or {},
                "by_decision_category",
            ),
        )
        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata or {}))

    def to_summary(self) -> dict[str, object]:
        """Return deterministic, JSON-safe retention classification metadata."""
        return {
            "hub_id": self.hub_id,
            "policy_id": self.policy_id,
            "kept_explanation_keys": list(self.kept_explanation_keys),
            "prune_candidate_explanation_keys": list(
                self.prune_candidate_explanation_keys
            ),
            "ignored_explanation_keys": list(self.ignored_explanation_keys),
            "by_decision_category": dict(self.by_decision_category or {}),
            "metadata": _json_safe_copy(self.metadata or {}),
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class StreamOfferLifecycleExplanationPruningPlan:
    """Read-only pruning candidate plan for lifecycle explanations."""

    hub_id: str
    policy_id: str
    candidate_explanation_keys: tuple[str, ...] | list[str] = ()
    retained_explanation_keys: tuple[str, ...] | list[str] = ()
    ignored_explanation_keys: tuple[str, ...] | list[str] = ()
    candidate_count: int = 0
    retained_count: int = 0
    ignored_count: int = 0
    by_decision_category: dict[str, int] | None = None
    candidate_by_category: dict[str, int] | None = None
    candidate_by_reason: dict[str, int] | None = None
    candidate_by_source: dict[str, int] | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _validate_required_string(self.hub_id, "hub_id")
        _validate_required_string(self.policy_id, "policy_id")
        object.__setattr__(
            self,
            "candidate_explanation_keys",
            _string_tuple(self.candidate_explanation_keys, "candidate_explanation_keys"),
        )
        object.__setattr__(
            self,
            "retained_explanation_keys",
            _string_tuple(self.retained_explanation_keys, "retained_explanation_keys"),
        )
        object.__setattr__(
            self,
            "ignored_explanation_keys",
            _string_tuple(self.ignored_explanation_keys, "ignored_explanation_keys"),
        )
        _validate_order(self.candidate_count, "candidate_count")
        _validate_order(self.retained_count, "retained_count")
        _validate_order(self.ignored_count, "ignored_count")
        object.__setattr__(
            self,
            "by_decision_category",
            _retention_decision_count_dict(
                self.by_decision_category or {},
                "by_decision_category",
            ),
        )
        object.__setattr__(
            self,
            "candidate_by_category",
            _count_dict(self.candidate_by_category or {}, "candidate_by_category"),
        )
        object.__setattr__(
            self,
            "candidate_by_reason",
            _count_dict(self.candidate_by_reason or {}, "candidate_by_reason"),
        )
        object.__setattr__(
            self,
            "candidate_by_source",
            _count_dict(self.candidate_by_source or {}, "candidate_by_source"),
        )
        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata or {}))

    def to_summary(self) -> dict[str, object]:
        """Return deterministic, JSON-safe pruning plan metadata."""
        return {
            "hub_id": self.hub_id,
            "policy_id": self.policy_id,
            "candidate_explanation_keys": list(self.candidate_explanation_keys),
            "retained_explanation_keys": list(self.retained_explanation_keys),
            "ignored_explanation_keys": list(self.ignored_explanation_keys),
            "candidate_count": self.candidate_count,
            "retained_count": self.retained_count,
            "ignored_count": self.ignored_count,
            "by_decision_category": dict(self.by_decision_category or {}),
            "candidate_by_category": dict(self.candidate_by_category or {}),
            "candidate_by_reason": dict(self.candidate_by_reason or {}),
            "candidate_by_source": dict(self.candidate_by_source or {}),
            "metadata": _json_safe_copy(self.metadata or {}),
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class StreamOfferLifecycleAuditSummary:
    """Read-only grouped lifecycle audit metadata for stream offers."""

    hub_id: str
    total_transitions: int = 0
    by_offer_id: dict[str, int] | None = None
    by_status: dict[str, int] | None = None
    by_reason: dict[str, int] | None = None
    by_category: dict[str, int] | None = None
    explanation_count: int = 0
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _validate_required_string(self.hub_id, "hub_id")
        _validate_order(self.total_transitions, "total_transitions")
        _validate_order(self.explanation_count, "explanation_count")
        object.__setattr__(
            self,
            "by_offer_id",
            _count_dict(self.by_offer_id or {}, "by_offer_id"),
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
            "by_category",
            _count_dict(self.by_category or {}, "by_category"),
        )
        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata or {}))

    def to_summary(self) -> dict[str, object]:
        """Return deterministic, JSON-safe grouped audit metadata."""
        return {
            "hub_id": self.hub_id,
            "total_transitions": self.total_transitions,
            "by_offer_id": dict(self.by_offer_id or {}),
            "by_status": dict(self.by_status or {}),
            "by_reason": dict(self.by_reason or {}),
            "by_category": dict(self.by_category or {}),
            "explanation_count": self.explanation_count,
            "metadata": _json_safe_copy(self.metadata or {}),
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class RendezvousRequest:
    """Simulator-local metadata for a future private hub poll request."""

    request_id: str
    offer_id: str
    polling_hub_id: str
    requester_id: str
    target_scope: str
    visibility_tier: StreamOfferVisibility | LaneVisibilityTier | int = 0
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _validate_required_string(self.request_id, "request_id")
        _validate_required_string(self.offer_id, "offer_id")
        _validate_required_string(self.polling_hub_id, "polling_hub_id")
        _validate_required_string(self.requester_id, "requester_id")
        _validate_required_string(self.target_scope, "target_scope")

        visibility_tier = self.visibility_tier
        if isinstance(visibility_tier, LaneVisibilityTier):
            visibility_tier = visibility_tier.tier
        if isinstance(visibility_tier, int):
            visibility_tier = StreamOfferVisibility(visibility_tier)
        if not isinstance(visibility_tier, StreamOfferVisibility):
            raise TypeError(
                "visibility_tier must be a StreamOfferVisibility, "
                "LaneVisibilityTier, or integer"
            )
        object.__setattr__(self, "visibility_tier", visibility_tier)
        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata or {}))

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe rendezvous request summary."""
        return {
            "request_id": self.request_id,
            "offer_id": self.offer_id,
            "polling_hub_id": self.polling_hub_id,
            "requester_id": self.requester_id,
            "target_scope": self.target_scope,
            "visibility_tier": self.visibility_tier.tier,
            "metadata": _json_safe_copy(self.metadata or {}),
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class RendezvousPollResult:
    """Simulator-local result for one explicit private polling helper call."""

    request_id: str
    polling_hub_id: str
    parent_hub_id: str
    target_scope: str
    visibility_tier: StreamOfferVisibility | LaneVisibilityTier | int = 0
    matched_offer_ids: tuple[str, ...] | list[str] = ()
    matched_offers: tuple[StreamOffer, ...] | list[StreamOffer] = ()
    status: RendezvousPollStatus | str = "empty"
    reason: str = "no_discoverable_offers"
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _validate_required_string(self.request_id, "request_id")
        _validate_required_string(self.polling_hub_id, "polling_hub_id")
        _validate_required_string(self.parent_hub_id, "parent_hub_id")
        _validate_required_string(self.target_scope, "target_scope")

        visibility_tier = self.visibility_tier
        if isinstance(visibility_tier, LaneVisibilityTier):
            visibility_tier = visibility_tier.tier
        if isinstance(visibility_tier, int):
            visibility_tier = StreamOfferVisibility(visibility_tier)
        if not isinstance(visibility_tier, StreamOfferVisibility):
            raise TypeError(
                "visibility_tier must be a StreamOfferVisibility, "
                "LaneVisibilityTier, or integer"
            )
        object.__setattr__(self, "visibility_tier", visibility_tier)

        matched_offer_ids = tuple(self.matched_offer_ids)
        for offer_id in matched_offer_ids:
            _validate_required_string(offer_id, "matched_offer_id")
        object.__setattr__(self, "matched_offer_ids", matched_offer_ids)

        matched_offers = tuple(self.matched_offers)
        for offer in matched_offers:
            _validate_offer(offer)
        object.__setattr__(self, "matched_offers", matched_offers)

        status = self.status
        if isinstance(status, str):
            status = RendezvousPollStatus(status)
        if not isinstance(status, RendezvousPollStatus):
            raise TypeError("status must be a RendezvousPollStatus or string")
        object.__setattr__(self, "status", status)

        _validate_poll_reason(self.reason)
        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata or {}))

    @property
    def matched_count(self) -> int:
        """Return the number of discoverable offers in this result."""
        return len(self.matched_offer_ids)

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe rendezvous poll summary."""
        return {
            "request_id": self.request_id,
            "polling_hub_id": self.polling_hub_id,
            "parent_hub_id": self.parent_hub_id,
            "target_scope": self.target_scope,
            "visibility_tier": self.visibility_tier.tier,
            "matched_offer_ids": list(self.matched_offer_ids),
            "matched_count": self.matched_count,
            "matched_offers": [offer.to_summary() for offer in self.matched_offers],
            "status": self.status.status,
            "reason": self.reason,
            "metadata": _json_safe_copy(self.metadata or {}),
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class LaneAdmissionPolicy:
    """Simulator-local hub policy for evaluating stream offer admission."""

    policy_id: str
    hub_id: str
    allowed_lane_signatures: tuple[str, ...] | list[str] = ()
    denied_lane_signatures: tuple[str, ...] | list[str] = ()
    allowed_requester_ids: tuple[str, ...] | list[str] = ()
    denied_requester_ids: tuple[str, ...] | list[str] = ()
    allowed_target_scopes: tuple[str, ...] | list[str] = ()
    denied_target_scopes: tuple[str, ...] | list[str] = ()
    max_visibility_tier: StreamOfferVisibility | LaneVisibilityTier | int | None = None
    require_discoverable: bool = False
    default_status: LaneAdmissionStatus | str = "hold"
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _validate_required_string(self.policy_id, "policy_id")
        _validate_required_string(self.hub_id, "hub_id")
        object.__setattr__(
            self,
            "allowed_lane_signatures",
            _lane_signature_tuple(self.allowed_lane_signatures),
        )
        object.__setattr__(
            self,
            "denied_lane_signatures",
            _lane_signature_tuple(self.denied_lane_signatures),
        )
        object.__setattr__(
            self,
            "allowed_requester_ids",
            _string_tuple(self.allowed_requester_ids, "allowed_requester_ids"),
        )
        object.__setattr__(
            self,
            "denied_requester_ids",
            _string_tuple(self.denied_requester_ids, "denied_requester_ids"),
        )
        object.__setattr__(
            self,
            "allowed_target_scopes",
            _string_tuple(self.allowed_target_scopes, "allowed_target_scopes"),
        )
        object.__setattr__(
            self,
            "denied_target_scopes",
            _string_tuple(self.denied_target_scopes, "denied_target_scopes"),
        )

        max_visibility_tier = self.max_visibility_tier
        if isinstance(max_visibility_tier, LaneVisibilityTier):
            max_visibility_tier = max_visibility_tier.tier
        if isinstance(max_visibility_tier, int):
            max_visibility_tier = StreamOfferVisibility(max_visibility_tier)
        if max_visibility_tier is not None and not isinstance(
            max_visibility_tier,
            StreamOfferVisibility,
        ):
            raise TypeError(
                "max_visibility_tier must be a StreamOfferVisibility, "
                "LaneVisibilityTier, integer, or None"
            )
        object.__setattr__(self, "max_visibility_tier", max_visibility_tier)

        if not isinstance(self.require_discoverable, bool):
            raise TypeError("require_discoverable must be a boolean")

        default_status = self.default_status
        if isinstance(default_status, str):
            default_status = LaneAdmissionStatus(default_status)
        if not isinstance(default_status, LaneAdmissionStatus):
            raise TypeError("default_status must be a LaneAdmissionStatus or string")
        object.__setattr__(self, "default_status", default_status)
        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata or {}))

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe lane admission policy summary."""
        return {
            "policy_id": self.policy_id,
            "hub_id": self.hub_id,
            "allowed_lane_signatures": list(self.allowed_lane_signatures),
            "denied_lane_signatures": list(self.denied_lane_signatures),
            "allowed_requester_ids": list(self.allowed_requester_ids),
            "denied_requester_ids": list(self.denied_requester_ids),
            "allowed_target_scopes": list(self.allowed_target_scopes),
            "denied_target_scopes": list(self.denied_target_scopes),
            "max_visibility_tier": (
                None
                if self.max_visibility_tier is None
                else self.max_visibility_tier.tier
            ),
            "require_discoverable": self.require_discoverable,
            "default_status": self.default_status.status,
            "metadata": _json_safe_copy(self.metadata or {}),
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


@dataclass(frozen=True, slots=True)
class LaneAdmissionDecision:
    """Deterministic result of evaluating one stream offer against policy."""

    decision_id: str
    policy_id: str | None
    offer_id: str | None
    request_id: str | None
    hub_id: str | None
    requester_id: str | None
    target_handle: str | None
    target_scope: str | None
    lane_signature: str | None
    status: LaneAdmissionStatus | str
    reason: LaneAdmissionReason | str
    allowed: bool
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _validate_required_string(self.decision_id, "decision_id")
        _validate_optional_string(self.policy_id, "policy_id")
        _validate_optional_string(self.offer_id, "offer_id")
        _validate_optional_string(self.request_id, "request_id")
        _validate_optional_string(self.hub_id, "hub_id")
        _validate_optional_string(self.requester_id, "requester_id")
        _validate_optional_string(self.target_handle, "target_handle")
        _validate_optional_string(self.target_scope, "target_scope")

        lane_signature = self.lane_signature
        if lane_signature is not None:
            lane_signature = parse_lane_signature(lane_signature).signature
        object.__setattr__(self, "lane_signature", lane_signature)

        status = self.status
        if isinstance(status, str):
            status = LaneAdmissionStatus(status)
        if not isinstance(status, LaneAdmissionStatus):
            raise TypeError("status must be a LaneAdmissionStatus or string")
        object.__setattr__(self, "status", status)

        reason = self.reason
        if isinstance(reason, str):
            reason = LaneAdmissionReason(reason)
        if not isinstance(reason, LaneAdmissionReason):
            raise TypeError("reason must be a LaneAdmissionReason or string")
        object.__setattr__(self, "reason", reason)

        if not isinstance(self.allowed, bool):
            raise TypeError("allowed must be a boolean")
        if self.allowed != (status.status == "pass_down"):
            raise ValueError("allowed must be true only for pass_down decisions")
        object.__setattr__(self, "metadata", _json_safe_copy(self.metadata or {}))

    def to_summary(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe lane admission decision summary."""
        return {
            "decision_id": self.decision_id,
            "policy_id": self.policy_id,
            "offer_id": self.offer_id,
            "request_id": self.request_id,
            "hub_id": self.hub_id,
            "requester_id": self.requester_id,
            "target_handle": self.target_handle,
            "target_scope": self.target_scope,
            "lane_signature": self.lane_signature,
            "status": self.status.status,
            "reason": self.reason.reason,
            "allowed": self.allowed,
            "metadata": _json_safe_copy(self.metadata or {}),
        }

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return self.to_summary()


def make_stream_offer(
    *,
    offer_id: str,
    requester_id: str,
    target_handle: str,
    lane_signature: LaneSignature | str,
    requested_mode: str = "message",
    visibility_tier: int = 0,
    rendezvous_scope: str | None = None,
    created_order: int = 0,
    expires_order: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> StreamOffer:
    """Return a pure simulator-local stream offer record."""
    return StreamOffer(
        offer_id=offer_id,
        requester_id=requester_id,
        target_handle=target_handle,
        lane_signature=lane_signature,
        requested_mode=requested_mode,
        visibility_tier=visibility_tier,
        status="created",
        rendezvous_scope=rendezvous_scope,
        created_order=created_order,
        expires_order=expires_order,
        metadata=_helper_metadata(metadata),
    )


def make_basic_messaging_stream_offer(
    *,
    offer_id: str,
    requester_id: str,
    target_handle: str,
    rendezvous_scope: str | None = None,
    created_order: int = 0,
) -> StreamOffer:
    """Return a pure `basic_messaging:v1` stream offer record."""
    return make_stream_offer(
        offer_id=offer_id,
        requester_id=requester_id,
        target_handle=target_handle,
        lane_signature="basic_messaging:v1",
        requested_mode="message",
        visibility_tier=0,
        rendezvous_scope=rendezvous_scope,
        created_order=created_order,
        expires_order=None,
        metadata={
            "simulator_local": True,
            "request_only": True,
            "delivery_behavior_changed": False,
            "networking": False,
        },
    )


def make_rendezvous_request(
    *,
    request_id: str,
    offer_id: str,
    polling_hub_id: str,
    requester_id: str,
    target_scope: str,
    visibility_tier: int = 0,
    metadata: dict[str, Any] | None = None,
) -> RendezvousRequest:
    """Return pure metadata for a future rendezvous polling request."""
    return RendezvousRequest(
        request_id=request_id,
        offer_id=offer_id,
        polling_hub_id=polling_hub_id,
        requester_id=requester_id,
        target_scope=target_scope,
        visibility_tier=visibility_tier,
        metadata=_helper_metadata(metadata),
    )


def make_lane_admission_policy(
    *,
    policy_id: str,
    hub_id: str,
    allowed_lane_signatures: list[str] | None = None,
    denied_lane_signatures: list[str] | None = None,
    allowed_requester_ids: list[str] | None = None,
    denied_requester_ids: list[str] | None = None,
    allowed_target_scopes: list[str] | None = None,
    denied_target_scopes: list[str] | None = None,
    max_visibility_tier: int | None = None,
    require_discoverable: bool = False,
    default_status: str = "hold",
    metadata: dict[str, Any] | None = None,
) -> LaneAdmissionPolicy:
    """Return a pure simulator-local lane admission policy record."""
    return LaneAdmissionPolicy(
        policy_id=policy_id,
        hub_id=hub_id,
        allowed_lane_signatures=allowed_lane_signatures or [],
        denied_lane_signatures=denied_lane_signatures or [],
        allowed_requester_ids=allowed_requester_ids or [],
        denied_requester_ids=denied_requester_ids or [],
        allowed_target_scopes=allowed_target_scopes or [],
        denied_target_scopes=denied_target_scopes or [],
        max_visibility_tier=max_visibility_tier,
        require_discoverable=require_discoverable,
        default_status=default_status,
        metadata=_helper_metadata(metadata),
    )


def make_stream_offer_lifecycle_explanation_retention_policy(
    *,
    policy_id: str,
    hub_id: str,
    retain_categories: list[str] | None = None,
    retain_reasons: list[str] | None = None,
    prune_categories: list[str] | None = None,
    prune_reasons: list[str] | None = None,
    retain_sources: list[str] | None = None,
    prune_sources: list[str] | None = None,
    max_records: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> StreamOfferLifecycleExplanationRetentionPolicy:
    """Return a pure simulator-local lifecycle explanation retention policy."""
    policy_metadata: dict[str, object] = {
        "simulator_local": True,
        "read_only": True,
        "retention_policy_only": True,
        "retained_history_mutated": False,
        "explanations_deleted": False,
        "offers_deleted": False,
        "delivery_behavior_changed": False,
        "traffic_hub_routing_changed": False,
        "networking": False,
    }
    if metadata is not None:
        safe_metadata = _json_safe_copy(metadata)
        if not isinstance(safe_metadata, dict):
            raise TypeError("metadata must be a JSON-safe dict")
        policy_metadata.update(safe_metadata)

    return StreamOfferLifecycleExplanationRetentionPolicy(
        policy_id=policy_id,
        hub_id=hub_id,
        retain_categories=retain_categories or [],
        retain_reasons=retain_reasons or [],
        prune_categories=prune_categories or [],
        prune_reasons=prune_reasons or [],
        retain_sources=retain_sources or [],
        prune_sources=prune_sources or [],
        max_records=max_records,
        metadata=policy_metadata,
    )


def is_stream_offer_active(offer: StreamOffer) -> bool:
    """Return whether an offer has a non-terminal structural status."""
    _validate_offer(offer)
    return offer.status.status in STREAM_OFFER_ACTIVE_STATUSES


def is_stream_offer_terminal(offer: StreamOffer) -> bool:
    """Return whether an offer has a terminal structural status."""
    _validate_offer(offer)
    return offer.status.status in STREAM_OFFER_TERMINAL_STATUSES


def is_stream_offer_expired(offer: StreamOffer, *, current_order: int) -> bool:
    """Return whether an offer is expired by status or simulator order."""
    _validate_offer(offer)
    _validate_order(current_order, "current_order")
    return offer.status.status == "expired" or (
        offer.expires_order is not None and current_order >= offer.expires_order
    )


def stream_offer_matches_rendezvous_request(
    offer: StreamOffer,
    request: RendezvousRequest,
) -> bool:
    """Return whether an offer structurally matches a rendezvous request."""
    _validate_offer(offer)
    _validate_rendezvous_request(request)
    return (
        _stream_offer_visibility_compatible(offer, request)
        and (
            offer.rendezvous_scope is None
            or offer.rendezvous_scope == request.target_scope
        )
    )


def is_stream_offer_discoverable_to_request(
    offer: StreamOffer,
    request: RendezvousRequest,
    *,
    current_order: int | None = None,
) -> bool:
    """Return whether an active offer is discoverable for a request."""
    _validate_offer(offer)
    _validate_rendezvous_request(request)
    if current_order is not None:
        _validate_order(current_order, "current_order")
    if not stream_offer_matches_rendezvous_request(offer, request):
        return False
    if not is_stream_offer_active(offer):
        return False
    return not (
        current_order is not None
        and is_stream_offer_expired(
            offer,
            current_order=current_order,
        )
    )


def stream_offer_matches_lane(
    offer: StreamOffer,
    lane_signature: LaneSignature | str,
) -> bool:
    """Return whether the offer references the same compact lane signature."""
    _validate_offer(offer)
    if isinstance(lane_signature, LaneSignature):
        lane_signature = lane_signature.signature
    elif isinstance(lane_signature, str):
        lane_signature = parse_lane_signature(lane_signature).signature
    else:
        raise TypeError("lane_signature must be a LaneSignature or string")
    return offer.lane_signature == lane_signature


def is_lane_admission_allowed(decision: LaneAdmissionDecision) -> bool:
    """Return whether a lane admission decision permits pass-down."""
    _validate_lane_admission_decision(decision)
    return decision.status.status == "pass_down"


def is_lane_admission_blocked(decision: LaneAdmissionDecision) -> bool:
    """Return whether a lane admission decision is a blocking terminal outcome."""
    _validate_lane_admission_decision(decision)
    return decision.status.status in LANE_ADMISSION_BLOCKED_STATUSES


def is_lane_admission_terminal(decision: LaneAdmissionDecision) -> bool:
    """Return whether a lane admission decision needs no further polling."""
    _validate_lane_admission_decision(decision)
    return decision.status.status in LANE_ADMISSION_TERMINAL_STATUSES


def _validate_offer(offer: StreamOffer) -> None:
    if not isinstance(offer, StreamOffer):
        raise TypeError("offer must be a StreamOffer")


def _validate_rendezvous_request(request: RendezvousRequest) -> None:
    if not isinstance(request, RendezvousRequest):
        raise TypeError("request must be a RendezvousRequest")


def _validate_lane_admission_decision(decision: LaneAdmissionDecision) -> None:
    if not isinstance(decision, LaneAdmissionDecision):
        raise TypeError("decision must be a LaneAdmissionDecision")


def _stream_offer_visibility_compatible(
    offer: StreamOffer,
    request: RendezvousRequest,
) -> bool:
    return offer.visibility_tier.tier <= request.visibility_tier.tier


def _helper_metadata(metadata: dict[str, Any] | None) -> dict[str, object]:
    if metadata is None:
        return {"simulator_local": True, "request_only": True}
    safe_metadata = _json_safe_copy(metadata)
    if not isinstance(safe_metadata, dict):
        raise TypeError("metadata must be a JSON-safe dict")
    return safe_metadata


def _validate_mode(value: str) -> None:
    _validate_required_string(value, "stream offer mode")
    if value not in STREAM_OFFER_MODES:
        raise ValueError(
            "stream offer mode must be one of " f"{', '.join(STREAM_OFFER_MODES)}"
        )


def _validate_status(value: str) -> None:
    _validate_required_string(value, "stream offer status")
    if value not in STREAM_OFFER_STATUSES:
        raise ValueError(
            "stream offer status must be one of " f"{', '.join(STREAM_OFFER_STATUSES)}"
        )


def _validate_status_transition_reason(value: str) -> None:
    _validate_required_string(value, "stream offer status transition reason")
    if value not in STREAM_OFFER_STATUS_TRANSITION_REASONS:
        raise ValueError(
            "stream offer status transition reason must be one of "
            f"{', '.join(STREAM_OFFER_STATUS_TRANSITION_REASONS)}"
        )


def _validate_lifecycle_explanation_category(value: str) -> None:
    _validate_required_string(value, "stream offer lifecycle explanation category")
    if value not in STREAM_OFFER_LIFECYCLE_EXPLANATION_CATEGORIES:
        raise ValueError(
            "stream offer lifecycle explanation category must be one of "
            f"{', '.join(STREAM_OFFER_LIFECYCLE_EXPLANATION_CATEGORIES)}"
        )


def _validate_lifecycle_explanation_reason(value: str) -> None:
    _validate_required_string(value, "stream offer lifecycle explanation reason")
    if value not in STREAM_OFFER_LIFECYCLE_EXPLANATION_REASONS:
        raise ValueError(
            "stream offer lifecycle explanation reason must be one of "
            f"{', '.join(STREAM_OFFER_LIFECYCLE_EXPLANATION_REASONS)}"
        )


def _validate_lifecycle_retention_decision_category(value: str) -> None:
    _validate_required_string(value, "stream offer lifecycle retention decision category")
    if value not in STREAM_OFFER_LIFECYCLE_RETENTION_DECISION_CATEGORIES:
        raise ValueError(
            "stream offer lifecycle retention decision category must be one of "
            f"{', '.join(STREAM_OFFER_LIFECYCLE_RETENTION_DECISION_CATEGORIES)}"
        )


def _validate_poll_status(value: str) -> None:
    _validate_required_string(value, "rendezvous poll status")
    if value not in RENDEZVOUS_POLL_STATUSES:
        raise ValueError(
            "rendezvous poll status must be one of "
            f"{', '.join(RENDEZVOUS_POLL_STATUSES)}"
        )


def _validate_poll_reason(value: str) -> None:
    _validate_required_string(value, "rendezvous poll reason")
    if value not in RENDEZVOUS_POLL_REASONS:
        raise ValueError(
            "rendezvous poll reason must be one of "
            f"{', '.join(RENDEZVOUS_POLL_REASONS)}"
        )


def _validate_lane_admission_status(value: str) -> None:
    _validate_required_string(value, "lane admission status")
    if value not in LANE_ADMISSION_STATUSES:
        raise ValueError(
            "lane admission status must be one of "
            f"{', '.join(LANE_ADMISSION_STATUSES)}"
        )


def _validate_lane_admission_reason(value: str) -> None:
    _validate_required_string(value, "lane admission reason")
    if value not in LANE_ADMISSION_REASONS:
        raise ValueError(
            "lane admission reason must be one of "
            f"{', '.join(LANE_ADMISSION_REASONS)}"
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


def _lane_signature_tuple(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    if not isinstance(values, tuple | list):
        raise TypeError("lane signature lists must be a list or tuple")
    return tuple(parse_lane_signature(value).signature for value in values)


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


def _retention_decision_count_dict(
    values: dict[str, int],
    field_name: str,
) -> dict[str, int]:
    if not isinstance(values, dict):
        raise TypeError(f"{field_name} must be a dict")
    copied: dict[str, int] = {}
    for key, count in values.items():
        _validate_lifecycle_retention_decision_category(key)
        _validate_order(count, field_name)
        copied[key] = count
    return {key: copied[key] for key in sorted(copied)}


def _lifecycle_explanation_category_tuple(
    values: tuple[str, ...] | list[str],
    field_name: str,
) -> tuple[str, ...]:
    if not isinstance(values, tuple | list):
        raise TypeError(f"{field_name} must be a list or tuple")
    for value in values:
        _validate_lifecycle_explanation_category(value)
    return tuple(values)


def _lifecycle_explanation_reason_tuple(
    values: tuple[str, ...] | list[str],
    field_name: str,
) -> tuple[str, ...]:
    if not isinstance(values, tuple | list):
        raise TypeError(f"{field_name} must be a list or tuple")
    for value in values:
        _validate_lifecycle_explanation_reason(value)
    return tuple(values)


def _json_safe_copy(value: Any) -> object:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, tuple | list):
        return [_json_safe_copy(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe_copy(item) for key, item in value.items()}
    raise TypeError("stream offer data must be JSON-safe simulator data")
