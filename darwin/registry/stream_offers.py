"""RegistryHub-local held stream offer helpers for v1.2."""

from __future__ import annotations

from dataclasses import replace

from darwin.models.hub import RegistryHub
from darwin.models.lane_signature import (
    LaneSignature,
    LaneVisibilityTier,
    parse_lane_signature,
)
from darwin.models.stream_offer import (
    LaneAdmissionDecision,
    LaneAdmissionPolicy,
    LaneAdmissionReason,
    LaneAdmissionStatus,
    RendezvousPollResult,
    RendezvousPollStatus,
    RendezvousRequest,
    StreamOffer,
    StreamOfferLifecycleApplyResult,
    StreamOfferLifecycleAuditSummary,
    StreamOfferLifecycleExplanation,
    StreamOfferLifecycleExplanationPruningApplyResult,
    StreamOfferLifecycleExplanationPruningPlan,
    StreamOfferLifecycleExplanationRetentionDecision,
    StreamOfferLifecycleExplanationRetentionPolicy,
    StreamOfferLifecyclePlan,
    StreamOfferMode,
    StreamOfferStatus,
    StreamOfferStatusTransition,
    StreamOfferStatusTransitionReason,
    StreamOfferVisibility,
    is_stream_offer_active,
    is_stream_offer_discoverable_to_request,
    is_stream_offer_expired,
    is_stream_offer_terminal,
    stream_offer_matches_rendezvous_request,
)


def hold_stream_offer(
    registry_hub: RegistryHub,
    offer: StreamOffer,
    *,
    replace_existing: bool = False,
) -> StreamOffer:
    """Hold a stream offer on a RegistryHub-local in-memory queue."""
    _validate_registry_hub(registry_hub)
    _validate_offer(offer)

    stored = replace(offer, status="held") if offer.status.status == "created" else offer
    existing_index = _held_offer_index(registry_hub, stored.offer_id)

    if existing_index is None:
        registry_hub.held_stream_offers.append(stored)
        return stored

    if not replace_existing:
        raise ValueError(f"held stream offer already exists: {stored.offer_id}")

    registry_hub.held_stream_offers[existing_index] = stored
    return stored


def get_held_stream_offer(
    registry_hub: RegistryHub,
    offer_id: str,
) -> StreamOffer | None:
    """Return a held stream offer by ID, if present."""
    _validate_registry_hub(registry_hub)
    _validate_required_string(offer_id, "offer_id")
    for offer in registry_hub.held_stream_offers:
        if offer.offer_id == offer_id:
            return offer
    return None


def query_held_stream_offers(
    registry_hub: RegistryHub,
    *,
    offer_id: str | None = None,
    requester_id: str | None = None,
    target_handle: str | None = None,
    lane_signature: LaneSignature | str | None = None,
    requested_mode: StreamOfferMode | str | None = None,
    visibility_tier: StreamOfferVisibility | LaneVisibilityTier | int | None = None,
    status: StreamOfferStatus | str | None = None,
    rendezvous_scope: str | None = None,
    active_only: bool | None = None,
    current_order: int | None = None,
) -> list[StreamOffer]:
    """Return held stream offers matching additive filters in append order."""
    _validate_registry_hub(registry_hub)
    _validate_optional_string(offer_id, "offer_id")
    _validate_optional_string(requester_id, "requester_id")
    _validate_optional_string(target_handle, "target_handle")
    _validate_optional_string(rendezvous_scope, "rendezvous_scope")
    lane_signature_key = _lane_signature_key(lane_signature)
    mode_key = _requested_mode_key(requested_mode)
    visibility_key = _visibility_tier_key(visibility_tier)
    status_key = _status_key(status)
    if active_only is not None and not isinstance(active_only, bool):
        raise TypeError("active_only must be a bool or None")
    if current_order is not None:
        _validate_order(current_order, "current_order")

    return [
        offer
        for offer in registry_hub.held_stream_offers
        if (offer_id is None or offer.offer_id == offer_id)
        and (requester_id is None or offer.requester_id == requester_id)
        and (target_handle is None or offer.target_handle == target_handle)
        and (lane_signature_key is None or offer.lane_signature == lane_signature_key)
        and (mode_key is None or offer.requested_mode.mode == mode_key)
        and (visibility_key is None or offer.visibility_tier.tier == visibility_key)
        and (status_key is None or offer.status.status == status_key)
        and (
            rendezvous_scope is None
            or offer.rendezvous_scope == rendezvous_scope
        )
        and _matches_active_filter(
            offer,
            active_only=active_only,
            current_order=current_order,
        )
    ]


def query_expired_held_stream_offers(
    registry_hub: RegistryHub,
    *,
    checked_at: int,
) -> list[StreamOffer]:
    """Return active held offers expired by an explicit simulator order."""
    _validate_registry_hub(registry_hub)
    _validate_order(checked_at, "checked_at")
    return [
        offer
        for offer in registry_hub.held_stream_offers
        if is_stream_offer_active(offer)
        and is_stream_offer_expired(offer, current_order=checked_at)
    ]


def plan_stream_offer_expiration(
    registry_hub: RegistryHub,
    *,
    checked_at: int,
    metadata: dict[str, object] | None = None,
) -> StreamOfferLifecyclePlan:
    """Build a read-only lifecycle plan for retained stream offers."""
    _validate_registry_hub(registry_hub)
    _validate_order(checked_at, "checked_at")
    if metadata is not None and not isinstance(metadata, dict):
        raise TypeError("metadata must be a JSON-safe dict")

    expired_offer_ids: list[str] = []
    cleanup_candidate_offer_ids: list[str] = []
    active_offer_ids: list[str] = []
    ignored_offer_ids: list[str] = []

    for offer in registry_hub.held_stream_offers:
        if is_stream_offer_active(offer):
            if is_stream_offer_expired(offer, current_order=checked_at):
                expired_offer_ids.append(offer.offer_id)
                cleanup_candidate_offer_ids.append(offer.offer_id)
            else:
                active_offer_ids.append(offer.offer_id)
            continue

        if is_stream_offer_terminal(offer):
            cleanup_candidate_offer_ids.append(offer.offer_id)
            continue

        ignored_offer_ids.append(offer.offer_id)

    plan_metadata: dict[str, object] = {
        "simulator_local": True,
        "read_only": True,
        "planning_only": True,
        "registry_hub_mutated": False,
        "offer_mutated": False,
        "transitions_recorded": False,
        "offers_deleted": False,
        "delivery_behavior_changed": False,
        "traffic_hub_routing_changed": False,
        "networking": False,
    }
    if metadata is not None:
        plan_metadata.update(metadata)

    return StreamOfferLifecyclePlan(
        hub_id=registry_hub.hub_id,
        checked_at=checked_at,
        expired_offer_ids=expired_offer_ids,
        cleanup_candidate_offer_ids=cleanup_candidate_offer_ids,
        active_offer_ids=active_offer_ids,
        ignored_offer_ids=ignored_offer_ids,
        metadata=plan_metadata,
    )


def summarize_stream_offer_lifecycle_plan(
    plan: StreamOfferLifecyclePlan,
) -> dict[str, object]:
    """Return a copied JSON-safe stream offer lifecycle plan summary."""
    _validate_lifecycle_plan(plan)
    return plan.to_summary()


