"""Focused v1.12 retained-audit batch apply coverage."""

from __future__ import annotations

import pickle
from copy import deepcopy
from dataclasses import replace

import pytest

from darwin.models import (
    AliasAuthorityOutcomeRecord,
    MessageDeliveryResult,
    RegistryHub,
    RetainedAuditCompactionApplyResult,
    RetainedAuditCompactionBatchApplyResult,
    RetainedAuditCompactionDecision,
)
from darwin.registry import (
    SUPPORTED_RETAINED_AUDIT_HISTORY_TYPES,
    apply_retained_audit_compaction_batch,
    apply_retained_audit_compaction_decision,
    classify_retained_audit_records_for_compaction,
    make_retained_audit_compaction_policy,
    summarize_retained_audit_compaction_batch_apply_result,
)


def test_batch_result_canonicalizes_all_eight_histories_and_returns_deep_copies():
    reversed_results = [
        RetainedAuditCompactionApplyResult(
            hub_id="registry_batch_112",
            policy_id=f"policy_{history_type}",
            history_type=history_type,
            compacted_record_keys=[f"{history_type}:compacted"],
            retained_record_keys=[f"{history_type}:retained"],
            ignored_record_keys=[f"{history_type}:ignored"],
            missing_record_keys=[f"{history_type}:missing"],
            unsupported_record_keys=[f"{history_type}:unsupported"],
            compacted_count=1,
            retained_count=1,
            ignored_count=1,
            missing_count=1,
            unsupported_count=1,
            metadata={"labels": ("child", history_type)},
        )
        for history_type in reversed(SUPPORTED_RETAINED_AUDIT_HISTORY_TYPES)
    ]

    result = RetainedAuditCompactionBatchApplyResult(
        hub_id="registry_batch_112",
        batch_id="batch_all_histories_112",
        apply_results=reversed_results,
        metadata={"labels": ("batch",), "nested": {"safe": True}},
    )

    assert result.history_types == SUPPORTED_RETAINED_AUDIT_HISTORY_TYPES
    assert result.compacted_count == 8
    assert result.retained_count == 8
    assert result.ignored_count == 8
    assert result.missing_count == 8
    assert result.unsupported_count == 8

    copied = summarize_retained_audit_compaction_batch_apply_result(result)
    assert copied["history_types"] == list(SUPPORTED_RETAINED_AUDIT_HISTORY_TYPES)
    assert [
        child["history_type"] for child in copied["apply_results"]
    ] == list(SUPPORTED_RETAINED_AUDIT_HISTORY_TYPES)
    copied["history_types"].reverse()
    copied["apply_results"][0]["compacted_record_keys"].append("mutated")
    copied["apply_results"][0]["metadata"]["labels"].append("mutated")
    copied["metadata"]["labels"].append("mutated")
    copied["metadata"]["nested"]["safe"] = False

    assert result.history_types == SUPPORTED_RETAINED_AUDIT_HISTORY_TYPES
    assert result.apply_results[0].compacted_record_keys == (
        "stream_offer_lifecycle_explanation:compacted",
    )
    assert result.apply_results[0].metadata["labels"] == [
        "child",
        "stream_offer_lifecycle_explanation",
    ]
    assert result.metadata == {"labels": ["batch"], "nested": {"safe": True}}


def test_batch_apply_is_canonical_aggregate_and_isolated():
    hub, message_decision, authority_decision = _hub_and_decisions()
    aliases_before = deepcopy(hub.aliases)
    conflicts_before = deepcopy(hub.conflicts)
    security_before = deepcopy(hub.security_events)

    result = apply_retained_audit_compaction_batch(
        hub,
        [authority_decision, message_decision],
        batch_id="batch_success_112",
        metadata={
            "caller": {"labels": ("reverse", "order")},
            "batch_id": "caller_override",
            "canonical_batch_order": False,
            "networking": True,
        },
    )

    assert result.history_types == (
        "message_delivery_result",
        "authority_outcome",
    )
    assert [child.policy_id for child in result.apply_results] == [
        "policy_message_112",
        "policy_authority_112",
    ]
    assert result.compacted_count == 2
    assert result.retained_count == 2
    assert result.ignored_count == 0
    assert result.missing_count == 0
    assert result.unsupported_count == 0
    assert result.metadata["caller"] == {"labels": ["reverse", "order"]}
    assert result.metadata["batch_id"] == "batch_success_112"
    assert result.metadata["canonical_batch_order"] is True
    assert result.metadata["networking"] is False
    assert result.metadata["registry_hub_mutated"] is True
    assert result.metadata["compact_snapshot_changed"] is False
    assert [record.message_id for record in hub.message_delivery_results] == [
        "message_keep_112"
    ]
    assert [
        record.record_id for record in hub.authority_outcome_history
    ] == ["authority_outcome:registry_batch_112:0001"]
    assert hub.aliases == aliases_before
    assert hub.conflicts == conflicts_before
    assert hub.security_events == security_before


