from darwin.models.device import Device
from darwin.models.hub import TrafficHub
from darwin.models.packet import DarwinPacket
from darwin.traffic.routing import (
    attach_device,
    connect_neighbor,
    forward_packet,
    select_route,
)


def make_packet(packet_id: str, source_device_id: str, target_device_id: str) -> DarwinPacket:
    return DarwinPacket(
        packet_id=packet_id,
        packet_class="traffic",
        packet_type="message",
        source_device_id=source_device_id,
        target_device_id=target_device_id,
    )


def test_direct_local_delivery_route():
    hub = TrafficHub(hub_id="hub_home_001")
    source = Device(device_id="dev_A9F3", label="source")
    target = Device(device_id="dev_B2C8", label="target")
    attach_device(hub, source)
    attach_device(hub, target)

    route = select_route(hub, "dev_B2C8")
    result = forward_packet(hub, make_packet("pkt_001", "dev_A9F3", "dev_B2C8"))

    assert route is not None
    assert route.route == ["hub_home_001"]
    assert route.final_hub_id == "hub_home_001"
    assert result.action == "delivered"
    assert result.route == ["hub_home_001"]
    assert result.final_hub_id == "hub_home_001"


def test_routed_delivery_across_three_hubs():
    hub_1 = TrafficHub(hub_id="hub_1")
    hub_2 = TrafficHub(hub_id="hub_2")
    hub_3 = TrafficHub(hub_id="hub_3")
    hubs = {hub.hub_id: hub for hub in [hub_1, hub_2, hub_3]}
    connect_neighbor(hub_1, hub_2)
    connect_neighbor(hub_2, hub_3)
    attach_device(hub_1, Device(device_id="dev_A9F3", label="source"))
    attach_device(hub_3, Device(device_id="dev_B2C8", label="target"))

    route = select_route(hub_1, "dev_B2C8", hubs)
    result = forward_packet(hub_1, make_packet("pkt_002", "dev_A9F3", "dev_B2C8"), hubs)

    assert route is not None
    assert route.route == ["hub_1", "hub_2", "hub_3"]
    assert result.action == "delivered"
    assert result.route == ["hub_1", "hub_2", "hub_3"]
    assert result.next_hop == "hub_2"
    assert result.final_hub_id == "hub_3"


def test_no_route_returns_route_unavailable():
    hub_1 = TrafficHub(hub_id="hub_1")
    hub_2 = TrafficHub(hub_id="hub_2")
    hubs = {hub.hub_id: hub for hub in [hub_1, hub_2]}
    attach_device(hub_2, Device(device_id="dev_B2C8", label="target"))

    route = select_route(hub_1, "dev_B2C8", hubs)
    result = forward_packet(hub_1, make_packet("pkt_003", "dev_A9F3", "dev_B2C8"), hubs)

    assert route is None
    assert result.action == "route_unavailable"
    assert result.route == []
    assert result.final_hub_id is None


def test_shortest_route_wins():
    hub_1 = TrafficHub(hub_id="hub_1")
    hub_2 = TrafficHub(hub_id="hub_2")
    hub_3 = TrafficHub(hub_id="hub_3")
    hub_4 = TrafficHub(hub_id="hub_4")
    hubs = {hub.hub_id: hub for hub in [hub_1, hub_2, hub_3, hub_4]}
    connect_neighbor(hub_1, hub_2)
    connect_neighbor(hub_2, hub_4)
    connect_neighbor(hub_1, hub_3)
    connect_neighbor(hub_3, hub_2)
    attach_device(hub_4, Device(device_id="dev_B2C8", label="target"))

    route = select_route(hub_1, "dev_B2C8", hubs)

    assert route is not None
    assert route.route == ["hub_1", "hub_2", "hub_4"]


def test_direct_attachment_preferred():
    hub_1 = TrafficHub(hub_id="hub_1")
    hub_2 = TrafficHub(hub_id="hub_2")
    hub_3 = TrafficHub(hub_id="hub_3")
    hubs = {hub.hub_id: hub for hub in [hub_1, hub_2, hub_3]}
    connect_neighbor(hub_1, hub_2)
    connect_neighbor(hub_2, hub_3)
    attach_device(hub_1, Device(device_id="dev_B2C8", label="local_target"))
    attach_device(hub_3, Device(device_id="dev_B2C8", label="remote_target"))

    route = select_route(hub_1, "dev_B2C8", hubs)

    assert route is not None
    assert route.route == ["hub_1"]