def apply_stream_offer_lifecycle_plan(
    registry_hub: RegistryHub,
    plan: StreamOfferLifecyclePlan,
    *,
    record_transition: bool = True,
    actor_id: str | None = None,
    request_id: str | None = None,
    transition_metadata: dict[str, object] | None = None,
    metadata: dict[str, object] | None = None,
) -> StreamOfferLifecycleApplyResult:
    """Explicitly apply eligible expiration targets from a lifecycle plan."""
    _validate_registry_hub(registry_hub)
    _validate_lifecycle_plan(plan)
    if registry_hub.hub_id != plan.hub_id:
        raise ValueError("plan hub_id must match registry_hub.hub_id")
    if not isinstance(record_transition, bool):
        raise TypeError("record_transition must be a bool")
    _validate_optional_string(actor_id, "actor_id")
    _validate_optional_string(request_id, "request_id")
    if transition_metadata is not None and not isinstance(transition_metadata, dict):
        raise TypeError("transition_metadata must be a JSON-safe dict")
    if metadata is not None and not isinstance(metadata, dict):
        raise TypeError("metadata must be a JSON-safe dict")

    applied_offer_ids: list[str] = []
    skipped_offer_ids: list[str] = []
    missing_offer_ids: list[str] = []
    recorded_transition_count = 0

    for offer_id in plan.expired_offer_ids:
        offer = get_held_stream_offer(registry_hub, offer_id)
        if offer is None:
            missing_offer_ids.append(offer_id)
            continue

        if not is_stream_offer_active(offer) or not is_stream_offer_expired(
            offer,
            current_order=plan.checked_at,
        ):
            skipped_offer_ids.append(offer_id)
            continue

        update_held_stream_offer_status(
            registry_hub,
            offer_id,
            "expired",
            record_transition=record_transition,
            transition_reason="expired",
            actor_id=actor_id,
            request_id=request_id,
            transition_metadata=transition_metadata,
        )
        applied_offer_ids.append(offer_id)
        if record_transition:
            recorded_transition_count += 1

    result_metadata: dict[str, object] = {
        "simulator_local": True,
        "explicit_apply": True,
        "planning_only": False,
        "registry_hub_mutated": bool(applied_offer_ids),
        "offer_statuses_mutated": bool(applied_offer_ids),
        "transitions_recorded": recorded_transition_count > 0,
        "offers_deleted": False,
        "delivery_behavior_changed": False,
        "traffic_hub_routing_changed": False,
        "networking": False,
    }
    if metadata is not None:
        result_metadata.update(metadata)

    return StreamOfferLifecycleApplyResult(
        hub_id=registry_hub.hub_id,
        plan_checked_at=plan.checked_at,
        applied_offer_ids=applied_offer_ids,
        skipped_offer_ids=skipped_offer_ids,
        missing_offer_ids=missing_offer_ids,
        recorded_transition_count=recorded_transition_count,
        metadata=result_metadata,
    )


def summarize_stream_offer_lifecycle_apply_result(
    result: StreamOfferLifecycleApplyResult,
) -> dict[str, object]:
    """Return a copied JSON-safe stream offer lifecycle apply result summary."""
    _validate_lifecycle_apply_result(result)
    return result.to_summary()


def explain_stream_offer_lifecycle_plan(
    plan: StreamOfferLifecyclePlan,
) -> list[StreamOfferLifecycleExplanation]:
    """Return read-only explanations for lifecycle plan classifications."""
    _validate_lifecycle_plan(plan)
    cleanup_candidate_offer_ids = set(plan.cleanup_candidate_offer_ids)
    explained_offer_ids: set[str] = set()
    explanations: list[StreamOfferLifecycleExplanation] = []

    for offer_id in plan.expired_offer_ids:
        explanations.append(
            _lifecycle_explanation(
                hub_id=plan.hub_id,
                offer_id=offer_id,
                category="expired",
                reason="expired_by_plan",
                status="expired",
                checked_at=plan.checked_at,
                source="lifecycle_plan",
                details={
                    "plan_field": "expired_offer_ids",
                    "cleanup_candidate": offer_id in cleanup_candidate_offer_ids,
                    "read_only": True,
                },
            )
        )
        explained_offer_ids.add(offer_id)

    for offer_id in plan.cleanup_candidate_offer_ids:
        if offer_id in explained_offer_ids:
            continue
        explanations.append(
            _lifecycle_explanation(
                hub_id=plan.hub_id,
                offer_id=offer_id,
                category="terminal",
                reason="terminal_cleanup_candidate",
                status="cleanup_candidate",
                checked_at=plan.checked_at,
                source="lifecycle_plan",
                details={
                    "plan_field": "cleanup_candidate_offer_ids",
                    "cleanup_candidate": True,
                    "read_only": True,
                },
            )
        )
        explained_offer_ids.add(offer_id)

    for offer_id in plan.active_offer_ids:
        if offer_id in explained_offer_ids:
            continue
        explanations.append(
            _lifecycle_explanation(
                hub_id=plan.hub_id,
                offer_id=offer_id,
                category="active",
                reason="active_by_plan",
                status="active",
                checked_at=plan.checked_at,
                source="lifecycle_plan",
                details={
                    "plan_field": "active_offer_ids",
                    "cleanup_candidate": False,
                    "read_only": True,
                },
            )
        )
        explained_offer_ids.add(offer_id)

    for offer_id in plan.ignored_offer_ids:
        if offer_id in explained_offer_ids:
            continue
        explanations.append(
            _lifecycle_explanation(
                hub_id=plan.hub_id,
                offer_id=offer_id,
                category="skipped",
                reason="ignored_by_plan",
                status="ignored",
                checked_at=plan.checked_at,
                source="lifecycle_plan",
                details={
                    "plan_field": "ignored_offer_ids",
                    "cleanup_candidate": False,
                    "read_only": True,
                },
            )
        )
        explained_offer_ids.add(offer_id)

    return explanations


def explain_stream_offer_lifecycle_apply_result(
    result: StreamOfferLifecycleApplyResult,
) -> list[StreamOfferLifecycleExplanation]:
    """Return read-only explanations for lifecycle apply result outcomes."""
    _validate_lifecycle_apply_result(result)
    explanations: list[StreamOfferLifecycleExplanation] = []

    for offer_id in result.applied_offer_ids:
        explanations.append(
            _lifecycle_explanation(
                hub_id=result.hub_id,
                offer_id=offer_id,
                category="applied",
                reason="applied_by_result",
                status="applied",
                checked_at=result.plan_checked_at,
                source="lifecycle_apply_result",
                details={
                    "result_field": "applied_offer_ids",
                    "recorded_transition_count": result.recorded_transition_count,
                    "read_only": True,
                },
            )
        )

    for offer_id in result.skipped_offer_ids:
        explanations.append(
            _lifecycle_explanation(
                hub_id=result.hub_id,
                offer_id=offer_id,
                category="skipped",
                reason="skipped_by_result",
                status="skipped",
                checked_at=result.plan_checked_at,
                source="lifecycle_apply_result",
                details={
                    "result_field": "skipped_offer_ids",
                    "read_only": True,
                },
            )
        )

    for offer_id in result.missing_offer_ids:
        explanations.append(
            _lifecycle_explanation(
                hub_id=result.hub_id,
                offer_id=offer_id,
                category="missing",
                reason="missing_by_result",
                status="missing",
                checked_at=result.plan_checked_at,
                source="lifecycle_apply_result",
                details={
                    "result_field": "missing_offer_ids",
                    "read_only": True,
                },
            )
        )

    return explanations


def summarize_stream_offer_lifecycle_explanations(
    explanations: list[StreamOfferLifecycleExplanation]
    | tuple[StreamOfferLifecycleExplanation, ...],
) -> list[dict[str, object]]:
    """Return copied JSON-safe lifecycle explanation summaries in order."""
    if not isinstance(explanations, list | tuple):
        raise TypeError("explanations must be a list or tuple")
    for explanation in explanations:
        _validate_lifecycle_explanation(explanation)
    return [explanation.to_summary() for explanation in explanations]


def record_stream_offer_lifecycle_explanation(
    registry_hub: RegistryHub,
    explanation: StreamOfferLifecycleExplanation,
) -> StreamOfferLifecycleExplanation:
    """Append one lifecycle explanation to RegistryHub-local history."""
    _validate_registry_hub(registry_hub)
    _validate_lifecycle_explanation(explanation)
    registry_hub.stream_offer_lifecycle_explanation_history.append(explanation)
    return explanation


def record_stream_offer_lifecycle_explanations(
    registry_hub: RegistryHub,
    explanations: list[StreamOfferLifecycleExplanation]
    | tuple[StreamOfferLifecycleExplanation, ...],
) -> list[StreamOfferLifecycleExplanation]:
    """Append lifecycle explanations to RegistryHub-local history in order."""
    _validate_registry_hub(registry_hub)
    explanation_records = _lifecycle_explanation_records(explanations)
    registry_hub.stream_offer_lifecycle_explanation_history.extend(explanation_records)
    return list(explanation_records)