def test_batch_apply_reports_stale_children_and_repeat_is_a_no_op():
    hub, message_decision, authority_decision = _hub_and_decisions()

    message_result = apply_retained_audit_compaction_decision(hub, message_decision)
    first_batch = apply_retained_audit_compaction_batch(
        hub,
        [authority_decision, message_decision],
        batch_id="batch_stale_112",
    )
    state_after_first_batch = pickle.dumps(hub, protocol=5)
    repeated = apply_retained_audit_compaction_batch(
        hub,
        [message_decision, authority_decision],
        batch_id="batch_stale_112",
    )

    assert message_result.compacted_count == 1
    assert first_batch.compacted_count == 1
    assert first_batch.missing_count == 1
    assert first_batch.apply_results[0].history_type == "message_delivery_result"
    assert first_batch.apply_results[0].missing_count == 1
    assert first_batch.apply_results[1].history_type == "authority_outcome"
    assert first_batch.apply_results[1].compacted_count == 1
    assert first_batch.metadata["stale_keys_reported"] is True
    assert repeated.compacted_count == 0
    assert repeated.missing_count == 2
    assert repeated.metadata["registry_hub_mutated"] is False
    assert pickle.dumps(hub, protocol=5) == state_after_first_batch


@pytest.mark.parametrize(
    ("mutate_decisions", "batch_id", "metadata", "error_type", "message"),
    [
        (
            lambda message, authority: [message],
            "batch_invalid_112",
            None,
            ValueError,
            "at least two",
        ),
        (
            lambda message, authority: [message, message],
            "batch_invalid_112",
            None,
            ValueError,
            "distinct",
        ),
        (
            lambda message, authority: [
                message,
                replace(authority, hub_id="registry_other_112"),
            ],
            "batch_invalid_112",
            None,
            ValueError,
            "hub_id must match",
        ),
        (
            lambda message, authority: [
                message,
                replace(authority, history_type="mixed"),
            ],
            "batch_invalid_112",
            None,
            ValueError,
            "supported single",
        ),
        (
            lambda message, authority: [message, object()],
            "batch_invalid_112",
            None,
            TypeError,
            "RetainedAuditCompactionDecision",
        ),
        (
            lambda message, authority: [message, authority],
            " ",
            None,
            ValueError,
            "batch_id",
        ),
        (
            lambda message, authority: [message, authority],
            "batch_invalid_112",
            {"invalid": object()},
            TypeError,
            "JSON-safe",
        ),
    ],
)
def test_batch_preflight_rejections_preserve_exact_hub_bytes(
    mutate_decisions,
    batch_id,
    metadata,
    error_type,
    message,
):
    hub, message_decision, authority_decision = _hub_and_decisions()
    before = pickle.dumps(hub, protocol=5)

    with pytest.raises(error_type, match=message):
        apply_retained_audit_compaction_batch(
            hub,
            mutate_decisions(message_decision, authority_decision),
            batch_id=batch_id,
            metadata=metadata,
        )

    assert pickle.dumps(hub, protocol=5) == before


def test_batch_structural_preflight_checks_all_histories_before_mutation():
    hub, message_decision, authority_decision = _hub_and_decisions()
    hub.authority_outcome_history.append({"invalid": "record"})
    before = pickle.dumps(hub, protocol=5)

    with pytest.raises(TypeError, match="supported retained audit"):
        apply_retained_audit_compaction_batch(
            hub,
            [message_decision, authority_decision],
            batch_id="batch_structural_preflight_112",
        )

    assert pickle.dumps(hub, protocol=5) == before


