"""Focused v1.10 retained-audit coverage for direct message delivery results."""

from __future__ import annotations

from copy import deepcopy

import pytest

from darwin.models import (
    MessageDeliveryResult,
    MessageEnvelope,
    RegistryHub,
    RetainedAuditCompactionDecision,
    RetainedAuditReplaySummary,
)
from darwin.registry import (
    SUPPORTED_RETAINED_AUDIT_HISTORY_TYPES,
    apply_retained_audit_compaction_decision,
    classify_retained_audit_records_for_compaction,
    deliver_message_to_mailbox,
    make_retained_audit_compaction_policy,
    summarize_retained_audit_replay,
)


def test_message_delivery_classification_maps_owner_fields_and_exact_keys():
    records = (
        _result(
            message_id="message_keep",
            recipient_address="darwin://global.chat.neo/inbox",
            mailbox_id="mailbox_neo",
            status="delivered",
            reason=None,
            source="delivery_keep",
        ),
        _result(
            message_id="message_compact",
            recipient_address="darwin://global.chat.trinity/inbox",
            mailbox_id="mailbox_trinity",
            status="queued",
            reason="endpoint_unavailable",
            source="delivery_compact",
        ),
        _result(
            message_id="message_foreign",
            registry_hub="registry_remote_001",
            status="rejected",
            reason="lane_not_registered",
        ),
        _result(
            message_id="message_missing_owner",
            registry_hub=None,
            status="rejected",
            reason="lane_not_registered",
        ),
        _result(
            message_id="message_non_string_owner",
            registry_hub=42,
            status="rejected",
            reason="lane_not_registered",
        ),
    )
    policy = make_retained_audit_compaction_policy(
        policy_id="message_delivery_audit_policy_110",
        hub_id="registry_chat_001",
        history_types=["message_delivery_result"],
        retain_statuses=["delivered"],
        compact_statuses=["queued", "rejected"],
    )

    decision = classify_retained_audit_records_for_compaction(records, policy)

    assert SUPPORTED_RETAINED_AUDIT_HISTORY_TYPES == (
        "stream_offer_lifecycle_explanation",
        "stream_offer_status_transition",
        "rendezvous_poll_result",
        "lane_admission_decision",
        "encrypted_delivery_result",
        "encryption_policy_decision",
        "message_delivery_result",
    )
    assert decision.history_type == "message_delivery_result"
    assert decision.retained_record_keys == (_key(0, records[0]),)
    assert decision.compaction_candidate_record_keys == (_key(1, records[1]),)
    assert decision.ignored_record_keys == (
        _key(2, records[2]),
        _key(3, records[3]),
        _key(4, records[4]),
    )
    assert decision.candidate_by_history_type == {"message_delivery_result": 1}
    assert decision.candidate_by_reason == {"endpoint_unavailable": 1}
    assert decision.candidate_by_status == {"queued": 1}
    assert decision.candidate_by_source == {"delivery_compact": 1}


def test_message_delivery_filter_precedence_and_max_records_preserve_order():
    records = (
        _result(
            message_id="message_first",
            status="delivered",
            reason=None,
            source="always_keep",
        ),
        _result(message_id="message_second", status="delivered", reason=None),
        _result(
            message_id="message_third",
            status="rejected",
            reason="lane_not_registered",
        ),
    )
    policy = make_retained_audit_compaction_policy(
        policy_id="message_delivery_audit_cap_110",
        hub_id="registry_chat_001",
        history_types=["message_delivery_result"],
        retain_sources=["always_keep"],
        compact_sources=["always_keep"],
        max_records=1,
    )

    decision = classify_retained_audit_records_for_compaction(records, policy)

    assert decision.retained_record_keys == (_key(0, records[0]),)
    assert decision.compaction_candidate_record_keys == (
        _key(1, records[1]),
        _key(2, records[2]),
    )


