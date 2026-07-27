"""Tests for retained audit compaction policy classification helpers."""

from __future__ import annotations

import json
from copy import deepcopy

from darwin.models import (
    RegistryHub,
    RetainedAuditCompactionDecision,
    RetainedAuditCompactionPolicy,
    StreamOfferLifecycleExplanation,
)
from darwin.registry import (
    classify_retained_audit_records_for_compaction,
    make_retained_audit_compaction_policy,
    make_stream_offer_status_transition,
    record_stream_offer_lifecycle_explanations,
    record_stream_offer_status_transition,
    summarize_retained_audit_compaction_decision,
    summarize_stream_offer_lifecycle_explanation_history,
    summarize_stream_offer_status_transitions,
)


def test_compaction_policy_classifies_retained_candidate_and_ignored_records():
    records = (
        _explanation(offer_id="offer_retained", category="active"),
        _explanation(
            offer_id="offer_candidate",
            category="expired",
            reason="expired_by_plan",
            status="expired",
        ),
        _explanation(
            hub_id="registry_remote_001",
            offer_id="offer_ignored",
            category="active",
        ),
    )
    policy = make_retained_audit_compaction_policy(
        policy_id="audit_compaction_policy_001",
        hub_id="registry_chat_001",
        compact_statuses=["expired"],
    )

    decision = classify_retained_audit_records_for_compaction(records, policy)

    assert isinstance(policy, RetainedAuditCompactionPolicy)
    assert isinstance(decision, RetainedAuditCompactionDecision)
    assert decision.retained_record_keys == (_explanation_key(0, records[0]),)
    assert decision.compaction_candidate_record_keys == (
        _explanation_key(1, records[1]),
    )
    assert decision.ignored_record_keys == (_explanation_key(2, records[2]),)
    assert decision.by_decision_category == {
        "compaction_candidate": 1,
        "ignored": 1,
        "retained": 1,
    }


def test_compaction_history_status_reason_source_and_hub_filters_work():
    transition = make_stream_offer_status_transition(
        offer_id="offer_transition",
        previous_status="held",
        new_status="expired",
        reason="expired",
        hub_id="registry_chat_001",
        metadata={"source": "lifecycle_apply_result"},
        sequence=2,
    )
    records = (
        _explanation(
            offer_id="offer_active",
            category="active",
            reason="active_by_plan",
            source="lifecycle_plan",
        ),
        _explanation(
            offer_id="offer_applied",
            category="applied",
            reason="applied_by_result",
            status="applied",
            source="lifecycle_apply_result",
        ),
        transition,
    )
    policy = make_retained_audit_compaction_policy(
        policy_id="audit_compaction_policy_001",
        hub_id="registry_chat_001",
        history_types=[
            "stream_offer_lifecycle_explanation",
            "stream_offer_status_transition",
        ],
        retain_reasons=["active_by_plan"],
        compact_statuses=["expired"],
        compact_sources=["lifecycle_apply_result"],
    )

    decision = classify_retained_audit_records_for_compaction(records, policy)

    assert decision.history_type == "mixed"
    assert decision.retained_record_keys == (_explanation_key(0, records[0]),)
    assert decision.compaction_candidate_record_keys == (
        _explanation_key(1, records[1]),
        _transition_key(2, transition),
    )
    assert decision.candidate_by_history_type == {
        "stream_offer_lifecycle_explanation": 1,
        "stream_offer_status_transition": 1,
    }
    assert decision.candidate_by_reason == {
        "applied_by_result": 1,
        "expired": 1,
    }
    assert decision.candidate_by_status == {
        "applied": 1,
        "expired": 1,
    }
    assert decision.candidate_by_source == {
        "lifecycle_apply_result": 2,
    }


def test_compaction_conflicting_filters_retain_by_documented_precedence():
    explanation = _explanation(
        offer_id="offer_conflict",
        category="active",
        reason="active_by_plan",
        source="lifecycle_plan",
    )
    policy = make_retained_audit_compaction_policy(
        policy_id="audit_compaction_policy_001",
        hub_id="registry_chat_001",
        retain_statuses=["active"],
        compact_reasons=["active_by_plan"],
        compact_sources=["lifecycle_plan"],
    )

    decision = classify_retained_audit_records_for_compaction(
        (explanation,),
        policy,
    )

    assert decision.retained_record_keys == (_explanation_key(0, explanation),)
    assert decision.compaction_candidate_record_keys == ()
    assert decision.metadata["filter_precedence"] == (
        "retain_filters_before_compact_filters"
    )