def test_batch_public_models_reject_invalid_result_shapes():
    child = RetainedAuditCompactionApplyResult(
        hub_id="registry_batch_112",
        policy_id="policy_message_112",
        history_type="message_delivery_result",
    )
    with pytest.raises(ValueError, match="at least two"):
        RetainedAuditCompactionBatchApplyResult(
            hub_id="registry_batch_112",
            batch_id="batch_invalid_112",
            apply_results=[child],
        )
    with pytest.raises(TypeError, match="BatchApplyResult"):
        summarize_retained_audit_compaction_batch_apply_result(object())


def _hub_and_decisions() -> tuple[
    RegistryHub,
    RetainedAuditCompactionDecision,
    RetainedAuditCompactionDecision,
]:
    hub = RegistryHub(hub_id="registry_batch_112", scope_path="global.batch")
    message_keep = _message_result(
        message_id="message_keep_112",
        status="delivered",
        reason=None,
        mailbox_id="mailbox_keep_112",
    )
    message_compact = _message_result(
        message_id="message_compact_112",
        status="bounced",
        reason="mailbox_not_found",
        mailbox_id=None,
    )
    authority_keep = _authority_outcome(
        sequence=1,
        final_status="fallback_granted",
        status="fallback_granted",
        reason="pass_up_denied_by_policy",
        granted_alias="global.batch.alpha",
    )
    authority_compact = _authority_outcome(
        sequence=2,
        final_status="name_taken",
        status="conflict",
        reason="fallback_alias_conflict",
        granted_alias=None,
    )
    hub.message_delivery_results.extend((message_keep, message_compact))
    hub.authority_outcome_history.extend((authority_keep, authority_compact))
    hub.aliases["global.batch.alpha"] = {"owner": "device_alpha_112"}
    hub.conflicts["conflict_112"] = {"alias": "global.alpha"}
    hub.security_events.append({"event_type": "preserved_112"})

    message_policy = make_retained_audit_compaction_policy(
        policy_id="policy_message_112",
        hub_id=hub.hub_id,
        history_types=["message_delivery_result"],
        compact_statuses=["bounced"],
    )
    authority_policy = make_retained_audit_compaction_policy(
        policy_id="policy_authority_112",
        hub_id=hub.hub_id,
        history_types=["authority_outcome"],
        compact_statuses=["name_taken"],
    )
    return (
        hub,
        classify_retained_audit_records_for_compaction(
            tuple(hub.message_delivery_results),
            message_policy,
        ),
        classify_retained_audit_records_for_compaction(
            tuple(hub.authority_outcome_history),
            authority_policy,
        ),
    )


def _message_result(
    *,
    message_id: str,
    status: str,
    reason: str | None,
    mailbox_id: str | None,
) -> MessageDeliveryResult:
    return MessageDeliveryResult(
        message_id=message_id,
        recipient_address=(
            "darwin://global.batch.keep/inbox"
            if mailbox_id is not None
            else "darwin://global.batch.missing/inbox"
        ),
        resolved_mailbox_id=mailbox_id,
        target_device_id="device_alpha_112" if mailbox_id is not None else None,
        lane_signature="basic_messaging:v1",
        endpoint_id="endpoint_alpha_112" if mailbox_id is not None else None,
        status=status,
        reason=reason,
        fallback_action=None if mailbox_id is not None else "reject",
        audit_path=("v1.12_batch_test",),
        metadata={"registry_hub": "registry_batch_112"},
    )


def _authority_outcome(
    *,
    sequence: int,
    final_status: str,
    status: str,
    reason: str,
    granted_alias: str | None,
) -> AliasAuthorityOutcomeRecord:
    return AliasAuthorityOutcomeRecord(
        record_id=f"authority_outcome:registry_batch_112:{sequence:04d}",
        requested_alias="global.alpha",
        granted_alias=granted_alias,
        target_device=(
            "device_alpha_112" if granted_alias is not None else "device_beta_112"
        ),
        requesting_hub="registry_batch_112",
        authority_ceiling="global.batch",
        final_status=final_status,
        status=status,
        reason=reason,
        decision_count=1,
        path_hubs=("registry_batch_112",),
        decisions=(
            {
                "hub_id": "registry_batch_112",
                "decision": "fallback_available",
            },
        ),
        fallback_used=final_status == "fallback_granted",
        conflict_detected=final_status == "name_taken",
        policy_denied=False,
        path_broken=False,
    )
