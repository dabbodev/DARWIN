from darwin.models.device import Device
from darwin.models.hub import TrafficHub
from darwin.models.packet import DarwinPacket
from darwin.traffic.routing import attach_device, connect_neighbor, forward_packet, select_route


def _hubs(*hub_ids: str) -> dict[str, TrafficHub]:
    return {hub_id: TrafficHub(hub_id=hub_id) for hub_id in hub_ids}


def _packet(packet_id: str, source: str, target: str) -> DarwinPacket:
    return DarwinPacket(
        packet_id=packet_id,
        packet_class="traffic",
        packet_type="message",
        source_device_id=source,
        target_device_id=target,
    )


def test_default_route_cost_preserves_existing_shortest_path():
    hubs = _hubs("hub_1", "hub_2", "hub_3")
    connect_neighbor(hubs["hub_1"], hubs["hub_2"])
    connect_neighbor(hubs["hub_2"], hubs["hub_3"])
    attach_device(hubs["hub_3"], Device(device_id="dev_target", label="target"))

    route = select_route(hubs["hub_1"], "dev_target", hubs)

    assert route is not None
    assert route.route == ["hub_1", "hub_2", "hub_3"]
    assert route.route_status == "available"


def test_lowest_cost_route_can_choose_more_hops():
    hubs = _hubs("hub_1", "hub_2", "hub_3", "hub_4", "hub_5")
    connect_neighbor(hubs["hub_1"], hubs["hub_2"], latency_ms=100, congestion="high")
    connect_neighbor(hubs["hub_2"], hubs["hub_4"], latency_ms=100, congestion="high")
    connect_neighbor(hubs["hub_1"], hubs["hub_3"], latency_ms=1, congestion="low")
    connect_neighbor(hubs["hub_3"], hubs["hub_5"], latency_ms=1, congestion="low")
    connect_neighbor(hubs["hub_5"], hubs["hub_4"], latency_ms=1, congestion="low")
    attach_device(hubs["hub_4"], Device(device_id="dev_target", label="target"))

    route = select_route(hubs["hub_1"], "dev_target", hubs)

    assert route is not None
    assert route.route == ["hub_1", "hub_3", "hub_5", "hub_4"]
    assert route.total_cost < 20


def test_blocked_link_is_avoided():
    hubs = _hubs("hub_1", "hub_2", "hub_3", "hub_4")
    connect_neighbor(hubs["hub_1"], hubs["hub_2"], congestion="blocked")
    connect_neighbor(hubs["hub_2"], hubs["hub_4"])
    connect_neighbor(hubs["hub_1"], hubs["hub_3"])
    connect_neighbor(hubs["hub_3"], hubs["hub_4"])
    attach_device(hubs["hub_4"], Device(device_id="dev_target", label="target"))

    route = select_route(hubs["hub_1"], "dev_target", hubs)

    assert route is not None
    assert route.route == ["hub_1", "hub_3", "hub_4"]


def test_untrusted_link_is_avoided_by_default():
    hubs = _hubs("hub_1", "hub_2", "hub_3", "hub_4")
    connect_neighbor(hubs["hub_1"], hubs["hub_2"], trust="untrusted")
    connect_neighbor(hubs["hub_2"], hubs["hub_4"])
    connect_neighbor(hubs["hub_1"], hubs["hub_3"], trust="verified")
    connect_neighbor(hubs["hub_3"], hubs["hub_4"], trust="verified")
    attach_device(hubs["hub_4"], Device(device_id="dev_target", label="target"))

    route = select_route(hubs["hub_1"], "dev_target", hubs)

    assert route is not None
    assert route.route == ["hub_1", "hub_3", "hub_4"]


def test_route_cost_tie_break_is_deterministic():
    hubs = _hubs("hub_1", "hub_2", "hub_3", "hub_4")
    connect_neighbor(hubs["hub_1"], hubs["hub_3"])
    connect_neighbor(hubs["hub_3"], hubs["hub_4"])
    connect_neighbor(hubs["hub_1"], hubs["hub_2"])
    connect_neighbor(hubs["hub_2"], hubs["hub_4"])
    attach_device(hubs["hub_4"], Device(device_id="dev_target", label="target"))

    routes = [
        select_route(hubs["hub_1"], "dev_target", hubs).route
        for _ in range(10)
    ]

    assert routes == [["hub_1", "hub_2", "hub_4"]] * 10


def test_direct_attachment_still_wins():
    hubs = _hubs("hub_1", "hub_2", "hub_3")
    connect_neighbor(hubs["hub_1"], hubs["hub_2"], latency_ms=1)
    connect_neighbor(hubs["hub_2"], hubs["hub_3"], latency_ms=1)
    attach_device(hubs["hub_1"], Device(device_id="dev_target", label="local"))
    attach_device(hubs["hub_3"], Device(device_id="dev_target", label="remote"))

    route = select_route(hubs["hub_1"], "dev_target", hubs)

    assert route is not None
    assert route.route == ["hub_1"]
    assert route.total_cost == 0


def test_forward_packet_reports_route_cost():
    hubs = _hubs("hub_1", "hub_2", "hub_3")
    connect_neighbor(hubs["hub_1"], hubs["hub_2"], latency_ms=5, congestion="medium")
    connect_neighbor(hubs["hub_2"], hubs["hub_3"], latency_ms=2, stability="variable")
    attach_device(hubs["hub_1"], Device(device_id="dev_source", label="source"))
    attach_device(hubs["hub_3"], Device(device_id="dev_target", label="target"))

    result = forward_packet(
        hubs["hub_1"],
        _packet("pkt_001", "dev_source", "dev_target"),
        hubs,
    )

    assert result.action == "delivered"
    assert result.route == ["hub_1", "hub_2", "hub_3"]
    assert result.route_status == "available"
    assert result.total_cost is not None
    assert result.total_cost > 0
    assert result.cost_breakdown is not None
    assert result.cost_breakdown.total == result.total_cost
