"""Focused v1.13 retained-audit batch compaction preview coverage."""

from __future__ import annotations

import pickle
from dataclasses import replace

import pytest

from darwin.models import (
    AliasAuthorityOutcomeRecord,
    MessageDeliveryResult,
    RegistryHub,
    RetainedAuditCompactionBatchPreviewResult,
    RetainedAuditCompactionDecision,
    RetainedAuditCompactionPreviewResult,
)
from darwin.registry import (
    SUPPORTED_RETAINED_AUDIT_HISTORY_TYPES,
    apply_retained_audit_compaction_batch,
    classify_retained_audit_records_for_compaction,
    make_retained_audit_compaction_policy,
    preview_retained_audit_compaction_batch,
    summarize_retained_audit_compaction_batch_preview_result,
    summarize_retained_audit_compaction_preview_result,
)


def test_preview_models_have_exact_summary_order_and_return_deep_copies():
    child = RetainedAuditCompactionPreviewResult(
        hub_id="registry_preview_113",
        policy_id="policy_message_113",
        history_type="message_delivery_result",
        would_compact_record_keys=["message:compact"],
        retained_record_keys=["message:retain"],
        ignored_record_keys=["message:ignore"],
        missing_record_keys=["message:missing"],
        unsupported_record_keys=["message:unsupported"],
        would_compact_count=1,
        retained_count=1,
        ignored_count=1,
        missing_count=1,
        unsupported_count=1,
        metadata={"labels": ("child",), "nested": {"safe": True}},
    )

    child_summary = summarize_retained_audit_compaction_preview_result(child)
    assert list(child_summary) == [
        "hub_id",
        "policy_id",
        "history_type",
        "would_compact_record_keys",
        "retained_record_keys",
        "ignored_record_keys",
        "missing_record_keys",
        "unsupported_record_keys",
        "would_compact_count",
        "retained_count",
        "ignored_count",
        "missing_count",
        "unsupported_count",
        "metadata",
    ]
    child_summary["would_compact_record_keys"].append("mutated")
    child_summary["metadata"]["labels"].append("mutated")
    child_summary["metadata"]["nested"]["safe"] = False
    assert child.would_compact_record_keys == ("message:compact",)
    assert child.metadata == {"labels": ["child"], "nested": {"safe": True}}


def test_batch_preview_model_canonicalizes_all_eight_histories_and_copies():
    results = [
        RetainedAuditCompactionPreviewResult(
            hub_id="registry_preview_113",
            policy_id=f"policy_{history_type}",
            history_type=history_type,
            would_compact_record_keys=[f"{history_type}:compact"],
            retained_record_keys=[f"{history_type}:retain"],
            ignored_record_keys=[f"{history_type}:ignore"],
            missing_record_keys=[f"{history_type}:missing"],
            unsupported_record_keys=[f"{history_type}:unsupported"],
            would_compact_count=1,
            retained_count=1,
            ignored_count=1,
            missing_count=1,
            unsupported_count=1,
            metadata={"labels": (history_type,)},
        )
        for history_type in reversed(SUPPORTED_RETAINED_AUDIT_HISTORY_TYPES)
    ]
    result = RetainedAuditCompactionBatchPreviewResult(
        hub_id="registry_preview_113",
        batch_id="batch_all_113",
        preview_results=results,
        metadata={"labels": ("batch",), "nested": {"safe": True}},
    )

    assert result.history_types == SUPPORTED_RETAINED_AUDIT_HISTORY_TYPES
    assert result.would_compact_count == 8
    assert result.retained_count == 8
    assert result.ignored_count == 8
    assert result.missing_count == 8
    assert result.unsupported_count == 8
    copied = summarize_retained_audit_compaction_batch_preview_result(result)
    assert list(copied) == [
        "hub_id",
        "batch_id",
        "history_types",
        "preview_results",
        "would_compact_count",
        "retained_count",
        "ignored_count",
        "missing_count",
        "unsupported_count",
        "metadata",
    ]
    copied["history_types"].reverse()
    copied["preview_results"][0]["metadata"]["labels"].append("mutated")
    copied["metadata"]["labels"].append("mutated")
    copied["metadata"]["nested"]["safe"] = False
    assert result.history_types == SUPPORTED_RETAINED_AUDIT_HISTORY_TYPES
    assert result.preview_results[0].metadata["labels"] == [
        "stream_offer_lifecycle_explanation"
    ]
    assert result.metadata == {"labels": ["batch"], "nested": {"safe": True}}


