"""Route record placeholders."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class RouteRecord:
    target_id: str
    route: list[str] = field(default_factory=list)
    route_status: str = "advisory"
    cost: float = 0.0

    @property
    def next_hop(self) -> str | None:
        return self.route[1] if len(self.route) > 1 else None

    @property
    def final_hub_id(self) -> str | None:
        return self.route[-1] if self.route else None


@dataclass(slots=True)
class ForwardingResult:
    packet_id: str
    action: str
    target_device_id: str | None
    route: list[str] = field(default_factory=list)
    next_hop: str | None = None
    final_hub_id: str | None = None
