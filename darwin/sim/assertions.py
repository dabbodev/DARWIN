"""Scenario assertion helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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
    "lane_sequence": _lane_sequence,
    "event_seen": _event_seen,
    "conflict_exists": _conflict_exists,
    "quarantine_exists": _quarantine_exists,
    "recommendation_exists": _recommendation_exists,
}
