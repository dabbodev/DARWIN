"""Traffic-owned symbolic relocation flow control."""

from __future__ import annotations

from darwin.models.device import Device
from darwin.models.hub import TrafficHub
from darwin.models.move import (
    FlowControlRecord,
    LanePauseResult,
    LaneResumeResult,
    RelocationRecord,
)
from darwin.traffic.metrics import record_lane_pause, record_lane_resume
from darwin.traffic.routing import select_route


def pause_lanes_for_relocation(
    traffic_hub: TrafficHub,
    device_id: str,
    hold_window: int = 3000,
) -> LanePauseResult:
    """Pause active lanes where a relocating device is source or target."""
    affected_lanes: list[str] = []
    flow_controls: list[FlowControlRecord] = []

    for lane_id, lane in sorted(traffic_hub.lanes.items()):
        if device_id not in {lane.source_device_id, lane.target_device_id}:
            continue
        if lane.state != "active":
            continue

        lane.state = "paused_relocation"
        affected_lanes.append(lane_id)
        reason = (
            "recipient_in_transit"
            if lane.target_device_id == device_id
            else "device_in_transit"
        )
        flow_control = FlowControlRecord(
            lane_id=lane_id,
            device_id=device_id,
            reason=reason,
            hold_new_packets=True,
            hold_window=hold_window,
        )
        traffic_hub.flow_controls[lane_id] = flow_control
        flow_controls.append(flow_control)

    relocation = RelocationRecord(
        device_id=device_id,
        state="in_transit" if affected_lanes else "awaiting_new_attachment",
        affected_lanes=list(affected_lanes),
    )
    traffic_hub.relocations[device_id] = relocation
    record_lane_pause(traffic_hub, affected_count=len(affected_lanes))

    action = "lanes_paused" if affected_lanes else "no_lanes_affected"
    return LanePauseResult(
        action=action,
        device_id=device_id,
        affected_lanes=affected_lanes,
        flow_controls=flow_controls,
        relocation=relocation,
    )


def resume_lanes_after_relocation(
    traffic_hub: TrafficHub,
    device_id: str,
    new_route_by_lane: dict[str, list[str]] | None = None,
    all_hubs: dict[str, TrafficHub] | None = None,
) -> LaneResumeResult:
    """Recalculate routes and resume relocation-paused lanes for a device."""
    lane_ids = _affected_lane_ids(traffic_hub, device_id)
    if not lane_ids:
        return LaneResumeResult(action="no_lanes_affected", device_id=device_id)

    resumed_lanes: list[str] = []
    failed_lanes: list[str] = []
    routes: dict[str, list[str]] = {}

    for lane_id in lane_ids:
        lane = traffic_hub.lanes[lane_id]
        if lane.state not in {"paused_relocation", "awaiting_verification", "rerouting"}:
            continue

        lane.state = "rerouting"
        new_route = _new_route_for_lane(
            traffic_hub=traffic_hub,
            target_device_id=lane.target_device_id,
            lane_id=lane_id,
            new_route_by_lane=new_route_by_lane,
            all_hubs=all_hubs,
        )
        if new_route is None:
            lane.state = "awaiting_verification"
            failed_lanes.append(lane_id)
            continue

        lane.current_route = new_route
        lane.state = "resumed"
        lane.activate()
        traffic_hub.flow_controls.pop(lane_id, None)
        resumed_lanes.append(lane_id)
        routes[lane_id] = new_route

    relocation = traffic_hub.relocations.get(device_id)
    if relocation is not None:
        relocation.affected_lanes = [
            lane_id for lane_id in lane_ids if lane_id not in resumed_lanes
        ]
        relocation.state = "resumed" if not failed_lanes else "route_update_pending"

    if failed_lanes and not resumed_lanes:
        return LaneResumeResult(
            action="route_unavailable",
            device_id=device_id,
            failed_lanes=failed_lanes,
            reason="route_unavailable",
        )
    if failed_lanes:
        record_lane_resume(traffic_hub, resumed_count=len(resumed_lanes))
        return LaneResumeResult(
            action="resume_incomplete",
            device_id=device_id,
            resumed_lanes=resumed_lanes,
            failed_lanes=failed_lanes,
            routes=routes,
            reason="route_unavailable",
        )

    record_lane_resume(traffic_hub, resumed_count=len(resumed_lanes))
    return LaneResumeResult(
        action="lanes_resumed",
        device_id=device_id,
        resumed_lanes=resumed_lanes,
        routes=routes,
    )


def update_lane_route_after_move(
    traffic_hub: TrafficHub,
    lane_id: str,
    new_route: list[str],
) -> LaneResumeResult:
    """Patch one lane route after symbolic relocation."""
    lane = traffic_hub.lanes.get(lane_id)
    if lane is None:
        return LaneResumeResult(
            action="lane_not_found",
            device_id="unknown",
            failed_lanes=[lane_id],
            reason="lane_not_found",
        )

    lane.current_route = list(new_route)
    record_lane_resume(traffic_hub, resumed_count=1)
    return LaneResumeResult(
        action="lane_route_updated",
        device_id=lane.target_device_id,
        resumed_lanes=[lane_id],
        routes={lane_id: list(new_route)},
    )


def reconnect_device_after_move(
    old_traffic_hub: TrafficHub,
    new_traffic_hub: TrafficHub,
    device: Device,
    all_hubs: dict[str, TrafficHub] | None = None,
) -> LaneResumeResult:
    """Move a traffic attachment and resume lanes stored on the old hub."""
    old_traffic_hub.detach_device(device.device_id)
    new_traffic_hub.attach_device(device)
    device.current_traffic_hub = new_traffic_hub.hub_id
    device.state = "online"
    return resume_lanes_after_relocation(
        old_traffic_hub,
        device.device_id,
        all_hubs=all_hubs,
    )


def _affected_lane_ids(traffic_hub: TrafficHub, device_id: str) -> list[str]:
    relocation = traffic_hub.relocations.get(device_id)
    if relocation is not None and relocation.affected_lanes:
        return list(relocation.affected_lanes)

    return [
        lane_id
        for lane_id, lane in sorted(traffic_hub.lanes.items())
        if device_id in {lane.source_device_id, lane.target_device_id}
        and lane.state in {"paused_relocation", "awaiting_verification", "rerouting"}
    ]


def _new_route_for_lane(
    traffic_hub: TrafficHub,
    target_device_id: str,
    lane_id: str,
    new_route_by_lane: dict[str, list[str]] | None,
    all_hubs: dict[str, TrafficHub] | None,
) -> list[str] | None:
    if new_route_by_lane is not None and lane_id in new_route_by_lane:
        return list(new_route_by_lane[lane_id])

    route_record = select_route(traffic_hub, target_device_id, all_hubs)
    if route_record is None:
        return None
    return list(route_record.route)