def test_preview_is_read_only_canonical_and_matches_immediate_apply_categories():
    hub, message_decision, authority_decision = _hub_and_decisions()
    message_decision = replace(
        message_decision,
        retained_record_keys=(),
        ignored_record_keys=message_decision.retained_record_keys,
        compaction_candidate_record_keys=(
            *message_decision.compaction_candidate_record_keys,
            "message_delivery_result:missing:113",
        ),
    )
    before = pickle.dumps(hub, protocol=5)
    caller_metadata = {
        "caller": {"labels": ("reverse", "order")},
        "batch_id": "caller_override",
        "canonical_batch_order": False,
        "structural_preflight_passed": False,
        "read_only": False,
        "networking": True,
        "would_mutate_registry_hub": False,
        "apply_parity_runtime_confirmed": True,
    }

    preview = preview_retained_audit_compaction_batch(
        hub,
        [authority_decision, message_decision],
        batch_id="batch_parity_113",
        metadata=caller_metadata,
    )

    assert pickle.dumps(hub, protocol=5) == before
    assert preview.history_types == (
        "message_delivery_result",
        "authority_outcome",
    )
    assert preview.would_compact_count == 2
    assert preview.retained_count == 1
    assert preview.ignored_count == 1
    assert preview.missing_count == 1
    assert preview.unsupported_count == 0
    assert all(child.unsupported_record_keys == () for child in preview.preview_results)
    assert preview.metadata["caller"] == {"labels": ["reverse", "order"]}
    assert preview.metadata["batch_id"] == "batch_parity_113"
    assert preview.metadata["batch_id_correlation_only"] is True
    assert preview.metadata["canonical_batch_order"] is True
    assert preview.metadata["structural_preflight_passed"] is True
    assert preview.metadata["stale_keys_reported"] is True
    assert preview.metadata["would_mutate_registry_hub"] is True
    assert preview.metadata["read_only"] is True
    assert preview.metadata["registry_hub_mutated"] is False
    assert preview.metadata["networking"] is False
    assert preview.metadata["apply_parity_requires_unchanged_state"] is True
    assert preview.metadata["apply_parity_runtime_confirmed"] is False
    caller_metadata["caller"]["labels"] = ("changed",)
    assert preview.metadata["caller"] == {"labels": ["reverse", "order"]}

    applied = apply_retained_audit_compaction_batch(
        hub,
        [message_decision, authority_decision],
        batch_id="batch_parity_113",
    )
    assert applied.history_types == preview.history_types
    for preview_child, apply_child in zip(
        preview.preview_results,
        applied.apply_results,
        strict=True,
    ):
        assert apply_child.hub_id == preview_child.hub_id
        assert apply_child.policy_id == preview_child.policy_id
        assert apply_child.history_type == preview_child.history_type
        assert apply_child.compacted_record_keys == (
            preview_child.would_compact_record_keys
        )
        assert apply_child.retained_record_keys == preview_child.retained_record_keys
        assert apply_child.ignored_record_keys == preview_child.ignored_record_keys
        assert apply_child.missing_record_keys == preview_child.missing_record_keys
        assert apply_child.unsupported_record_keys == (
            preview_child.unsupported_record_keys
        )


def test_same_batch_id_is_reusable_and_repeated_preview_is_stable_and_read_only():
    hub, message_decision, authority_decision = _hub_and_decisions()
    before = pickle.dumps(hub, protocol=5)

    first = preview_retained_audit_compaction_batch(
        hub,
        [message_decision, authority_decision],
        batch_id="batch_reusable_113",
    )
    second = preview_retained_audit_compaction_batch(
        hub,
        [authority_decision, message_decision],
        batch_id="batch_reusable_113",
    )

    assert first.to_summary() == second.to_summary()
    assert pickle.dumps(hub, protocol=5) == before
    assert first.metadata["batch_id_correlation_only"] is True


def test_preview_helper_canonicalizes_all_eight_empty_decisions():
    hub = RegistryHub(hub_id="registry_preview_113", scope_path="global.preview")
    decisions = [
        RetainedAuditCompactionDecision(
            hub_id=hub.hub_id,
            policy_id=f"policy_{history_type}",
            history_type=history_type,
        )
        for history_type in reversed(SUPPORTED_RETAINED_AUDIT_HISTORY_TYPES)
    ]
    before = pickle.dumps(hub, protocol=5)

    result = preview_retained_audit_compaction_batch(
        hub,
        decisions,
        batch_id="batch_all_empty_113",
    )

    assert result.history_types == SUPPORTED_RETAINED_AUDIT_HISTORY_TYPES
    assert result.would_compact_count == 0
    assert result.missing_count == 0
    assert result.unsupported_count == 0
    assert result.metadata["would_mutate_registry_hub"] is False
    assert pickle.dumps(hub, protocol=5) == before


@pytest.mark.parametrize(
    ("mutate_decisions", "batch_id", "metadata", "error_type", "message"),
    [
        (
            lambda message, authority: object(),
            "batch_invalid_113",
            None,
            TypeError,
            "list or tuple",
        ),
        (
            lambda message, authority: [message],
            "batch_invalid_113",
            None,
            ValueError,
            "at least two",
        ),
        (
            lambda message, authority: [message, message],
            "batch_invalid_113",
            None,
            ValueError,
            "distinct",
        ),
        (
            lambda message, authority: [
                message,
                replace(authority, hub_id="registry_other_113"),
            ],
            "batch_invalid_113",
            None,
            ValueError,
            "hub_id must match",
        ),
        (
            lambda message, authority: [
                message,
                replace(authority, history_type="mixed"),
            ],
            "batch_invalid_113",
            None,
            ValueError,
            "supported single",
        ),
        (
            lambda message, authority: [message, object()],
            "batch_invalid_113",
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
            "batch_invalid_113",
            {"invalid": object()},
            TypeError,
            "JSON-safe",
        ),
    ],
)
def test_preview_preflight_rejections_preserve_exact_hub_bytes(
    mutate_decisions,
    batch_id,
    metadata,
    error_type,
    message,
):
    hub, message_decision, authority_decision = _hub_and_decisions()
    before = pickle.dumps(hub, protocol=5)

    with pytest.raises(error_type, match=message):
        preview_retained_audit_compaction_batch(
            hub,
            mutate_decisions(message_decision, authority_decision),
            batch_id=batch_id,
            metadata=metadata,
        )

    assert pickle.dumps(hub, protocol=5) == before


