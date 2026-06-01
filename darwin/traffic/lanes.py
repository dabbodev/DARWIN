"""Logical lane helpers for symbolic traffic delivery."""

from __future__ import annotations

from typing import Any

from darwin.auth.hmac_bridge import (
    compute_hmac_tag,
    packet_auth_material,
)
from darwin.auth.modes import AUTH_MODE_HMAC_SHA256_EXPERIMENTAL, AUTH_MODE_SYMBOLIC
from darwin.models.hub import TrafficHub
from darwin.models.lane import (
    LaneAckResult,
    LaneCloseResult,
    LaneOpenResult,
    LaneSendResult,
    LogicalLane,
)
from darwin.models.packet import DarwinPacket
from darwin.traffic.metrics import record_lane_open, record_lane_send, record_route_unavailable
from darwin.traffic.routing import forward_packet, select_route


def _next_lane_id(hub: TrafficHub) -> str:
    lane_number = 1
    while True:
        lane_id = f"lane_{lane_number:03d}"
        if lane_id not in hub.lanes:
            return lane_id
        lane_number += 1


def open_lane(
    start_hub: TrafficHub,
    source_device_id: str,
    target_device_id: str,
    all_hubs: dict[str, TrafficHub] | None = None,
    lane_id: str | None = None,
) -> LaneOpenResult:
    """Open a logical lane over the currently selected traffic route."""
    selected_lane_id = lane_id or _next_lane_id(start_hub)

    if selected_lane_id in start_hub.lanes:
        existing_lane = start_hub.lanes[selected_lane_id]
        return LaneOpenResult(
            lane_id=selected_lane_id,
            action="lane_already_exists",
            source_device_id=source_device_id,
            target_device_id=target_device_id,
            lane=existing_lane,
            route=list(existing_lane.current_route),
        )

    if source_device_id not in start_hub.direct_attachments:
        return LaneOpenResult(
            lane_id=selected_lane_id,
            action="source_not_attached",
            source_device_id=source_device_id,
            target_device_id=target_device_id,
        )

    if start_hub.direct_attachments[source_device_id].status == "quarantined":
        return LaneOpenResult(
            lane_id=selected_lane_id,
            action="source_quarantined",
            source_device_id=source_device_id,
            target_device_id=target_device_id,
        )

    route_record = select_route(start_hub, target_device_id, all_hubs)
    if route_record is None:
        record_route_unavailable(start_hub)
        return LaneOpenResult(
            lane_id=selected_lane_id,
            action="route_unavailable",
            source_device_id=source_device_id,
            target_device_id=target_device_id,
        )

    lane = LogicalLane(
        lane_id=selected_lane_id,
        source_device_id=source_device_id,
        target_device_id=target_device_id,
        current_route=list(route_record.route),
        route_total_cost=route_record.total_cost,
        route_cost_breakdown=route_record.cost_breakdown,
    )
    lane.activate()
    start_hub.lanes[selected_lane_id] = lane
    record_lane_open(start_hub)

    return LaneOpenResult(
        lane_id=selected_lane_id,
        action="lane_opened",
        source_device_id=source_device_id,
        target_device_id=target_device_id,
        lane=lane,
        route=list(route_record.route),
        next_hop=route_record.next_hop,
        final_hub_id=route_record.final_hub_id,
        route_status=route_record.route_status,
        total_cost=route_record.total_cost,
        cost_breakdown=route_record.cost_breakdown,
    )


