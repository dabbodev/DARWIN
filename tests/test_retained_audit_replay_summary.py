"""Tests for retained audit replay summary helpers."""

from __future__ import annotations

import json
from copy import deepcopy

from darwin.models import (
    RegistryHub,
    RetainedAuditReplaySummary,
    StreamOfferLifecycleExplanation,
)
from darwin.registry import (
    classify_retained_audit_records_for_compaction,
    make_retained_audit_compaction_policy,
    make_stream_offer_status_transition,
    record_stream_offer_lifecycle_explanations,
    record_stream_offer_status_transition,
    summarize_retained_audit_replay,
    summarize_retained_audit_replay_by_history_type,
    summarize_retained_audit_replay_by_reason,
    summarize_stream_offer_lifecycle_explanation_history,
    summarize_stream_offer_status_transitions,
)


def test_replay_summary_preserves_order_and_groups_records():
    explanation = _explanation(
        offer_id="offer_b",
        category="active",
        reason="active_by_plan",
        status="active",
        source="lifecycle_plan",
    )
    transition = make_stream_offer_status_transition(
        offer_id="offer_a",
        previous_status="held",
        new_status="denied",
        reason="manual_deny",
        hub_id="registry_chat_001",
        metadata={"source": "manual_review"},
        sequence=3,
    )
    records = (explanation, transition)

    summary = summarize_retained_audit_replay(
        records,
        hub_id="registry_chat_001",
    )

    assert isinstance(summary, RetainedAuditReplaySummary)
    assert summary.history_type == "mixed"
    assert summary.record_count == 2
    assert summary.record_keys == (
        _explanation_key(0, explanation),
        _transition_key(1, transition),
    )
    assert summary.first_record_key == _explanation_key(0, explanation)
    assert summary.last_record_key == _transition_key(1, transition)
    assert summary.by_status == {"active": 1, "denied": 1}
    assert summary.by_reason == {"active_by_plan": 1, "manual_deny": 1}
    assert summary.by_source == {"lifecycle_plan": 1, "manual_review": 1}
    assert summary.by_offer_id == {"offer_a": 1, "offer_b": 1}
    assert summarize_retained_audit_replay_by_history_type(
        records,
        hub_id="registry_chat_001",
    ) == {
        "stream_offer_lifecycle_explanation": 1,
        "stream_offer_status_transition": 1,
    }
    assert summarize_retained_audit_replay_by_reason(
        records,
        hub_id="registry_chat_001",
    ) == {"active_by_plan": 1, "manual_deny": 1}


def test_replay_summary_can_filter_to_one_history_type():
    records = (
        _explanation(offer_id="offer_exp", category="expired"),
        make_stream_offer_status_transition(
            offer_id="offer_trans",
            previous_status="held",
            new_status="expired",
            reason="expired",
            hub_id="registry_chat_001",
            metadata={"source": "lifecycle_apply_result"},
        ),
    )

    summary = summarize_retained_audit_replay(
        records,
        hub_id="registry_chat_001",
        history_type="stream_offer_status_transition",
    )

    assert summary.history_type == "stream_offer_status_transition"
    assert summary.record_count == 1
    assert summary.record_keys == (_transition_key(1, records[1]),)
    assert summary.by_status == {"expired": 1}
    assert summary.by_source == {"lifecycle_apply_result": 1}
    assert summary.metadata["filtered_record_keys"] == [_explanation_key(0, records[0])]