def query_stream_offer_lifecycle_explanations(
    registry_hub: RegistryHub,
    *,
    hub_id: str | None = None,
    offer_id: str | None = None,
    category: str | None = None,
    reason: str | None = None,
    status: str | None = None,
    source: str | None = None,
) -> list[StreamOfferLifecycleExplanation]:
    """Return retained lifecycle explanations matching additive filters."""
    _validate_registry_hub(registry_hub)
    _validate_optional_string(hub_id, "hub_id")
    _validate_optional_string(offer_id, "offer_id")
    _validate_optional_string(category, "category")
    _validate_optional_string(reason, "reason")
    _validate_optional_string(status, "status")
    _validate_optional_string(source, "source")

    return [
        explanation
        for explanation in registry_hub.stream_offer_lifecycle_explanation_history
        if (hub_id is None or explanation.hub_id == hub_id)
        and (offer_id is None or explanation.offer_id == offer_id)
        and (category is None or explanation.category == category)
        and (reason is None or explanation.reason == reason)
        and (status is None or explanation.status == status)
        and (source is None or explanation.source == source)
    ]


def summarize_stream_offer_lifecycle_explanation_history(
    registry_hub: RegistryHub,
) -> list[dict[str, object]]:
    """Return copied JSON-safe retained lifecycle explanations in append order."""
    _validate_registry_hub(registry_hub)
    return summarize_stream_offer_lifecycle_explanations(
        registry_hub.stream_offer_lifecycle_explanation_history
    )


def classify_stream_offer_lifecycle_explanations_for_retention(
    explanations: list[StreamOfferLifecycleExplanation]
    | tuple[StreamOfferLifecycleExplanation, ...],
    policy: StreamOfferLifecycleExplanationRetentionPolicy,
    *,
    metadata: dict[str, object] | None = None,
) -> StreamOfferLifecycleExplanationRetentionDecision:
    """Classify explicit lifecycle explanations under a read-only policy."""
    explanation_records = _lifecycle_explanation_records(explanations)
    _validate_lifecycle_retention_policy(policy)
    if metadata is not None and not isinstance(metadata, dict):
        raise TypeError("metadata must be a JSON-safe dict")

    entries: list[tuple[str, str]] = []
    keepable_keys: list[str] = []

    for index, explanation in enumerate(explanation_records):
        explanation_key = _lifecycle_explanation_key(index, explanation)
        if explanation.hub_id != policy.hub_id:
            entries.append((explanation_key, "ignored"))
            continue

        if _matches_lifecycle_retention_filters(
            explanation,
            categories=policy.retain_categories,
            reasons=policy.retain_reasons,
            sources=policy.retain_sources,
        ):
            entries.append((explanation_key, "kept"))
            keepable_keys.append(explanation_key)
            continue

        if _matches_lifecycle_retention_filters(
            explanation,
            categories=policy.prune_categories,
            reasons=policy.prune_reasons,
            sources=policy.prune_sources,
        ):
            entries.append((explanation_key, "prune_candidate"))
            continue

        entries.append((explanation_key, "kept"))
        keepable_keys.append(explanation_key)

    if policy.max_records is not None:
        kept_under_cap = set(keepable_keys[: policy.max_records])
        entries = [
            (
                explanation_key,
                (
                    "prune_candidate"
                    if decision_category == "kept"
                    and explanation_key not in kept_under_cap
                    else decision_category
                ),
            )
            for explanation_key, decision_category in entries
        ]

    kept_explanation_keys = [
        explanation_key
        for explanation_key, decision_category in entries
        if decision_category == "kept"
    ]
    prune_candidate_explanation_keys = [
        explanation_key
        for explanation_key, decision_category in entries
        if decision_category == "prune_candidate"
    ]
    ignored_explanation_keys = [
        explanation_key
        for explanation_key, decision_category in entries
        if decision_category == "ignored"
    ]

    by_decision_category = {
        "ignored": len(ignored_explanation_keys),
        "kept": len(kept_explanation_keys),
        "prune_candidate": len(prune_candidate_explanation_keys),
    }
    decision_metadata: dict[str, object] = {
        "simulator_local": True,
        "read_only": True,
        "retention_decision_only": True,
        "policy_decision": True,
        "registry_hub_mutated": False,
        "retained_history_mutated": False,
        "explanations_deleted": False,
        "offers_deleted": False,
        "delivery_behavior_changed": False,
        "traffic_hub_routing_changed": False,
        "networking": False,
        "filter_precedence": "retain_filters_before_prune_filters",
        "max_records_applied": policy.max_records is not None,
    }
    if metadata is not None:
        decision_metadata.update(metadata)

    return StreamOfferLifecycleExplanationRetentionDecision(
        hub_id=policy.hub_id,
        policy_id=policy.policy_id,
        kept_explanation_keys=kept_explanation_keys,
        prune_candidate_explanation_keys=prune_candidate_explanation_keys,
        ignored_explanation_keys=ignored_explanation_keys,
        by_decision_category=by_decision_category,
        metadata=decision_metadata,
    )


def summarize_stream_offer_lifecycle_explanation_retention_decision(
    decision: StreamOfferLifecycleExplanationRetentionDecision,
) -> dict[str, object]:
    """Return a copied JSON-safe retention classification summary."""
    _validate_lifecycle_retention_decision(decision)
    return decision.to_summary()


def plan_stream_offer_lifecycle_explanation_pruning(
    decision: StreamOfferLifecycleExplanationRetentionDecision | None = None,
    *,
    explanations: list[StreamOfferLifecycleExplanation]
    | tuple[StreamOfferLifecycleExplanation, ...]
    | None = None,
    policy: StreamOfferLifecycleExplanationRetentionPolicy | None = None,
    metadata: dict[str, object] | None = None,
) -> StreamOfferLifecycleExplanationPruningPlan:
    """Return a read-only pruning plan from a retention decision or policy."""
    if decision is None:
        if policy is None:
            raise TypeError("decision or policy must be provided")
        _validate_lifecycle_retention_policy(policy)
        retention_decision = classify_stream_offer_lifecycle_explanations_for_retention(
            explanations,
            policy,
        )
        decision_source = "classified_from_policy"
    else:
        _validate_lifecycle_retention_decision(decision)
        retention_decision = decision
        decision_source = "explicit_decision"
        if policy is not None:
            _validate_lifecycle_retention_policy(policy)
            if policy.hub_id != decision.hub_id or policy.policy_id != decision.policy_id:
                raise ValueError("policy must match decision hub_id and policy_id")

    explanation_records = _lifecycle_explanation_records(explanations)
    if metadata is not None and not isinstance(metadata, dict):
        raise TypeError("metadata must be a JSON-safe dict")

    candidate_explanation_keys = retention_decision.prune_candidate_explanation_keys
    retained_explanation_keys = retention_decision.kept_explanation_keys
    ignored_explanation_keys = retention_decision.ignored_explanation_keys
    candidate_key_set = set(candidate_explanation_keys)
    candidate_by_category: dict[str, int] = {}
    candidate_by_reason: dict[str, int] = {}
    candidate_by_source: dict[str, int] = {}

    for index, explanation in enumerate(explanation_records):
        explanation_key = _lifecycle_explanation_key(index, explanation)
        if explanation_key not in candidate_key_set:
            continue
        _increment_count(candidate_by_category, explanation.category)
        _increment_count(candidate_by_reason, explanation.reason)
        _increment_count(
            candidate_by_source,
            "none" if explanation.source is None else explanation.source,
        )

    by_decision_category = {
        "ignored": len(ignored_explanation_keys),
        "kept": len(retained_explanation_keys),
        "prune_candidate": len(candidate_explanation_keys),
    }
    plan_metadata: dict[str, object] = {
        "simulator_local": True,
        "read_only": True,
        "pruning_plan_only": True,
        "decision_source": decision_source,
        "registry_hub_mutated": False,
        "retained_history_mutated": False,
        "explanations_deleted": False,
        "offers_deleted": False,
        "pruning_applied": False,
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
        "candidate_group_counts_included": bool(explanation_records),
    }
    if metadata is not None:
        plan_metadata.update(metadata)

    return StreamOfferLifecycleExplanationPruningPlan(
        hub_id=retention_decision.hub_id,
        policy_id=retention_decision.policy_id,
        candidate_explanation_keys=candidate_explanation_keys,
        retained_explanation_keys=retained_explanation_keys,
        ignored_explanation_keys=ignored_explanation_keys,
        candidate_count=len(candidate_explanation_keys),
        retained_count=len(retained_explanation_keys),
        ignored_count=len(ignored_explanation_keys),
        by_decision_category=by_decision_category,
        candidate_by_category=_sorted_count_dict(candidate_by_category),
        candidate_by_reason=_sorted_count_dict(candidate_by_reason),
        candidate_by_source=_sorted_count_dict(candidate_by_source),
        metadata=plan_metadata,
    )