def test_message_delivery_replay_uses_existing_dimensions_and_returns_copies():
    delivered = _result(
        message_id="message_zeta",
        mailbox_id="mailbox_shared",
        lane_signature="video_chat:v1",
        status="delivered",
        reason=None,
        source="zeta",
    )
    queued = _result(
        message_id="message_alpha",
        mailbox_id="mailbox_shared",
        lane_signature="basic_messaging:v1",
        status="queued",
        reason="endpoint_unavailable",
        source="alpha",
    )
    rejected = _result(
        message_id="message_none",
        recipient_address="darwin://global.chat.missing/inbox",
        mailbox_id=None,
        lane_signature="file_transfer:v1",
        status="rejected",
        reason="mailbox_not_found",
    )

    summary = summarize_retained_audit_replay(
        (delivered, queued, rejected),
        hub_id="registry_chat_001",
        metadata={"labels": ("v1.10",)},
    )

    assert summary.by_message_id == {
        "message_alpha": 1,
        "message_none": 1,
        "message_zeta": 1,
    }
    assert summary.by_mailbox_id == {"mailbox_shared": 2}
    assert summary.by_lane_signature == {
        "basic_messaging:v1": 1,
        "file_transfer:v1": 1,
        "video_chat:v1": 1,
    }
    assert summary.by_status == {"delivered": 1, "queued": 1, "rejected": 1}
    assert summary.by_reason == {
        "endpoint_unavailable": 1,
        "mailbox_not_found": 1,
        "none": 1,
    }
    assert summary.by_source == {"alpha": 1, "none": 1, "zeta": 1}
    assert summary.by_request_id == {}
    assert summary.by_offer_id == {}
    assert summary.by_policy_id == {}

    copied = summary.to_summary()
    copied["by_message_id"]["message_alpha"] = 99
    copied["by_mailbox_id"]["mailbox_shared"] = 99
    copied["by_lane_signature"]["basic_messaging:v1"] = 99
    copied["metadata"]["labels"].append("mutated")
    assert summary.by_message_id["message_alpha"] == 1
    assert summary.by_mailbox_id["mailbox_shared"] == 2
    assert summary.by_lane_signature["basic_messaging:v1"] == 1
    assert summary.metadata["labels"] == ["v1.10"]


def test_replay_model_still_validates_existing_message_mailbox_lane_counts():
    summary = RetainedAuditReplaySummary(
        hub_id="registry_chat_001",
        history_type="message_delivery_result",
        by_message_id={"message_zeta": 2, "message_alpha": 1},
        by_mailbox_id={"mailbox_zeta": 2, "mailbox_alpha": 1},
        by_lane_signature={"video_chat:v1": 2, "basic_messaging:v1": 1},
    )

    assert list(summary.by_message_id) == ["message_alpha", "message_zeta"]
    assert list(summary.by_mailbox_id) == ["mailbox_alpha", "mailbox_zeta"]
    assert list(summary.by_lane_signature) == [
        "basic_messaging:v1",
        "video_chat:v1",
    ]
    with pytest.raises(ValueError, match="greater than or equal to 0"):
        RetainedAuditReplaySummary(
            hub_id="registry_chat_001",
            history_type="message_delivery_result",
            by_message_id={"message_invalid": -1},
        )


