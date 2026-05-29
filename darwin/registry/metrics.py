"""Registry metric counters and advisory growth recommendations."""

from __future__ import annotations

from darwin.models.hub import RegistryHub
from darwin.models.recommendation import GrowthPolicy, GrowthRecommendation


def refresh_registry_counts(hub: RegistryHub) -> None:
    """Refresh count gauges from current RegistryHub state."""
    hub.metrics.device_count = len(hub.devices)
    hub.metrics.active_device_count = sum(
        1 for device in hub.devices.values() if device.current_state == "online"
    )


def record_registry_lookup(hub: RegistryHub, found: bool) -> None:
    """Record a registry lookup and whether it missed."""
    hub.metrics.lookup_count += 1
    if not found:
        hub.metrics.lookup_miss_count += 1


def record_label_conflict(hub: RegistryHub) -> None:
    """Record a local label conflict."""
    hub.metrics.label_conflict_count += 1


def record_duplicate_device_conflict(hub: RegistryHub) -> None:
    """Record a duplicate active durable-ID claim."""
    hub.metrics.duplicate_device_conflict_count += 1


def record_checkpoint_update(hub: RegistryHub) -> None:
    """Record a successful checkpoint update."""
    hub.metrics.checkpoint_update_count += 1
    refresh_registry_counts(hub)


def record_move_contract(hub: RegistryHub) -> None:
    """Record a successful move contract application."""
    hub.metrics.move_contract_count += 1
    refresh_registry_counts(hub)


def record_summary_generation(hub: RegistryHub) -> None:
    """Record an upward summary generation."""
    hub.metrics.summary_generation_count += 1


def record_upward_summary_acceptance(hub: RegistryHub) -> None:
    """Record an accepted child summary."""
    hub.metrics.upward_summary_accept_count += 1


def recommend_registry_split(
    registry_hub: RegistryHub,
    policy: GrowthPolicy | None = None,
) -> GrowthRecommendation | None:
    """Recommend splitting a registry scope when symbolic identity pressure is high."""
    active_policy = policy or GrowthPolicy()

    if registry_hub.metrics.device_count > active_policy.registry_split_device_count_threshold:
        return GrowthRecommendation(
            recommendation_id=_recommendation_id(
                registry_hub.hub_id,
                "split_registry_scope",
                "high_device_count",
            ),
            recommendation_type="split_registry_scope",
            affected_hubs=[registry_hub.hub_id],
            affected_branches=[registry_hub.scope_path],
            reason="high_device_count",
            confidence="high",
            expected_benefit="reduce_registry_identity_pressure",
            requires_admin_approval=True,
        )

    miss_rate = _lookup_miss_rate(registry_hub)
    if (
        registry_hub.metrics.lookup_count > 0
        and miss_rate > active_policy.registry_lookup_miss_rate_threshold
    ):
        return GrowthRecommendation(
            recommendation_id=_recommendation_id(
                registry_hub.hub_id,
                "split_registry_scope",
                "high_lookup_miss_rate",
            ),
            recommendation_type="split_registry_scope",
            affected_hubs=[registry_hub.hub_id],
            affected_branches=[registry_hub.scope_path],
            reason="high_lookup_miss_rate",
            confidence="medium",
            expected_benefit="improve_registry_scope_fit",
            requires_admin_approval=True,
        )

    return None


def recommend_security_pressure(
    registry_hub: RegistryHub,
    policy: GrowthPolicy | None = None,
) -> GrowthRecommendation | None:
    """Recommend investigation when registry identity conflict pressure is high."""
    active_policy = policy or GrowthPolicy()
    if (
        registry_hub.metrics.duplicate_device_conflict_count
        <= active_policy.security_pressure_invalid_auth_threshold
    ):
        return None

    return GrowthRecommendation(
        recommendation_id=_recommendation_id(
            registry_hub.hub_id,
            "investigate_security_pressure",
            "duplicate_identity_pressure",
        ),
        recommendation_type="investigate_security_pressure",
        affected_hubs=[registry_hub.hub_id],
        affected_branches=[registry_hub.scope_path],
        reason="duplicate_identity_pressure",
        confidence="high",
        expected_benefit="surface_repeated_symbolic_identity_conflicts",
        requires_admin_approval=True,
    )


def _lookup_miss_rate(registry_hub: RegistryHub) -> float:
    if registry_hub.metrics.lookup_count == 0:
        return 0.0
    return registry_hub.metrics.lookup_miss_count / registry_hub.metrics.lookup_count


def _recommendation_id(hub_id: str, recommendation_type: str, reason: str) -> str:
    return f"{hub_id}:{recommendation_type}:{reason}"
