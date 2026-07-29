"""Tests for explicit retained audit compaction apply helpers."""

from __future__ import annotations

import json
from copy import deepcopy

from darwin.models import (
    RegistryHub,
    RetainedAuditCompactionApplyResult,
    RetainedAuditCompactionDecision,
    StreamOfferLifecycleExplanation,
    make_basic_messaging_stream_offer,
)
from darwin.registry import (
    apply_retained_audit_compaction_decision,
    classify_retained_audit_records_for_compaction,
    hold_stream_offer,
    make_retained_audit_compaction_policy,
    make_stream_offer_status_transition,
    record_stream_offer_lifecycle_explanations,
    record_stream_offer_status_transition,
    summarize_held_stream_offers,
    summarize_retained_audit_compaction_apply_result,
    summarize_stream_offer_lifecycle_explanation_history,
    summarize_stream_offer_status_transitions,
)


def test_compaction_apply_explicitly_removes_only_candidate_records():
    hub = RegistryHub(hub_id="registry_chat_001", scope_path="global.chat")
    explanations = (
        _explanation(offer_id="offer_keep", category="active"),
        _explanation(offer_id="offer_compact", category="expired"),
        _explanation(
            hub_id="registry_remote_001",
            offer_id="offer_ignored",
            category="active",
        ),
        _explanation(offer_id="offer_after", category="terminal"),
    )
    record_stream_offer_lifecycle_explanations(hub, explanations)
    transition = make_stream_offer_status_transition(
        offer_id="offer_transition",
        previous_status="held",
        new_status="denied",
        reason="manual_deny",
        hub_id=hub.hub_id,
        metadata={"source": "manual_review"},
        sequence=1,
    )
    record_stream_offer_status_transition(hub, transition)
    held_offer = hold_stream_offer(
        hub,
        make_basic_messaging_stream_offer(
            offer_id="offer_held",
            requester_id="device_a",
            target_handle="target.chat",
        ),
    )
    transition_history_before = deepcopy(summarize_stream_offer_status_transitions(hub))
    held_offers_before = deepcopy(summarize_held_stream_offers(hub))
    policy = make_retained_audit_compaction_policy(
        policy_id="audit_compaction_policy_001",
        hub_id=hub.hub_id,
        history_types=["stream_offer_lifecycle_explanation"],
        compact_statuses=["expired"],
    )
    decision = classify_retained_audit_records_for_compaction(
        hub.stream_offer_lifecycle_explanation_history,
        policy,
    )
    decision = RetainedAuditCompactionDecision(
        hub_id=decision.hub_id,
        policy_id=decision.policy_id,
        history_type=decision.history_type,
        retained_record_keys=decision.retained_record_keys,
        compaction_candidate_record_keys=(
            *decision.compaction_candidate_record_keys,
            "lifecycle_explanation:99:registry_chat_001:missing:expired:"
            "expired_by_plan:expired:lifecycle_plan:5",
        ),
        ignored_record_keys=decision.ignored_record_keys,
        by_decision_category=decision.by_decision_category,
        metadata=decision.metadata,
    )

    history_before_apply = deepcopy(summarize_stream_offer_lifecycle_explanation_history(hub))
    assert [record.offer_id for record in hub.stream_offer_lifecycle_explanation_history] == [
        "offer_keep",
        "offer_compact",
        "offer_ignored",
        "offer_after",
    ]

    result = apply_retained_audit_compaction_decision(hub, decision)

    assert isinstance(result, RetainedAuditCompactionApplyResult)
    assert history_before_apply[1]["offer_id"] == "offer_compact"
    assert result.compacted_record_keys == (_explanation_key(1, explanations[1]),)
    assert result.retained_record_keys == (
        _explanation_key(0, explanations[0]),
        _explanation_key(3, explanations[3]),
    )
    assert result.ignored_record_keys == (_explanation_key(2, explanations[2]),)
    assert result.missing_record_keys == (
        "lifecycle_explanation:99:registry_chat_001:missing:expired:"
        "expired_by_plan:expired:lifecycle_plan:5",
    )
    assert result.unsupported_record_keys == ()
    assert [record.offer_id for record in hub.stream_offer_lifecycle_explanation_history] == [
        "offer_keep",
        "offer_ignored",
        "offer_after",
    ]
    assert summarize_stream_offer_status_transitions(hub) == transition_history_before
    assert summarize_held_stream_offers(hub) == held_offers_before
    assert hub.held_stream_offers == [held_offer]
    assert result.metadata["explicit_apply"] is True
    assert result.metadata["selected_history_type"] == (
        "stream_offer_lifecycle_explanation"
    )
    assert result.metadata["held_offers_mutated"] is False
    assert result.metadata["traffic_hub_routing_changed"] is False
    assert result.metadata["compact_snapshot_changed"] is False