def test_preview_structural_preflight_checks_every_history_without_mutation():
    hub, message_decision, authority_decision = _hub_and_decisions()
    hub.authority_outcome_history.append({"invalid": "record"})
    before = pickle.dumps(hub, protocol=5)

    with pytest.raises(TypeError, match="supported retained audit"):
        preview_retained_audit_compaction_batch(
            hub,
            [message_decision, authority_decision],
            batch_id="batch_structural_113",
        )

    assert pickle.dumps(hub, protocol=5) == before


def test_preview_public_models_reject_invalid_shapes_and_summarizer_types():
    valid = RetainedAuditCompactionPreviewResult(
        hub_id="registry_preview_113",
        policy_id="policy_message_113",
        history_type="message_delivery_result",
    )
    with pytest.raises(ValueError, match="greater than or equal"):
        RetainedAuditCompactionPreviewResult(
            hub_id="registry_preview_113",
            policy_id="policy_message_113",
            history_type="message_delivery_result",
            would_compact_count=-1,
        )
    with pytest.raises(TypeError, match="JSON-safe dict"):
        RetainedAuditCompactionPreviewResult(
            hub_id="registry_preview_113",
            policy_id="policy_message_113",
            history_type="message_delivery_result",
            metadata=["invalid"],
        )
    with pytest.raises(ValueError, match="at least two"):
        RetainedAuditCompactionBatchPreviewResult(
            hub_id="registry_preview_113",
            batch_id="batch_invalid_113",
            preview_results=[valid],
        )
    with pytest.raises(TypeError, match="PreviewResult"):
        summarize_retained_audit_compaction_preview_result(object())
    with pytest.raises(TypeError, match="BatchPreviewResult"):
        summarize_retained_audit_compaction_batch_preview_result(object())


def _hub_and_decisions() -> tuple[
    RegistryHub,
    RetainedAuditCompactionDecision,
    RetainedAuditCompactionDecision,
]:
    hub = RegistryHub(hub_id="registry_preview_113", scope_path="global.preview")
    message_keep = _message_result(
        message_id="message_keep_113",
        status="delivered",
        reason=None,
        mailbox_id="mailbox_keep_113",
    )
    message_compact = _message_result(
        message_id="message_compact_113",
        status="bounced",
        reason="mailbox_not_found",
        mailbox_id=None,
    )
    authority_keep = _authority_outcome(
        sequence=1,
        final_status="fallback_granted",
        status="fallback_granted",
        reason="pass_up_denied_by_policy",
        granted_alias="global.preview.alpha",
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
    hub.aliases["global.preview.alpha"] = {"owner": "device_alpha_113"}
    hub.conflicts["conflict_113"] = {"alias": "global.alpha"}
    hub.security_events.append({"event_type": "preserved_113"})

    message_policy = make_retained_audit_compaction_policy(
        policy_id="policy_message_113",
        hub_id=hub.hub_id,
        history_types=["message_delivery_result"],
        compact_statuses=["bounced"],
    )
    authority_policy = make_retained_audit_compaction_policy(
        policy_id="policy_authority_113",
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
            "darwin://global.preview.keep/inbox"
            if mailbox_id is not None
            else "darwin://global.preview.missing/inbox"
        ),
        resolved_mailbox_id=mailbox_id,
        target_device_id="device_alpha_113" if mailbox_id is not None else None,
        lane_signature="basic_messaging:v1",
        endpoint_id="endpoint_alpha_113" if mailbox_id is not None else None,
        status=status,
        reason=reason,
        fallback_action=None if mailbox_id is not None else "reject",
        audit_path=("v1.13_batch_preview_test",),
        metadata={"registry_hub": "registry_preview_113"},
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
        record_id=f"authority_outcome:registry_preview_113:{sequence:04d}",
        requested_alias="global.alpha",
        granted_alias=granted_alias,
        target_device=(
            "device_alpha_113" if granted_alias is not None else "device_beta_113"
        ),
        requesting_hub="registry_preview_113",
        authority_ceiling="global.preview",
        final_status=final_status,
        status=status,
        reason=reason,
        decision_count=1,
        path_hubs=("registry_preview_113",),
        decisions=(
            {
                "hub_id": "registry_preview_113",
                "decision": "fallback_available",
            },
        ),
        fallback_used=final_status == "fallback_granted",
        conflict_detected=final_status == "name_taken",
        policy_denied=False,
        path_broken=False,
    )
