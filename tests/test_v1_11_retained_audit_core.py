"""Focused v1.11 retained-audit coverage for authority outcomes."""

from __future__ import annotations

from copy import deepcopy

import pytest

from darwin.models import (
    AliasAuthorityOutcomeRecord,
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


def test_authority_outcome_classification_uses_final_status_owner_and_exact_key():
    records = (
        _outcome(
            sequence=1,
            requested_alias="global.alpha",
            granted_alias="global.family.alpha",
            target_device="device_alpha",
            final_status="fallback_granted",
            status="fallback_granted",
            reason="insufficient_authority",
        ),
        _outcome(
            sequence=2,
            requested_alias="global.alpha",
            granted_alias=None,
            target_device="device_beta",
            final_status="name_taken",
            status="conflict",
            reason="alias_conflict",
        ),
        _outcome(sequence=3, requesting_hub="registry_foreign_001"),
        _outcome(sequence=4, requesting_hub=None),
        _outcome(sequence=5, requesting_hub=42),
    )
    policy = make_retained_audit_compaction_policy(
        policy_id="authority_audit_policy_111",
        hub_id="registry_home_001",
        history_types=["authority_outcome"],
        retain_statuses=["fallback_granted"],
        compact_statuses=["name_taken"],
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
        "authority_outcome",
    )
    assert decision.retained_record_keys == (_key(0, records[0]),)
    assert decision.compaction_candidate_record_keys == (_key(1, records[1]),)
    assert decision.ignored_record_keys == (
        _key(2, records[2]),
        _key(3, records[3]),
        _key(4, records[4]),
    )
    assert decision.candidate_by_status == {"name_taken": 1}
    assert decision.candidate_by_reason == {"alias_conflict": 1}
    assert decision.candidate_by_source == {"none": 1}


def test_authority_outcome_replay_groups_alias_device_and_path_copies():
    records = (
        _outcome(
            sequence=1,
            requested_alias="global.zeta",
            granted_alias="global.family.zeta",
            target_device="device_shared",
            final_status="fallback_granted",
            status="fallback_granted",
            reason="insufficient_authority",
            path_hubs=("registry_home_001", "registry_family_001"),
        ),
        _outcome(
            sequence=2,
            requested_alias="global.alpha",
            granted_alias=None,
            target_device="device_shared",
            final_status="policy_denied",
            status="rejected",
            reason="pass_up_denied_by_policy",
            path_hubs=("registry_home_001", "registry_family_001"),
        ),
    )

    summary = summarize_retained_audit_replay(
        records,
        hub_id="registry_home_001",
        metadata={"labels": ("v1.11",)},
    )

    assert summary.by_requested_alias == {"global.alpha": 1, "global.zeta": 1}
    assert summary.by_granted_alias == {"global.family.zeta": 1}
    assert summary.by_target_device == {"device_shared": 2}
    assert summary.by_path_hub == {
        "registry_family_001": 2,
        "registry_home_001": 2,
    }
    assert summary.by_status == {"fallback_granted": 1, "policy_denied": 1}
    assert summary.by_reason == {
        "insufficient_authority": 1,
        "pass_up_denied_by_policy": 1,
    }

    copied = summary.to_summary()
    copied["by_requested_alias"]["global.alpha"] = 99
    copied["by_granted_alias"]["global.family.zeta"] = 99
    copied["by_target_device"]["device_shared"] = 99
    copied["by_path_hub"]["registry_home_001"] = 99
    copied["metadata"]["labels"].append("mutated")
    assert summary.by_requested_alias["global.alpha"] == 1
    assert summary.by_granted_alias["global.family.zeta"] == 1
    assert summary.by_target_device["device_shared"] == 2
    assert summary.by_path_hub["registry_home_001"] == 2
    assert summary.metadata["labels"] == ["v1.11"]


def test_replay_model_validates_new_authority_count_maps():
    summary = RetainedAuditReplaySummary(
        hub_id="registry_home_001",
        history_type="authority_outcome",
        by_requested_alias={"global.zeta": 2, "global.alpha": 1},
        by_granted_alias={"global.family.zeta": 2, "global.family.alpha": 1},
        by_target_device={"device_zeta": 2, "device_alpha": 1},
        by_path_hub={"registry_zeta": 2, "registry_alpha": 1},
    )

    assert list(summary.by_requested_alias) == ["global.alpha", "global.zeta"]
    assert list(summary.by_granted_alias) == [
        "global.family.alpha",
        "global.family.zeta",
    ]
    assert list(summary.by_target_device) == ["device_alpha", "device_zeta"]
    assert list(summary.by_path_hub) == ["registry_alpha", "registry_zeta"]
    with pytest.raises(ValueError, match="greater than or equal to 0"):
        RetainedAuditReplaySummary(
            hub_id="registry_home_001",
            history_type="authority_outcome",
            by_path_hub={"registry_invalid": -1},
        )


def test_authority_outcome_apply_is_isolated_stale_and_repeatable():
    hub = RegistryHub(hub_id="registry_home_001", scope_path="global.family.home")
    keep = _outcome(sequence=1)
    compact = _outcome(
        sequence=2,
        requested_alias="global.taken",
        granted_alias=None,
        target_device="device_beta",
        final_status="name_taken",
        status="conflict",
        reason="alias_conflict",
    )
    after = _outcome(sequence=3, requested_alias="global.after")
    hub.authority_outcome_history.extend((keep, compact, after))
    hub.aliases["global.family.server"] = {"owner": "device_alpha"}
    hub.conflicts["conflict_001"] = {"alias": "global.taken"}
    hub.security_events.append({"event_type": "preserved"})
    hub.message_delivery_results.append({"message_id": "preserved"})
    aliases_before = deepcopy(hub.aliases)
    conflicts_before = deepcopy(hub.conflicts)
    security_before = deepcopy(hub.security_events)
    delivery_before = deepcopy(hub.message_delivery_results)
    policy = make_retained_audit_compaction_policy(
        policy_id="authority_audit_apply_111",
        hub_id=hub.hub_id,
        history_types=["authority_outcome"],
        compact_statuses=["name_taken"],
    )
    classified = classify_retained_audit_records_for_compaction(
        hub.authority_outcome_history,
        policy,
    )
    stale_key = (
        "authority_outcome:99:registry_home_001:"
        "authority_outcome:registry_home_001:0099:global.stale:none:"
        "device_stale:name_taken:conflict:alias_conflict:registry_home_001"
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
    assert hub.authority_outcome_history == [keep, after]
    assert hub.aliases == aliases_before
    assert hub.conflicts == conflicts_before
    assert hub.security_events == security_before
    assert hub.message_delivery_results == delivery_before
    assert result.metadata["authority_history_mutated"] is True
    assert result.metadata["alias_history_mutated"] is False
    assert result.metadata["delivery_state_mutated"] is False

    repeated = apply_retained_audit_compaction_decision(hub, decision)
    assert repeated.compacted_record_keys == ()
    assert repeated.missing_record_keys == (_key(1, compact), stale_key)
    assert repeated.metadata["authority_history_mutated"] is False


def test_mixed_apply_and_prior_history_contracts_remain_unchanged():
    hub = RegistryHub(hub_id="registry_home_001", scope_path="global.family.home")
    record = _outcome(sequence=1)
    hub.authority_outcome_history.append(record)
    mixed = RetainedAuditCompactionDecision(
        hub_id=hub.hub_id,
        policy_id="mixed_policy_111",
        history_type="mixed",
        compaction_candidate_record_keys=(_key(0, record),),
    )

    applied = apply_retained_audit_compaction_decision(hub, mixed)

    assert SUPPORTED_RETAINED_AUDIT_HISTORY_TYPES[:7] == (
        "stream_offer_lifecycle_explanation",
        "stream_offer_status_transition",
        "rendezvous_poll_result",
        "lane_admission_decision",
        "encrypted_delivery_result",
        "encryption_policy_decision",
        "message_delivery_result",
    )
    assert applied.unsupported_record_keys == mixed.compaction_candidate_record_keys
    assert applied.metadata["unsupported_history_type"] is True
    assert applied.metadata["authority_history_mutated"] is False
    assert hub.authority_outcome_history == [record]


def _outcome(
    *,
    sequence: int,
    requesting_hub: str | int | None = "registry_home_001",
    requested_alias: str = "global.server",
    granted_alias: str | None = "global.family.server",
    target_device: str | None = "device_alpha",
    final_status: str = "fallback_granted",
    status: str | None = "fallback_granted",
    reason: str | None = "insufficient_authority",
    path_hubs: tuple[str, ...] = ("registry_home_001", "registry_family_001"),
) -> AliasAuthorityOutcomeRecord:
    return AliasAuthorityOutcomeRecord(
        record_id=f"authority_outcome:registry_home_001:{sequence:04d}",
        requested_alias=requested_alias,
        granted_alias=granted_alias,
        target_device=target_device,
        requesting_hub=requesting_hub,  # type: ignore[arg-type]
        authority_ceiling="global.family",
        final_status=final_status,
        status=status,
        reason=reason,
        decision_count=len(path_hubs),
        path_hubs=path_hubs,
        decisions=tuple(
            {
                "hub_id": hub_id,
                "decision": "fallback_available",
            }
            for hub_id in path_hubs
        ),
        fallback_used=final_status == "fallback_granted",
        conflict_detected=final_status == "name_taken",
        policy_denied=final_status == "policy_denied",
        path_broken=final_status == "authority_path_broken",
    )


def _key(index: int, record: AliasAuthorityOutcomeRecord) -> str:
    requesting_hub = (
        record.requesting_hub if isinstance(record.requesting_hub, str) else "none"
    )
    return (
        f"authority_outcome:{index}:{requesting_hub}:{record.record_id}:"
        f"{record.requested_alias}:{record.granted_alias or 'none'}:"
        f"{record.target_device or 'none'}:{record.final_status}:"
        f"{record.status or 'none'}:{record.reason or 'none'}:"
        f"{','.join(record.path_hubs) or 'none'}"
    )