def summarize_stream_offer_lifecycle_explanation_pruning_plan(
    plan: StreamOfferLifecycleExplanationPruningPlan,
) -> dict[str, object]:
    """Return a copied JSON-safe pruning plan summary."""
    _validate_lifecycle_pruning_plan(plan)
    return plan.to_summary()


def summarize_stream_offer_lifecycle_explanation_pruning_by_reason(
    plan: StreamOfferLifecycleExplanationPruningPlan,
) -> dict[str, int]:
    """Return deterministic pruning candidate counts by explanation reason."""
    _validate_lifecycle_pruning_plan(plan)
    return dict(plan.candidate_by_reason or {})


def summarize_stream_offer_lifecycle_explanation_pruning_by_category(
    plan: StreamOfferLifecycleExplanationPruningPlan,
) -> dict[str, int]:
    """Return deterministic pruning candidate counts by explanation category."""
    _validate_lifecycle_pruning_plan(plan)
    return dict(plan.candidate_by_category or {})


def apply_stream_offer_lifecycle_explanation_pruning_plan(
    registry_hub: RegistryHub,
    plan: StreamOfferLifecycleExplanationPruningPlan,
    *,
    metadata: dict[str, object] | None = None,
) -> StreamOfferLifecycleExplanationPruningApplyResult:
    """Explicitly remove retained lifecycle explanation records selected by a plan."""
    _validate_registry_hub(registry_hub)
    _validate_lifecycle_pruning_plan(plan)
    if registry_hub.hub_id != plan.hub_id:
        raise ValueError("plan hub_id must match registry_hub.hub_id")
    if metadata is not None and not isinstance(metadata, dict):
        raise TypeError("metadata must be a JSON-safe dict")

    candidate_key_set = set(plan.candidate_explanation_keys)
    retained_key_set = set(plan.retained_explanation_keys)
    ignored_key_set = set(plan.ignored_explanation_keys)
    pruned_explanation_keys: list[str] = []
    retained_explanation_keys: list[str] = []
    ignored_explanation_keys: list[str] = []
    remaining_explanations: list[StreamOfferLifecycleExplanation] = []

    for index, explanation in enumerate(
        registry_hub.stream_offer_lifecycle_explanation_history
    ):
        explanation_key = _lifecycle_explanation_key(index, explanation)
        if explanation_key in candidate_key_set:
            pruned_explanation_keys.append(explanation_key)
            continue

        remaining_explanations.append(explanation)
        if explanation_key in retained_key_set:
            retained_explanation_keys.append(explanation_key)
        if explanation_key in ignored_key_set:
            ignored_explanation_keys.append(explanation_key)

    pruned_key_set = set(pruned_explanation_keys)
    missing_explanation_keys = [
        explanation_key
        for explanation_key in plan.candidate_explanation_keys
        if explanation_key not in pruned_key_set
    ]
    registry_hub.stream_offer_lifecycle_explanation_history[:] = remaining_explanations

    result_metadata: dict[str, object] = {
        "simulator_local": True,
        "explicit_apply": True,
        "read_only": False,
        "pruning_apply_result_only": True,
        "registry_hub_mutated": bool(pruned_explanation_keys),
        "retained_history_mutated": bool(pruned_explanation_keys),
        "explanations_deleted": bool(pruned_explanation_keys),
        "offers_deleted": False,
        "held_offers_mutated": False,
        "lifecycle_plans_mutated": False,
        "lifecycle_apply_results_mutated": False,
        "transition_history_mutated": False,
        "polling_history_mutated": False,
        "admission_history_mutated": False,
        "delivery_behavior_changed": False,
        "traffic_hub_state_changed": False,
        "traffic_hub_routing_changed": False,
        "compact_snapshot_changed": False,
        "automatic_cleanup": False,
        "cleanup_scheduled": False,
        "background_worker": False,
        "retry_loop": False,
        "durable_queue": False,
        "live_timer": False,
        "live_clock": False,
        "networking": False,
        "dns_lookup": False,
        "external_services": False,
        "cryptography": False,
        "canonical_identity_rewritten": False,
    }
    if metadata is not None:
        result_metadata.update(metadata)

    return StreamOfferLifecycleExplanationPruningApplyResult(
        hub_id=registry_hub.hub_id,
        policy_id=plan.policy_id,
        pruned_explanation_keys=pruned_explanation_keys,
        retained_explanation_keys=retained_explanation_keys,
        ignored_explanation_keys=ignored_explanation_keys,
        missing_explanation_keys=missing_explanation_keys,
        pruned_count=len(pruned_explanation_keys),
        retained_count=len(retained_explanation_keys),
        ignored_count=len(ignored_explanation_keys),
        missing_count=len(missing_explanation_keys),
        metadata=result_metadata,
    )


def summarize_stream_offer_lifecycle_explanation_pruning_apply_result(
    result: StreamOfferLifecycleExplanationPruningApplyResult,
) -> dict[str, object]:
    """Return a copied JSON-safe pruning apply result summary."""
    _validate_lifecycle_pruning_apply_result(result)
    return result.to_summary()


def summarize_stream_offer_lifecycle_audit(
    registry_hub: RegistryHub,
    *,
    explanations: list[StreamOfferLifecycleExplanation]
    | tuple[StreamOfferLifecycleExplanation, ...]
    | None = None,
    metadata: dict[str, object] | None = None,
) -> StreamOfferLifecycleAuditSummary:
    """Return a grouped read-only lifecycle audit summary for a RegistryHub."""
    _validate_registry_hub(registry_hub)
    explanation_records = _lifecycle_explanation_records(explanations)
    if metadata is not None and not isinstance(metadata, dict):
        raise TypeError("metadata must be a JSON-safe dict")

    by_offer_id: dict[str, int] = {}
    by_status: dict[str, int] = {}
    by_reason: dict[str, int] = {}
    by_category: dict[str, int] = {}

    for transition in registry_hub.stream_offer_status_transition_history:
        _validate_status_transition(transition)
        _increment_count(by_offer_id, transition.offer_id)
        _increment_count(by_status, transition.new_status.status)
        _increment_count(by_reason, transition.reason.reason)

    for explanation in explanation_records:
        _increment_count(by_offer_id, explanation.offer_id)
        _increment_count(by_status, explanation.status)
        _increment_count(by_reason, explanation.reason)
        _increment_count(by_category, explanation.category)

    summary_metadata: dict[str, object] = {
        "simulator_local": True,
        "read_only": True,
        "audit_summary_only": True,
        "policy_decision": False,
        "registry_hub_mutated": False,
        "offer_mutated": False,
        "transitions_recorded": False,
        "offers_deleted": False,
        "delivery_behavior_changed": False,
        "traffic_hub_routing_changed": False,
        "networking": False,
        "included_explanations": bool(explanation_records),
    }
    if metadata is not None:
        summary_metadata.update(metadata)

    return StreamOfferLifecycleAuditSummary(
        hub_id=registry_hub.hub_id,
        total_transitions=len(registry_hub.stream_offer_status_transition_history),
        by_offer_id=_sorted_count_dict(by_offer_id),
        by_status=_sorted_count_dict(by_status),
        by_reason=_sorted_count_dict(by_reason),
        by_category=_sorted_count_dict(by_category),
        explanation_count=len(explanation_records),
        metadata=summary_metadata,
    )