def send_lane_data(
    start_hub: TrafficHub,
    lane_id: str,
    payload: Any,
    all_hubs: dict[str, TrafficHub] | None = None,
    auth_tag_valid: bool = True,
    auth_mode: str = AUTH_MODE_SYMBOLIC,
    auth_secret: str | bytes | None = None,
    auth_tag: str | None = None,
    tamper_auth_tag: bool = False,
) -> LaneSendResult:
    """Send symbolic data over an active lane and acknowledge delivery."""
    lane = start_hub.lanes.get(lane_id)
    if lane is None:
        return LaneSendResult(lane_id=lane_id, action="lane_not_found", payload=payload)

    if lane.state != "active":
        action = (
            "lane_paused_relocation" if lane.state == "paused_relocation" else "lane_not_active"
        )
        return LaneSendResult(
            lane_id=lane_id,
            action=action,
            source_device_id=lane.source_device_id,
            target_device_id=lane.target_device_id,
            last_sent_sequence=lane.last_sent_sequence,
            last_acknowledged_sequence=lane.last_acknowledged_sequence,
            payload=payload,
        )

    sequence_number = lane.last_sent_sequence + 1
    record_lane_send(start_hub)
    packet = DarwinPacket(
        packet_id=f"{lane_id}_seq_{sequence_number:06d}",
        packet_class="DATA",
        packet_type="data_payload",
        source_device_id=lane.source_device_id,
        target_device_id=lane.target_device_id,
        source_hub_id=start_hub.hub_id,
        lane_id=lane.lane_id,
        sequence_number=sequence_number,
        payload=payload,
        auth_tag_valid=auth_tag_valid,
        auth_mode=auth_mode,
        auth_tag=auth_tag,
    )
    if auth_mode == AUTH_MODE_HMAC_SHA256_EXPERIMENTAL and auth_secret is not None:
        packet.auth_tag = compute_hmac_tag(auth_secret, packet_auth_material(packet))
        if tamper_auth_tag or not auth_tag_valid:
            packet.auth_tag = _tampered_tag(packet.auth_tag)

    result = forward_packet(start_hub, packet, all_hubs, auth_secret=auth_secret)

    if result.action != "delivered":
        return LaneSendResult(
            lane_id=lane_id,
            action=result.action,
            source_device_id=lane.source_device_id,
            target_device_id=lane.target_device_id,
            packet_id=packet.packet_id,
            sequence_number=sequence_number,
            route=list(result.route),
            next_hop=result.next_hop,
            final_hub_id=result.final_hub_id,
            route_status=result.route_status,
            total_cost=result.total_cost,
            cost_breakdown=result.cost_breakdown,
            last_sent_sequence=lane.last_sent_sequence,
            last_acknowledged_sequence=lane.last_acknowledged_sequence,
            payload=payload,
        )

    lane.last_sent_sequence = sequence_number
    ack_result = acknowledge_lane_packet(start_hub, lane_id, sequence_number)

    return LaneSendResult(
        lane_id=lane_id,
        action=result.action,
        source_device_id=lane.source_device_id,
        target_device_id=lane.target_device_id,
        packet_id=packet.packet_id,
        sequence_number=sequence_number,
        route=list(result.route),
        next_hop=result.next_hop,
        final_hub_id=result.final_hub_id,
        route_status=result.route_status,
        total_cost=result.total_cost,
        cost_breakdown=result.cost_breakdown,
        last_sent_sequence=lane.last_sent_sequence,
        last_acknowledged_sequence=ack_result.last_acknowledged_sequence,
        payload=payload,
    )


def _tampered_tag(tag: str) -> str:
    return ("0" if tag[:1] != "0" else "1") + tag[1:]


def acknowledge_lane_packet(
    hub: TrafficHub,
    lane_id: str,
    sequence_number: int,
) -> LaneAckResult:
    """Acknowledge a delivered lane packet without moving the ack counter backward."""
    lane = hub.lanes.get(lane_id)
    if lane is None:
        return LaneAckResult(
            lane_id=lane_id,
            action="lane_not_found",
            sequence_number=sequence_number,
            last_acknowledged_sequence=0,
        )

    if sequence_number > lane.last_acknowledged_sequence:
        lane.last_acknowledged_sequence = sequence_number
        action = "acknowledged"
    else:
        action = "ack_ignored"

    return LaneAckResult(
        lane_id=lane_id,
        action=action,
        sequence_number=sequence_number,
        last_acknowledged_sequence=lane.last_acknowledged_sequence,
    )


def close_lane(hub: TrafficHub, lane_id: str) -> LaneCloseResult:
    """Close a lane and leave its final state available for inspection."""
    lane = hub.lanes.get(lane_id)
    if lane is None:
        return LaneCloseResult(lane_id=lane_id, action="lane_not_found")

    if lane.state == "terminated":
        return LaneCloseResult(lane_id=lane_id, action="lane_already_terminated", state=lane.state)

    lane.close()
    lane.terminate()
    return LaneCloseResult(lane_id=lane_id, action="lane_terminated", state=lane.state)
