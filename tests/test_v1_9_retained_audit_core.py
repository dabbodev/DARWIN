"""Focused v1.9 retained-audit coverage for encryption policy decisions."""

from __future__ import annotations

from copy import deepcopy

import pytest

from darwin.models import (
    EncryptedDeliveryResult,
    EncryptionPolicyDecision,
    LaneAdmissionDecision,
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


def test_policy_decision_classification_maps_owner_fields_and_exact_keys():
    records = (
        _decision(
            policy_id="policy_keep",
            mailbox_id="mailbox_keep",
            message_id="message_keep",
            status="accepted",
            reason=None,
            source="policy_keep",
        ),
        _decision(
            policy_id="policy_compact",
            mailbox_id="mailbox_compact",
            message_id="message_compact",
            status="unsupported_profile",
            reason="unsupported_profile",
            source="policy_compact",
        ),
        _decision(
            policy_id="policy_foreign",
            registry_hub="registry_remote_001",
            status="missing_envelope",
            reason="missing_envelope",
        ),
        _decision(
            policy_id="policy_missing_owner",
            registry_hub=None,
            status="missing_envelope",
            reason="missing_envelope",
            note="missing_envelope",
        ),
        _decision(
            policy_id="policy_non_string_owner",
            registry_hub=42,
            status="missing_envelope",
            reason="missing_envelope",
        ),
    )
    policy = make_retained_audit_compaction_policy(
        policy_id="policy_audit_190",
        hub_id="registry_chat_001",
        history_types=["encryption_policy_decision"],
        retain_statuses=["accepted"],
        compact_statuses=["unsupported_profile", "missing_envelope"],
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
    assert decision.history_type == "encryption_policy_decision"
    assert decision.retained_record_keys == (_key(0, records[0]),)
    assert decision.compaction_candidate_record_keys == (_key(1, records[1]),)
    assert decision.ignored_record_keys == (
        _key(2, records[2]),
        _key(3, records[3]),
        _key(4, records[4]),
    )
    assert decision.candidate_by_history_type == {"encryption_policy_decision": 1}
    assert decision.candidate_by_reason == {"unsupported_profile": 1}
    assert decision.candidate_by_status == {"unsupported_profile": 1}
    assert decision.candidate_by_source == {"policy_compact": 1}


def test_policy_decision_filter_precedence_and_max_records_preserve_order():
    records = (
        _decision(
            policy_id="policy_first",
            status="accepted",
            reason=None,
            source="always_keep",
        ),
        _decision(
            policy_id="policy_second",
            status="accepted",
            reason=None,
        ),
        _decision(
            policy_id="policy_third",
            status="missing_envelope",
            reason="missing_envelope",
        ),
    )
    policy = make_retained_audit_compaction_policy(
        policy_id="policy_audit_cap_190",
        hub_id="registry_chat_001",
        history_types=["encryption_policy_decision"],
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


def test_policy_and_lane_replay_grouping_is_sorted_generic_and_copied():
    policy_zeta = _decision(
        policy_id="policy_zeta",
        mailbox_id="mailbox_shared",
        message_id="message_zeta",
        lane_signature="video_chat:v1",
        status="accepted",
        reason=None,
    )
    policy_alpha = _decision(
        policy_id="policy_alpha",
        mailbox_id="mailbox_shared",
        message_id="message_alpha",
        lane_signature="basic_messaging:v1",
        status="missing_envelope",
        reason="missing_envelope",
    )
    admission = LaneAdmissionDecision(
        decision_id="decision_lane",
        policy_id="policy_lane",
        offer_id="offer_lane",
        request_id="request_lane",
        hub_id="registry_chat_001",
        requester_id="device_a",
        target_handle="target.chat",
        target_scope="global.chat",
        lane_signature="file_transfer:v1",
        status="pass_down",
        reason="accepted",
        allowed=True,
    )
    encrypted = EncryptedDeliveryResult(
        request_id="request_encrypted",
        message_id="message_encrypted",
        mailbox_id="mailbox_shared",
        lane_signature="voice_call:v1",
        gate_decision={"policy_id": "nested_policy_must_not_group"},
        delivery_result=None,
        status="not_delivered",
        reason="delivery_not_attempted",
        delivery_attempted=False,
        delivery_allowed=True,
        policy_required=True,
        metadata={"registry_hub": "registry_chat_001"},
    )

    summary = summarize_retained_audit_replay(
        (policy_zeta, policy_alpha, admission, encrypted),
        hub_id="registry_chat_001",
        metadata={"labels": ("v1.9",)},
    )

    assert summary.by_policy_id == {
        "policy_alpha": 1,
        "policy_lane": 1,
        "policy_zeta": 1,
    }
    assert summary.by_lane_signature == {
        "basic_messaging:v1": 1,
        "file_transfer:v1": 1,
        "video_chat:v1": 1,
        "voice_call:v1": 1,
    }
    assert "nested_policy_must_not_group" not in summary.by_policy_id
    copied = summary.to_summary()
    copied["by_policy_id"]["policy_alpha"] = 99
    copied["by_lane_signature"]["basic_messaging:v1"] = 99
    copied["metadata"]["labels"].append("mutated")
    assert summary.by_policy_id["policy_alpha"] == 1
    assert summary.by_lane_signature["basic_messaging:v1"] == 1
    assert summary.metadata["labels"] == ["v1.9"]


def test_replay_model_sorts_and_validates_policy_and_lane_counts():
    summary = RetainedAuditReplaySummary(
        hub_id="registry_chat_001",
        history_type="encryption_policy_decision",
        by_policy_id={"policy_zeta": 2, "policy_alpha": 1},
        by_lane_signature={"voice_call:v1": 2, "basic_messaging:v1": 1},
    )

    assert list(summary.by_policy_id) == ["policy_alpha", "policy_zeta"]
    assert list(summary.by_lane_signature) == [
        "basic_messaging:v1",
        "voice_call:v1",
    ]
    with pytest.raises(ValueError, match="greater than or equal to 0"):
        RetainedAuditReplaySummary(
            hub_id="registry_chat_001",
            history_type="encryption_policy_decision",
            by_policy_id={"policy_invalid": -1},
        )
    with pytest.raises(ValueError, match="greater than or equal to 0"):
        RetainedAuditReplaySummary(
            hub_id="registry_chat_001",
            history_type="encryption_policy_decision",
            by_lane_signature={"basic_messaging:v1": -1},
        )


def test_policy_decision_apply_is_isolated_reports_stale_and_is_repeatable():
    hub = RegistryHub(hub_id="registry_chat_001", scope_path="global.chat")
    keep = _decision(policy_id="policy_keep", message_id="message_keep")
    compact = _decision(
        policy_id="policy_compact",
        message_id="message_compact",
        status="missing_envelope",
        reason="missing_envelope",
    )
    after = _decision(policy_id="policy_after", message_id="message_after")
    hub.encryption_policy_decision_history.extend((keep, compact, after))
    nested_policy_snapshot = compact.to_summary()
    hub.encrypted_delivery_result_history.append(
        EncryptedDeliveryResult(
            request_id="request_nested",
            message_id=compact.message_id,
            mailbox_id=compact.mailbox_id,
            lane_signature=compact.lane_signature,
            gate_decision={"policy_decision": nested_policy_snapshot},
            delivery_result=None,
            status="not_delivered",
            reason="delivery_not_attempted",
            delivery_attempted=False,
            delivery_allowed=True,
            policy_required=True,
            metadata={"registry_hub": hub.hub_id},
        )
    )
    hub.message_delivery_results.append({"message_id": "message_unchanged"})
    hub.message_inboxes["mailbox_neo"] = [{"message_id": "message_unchanged"}]
    hub.mailbox_encryption_policies["policy_config"] = {"unchanged": True}
    hub.held_stream_offers.append({"offer_id": "offer_unchanged"})
    encrypted_before = deepcopy(hub.encrypted_delivery_result_history)
    delivery_before = deepcopy(hub.message_delivery_results)
    inboxes_before = deepcopy(hub.message_inboxes)
    policy_config_before = deepcopy(hub.mailbox_encryption_policies)
    held_before = deepcopy(hub.held_stream_offers)
    policy = make_retained_audit_compaction_policy(
        policy_id="policy_audit_apply_190",
        hub_id=hub.hub_id,
        history_types=["encryption_policy_decision"],
        compact_statuses=["missing_envelope"],
    )
    classified = classify_retained_audit_records_for_compaction(
        hub.encryption_policy_decision_history,
        policy,
    )
    stale_key = (
        "encryption_policy_decision:99:registry_chat_001:policy_stale:"
        "mailbox_neo:message_stale:basic_messaging:v1:missing_envelope:"
        "missing_envelope"
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
    assert hub.encryption_policy_decision_history == [keep, after]
    assert hub.encrypted_delivery_result_history == encrypted_before
    assert hub.message_delivery_results == delivery_before
    assert hub.message_inboxes == inboxes_before
    assert hub.mailbox_encryption_policies == policy_config_before
    assert hub.held_stream_offers == held_before
    assert result.metadata["encryption_policy_history_mutated"] is True
    assert result.metadata["encrypted_delivery_history_mutated"] is False
    assert result.metadata["delivery_state_mutated"] is False

    repeated = apply_retained_audit_compaction_decision(hub, decision)
    assert repeated.compacted_record_keys == ()
    assert repeated.missing_record_keys == (_key(1, compact), stale_key)
    assert repeated.metadata["encryption_policy_history_mutated"] is False
    assert hub.encrypted_delivery_result_history == encrypted_before


def test_mixed_apply_remains_unsupported_for_policy_decision_history():
    hub = RegistryHub(hub_id="registry_chat_001", scope_path="global.chat")
    record = _decision(policy_id="policy_unchanged")
    hub.encryption_policy_decision_history.append(record)
    mixed = RetainedAuditCompactionDecision(
        hub_id=hub.hub_id,
        policy_id="mixed_policy_190",
        history_type="mixed",
        compaction_candidate_record_keys=(_key(0, record),),
    )

    applied = apply_retained_audit_compaction_decision(hub, mixed)

    assert applied.unsupported_record_keys == mixed.compaction_candidate_record_keys
    assert applied.metadata["unsupported_history_type"] is True
    assert applied.metadata["encryption_policy_history_mutated"] is False
    assert hub.encryption_policy_decision_history == [record]


def _decision(
    *,
    policy_id: str,
    registry_hub: str | int | None = "registry_chat_001",
    mailbox_id: str = "mailbox_neo",
    message_id: str | None = "message_001",
    lane_signature: str = "basic_messaging:v1",
    status: str = "accepted",
    reason: str | None = None,
    source: str | None = None,
    note: str | None = None,
) -> EncryptionPolicyDecision:
    metadata: dict[str, object] = {}
    if registry_hub is not None:
        metadata["registry_hub"] = registry_hub
    if source is not None:
        metadata["source"] = source
    if note is not None:
        metadata["note"] = note
    return EncryptionPolicyDecision(
        policy_id=policy_id,
        mailbox_id=mailbox_id,
        lane_signature=lane_signature,
        message_id=message_id,
        status=status,
        reason=reason,
        encryption_required=True,
        envelope_accepted=status == "accepted",
        profile="symbolic_e2ee_v1",
        encryption_identity_id="enc_mailbox_neo",
        key_bundle_id="kb_mailbox_neo_001",
        metadata=metadata,
    )


def _key(index: int, decision: EncryptionPolicyDecision) -> str:
    hub_id = decision.metadata.get("registry_hub")
    if not isinstance(hub_id, str):
        hub_id = "none"
    reason = "none" if decision.reason is None else decision.reason.reason
    return (
        f"encryption_policy_decision:{index}:{hub_id}:{decision.policy_id}:"
        f"{decision.mailbox_id}:{decision.message_id or 'none'}:"
        f"{decision.lane_signature}:{decision.status.status}:{reason}"
    )