def test_compaction_apply_supports_status_transition_history_only():
    hub = RegistryHub(hub_id="registry_chat_001", scope_path="global.chat")
    explanation = _explanation(offer_id="offer_exp", category="expired")
    record_stream_offer_lifecycle_explanations(hub, (explanation,))
    keep_transition = make_stream_offer_status_transition(
        offer_id="offer_keep",
        previous_status="created",
        new_status="held",
        reason="manual_hold",
        hub_id=hub.hub_id,
        metadata={"source": "lifecycle_apply_result"},
        sequence=1,
    )
    compact_transition = make_stream_offer_status_transition(
        offer_id="offer_compact",
        previous_status="held",
        new_status="expired",
        reason="expired",
        hub_id=hub.hub_id,
        metadata={"source": "lifecycle_apply_result"},
        sequence=2,
    )
    record_stream_offer_status_transition(hub, keep_transition)
    record_stream_offer_status_transition(hub, compact_transition)
    explanation_history_before = deepcopy(
        summarize_stream_offer_lifecycle_explanation_history(hub)
    )
    policy = make_retained_audit_compaction_policy(
        policy_id="audit_compaction_policy_001",
        hub_id=hub.hub_id,
        history_types=["stream_offer_status_transition"],
        compact_statuses=["expired"],
    )
    decision = classify_retained_audit_records_for_compaction(
        hub.stream_offer_status_transition_history,
        policy,
    )

    result = apply_retained_audit_compaction_decision(hub, decision)

    assert result.compacted_record_keys == (_transition_key(1, compact_transition),)
    assert result.retained_record_keys == (_transition_key(0, keep_transition),)
    assert [record.offer_id for record in hub.stream_offer_status_transition_history] == [
        "offer_keep",
    ]
    assert (
        summarize_stream_offer_lifecycle_explanation_history(hub)
        == explanation_history_before
    )


def test_compaction_apply_unsupported_history_type_is_noop():
    hub = RegistryHub(hub_id="registry_chat_001", scope_path="global.chat")
    explanation = _explanation(offer_id="offer_exp", category="expired")
    record_stream_offer_lifecycle_explanations(hub, (explanation,))
    history_before = deepcopy(summarize_stream_offer_lifecycle_explanation_history(hub))
    decision = RetainedAuditCompactionDecision(
        hub_id=hub.hub_id,
        policy_id="audit_compaction_policy_001",
        history_type="mixed",
        retained_record_keys=("retained:key",),
        compaction_candidate_record_keys=("candidate:key",),
        ignored_record_keys=("ignored:key", "candidate:key"),
    )

    result = apply_retained_audit_compaction_decision(hub, decision)

    assert result.compacted_record_keys == ()
    assert result.missing_record_keys == ()
    assert result.unsupported_record_keys == (
        "candidate:key",
        "retained:key",
        "ignored:key",
    )
    assert result.unsupported_count == 3
    assert result.metadata["unsupported_history_type"] is True
    assert result.metadata["registry_hub_mutated"] is False
    assert summarize_stream_offer_lifecycle_explanation_history(hub) == history_before


def test_compaction_apply_empty_decision_is_deterministic_and_safe():
    hub = RegistryHub(hub_id="registry_chat_001", scope_path="global.chat")
    explanation = _explanation(offer_id="offer_keep", category="active")
    record_stream_offer_lifecycle_explanations(hub, (explanation,))
    history_before = deepcopy(summarize_stream_offer_lifecycle_explanation_history(hub))
    decision = RetainedAuditCompactionDecision(
        hub_id=hub.hub_id,
        policy_id="audit_compaction_policy_001",
        history_type="stream_offer_lifecycle_explanation",
    )

    result = apply_retained_audit_compaction_decision(
        hub,
        decision,
        metadata={"labels": ("audit",)},
    )

    assert result.to_summary() == {
        "hub_id": hub.hub_id,
        "policy_id": "audit_compaction_policy_001",
        "history_type": "stream_offer_lifecycle_explanation",
        "compacted_record_keys": [],
        "retained_record_keys": [],
        "ignored_record_keys": [],
        "missing_record_keys": [],
        "unsupported_record_keys": [],
        "compacted_count": 0,
        "retained_count": 0,
        "ignored_count": 0,
        "missing_count": 0,
        "unsupported_count": 0,
        "metadata": {
            "simulator_local": True,
            "explicit_apply": True,
            "read_only": False,
            "compaction_apply_result_only": True,
            "registry_hub_mutated": False,
            "retained_history_mutated": False,
            "selected_history_type": "stream_offer_lifecycle_explanation",
            "selected_history_mutated": False,
            "records_compacted": False,
            "records_deleted": False,
            "records_rewritten": False,
            "unsupported_history_type": False,
            "held_offers_mutated": False,
            "stream_offers_mutated": False,
            "lifecycle_plans_mutated": False,
            "lifecycle_apply_results_mutated": False,
            "polling_history_mutated": False,
            "admission_history_mutated": False,
            "encrypted_delivery_history_mutated": False,
            "encryption_policy_history_mutated": False,
            "message_delivery_history_mutated": False,
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
            "supported_history_types": [
                "stream_offer_lifecycle_explanation",
                "stream_offer_status_transition",
                "rendezvous_poll_result",
                "lane_admission_decision",
                "encrypted_delivery_result",
                "encryption_policy_decision",
                "message_delivery_result",
                "authority_outcome",
            ],
            "labels": ["audit"],
        },
    }
    assert summarize_stream_offer_lifecycle_explanation_history(hub) == history_before
    json.dumps(result.to_summary(), sort_keys=True)


