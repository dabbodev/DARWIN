"""Focused v1.7 retained-audit coverage for poll and admission histories."""

from __future__ import annotations

from darwin.models import (
    LaneAdmissionDecision,
    RegistryHub,
    RendezvousPollResult,
    RetainedAuditCompactionDecision,
)
from darwin.registry import (
    SUPPORTED_RETAINED_AUDIT_HISTORY_TYPES,
    apply_retained_audit_compaction_decision,
    classify_retained_audit_records_for_compaction,
    make_retained_audit_compaction_policy,
    record_lane_admission_decision,
    record_rendezvous_poll_result,
    summarize_retained_audit_replay,
)


def test_poll_and_admission_classification_maps_owners_and_fields():
    records = (
        _poll(
            request_id="request_keep",
            matched_offer_ids=("offer_b", "offer_a"),
            status="matched",
            reason="offers_available",
            source="poll_keep",
        ),
        _poll(
            request_id="request_compact",
            status="empty",
            reason="no_discoverable_offers",
            source="poll_compact",
        ),
        _poll(
            request_id="request_foreign",
            parent_hub_id="registry_remote_001",
            status="empty",
            reason="no_discoverable_offers",
            source="poll_foreign",
        ),
        _admission(
            decision_id="decision_compact",
            request_id="request_compact",
            offer_id="offer_admission",
            status="deny",
            reason="explicit_lane_denied",
            source="admission_compact",
        ),
        _admission(
            decision_id="decision_missing_hub",
            hub_id=None,
            request_id=None,
            offer_id=None,
            status="hold",
            reason="default_hold",
            source="admission_missing",
        ),
    )
    policy = make_retained_audit_compaction_policy(
        policy_id="audit_compaction_policy_170",
        hub_id="registry_chat_001",
        history_types=["rendezvous_poll_result", "lane_admission_decision"],
        compact_statuses=["empty", "deny"],
    )

    decision = classify_retained_audit_records_for_compaction(records, policy)

    assert SUPPORTED_RETAINED_AUDIT_HISTORY_TYPES == (
        "stream_offer_lifecycle_explanation",
        "stream_offer_status_transition",
        "rendezvous_poll_result",
        "lane_admission_decision",
        "encrypted_delivery_result",
        "encryption_policy_decision",
    )
    assert decision.history_type == "mixed"
    assert decision.retained_record_keys == (_poll_key(0, records[0]),)
    assert decision.compaction_candidate_record_keys == (
        _poll_key(1, records[1]),
        _admission_key(3, records[3]),
    )
    assert decision.ignored_record_keys == (
        _poll_key(2, records[2]),
        _admission_key(4, records[4]),
    )
    assert decision.candidate_by_history_type == {
        "lane_admission_decision": 1,
        "rendezvous_poll_result": 1,
    }
    assert decision.candidate_by_reason == {
        "explicit_lane_denied": 1,
        "no_discoverable_offers": 1,
    }
    assert decision.candidate_by_status == {"deny": 1, "empty": 1}
    assert decision.candidate_by_source == {
        "admission_compact": 1,
        "poll_compact": 1,
    }


