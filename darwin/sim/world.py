"""World container for DARWIN simulator state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from darwin.models.device import Device
from darwin.models.hub import RegistryHub, TrafficHub
from darwin.models.lane import LogicalLane
from darwin.models.route import LinkMetrics
from darwin.sim.event_log import EventLog
from darwin.traffic.routing import attach_device, connect_neighbor


@dataclass(slots=True)
class World:
    current_time: int = 0
    devices: dict[str, Device] = field(default_factory=dict)
    registry_hubs: dict[str, RegistryHub] = field(default_factory=dict)
    traffic_hubs: dict[str, TrafficHub] = field(default_factory=dict)
    lanes: dict[str, LogicalLane] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)
    event_log: EventLog = field(default_factory=EventLog)
    action_results: list[object] = field(default_factory=list)

    def add_device(self, device: Device) -> None:
        self.devices[device.device_id] = device

    def add_registry_hub(self, hub: RegistryHub) -> None:
        self.registry_hubs[hub.hub_id] = hub

    def add_traffic_hub(self, hub: TrafficHub) -> None:
        self.traffic_hubs[hub.hub_id] = hub

    def create_registry_hub(
        self,
        hub_id: str,
        scope_path: str,
        parent_hub_id: str | None = None,
        alias_authority_policy: dict[str, object] | None = None,
    ) -> RegistryHub:
        hub = RegistryHub(
            hub_id=hub_id,
            scope_path=scope_path,
            parent_hub_id=parent_hub_id,
            alias_authority_policy=(
                {} if alias_authority_policy is None else dict(alias_authority_policy)
            ),
        )
        self.add_registry_hub(hub)
        return hub

    def create_traffic_hub(self, hub_id: str) -> TrafficHub:
        hub = TrafficHub(hub_id=hub_id)
        self.add_traffic_hub(hub)
        return hub

    def create_hybrid_hub(
        self,
        hub_id: str,
        scope_path: str,
        parent_hub_id: str | None = None,
        alias_authority_policy: dict[str, object] | None = None,
    ) -> tuple[RegistryHub, TrafficHub]:
        registry_hub = self.create_registry_hub(
            hub_id=hub_id,
            scope_path=scope_path,
            parent_hub_id=parent_hub_id,
            alias_authority_policy=alias_authority_policy,
        )
        traffic_hub = self.create_traffic_hub(hub_id)
        return registry_hub, traffic_hub

    def connect_traffic_hubs(
        self,
        from_hub_id: str,
        to_hub_id: str,
        metrics: LinkMetrics | None = None,
    ) -> None:
        connect_neighbor(
            self.traffic_hubs[from_hub_id],
            self.traffic_hubs[to_hub_id],
            metrics,
        )

    def attach_device_to_traffic(self, device_id: str, traffic_hub_id: str) -> None:
        attach_device(self.traffic_hubs[traffic_hub_id], self.devices[device_id])

    def advance_time(self, ticks: int = 1) -> None:
        if ticks < 0:
            raise ValueError("ticks must be non-negative")
        self.current_time += ticks

    def log(
        self,
        message: str,
        event_type: str | None = None,
        *,
        actor: str | None = None,
        target: str | None = None,
        device_id: str | None = None,
        hub_id: str | None = None,
        lane_id: str | None = None,
        status: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        self.event_log.write(
            self.current_time,
            message,
            event_type=event_type,
            actor=actor,
            target=target,
            device_id=device_id,
            hub_id=hub_id,
            lane_id=lane_id,
            status=status,
            data=data,
        )
        self.events.append(self.event_log.lines[-1])

    def snapshot(self, detailed: bool = False) -> dict[str, object]:
        if detailed:
            return self.detailed_snapshot()

        return {
            "time": self.current_time,
            "devices": sorted(self.devices),
            "registry_hubs": sorted(self.registry_hubs),
            "traffic_hubs": sorted(self.traffic_hubs),
            "lanes": sorted(self.lanes),
        }

    def detailed_snapshot(self) -> dict[str, object]:
        return {
            "current_time": self.current_time,
            "devices": {
                device_id: {
                    "label": device.label,
                    "passport_id": device.passport_id,
                    "current_registry_hub": device.current_registry_hub,
                    "current_traffic_hub": device.current_traffic_hub,
                    "state": device.state,
                    "checkpoint_tier": device.checkpoint_tier,
                }
                for device_id, device in sorted(self.devices.items())
            },
            "registry_hubs": {
                hub_id: {
                    "scope_path": hub.scope_path,
                    "parent_hub_id": hub.parent_hub_id,
                    "alias_authority_policy": dict(
                        sorted(hub.alias_authority_policy.items())
                    ),
                    "labels": dict(sorted(hub.labels.items())),
                    "aliases": {
                        alias: {
                            "alias_type": record.alias_type,
                            "target_device_id": record.target_device_id,
                            "target_service_id": record.target_service_id,
                            "target_identity_chain": record.target_identity_chain,
                            "requested_by_device_id": record.requested_by_device_id,
                            "requested_through_hub": record.requested_through_hub,
                            "approved_by_registry_hub": record.approved_by_registry_hub,
                            "authority_scope": record.authority_scope,
                            "status": record.status,
                            "visibility": record.visibility,
                            "ttl": record.ttl,
                            "conflict_id": record.conflict_id,
                            "requested_alias": record.requested_alias,
                            "granted_alias": record.granted_alias,
                            "fallback_reason": record.fallback_reason,
                            "authority_ceiling": record.authority_ceiling,
                            "fallback_from": record.fallback_from,
                        }
                        for alias, record in sorted(hub.aliases.items())
                    },
                    "alias_bundles": {
                        bundle_path: {
                            "bundle_type": bundle.bundle_type,
                            "delegated_to_registry_hub": bundle.delegated_to_registry_hub,
                            "authority_scope": bundle.authority_scope,
                            "approved_by_registry_hub": bundle.approved_by_registry_hub,
                            "status": bundle.status,
                            "visibility": bundle.visibility,
                            "allowed_record_types": list(bundle.allowed_record_types),
                            "policy": dict(bundle.policy),
                            "created_by_device_id": bundle.created_by_device_id,
                        }
                        for bundle_path, bundle in sorted(hub.alias_bundles.items())
                    },
                    "devices": {
                        device_id: {
                            "label": record.current_label,
                            "requested_label": record.requested_label,
                            "state": record.current_state,
                            "attachment": record.current_attachment,
                            "checkpoint_tier": record.checkpoint_tier,
                        }
                        for device_id, record in sorted(hub.devices.items())
                    },
                    "conflicts": {
                        conflict_id: {
                            "conflict_type": conflict.conflict_type,
                            "requested_label": conflict.requested_label,
                            "existing_device_id": conflict.existing_device_id,
                            "requesting_device_id": conflict.requesting_device_id,
                            "assigned_temp_label": conflict.assigned_temp_label,
                            "status": conflict.status,
                        }
                        for conflict_id, conflict in sorted(hub.conflicts.items())
                    },
                    "quarantines": {
                        device_id: {
                            "reason": quarantine.reason,
                            "source_hub_id": quarantine.source_hub_id,
                            "status": quarantine.status,
                        }
                        for device_id, quarantine in sorted(hub.quarantines.items())
                    },
                    "local_sessions": {
                        session_id: {
                            "device_id": session.device_id,
                            "scope": session.scope,
                            "auth_mode": session.auth_mode,
                            "current_counter": session.current_counter,
                            "created_at": session.created_at,
                            "expires_at": session.expires_at,
                            "state": session.state,
                            "rotation_index": session.rotation_index,
                        }
                        for session_id, session in sorted(hub.local_sessions.items())
                    },
                }
                for hub_id, hub in sorted(self.registry_hubs.items())
            },
            "traffic_hubs": {
                hub_id: {
                    "neighbors": sorted(hub.neighbors),
                    "neighbor_details": {
                        neighbor_id: {
                            "status": neighbor.status,
                            "latency_ms": neighbor.metrics.latency_ms,
                            "congestion": neighbor.metrics.congestion,
                            "trust": neighbor.metrics.trust,
                            "stability": neighbor.metrics.stability,
                        }
                        for neighbor_id, neighbor in sorted(hub.neighbors.items())
                    },
                    "direct_attachments": {
                        device_id: {
                            "hub_id": record.hub_id,
                            "status": record.status,
                            "attachment_type": record.attachment_type,
                        }
                        for device_id, record in sorted(hub.direct_attachments.items())
                    },
                    "lanes": sorted(hub.lanes),
                    "routes": {
                        target_id: route.to_decision().to_dict()
                        for target_id, route in sorted(hub.routes.items())
                    },
                    "recommendations": [
                        recommendation.recommendation_type
                        for recommendation in hub.growth_recommendations
                    ],
                }
                for hub_id, hub in sorted(self.traffic_hubs.items())
            },
            "lanes": {
                lane_id: {
                    "source": lane.source_device_id,
                    "target": lane.target_device_id,
                    "state": lane.state,
                    "route": list(lane.current_route),
                    "route_total_cost": lane.route_total_cost,
                    "route_cost_breakdown": (
                        None
                        if lane.route_cost_breakdown is None
                        else lane.route_cost_breakdown.to_dict()
                    ),
                    "last_sent_sequence": lane.last_sent_sequence,
                    "last_acknowledged_sequence": lane.last_acknowledged_sequence,
                }
                for lane_id, lane in sorted(self.lanes.items())
            },
            "recommendations": {
                hub_id: [
                    {
                        "recommendation_id": recommendation.recommendation_id,
                        "recommendation_type": recommendation.recommendation_type,
                        "affected_hubs": list(recommendation.affected_hubs),
                        "affected_branches": list(recommendation.affected_branches),
                        "reason": recommendation.reason,
                        "confidence": recommendation.confidence,
                        "status": recommendation.status,
                    }
                    for recommendation in hub.growth_recommendations
                ]
                for hub_id, hub in sorted(self.traffic_hubs.items())
            },
            "alias_authority_claims": self._alias_authority_claim_snapshots(),
        }

    def _alias_authority_claim_snapshots(self) -> list[dict[str, object]]:
        claims = []
        for result in self.action_results:
            authority_path = getattr(result, "authority_path", None)
            if authority_path is None:
                continue

            authority_summary = authority_path.to_summary()
            claims.append(
                {
                    "requested_alias": getattr(result, "requested_alias", None),
                    "granted_alias": getattr(result, "granted_alias", None),
                    "status": getattr(result, "status", None),
                    "reason": getattr(result, "reason", None),
                    "success": getattr(result, "success", None),
                    "authority_ceiling": getattr(result, "authority_ceiling", None),
                    "authority_path": authority_summary.to_dict(),
                }
            )
        return claims