def summarize_stream_offer_lifecycle_audit_by_offer(
    registry_hub: RegistryHub,
    *,
    explanations: list[StreamOfferLifecycleExplanation]
    | tuple[StreamOfferLifecycleExplanation, ...]
    | None = None,
) -> dict[str, int]:
    """Return grouped lifecycle audit counts by offer ID."""
    return dict(
        summarize_stream_offer_lifecycle_audit(
            registry_hub,
            explanations=explanations,
        ).by_offer_id
        or {}
    )


def summarize_stream_offer_lifecycle_audit_by_reason(
    registry_hub: RegistryHub,
    *,
    explanations: list[StreamOfferLifecycleExplanation]
    | tuple[StreamOfferLifecycleExplanation, ...]
    | None = None,
) -> dict[str, int]:
    """Return grouped lifecycle audit counts by transition/explanation reason."""
    return dict(
        summarize_stream_offer_lifecycle_audit(
            registry_hub,
            explanations=explanations,
        ).by_reason
        or {}
    )


def update_held_stream_offer_status(
    registry_hub: RegistryHub,
    offer_id: str,
    status: StreamOfferStatus | str,
    *,
    metadata: dict[str, object] | None = None,
    record_transition: bool = False,
    transition_reason: StreamOfferStatusTransitionReason | str = "status_updated",
    actor_id: str | None = None,
    request_id: str | None = None,
    transition_metadata: dict[str, object] | None = None,
    transition_sequence: int | None = None,
) -> StreamOffer:
    """Update a held stream offer status and optionally merge JSON-safe metadata."""
    _validate_registry_hub(registry_hub)
    _validate_required_string(offer_id, "offer_id")
    if not isinstance(record_transition, bool):
        raise TypeError("record_transition must be a bool")
    status_value = _status_key(status)
    assert status_value is not None

    existing_index = _held_offer_index(registry_hub, offer_id)
    if existing_index is None:
        raise KeyError(f"held stream offer is not registered: {offer_id}")

    offer = registry_hub.held_stream_offers[existing_index]
    merged_metadata = dict(offer.metadata or {})
    if metadata is not None:
        if not isinstance(metadata, dict):
            raise TypeError("metadata must be a JSON-safe dict")
        merged_metadata.update(metadata)

    updated = replace(offer, status=status_value, metadata=merged_metadata)
    registry_hub.held_stream_offers[existing_index] = updated
    if record_transition:
        _validate_optional_string(actor_id, "actor_id")
        _validate_optional_string(request_id, "request_id")
        if transition_metadata is not None and not isinstance(transition_metadata, dict):
            raise TypeError("transition_metadata must be a JSON-safe dict")
        _validate_optional_order(transition_sequence, "transition_sequence")
        transition_reason_value = _transition_reason_key(transition_reason)
        record_stream_offer_status_transition(
            registry_hub,
            make_stream_offer_status_transition(
                offer_id=offer_id,
                previous_status=offer.status,
                new_status=status_value,
                reason=transition_reason_value,
                hub_id=registry_hub.hub_id,
                actor_id=actor_id,
                request_id=request_id,
                metadata=transition_metadata,
                sequence=transition_sequence,
            ),
        )
    return updated


def summarize_held_stream_offers(registry_hub: RegistryHub) -> list[dict[str, object]]:
    """Return JSON-safe summaries for held stream offers in append order."""
    _validate_registry_hub(registry_hub)
    return [offer.to_summary() for offer in registry_hub.held_stream_offers]


def make_stream_offer_status_transition(
    *,
    offer_id: str,
    previous_status: StreamOfferStatus | str,
    new_status: StreamOfferStatus | str,
    reason: StreamOfferStatusTransitionReason | str,
    hub_id: str,
    actor_id: str | None = None,
    request_id: str | None = None,
    metadata: dict[str, object] | None = None,
    sequence: int | None = None,
) -> StreamOfferStatusTransition:
    """Return symbolic simulator-local stream offer transition metadata."""
    return StreamOfferStatusTransition(
        offer_id=offer_id,
        previous_status=previous_status,
        new_status=new_status,
        reason=reason,
        hub_id=hub_id,
        actor_id=actor_id,
        request_id=request_id,
        metadata=metadata,
        sequence=sequence,
    )


def record_stream_offer_status_transition(
    registry_hub: RegistryHub,
    transition: StreamOfferStatusTransition,
) -> StreamOfferStatusTransition:
    """Append a status transition to RegistryHub-local lifecycle history."""
    _validate_registry_hub(registry_hub)
    _validate_status_transition(transition)
    registry_hub.stream_offer_status_transition_history.append(transition)
    return transition


def query_stream_offer_status_transitions(
    registry_hub: RegistryHub,
    *,
    offer_id: str | None = None,
    hub_id: str | None = None,
    previous_status: StreamOfferStatus | str | None = None,
    new_status: StreamOfferStatus | str | None = None,
    status: StreamOfferStatus | str | None = None,
    reason: StreamOfferStatusTransitionReason | str | None = None,
    actor_id: str | None = None,
    request_id: str | None = None,
) -> list[StreamOfferStatusTransition]:
    """Return retained status transitions matching additive filters."""
    _validate_registry_hub(registry_hub)
    _validate_optional_string(offer_id, "offer_id")
    _validate_optional_string(hub_id, "hub_id")
    _validate_optional_string(actor_id, "actor_id")
    _validate_optional_string(request_id, "request_id")
    previous_status_key = _status_key(previous_status)
    new_status_key = _status_key(new_status)
    status_key = _status_key(status)
    reason_key = _transition_reason_key(reason)

    return [
        transition
        for transition in registry_hub.stream_offer_status_transition_history
        if (offer_id is None or transition.offer_id == offer_id)
        and (hub_id is None or transition.hub_id == hub_id)
        and (
            previous_status_key is None
            or transition.previous_status.status == previous_status_key
        )
        and (
            new_status_key is None
            or transition.new_status.status == new_status_key
        )
        and (
            status_key is None
            or transition.previous_status.status == status_key
            or transition.new_status.status == status_key
        )
        and (reason_key is None or transition.reason.reason == reason_key)
        and (actor_id is None or transition.actor_id == actor_id)
        and (request_id is None or transition.request_id == request_id)
    ]


def summarize_stream_offer_status_transitions(
    registry_hub: RegistryHub,
) -> list[dict[str, object]]:
    """Return JSON-safe retained status transition summaries in append order."""
    _validate_registry_hub(registry_hub)
    return [
        transition.to_summary()
        for transition in registry_hub.stream_offer_status_transition_history
    ]


def record_rendezvous_poll_result(
    registry_hub: RegistryHub,
    result: RendezvousPollResult,
) -> RendezvousPollResult:
    """Append a rendezvous poll result to RegistryHub-local audit history."""
    _validate_registry_hub(registry_hub)
    _validate_poll_result(result)
    registry_hub.rendezvous_poll_result_history.append(result)
    return result


def query_rendezvous_poll_results(
    registry_hub: RegistryHub,
    *,
    request_id: str | None = None,
    polling_hub_id: str | None = None,
    parent_hub_id: str | None = None,
    target_scope: str | None = None,
    visibility_tier: StreamOfferVisibility | LaneVisibilityTier | int | None = None,
    status: RendezvousPollStatus | str | None = None,
    reason: str | None = None,
    matched_offer_id: str | None = None,
) -> list[RendezvousPollResult]:
    """Return retained poll results matching additive filters in append order."""
    _validate_registry_hub(registry_hub)
    _validate_optional_string(request_id, "request_id")
    _validate_optional_string(polling_hub_id, "polling_hub_id")
    _validate_optional_string(parent_hub_id, "parent_hub_id")
    _validate_optional_string(target_scope, "target_scope")
    _validate_optional_string(reason, "reason")
    _validate_optional_string(matched_offer_id, "matched_offer_id")
    visibility_key = _visibility_tier_key(visibility_tier)
    poll_status_key = _poll_status_key(status)

    return [
        result
        for result in registry_hub.rendezvous_poll_result_history
        if (request_id is None or result.request_id == request_id)
        and (polling_hub_id is None or result.polling_hub_id == polling_hub_id)
        and (parent_hub_id is None or result.parent_hub_id == parent_hub_id)
        and (target_scope is None or result.target_scope == target_scope)
        and (visibility_key is None or result.visibility_tier.tier == visibility_key)
        and (poll_status_key is None or result.status.status == poll_status_key)
        and (reason is None or result.reason == reason)
        and (
            matched_offer_id is None
            or matched_offer_id in result.matched_offer_ids
        )
    ]