def test_replay_summary_empty_inputs_are_deterministic():
    summary = summarize_retained_audit_replay((), hub_id="registry_chat_001")

    assert summary.to_summary() == {
        "hub_id": "registry_chat_001",
        "history_type": "mixed",
        "record_count": 0,
        "record_keys": [],
        "by_status": {},
        "by_reason": {},
        "by_source": {},
        "by_offer_id": {},
        "by_request_id": {},
        "by_message_id": {},
        "by_mailbox_id": {},
        "first_record_key": None,
        "last_record_key": None,
        "metadata": {
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
            "supported_history_types": [
                "stream_offer_lifecycle_explanation",
                "stream_offer_status_transition",
                "rendezvous_poll_result",
                "lane_admission_decision",
                "encrypted_delivery_result",
            ],
            "history_type_filter": None,
            "decision_category_filter": "all",
            "ignored_record_keys": [],
            "filtered_record_keys": [],
            "unsupported_records_ignored": False,
            "wrong_hub_records_ignored": False,
            "filtered_records_ignored": False,
        },
    }
    assert summarize_retained_audit_replay_by_history_type(
        (),
        hub_id="registry_chat_001",
    ) == {}
    assert summarize_retained_audit_replay_by_reason(
        (),
        hub_id="registry_chat_001",
    ) == {}
    json.dumps(summary.to_summary(), sort_keys=True)


def test_replay_summary_unsupported_records_are_ignored_deterministically():
    summary = summarize_retained_audit_replay(
        ({"unsupported": True},),
        hub_id="registry_chat_001",
    )

    assert summary.record_count == 0
    assert summary.record_keys == ()
    assert summary.metadata["ignored_record_keys"] == ["unsupported:0:dict"]
    assert summary.metadata["unsupported_records_ignored"] is True


def test_replay_summary_helpers_are_read_only_and_copied():
    hub = RegistryHub(hub_id="registry_chat_001", scope_path="global.chat")
    explanations = (
        _explanation(offer_id="offer_keep", category="active"),
        _explanation(offer_id="offer_candidate", category="expired"),
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

    summary = summarize_retained_audit_replay(
        (
            *hub.stream_offer_lifecycle_explanation_history,
            *hub.stream_offer_status_transition_history,
        ),
        hub_id=hub.hub_id,
        metadata={"labels": ("audit",)},
    )
    summary_dict = summary.to_summary()
    summary_dict["metadata"]["labels"].append("mutated")

    assert (
        summarize_stream_offer_lifecycle_explanation_history(hub)
        == explanation_history_before
    )
    assert summarize_stream_offer_status_transitions(hub) == transition_history_before
    assert hub.stream_offer_lifecycle_explanation_history == list(explanations)
    assert hub.stream_offer_status_transition_history == [transition]
    assert summary.metadata["labels"] == ["audit"]


def test_replay_summary_can_filter_with_compaction_decision_keys():
    records = (
        _explanation(offer_id="offer_keep", category="active"),
        _explanation(
            offer_id="offer_candidate",
            category="expired",
            reason="expired_by_plan",
            status="expired",
        ),
    )
    policy = make_retained_audit_compaction_policy(
        policy_id="audit_compaction_policy_001",
        hub_id="registry_chat_001",
        compact_statuses=["expired"],
    )
    decision = classify_retained_audit_records_for_compaction(records, policy)

    retained_summary = summarize_retained_audit_replay(
        records,
        hub_id="registry_chat_001",
        decision=decision,
        decision_category="retained",
    )
    candidate_summary = summarize_retained_audit_replay(
        records,
        hub_id="registry_chat_001",
        decision=decision,
        decision_category="compaction_candidate",
    )
    all_summary = summarize_retained_audit_replay(
        records,
        hub_id="registry_chat_001",
        decision=decision,
    )

    assert retained_summary.record_keys == (_explanation_key(0, records[0]),)
    assert candidate_summary.record_keys == (_explanation_key(1, records[1]),)
    assert all_summary.record_count == 2
    assert retained_summary.metadata["decision_category_filter"] == "retained"
    assert candidate_summary.metadata["decision_category_filter"] == (
        "compaction_candidate"
    )


def test_replay_summary_does_not_group_v1_6_transition_request_ids():
    transition = make_stream_offer_status_transition(
        offer_id="offer_transition",
        previous_status="held",
        new_status="denied",
        reason="manual_deny",
        hub_id="registry_chat_001",
        request_id="request_v1_6_transition",
    )

    summary = summarize_retained_audit_replay(
        (transition,),
        hub_id="registry_chat_001",
    )

    assert summary.record_keys == (_transition_key(0, transition),)
    assert summary.by_request_id == {}


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