def test_compaction_apply_summarizer_is_deterministic_and_copied():
    result = RetainedAuditCompactionApplyResult(
        hub_id="registry_chat_001",
        policy_id="audit_compaction_policy_001",
        history_type="stream_offer_lifecycle_explanation",
        compacted_record_keys=("compact:key",),
        retained_record_keys=("retain:key",),
        ignored_record_keys=("ignore:key",),
        missing_record_keys=("missing:key",),
        compacted_count=1,
        retained_count=1,
        ignored_count=1,
        missing_count=1,
        metadata={"labels": ("audit",)},
    )

    summary = summarize_retained_audit_compaction_apply_result(result)
    summary["metadata"]["labels"].append("mutated")

    assert result.metadata["labels"] == ["audit"]
    assert summary["compacted_record_keys"] == ["compact:key"]
    assert summary["retained_record_keys"] == ["retain:key"]
    assert summary["ignored_record_keys"] == ["ignore:key"]
    assert summary["missing_record_keys"] == ["missing:key"]
    json.dumps(result.to_summary(), sort_keys=True)


def test_compaction_classification_does_not_auto_apply():
    hub = RegistryHub(hub_id="registry_chat_001", scope_path="global.chat")
    explanations = (
        _explanation(offer_id="offer_keep", category="active"),
        _explanation(offer_id="offer_candidate", category="expired"),
    )
    record_stream_offer_lifecycle_explanations(hub, explanations)
    policy = make_retained_audit_compaction_policy(
        policy_id="audit_compaction_policy_001",
        hub_id=hub.hub_id,
        history_types=["stream_offer_lifecycle_explanation"],
        compact_statuses=["expired"],
    )

    decision = classify_retained_audit_records_for_compaction(
        hub.stream_offer_lifecycle_explanation_history,
        policy,
    )

    assert decision.compaction_candidate_record_keys == (
        _explanation_key(1, explanations[1]),
    )
    assert [record.offer_id for record in hub.stream_offer_lifecycle_explanation_history] == [
        "offer_keep",
        "offer_candidate",
    ]


def _explanation(
    *,
    offer_id: str,
    category: str,
    reason: str | None = None,
    status: str | None = None,
    hub_id: str = "registry_chat_001",
    checked_at: int | None = 5,
    source: str | None = "lifecycle_plan",
) -> StreamOfferLifecycleExplanation:
    if reason is None:
        reason = {
            "active": "active_by_plan",
            "applied": "applied_by_result",
            "expired": "expired_by_plan",
            "missing": "missing_by_result",
            "skipped": "skipped_by_result",
            "terminal": "terminal_cleanup_candidate",
        }[category]
    return StreamOfferLifecycleExplanation(
        hub_id=hub_id,
        offer_id=offer_id,
        category=category,
        reason=reason,
        status=status or category,
        checked_at=checked_at,
        source=source,
    )


def _explanation_key(index: int, explanation: StreamOfferLifecycleExplanation) -> str:
    checked_at = "none" if explanation.checked_at is None else str(explanation.checked_at)
    source = "none" if explanation.source is None else explanation.source
    return (
        f"lifecycle_explanation:{index}:{explanation.hub_id}:"
        f"{explanation.offer_id}:{explanation.category}:{explanation.reason}:"
        f"{explanation.status}:{source}:{checked_at}"
    )


def _transition_key(index: int, transition: object) -> str:
    sequence = "none" if transition.sequence is None else str(transition.sequence)
    actor_id = "none" if transition.actor_id is None else transition.actor_id
    request_id = "none" if transition.request_id is None else transition.request_id
    return (
        f"status_transition:{index}:{transition.hub_id}:{transition.offer_id}:"
        f"{transition.previous_status.status}:{transition.new_status.status}:"
        f"{transition.reason.reason}:{actor_id}:{request_id}:{sequence}"
    )