def test_poll_and_admission_replay_groups_requests_without_expanding_poll_offers():
    records = (
        _poll(
            request_id="request_shared",
            matched_offer_ids=("offer_poll_a", "offer_poll_b"),
            status="matched",
            reason="offers_available",
            source="poll_source",
        ),
        _poll(
            request_id="request_zeta",
            status="empty",
            reason="no_discoverable_offers",
            source="poll_source",
        ),
        _admission(
            decision_id="decision_shared",
            request_id="request_shared",
            offer_id="offer_admission_a",
            source="admission_source",
        ),
        _admission(
            decision_id="decision_without_request",
            request_id=None,
            offer_id="offer_admission_b",
            status="hold",
            reason="default_hold",
            source=None,
        ),
    )

    summary = summarize_retained_audit_replay(
        records,
        hub_id="registry_chat_001",
        metadata={"labels": ("v1.7",)},
    )

    assert summary.record_keys == tuple(
        _poll_key(index, record)
        if isinstance(record, RendezvousPollResult)
        else _admission_key(index, record)
        for index, record in enumerate(records)
    )
    assert summary.by_request_id == {
        "request_shared": 2,
        "request_zeta": 1,
    }
    assert summary.by_offer_id == {
        "offer_admission_a": 1,
        "offer_admission_b": 1,
    }
    assert summary.by_source == {
        "admission_source": 1,
        "none": 1,
        "poll_source": 2,
    }
    assert summary.by_status == {
        "empty": 1,
        "hold": 1,
        "matched": 1,
        "pass_down": 1,
    }
    assert summary.by_reason == {
        "accepted": 1,
        "default_hold": 1,
        "no_discoverable_offers": 1,
        "offers_available": 1,
    }

    copied = summary.to_summary()
    copied["by_request_id"]["request_shared"] = 99
    copied["metadata"]["labels"].append("mutated")
    assert summary.by_request_id == {
        "request_shared": 2,
        "request_zeta": 1,
    }
    assert summary.metadata["labels"] == ["v1.7"]


def test_poll_apply_is_explicit_isolated_ordered_and_reports_stale_keys():
    hub = RegistryHub(hub_id="registry_chat_001", scope_path="global.chat")
    poll_keep = _poll(request_id="request_keep", source="poll_keep")
    poll_compact = _poll(
        request_id="request_compact",
        status="empty",
        reason="no_discoverable_offers",
        source="poll_compact",
    )
    poll_after = _poll(request_id="request_after", source="poll_after")
    admission = _admission(
        decision_id="decision_unchanged",
        request_id="request_admission",
        offer_id="offer_admission",
    )
    for poll in (poll_keep, poll_compact, poll_after):
        record_rendezvous_poll_result(hub, poll)
    record_lane_admission_decision(hub, admission)
    policy = make_retained_audit_compaction_policy(
        policy_id="poll_compaction_policy_170",
        hub_id=hub.hub_id,
        history_types=["rendezvous_poll_result"],
        compact_statuses=["empty"],
    )
    classified = classify_retained_audit_records_for_compaction(
        hub.rendezvous_poll_result_history,
        policy,
    )
    stale_key = (
        "rendezvous_poll:99:registry_chat_001:hub_private_child:"
        "request_stale:global.chat:1:empty:no_discoverable_offers:none"
    )
    decision = RetainedAuditCompactionDecision(
        hub_id=classified.hub_id,
        policy_id=classified.policy_id,
        history_type=classified.history_type,
        retained_record_keys=classified.retained_record_keys,
        compaction_candidate_record_keys=(
            *classified.compaction_candidate_record_keys,
            stale_key,
        ),
        ignored_record_keys=classified.ignored_record_keys,
    )

    result = apply_retained_audit_compaction_decision(hub, decision)

    assert result.compacted_record_keys == (_poll_key(1, poll_compact),)
    assert result.retained_record_keys == (
        _poll_key(0, poll_keep),
        _poll_key(2, poll_after),
    )
    assert result.missing_record_keys == (stale_key,)
    assert hub.rendezvous_poll_result_history == [poll_keep, poll_after]
    assert hub.lane_admission_decision_history == [admission]
    assert result.metadata["polling_history_mutated"] is True
    assert result.metadata["admission_history_mutated"] is False

    repeated = apply_retained_audit_compaction_decision(hub, decision)
    assert repeated.compacted_record_keys == ()
    assert repeated.missing_record_keys == (
        _poll_key(1, poll_compact),
        stale_key,
    )
    assert repeated.metadata["polling_history_mutated"] is False
    assert repeated.metadata["registry_hub_mutated"] is False


