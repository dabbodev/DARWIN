"""Route records and simple route-cost policy models."""

from __future__ import annotations

from dataclasses import dataclass, field

CONGESTION_PENALTIES = {
    "low": 0.0,
    "medium": 10.0,
    "high": 50.0,
    "blocked": 1_000_000.0,
}

TRUST_PENALTIES = {
    "verified": 0.0,
    "advisory": 5.0,
    "unknown": 25.0,
    "untrusted": 1_000_000.0,
}

STABILITY_PENALTIES = {
    "stable": 0.0,
    "variable": 5.0,
    "unstable": 20.0,
}


@dataclass(frozen=True, slots=True)
class RoutingPolicy:
    """Weights and avoidance rules for symbolic route-cost scoring."""

    latency_weight: float = 1.0
    congestion_weight: float = 1.0
    trust_weight: float = 1.0
    hop_weight: float = 1.0
    stability_weight: float = 1.0
    avoid_blocked: bool = True
    avoid_untrusted: bool = True

    def __post_init__(self) -> None:
        weights = {
            "latency_weight": self.latency_weight,
            "congestion_weight": self.congestion_weight,
            "trust_weight": self.trust_weight,
            "hop_weight": self.hop_weight,
            "stability_weight": self.stability_weight,
        }
        for field_name, value in weights.items():
            if value < 0:
                raise ValueError(f"{field_name} must be non-negative")


@dataclass(frozen=True, slots=True)
class RouteCostBreakdown:
    """Aggregated weighted cost components for a selected route."""

    latency: float = 0.0
    congestion: float = 0.0
    trust: float = 0.0
    hops: float = 0.0
    stability: float = 0.0

    @property
    def total(self) -> float:
        return self.latency + self.congestion + self.trust + self.hops + self.stability

    def combine(self, other: RouteCostBreakdown) -> RouteCostBreakdown:
        return RouteCostBreakdown(
            latency=self.latency + other.latency,
            congestion=self.congestion + other.congestion,
            trust=self.trust + other.trust,
            hops=self.hops + other.hops,
            stability=self.stability + other.stability,
        )

    def to_dict(self) -> dict[str, float]:
        return {
            "latency": self.latency,
            "congestion": self.congestion,
            "trust": self.trust,
            "hops": self.hops,
            "stability": self.stability,
            "total": self.total,
        }


@dataclass(frozen=True, slots=True)
class LinkMetrics:
    """Symbolic per-link metrics used by the deterministic route selector."""

    latency_ms: int = 1
    congestion: str = "low"
    trust: str = "verified"
    stability: str = "stable"

    def __post_init__(self) -> None:
        if self.latency_ms < 0:
            raise ValueError("latency_ms must be non-negative")
        if self.congestion not in CONGESTION_PENALTIES:
            raise ValueError(f"Unsupported congestion: {self.congestion}")
        if self.trust not in TRUST_PENALTIES:
            raise ValueError(f"Unsupported trust: {self.trust}")
        if self.stability not in STABILITY_PENALTIES:
            raise ValueError(f"Unsupported stability: {self.stability}")

    def is_usable(self, policy: RoutingPolicy) -> bool:
        if policy.avoid_blocked and self.congestion == "blocked":
            return False
        return not (policy.avoid_untrusted and self.trust == "untrusted")

    def cost_breakdown(self, policy: RoutingPolicy) -> RouteCostBreakdown:
        return RouteCostBreakdown(
            latency=float(self.latency_ms) * policy.latency_weight,
            congestion=CONGESTION_PENALTIES[self.congestion] * policy.congestion_weight,
            trust=TRUST_PENALTIES[self.trust] * policy.trust_weight,
            hops=policy.hop_weight,
            stability=STABILITY_PENALTIES[self.stability] * policy.stability_weight,
        )


@dataclass(frozen=True, slots=True)
class RouteDecision:
    """Serializable summary of one route-selection outcome."""

    target_id: str
    route: list[str] = field(default_factory=list)
    route_status: str = "unavailable"
    total_cost: float = 0.0
    next_hop: str | None = None
    final_hub_id: str | None = None
    cost_breakdown: RouteCostBreakdown | None = None

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {
            "target_id": self.target_id,
            "route": list(self.route),
            "route_status": self.route_status,
            "total_cost": self.total_cost,
            "next_hop": self.next_hop,
            "final_hub_id": self.final_hub_id,
        }
        if self.cost_breakdown is not None:
            data["cost_breakdown"] = self.cost_breakdown.to_dict()
        return data


@dataclass(slots=True)
class RouteRecord:
    target_id: str
    route: list[str] = field(default_factory=list)
    route_status: str = "advisory"
    cost: float = 0.0
    total_cost: float = 0.0
    cost_breakdown: RouteCostBreakdown | None = None

    @property
    def next_hop(self) -> str | None:
        return self.route[1] if len(self.route) > 1 else None

    @property
    def final_hub_id(self) -> str | None:
        return self.route[-1] if self.route else None

    def to_decision(self) -> RouteDecision:
        return RouteDecision(
            target_id=self.target_id,
            route=list(self.route),
            route_status=self.route_status,
            total_cost=self.total_cost,
            next_hop=self.next_hop,
            final_hub_id=self.final_hub_id,
            cost_breakdown=self.cost_breakdown,
        )


@dataclass(slots=True)
class ForwardingResult:
    packet_id: str
    action: str
    target_device_id: str | None
    route: list[str] = field(default_factory=list)
    next_hop: str | None = None
    final_hub_id: str | None = None
    route_status: str | None = None
    total_cost: float | None = None
    cost_breakdown: RouteCostBreakdown | None = None
