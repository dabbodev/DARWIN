"""Scenario assertion helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from darwin.models.encrypted_delivery import EncryptedDeliveryResult
from darwin.models.encryption import EncryptionPolicyDecision
from darwin.models.stream_offer import (
    LaneAdmissionDecision,
    RendezvousPollResult,
    StreamOfferLifecycleApplyResult,
    StreamOfferLifecycleAuditSummary,
    StreamOfferLifecycleExplanation,
    StreamOfferLifecycleExplanationPruningApplyResult,
    StreamOfferLifecycleExplanationPruningPlan,
    StreamOfferLifecycleExplanationRetentionDecision,
    StreamOfferLifecyclePlan,
    StreamOfferStatusTransition,
)
from darwin.registry.aliases import resolve_alias
from darwin.registry.authority_audit import (
    build_authority_audit_trace,
    summarize_authority_path,
)
from darwin.registry.encrypted_delivery import (
    build_encrypted_delivery_audit_entry,
    query_encrypted_delivery_results,
)
from darwin.registry.encryption_registry import query_encryption_policy_decisions
from darwin.registry.history_queries import (
    query_alias_conflicts,
    query_alias_history,
    query_authority_outcomes,
    query_quarantine_events,
)
from darwin.registry.mailbox_registry import get_mailbox, list_mailbox_capabilities
from darwin.registry.message_delivery import (
    get_mailbox_inbox,
    list_message_delivery_results,
)
from darwin.registry.stream_offers import (
    query_held_stream_offers,
    query_lane_admission_decisions,
    query_rendezvous_poll_results,
    query_stream_offer_lifecycle_explanations,
    query_stream_offer_status_transitions,
)
from darwin.registry.trace_explain import explain_authority_trace
from darwin.sim.world import World


@dataclass(frozen=True, slots=True)
class AssertionResult:
    assertion_type: str
    passed: bool
    message: str
    expected: Any = None
    actual: Any = None


def evaluate_assertions(world: World, assertions: list[dict[str, Any]]) -> list[AssertionResult]:
    return [evaluate_assertion(world, assertion) for assertion in assertions]


def evaluate_assertion(world: World, assertion: dict[str, Any]) -> AssertionResult:
    assertion_type = assertion.get("type") or assertion.get("assert")
    if not isinstance(assertion_type, str) or not assertion_type:
        return AssertionResult(
            assertion_type="unknown",
            passed=False,
            message="Assertion requires a type",
        )

    evaluator = _EVALUATORS.get(assertion_type)
    if evaluator is None:
        return AssertionResult(
            assertion_type=assertion_type,
            passed=False,
            message=f"Unsupported assertion type: {assertion_type}",
        )
    return evaluator(world, assertion_type, assertion)


def _device_registered(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub = world.registry_hubs.get(str(assertion.get("registry_hub")))
    device_id = str(assertion.get("device"))
    actual = hub is not None and device_id in hub.devices
    return _result(assertion_type, actual, True, f"{device_id} registered")


def _label_maps_to(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub = world.registry_hubs.get(str(assertion.get("registry_hub")))
    label = str(assertion.get("label"))
    expected = str(assertion.get("device"))
    actual = None if hub is None else hub.labels.get(label)
    return _result(
        assertion_type,
        actual == expected,
        expected,
        f"{label} maps to {expected}",
        actual,
    )


def _device_state(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub = world.registry_hubs.get(str(assertion.get("registry_hub")))
    device_id = str(assertion.get("device"))
    expected = str(assertion.get("expected"))
    actual = None
    if hub is not None and device_id in hub.devices:
        actual = hub.devices[device_id].current_state
    return _result(
        assertion_type,
        actual == expected,
        expected,
        f"{device_id} state is {expected}",
        actual,
    )


def _lane_state(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub = world.traffic_hubs.get(str(assertion.get("traffic_hub")))
    lane_id = str(assertion.get("lane"))
    expected = str(assertion.get("expected"))
    actual = None
    if hub is not None and lane_id in hub.lanes:
        actual = hub.lanes[lane_id].state
    return _result(
        assertion_type,
        actual == expected,
        expected,
        f"{lane_id} state is {expected}",
        actual,
    )


def _lane_not_active(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub = world.traffic_hubs.get(str(assertion.get("traffic_hub")))
    lane_id = str(assertion.get("lane"))
    actual = None
    if hub is not None and lane_id in hub.lanes:
        actual = hub.lanes[lane_id].state
    return _result(
        assertion_type,
        actual is not None and actual != "active",
        "not active",
        f"{lane_id} is not active",
        actual,
    )


def _lane_sequence(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub = world.traffic_hubs.get(str(assertion.get("traffic_hub")))
    lane_id = str(assertion.get("lane"))
    expected = {
        "last_sent": int(assertion.get("last_sent", 0)),
        "last_acknowledged": int(assertion.get("last_acknowledged", 0)),
    }
    actual = None
    if hub is not None and lane_id in hub.lanes:
        lane = hub.lanes[lane_id]
        actual = {
            "last_sent": lane.last_sent_sequence,
            "last_acknowledged": lane.last_acknowledged_sequence,
        }
    return _result(
        assertion_type,
        actual == expected,
        expected,
        f"{lane_id} sequence matches",
        actual,
    )


def _flow_control_exists(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub = world.traffic_hubs.get(str(assertion.get("traffic_hub")))
    lane_id = str(assertion.get("lane"))
    actual = hub is not None and lane_id in hub.flow_controls
    return _result(assertion_type, actual, True, f"flow control exists: {lane_id}")


def _flow_control_absent(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub = world.traffic_hubs.get(str(assertion.get("traffic_hub")))
    lane_id = str(assertion.get("lane"))
    actual = hub is not None and lane_id not in hub.flow_controls
    return _result(assertion_type, actual, True, f"flow control absent: {lane_id}")


def _latest_step_status(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    expected = str(assertion.get("expected"))
    latest_result = world.action_results[-1] if world.action_results else None
    actual = getattr(latest_result, "action", None)
    if actual is None:
        actual = getattr(latest_result, "status", None)
    return _result(
        assertion_type,
        actual == expected,
        expected,
        f"latest step status is {expected}",
        actual,
    )


def _latest_step_reason(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    expected = str(assertion.get("expected"))
    latest_result = world.action_results[-1] if world.action_results else None
    actual = getattr(latest_result, "reason", None)
    return _result(
        assertion_type,
        actual == expected,
        expected,
        f"latest step reason is {expected}",
        actual,
    )


def _relocation_failed(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub = world.traffic_hubs.get(str(assertion.get("traffic_hub")))
    device_id = str(assertion.get("device"))
    actual = None
    if hub is not None and device_id in hub.relocations:
        actual = hub.relocations[device_id].state
    return _result(
        assertion_type,
        actual == "failed",
        "failed",
        f"{device_id} relocation failed",
        actual,
    )


def _move_recorded(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub = world.registry_hubs.get(str(assertion.get("registry_hub")))
    device_id = str(assertion.get("device"))
    actual = None if hub is None else len(hub.moves.get(device_id, []))
    return _result(
        assertion_type,
        actual is not None and actual > 0,
        "> 0",
        f"{device_id} has recorded moves",
        actual,
    )


def _move_not_recorded(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub = world.registry_hubs.get(str(assertion.get("registry_hub")))
    device_id = str(assertion.get("device"))
    actual = None if hub is None else len(hub.moves.get(device_id, []))
    return _result(
        assertion_type,
        actual == 0,
        0,
        f"{device_id} has no recorded moves",
        actual,
    )


def _attachment_is(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub = world.registry_hubs.get(str(assertion.get("registry_hub")))
    device_id = str(assertion.get("device"))
    expected = str(assertion.get("expected_attachment"))
    actual = None
    if hub is not None:
        attachment = hub.attachments.get(device_id)
        if attachment is not None:
            actual = attachment.current_attachment
        elif device_id in hub.devices:
            actual = hub.devices[device_id].current_attachment
    return _result(
        assertion_type,
        actual == expected,
        expected,
        f"{device_id} attachment is {expected}",
        actual,
    )


def _route_for_lane(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub = world.traffic_hubs.get(str(assertion.get("traffic_hub")))
    lane_id = str(assertion.get("lane"))
    expected = [str(hub_id) for hub_id in assertion.get("expected_route", [])]
    actual = None
    if hub is not None and lane_id in hub.lanes:
        actual = list(hub.lanes[lane_id].current_route)
    return _result(
        assertion_type,
        actual == expected,
        expected,
        f"{lane_id} route matches",
        actual,
    )


def _event_seen(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    event_type = str(assertion.get("event_type"))
    actual = world.event_log.has_event_type(event_type)
    return _result(assertion_type, actual, True, f"event seen: {event_type}")


def _conflict_exists(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub = world.registry_hubs.get(str(assertion.get("registry_hub")))
    expected = str(assertion.get("conflict_type"))
    actual = []
    if hub is not None:
        actual = [conflict.conflict_type for conflict in hub.conflicts.values()]
    return _result(
        assertion_type,
        expected in actual,
        expected,
        f"conflict exists: {expected}",
        actual,
    )


def _quarantine_exists(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub = world.registry_hubs.get(str(assertion.get("registry_hub")))
    device_id = str(assertion.get("device"))
    actual = hub is not None and device_id in hub.quarantines
    return _result(assertion_type, actual, True, f"quarantine exists: {device_id}")


def _recommendation_exists(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub = world.traffic_hubs.get(str(assertion.get("traffic_hub")))
    expected = str(assertion.get("recommendation_type"))
    actual = []
    if hub is not None:
        actual = [
            recommendation.recommendation_type
            for recommendation in hub.growth_recommendations
        ]
    return _result(
        assertion_type,
        expected in actual,
        expected,
        f"recommendation exists: {expected}",
        actual,
    )


def _session_state(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub = world.registry_hubs.get(str(assertion.get("registry_hub")))
    session_id = str(assertion.get("session_id"))
    expected = str(assertion.get("expected"))
    actual = None
    if hub is not None and session_id in hub.local_sessions:
        actual = hub.local_sessions[session_id].state
    return _result(
        assertion_type,
        actual == expected,
        expected,
        f"{session_id} session state is {expected}",
        actual,
    )


def _session_counter(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub = world.registry_hubs.get(str(assertion.get("registry_hub")))
    session_id = str(assertion.get("session_id"))
    expected = int(assertion.get("expected", 0))
    actual = None
    if hub is not None and session_id in hub.local_sessions:
        actual = hub.local_sessions[session_id].current_counter
    return _result(
        assertion_type,
        actual == expected,
        expected,
        f"{session_id} session counter is {expected}",
        actual,
    )


def _checkpoint_state(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub = world.registry_hubs.get(str(assertion.get("registry_hub")))
    device_id = str(assertion.get("device"))
    expected = str(assertion.get("expected"))
    actual = None
    if hub is not None and device_id in hub.checkpoints:
        actual = hub.checkpoints[device_id].state
    return _result(
        assertion_type,
        actual == expected,
        expected,
        f"{device_id} checkpoint state is {expected}",
        actual,
    )


def _alias_resolves_to(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub = world.registry_hubs.get(str(assertion.get("registry_hub")))
    alias = str(assertion.get("alias"))
    expected_device = str(assertion.get("device"))
    expected_identity = assertion.get("identity_chain")
    expected = {"device": expected_device}
    if expected_identity is not None:
        expected["identity_chain"] = str(expected_identity)

    actual = None
    if hub is not None:
        result = resolve_alias(hub, alias)
        actual = {
            "device": result.target_device_id,
            "identity_chain": result.target_identity_chain,
            "status": result.status,
        }

    passed = (
        actual is not None
        and actual["device"] == expected_device
        and (
            expected_identity is None
            or actual["identity_chain"] == str(expected_identity)
        )
    )
    return _result(
        assertion_type,
        passed,
        expected,
        f"{alias} resolves to {expected_device}",
        actual,
    )


def _alias_status(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub = world.registry_hubs.get(str(assertion.get("registry_hub")))
    alias = str(assertion.get("alias"))
    expected = str(assertion.get("expected"))
    actual = None
    if hub is not None:
        alias_record = hub.aliases.get(alias)
        actual = "not_found" if alias_record is None else alias_record.status
    return _result(
        assertion_type,
        actual == expected,
        expected,
        f"{alias} status is {expected}",
        actual,
    )


def _alias_bundle_status(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub = world.registry_hubs.get(str(assertion.get("registry_hub")))
    bundle_path = str(assertion.get("bundle_path"))
    expected = str(assertion.get("expected"))
    actual = None
    if hub is not None:
        bundle = hub.alias_bundles.get(bundle_path)
        actual = "not_found" if bundle is None else bundle.status
    return _result(
        assertion_type,
        actual == expected,
        expected,
        f"{bundle_path} bundle status is {expected}",
        actual,
    )


def _bundle_alias_resolves_to(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    assertion = dict(assertion)
    assertion["alias"] = f"{assertion.get('bundle_path')}.{assertion.get('child_name')}"
    return _alias_resolves_to(world, assertion_type, assertion)


def _alias_granted_as(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub = world.registry_hubs.get(str(assertion.get("registry_hub")))
    requested_alias = str(assertion.get("requested_alias"))
    granted_alias = str(assertion.get("granted_alias"))
    actual = None
    if hub is not None:
        alias_record = hub.aliases.get(granted_alias)
        if alias_record is not None:
            actual = {
                "requested_alias": alias_record.requested_alias,
                "granted_alias": alias_record.granted_alias or alias_record.alias,
                "status": alias_record.status,
            }
    expected = {
        "requested_alias": requested_alias,
        "granted_alias": granted_alias,
        "status": "active",
    }
    passed = actual == expected
    return _result(
        assertion_type,
        passed,
        expected,
        f"{requested_alias} granted as {granted_alias}",
        actual,
    )


def _alias_authority_ceiling(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub = world.registry_hubs.get(str(assertion.get("registry_hub")))
    alias = str(assertion.get("alias"))
    expected = str(assertion.get("expected"))
    actual = None
    if hub is not None:
        alias_record = hub.aliases.get(alias)
        if alias_record is not None:
            actual = alias_record.authority_ceiling or alias_record.authority_scope
    return _result(
        assertion_type,
        actual == expected,
        expected,
        f"{alias} authority ceiling is {expected}",
        actual,
    )


def _alias_authority_path_summary(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    requested_alias = str(assertion.get("requested_alias"))
    expected = {
        key: assertion[key]
        for key in (
            "final_status",
            "granted_alias",
            "authority_ceiling",
            "decision_count",
            "path_hubs",
        )
        if key in assertion
    }
    actual = None
    for result in reversed(world.action_results):
        authority_path = getattr(result, "authority_path", None)
        if authority_path is None:
            continue
        if authority_path.requested_alias != requested_alias:
            continue
        summary = authority_path.to_summary().to_dict()
        actual = {key: summary.get(key) for key in expected}
        break

    return _result(
        assertion_type,
        actual == expected,
        expected,
        f"{requested_alias} authority path summary matches",
        actual,
    )


def _alias_history_contains(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub = world.registry_hubs.get(str(assertion.get("registry_hub")))
    filters = {
        "alias": _optional_filter_str(assertion, "alias"),
        "device_id": _optional_device_filter(assertion),
        "status": _optional_filter_str(assertion, "status"),
    }
    records = []
    actual_context = {
        "registry_hub": str(assertion.get("registry_hub")),
        "registry_hub_found": hub is not None,
    }
    if hub is not None:
        records = [
            result.to_dict()
            for result in query_alias_history(
                hub,
                alias=filters["alias"],
                device_id=filters["device_id"],
                status=filters["status"],
            )
        ]
    return _count_result(
        assertion_type,
        assertion,
        records,
        f"alias history contains {filters}",
        expected_context={"filters": filters},
        actual_context=actual_context,
    )


def _alias_conflict_history_contains(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub = world.registry_hubs.get(str(assertion.get("registry_hub")))
    filters = {
        "alias": _optional_filter_str(assertion, "alias"),
        "device_id": _optional_device_filter(assertion),
    }
    records = []
    actual_context = {
        "registry_hub": str(assertion.get("registry_hub")),
        "registry_hub_found": hub is not None,
    }
    if hub is not None:
        records = [
            result.to_dict()
            for result in query_alias_conflicts(
                hub,
                alias=filters["alias"],
                device_id=filters["device_id"],
            )
        ]
    return _count_result(
        assertion_type,
        assertion,
        records,
        f"alias conflict history contains {filters}",
        expected_context={"filters": filters},
        actual_context=actual_context,
    )


def _authority_audit_trace_contains(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub_id = str(assertion.get("registry_hub"))
    hub = world.registry_hubs.get(hub_id)
    filters = {
        "requested_alias": _optional_filter_str(assertion, "requested_alias"),
        "granted_alias": _optional_filter_str(assertion, "granted_alias"),
        "device_id": _optional_device_filter(assertion),
        "final_status": _optional_filter_str(assertion, "final_status"),
        "outcome": _optional_filter_str(assertion, "outcome"),
        "summary_contains": _optional_filter_str(assertion, "summary_contains"),
    }
    candidates: list[dict[str, object]] = []
    actual_context = {
        "registry_hub": hub_id,
        "registry_hub_found": hub is not None,
    }
    if hub is not None:
        for trace in build_authority_audit_trace(
            hub,
            requested_alias=filters["requested_alias"],
            granted_alias=filters["granted_alias"],
            device_id=filters["device_id"],
            final_status=filters["final_status"],
        ):
            candidates.append(
                _authority_trace_candidate(
                    "retained_registry_hub",
                    trace,
                )
            )

    candidates.extend(_in_memory_authority_trace_candidates(world, hub_id, filters))
    candidates = _filter_authority_trace_candidates(candidates, filters)
    return _count_result(
        assertion_type,
        assertion,
        candidates,
        f"authority audit trace contains {filters}",
        expected_context={"filters": filters},
        actual_context=actual_context,
    )


def _authority_outcome_history_contains(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub_id = str(assertion.get("registry_hub"))
    hub = world.registry_hubs.get(hub_id)
    filters = {
        "requested_alias": _optional_filter_str(assertion, "requested_alias"),
        "granted_alias": _optional_filter_str(assertion, "granted_alias"),
        "device_id": _optional_device_filter(assertion),
        "requesting_hub": _optional_filter_str(assertion, "requesting_hub"),
        "final_status": _optional_filter_str(assertion, "final_status"),
        "status": _optional_filter_str(assertion, "status"),
        "reason": _optional_filter_str(assertion, "reason"),
        "authority_ceiling": _optional_filter_str(assertion, "authority_ceiling"),
        "fallback_used": _optional_bool_filter(assertion, "fallback_used"),
        "conflict_detected": _optional_bool_filter(assertion, "conflict_detected"),
        "policy_denied": _optional_bool_filter(assertion, "policy_denied"),
        "path_broken": _optional_bool_filter(assertion, "path_broken"),
    }
    records = []
    actual_context = {
        "registry_hub": hub_id,
        "registry_hub_found": hub is not None,
    }
    if hub is not None:
        records = [
            result.to_dict()
            for result in query_authority_outcomes(
                hub,
                requested_alias=filters["requested_alias"],
                granted_alias=filters["granted_alias"],
                device_id=filters["device_id"],
                requesting_hub=filters["requesting_hub"],
                final_status=filters["final_status"],
                status=filters["status"],
                reason=filters["reason"],
                authority_ceiling=filters["authority_ceiling"],
                fallback_used=filters["fallback_used"],
                conflict_detected=filters["conflict_detected"],
                policy_denied=filters["policy_denied"],
                path_broken=filters["path_broken"],
            )
        ]
    return _count_result(
        assertion_type,
        assertion,
        records,
        f"authority outcome history contains {filters}",
        expected_context={"filters": filters},
        actual_context=actual_context,
    )


def _quarantine_history_contains(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub = world.registry_hubs.get(str(assertion.get("registry_hub")))
    filters = {
        "device_id": _optional_device_filter(assertion),
        "reason": _optional_filter_str(assertion, "reason"),
    }
    records = []
    actual_context = {
        "registry_hub": str(assertion.get("registry_hub")),
        "registry_hub_found": hub is not None,
    }
    if hub is not None:
        records = [
            result.to_dict()
            for result in query_quarantine_events(
                hub,
                device_id=filters["device_id"],
                reason=filters["reason"],
            )
        ]
    return _count_result(
        assertion_type,
        assertion,
        records,
        f"quarantine history contains {filters}",
        expected_context={"filters": filters},
        actual_context=actual_context,
    )


def _alias_not_resolved(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub = world.registry_hubs.get(str(assertion.get("registry_hub")))
    alias = str(assertion.get("alias"))
    actual = None
    if hub is not None:
        result = resolve_alias(hub, alias)
        actual = {
            "success": result.success,
            "status": result.status,
            "reason": result.reason,
        }
    return _result(
        assertion_type,
        actual is not None and not actual["success"],
        "not resolved",
        f"{alias} is not resolved",
        actual,
    )


def _canonical_identity_unchanged(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub = world.registry_hubs.get(str(assertion.get("registry_hub")))
    device_id = str(assertion.get("device"))
    expected = str(assertion.get("expected_identity_chain"))
    actual = None
    if hub is not None and device_id in hub.devices:
        actual = hub.devices[device_id].identity_chain
    return _result(
        assertion_type,
        actual == expected,
        expected,
        f"{device_id} canonical identity remains unchanged",
        actual,
    )


def _mailbox_registered(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub_id = str(assertion.get("registry_hub"))
    hub = world.registry_hubs.get(hub_id)
    mailbox_id = str(assertion.get("mailbox_id"))
    expected = {
        key: assertion[key]
        for key in ("address", "canonical_device_id", "scope")
        if key in assertion
    }
    expected["mailbox_id"] = mailbox_id
    actual = {
        "registry_hub": hub_id,
        "registry_hub_found": hub is not None,
        "mailbox_found": False,
    }
    if hub is not None:
        mailbox = get_mailbox(hub, mailbox_id)
        if mailbox is not None:
            actual.update(
                {
                    "mailbox_found": True,
                    "mailbox_id": mailbox.mailbox_id,
                    "address": mailbox.address.raw,
                    "canonical_device_id": mailbox.canonical_device_id,
                    "scope": mailbox.scope,
                }
            )

    passed = bool(actual["mailbox_found"])
    if passed and "address" in assertion:
        passed = actual["address"] == str(assertion["address"])
    if passed and "canonical_device_id" in assertion:
        passed = actual["canonical_device_id"] == str(assertion["canonical_device_id"])
    if passed and "scope" in assertion:
        passed = actual["scope"] == str(assertion["scope"])
    return _result(
        assertion_type,
        passed,
        expected,
        f"mailbox registered: {mailbox_id}",
        actual,
    )


def _mailbox_supports_lane(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub_id = str(assertion.get("registry_hub"))
    hub = world.registry_hubs.get(hub_id)
    mailbox_id = str(assertion.get("mailbox_id"))
    lane_signature = str(assertion.get("lane_signature"))
    enabled_filter = _optional_bool_filter(assertion, "enabled")
    expected = {
        "mailbox_id": mailbox_id,
        "lane_signature": lane_signature,
        "enabled": enabled_filter,
    }
    capabilities = []
    actual = {
        "registry_hub": hub_id,
        "registry_hub_found": hub is not None,
        "capabilities": capabilities,
    }
    if hub is not None:
        capabilities = [
            capability.to_summary()
            for capability in list_mailbox_capabilities(hub, mailbox_id)
            if capability.lane_signature == lane_signature
        ]
        actual["capabilities"] = capabilities

    if enabled_filter is None:
        passed = bool(capabilities)
    else:
        passed = any(capability["enabled"] is enabled_filter for capability in capabilities)
    return _result(
        assertion_type,
        passed,
        expected,
        f"mailbox {mailbox_id} supports lane {lane_signature}",
        actual,
    )


def _message_delivery_result_contains(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub_id = str(assertion.get("registry_hub"))
    hub = world.registry_hubs.get(hub_id)
    filters = {
        "message_id": _optional_filter_str(assertion, "message_id"),
        "recipient_address": _optional_filter_str(assertion, "recipient_address"),
        "mailbox_id": _optional_filter_str(assertion, "mailbox_id"),
        "status": _optional_filter_str(assertion, "status"),
        "reason": _optional_filter_str(assertion, "reason"),
        "lane_signature": _optional_filter_str(assertion, "lane_signature"),
        "endpoint_id": _optional_filter_str(assertion, "endpoint_id"),
        "fallback_action": _optional_filter_str(assertion, "fallback_action"),
    }
    records = []
    actual_context = {
        "registry_hub": hub_id,
        "registry_hub_found": hub is not None,
    }
    if hub is not None:
        records = [
            result.to_summary()
            for result in list_message_delivery_results(
                hub,
                message_id=filters["message_id"],
                recipient_address=filters["recipient_address"],
                mailbox_id=filters["mailbox_id"],
                status=filters["status"],
                reason=filters["reason"],
                lane_signature=filters["lane_signature"],
            )
        ]
        records = [
            record
            for record in records
            if (
                filters["endpoint_id"] is None
                or record["endpoint_id"] == filters["endpoint_id"]
            )
            and (
                filters["fallback_action"] is None
                or record["fallback_action"] == filters["fallback_action"]
            )
        ]
    return _count_result(
        assertion_type,
        assertion,
        records,
        f"message delivery result contains {filters}",
        expected_context={"filters": filters},
        actual_context=actual_context,
    )


def _mailbox_inbox_contains(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub_id = str(assertion.get("registry_hub"))
    hub = world.registry_hubs.get(hub_id)
    mailbox_id = str(assertion.get("mailbox_id"))
    filters = {
        "message_id": _optional_filter_str(assertion, "message_id"),
        "sender_id": _optional_filter_str(assertion, "sender_id"),
        "recipient_address": _optional_filter_str(assertion, "recipient_address"),
        "lane_signature": _optional_filter_str(assertion, "lane_signature"),
        "payload_kind": _optional_filter_str(assertion, "payload_kind"),
        "payload": assertion.get("payload") if "payload" in assertion else None,
    }
    records = []
    actual_context = {
        "registry_hub": hub_id,
        "registry_hub_found": hub is not None,
        "mailbox_id": mailbox_id,
    }
    if hub is not None:
        records = [
            envelope.to_summary()
            for envelope in get_mailbox_inbox(hub, mailbox_id)
        ]
        records = [
            record
            for record in records
            if _matches_message_filters(record, assertion, filters)
        ]
    return _count_result(
        assertion_type,
        assertion,
        records,
        f"mailbox inbox contains {filters}",
        expected_context={"filters": filters},
        actual_context=actual_context,
    )


def _encryption_identity_registered(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub_id = str(assertion.get("registry_hub"))
    hub = world.registry_hubs.get(hub_id)
    identity_id = str(assertion.get("encryption_identity_id"))
    expected = {
        key: assertion[key]
        for key in ("subject_id", "subject_kind", "profile", "status")
        if key in assertion
    }
    expected["encryption_identity_id"] = identity_id
    actual = {
        "registry_hub": hub_id,
        "registry_hub_found": hub is not None,
        "identity_found": False,
    }
    if hub is not None:
        identity = hub.encryption_identities.get(identity_id)
        if identity is not None:
            actual.update(identity.to_summary())
            actual["identity_found"] = True

    passed = _record_matches_expected(actual, expected, "identity_found")
    return _result(
        assertion_type,
        passed,
        expected,
        f"encryption identity registered: {identity_id}",
        actual,
    )


def _key_bundle_registered(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub_id = str(assertion.get("registry_hub"))
    hub = world.registry_hubs.get(hub_id)
    key_bundle_id = str(assertion.get("key_bundle_id"))
    expected = {
        key: assertion[key]
        for key in ("encryption_identity_id", "profile", "status")
        if key in assertion
    }
    expected["key_bundle_id"] = key_bundle_id
    actual = {
        "registry_hub": hub_id,
        "registry_hub_found": hub is not None,
        "key_bundle_found": False,
    }
    if hub is not None:
        key_bundle = hub.key_bundle_references.get(key_bundle_id)
        if key_bundle is not None:
            actual.update(key_bundle.to_summary())
            actual["key_bundle_found"] = True

    passed = _record_matches_expected(actual, expected, "key_bundle_found")
    return _result(
        assertion_type,
        passed,
        expected,
        f"key bundle registered: {key_bundle_id}",
        actual,
    )


def _mailbox_encryption_binding_registered(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub_id = str(assertion.get("registry_hub"))
    hub = world.registry_hubs.get(hub_id)
    mailbox_id = str(assertion.get("mailbox_id"))
    expected = {
        key: assertion[key]
        for key in ("encryption_identity_id", "key_bundle_id", "profile", "status")
        if key in assertion
    }
    expected["mailbox_id"] = mailbox_id
    if "lane_signature" in assertion:
        expected["lane_signature"] = str(assertion["lane_signature"])
    actual = {
        "registry_hub": hub_id,
        "registry_hub_found": hub is not None,
        "binding_found": False,
    }
    if hub is not None:
        binding = hub.mailbox_encryption_bindings.get(mailbox_id)
        if binding is not None:
            actual.update(binding.to_summary())
            actual["binding_found"] = True

    passed = _record_matches_expected(actual, expected, "binding_found")
    if passed and "lane_signature" in expected:
        passed = expected["lane_signature"] in actual.get("required_for_lanes", [])
    return _result(
        assertion_type,
        passed,
        expected,
        f"mailbox encryption binding registered: {mailbox_id}",
        actual,
    )


def _mailbox_encryption_policy_registered(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub_id = str(assertion.get("registry_hub"))
    hub = world.registry_hubs.get(hub_id)
    policy_id = str(assertion.get("policy_id"))
    expected = {
        key: assertion[key]
        for key in ("mailbox_id", "allow_plaintext_fallback")
        if key in assertion
    }
    expected["policy_id"] = policy_id
    if "lane_signature" in assertion:
        expected["lane_signature"] = str(assertion["lane_signature"])
    if "profile" in assertion:
        expected["profile"] = str(assertion["profile"])
    actual = {
        "registry_hub": hub_id,
        "registry_hub_found": hub is not None,
        "policy_found": False,
    }
    if hub is not None:
        policy = hub.mailbox_encryption_policies.get(policy_id)
        if policy is not None:
            actual.update(policy.to_summary())
            actual["policy_found"] = True

    direct_expected = {
        key: value
        for key, value in expected.items()
        if key not in {"lane_signature", "profile"}
    }
    passed = _record_matches_expected(actual, direct_expected, "policy_found")
    if passed and "lane_signature" in expected:
        passed = expected["lane_signature"] in actual.get("required_for_lanes", [])
    if passed and "profile" in expected:
        passed = expected["profile"] in actual.get("allowed_profiles", [])
    return _result(
        assertion_type,
        passed,
        expected,
        f"mailbox encryption policy registered: {policy_id}",
        actual,
    )


def _encryption_policy_decision_contains(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub_id = str(assertion.get("registry_hub"))
    hub = world.registry_hubs.get(hub_id)
    filters = {
        "registry_hub": hub_id,
        "policy_id": _optional_filter_str(assertion, "policy_id"),
        "mailbox_id": _optional_filter_str(assertion, "mailbox_id"),
        "lane_signature": _optional_filter_str(assertion, "lane_signature"),
        "message_id": _optional_filter_str(assertion, "message_id"),
        "status": _optional_filter_str(assertion, "status"),
        "reason": _optional_filter_str(assertion, "reason"),
        "encryption_required": _optional_bool_filter(
            assertion,
            "encryption_required",
        ),
        "envelope_accepted": _optional_bool_filter(assertion, "envelope_accepted"),
        "profile": _optional_filter_str(assertion, "profile"),
        "encryption_identity_id": _optional_filter_str(
            assertion,
            "encryption_identity_id",
        ),
        "key_bundle_id": _optional_filter_str(assertion, "key_bundle_id"),
    }
    query_filters = {
        key: value
        for key, value in filters.items()
        if key != "registry_hub"
    }
    records = []
    source = "retained_history"
    if hub is not None:
        records = [
            decision.to_summary()
            for decision in query_encryption_policy_decisions(hub, **query_filters)
        ]
    if not records:
        source = "action_results"
        records = [
            decision.to_summary()
            for decision in world.action_results
            if isinstance(decision, EncryptionPolicyDecision)
        ]
        records = [
            record
            for record in records
            if _matches_encryption_policy_decision_filters(record, filters)
        ]
    return _count_result(
        assertion_type,
        assertion,
        records,
        f"encryption policy decision contains {filters}",
        expected_context={"filters": filters},
        actual_context={
            "registry_hub": hub_id,
            "registry_hub_found": hub_id in world.registry_hubs,
            "source": source,
        },
    )


def _encrypted_delivery_result_contains(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub_id = str(assertion.get("registry_hub"))
    hub = world.registry_hubs.get(hub_id)
    filters = {
        "registry_hub": hub_id,
        "request_id": _optional_filter_str(assertion, "request_id"),
        "message_id": _optional_filter_str(assertion, "message_id"),
        "mailbox_id": _optional_filter_str(assertion, "mailbox_id"),
        "lane_signature": _optional_filter_str(assertion, "lane_signature"),
        "status": _optional_filter_str(assertion, "status"),
        "reason": _optional_filter_str(assertion, "reason"),
        "delivery_attempted": _optional_bool_filter(
            assertion,
            "delivery_attempted",
        ),
        "delivery_allowed": _optional_bool_filter(assertion, "delivery_allowed"),
        "policy_required": _optional_bool_filter(assertion, "policy_required"),
        "gate_status": _optional_filter_str(assertion, "gate_status"),
        "gate_reason": _optional_filter_str(assertion, "gate_reason"),
        "delivery_status": _optional_filter_str(assertion, "delivery_status"),
        "delivery_reason": _optional_filter_str(assertion, "delivery_reason"),
        "endpoint_id": _optional_filter_str(assertion, "endpoint_id"),
    }
    source = "retained_history"
    if hub is not None and hub.encrypted_delivery_result_history:
        records = [
            result.to_summary()
            for result in query_encrypted_delivery_results(
                hub,
                **_encrypted_delivery_result_query_filters(filters),
            )
        ]
    else:
        source = "action_results"
        records = [
            result.to_summary()
            for result in world.action_results
            if isinstance(result, EncryptedDeliveryResult)
        ]
        records = [
            record
            for record in records
            if _matches_encrypted_delivery_result_filters(record, filters)
        ]
    return _count_result(
        assertion_type,
        assertion,
        records,
        f"encrypted delivery result contains {filters}",
        expected_context={"filters": filters},
        actual_context={
            "registry_hub": hub_id,
            "registry_hub_found": hub_id in world.registry_hubs,
            "source": source,
        },
    )


def _encrypted_delivery_audit_contains(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub_id = str(assertion.get("registry_hub"))
    hub = world.registry_hubs.get(hub_id)
    filters = {
        "registry_hub": hub_id,
        "request_id": _optional_filter_str(assertion, "request_id"),
        "message_id": _optional_filter_str(assertion, "message_id"),
        "mailbox_id": _optional_filter_str(assertion, "mailbox_id"),
        "lane_signature": _optional_filter_str(assertion, "lane_signature"),
        "gate_status": _optional_filter_str(assertion, "gate_status"),
        "gate_reason": _optional_filter_str(assertion, "gate_reason"),
        "delivery_status": _optional_filter_str(assertion, "delivery_status"),
        "delivery_reason": _optional_filter_str(assertion, "delivery_reason"),
        "policy_id": _optional_filter_str(assertion, "policy_id"),
        "encryption_required": _optional_bool_filter(
            assertion,
            "encryption_required",
        ),
        "envelope_accepted": _optional_bool_filter(assertion, "envelope_accepted"),
    }
    source = "retained_history"
    if hub is not None and hub.encrypted_delivery_result_history:
        records = [
            _encrypted_delivery_audit_summary(result)
            for result in query_encrypted_delivery_results(
                hub,
                **_encrypted_delivery_audit_query_filters(filters),
            )
        ]
        records = [
            record
            for record in records
            if _matches_encrypted_delivery_audit_filters(record, filters)
        ]
    else:
        source = "action_results"
        records = [
            _encrypted_delivery_audit_summary(result)
            for result in world.action_results
            if isinstance(result, EncryptedDeliveryResult)
        ]
        records = [
            record
            for record in records
            if _matches_encrypted_delivery_audit_filters(record, filters)
        ]
    return _count_result(
        assertion_type,
        assertion,
        records,
        f"encrypted delivery audit contains {filters}",
        expected_context={"filters": filters},
        actual_context={
            "registry_hub": hub_id,
            "registry_hub_found": hub_id in world.registry_hubs,
            "source": source,
        },
    )


def _held_stream_offer_contains(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub_id = str(assertion.get("registry_hub"))
    hub = world.registry_hubs.get(hub_id)
    filters = {
        "offer_id": _optional_filter_str(assertion, "offer_id"),
        "requester_id": _optional_filter_str(assertion, "requester_id"),
        "target_handle": _optional_filter_str(assertion, "target_handle"),
        "lane_signature": _optional_filter_str(assertion, "lane_signature"),
        "requested_mode": _optional_filter_str(assertion, "requested_mode"),
        "visibility_tier": _optional_int_field(assertion, "visibility_tier"),
        "status": _optional_filter_str(assertion, "status"),
        "rendezvous_scope": _optional_filter_str(assertion, "rendezvous_scope"),
    }
    records = []
    if hub is not None:
        records = [
            offer.to_summary()
            for offer in query_held_stream_offers(
                hub,
                offer_id=filters["offer_id"],
                requester_id=filters["requester_id"],
                target_handle=filters["target_handle"],
                lane_signature=filters["lane_signature"],
                requested_mode=filters["requested_mode"],
                visibility_tier=filters["visibility_tier"],
                status=filters["status"],
                rendezvous_scope=filters["rendezvous_scope"],
            )
        ]
    return _count_result(
        assertion_type,
        assertion,
        records,
        f"held stream offer contains {filters}",
        expected_context={"filters": filters},
        actual_context={
            "registry_hub": hub_id,
            "registry_hub_found": hub is not None,
        },
    )


def _rendezvous_poll_result_contains(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub_id = str(assertion.get("registry_hub"))
    hub = world.registry_hubs.get(hub_id)
    filters = {
        "registry_hub": hub_id,
        "request_id": _optional_filter_str(assertion, "request_id"),
        "polling_hub_id": _optional_filter_str(assertion, "polling_hub_id"),
        "parent_hub_id": _optional_filter_str(assertion, "parent_hub_id"),
        "target_scope": _optional_filter_str(assertion, "target_scope"),
        "visibility_tier": _optional_int_field(assertion, "visibility_tier"),
        "status": _optional_filter_str(assertion, "status"),
        "reason": _optional_filter_str(assertion, "reason"),
        "matched_offer_id": _optional_filter_str(assertion, "matched_offer_id"),
        "matched_offer_ids": _optional_str_sequence_filter(
            assertion,
            "matched_offer_ids",
        ),
    }
    source = "action_results"
    records: list[dict[str, object]]
    if hub is not None and hub.rendezvous_poll_result_history:
        source = "retained_history"
        records = [
            result.to_summary()
            for result in query_rendezvous_poll_results(
                hub,
                request_id=filters["request_id"],
                polling_hub_id=filters["polling_hub_id"],
                parent_hub_id=filters["parent_hub_id"] or hub_id,
                target_scope=filters["target_scope"],
                visibility_tier=filters["visibility_tier"],
                status=filters["status"],
                reason=filters["reason"],
                matched_offer_id=filters["matched_offer_id"],
            )
        ]
        records = [
            record
            for record in records
            if _matches_rendezvous_poll_result_filters(record, filters)
        ]
    else:
        records = [
            result.to_summary()
            for result in world.action_results
            if isinstance(result, RendezvousPollResult)
        ]
        records = [
            record
            for record in records
            if _matches_rendezvous_poll_result_filters(record, filters)
        ]
    return _count_result(
        assertion_type,
        assertion,
        records,
        f"rendezvous poll result contains {filters}",
        expected_context={"filters": filters},
        actual_context={
            "registry_hub": hub_id,
            "registry_hub_found": hub is not None,
            "source": source,
        },
    )


def _lane_admission_decision_contains(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub_id = str(assertion.get("registry_hub"))
    hub = world.registry_hubs.get(hub_id)
    filters = {
        "registry_hub": hub_id,
        "decision_id": _optional_filter_str(assertion, "decision_id"),
        "policy_id": _optional_filter_str(assertion, "policy_id"),
        "offer_id": _optional_filter_str(assertion, "offer_id"),
        "request_id": _optional_filter_str(assertion, "request_id"),
        "hub_id": _optional_filter_str(assertion, "hub_id"),
        "requester_id": _optional_filter_str(assertion, "requester_id"),
        "target_handle": _optional_filter_str(assertion, "target_handle"),
        "target_scope": _optional_filter_str(assertion, "target_scope"),
        "lane_signature": _optional_filter_str(assertion, "lane_signature"),
        "status": _optional_filter_str(assertion, "status"),
        "reason": _optional_filter_str(assertion, "reason"),
        "allowed": _optional_bool_filter(assertion, "allowed"),
    }
    source = "action_results"
    records: list[dict[str, object]]
    if hub is not None and hub.lane_admission_decision_history:
        source = "retained_history"
        records = [
            decision.to_summary()
            for decision in query_lane_admission_decisions(
                hub,
                decision_id=filters["decision_id"],
                policy_id=filters["policy_id"],
                offer_id=filters["offer_id"],
                request_id=filters["request_id"],
                hub_id=filters["hub_id"] or hub_id,
                requester_id=filters["requester_id"],
                target_handle=filters["target_handle"],
                target_scope=filters["target_scope"],
                lane_signature=filters["lane_signature"],
                status=filters["status"],
                reason=filters["reason"],
                allowed=filters["allowed"],
            )
        ]
        records = [
            record
            for record in records
            if _matches_lane_admission_decision_filters(record, filters)
        ]
    else:
        records = [
            result.to_summary()
            for result in world.action_results
            if isinstance(result, LaneAdmissionDecision)
        ]
        records = [
            record
            for record in records
            if _matches_lane_admission_decision_filters(record, filters)
        ]
    return _count_result(
        assertion_type,
        assertion,
        records,
        f"lane admission decision contains {filters}",
        expected_context={"filters": filters},
        actual_context={
            "registry_hub": hub_id,
            "registry_hub_found": hub is not None,
            "source": source,
        },
    )


def _stream_offer_lifecycle_plan_contains(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub_id = str(assertion.get("registry_hub"))
    filters = {
        "hub_id": hub_id,
        "checked_at": _optional_int_field(assertion, "checked_at"),
        "expired_offer_id": _optional_filter_str(assertion, "expired_offer_id"),
        "expired_offer_ids": _optional_str_sequence_filter(
            assertion,
            "expired_offer_ids",
        ),
        "cleanup_candidate_offer_id": _optional_filter_str(
            assertion,
            "cleanup_candidate_offer_id",
        ),
        "cleanup_candidate_offer_ids": _optional_str_sequence_filter(
            assertion,
            "cleanup_candidate_offer_ids",
        ),
        "active_offer_id": _optional_filter_str(assertion, "active_offer_id"),
        "active_offer_ids": _optional_str_sequence_filter(
            assertion,
            "active_offer_ids",
        ),
        "ignored_offer_id": _optional_filter_str(assertion, "ignored_offer_id"),
        "ignored_offer_ids": _optional_str_sequence_filter(
            assertion,
            "ignored_offer_ids",
        ),
    }
    records = [
        result.to_summary()
        for result in world.action_results
        if isinstance(result, StreamOfferLifecyclePlan)
    ]
    records = [
        record
        for record in records
        if _matches_stream_offer_lifecycle_plan_filters(record, filters)
    ]
    return _count_result(
        assertion_type,
        assertion,
        records,
        f"stream offer lifecycle plan contains {filters}",
        expected_context={"filters": filters},
        actual_context={
            "registry_hub": hub_id,
            "registry_hub_found": hub_id in world.registry_hubs,
            "source": "action_results",
        },
    )


def _stream_offer_lifecycle_apply_result_contains(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub_id = str(assertion.get("registry_hub"))
    filters = {
        "hub_id": hub_id,
        "plan_checked_at": _optional_int_field(assertion, "plan_checked_at"),
        "applied_offer_id": _optional_filter_str(assertion, "applied_offer_id"),
        "applied_offer_ids": _optional_str_sequence_filter(
            assertion,
            "applied_offer_ids",
        ),
        "skipped_offer_id": _optional_filter_str(assertion, "skipped_offer_id"),
        "skipped_offer_ids": _optional_str_sequence_filter(
            assertion,
            "skipped_offer_ids",
        ),
        "missing_offer_id": _optional_filter_str(assertion, "missing_offer_id"),
        "missing_offer_ids": _optional_str_sequence_filter(
            assertion,
            "missing_offer_ids",
        ),
        "recorded_transition_count": _optional_int_field(
            assertion,
            "recorded_transition_count",
        ),
    }
    records = [
        result.to_summary()
        for result in world.action_results
        if isinstance(result, StreamOfferLifecycleApplyResult)
    ]
    records = [
        record
        for record in records
        if _matches_stream_offer_lifecycle_apply_result_filters(record, filters)
    ]
    return _count_result(
        assertion_type,
        assertion,
        records,
        f"stream offer lifecycle apply result contains {filters}",
        expected_context={"filters": filters},
        actual_context={
            "registry_hub": hub_id,
            "registry_hub_found": hub_id in world.registry_hubs,
            "source": "action_results",
        },
    )


def _stream_offer_lifecycle_explanation_contains(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub_id = str(assertion.get("registry_hub"))
    hub = world.registry_hubs.get(hub_id)
    filters = _stream_offer_lifecycle_explanation_filters(assertion, hub_id)
    source = "action_results"
    records: list[dict[str, object]]
    if hub is not None and hub.stream_offer_lifecycle_explanation_history:
        source = "retained_history"
        records = [
            explanation.to_summary()
            for explanation in query_stream_offer_lifecycle_explanations(
                hub,
                hub_id=filters["hub_id"],
                offer_id=filters["offer_id"],
                category=filters["category"],
                reason=filters["reason"],
                status=filters["status"],
                source=filters["source"],
            )
        ]
    else:
        records = [
            result.to_summary()
            for result in world.action_results
            if isinstance(result, StreamOfferLifecycleExplanation)
        ]
    records = [
        record
        for record in records
        if _matches_stream_offer_lifecycle_explanation_filters(record, filters)
    ]
    return _count_result(
        assertion_type,
        assertion,
        records,
        f"stream offer lifecycle explanation contains {filters}",
        expected_context={"filters": filters},
        actual_context={
            "registry_hub": hub_id,
            "registry_hub_found": hub is not None,
            "source": source,
        },
    )


def _stream_offer_lifecycle_explanation_history_contains(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub_id = str(assertion.get("registry_hub"))
    hub = world.registry_hubs.get(hub_id)
    filters = _stream_offer_lifecycle_explanation_filters(assertion, hub_id)
    records: list[dict[str, object]] = []
    if hub is not None:
        records = [
            explanation.to_summary()
            for explanation in query_stream_offer_lifecycle_explanations(
                hub,
                hub_id=filters["hub_id"],
                offer_id=filters["offer_id"],
                category=filters["category"],
                reason=filters["reason"],
                status=filters["status"],
                source=filters["source"],
            )
        ]
        records = [
            record
            for record in records
            if _matches_stream_offer_lifecycle_explanation_filters(record, filters)
        ]
    return _count_result(
        assertion_type,
        assertion,
        records,
        f"stream offer lifecycle explanation history contains {filters}",
        expected_context={"filters": filters},
        actual_context={
            "registry_hub": hub_id,
            "registry_hub_found": hub is not None,
            "source": "retained_history",
        },
    )


def _stream_offer_lifecycle_audit_summary_contains(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub_id = str(assertion.get("registry_hub"))
    filters = {
        "hub_id": hub_id,
        "total_transitions": _optional_int_field(assertion, "total_transitions"),
        "explanation_count": _optional_int_field(assertion, "explanation_count"),
        "offer_id": _optional_filter_str(assertion, "offer_id"),
        "offer_count": _optional_int_field(assertion, "offer_count"),
        "status": _optional_filter_str(assertion, "status"),
        "status_count": _optional_int_field(assertion, "status_count"),
        "reason": _optional_filter_str(assertion, "reason"),
        "reason_count": _optional_int_field(assertion, "reason_count"),
        "category": _optional_filter_str(assertion, "category"),
        "category_count": _optional_int_field(assertion, "category_count"),
    }
    records = [
        result.to_summary()
        for result in world.action_results
        if isinstance(result, StreamOfferLifecycleAuditSummary)
    ]
    records = [
        record
        for record in records
        if _matches_stream_offer_lifecycle_audit_summary_filters(record, filters)
    ]
    return _count_result(
        assertion_type,
        assertion,
        records,
        f"stream offer lifecycle audit summary contains {filters}",
        expected_context={"filters": filters},
        actual_context={
            "registry_hub": hub_id,
            "registry_hub_found": hub_id in world.registry_hubs,
            "source": "action_results",
        },
    )


def _stream_offer_lifecycle_retention_decision_contains(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub_id = str(assertion.get("registry_hub"))
    filters = _stream_offer_lifecycle_retention_filters(assertion, hub_id)
    records = [
        result.to_summary()
        for result in world.action_results
        if isinstance(result, StreamOfferLifecycleExplanationRetentionDecision)
    ]
    records = [
        record
        for record in records
        if _matches_stream_offer_lifecycle_retention_decision_filters(record, filters)
    ]
    return _count_result(
        assertion_type,
        assertion,
        records,
        f"stream offer lifecycle retention decision contains {filters}",
        expected_context={"filters": filters},
        actual_context={
            "registry_hub": hub_id,
            "registry_hub_found": hub_id in world.registry_hubs,
            "source": "action_results",
        },
    )


def _stream_offer_lifecycle_pruning_plan_contains(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub_id = str(assertion.get("registry_hub"))
    filters = _stream_offer_lifecycle_retention_filters(assertion, hub_id)
    filters.update(
        {
            "candidate_explanation_keys": filters["prune_candidate_explanation_keys"],
            "retained_explanation_keys": filters["kept_explanation_keys"],
            "candidate_count": _optional_int_field(assertion, "candidate_count"),
            "retained_count": _optional_int_field(assertion, "retained_count"),
            "ignored_count": _optional_int_field(assertion, "ignored_count"),
            "category": _optional_filter_str(assertion, "category"),
            "category_count": _optional_int_field(assertion, "category_count"),
            "reason": _optional_filter_str(assertion, "reason"),
            "reason_count": _optional_int_field(assertion, "reason_count"),
            "source": _optional_filter_str(assertion, "source"),
            "source_count": _optional_int_field(assertion, "source_count"),
        }
    )
    records = [
        result.to_summary()
        for result in world.action_results
        if isinstance(result, StreamOfferLifecycleExplanationPruningPlan)
    ]
    records = [
        record
        for record in records
        if _matches_stream_offer_lifecycle_pruning_plan_filters(record, filters)
    ]
    return _count_result(
        assertion_type,
        assertion,
        records,
        f"stream offer lifecycle pruning plan contains {filters}",
        expected_context={"filters": filters},
        actual_context={
            "registry_hub": hub_id,
            "registry_hub_found": hub_id in world.registry_hubs,
            "source": "action_results",
        },
    )


def _stream_offer_lifecycle_pruning_apply_result_contains(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub_id = str(assertion.get("registry_hub"))
    filters = {
        "hub_id": hub_id,
        "policy_id": _optional_filter_str(assertion, "policy_id"),
        "pruned_explanation_key": _optional_filter_str(
            assertion,
            "pruned_explanation_key",
        ),
        "pruned_explanation_keys": _optional_str_sequence_filter(
            assertion,
            "pruned_explanation_keys",
        ),
        "retained_explanation_key": _optional_filter_str(
            assertion,
            "retained_explanation_key",
        ),
        "retained_explanation_keys": _optional_str_sequence_filter(
            assertion,
            "retained_explanation_keys",
        ),
        "ignored_explanation_key": _optional_filter_str(
            assertion,
            "ignored_explanation_key",
        ),
        "ignored_explanation_keys": _optional_str_sequence_filter(
            assertion,
            "ignored_explanation_keys",
        ),
        "missing_explanation_key": _optional_filter_str(
            assertion,
            "missing_explanation_key",
        ),
        "missing_explanation_keys": _optional_str_sequence_filter(
            assertion,
            "missing_explanation_keys",
        ),
        "pruned_count": _optional_int_field(assertion, "pruned_count"),
        "retained_count": _optional_int_field(assertion, "retained_count"),
        "ignored_count": _optional_int_field(assertion, "ignored_count"),
        "missing_count": _optional_int_field(assertion, "missing_count"),
    }
    records = [
        result.to_summary()
        for result in world.action_results
        if isinstance(result, StreamOfferLifecycleExplanationPruningApplyResult)
    ]
    records = [
        record
        for record in records
        if _matches_stream_offer_lifecycle_pruning_apply_result_filters(
            record,
            filters,
        )
    ]
    return _count_result(
        assertion_type,
        assertion,
        records,
        f"stream offer lifecycle pruning apply result contains {filters}",
        expected_context={"filters": filters},
        actual_context={
            "registry_hub": hub_id,
            "registry_hub_found": hub_id in world.registry_hubs,
            "source": "action_results",
        },
    )


def _stream_offer_status_transition_contains(
    world: World,
    assertion_type: str,
    assertion: dict[str, Any],
) -> AssertionResult:
    hub_id = str(assertion.get("registry_hub"))
    hub = world.registry_hubs.get(hub_id)
    filters = {
        "registry_hub": hub_id,
        "offer_id": _optional_filter_str(assertion, "offer_id"),
        "hub_id": _optional_filter_str(assertion, "hub_id"),
        "previous_status": _optional_filter_str(assertion, "previous_status"),
        "new_status": _optional_filter_str(assertion, "new_status"),
        "status": _optional_filter_str(assertion, "status"),
        "reason": _optional_filter_str(assertion, "reason"),
        "actor_id": _optional_filter_str(assertion, "actor_id"),
        "request_id": _optional_filter_str(assertion, "request_id"),
    }
    source = "action_results"
    records: list[dict[str, object]]
    if hub is not None and hub.stream_offer_status_transition_history:
        source = "retained_history"
        records = [
            transition.to_summary()
            for transition in query_stream_offer_status_transitions(
                hub,
                offer_id=filters["offer_id"],
                hub_id=filters["hub_id"] or hub_id,
                previous_status=filters["previous_status"],
                new_status=filters["new_status"],
                status=filters["status"],
                reason=filters["reason"],
                actor_id=filters["actor_id"],
                request_id=filters["request_id"],
            )
        ]
        records = [
            record
            for record in records
            if _matches_stream_offer_status_transition_filters(record, filters)
        ]
    else:
        records = [
            result.to_summary()
            for result in world.action_results
            if isinstance(result, StreamOfferStatusTransition)
        ]
        records = [
            record
            for record in records
            if _matches_stream_offer_status_transition_filters(record, filters)
        ]
    return _count_result(
        assertion_type,
        assertion,
        records,
        f"stream offer status transition contains {filters}",
        expected_context={"filters": filters},
        actual_context={
            "registry_hub": hub_id,
            "registry_hub_found": hub is not None,
            "source": source,
        },
    )


def _result(
    assertion_type: str,
    passed: bool,
    expected: Any,
    message: str,
    actual: Any | None = None,
) -> AssertionResult:
    if passed:
        return AssertionResult(
            assertion_type=assertion_type,
            passed=True,
            message=message,
            expected=expected,
            actual=actual,
        )
    return AssertionResult(
        assertion_type=assertion_type,
        passed=False,
        message=f"{message} failed",
        expected=expected,
        actual=actual,
    )


def _count_result(
    assertion_type: str,
    assertion: dict[str, Any],
    records: list[dict[str, object]],
    message: str,
    *,
    expected_context: dict[str, object] | None = None,
    actual_context: dict[str, object] | None = None,
) -> AssertionResult:
    count = len(records)
    expected_count = _optional_int_field(assertion, "expected_count")
    min_count = _optional_int_field(assertion, "min_count")
    expected: dict[str, object] = {
        "expected_count": expected_count,
        "min_count": min_count,
    }
    if expected_context is not None:
        expected.update(expected_context)
    actual = {
        "count": count,
        "records": records,
    }
    if actual_context is not None:
        actual.update(actual_context)

    passed = True
    if expected_count is not None:
        passed = passed and count == expected_count
    if min_count is not None:
        passed = passed and count >= min_count
    if expected_count is None and min_count is None:
        passed = count > 0
        expected = {"min_count": 1}
        if expected_context is not None:
            expected.update(expected_context)

    return _result(
        assertion_type,
        passed,
        expected,
        message,
        actual,
    )


def _authority_trace_candidate(
    source: str,
    trace: dict[str, object],
) -> dict[str, object]:
    return {
        "source": source,
        "trace": trace,
        "explanation": explain_authority_trace(trace),
    }


def _in_memory_authority_trace_candidates(
    world: World,
    hub_id: str,
    filters: dict[str, str | None],
) -> list[dict[str, object]]:
    candidates = []
    for result in world.action_results:
        authority_path = getattr(result, "authority_path", None)
        if authority_path is None:
            continue
        if authority_path.final_status in {"approved_here", "fallback_granted"}:
            continue
        path_hub_ids = {decision.hub_id for decision in authority_path.decisions}
        path_hub_ids.add(authority_path.requesting_hub_id)
        if hub_id not in path_hub_ids:
            continue
        if (
            filters["requested_alias"] is not None
            and authority_path.requested_alias != filters["requested_alias"]
        ):
            continue
        if (
            filters["granted_alias"] is not None
            and authority_path.granted_alias != filters["granted_alias"]
        ):
            continue
        if (
            filters["device_id"] is not None
            and authority_path.target_device_id != filters["device_id"]
        ):
            continue
        if (
            filters["final_status"] is not None
            and authority_path.final_status != filters["final_status"]
        ):
            continue
        candidates.append(
            _authority_trace_candidate(
                "in_memory_authority_path",
                summarize_authority_path(authority_path),
            )
        )
    return candidates


def _filter_authority_trace_candidates(
    candidates: list[dict[str, object]],
    filters: dict[str, str | None],
) -> list[dict[str, object]]:
    outcome = filters["outcome"]
    summary_contains = filters["summary_contains"]
    if outcome is None and summary_contains is None:
        return candidates

    filtered = []
    for candidate in candidates:
        explanation = candidate["explanation"]
        if not isinstance(explanation, dict):
            continue
        if outcome is not None and explanation.get("outcome") != outcome:
            continue
        if summary_contains is not None:
            summary = str(explanation.get("summary", ""))
            if summary_contains not in summary:
                continue
        filtered.append(candidate)
    return filtered


def _optional_filter_str(
    assertion: dict[str, Any],
    field_name: str,
) -> str | None:
    if field_name not in assertion or assertion[field_name] is None:
        return None
    return str(assertion[field_name])


def _optional_device_filter(assertion: dict[str, Any]) -> str | None:
    if "device_id" in assertion and assertion["device_id"] is not None:
        return str(assertion["device_id"])
    if "device" in assertion and assertion["device"] is not None:
        return str(assertion["device"])
    return None


def _optional_bool_filter(assertion: dict[str, Any], field_name: str) -> bool | None:
    if field_name not in assertion or assertion[field_name] is None:
        return None
    value = assertion[field_name]
    if isinstance(value, bool):
        return value
    raise ValueError(f"{field_name} must be a boolean")


def _optional_int_field(assertion: dict[str, Any], field_name: str) -> int | None:
    if field_name not in assertion or assertion[field_name] is None:
        return None
    return int(assertion[field_name])


def _optional_str_sequence_filter(
    assertion: dict[str, Any],
    field_name: str,
) -> list[str] | None:
    if field_name not in assertion or assertion[field_name] is None:
        return None
    value = assertion[field_name]
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _matches_message_filters(
    record: dict[str, object],
    assertion: dict[str, Any],
    filters: dict[str, object],
) -> bool:
    for field_name in (
        "message_id",
        "sender_id",
        "recipient_address",
        "lane_signature",
        "payload_kind",
    ):
        value = filters[field_name]
        if value is not None and record[field_name] != value:
            return False
    return "payload" not in assertion or record["payload"] == filters["payload"]


def _record_matches_expected(
    actual: dict[str, object],
    expected: dict[str, object],
    found_field: str,
) -> bool:
    if not actual.get(found_field):
        return False
    for field_name, expected_value in expected.items():
        if field_name == "lane_signature":
            continue
        if actual.get(field_name) != expected_value:
            return False
    return True


def _matches_encryption_policy_decision_filters(
    record: dict[str, object],
    filters: dict[str, object],
) -> bool:
    metadata = record.get("metadata")
    registry_hub = metadata.get("registry_hub") if isinstance(metadata, dict) else None
    if registry_hub != filters["registry_hub"]:
        return False
    for field_name in (
        "policy_id",
        "mailbox_id",
        "lane_signature",
        "message_id",
        "status",
        "reason",
        "encryption_required",
        "envelope_accepted",
        "profile",
        "encryption_identity_id",
        "key_bundle_id",
    ):
        value = filters[field_name]
        if value is not None and record.get(field_name) != value:
            return False
    return True


def _matches_encrypted_delivery_result_filters(
    record: dict[str, object],
    filters: dict[str, object],
) -> bool:
    metadata = record.get("metadata")
    registry_hub = metadata.get("registry_hub") if isinstance(metadata, dict) else None
    if registry_hub != filters["registry_hub"]:
        return False
    for field_name in (
        "request_id",
        "message_id",
        "mailbox_id",
        "lane_signature",
        "status",
        "reason",
        "delivery_attempted",
        "delivery_allowed",
        "policy_required",
    ):
        value = filters[field_name]
        if value is not None and record.get(field_name) != value:
            return False

    gate_decision = record.get("gate_decision")
    if not isinstance(gate_decision, dict):
        return False
    if (
        filters["gate_status"] is not None
        and gate_decision.get("status") != filters["gate_status"]
    ):
        return False
    if (
        filters["gate_reason"] is not None
        and gate_decision.get("reason") != filters["gate_reason"]
    ):
        return False

    delivery_result = record.get("delivery_result")
    if delivery_result is not None and not isinstance(delivery_result, dict):
        return False
    if (
        filters["delivery_status"] is not None
        and _nested_delivery_value(delivery_result, "status") != filters["delivery_status"]
    ):
        return False
    if (
        filters["delivery_reason"] is not None
        and _nested_delivery_value(delivery_result, "reason") != filters["delivery_reason"]
    ):
        return False
    return not (
        filters["endpoint_id"] is not None
        and _nested_delivery_value(delivery_result, "endpoint_id")
        != filters["endpoint_id"]
    )


def _encrypted_delivery_result_query_filters(
    filters: dict[str, object],
) -> dict[str, object]:
    return {
        key: value
        for key, value in filters.items()
        if key != "registry_hub"
    }


def _encrypted_delivery_audit_summary(
    result: EncryptedDeliveryResult,
) -> dict[str, object]:
    summary = build_encrypted_delivery_audit_entry(result).to_summary()
    result_metadata = result.metadata if isinstance(result.metadata, dict) else {}
    audit_metadata = dict(summary.get("metadata", {}))
    if "registry_hub" in result_metadata:
        audit_metadata["registry_hub"] = result_metadata["registry_hub"]
    summary["metadata"] = audit_metadata
    return summary


def _matches_encrypted_delivery_audit_filters(
    record: dict[str, object],
    filters: dict[str, object],
) -> bool:
    metadata = record.get("metadata")
    registry_hub = metadata.get("registry_hub") if isinstance(metadata, dict) else None
    if registry_hub != filters["registry_hub"]:
        return False
    for field_name in (
        "request_id",
        "message_id",
        "mailbox_id",
        "lane_signature",
        "gate_status",
        "gate_reason",
        "delivery_status",
        "delivery_reason",
        "policy_id",
        "encryption_required",
        "envelope_accepted",
    ):
        value = filters[field_name]
        if value is not None and record.get(field_name) != value:
            return False
    return True


def _matches_rendezvous_poll_result_filters(
    record: dict[str, object],
    filters: dict[str, object],
) -> bool:
    parent_hub_id = filters["parent_hub_id"] or filters["registry_hub"]
    if parent_hub_id is not None and record.get("parent_hub_id") != parent_hub_id:
        return False
    for field_name in (
        "request_id",
        "polling_hub_id",
        "target_scope",
        "visibility_tier",
        "status",
        "reason",
    ):
        value = filters[field_name]
        if value is not None and record.get(field_name) != value:
            return False

    matched_offer_ids = record.get("matched_offer_ids")
    if not isinstance(matched_offer_ids, list):
        return False
    if (
        filters["matched_offer_id"] is not None
        and filters["matched_offer_id"] not in matched_offer_ids
    ):
        return False
    expected_ids = filters["matched_offer_ids"]
    return not (
        expected_ids is not None
        and not set(expected_ids).issubset(set(matched_offer_ids))
    )


def _matches_lane_admission_decision_filters(
    record: dict[str, object],
    filters: dict[str, object],
) -> bool:
    if record.get("hub_id") != filters["registry_hub"]:
        return False
    for field_name in (
        "decision_id",
        "policy_id",
        "offer_id",
        "request_id",
        "hub_id",
        "requester_id",
        "target_handle",
        "target_scope",
        "lane_signature",
        "status",
        "reason",
        "allowed",
    ):
        value = filters[field_name]
        if value is not None and record.get(field_name) != value:
            return False
    return True


def _matches_stream_offer_lifecycle_plan_filters(
    record: dict[str, object],
    filters: dict[str, object],
) -> bool:
    if record.get("hub_id") != filters["hub_id"]:
        return False
    if filters["checked_at"] is not None and record.get("checked_at") != filters["checked_at"]:
        return False
    return (
        _list_field_matches(record, filters, "expired_offer_ids", "expired_offer_id")
        and _list_field_matches(
            record,
            filters,
            "cleanup_candidate_offer_ids",
            "cleanup_candidate_offer_id",
        )
        and _list_field_matches(record, filters, "active_offer_ids", "active_offer_id")
        and _list_field_matches(record, filters, "ignored_offer_ids", "ignored_offer_id")
    )


def _matches_stream_offer_lifecycle_apply_result_filters(
    record: dict[str, object],
    filters: dict[str, object],
) -> bool:
    if record.get("hub_id") != filters["hub_id"]:
        return False
    for field_name in ("plan_checked_at", "recorded_transition_count"):
        value = filters[field_name]
        if value is not None and record.get(field_name) != value:
            return False
    return (
        _list_field_matches(record, filters, "applied_offer_ids", "applied_offer_id")
        and _list_field_matches(record, filters, "skipped_offer_ids", "skipped_offer_id")
        and _list_field_matches(record, filters, "missing_offer_ids", "missing_offer_id")
    )


def _stream_offer_lifecycle_explanation_filters(
    assertion: dict[str, Any],
    hub_id: str,
) -> dict[str, object]:
    return {
        "hub_id": hub_id,
        "offer_id": _optional_filter_str(assertion, "offer_id"),
        "category": _optional_filter_str(assertion, "category"),
        "reason": _optional_filter_str(assertion, "reason"),
        "status": _optional_filter_str(assertion, "status"),
        "source": _optional_filter_str(assertion, "source"),
        "checked_at": _optional_int_field(assertion, "checked_at"),
    }


def _matches_stream_offer_lifecycle_explanation_filters(
    record: dict[str, object],
    filters: dict[str, object],
) -> bool:
    for field_name in (
        "hub_id",
        "offer_id",
        "category",
        "reason",
        "status",
        "source",
        "checked_at",
    ):
        value = filters[field_name]
        if value is not None and record.get(field_name) != value:
            return False
    return True


def _matches_stream_offer_lifecycle_audit_summary_filters(
    record: dict[str, object],
    filters: dict[str, object],
) -> bool:
    for field_name in ("hub_id", "total_transitions", "explanation_count"):
        value = filters[field_name]
        if value is not None and record.get(field_name) != value:
            return False
    return (
        _count_field_matches(record, filters, "by_offer_id", "offer_id", "offer_count")
        and _count_field_matches(record, filters, "by_status", "status", "status_count")
        and _count_field_matches(record, filters, "by_reason", "reason", "reason_count")
        and _count_field_matches(
            record,
            filters,
            "by_category",
            "category",
            "category_count",
        )
    )


def _stream_offer_lifecycle_retention_filters(
    assertion: dict[str, Any],
    hub_id: str,
) -> dict[str, object]:
    return {
        "hub_id": hub_id,
        "policy_id": _optional_filter_str(assertion, "policy_id"),
        "kept_explanation_key": _optional_filter_str(
            assertion,
            "kept_explanation_key",
        ),
        "kept_explanation_keys": _optional_str_sequence_filter(
            assertion,
            "kept_explanation_keys",
        ),
        "prune_candidate_explanation_key": _optional_filter_str(
            assertion,
            "prune_candidate_explanation_key",
        ),
        "prune_candidate_explanation_keys": _optional_str_sequence_filter(
            assertion,
            "prune_candidate_explanation_keys",
        ),
        "ignored_explanation_key": _optional_filter_str(
            assertion,
            "ignored_explanation_key",
        ),
        "ignored_explanation_keys": _optional_str_sequence_filter(
            assertion,
            "ignored_explanation_keys",
        ),
        "kept_count": _optional_int_field(assertion, "kept_count"),
        "prune_candidate_count": _optional_int_field(
            assertion,
            "prune_candidate_count",
        ),
        "ignored_count": _optional_int_field(assertion, "ignored_count"),
    }


def _matches_stream_offer_lifecycle_retention_decision_filters(
    record: dict[str, object],
    filters: dict[str, object],
) -> bool:
    if record.get("hub_id") != filters["hub_id"]:
        return False
    if filters["policy_id"] is not None and record.get("policy_id") != filters["policy_id"]:
        return False
    return (
        _list_field_matches(
            record,
            filters,
            "kept_explanation_keys",
            "kept_explanation_key",
        )
        and _list_field_matches(
            record,
            filters,
            "prune_candidate_explanation_keys",
            "prune_candidate_explanation_key",
        )
        and _list_field_matches(
            record,
            filters,
            "ignored_explanation_keys",
            "ignored_explanation_key",
        )
        and _count_matches(record, filters, "kept_explanation_keys", "kept_count")
        and _count_matches(
            record,
            filters,
            "prune_candidate_explanation_keys",
            "prune_candidate_count",
        )
        and _count_matches(record, filters, "ignored_explanation_keys", "ignored_count")
    )


def _matches_stream_offer_lifecycle_pruning_plan_filters(
    record: dict[str, object],
    filters: dict[str, object],
) -> bool:
    if record.get("hub_id") != filters["hub_id"]:
        return False
    if filters["policy_id"] is not None and record.get("policy_id") != filters["policy_id"]:
        return False
    for field_name in ("candidate_count", "retained_count", "ignored_count"):
        value = filters[field_name]
        if value is not None and record.get(field_name) != value:
            return False
    return (
        _list_field_matches(
            record,
            filters,
            "candidate_explanation_keys",
            "prune_candidate_explanation_key",
        )
        and _list_field_matches(
            record,
            filters,
            "retained_explanation_keys",
            "kept_explanation_key",
        )
        and _list_field_matches(
            record,
            filters,
            "ignored_explanation_keys",
            "ignored_explanation_key",
        )
        and _count_field_matches(
            record,
            filters,
            "candidate_by_category",
            "category",
            "category_count",
        )
        and _count_field_matches(
            record,
            filters,
            "candidate_by_reason",
            "reason",
            "reason_count",
        )
        and _count_field_matches(
            record,
            filters,
            "candidate_by_source",
            "source",
            "source_count",
        )
    )


def _matches_stream_offer_lifecycle_pruning_apply_result_filters(
    record: dict[str, object],
    filters: dict[str, object],
) -> bool:
    if record.get("hub_id") != filters["hub_id"]:
        return False
    if filters["policy_id"] is not None and record.get("policy_id") != filters["policy_id"]:
        return False
    for field_name in ("pruned_count", "retained_count", "ignored_count", "missing_count"):
        value = filters[field_name]
        if value is not None and record.get(field_name) != value:
            return False
    return (
        _list_field_matches(
            record,
            filters,
            "pruned_explanation_keys",
            "pruned_explanation_key",
        )
        and _list_field_matches(
            record,
            filters,
            "retained_explanation_keys",
            "retained_explanation_key",
        )
        and _list_field_matches(
            record,
            filters,
            "ignored_explanation_keys",
            "ignored_explanation_key",
        )
        and _list_field_matches(
            record,
            filters,
            "missing_explanation_keys",
            "missing_explanation_key",
        )
    )


def _count_matches(
    record: dict[str, object],
    filters: dict[str, object],
    list_field_name: str,
    count_filter_name: str,
) -> bool:
    expected_count = filters[count_filter_name]
    if expected_count is None:
        return True
    value = record.get(list_field_name)
    return isinstance(value, list) and len(value) == expected_count


def _matches_stream_offer_status_transition_filters(
    record: dict[str, object],
    filters: dict[str, object],
) -> bool:
    if record.get("hub_id") != (filters["hub_id"] or filters["registry_hub"]):
        return False
    for field_name in (
        "offer_id",
        "previous_status",
        "new_status",
        "reason",
        "actor_id",
        "request_id",
    ):
        value = filters[field_name]
        if value is not None and record.get(field_name) != value:
            return False
    return not (
        filters["status"] is not None
        and record.get("previous_status") != filters["status"]
        and record.get("new_status") != filters["status"]
    )


def _count_field_matches(
    record: dict[str, object],
    filters: dict[str, object],
    count_field_name: str,
    key_filter_name: str,
    count_filter_name: str,
) -> bool:
    key = filters[key_filter_name]
    count = filters[count_filter_name]
    if key is None and count is None:
        return True
    values = record.get(count_field_name)
    if not isinstance(values, dict):
        return False
    if key is None:
        return False
    actual_count = values.get(key)
    if count is not None:
        return actual_count == count
    return actual_count is not None


def _list_field_matches(
    record: dict[str, object],
    filters: dict[str, object],
    list_field_name: str,
    item_filter_name: str,
) -> bool:
    values = record.get(list_field_name)
    if not isinstance(values, list):
        return False
    item = filters[item_filter_name]
    if item is not None and item not in values:
        return False
    expected_items = filters[list_field_name]
    return not (
        expected_items is not None
        and not set(expected_items).issubset(set(values))
    )


def _encrypted_delivery_audit_query_filters(
    filters: dict[str, object],
) -> dict[str, object]:
    return {
        "request_id": filters["request_id"],
        "message_id": filters["message_id"],
        "mailbox_id": filters["mailbox_id"],
        "lane_signature": filters["lane_signature"],
        "gate_status": filters["gate_status"],
        "gate_reason": filters["gate_reason"],
    }


def _nested_delivery_value(
    delivery_result: object,
    field_name: str,
) -> object | None:
    if not isinstance(delivery_result, dict):
        return None
    return delivery_result.get(field_name)


_EVALUATORS = {
    "device_registered": _device_registered,
    "label_maps_to": _label_maps_to,
    "device_state": _device_state,
    "lane_state": _lane_state,
    "lane_not_active": _lane_not_active,
    "lane_sequence": _lane_sequence,
    "flow_control_exists": _flow_control_exists,
    "flow_control_absent": _flow_control_absent,
    "latest_step_status": _latest_step_status,
    "latest_step_reason": _latest_step_reason,
    "relocation_failed": _relocation_failed,
    "move_recorded": _move_recorded,
    "move_not_recorded": _move_not_recorded,
    "attachment_is": _attachment_is,
    "route_for_lane": _route_for_lane,
    "event_seen": _event_seen,
    "conflict_exists": _conflict_exists,
    "quarantine_exists": _quarantine_exists,
    "recommendation_exists": _recommendation_exists,
    "session_state": _session_state,
    "session_counter": _session_counter,
    "checkpoint_state": _checkpoint_state,
    "alias_resolves_to": _alias_resolves_to,
    "alias_status": _alias_status,
    "alias_bundle_status": _alias_bundle_status,
    "bundle_alias_resolves_to": _bundle_alias_resolves_to,
    "alias_granted_as": _alias_granted_as,
    "alias_authority_ceiling": _alias_authority_ceiling,
    "alias_authority_path_summary": _alias_authority_path_summary,
    "alias_history_contains": _alias_history_contains,
    "alias_conflict_history_contains": _alias_conflict_history_contains,
    "authority_audit_trace_contains": _authority_audit_trace_contains,
    "authority_outcome_history_contains": _authority_outcome_history_contains,
    "quarantine_history_contains": _quarantine_history_contains,
    "alias_not_resolved": _alias_not_resolved,
    "canonical_identity_unchanged": _canonical_identity_unchanged,
    "mailbox_registered": _mailbox_registered,
    "mailbox_supports_lane": _mailbox_supports_lane,
    "message_delivery_result_contains": _message_delivery_result_contains,
    "mailbox_inbox_contains": _mailbox_inbox_contains,
    "encryption_identity_registered": _encryption_identity_registered,
    "key_bundle_registered": _key_bundle_registered,
    "mailbox_encryption_binding_registered": (
        _mailbox_encryption_binding_registered
    ),
    "mailbox_encryption_policy_registered": _mailbox_encryption_policy_registered,
    "encryption_policy_decision_contains": _encryption_policy_decision_contains,
    "encrypted_delivery_result_contains": _encrypted_delivery_result_contains,
    "encrypted_delivery_audit_contains": _encrypted_delivery_audit_contains,
    "held_stream_offer_contains": _held_stream_offer_contains,
    "rendezvous_poll_result_contains": _rendezvous_poll_result_contains,
    "lane_admission_decision_contains": _lane_admission_decision_contains,
    "stream_offer_lifecycle_plan_contains": _stream_offer_lifecycle_plan_contains,
    "stream_offer_lifecycle_apply_result_contains": (
        _stream_offer_lifecycle_apply_result_contains
    ),
    "stream_offer_lifecycle_explanation_contains": (
        _stream_offer_lifecycle_explanation_contains
    ),
    "stream_offer_lifecycle_explanation_history_contains": (
        _stream_offer_lifecycle_explanation_history_contains
    ),
    "stream_offer_lifecycle_audit_summary_contains": (
        _stream_offer_lifecycle_audit_summary_contains
    ),
    "stream_offer_lifecycle_retention_decision_contains": (
        _stream_offer_lifecycle_retention_decision_contains
    ),
    "stream_offer_lifecycle_pruning_plan_contains": (
        _stream_offer_lifecycle_pruning_plan_contains
    ),
    "stream_offer_lifecycle_pruning_apply_result_contains": (
        _stream_offer_lifecycle_pruning_apply_result_contains
    ),
    "stream_offer_status_transition_contains": (
        _stream_offer_status_transition_contains
    ),
}