def test_admission_apply_mutates_only_admission_history_and_mixed_is_noop():
    hub = RegistryHub(hub_id="registry_chat_001", scope_path="global.chat")
    poll = _poll(request_id="request_poll")
    admission_keep = _admission(
        decision_id="decision_keep",
        request_id="request_keep",
        offer_id="offer_keep",
    )
    admission_compact = _admission(
        decision_id="decision_compact",
        request_id="request_compact",
        offer_id="offer_compact",
        status="deny",
        reason="explicit_lane_denied",
    )
    record_rendezvous_poll_result(hub, poll)
    record_lane_admission_decision(hub, admission_keep)
    record_lane_admission_decision(hub, admission_compact)
    policy = make_retained_audit_compaction_policy(
        policy_id="admission_compaction_policy_170",
        hub_id=hub.hub_id,
        history_types=["lane_admission_decision"],
        compact_statuses=["deny"],
    )
    decision = classify_retained_audit_records_for_compaction(
        hub.lane_admission_decision_history,
        policy,
    )
    mixed = RetainedAuditCompactionDecision(
        hub_id=hub.hub_id,
        policy_id="mixed_compaction_policy_170",
        history_type="mixed",
        compaction_candidate_record_keys=(
            _poll_key(0, poll),
            _admission_key(1, admission_compact),
        ),
    )

    mixed_result = apply_retained_audit_compaction_decision(hub, mixed)
    assert mixed_result.unsupported_record_keys == mixed.compaction_candidate_record_keys
    assert mixed_result.metadata["unsupported_history_type"] is True
    assert hub.rendezvous_poll_result_history == [poll]
    assert hub.lane_admission_decision_history == [
        admission_keep,
        admission_compact,
    ]

    result = apply_retained_audit_compaction_decision(hub, decision)
    assert result.compacted_record_keys == (_admission_key(1, admission_compact),)
    assert result.retained_record_keys == (_admission_key(0, admission_keep),)
    assert hub.rendezvous_poll_result_history == [poll]
    assert hub.lane_admission_decision_history == [admission_keep]
    assert result.metadata["polling_history_mutated"] is False
    assert result.metadata["admission_history_mutated"] is True


def _poll(
    *,
    request_id: str,
    parent_hub_id: str = "registry_chat_001",
    polling_hub_id: str = "hub_private_child",
    matched_offer_ids: tuple[str, ...] = ("offer_default",),
    status: str = "matched",
    reason: str = "offers_available",
    source: str | None = "poll_source",
) -> RendezvousPollResult:
    metadata = {} if source is None else {"source": source}
    return RendezvousPollResult(
        request_id=request_id,
        polling_hub_id=polling_hub_id,
        parent_hub_id=parent_hub_id,
        target_scope="global.chat",
        visibility_tier=1,
        matched_offer_ids=matched_offer_ids if status == "matched" else (),
        status=status,
        reason=reason,
        metadata=metadata,
    )


def _admission(
    *,
    decision_id: str,
    hub_id: str | None = "registry_chat_001",
    policy_id: str | None = "policy_chat_001",
    offer_id: str | None,
    request_id: str | None,
    status: str = "pass_down",
    reason: str = "accepted",
    source: str | None = "admission_source",
) -> LaneAdmissionDecision:
    metadata = {} if source is None else {"source": source}
    return LaneAdmissionDecision(
        decision_id=decision_id,
        policy_id=policy_id,
        offer_id=offer_id,
        request_id=request_id,
        hub_id=hub_id,
        requester_id=None,
        target_handle=None,
        target_scope=None,
        lane_signature=None,
        status=status,
        reason=reason,
        allowed=status == "pass_down",
        metadata=metadata,
    )


def _poll_key(index: int, record: object) -> str:
    matched_offer_ids = ",".join(record.matched_offer_ids) or "none"
    return (
        f"rendezvous_poll:{index}:{record.parent_hub_id}:"
        f"{record.polling_hub_id}:{record.request_id}:{record.target_scope}:"
        f"{record.visibility_tier.tier}:{record.status.status}:{record.reason}:"
        f"{matched_offer_ids}"
    )


def _admission_key(index: int, record: object) -> str:
    return (
        f"lane_admission:{index}:{record.hub_id or 'none'}:{record.decision_id}:"
        f"{record.policy_id or 'none'}:{record.offer_id or 'none'}:"
        f"{record.request_id or 'none'}:{record.status.status}:"
        f"{record.reason.reason}"
    )
