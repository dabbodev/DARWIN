"""Focused v1.14 strict-stale retained-audit batch apply coverage."""

from __future__ import annotations

import pickle
from dataclasses import replace

import pytest

from darwin.models import (
    AliasAuthorityOutcomeRecord,
    MessageDeliveryResult,
    RegistryHub,
    RetainedAuditCompactionDecision,
)
from darwin.registry import (
    apply_retained_audit_compaction_batch,
    apply_retained_audit_compaction_decision,
    classify_retained_audit_records_for_compaction,
    make_retained_audit_compaction_policy,
    preview_retained_audit_compaction_batch,
)


def test_default_and_explicit_false_preserve_nonfatal_stale_batch_behavior():
    default_hub, default_message, default_authority = _hub_and_decisions()
    explicit_hub, explicit_message, explicit_authority = _hub_and_decisions()
    apply_retained_audit_compaction_decision(default_hub, default_message)
    apply_retained_audit_compaction_decision(explicit_hub, explicit_message)

    default_result = apply_retained_audit_compaction_batch(
        default_hub,
        [default_authority, default_message],
        batch_id="batch_default_114",
        metadata={"strict_stale_abort": True},
    )
    explicit_result = apply_retained_audit_compaction_batch(
        explicit_hub,
        [explicit_authority, explicit_message],
        batch_id="batch_default_114",
        metadata={"strict_stale_abort": True},
        strict_stale_abort=False,
    )

    assert default_result.to_summary() == explicit_result.to_summary()
    assert pickle.dumps(default_hub, protocol=5) == pickle.dumps(
        explicit_hub,
        protocol=5,
    )
    assert default_result.compacted_count == 1
    assert default_result.missing_count == 1
    assert default_result.metadata["strict_stale_abort"] is False


def test_strict_stale_abort_rejects_before_any_selected_history_write():
    hub, message_decision, authority_decision = _hub_and_decisions()
    apply_retained_audit_compaction_decision(hub, message_decision)
    before = pickle.dumps(hub, protocol=5)
    missing_by_history = {
        "message_delivery_result": list(
            message_decision.compaction_candidate_record_keys
        )
    }

    with pytest.raises(ValueError) as exc_info:
        apply_retained_audit_compaction_batch(
            hub,
            [authority_decision, message_decision],
            batch_id="batch_strict_stale_114",
            strict_stale_abort=True,
        )

    assert str(exc_info.value) == (
        "strict_stale_abort rejected batch batch_strict_stale_114: "
        f"missing compaction candidate record keys {missing_by_history}"
    )
    assert pickle.dumps(hub, protocol=5) == before
    assert [record.final_status for record in hub.authority_outcome_history] == [
        "fallback_granted",
        "name_taken",
    ]


def test_strict_stale_error_lists_missing_keys_in_canonical_history_order():
    hub, message_decision, authority_decision = _hub_and_decisions()
    apply_retained_audit_compaction_decision(hub, authority_decision)
    apply_retained_audit_compaction_decision(hub, message_decision)
    before = pickle.dumps(hub, protocol=5)
    missing_by_history = {
        "message_delivery_result": list(
            message_decision.compaction_candidate_record_keys
        ),
        "authority_outcome": list(
            authority_decision.compaction_candidate_record_keys
        ),
    }

    with pytest.raises(ValueError) as exc_info:
        apply_retained_audit_compaction_batch(
            hub,
            [authority_decision, message_decision],
            batch_id="batch_canonical_missing_114",
            strict_stale_abort=True,
        )

    assert str(exc_info.value) == (
        "strict_stale_abort rejected batch batch_canonical_missing_114: "
        f"missing compaction candidate record keys {missing_by_history}"
    )
    assert pickle.dumps(hub, protocol=5) == before


def test_strict_stale_error_preserves_decision_key_order_and_rejects_mixed():
    hub, message_decision, authority_decision = _hub_and_decisions()
    current_key = message_decision.compaction_candidate_record_keys[0]
    missing_keys = (
        "message_delivery_result:missing:zeta:114",
        "message_delivery_result:missing:alpha:114",
    )
    message_decision = replace(
        message_decision,
        compaction_candidate_record_keys=(
            missing_keys[0],
            current_key,
            missing_keys[1],
        ),
    )
    before = pickle.dumps(hub, protocol=5)
    missing_by_history = {"message_delivery_result": list(missing_keys)}

    with pytest.raises(ValueError) as exc_info:
        apply_retained_audit_compaction_batch(
            hub,
            [authority_decision, message_decision],
            batch_id="batch_mixed_stale_114",
            strict_stale_abort=True,
        )

    assert str(exc_info.value) == (
        "strict_stale_abort rejected batch batch_mixed_stale_114: "
        f"missing compaction candidate record keys {missing_by_history}"
    )
    assert pickle.dumps(hub, protocol=5) == before
    assert any(
        record.message_id == "message_compact_114"
        for record in hub.message_delivery_results
    )