def test_message_delivery_apply_is_isolated_reports_stale_and_is_repeatable():
    hub = RegistryHub(hub_id="registry_chat_001", scope_path="global.chat")
    keep = _result(message_id="message_keep", status="delivered", reason=None)
    compact = _result(
        message_id="message_compact",
        status="queued",
        reason="endpoint_unavailable",
    )
    after = _result(message_id="message_after", status="delivered", reason=None)
    hub.message_delivery_results.extend((keep, compact, after))
    hub.message_inboxes["mailbox_neo"] = [{"message_id": "message_keep"}]
    hub.encrypted_delivery_result_history.append({"request_id": "request_unchanged"})
    hub.encryption_policy_decision_history.append({"policy_id": "policy_unchanged"})
    hub.held_stream_offers.append({"offer_id": "offer_unchanged"})
    inboxes_before = deepcopy(hub.message_inboxes)
    encrypted_before = deepcopy(hub.encrypted_delivery_result_history)
    policy_before = deepcopy(hub.encryption_policy_decision_history)
    held_before = deepcopy(hub.held_stream_offers)
    policy = make_retained_audit_compaction_policy(
        policy_id="message_delivery_audit_apply_110",
        hub_id=hub.hub_id,
        history_types=["message_delivery_result"],
        compact_statuses=["queued"],
    )
    classified = classify_retained_audit_records_for_compaction(
        hub.message_delivery_results,
        policy,
    )
    stale_key = (
        "message_delivery_result:99:registry_chat_001:message_stale:"
        "darwin://global.chat.neo/inbox:mailbox_neo:basic_messaging:v1:"
        "queued:endpoint_unavailable"
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

    assert result.compacted_record_keys == (_key(1, compact),)
    assert result.missing_record_keys == (stale_key,)
    assert hub.message_delivery_results == [keep, after]
    assert hub.message_inboxes == inboxes_before
    assert hub.encrypted_delivery_result_history == encrypted_before
    assert hub.encryption_policy_decision_history == policy_before
    assert hub.held_stream_offers == held_before
    assert result.metadata["message_delivery_history_mutated"] is True
    assert result.metadata["delivery_state_mutated"] is False
    assert result.metadata["encrypted_delivery_history_mutated"] is False
    assert result.metadata["encryption_policy_history_mutated"] is False

    repeated = apply_retained_audit_compaction_decision(hub, decision)
    assert repeated.compacted_record_keys == ()
    assert repeated.missing_record_keys == (_key(1, compact), stale_key)
    assert repeated.metadata["message_delivery_history_mutated"] is False
    assert hub.message_inboxes == inboxes_before


def test_delivery_helper_adds_registry_owner_without_changing_delivery_behavior():
    hub = RegistryHub(hub_id="registry_chat_001", scope_path="global.chat")
    envelope = MessageEnvelope(
        message_id="message_owned",
        sender_id="device_sender",
        recipient_address="darwin://global.chat.neo/inbox",
        lane_signature="basic_messaging:v1",
        payload_kind="text",
        payload="hello",
    )

    result = deliver_message_to_mailbox(hub, envelope)

    assert result.status.status == "rejected"
    assert result.reason.reason == "lane_not_registered"
    assert result.metadata["registry_hub"] == hub.hub_id
    assert result.to_summary()["metadata"]["registry_hub"] == hub.hub_id
    assert hub.message_delivery_results == [result]


def test_mixed_apply_remains_unsupported_for_message_delivery_history():
    hub = RegistryHub(hub_id="registry_chat_001", scope_path="global.chat")
    record = _result(message_id="message_unchanged")
    hub.message_delivery_results.append(record)
    mixed = RetainedAuditCompactionDecision(
        hub_id=hub.hub_id,
        policy_id="mixed_policy_110",
        history_type="mixed",
        compaction_candidate_record_keys=(_key(0, record),),
    )

    applied = apply_retained_audit_compaction_decision(hub, mixed)

    assert applied.unsupported_record_keys == mixed.compaction_candidate_record_keys
    assert applied.metadata["unsupported_history_type"] is True
    assert applied.metadata["message_delivery_history_mutated"] is False
    assert hub.message_delivery_results == [record]


def _result(
    *,
    message_id: str,
    registry_hub: str | int | None = "registry_chat_001",
    recipient_address: str = "darwin://global.chat.neo/inbox",
    mailbox_id: str | None = "mailbox_neo",
    lane_signature: str = "basic_messaging:v1",
    status: str = "delivered",
    reason: str | None = None,
    source: str | None = None,
) -> MessageDeliveryResult:
    metadata: dict[str, object] = {}
    if registry_hub is not None:
        metadata["registry_hub"] = registry_hub
    if source is not None:
        metadata["source"] = source
    return MessageDeliveryResult(
        message_id=message_id,
        recipient_address=recipient_address,
        resolved_mailbox_id=mailbox_id,
        target_device_id="device_target" if mailbox_id is not None else None,
        lane_signature=lane_signature,
        endpoint_id="endpoint_target" if status == "delivered" else None,
        status=status,
        reason=reason,
        fallback_action=None if status == "delivered" else "reject",
        audit_path=("retained_audit_test",),
        metadata=metadata,
    )


def _key(index: int, result: MessageDeliveryResult) -> str:
    hub_id = result.metadata.get("registry_hub")
    if not isinstance(hub_id, str):
        hub_id = "none"
    reason = "none" if result.reason is None else result.reason.reason
    return (
        f"message_delivery_result:{index}:{hub_id}:{result.message_id}:"
        f"{result.recipient_address}:{result.resolved_mailbox_id or 'none'}:"
        f"{result.lane_signature}:{result.status.status}:{reason}"
    )
