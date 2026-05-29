"""Deterministic scenario runner for DARWIN v0.1."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from darwin.models.checkpoint import make_checkpoint_packet
from darwin.models.device import Device
from darwin.models.hub import LocalDeviceRecord
from darwin.registry.checkpoints import record_checkpoint as record_checkpoint_op
from darwin.registry.operations import (
    register_device as register_device_op,
)
from darwin.registry.operations import (
    resolve_label as resolve_label_op,
)
from darwin.registry.relocation import (
    create_move_contract,
    update_attachment_after_move,
)
from darwin.registry.relocation import (
    mark_in_transit as mark_in_transit_op,
)
from darwin.registry.security import verify_rolling_proof as verify_rolling_proof_op
from darwin.sim.assertions import AssertionResult, evaluate_assertions
from darwin.sim.scenarios import Scenario, load_scenario
from darwin.sim.world import World
from darwin.traffic.lanes import open_lane as open_lane_op
from darwin.traffic.lanes import send_lane_data as send_lane_data_op
from darwin.traffic.metrics import (
    recommend_traffic_bridge as recommend_traffic_bridge_op,
)
from darwin.traffic.metrics import (
    record_cross_tree_packet as record_cross_tree_packet_op,
)
from darwin.traffic.relocation import (
    pause_lanes_for_relocation as pause_lanes_for_relocation_op,
)
from darwin.traffic.relocation import (
    resume_lanes_after_relocation as resume_lanes_after_relocation_op,
)


@dataclass(slots=True)
class ScenarioRunResult:
    scenario_id: str
    passed: bool
    assertion_results: list[AssertionResult]
    event_log: list[str]
    final_snapshot: dict[str, object]
    world: World

    def to_dict(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "passed": self.passed,
            "assertion_results": [
                asdict(assertion_result)
                for assertion_result in self.assertion_results
            ],
            "event_log": list(self.event_log),
            "final_snapshot": self.final_snapshot,
        }

    def render(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        lines = [f"{self.scenario_id}: {status}", "", "Event log:"]
        lines.extend(self.event_log or ["(no events)"])
        lines.extend(["", "Final snapshot:", json.dumps(self.final_snapshot, indent=2)])
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.render()


def run_scenario(source: Scenario | dict[str, Any] | str | Path) -> ScenarioRunResult:
    """Run a scenario from a dict or file path and return deterministic results."""
    scenario = load_scenario(source)
    world = World()
    _apply_setup(world, scenario.setup)

    for step in scenario.steps:
        _run_step(world, step.action, step.fields)
        world.advance_time()

    assertion_results = evaluate_assertions(world, scenario.assertions)
    passed = all(result.passed for result in assertion_results)
    return ScenarioRunResult(
        scenario_id=scenario.scenario_id,
        passed=passed,
        assertion_results=assertion_results,
        event_log=world.event_log.lines,
        final_snapshot=world.snapshot(detailed=True),
        world=world,
    )


def run_scenario_dict(data: dict[str, Any]) -> ScenarioRunResult:
    return run_scenario(data)


def _apply_setup(world: World, setup: dict[str, Any]) -> None:
    for hub_config in _configs(setup.get("registry_hubs", []), "hub_id"):
        world.create_registry_hub(
            hub_id=str(hub_config["hub_id"]),
            scope_path=str(hub_config["scope_path"]),
            parent_hub_id=_optional_str(hub_config.get("parent_hub_id")),
        )

    for hub_config in _configs(setup.get("traffic_hubs", []), "hub_id"):
        world.create_traffic_hub(hub_id=str(hub_config["hub_id"]))

    for hub_config in _configs(setup.get("hybrid_hubs", []), "hub_id"):
        world.create_hybrid_hub(
            hub_id=str(hub_config["hub_id"]),
            scope_path=str(hub_config["scope_path"]),
            parent_hub_id=_optional_str(hub_config.get("parent_hub_id")),
        )

    for link_config in _configs(setup.get("links", []), "from"):
        world.connect_traffic_hubs(str(link_config["from"]), str(link_config["to"]))

    for device_config in _configs(setup.get("devices", []), "device_id"):
        device = Device(
            device_id=str(device_config["device_id"]),
            label=str(device_config.get("label", device_config["device_id"])),
            checkpoint_tier=int(device_config.get("checkpoint_tier", 1)),
        )
        world.add_device(device)

        registry_hub_id = device_config.get("registry_hub")
        if registry_hub_id is not None:
            register_device_op(
                world.registry_hubs[str(registry_hub_id)],
                device,
                requested_label=device.label,
                checkpoint_tier=device.checkpoint_tier,
                current_time=world.current_time,
            )

        traffic_hub_id = device_config.get("traffic_hub")
        if traffic_hub_id is not None:
            world.attach_device_to_traffic(device.device_id, str(traffic_hub_id))


def _run_step(world: World, action: str, fields: dict[str, Any]) -> None:
    handlers = {
        "register_device": _step_register_device,
        "resolve_label": _step_resolve_label,
        "open_lane": _step_open_lane,
        "send_lane_data": _step_send_lane_data,
        "record_checkpoint": _step_record_checkpoint,
        "mark_in_transit": _step_mark_in_transit,
        "pause_lanes_for_relocation": _step_pause_lanes_for_relocation,
        "move_device": _step_move_device,
        "resume_lanes_after_relocation": _step_resume_lanes_after_relocation,
        "verify_rolling_proof": _step_verify_rolling_proof,
        "record_cross_tree_packet": _step_record_cross_tree_packet,
        "recommend_traffic_bridge": _step_recommend_traffic_bridge,
        "advance_time": _step_advance_time,
    }
    try:
        handler = handlers[action]
    except KeyError as exc:
        raise ValueError(f"Unsupported scenario step action: {action}") from exc
    handler(world, fields)


def _step_register_device(world: World, fields: dict[str, Any]) -> None:
    device_id = str(fields["device"])
    label = str(fields.get("label", device_id))
    device = world.devices.get(device_id)
    if device is None:
        device = Device(device_id=device_id, label=label)
        world.add_device(device)

    hub = world.registry_hubs[str(fields["registry_hub"])]
    result = register_device_op(
        hub,
        device,
        requested_label=label,
        checkpoint_tier=device.checkpoint_tier,
        current_time=world.current_time,
    )
    world.action_results.append(result)

    if isinstance(result, LocalDeviceRecord):
        event_type = "label_conflict" if result.current_label != label else "registered_device"
        suffix = "" if result.current_label == label else f" (requested {label}; label_conflict)"
        world.log(
            f"registered {device_id} at {hub.hub_id} as {result.current_label}{suffix}",
            event_type=event_type,
        )
        return

    world.log(
        f"registration failed for {device_id} at {hub.hub_id}: {result.reason}",
        event_type=result.action,
    )


def _step_resolve_label(world: World, fields: dict[str, Any]) -> None:
    hub = world.registry_hubs[str(fields["registry_hub"])]
    label = str(fields["label"])
    result = resolve_label_op(hub, label)
    world.action_results.append(result)
    if result is None:
        world.log(f"resolved {label} at {hub.hub_id}: not found", event_type="label_not_found")
    else:
        world.log(
            f"resolved {label} at {hub.hub_id} to {result.device_id}",
            event_type="label_resolved",
        )


def _step_open_lane(world: World, fields: dict[str, Any]) -> None:
    hub = world.traffic_hubs[str(fields["traffic_hub"])]
    result = open_lane_op(
        hub,
        source_device_id=str(fields["source"]),
        target_device_id=str(fields["target"]),
        all_hubs=world.traffic_hubs,
        lane_id=_optional_str(fields.get("lane_id")),
    )
    world.action_results.append(result)
    if result.lane is not None:
        world.lanes[result.lane_id or result.lane.lane_id] = result.lane
    world.log(
        f"{result.action} {result.lane_id} from {result.source_device_id} "
        f"to {result.target_device_id} via {result.route}",
        event_type=result.action,
    )


def _step_send_lane_data(world: World, fields: dict[str, Any]) -> None:
    hub = world.traffic_hubs[str(fields["traffic_hub"])]
    result = send_lane_data_op(
        hub,
        lane_id=str(fields["lane"]),
        payload=fields.get("payload"),
        all_hubs=world.traffic_hubs,
        auth_tag_valid=bool(fields.get("auth_tag_valid", True)),
    )
    world.action_results.append(result)
    world.log(
        f"{result.action} on {result.lane_id} seq={result.sequence_number} "
        f"sent={result.last_sent_sequence} ack={result.last_acknowledged_sequence}",
        event_type=result.action,
    )


def _step_record_checkpoint(world: World, fields: dict[str, Any]) -> None:
    device = world.devices[str(fields["device"])]
    hub = world.registry_hubs[str(fields["registry_hub"])]
    packet = make_checkpoint_packet(
        device,
        hub.hub_id,
        state=str(fields["state"]),
        current_time=world.current_time,
        auth_tag_valid=bool(fields.get("auth_tag_valid", True)),
        battery_level=_optional_int(fields.get("battery_level")),
        active_lane_count=_optional_int(fields.get("active_lane_count")),
    )
    result = record_checkpoint_op(hub, packet)
    world.action_results.append(result)
    world.log(
        f"{result.action} for {result.device_id} at {hub.hub_id} state={fields['state']}",
        event_type=result.action,
    )


def _step_mark_in_transit(world: World, fields: dict[str, Any]) -> None:
    device_id = str(fields["device"])
    hub = world.registry_hubs[str(fields["registry_hub"])]
    result = mark_in_transit_op(hub, device_id, current_time=world.current_time)
    if device_id in world.devices and result.success:
        world.devices[device_id].mark_in_transit()
    world.action_results.append(result)
    world.log(f"{result.action} {device_id} at {hub.hub_id}", event_type=result.action)


def _step_pause_lanes_for_relocation(world: World, fields: dict[str, Any]) -> None:
    hub = world.traffic_hubs[str(fields["traffic_hub"])]
    result = pause_lanes_for_relocation_op(hub, str(fields["device"]))
    world.action_results.append(result)
    world.log(
        f"{result.action} for {result.device_id}: {result.affected_lanes}",
        event_type=result.action,
    )


def _step_move_device(world: World, fields: dict[str, Any]) -> None:
    device_id = str(fields["device"])
    device = world.devices[device_id]
    old_registry_hub = world.registry_hubs[str(fields["old_registry_hub"])]
    new_registry_hub = world.registry_hubs[str(fields["new_registry_hub"])]
    old_traffic_hub = world.traffic_hubs[str(fields["old_traffic_hub"])]
    new_traffic_hub = world.traffic_hubs[str(fields["new_traffic_hub"])]
    new_scope = str(fields.get("new_scope", new_registry_hub.scope_path))

    old_record = old_registry_hub.devices.get(device_id)
    passport_id = (
        old_record.passport_id
        if old_record is not None
        else device.passport_id or f"passport_{device_id}"
    )
    contract = create_move_contract(
        device_id=device_id,
        passport_id=passport_id,
        from_scope=old_registry_hub.scope_path,
        to_scope=new_scope,
        old_attachment=old_registry_hub.hub_id,
        new_attachment=new_registry_hub.hub_id,
        timestamp=world.current_time,
    )
    result = update_attachment_after_move(
        old_registry_hub,
        device_id,
        new_attachment=new_registry_hub.hub_id,
        new_scope=new_scope,
        move_contract=contract,
    )

    old_traffic_hub.detach_device(device_id)
    new_traffic_hub.attach_device(device)
    device.current_registry_hub = new_registry_hub.hub_id
    device.current_traffic_hub = new_traffic_hub.hub_id
    device.state = "online"

    if new_registry_hub.hub_id != old_registry_hub.hub_id:
        register_device_op(
            new_registry_hub,
            device,
            requested_label=device.label,
            checkpoint_tier=device.checkpoint_tier,
            current_time=world.current_time,
        )

    world.action_results.append(result)
    world.log(
        f"moved {device_id} from {old_traffic_hub.hub_id} to {new_traffic_hub.hub_id}",
        event_type="device_moved",
    )


def _step_resume_lanes_after_relocation(world: World, fields: dict[str, Any]) -> None:
    hub = world.traffic_hubs[str(fields["traffic_hub"])]
    result = resume_lanes_after_relocation_op(
        hub,
        str(fields["device"]),
        all_hubs=world.traffic_hubs,
    )
    world.action_results.append(result)
    world.log(
        f"{result.action} for {result.device_id}: {result.routes}",
        event_type=result.action,
    )


def _step_verify_rolling_proof(world: World, fields: dict[str, Any]) -> None:
    hub = world.registry_hubs[str(fields["registry_hub"])]
    result = verify_rolling_proof_op(
        hub,
        str(fields["device"]),
        proof_valid=bool(fields["proof_valid"]),
        current_time=world.current_time,
    )
    world.action_results.append(result)
    world.log(
        f"{result.action} rolling proof for {result.device_id}",
        event_type=result.security_event.event_type if result.security_event else result.action,
    )


def _step_record_cross_tree_packet(world: World, fields: dict[str, Any]) -> None:
    hub = world.traffic_hubs[str(fields["traffic_hub"])]
    count = int(fields.get("count", 1))
    for _ in range(count):
        record_cross_tree_packet_op(
            hub,
            from_branch=str(fields["from_branch"]),
            to_branch=str(fields["to_branch"]),
        )
    world.log(
        f"recorded {count} cross-tree packet(s) at {hub.hub_id}",
        event_type="cross_tree_packet_recorded",
    )


def _step_recommend_traffic_bridge(world: World, fields: dict[str, Any]) -> None:
    hub = world.traffic_hubs[str(fields["traffic_hub"])]
    recommendation = recommend_traffic_bridge_op(hub)
    world.action_results.append(recommendation)
    if recommendation is None:
        world.log(
            f"no traffic bridge recommendation for {hub.hub_id}",
            event_type="no_recommendation",
        )
        return
    world.log(
        f"recommended {recommendation.recommendation_type} for {hub.hub_id}",
        event_type=recommendation.recommendation_type,
    )


def _step_advance_time(world: World, fields: dict[str, Any]) -> None:
    ticks = int(fields.get("ticks", 1))
    world.advance_time(ticks)
    world.log(f"advanced time by {ticks}", event_type="time_advanced")


def _configs(value: Any, key_name: str) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, list):
        return [dict(item) for item in value]
    if isinstance(value, dict):
        configs = []
        for key, item in value.items():
            config = dict(item) if isinstance(item, dict) else {}
            config.setdefault(key_name, key)
            configs.append(config)
        return configs
    raise TypeError("Scenario setup sections must be lists or mappings")


def _optional_str(value: Any) -> str | None:
    return None if value is None else str(value)


def _optional_int(value: Any) -> int | None:
    return None if value is None else int(value)
