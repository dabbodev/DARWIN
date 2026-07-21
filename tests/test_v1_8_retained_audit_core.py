"""Focused v1.8 retained-audit coverage for encrypted delivery results."""

from __future__ import annotations

from copy import deepcopy

import pytest

from darwin.models import (
    EncryptedDeliveryResult,
    RegistryHub,
    RetainedAuditCompactionDecision,
    RetainedAuditReplaySummary,
)
from darwin.registry import (
    SUPPORTED_RETAINED_AUDIT_HISTORY_TYPES,
    apply_retained_audit_compaction_decision,
    classify_retained_audit_records_for_compaction,
    make_retained_audit_compaction_policy,
    summarize_retained_audit_replay,
)


def test_encrypted_delivery_classification_maps_owner_fields_and_exact_keys():
    records = (
        _result(
            request_id="request_keep",
            message_id="message_keep",
            mailbox_id="mailbox_zeta",
            status="delivered",
            reason=None,
            source="delivery_keep",
        ),
        _result(
            request_id="request_compact",
            message_id="message_compact",
            mailbox_id="mailbox_alpha",
            status="gate_blocked",
            reason="unsupported_profile",
            source="delivery_compact",
        ),
        _result(
            request_id="request_foreign",
            registry_hub="registry_remote_001",
            status="not_delivered",
            reason="delivery_not_attempted",
        ),
        _result(
            request_id="request_missing_owner",
            registry_hub=None,
            status="not_delivered",
            reason="delivery_not_attempted",
            note="delivery_not_attempted",
        ),
        _result(
            request_id="request_non_string_owner",
            registry_hub=42,
            status="not_delivered",
            reason="delivery_not_attempted",
        ),
    )
    policy = make_retained_audit_compaction_policy(
        policy_id="encrypted_audit_policy_180",
        hub_id="registry_chat_001",
        history_types=["encrypted_delivery_result"],
        retain_statuses=["delivered"],
        compact_statuses=["gate_blocked", "not_delivered"],
    )

    decision = classify_retained_audit_records_for_compaction(records, policy)

    assert SUPPORTED_RETAINED_AUDIT_HISTORY_TYPES == (
        "stream_offer_lifecycle_explanation",
        "stream_offer_status_transition",
        "rendezvous_poll_result",
        "lane_admission_decision",
        "encrypted_delivery_result",
    )
    assert decision.history_type == "encrypted_delivery_result"
    assert decision.retained_record_keys == (_key(0, records[0]),)
    assert decision.compaction_candidate_record_keys == (_key(1, records[1]),)
    assert decision.ignored_record_keys == (
        _key(2, records[2]),
        _key(3, records[3]),
        _key(4, records[4]),
    )
    assert decision.candidate_by_history_type == {"encrypted_delivery_result": 1}
    assert decision.candidate_by_reason == {"unsupported_profile": 1}
    assert decision.candidate_by_status == {"gate_blocked": 1}
    assert decision.candidate_by_source == {"delivery_compact": 1}


def test_encrypted_delivery_max_records_preserves_order_after_filtering():
    records = (
        _result(request_id="request_first", status="delivered"),
        _result(
            request_id="request_second",
            status="not_delivered",
            reason="delivery_not_attempted",
        ),
    )
    policy = make_retained_audit_compaction_policy(
        policy_id="encrypted_audit_max_policy_180",
        hub_id="registry_chat_001",
        history_types=["encrypted_delivery_result"],
        max_records=1,
    )

    decision = classify_retained_audit_records_for_compaction(records, policy)

    assert decision.retained_record_keys == (_key(0, records[0]),)
    assert decision.compaction_candidate_record_keys == (_key(1, records[1]),)


def test_encrypted_delivery_replay_groups_message_and_mailbox_ids_with_copy_isolation():
    records = (
        _result(
            request_id="request_zeta",
            message_id="message_zeta",
            mailbox_id="mailbox_shared",
            status="delivered",
            reason=None,
            source="zeta",
        ),
        _result(
            request_id="request_alpha",
            message_id="message_alpha",
            mailbox_id="mailbox_shared",
            status="gate_blocked",
            reason="unsupported_profile",
            source="alpha",
        ),
        _result(
            request_id="request_none_source",
            message_id=None,
            mailbox_id=None,
            status="not_delivered",
            reason="delivery_not_attempted",
            note="delivery_not_attempted",
        ),
    )

    summary = summarize_retained_audit_replay(
        records,
        hub_id="registry_chat_001",
        metadata={"labels": ("v1.8",)},
    )

    assert summary.record_keys == tuple(_key(index, record) for index, record in enumerate(records))
    assert summary.by_request_id == {
        "request_alpha": 1,
        "request_none_source": 1,
        "request_zeta": 1,
    }
    assert summary.by_message_id == {"message_alpha": 1, "message_zeta": 1}
    assert summary.by_mailbox_id == {"mailbox_shared": 2}
    assert summary.by_status == {"delivered": 1, "gate_blocked": 1, "not_delivered": 1}
    assert summary.by_reason == {
        "delivery_not_attempted": 1,
        "none": 1,
        "unsupported_profile": 1,
    }
    assert summary.by_source == {"alpha": 1, "none": 1, "zeta": 1}
    assert summary.by_offer_id == {}

    copied = summary.to_summary()
    copied["by_message_id"]["message_alpha"] = 99
    copied["by_mailbox_id"]["mailbox_shared"] = 99
    copied["metadata"]["labels"].append("mutated")
    assert summary.by_message_id == {"message_alpha": 1, "message_zeta": 1}
    assert summary.by_mailbox_id == {"mailbox_shared": 2}
    assert summary.metadata["labels"] == ["v1.8"]


