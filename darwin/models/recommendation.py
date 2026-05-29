"""Advisory growth recommendation models for DARWIN v0.1."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class GrowthPolicy:
    """Simple threshold policy for symbolic growth recommendations."""

    traffic_bridge_cross_tree_threshold: int = 10
    registry_split_device_count_threshold: int = 250
    registry_lookup_miss_rate_threshold: float = 0.20
    roaming_witness_relocation_threshold: int = 5
    security_pressure_invalid_auth_threshold: int = 5


@dataclass(slots=True)
class GrowthRecommendation:
    """Advisory record describing a possible simulator topology improvement."""

    recommendation_id: str
    recommendation_type: str
    affected_hubs: list[str] = field(default_factory=list)
    affected_branches: list[str] = field(default_factory=list)
    reason: str = ""
    confidence: str = "medium"
    expected_benefit: str = ""
    requires_admin_approval: bool = True
    status: str = "proposed"


@dataclass(slots=True)
class MetricsSampleResult:
    """Result wrapper for explicit metric sampling helpers."""

    hub_id: str
    sample_type: str
    metric_name: str
    metric_value: int | float


@dataclass(slots=True)
class TrafficBridgeRecommendationResult:
    """Outcome of evaluating traffic bridge pressure."""

    recommended: bool
    recommendation: GrowthRecommendation | None = None


@dataclass(slots=True)
class RegistrySplitRecommendationResult:
    """Outcome of evaluating registry split pressure."""

    recommended: bool
    recommendation: GrowthRecommendation | None = None


@dataclass(slots=True)
class RoamingWitnessRecommendationResult:
    """Outcome of evaluating roaming witness pressure."""

    recommended: bool
    recommendation: GrowthRecommendation | None = None
