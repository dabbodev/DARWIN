"""Scenario assertion helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from darwin.registry.aliases import resolve_alias
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
    "alias_granted_as": _alias_granted_as,
    "alias_authority_ceiling": _alias_authority_ceiling,
    "alias_not_resolved": _alias_not_resolved,
    "canonical_identity_unchanged": _canonical_identity_unchanged,
}