def test_compaction_max_records_caps_retained_records_deterministically():
    records = (
        _explanation(offer_id="offer_001", category="active"),
        _explanation(offer_id="offer_002", category="terminal"),
        _explanation(offer_id="offer_003", category="applied", status="applied"),
    )
    policy = make_retained_audit_compaction_policy(
        policy_id="audit_compaction_policy_001",
        hub_id="registry_chat_001",
        max_records=1,
    )

    decision = classify_retained_audit_records_for_compaction(records, policy)

    assert decision.retained_record_keys == (_explanation_key(0, records[0]),)
    assert decision.compaction_candidate_record_keys == (
        _explanation_key(1, records[1]),
        _explanation_key(2, records[2]),
    )
    assert decision.metadata["max_records_applied"] is True


def test_compaction_empty_inputs_produce_deterministic_empty_decision():
    policy = make_retained_audit_compaction_policy(
        policy_id="audit_compaction_policy_001",
        hub_id="registry_chat_001",
        history_types=["stream_offer_lifecycle_explanation"],
        metadata={"labels": ("audit",)},
    )

    decision = classify_retained_audit_records_for_compaction((), policy)
    summary = summarize_retained_audit_compaction_decision(decision)
    summary["metadata"]["filter_precedence"] = "mutated"

    assert policy.metadata["labels"] == ["audit"]
    assert decision.to_summary() == {
        "hub_id": "registry_chat_001",
        "policy_id": "audit_compaction_policy_001",
        "history_type": "stream_offer_lifecycle_explanation",
        "retained_record_keys": [],
        "compaction_candidate_record_keys": [],
        "ignored_record_keys": [],
        "by_decision_category": {
            "compaction_candidate": 0,
            "ignored": 0,
            "retained": 0,
        },
        "candidate_by_history_type": {},
        "candidate_by_reason": {},
        "candidate_by_status": {},
        "candidate_by_source": {},
        "metadata": {
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
            "max_records_applied": False,
            "supported_history_types": [
                "stream_offer_lifecycle_explanation",
                "stream_offer_status_transition",
                "rendezvous_poll_result",
                "lane_admission_decision",
                "encrypted_delivery_result",
                "encryption_policy_decision",
                "message_delivery_result",
            ],
            "unsupported_records_ignored": False,
        },
    }
    json.dumps(summary, sort_keys=True)


def test_compaction_classification_reads_explicit_history_without_mutating_it():
    hub = RegistryHub(hub_id="registry_chat_001", scope_path="global.chat")
    explanations = (
        _explanation(offer_id="offer_keep", category="active"),
        _explanation(
            offer_id="offer_candidate",
            category="expired",
            reason="expired_by_plan",
            status="expired",
        ),
    )
    transition = make_stream_offer_status_transition(
        offer_id="offer_transition",
        previous_status="held",
        new_status="denied",
        reason="manual_deny",
        hub_id=hub.hub_id,
        metadata={"source": "manual_review"},
        sequence=1,
    )
    record_stream_offer_lifecycle_explanations(hub, explanations)
    record_stream_offer_status_transition(hub, transition)
    explanation_history_before = deepcopy(
        summarize_stream_offer_lifecycle_explanation_history(hub)
    )
    transition_history_before = deepcopy(summarize_stream_offer_status_transitions(hub))
    policy = make_retained_audit_compaction_policy(
        policy_id="audit_compaction_policy_001",
        hub_id=hub.hub_id,
        compact_statuses=["expired", "denied"],
    )

    decision = classify_retained_audit_records_for_compaction(
        (
            *hub.stream_offer_lifecycle_explanation_history,
            *hub.stream_offer_status_transition_history,
        ),
        policy,
    )

    assert decision.retained_record_keys == (_explanation_key(0, explanations[0]),)
    assert decision.compaction_candidate_record_keys == (
        _explanation_key(1, explanations[1]),
        _transition_key(2, transition),
    )
    assert (
        summarize_stream_offer_lifecycle_explanation_history(hub)
        == explanation_history_before
    )
    assert summarize_stream_offer_status_transitions(hub) == transition_history_before
    assert hub.stream_offer_lifecycle_explanation_history == list(explanations)
    assert hub.stream_offer_status_transition_history == [transition]


def test_compaction_unsupported_records_are_ignored_deterministically():
    policy = make_retained_audit_compaction_policy(
        policy_id="audit_compaction_policy_001",
        hub_id="registry_chat_001",
    )

    decision = classify_retained_audit_records_for_compaction(
        ({"unsupported": True},),
        policy,
    )

    assert decision.retained_record_keys == ()
    assert decision.compaction_candidate_record_keys == ()
    assert decision.ignored_record_keys == ("unsupported:0:dict",)
    assert decision.metadata["unsupported_records_ignored"] is True


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