@pytest.mark.parametrize("strict_stale_abort", [None, 0, 1, "true", [], {}])
def test_strict_stale_abort_rejects_non_boolean_after_read_only_preflight(
    strict_stale_abort,
):
    hub, message_decision, authority_decision = _hub_and_decisions()
    before = pickle.dumps(hub, protocol=5)

    with pytest.raises(
        TypeError,
        match="^strict_stale_abort must be a boolean$",
    ):
        apply_retained_audit_compaction_batch(
            hub,
            [message_decision, authority_decision],
            batch_id="batch_invalid_strict_114",
            strict_stale_abort=strict_stale_abort,
        )

    assert pickle.dumps(hub, protocol=5) == before


def test_legacy_preflight_errors_take_precedence_over_invalid_strict_flag():
    hub, message_decision, _authority_decision = _hub_and_decisions()
    before = pickle.dumps(hub, protocol=5)

    with pytest.raises(ValueError, match="at least two"):
        apply_retained_audit_compaction_batch(
            hub,
            [message_decision],
            batch_id="batch_preflight_first_114",
            strict_stale_abort="true",
        )

    assert pickle.dumps(hub, protocol=5) == before


def test_full_structural_preflight_precedes_the_strict_stale_guard():
    hub, message_decision, authority_decision = _hub_and_decisions()
    apply_retained_audit_compaction_decision(hub, message_decision)
    hub.authority_outcome_history.append({"invalid": "record"})
    before = pickle.dumps(hub, protocol=5)

    with pytest.raises(TypeError, match="supported retained audit"):
        apply_retained_audit_compaction_batch(
            hub,
            [message_decision, authority_decision],
            batch_id="batch_structural_first_114",
            strict_stale_abort=True,
        )

    assert pickle.dumps(hub, protocol=5) == before


def test_fresh_strict_apply_is_canonical_and_keeps_child_metadata_unchanged():
    strict_hub, strict_message, strict_authority = _hub_and_decisions()
    default_hub, default_message, default_authority = _hub_and_decisions()
    caller_metadata = {
        "caller": {"labels": ("strict", "fresh")},
        "strict_stale_abort": False,
        "stale_keys_reported": True,
        "canonical_batch_order": False,
        "networking": True,
    }

    strict_result = apply_retained_audit_compaction_batch(
        strict_hub,
        [strict_authority, strict_message],
        batch_id="batch_fresh_strict_114",
        metadata=caller_metadata,
        strict_stale_abort=True,
    )
    default_result = apply_retained_audit_compaction_batch(
        default_hub,
        [default_authority, default_message],
        batch_id="batch_fresh_strict_114",
        metadata=caller_metadata,
    )

    assert strict_result.history_types == (
        "message_delivery_result",
        "authority_outcome",
    )
    assert strict_result.compacted_count == 2
    assert strict_result.missing_count == 0
    assert strict_result.metadata["strict_stale_abort"] is True
    assert strict_result.metadata["stale_keys_reported"] is False
    assert strict_result.metadata["canonical_batch_order"] is True
    assert strict_result.metadata["networking"] is False
    assert strict_result.metadata["caller"] == {"labels": ["strict", "fresh"]}
    assert [child.metadata for child in strict_result.apply_results] == [
        child.metadata for child in default_result.apply_results
    ]
    assert all(
        "strict_stale_abort" not in child.metadata
        and "caller" not in child.metadata
        for child in strict_result.apply_results
    )

    caller_metadata["caller"]["labels"] = ("changed",)
    assert strict_result.metadata["caller"] == {"labels": ["strict", "fresh"]}


def test_strict_stale_abort_allows_an_initial_zero_candidate_no_op():
    hub = RegistryHub(hub_id="registry_zero_114", scope_path="global.zero")
    decisions = [
        RetainedAuditCompactionDecision(
            hub_id=hub.hub_id,
            policy_id="policy_message_zero_114",
            history_type="message_delivery_result",
        ),
        RetainedAuditCompactionDecision(
            hub_id=hub.hub_id,
            policy_id="policy_authority_zero_114",
            history_type="authority_outcome",
        ),
    ]
    before = pickle.dumps(hub, protocol=5)

    result = apply_retained_audit_compaction_batch(
        hub,
        list(reversed(decisions)),
        batch_id="batch_zero_114",
        strict_stale_abort=True,
    )

    assert result.history_types == (
        "message_delivery_result",
        "authority_outcome",
    )
    assert result.compacted_count == 0
    assert result.missing_count == 0
    assert result.metadata["strict_stale_abort"] is True
    assert result.metadata["registry_hub_mutated"] is False
    assert pickle.dumps(hub, protocol=5) == before