def test_replay_model_sorts_and_validates_new_group_counts():
    summary = RetainedAuditReplaySummary(
        hub_id="registry_chat_001",
        history_type="encrypted_delivery_result",
        by_message_id={"message_zeta": 2, "message_alpha": 1},
        by_mailbox_id={"mailbox_zeta": 2, "mailbox_alpha": 1},
    )

    assert list(summary.by_message_id) == ["message_alpha", "message_zeta"]
    assert list(summary.by_mailbox_id) == ["mailbox_alpha", "mailbox_zeta"]
    with pytest.raises(ValueError, match="greater than or equal to 0"):
        RetainedAuditReplaySummary(
            hub_id="registry_chat_001",
            history_type="encrypted_delivery_result",
            by_message_id={"message_invalid": -1},
        )


def test_encrypted_delivery_apply_is_isolated_reports_stale_and_is_repeatable():
    hub = RegistryHub(hub_id="registry_chat_001", scope_path="global.chat")
    keep = _result(request_id="request_keep", status="delivered")
    compact = _result(
        request_id="request_compact",
        status="gate_blocked",
        reason="unsupported_profile",
    )
    after = _result(request_id="request_after", status="delivered")
    hub.encrypted_delivery_result_history.extend((keep, compact, after))
    hub.encryption_policy_decision_history.append({"policy_id": "policy_unchanged"})
    hub.message_delivery_results.append({"message_id": "message_unchanged"})
    hub.message_inboxes["mailbox_neo"] = [{"message_id": "message_unchanged"}]
    policy_decisions_before = deepcopy(hub.encryption_policy_decision_history)
    delivery_results_before = deepcopy(hub.message_delivery_results)
    inboxes_before = deepcopy(hub.message_inboxes)
    policy = make_retained_audit_compaction_policy(
        policy_id="encrypted_audit_apply_policy_180",
        hub_id=hub.hub_id,
        history_types=["encrypted_delivery_result"],
        compact_statuses=["gate_blocked"],
    )
    classified = classify_retained_audit_records_for_compaction(
        hub.encrypted_delivery_result_history,
        policy,
    )
    stale_key = (
        "encrypted_delivery_result:99:registry_chat_001:request_stale:none:none:"
        "none:gate_blocked:unsupported_profile"
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
    assert hub.encrypted_delivery_result_history == [keep, after]
    assert hub.encryption_policy_decision_history == policy_decisions_before
    assert hub.message_delivery_results == delivery_results_before
    assert hub.message_inboxes == inboxes_before
    assert result.metadata["encrypted_delivery_history_mutated"] is True
    assert result.metadata["delivery_state_mutated"] is False

    repeated = apply_retained_audit_compaction_decision(hub, decision)
    assert repeated.compacted_record_keys == ()
    assert repeated.missing_record_keys == (_key(1, compact), stale_key)
    assert repeated.metadata["encrypted_delivery_history_mutated"] is False
    assert hub.encryption_policy_decision_history == policy_decisions_before
    assert hub.message_delivery_results == delivery_results_before
    assert hub.message_inboxes == inboxes_before


def test_mixed_apply_remains_unsupported_and_does_not_mutate_encrypted_history():
    hub = RegistryHub(hub_id="registry_chat_001", scope_path="global.chat")
    result = _result(request_id="request_unchanged", status="delivered")
    hub.encrypted_delivery_result_history.append(result)
    mixed = RetainedAuditCompactionDecision(
        hub_id=hub.hub_id,
        policy_id="mixed_policy_180",
        history_type="mixed",
        compaction_candidate_record_keys=(_key(0, result),),
    )

    applied = apply_retained_audit_compaction_decision(hub, mixed)

    assert applied.unsupported_record_keys == mixed.compaction_candidate_record_keys
    assert applied.metadata["unsupported_history_type"] is True
    assert applied.metadata["encrypted_delivery_history_mutated"] is False
    assert hub.encrypted_delivery_result_history == [result]


def _result(
    *,
    request_id: str,
    registry_hub: str | int | None = "registry_chat_001",
    message_id: str | None = "message_001",
    mailbox_id: str | None = "mailbox_neo",
    status: str = "not_delivered",
    reason: str | None = "delivery_not_attempted",
    source: str | None = None,
    note: str | None = None,
) -> EncryptedDeliveryResult:
    metadata: dict[str, object] = {}
    if registry_hub is not None:
        metadata["registry_hub"] = registry_hub
    if source is not None:
        metadata["source"] = source
    if note is not None:
        metadata["note"] = note
    return EncryptedDeliveryResult(
        request_id=request_id,
        message_id=message_id,
        mailbox_id=mailbox_id,
        lane_signature="basic_messaging:v1",
        gate_decision={"status": "allowed", "reason": "accepted"},
        delivery_result=None,
        status=status,
        reason=reason,
        delivery_attempted=status == "delivered",
        delivery_allowed=status != "gate_blocked",
        policy_required=True,
        metadata=metadata,
    )


def _key(index: int, result: EncryptedDeliveryResult) -> str:
    hub_id = result.metadata.get("registry_hub")
    if not isinstance(hub_id, str):
        hub_id = "none"
    return (
        f"encrypted_delivery_result:{index}:{hub_id}:{result.request_id}:"
        f"{result.message_id or 'none'}:{result.mailbox_id or 'none'}:"
        f"{result.lane_signature or 'none'}:{result.status.status}:{result.reason or 'none'}"
    )