def summarize_rendezvous_poll_results(
    registry_hub: RegistryHub,
) -> list[dict[str, object]]:
    """Return JSON-safe retained poll result summaries in append order."""
    _validate_registry_hub(registry_hub)
    return [
        result.to_summary()
        for result in registry_hub.rendezvous_poll_result_history
    ]


def poll_held_stream_offers(
    parent_hub: RegistryHub | None,
    request: RendezvousRequest,
    *,
    lane_signature: LaneSignature | str | None = None,
    requested_mode: StreamOfferMode | str | None = None,
    active_only: bool = True,
    current_order: int | None = None,
) -> RendezvousPollResult:
    """Return discoverable held stream offers for one explicit poll request."""
    _validate_rendezvous_request(request)
    if parent_hub is None:
        return _poll_result(
            request,
            parent_hub_id="hub_missing",
            matched_offers=[],
            status="invalid_request",
            reason="hub_missing",
        )
    _validate_registry_hub(parent_hub)
    lane_signature_key = _lane_signature_key(lane_signature)
    mode_key = _requested_mode_key(requested_mode)
    if not isinstance(active_only, bool):
        raise TypeError("active_only must be a bool")
    if current_order is not None:
        _validate_order(current_order, "current_order")

    matches = [
        offer
        for offer in parent_hub.held_stream_offers
        if _poll_offer_matches(
            offer,
            request,
            lane_signature_key=lane_signature_key,
            mode_key=mode_key,
            active_only=active_only,
            current_order=current_order,
        )
    ]

    if matches:
        return _poll_result(
            request,
            parent_hub_id=parent_hub.hub_id,
            matched_offers=matches,
            status="matched",
            reason="offers_available",
        )

    reason = (
        "scope_mismatch"
        if _has_scope_visible_offer(parent_hub, request)
        else "no_discoverable_offers"
    )
    return _poll_result(
        request,
        parent_hub_id=parent_hub.hub_id,
        matched_offers=[],
        status="empty",
        reason=reason,
    )


def mark_stream_offers_discoverable(
    parent_hub: RegistryHub,
    offer_ids: list[str],
    *,
    metadata: dict[str, object] | None = None,
) -> list[StreamOffer]:
    """Mark selected held stream offers discoverable without delivery side effects."""
    _validate_registry_hub(parent_hub)
    if not isinstance(offer_ids, list):
        raise TypeError("offer_ids must be a list")
    for offer_id in offer_ids:
        _validate_required_string(offer_id, "offer_id")

    updated_offers: list[StreamOffer] = []
    requested_ids = set(offer_ids)
    for index, offer in enumerate(parent_hub.held_stream_offers):
        if offer.offer_id not in requested_ids:
            continue

        merged_metadata = dict(offer.metadata or {})
        if metadata is not None:
            if not isinstance(metadata, dict):
                raise TypeError("metadata must be a JSON-safe dict")
            merged_metadata.update(metadata)

        updated = replace(offer, status="discoverable", metadata=merged_metadata)
        parent_hub.held_stream_offers[index] = updated
        updated_offers.append(updated)

    return updated_offers


def record_lane_admission_decision(
    registry_hub: RegistryHub,
    decision: LaneAdmissionDecision,
) -> LaneAdmissionDecision:
    """Append a lane admission decision to RegistryHub-local audit history."""
    _validate_registry_hub(registry_hub)
    _validate_lane_admission_decision(decision)
    registry_hub.lane_admission_decision_history.append(decision)
    return decision


def query_lane_admission_decisions(
    registry_hub: RegistryHub,
    *,
    decision_id: str | None = None,
    policy_id: str | None = None,
    offer_id: str | None = None,
    request_id: str | None = None,
    hub_id: str | None = None,
    requester_id: str | None = None,
    target_handle: str | None = None,
    target_scope: str | None = None,
    lane_signature: LaneSignature | str | None = None,
    status: LaneAdmissionStatus | str | None = None,
    reason: LaneAdmissionReason | str | None = None,
    allowed: bool | None = None,
) -> list[LaneAdmissionDecision]:
    """Return retained admission decisions matching additive filters in append order."""
    _validate_registry_hub(registry_hub)
    _validate_optional_string(decision_id, "decision_id")
    _validate_optional_string(policy_id, "policy_id")
    _validate_optional_string(offer_id, "offer_id")
    _validate_optional_string(request_id, "request_id")
    _validate_optional_string(hub_id, "hub_id")
    _validate_optional_string(requester_id, "requester_id")
    _validate_optional_string(target_handle, "target_handle")
    _validate_optional_string(target_scope, "target_scope")
    lane_signature_key = _lane_signature_key(lane_signature)
    admission_status_key = _lane_admission_status_key(status)
    admission_reason_key = _lane_admission_reason_key(reason)
    if allowed is not None and not isinstance(allowed, bool):
        raise TypeError("allowed must be a bool or None")

    return [
        decision
        for decision in registry_hub.lane_admission_decision_history
        if (decision_id is None or decision.decision_id == decision_id)
        and (policy_id is None or decision.policy_id == policy_id)
        and (offer_id is None or decision.offer_id == offer_id)
        and (request_id is None or decision.request_id == request_id)
        and (hub_id is None or decision.hub_id == hub_id)
        and (requester_id is None or decision.requester_id == requester_id)
        and (target_handle is None or decision.target_handle == target_handle)
        and (target_scope is None or decision.target_scope == target_scope)
        and (
            lane_signature_key is None
            or decision.lane_signature == lane_signature_key
        )
        and (
            admission_status_key is None
            or decision.status.status == admission_status_key
        )
        and (
            admission_reason_key is None
            or decision.reason.reason == admission_reason_key
        )
        and (allowed is None or decision.allowed is allowed)
    ]


def summarize_lane_admission_decisions(
    registry_hub: RegistryHub,
) -> list[dict[str, object]]:
    """Return JSON-safe retained admission decision summaries in append order."""
    _validate_registry_hub(registry_hub)
    return [
        decision.to_summary()
        for decision in registry_hub.lane_admission_decision_history
    ]


