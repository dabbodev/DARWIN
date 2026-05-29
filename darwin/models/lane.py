"""Logical lane models for persistent symbolic traffic relationships."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from darwin.models.route import RouteCostBreakdown


@dataclass(slots=True)
class LogicalLane:
    """Persistent connection relationship between two durable device IDs."""

    lane_id: str
    source_device_id: str
    target_device_id: str
    lane_mode: str = "reliable_ordered"
    state: str = "opening"
    current_route: list[str] = field(default_factory=list)
    route_total_cost: float | None = None
    route_cost_breakdown: RouteCostBreakdown | None = None
    last_sent_sequence: int = 0
    last_acknowledged_sequence: int = 0

    def activate(self) -> None:
        self.state = "active"

    def close(self) -> None:
        self.state = "closing"

    def terminate(self) -> None:
        self.state = "terminated"


@dataclass(slots=True)
class LaneOpenResult:
    lane_id: str | None
    action: str
    source_device_id: str
    target_device_id: str
    lane: LogicalLane | None = None
    route: list[str] = field(default_factory=list)
    next_hop: str | None = None
    final_hub_id: str | None = None
    route_status: str | None = None
    total_cost: float | None = None
    cost_breakdown: RouteCostBreakdown | None = None


@dataclass(slots=True)
class LaneSendResult:
    lane_id: str
    action: str
    source_device_id: str | None = None
    target_device_id: str | None = None
    packet_id: str | None = None
    sequence_number: int | None = None
    route: list[str] = field(default_factory=list)
    next_hop: str | None = None
    final_hub_id: str | None = None
    route_status: str | None = None
    total_cost: float | None = None
    cost_breakdown: RouteCostBreakdown | None = None
    last_sent_sequence: int | None = None
    last_acknowledged_sequence: int | None = None
    payload: Any = None


@dataclass(slots=True)
class LaneAckResult:
    lane_id: str
    action: str
    sequence_number: int
    last_acknowledged_sequence: int


@dataclass(slots=True)
class LaneCloseResult:
    lane_id: str
    action: str
    state: str | None = None
