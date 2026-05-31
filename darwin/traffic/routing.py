"""Routing helpers for simulator experiments."""

from __future__ import annotations

from heapq import heappop, heappush
from typing import TYPE_CHECKING

from darwin.models.hub import DirectAttachmentRecord, TrafficHub
from darwin.models.route import (
    ForwardingResult,
    LinkMetrics,
    RouteCostBreakdown,
    RouteRecord,
    RoutingPolicy,
)
from darwin.traffic.metrics import (
    record_packet_dropped,
    record_packet_forwarded,
    record_route_selection,
    record_route_unavailable,
)
from darwin.traffic.security import (
    is_quarantined_for_normal_traffic,
    log_security_event,
    verify_packet_auth,
)

if TYPE_CHECKING:
    from darwin.models.device import Device
    from darwin.models.packet import DarwinPacket


def route_cost(
    latency_ms: float,
    congestion_penalty: float = 0.0,
    trust_penalty: float = 0.0,
) -> float:
    """Compute the intentionally simple v0.1 route cost."""
    return latency_ms + congestion_penalty + trust_penalty


def connect_neighbor(
    hub_a: TrafficHub,
    hub_b: TrafficHub,
    metrics: LinkMetrics | None = None,
    *,
    latency_ms: int | None = None,
    congestion: str | None = None,
    trust: str | None = None,
    stability: str | None = None,
) -> None:
    """Connect two traffic hubs bidirectionally."""
    hub_a.connect_neighbor(
        hub_b,
        metrics,
        latency_ms=latency_ms,
        congestion=congestion,
        trust=trust,
        stability=stability,
    )


def attach_device(hub: TrafficHub, device: Device | str) -> DirectAttachmentRecord:
    """Attach a simulated device or device ID to a traffic hub."""
    return hub.attach_device(device)


def detach_device(hub: TrafficHub, device_id: str) -> DirectAttachmentRecord | None:
    """Detach a simulated device from a traffic hub."""
    return hub.detach_device(device_id)


def select_route(
    start_hub: TrafficHub,
    target_device_id: str,
    all_hubs: dict[str, TrafficHub] | None = None,
    policy: RoutingPolicy | None = None,
) -> RouteRecord | None:
    """Select the lowest-cost symbolic hub path to a directly attached target device."""
    record_route_selection(start_hub)
    hub_map = dict(all_hubs or {})
    hub_map[start_hub.hub_id] = start_hub

    if target_device_id in start_hub.direct_attachments:
        record = RouteRecord(
            target_id=target_device_id,
            route=[start_hub.hub_id],
            route_status="available",
            cost=0.0,
            total_cost=0.0,
            cost_breakdown=RouteCostBreakdown(),
        )
        start_hub.routes[target_device_id] = record
        return record

    routing_policy = policy or RoutingPolicy()
    pending: list[tuple[float, tuple[str, ...], str, RouteCostBreakdown]] = []
    start_route = (start_hub.hub_id,)
    heappush(pending, (0.0, start_route, start_hub.hub_id, RouteCostBreakdown()))
    best_seen: dict[str, tuple[float, tuple[str, ...]]] = {
        start_hub.hub_id: (0.0, start_route)
    }
    finalized: set[str] = set()

    while pending:
        current_cost, route_tuple, hub_id, breakdown = heappop(pending)
        if hub_id in finalized:
            continue
        finalized.add(hub_id)
        hub = hub_map.get(hub_id)
        if hub is None:
            continue

        if target_device_id in hub.direct_attachments:
            record = RouteRecord(
                target_id=target_device_id,
                route=list(route_tuple),
                route_status="available",
                cost=float(len(route_tuple) - 1),
                total_cost=current_cost,
                cost_breakdown=breakdown,
            )
            start_hub.routes[target_device_id] = record
            return record

        for neighbor_id, neighbor in sorted(hub.neighbors.items()):
            if neighbor_id in finalized or neighbor_id not in hub_map:
                continue
            if neighbor.status != "connected":
                continue
            if not neighbor.metrics.is_usable(routing_policy):
                continue

            link_breakdown = neighbor.metrics.cost_breakdown(routing_policy)
            next_breakdown = breakdown.combine(link_breakdown)
            next_cost = next_breakdown.total
            next_route = (*route_tuple, neighbor_id)
            previous = best_seen.get(neighbor_id)
            if previous is not None and previous <= (next_cost, next_route):
                continue
            best_seen[neighbor_id] = (next_cost, next_route)
            heappush(pending, (next_cost, next_route, neighbor_id, next_breakdown))

    return None


def forward_packet(
    start_hub: TrafficHub,
    packet: DarwinPacket,
    all_hubs: dict[str, TrafficHub] | None = None,
    policy: RoutingPolicy | None = None,
) -> ForwardingResult:
    """Forward a simulated DARWIN packet through traffic hubs, if a route exists."""
    auth_result = verify_packet_auth(start_hub, packet)
    if not auth_result.success:
        result = ForwardingResult(
            packet_id=packet.packet_id,
            action=auth_result.action,
            target_device_id=packet.target_device_id,
        )
        start_hub.forwarding_log.append(result)
        return result

    if is_quarantined_for_normal_traffic(start_hub, packet.source_device_id):
        log_security_event(
            traffic_hub=start_hub,
            event_type="quarantined_device_blocked",
            claimed_device_id=packet.source_device_id,
            severity="medium",
            action_taken="packet_rejected",
            reason="source_quarantined",
        )
        result = ForwardingResult(
            packet_id=packet.packet_id,
            action="source_quarantined",
            target_device_id=packet.target_device_id,
        )
        record_packet_dropped(start_hub)
        start_hub.forwarding_log.append(result)
        return result

    if packet.target_device_id is None:
        result = ForwardingResult(
            packet_id=packet.packet_id,
            action="route_unavailable",
            target_device_id=None,
        )
        record_route_unavailable(start_hub)
        start_hub.forwarding_log.append(result)
        return result

    route_record = select_route(start_hub, packet.target_device_id, all_hubs, policy)
    if route_record is None:
        result = ForwardingResult(
            packet_id=packet.packet_id,
            action="route_unavailable",
            target_device_id=packet.target_device_id,
        )
        record_route_unavailable(start_hub)
        start_hub.forwarding_log.append(result)
        return result

    result = ForwardingResult(
        packet_id=packet.packet_id,
        action="delivered",
        target_device_id=packet.target_device_id,
        route=list(route_record.route),
        next_hop=route_record.next_hop,
        final_hub_id=route_record.final_hub_id,
        route_status=route_record.route_status,
        total_cost=route_record.total_cost,
        cost_breakdown=route_record.cost_breakdown,
    )

    hub_map = dict(all_hubs or {})
    hub_map[start_hub.hub_id] = start_hub
    logged_hubs: set[str] = set()
    for hub_id in route_record.route:
        hub = hub_map.get(hub_id)
        if hub is not None and hub_id not in logged_hubs:
            hub.forwarding_log.append(result)
            logged_hubs.add(hub_id)
    record_packet_forwarded(start_hub, delivered=True)

    return result
