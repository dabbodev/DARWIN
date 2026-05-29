"""Traffic metric counters and advisory growth recommendations."""

from __future__ import annotations

from darwin.models.hub import TrafficHub
from darwin.models.recommendation import GrowthPolicy, GrowthRecommendation


def record_packet_forwarded(hub: TrafficHub, delivered: bool = False) -> None:
    """Record a packet forwarding attempt and optional delivery."""
    hub.metrics.packets_forwarded += 1
    if delivered:
        hub.metrics.packets_delivered += 1


def record_packet_dropped(hub: TrafficHub) -> None:
    """Record a packet drop."""
    hub.metrics.packets_dropped += 1


def record_route_unavailable(hub: TrafficHub) -> None:
    """Record an unavailable route."""
    hub.metrics.route_unavailable_count += 1
    record_packet_dropped(hub)


def record_invalid_packet_auth(hub: TrafficHub) -> None:
    """Record symbolic packet authentication failure."""
    hub.metrics.invalid_packet_auth_count += 1
    record_packet_dropped(hub)


def record_lane_open(hub: TrafficHub) -> None:
    """Record a successfully opened logical lane."""
    hub.metrics.lane_open_count += 1


def record_lane_send(hub: TrafficHub) -> None:
    """Record a logical lane send attempt."""
    hub.metrics.lane_send_count += 1


def record_lane_pause(hub: TrafficHub, affected_count: int) -> None:
    """Record relocation lane pauses and flow holds."""
    hub.metrics.relocation_count += 1
    if affected_count > 0:
        hub.metrics.lane_pause_count += affected_count
        hub.metrics.flow_hold_count += affected_count


def record_lane_resume(hub: TrafficHub, resumed_count: int) -> None:
    """Record relocation lane resumes."""
    if resumed_count > 0:
        hub.metrics.lane_resume_count += resumed_count


def record_route_selection(hub: TrafficHub) -> None:
    """Record an explicit route selection attempt."""
    hub.metrics.route_selection_count += 1


def record_cross_tree_packet(
    traffic_hub: TrafficHub,
    from_branch: str,
    to_branch: str,
) -> None:
    """Record symbolic cross-branch packet pressure without routing side effects."""
    traffic_hub.metrics.cross_tree_packet_count += 1
    traffic_hub._cross_tree_branches.add(from_branch)
    traffic_hub._cross_tree_branches.add(to_branch)


def recommend_traffic_bridge(
    traffic_hub: TrafficHub,
    policy: GrowthPolicy | None = None,
) -> GrowthRecommendation | None:
    """Recommend a traffic bridge when cross-tree packet pressure is sustained."""
    active_policy = policy or GrowthPolicy()
    if (
        traffic_hub.metrics.cross_tree_packet_count
        <= active_policy.traffic_bridge_cross_tree_threshold
    ):
        return None

    recommendation = GrowthRecommendation(
        recommendation_id=_recommendation_id(
            traffic_hub.hub_id,
            "create_traffic_bridge",
            "sustained_cross_tree_traffic",
        ),
        recommendation_type="create_traffic_bridge",
        affected_hubs=[traffic_hub.hub_id],
        affected_branches=sorted(traffic_hub._cross_tree_branches),
        reason="sustained_cross_tree_traffic",
        confidence="high",
        expected_benefit="reduce_repeated_cross_tree_forwarding_pressure",
        requires_admin_approval=True,
    )
    _store_recommendation(traffic_hub, recommendation)
    return recommendation


def recommend_roaming_witness_hub(
    traffic_hub: TrafficHub,
    policy: GrowthPolicy | None = None,
) -> GrowthRecommendation | None:
    """Recommend a roaming witness hub when relocation churn is high."""
    active_policy = policy or GrowthPolicy()
    if traffic_hub.metrics.relocation_count <= active_policy.roaming_witness_relocation_threshold:
        return None

    recommendation = GrowthRecommendation(
        recommendation_id=_recommendation_id(
            traffic_hub.hub_id,
            "create_roaming_witness_hub",
            "high_relocation_churn",
        ),
        recommendation_type="create_roaming_witness_hub",
        affected_hubs=[traffic_hub.hub_id],
        reason="high_relocation_churn",
        confidence="high",
        expected_benefit="stabilize_symbolic_relocation_observation",
        requires_admin_approval=True,
    )
    _store_recommendation(traffic_hub, recommendation)
    return recommendation


def recommend_security_pressure(
    traffic_hub: TrafficHub,
    policy: GrowthPolicy | None = None,
) -> GrowthRecommendation | None:
    """Recommend investigation when traffic auth failures repeatedly occur."""
    active_policy = policy or GrowthPolicy()
    if (
        traffic_hub.metrics.invalid_packet_auth_count
        <= active_policy.security_pressure_invalid_auth_threshold
    ):
        return None

    recommendation = GrowthRecommendation(
        recommendation_id=_recommendation_id(
            traffic_hub.hub_id,
            "investigate_security_pressure",
            "repeated_symbolic_auth_failures",
        ),
        recommendation_type="investigate_security_pressure",
        affected_hubs=[traffic_hub.hub_id],
        reason="repeated_symbolic_auth_failures",
        confidence="high",
        expected_benefit="surface_repeated_invalid_symbolic_packet_auth",
        requires_admin_approval=True,
    )
    _store_recommendation(traffic_hub, recommendation)
    return recommendation


def _store_recommendation(
    traffic_hub: TrafficHub,
    recommendation: GrowthRecommendation,
) -> None:
    existing_ids = {
        existing.recommendation_id for existing in traffic_hub.growth_recommendations
    }
    if recommendation.recommendation_id not in existing_ids:
        traffic_hub.growth_recommendations.append(recommendation)


def _recommendation_id(hub_id: str, recommendation_type: str, reason: str) -> str:
    return f"{hub_id}:{recommendation_type}:{reason}"
