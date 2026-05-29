from darwin.models.hub import RegistryHub, TrafficHub
from darwin.registry.metrics import recommend_registry_split
from darwin.traffic.metrics import (
    recommend_roaming_witness_hub,
    recommend_security_pressure,
    recommend_traffic_bridge,
    record_cross_tree_packet,
)


def test_traffic_bridge_recommendation_after_cross_tree_pressure():
    hub = TrafficHub(hub_id="traffic_home_001")

    for _ in range(11):
        record_cross_tree_packet(hub, "global.family.home", "global.family.office")

    recommendation = recommend_traffic_bridge(hub)

    assert recommendation is not None
    assert recommendation.recommendation_type == "create_traffic_bridge"
    assert recommendation.reason == "sustained_cross_tree_traffic"
    assert recommendation.requires_admin_approval is True
    assert hub.growth_recommendations == [recommendation]


def test_registry_split_recommendation_after_high_device_count():
    hub = RegistryHub(hub_id="registry_home_001", scope_path="global.family.home")
    hub.metrics.device_count = 251

    recommendation = recommend_registry_split(hub)

    assert recommendation is not None
    assert recommendation.recommendation_type == "split_registry_scope"
    assert recommendation.reason == "high_device_count"


def test_roaming_witness_recommendation_after_relocation_churn():
    hub = TrafficHub(hub_id="traffic_home_001")
    hub.metrics.relocation_count = 6

    recommendation = recommend_roaming_witness_hub(hub)

    assert recommendation is not None
    assert recommendation.recommendation_type == "create_roaming_witness_hub"
    assert recommendation.reason == "high_relocation_churn"


def test_security_pressure_recommendation_after_invalid_auth_spike():
    hub = TrafficHub(hub_id="traffic_home_001")
    hub.metrics.invalid_packet_auth_count = 6

    recommendation = recommend_security_pressure(hub)

    assert recommendation is not None
    assert recommendation.recommendation_type == "investigate_security_pressure"
    assert recommendation.reason == "repeated_symbolic_auth_failures"