def evaluate_lane_admission_policy(
    policy: LaneAdmissionPolicy,
    offer: StreamOffer,
    *,
    request: RendezvousRequest | None = None,
    poll_result: RendezvousPollResult | None = None,
    decision_id: str | None = None,
    metadata: dict[str, object] | None = None,
) -> LaneAdmissionDecision:
    """Evaluate one stream offer against a simulator-local admission policy."""
    _validate_optional_rendezvous_request(request)
    _validate_optional_poll_result(poll_result)
    _validate_optional_string(decision_id, "decision_id")
    if metadata is not None and not isinstance(metadata, dict):
        raise TypeError("metadata must be a JSON-safe dict")

    if not isinstance(policy, LaneAdmissionPolicy):
        return _lane_admission_decision(
            policy=None,
            offer=offer if isinstance(offer, StreamOffer) else None,
            request=request,
            poll_result=poll_result,
            decision_id=decision_id,
            status="deny",
            reason="invalid_policy",
            metadata=metadata,
        )

    if not isinstance(offer, StreamOffer):
        return _lane_admission_decision(
            policy=policy,
            offer=None,
            request=request,
            poll_result=poll_result,
            decision_id=decision_id,
            status="deny",
            reason="invalid_offer",
            metadata=metadata,
        )

    if is_stream_offer_terminal(offer):
        return _lane_admission_decision(
            policy=policy,
            offer=offer,
            request=request,
            poll_result=poll_result,
            decision_id=decision_id,
            status="deny",
            reason="invalid_offer",
            metadata=metadata,
        )

    target_scope = _target_scope(offer, request, poll_result)

    if offer.requester_id in policy.denied_requester_ids:
        return _lane_admission_decision(
            policy=policy,
            offer=offer,
            request=request,
            poll_result=poll_result,
            decision_id=decision_id,
            status="deny",
            reason="explicit_requester_denied",
            metadata=metadata,
        )

    if offer.lane_signature in policy.denied_lane_signatures:
        return _lane_admission_decision(
            policy=policy,
            offer=offer,
            request=request,
            poll_result=poll_result,
            decision_id=decision_id,
            status="deny",
            reason="explicit_lane_denied",
            metadata=metadata,
        )

    if target_scope is not None and target_scope in policy.denied_target_scopes:
        return _lane_admission_decision(
            policy=policy,
            offer=offer,
            request=request,
            poll_result=poll_result,
            decision_id=decision_id,
            status="deny",
            reason="explicit_scope_denied",
            metadata=metadata,
        )

    if (
        policy.max_visibility_tier is not None
        and offer.visibility_tier.tier > policy.max_visibility_tier.tier
    ):
        return _lane_admission_decision(
            policy=policy,
            offer=offer,
            request=request,
            poll_result=poll_result,
            decision_id=decision_id,
            status="deny",
            reason="visibility_tier_exceeded",
            metadata=metadata,
        )

    if policy.require_discoverable and not _offer_in_poll_result(offer, poll_result):
        return _lane_admission_decision(
            policy=policy,
            offer=offer,
            request=request,
            poll_result=poll_result,
            decision_id=decision_id,
            status="requires_poll",
            reason="not_discoverable",
            metadata=metadata,
        )

    if (
        policy.allowed_lane_signatures
        and offer.lane_signature not in policy.allowed_lane_signatures
    ):
        return _lane_admission_decision(
            policy=policy,
            offer=offer,
            request=request,
            poll_result=poll_result,
            decision_id=decision_id,
            status="hold",
            reason="lane_not_allowed",
            metadata=metadata,
        )

    if (
        policy.allowed_requester_ids
        and offer.requester_id not in policy.allowed_requester_ids
    ):
        return _lane_admission_decision(
            policy=policy,
            offer=offer,
            request=request,
            poll_result=poll_result,
            decision_id=decision_id,
            status="hold",
            reason="requester_not_allowed",
            metadata=metadata,
        )

    if policy.allowed_target_scopes and (
        target_scope is None or target_scope not in policy.allowed_target_scopes
    ):
        return _lane_admission_decision(
            policy=policy,
            offer=offer,
            request=request,
            poll_result=poll_result,
            decision_id=decision_id,
            status="hold",
            reason="scope_not_allowed",
            metadata=metadata,
        )

    return _lane_admission_decision(
        policy=policy,
        offer=offer,
        request=request,
        poll_result=poll_result,
        decision_id=decision_id,
        status=policy.default_status.status,
        reason=_default_lane_admission_reason(policy.default_status.status),
        metadata=metadata,
    )


def _lane_admission_decision(
    *,
    policy: LaneAdmissionPolicy | None,
    offer: StreamOffer | None,
    request: RendezvousRequest | None,
    poll_result: RendezvousPollResult | None,
    decision_id: str | None,
    status: str,
    reason: str,
    metadata: dict[str, object] | None,
) -> LaneAdmissionDecision:
    decision_metadata: dict[str, object] = {
        "simulator_local": True,
        "policy_only": True,
        "read_only": True,
        "registry_hub_mutated": False,
        "offer_mutated": False,
        "message_mutated": False,
        "inbox_mutated": False,
        "delivery_result_created": False,
        "delivery_behavior_changed": False,
        "traffic_hub_routing_changed": False,
        "networking": False,
    }
    if poll_result is not None:
        decision_metadata["poll_result_status"] = poll_result.status.status
        decision_metadata["poll_result_reason"] = poll_result.reason
    if metadata is not None:
        decision_metadata.update(metadata)

    target_scope = _target_scope(offer, request, poll_result)
    if decision_id is None:
        decision_id = _lane_admission_decision_id(policy, offer, request)

    return LaneAdmissionDecision(
        decision_id=decision_id,
        policy_id=None if policy is None else policy.policy_id,
        offer_id=None if offer is None else offer.offer_id,
        request_id=None if request is None else request.request_id,
        hub_id=None if policy is None else policy.hub_id,
        requester_id=None if offer is None else offer.requester_id,
        target_handle=None if offer is None else offer.target_handle,
        target_scope=target_scope,
        lane_signature=None if offer is None else offer.lane_signature,
        status=status,
        reason=reason,
        allowed=status == "pass_down",
        metadata=decision_metadata,
    )


def _lane_admission_decision_id(
    policy: LaneAdmissionPolicy | None,
    offer: StreamOffer | None,
    request: RendezvousRequest | None,
) -> str:
    policy_id = "invalid_policy" if policy is None else policy.policy_id
    offer_id = "invalid_offer" if offer is None else offer.offer_id
    request_id = "no_request" if request is None else request.request_id
    return f"lane_admission:{policy_id}:{offer_id}:{request_id}"


def _default_lane_admission_reason(status: str) -> str:
    if status == "pass_down":
        return "accepted"
    if status == "rate_limited":
        return "rate_limited"
    if status == "quarantined":
        return "quarantined"
    if status == "deny":
        return "default_hold"
    if status == "requires_poll":
        return "not_discoverable"
    return "default_hold"


def _target_scope(
    offer: StreamOffer | None,
    request: RendezvousRequest | None,
    poll_result: RendezvousPollResult | None,
) -> str | None:
    if request is not None:
        return request.target_scope
    if poll_result is not None:
        return poll_result.target_scope
    if offer is not None:
        return offer.rendezvous_scope
    return None


def _offer_in_poll_result(
    offer: StreamOffer,
    poll_result: RendezvousPollResult | None,
) -> bool:
    if poll_result is None:
        return False
    return (
        poll_result.status.status == "matched"
        and offer.offer_id in poll_result.matched_offer_ids
    )


def _poll_offer_matches(
    offer: StreamOffer,
    request: RendezvousRequest,
    *,
    lane_signature_key: str | None,
    mode_key: str | None,
    active_only: bool,
    current_order: int | None,
) -> bool:
    if lane_signature_key is not None and offer.lane_signature != lane_signature_key:
        return False
    if mode_key is not None and offer.requested_mode.mode != mode_key:
        return False
    if active_only:
        return is_stream_offer_discoverable_to_request(
            offer,
            request,
            current_order=current_order,
        )
    return stream_offer_matches_rendezvous_request(offer, request)


def _poll_result(
    request: RendezvousRequest,
    *,
    parent_hub_id: str,
    matched_offers: list[StreamOffer],
    status: str,
    reason: str,
) -> RendezvousPollResult:
    return RendezvousPollResult(
        request_id=request.request_id,
        polling_hub_id=request.polling_hub_id,
        parent_hub_id=parent_hub_id,
        target_scope=request.target_scope,
        visibility_tier=request.visibility_tier,
        matched_offer_ids=[offer.offer_id for offer in matched_offers],
        matched_offers=matched_offers,
        status=status,
        reason=reason,
        metadata={
            "simulator_local": True,
            "read_only": True,
            "delivery_behavior_changed": False,
            "networking": False,
        },
    )


def _has_scope_visible_offer(
    parent_hub: RegistryHub,
    request: RendezvousRequest,
) -> bool:
    return any(
        offer.rendezvous_scope is not None
        and offer.rendezvous_scope != request.target_scope
        and offer.visibility_tier.tier <= request.visibility_tier.tier
        for offer in parent_hub.held_stream_offers
    )


def _matches_active_filter(
    offer: StreamOffer,
    *,
    active_only: bool | None,
    current_order: int | None,
) -> bool:
    if active_only is None:
        return True

    expired_by_order = (
        False
        if current_order is None
        else is_stream_offer_expired(offer, current_order=current_order)
    )
    active = is_stream_offer_active(offer) and not expired_by_order
    return active if active_only else not active


def _held_offer_index(registry_hub: RegistryHub, offer_id: str) -> int | None:
    for index, existing in enumerate(registry_hub.held_stream_offers):
        if existing.offer_id == offer_id:
            return index
    return None


def _lane_signature_key(lane_signature: LaneSignature | str | None) -> str | None:
    if lane_signature is None:
        return None
    if isinstance(lane_signature, LaneSignature):
        return lane_signature.signature
    if isinstance(lane_signature, str):
        return parse_lane_signature(lane_signature).signature
    raise TypeError("lane_signature must be a LaneSignature, string, or None")