def test_repeating_a_successful_strict_apply_rejects_without_further_mutation():
    hub, message_decision, authority_decision = _hub_and_decisions()
    decisions = [authority_decision, message_decision]
    first = apply_retained_audit_compaction_batch(
        hub,
        decisions,
        batch_id="batch_repeat_strict_114",
        strict_stale_abort=True,
    )
    after_first = pickle.dumps(hub, protocol=5)

    with pytest.raises(ValueError, match="^strict_stale_abort rejected batch"):
        apply_retained_audit_compaction_batch(
            hub,
            decisions,
            batch_id="batch_repeat_strict_114",
            strict_stale_abort=True,
        )

    assert first.compacted_count == 2
    assert first.missing_count == 0
    assert pickle.dumps(hub, protocol=5) == after_first


def test_preview_does_not_reserve_freshness_for_later_strict_apply():
    hub, message_decision, authority_decision = _hub_and_decisions()
    before_preview = pickle.dumps(hub, protocol=5)

    preview = preview_retained_audit_compaction_batch(
        hub,
        [authority_decision, message_decision],
        batch_id="batch_preview_then_strict_114",
    )

    assert preview.would_compact_count == 2
    assert preview.missing_count == 0
    assert preview.metadata["batch_id_correlation_only"] is True
    assert pickle.dumps(hub, protocol=5) == before_preview

    apply_retained_audit_compaction_decision(hub, message_decision)
    before_strict_apply = pickle.dumps(hub, protocol=5)

    with pytest.raises(ValueError, match="^strict_stale_abort rejected batch"):
        apply_retained_audit_compaction_batch(
            hub,
            [message_decision, authority_decision],
            batch_id="batch_preview_then_strict_114",
            strict_stale_abort=True,
        )

    assert pickle.dumps(hub, protocol=5) == before_strict_apply
    assert [record.final_status for record in hub.authority_outcome_history] == [
        "fallback_granted",
        "name_taken",
    ]


def _hub_and_decisions() -> tuple[
    RegistryHub,
    RetainedAuditCompactionDecision,
    RetainedAuditCompactionDecision,
]:
    hub = RegistryHub(hub_id="registry_strict_114", scope_path="global.strict")
    message_keep = _message_result(
        message_id="message_keep_114",
        status="delivered",
        reason=None,
        mailbox_id="mailbox_keep_114",
    )
    message_compact = _message_result(
        message_id="message_compact_114",
        status="bounced",
        reason="mailbox_not_found",
        mailbox_id=None,
    )
    authority_keep = _authority_outcome(
        sequence=1,
        final_status="fallback_granted",
        status="fallback_granted",
        reason="pass_up_denied_by_policy",
        granted_alias="global.strict.alpha",
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
    hub.aliases["global.strict.alpha"] = {"owner": "device_alpha_114"}
    hub.conflicts["conflict_114"] = {"alias": "global.alpha"}
    hub.security_events.append({"event_type": "preserved_114"})

    message_policy = make_retained_audit_compaction_policy(
        policy_id="policy_message_114",
        hub_id=hub.hub_id,
        history_types=["message_delivery_result"],
        compact_statuses=["bounced"],
    )
    authority_policy = make_retained_audit_compaction_policy(
        policy_id="policy_authority_114",
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
            "darwin://global.strict.keep/inbox"
            if mailbox_id is not None
            else "darwin://global.strict.missing/inbox"
        ),
        resolved_mailbox_id=mailbox_id,
        target_device_id="device_alpha_114" if mailbox_id is not None else None,
        lane_signature="basic_messaging:v1",
        endpoint_id="endpoint_alpha_114" if mailbox_id is not None else None,
        status=status,
        reason=reason,
        fallback_action=None if mailbox_id is not None else "reject",
        audit_path=("v1.14_strict_stale_test",),
        metadata={"registry_hub": "registry_strict_114"},
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
        record_id=f"authority_outcome:registry_strict_114:{sequence:04d}",
        requested_alias="global.alpha",
        granted_alias=granted_alias,
        target_device=(
            "device_alpha_114" if granted_alias is not None else "device_beta_114"
        ),
        requesting_hub="registry_strict_114",
        authority_ceiling="global.strict",
        final_status=final_status,
        status=status,
        reason=reason,
        decision_count=1,
        path_hubs=("registry_strict_114",),
        decisions=(
            {
                "hub_id": "registry_strict_114",
                "decision": "fallback_available",
            },
        ),
        fallback_used=final_status == "fallback_granted",
        conflict_detected=final_status == "name_taken",
        policy_denied=False,
        path_broken=False,
    )
