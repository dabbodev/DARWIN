from darwin.models.device import Device
from darwin.models.hub import RegistryHub, TrafficHub
from darwin.models.packet import DarwinPacket
from darwin.registry.operations import register_device, resolve_device_id, resolve_label
from darwin.traffic.lanes import open_lane, send_lane_data
from darwin.traffic.routing import attach_device, forward_packet


def make_packet(
    packet_id: str,
    source_device_id: str,
    target_device_id: str,
    auth_tag_valid: bool = True,
) -> DarwinPacket:
    return DarwinPacket(
        packet_id=packet_id,
        packet_class="traffic",
        packet_type="message",
        source_device_id=source_device_id,
        target_device_id=target_device_id,
        auth_tag_valid=auth_tag_valid,
    )


def test_traffic_metrics_increment_on_successful_forward():
    hub = TrafficHub(hub_id="hub_home_001")
    attach_device(hub, Device(device_id="dev_A9F3", label="source"))
    attach_device(hub, Device(device_id="dev_B2C8", label="target"))

    result = forward_packet(hub, make_packet("pkt_001", "dev_A9F3", "dev_B2C8"))

    assert result.action == "delivered"
    assert hub.metrics.packets_forwarded == 1
    assert hub.metrics.packets_delivered == 1


def test_traffic_metrics_increment_on_route_unavailable():
    hub = TrafficHub(hub_id="hub_home_001")

    result = forward_packet(hub, make_packet("pkt_001", "dev_A9F3", "dev_MISSING"))

    assert result.action == "route_unavailable"
    assert hub.metrics.route_unavailable_count == 1


def test_invalid_packet_auth_increments_security_metric():
    hub = TrafficHub(hub_id="hub_home_001")
    attach_device(hub, Device(device_id="dev_A9F3", label="source"))
    attach_device(hub, Device(device_id="dev_B2C8", label="target"))

    result = forward_packet(
        hub,
        make_packet("pkt_bad_auth", "dev_A9F3", "dev_B2C8", auth_tag_valid=False),
    )

    assert result.action == "invalid_auth_tag"
    assert hub.metrics.invalid_packet_auth_count == 1


def test_lane_metrics_increment_on_open_and_send():
    hub = TrafficHub(hub_id="hub_home_001")
    attach_device(hub, Device(device_id="dev_A9F3", label="source"))
    attach_device(hub, Device(device_id="dev_B2C8", label="target"))

    open_result = open_lane(hub, "dev_A9F3", "dev_B2C8", lane_id="lane_001")
    send_result = send_lane_data(hub, "lane_001", {"message": "hello"})

    assert open_result.action == "lane_opened"
    assert send_result.action == "delivered"
    assert hub.metrics.lane_open_count == 1
    assert hub.metrics.lane_send_count == 1


def test_registry_metrics_increment_on_registration_and_lookup():
    hub = RegistryHub(hub_id="registry_home_001", scope_path="global.family.home")
    device = Device(device_id="dev_A9F3", label="phone")

    register_device(hub, device)
    record = resolve_device_id(hub, "dev_A9F3")

    assert record is not None
    assert hub.metrics.device_count == 1
    assert hub.metrics.active_device_count == 1
    assert hub.metrics.lookup_count == 1


def test_registry_lookup_miss_metric():
    hub = RegistryHub(hub_id="registry_home_001", scope_path="global.family.home")

    label_result = resolve_label(hub, "missing")
    device_result = resolve_device_id(hub, "dev_MISSING")

    assert label_result is None
    assert device_result is None
    assert hub.metrics.lookup_count == 2
    assert hub.metrics.lookup_miss_count == 2