def _requested_mode_key(requested_mode: StreamOfferMode | str | None) -> str | None:
    if requested_mode is None:
        return None
    if isinstance(requested_mode, StreamOfferMode):
        return requested_mode.mode
    if isinstance(requested_mode, str):
        return StreamOfferMode(requested_mode).mode
    raise TypeError("requested_mode must be a StreamOfferMode, string, or None")


def _visibility_tier_key(
    visibility_tier: StreamOfferVisibility | LaneVisibilityTier | int | None,
) -> int | None:
    if visibility_tier is None:
        return None
    if isinstance(visibility_tier, StreamOfferVisibility | LaneVisibilityTier):
        return visibility_tier.tier
    if isinstance(visibility_tier, int):
        return StreamOfferVisibility(visibility_tier).tier
    raise TypeError(
        "visibility_tier must be a StreamOfferVisibility, LaneVisibilityTier, "
        "integer, or None"
    )


def _status_key(status: StreamOfferStatus | str | None) -> str | None:
    if status is None:
        return None
    if isinstance(status, StreamOfferStatus):
        return status.status
    if isinstance(status, str):
        return StreamOfferStatus(status).status
    raise TypeError("status must be a StreamOfferStatus, string, or None")


def _transition_reason_key(
    reason: StreamOfferStatusTransitionReason | str | None,
) -> str | None:
    if reason is None:
        return None
    if isinstance(reason, StreamOfferStatusTransitionReason):
        return reason.reason
    if isinstance(reason, str):
        return StreamOfferStatusTransitionReason(reason).reason
    raise TypeError(
        "reason must be a StreamOfferStatusTransitionReason, string, or None"
    )


def _poll_status_key(status: RendezvousPollStatus | str | None) -> str | None:
    if status is None:
        return None
    if isinstance(status, RendezvousPollStatus):
        return status.status
    if isinstance(status, str):
        return RendezvousPollStatus(status).status
    raise TypeError("status must be a RendezvousPollStatus, string, or None")


def _lane_admission_status_key(
    status: LaneAdmissionStatus | str | None,
) -> str | None:
    if status is None:
        return None
    if isinstance(status, LaneAdmissionStatus):
        return status.status
    if isinstance(status, str):
        return LaneAdmissionStatus(status).status
    raise TypeError("status must be a LaneAdmissionStatus, string, or None")


def _lane_admission_reason_key(
    reason: LaneAdmissionReason | str | None,
) -> str | None:
    if reason is None:
        return None
    if isinstance(reason, LaneAdmissionReason):
        return reason.reason
    if isinstance(reason, str):
        return LaneAdmissionReason(reason).reason
    raise TypeError("reason must be a LaneAdmissionReason, string, or None")


def _validate_poll_result(result: RendezvousPollResult) -> None:
    if not isinstance(result, RendezvousPollResult):
        raise TypeError("result must be a RendezvousPollResult")


def _validate_lane_admission_decision(decision: LaneAdmissionDecision) -> None:
    if not isinstance(decision, LaneAdmissionDecision):
        raise TypeError("decision must be a LaneAdmissionDecision")


def _validate_status_transition(transition: StreamOfferStatusTransition) -> None:
    if not isinstance(transition, StreamOfferStatusTransition):
        raise TypeError("transition must be a StreamOfferStatusTransition")


def _validate_lifecycle_plan(plan: StreamOfferLifecyclePlan) -> None:
    if not isinstance(plan, StreamOfferLifecyclePlan):
        raise TypeError("plan must be a StreamOfferLifecyclePlan")


def _validate_lifecycle_apply_result(result: StreamOfferLifecycleApplyResult) -> None:
    if not isinstance(result, StreamOfferLifecycleApplyResult):
        raise TypeError("result must be a StreamOfferLifecycleApplyResult")


def _validate_lifecycle_explanation(
    explanation: StreamOfferLifecycleExplanation,
) -> None:
    if not isinstance(explanation, StreamOfferLifecycleExplanation):
        raise TypeError("explanation must be a StreamOfferLifecycleExplanation")


def _validate_lifecycle_retention_policy(
    policy: StreamOfferLifecycleExplanationRetentionPolicy,
) -> None:
    if not isinstance(policy, StreamOfferLifecycleExplanationRetentionPolicy):
        raise TypeError(
            "policy must be a StreamOfferLifecycleExplanationRetentionPolicy"
        )


def _validate_lifecycle_retention_decision(
    decision: StreamOfferLifecycleExplanationRetentionDecision,
) -> None:
    if not isinstance(decision, StreamOfferLifecycleExplanationRetentionDecision):
        raise TypeError(
            "decision must be a StreamOfferLifecycleExplanationRetentionDecision"
        )


def _validate_lifecycle_pruning_plan(
    plan: StreamOfferLifecycleExplanationPruningPlan,
) -> None:
    if not isinstance(plan, StreamOfferLifecycleExplanationPruningPlan):
        raise TypeError(
            "plan must be a StreamOfferLifecycleExplanationPruningPlan"
        )


def _validate_lifecycle_pruning_apply_result(
    result: StreamOfferLifecycleExplanationPruningApplyResult,
) -> None:
    if not isinstance(result, StreamOfferLifecycleExplanationPruningApplyResult):
        raise TypeError(
            "result must be a StreamOfferLifecycleExplanationPruningApplyResult"
        )


def _lifecycle_explanation_records(
    explanations: list[StreamOfferLifecycleExplanation]
    | tuple[StreamOfferLifecycleExplanation, ...]
    | None,
) -> tuple[StreamOfferLifecycleExplanation, ...]:
    if explanations is None:
        return ()
    if not isinstance(explanations, list | tuple):
        raise TypeError("explanations must be a list, tuple, or None")
    for explanation in explanations:
        _validate_lifecycle_explanation(explanation)
    return tuple(explanations)


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


def _matches_lifecycle_retention_filters(
    explanation: StreamOfferLifecycleExplanation,
    *,
    categories: tuple[str, ...],
    reasons: tuple[str, ...],
    sources: tuple[str, ...],
) -> bool:
    return (
        (bool(categories) and explanation.category in categories)
        or (bool(reasons) and explanation.reason in reasons)
        or (
            bool(sources)
            and explanation.source is not None
            and explanation.source in sources
        )
    )


def _validate_offer(offer: StreamOffer) -> None:
    if not isinstance(offer, StreamOffer):
        raise TypeError("offer must be a StreamOffer")


def _validate_rendezvous_request(request: RendezvousRequest) -> None:
    if not isinstance(request, RendezvousRequest):
        raise TypeError("request must be a RendezvousRequest")


def _validate_optional_rendezvous_request(request: RendezvousRequest | None) -> None:
    if request is None:
        return
    _validate_rendezvous_request(request)


def _validate_optional_poll_result(poll_result: RendezvousPollResult | None) -> None:
    if poll_result is None:
        return
    if not isinstance(poll_result, RendezvousPollResult):
        raise TypeError("poll_result must be a RendezvousPollResult or None")


def _validate_registry_hub(registry_hub: RegistryHub) -> None:
    if not isinstance(registry_hub, RegistryHub):
        raise TypeError("registry_hub must be a RegistryHub")


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


def _lifecycle_explanation(
    *,
    hub_id: str,
    offer_id: str,
    category: str,
    reason: str,
    status: str,
    checked_at: int,
    source: str,
    details: dict[str, object],
) -> StreamOfferLifecycleExplanation:
    return StreamOfferLifecycleExplanation(
        hub_id=hub_id,
        offer_id=offer_id,
        category=category,
        reason=reason,
        status=status,
        checked_at=checked_at,
        source=source,
        details={
            "simulator_local": True,
            "policy_decision": False,
            "registry_hub_mutated": False,
            "offer_mutated": False,
            "transitions_recorded": False,
            "offers_deleted": False,
            "delivery_behavior_changed": False,
            "traffic_hub_routing_changed": False,
            "networking": False,
            **details,
        },
    )


def _increment_count(counts: dict[str, int], key: str) -> None:
    counts[key] = counts.get(key, 0) + 1


def _sorted_count_dict(counts: dict[str, int]) -> dict[str, int]:
    return {key: counts[key] for key in sorted(counts)}
