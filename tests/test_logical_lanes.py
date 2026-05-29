from darwin.models.device import Device
from darwin.models.hub import TrafficHub
from darwin.traffic.lanes import (
    acknowledge_lane_packet,
    close_lane,
    open_lane,
    send_lane_data,
)
from darwin.traffic.routing import attach_device, connect_neighbor


def test_open_lane_between_devices_on_same_hub():
    hub = TrafficHub(hub_id="hub_home_001")
    attach_device(hub, Device(device_id="dev_A9F3", label="source"))
    attach_device(hub, Device(device_id="dev_B2C8", label="target"))

    result = open_lane(hub, "dev_A9F3", "dev_B2C8", lane_id="lane_001")

    assert result.action == "lane_opened"
    assert result.lane is not None
    assert result.lane.state == "active"
    assert result.lane.current_route == ["hub_home_001"]
    assert result.lane.last_sent_sequence == 0
    assert result.lane.last_acknowledged_sequence == 0
    assert hub.lanes["lane_001"] == result.lane


def test_open_lane_across_three_hubs():
    hub_1 = TrafficHub(hub_id="hub_1")
    hub_2 = TrafficHub(hub_id="hub_2")
    hub_3 = TrafficHub(hub_id="hub_3")
    hubs = {hub.hub_id: hub for hub in [hub_1, hub_2, hub_3]}
    connect_neighbor(hub_1, hub_2)
    connect_neighbor(hub_2, hub_3)
    attach_device(hub_1, Device(device_id="dev_A9F3", label="source"))
    attach_device(hub_3, Device(device_id="dev_B2C8", label="target"))

    result = open_lane(hub_1, "dev_A9F3", "dev_B2C8", hubs, lane_id="lane_001")

    assert result.action == "lane_opened"
    assert result.lane is not None
    assert result.lane.current_route == ["hub_1", "hub_2", "hub_3"]
    assert result.lane.state == "active"


def test_send_data_over_lane_increments_sequence_and_ack():
    hub = TrafficHub(hub_id="hub_home_001")
    attach_device(hub, Device(device_id="dev_A9F3", label="source"))
    attach_device(hub, Device(device_id="dev_B2C8", label="target"))
    open_result = open_lane(hub, "dev_A9F3", "dev_B2C8", lane_id="lane_001")

    first_result = send_lane_data(hub, "lane_001", {"message": "first"})
    second_result = send_lane_data(hub, "lane_001", {"message": "second"})

    assert open_result.lane is not None
    assert first_result.action == "delivered"
    assert first_result.sequence_number == 1
    assert second_result.action == "delivered"
    assert second_result.sequence_number == 2
    assert open_result.lane.last_sent_sequence == 2
    assert open_result.lane.last_acknowledged_sequence == 2


def test_open_lane_fails_when_target_unreachable():
    hub_1 = TrafficHub(hub_id="hub_1")
    hub_2 = TrafficHub(hub_id="hub_2")
    hubs = {hub.hub_id: hub for hub in [hub_1, hub_2]}
    attach_device(hub_1, Device(device_id="dev_A9F3", label="source"))
    attach_device(hub_2, Device(device_id="dev_B2C8", label="target"))

    result = open_lane(hub_1, "dev_A9F3", "dev_B2C8", hubs, lane_id="lane_001")

    assert result.action == "route_unavailable"
    assert result.lane is None
    assert "lane_001" not in hub_1.lanes


def test_send_on_unknown_lane_returns_clean_failure():
    hub = TrafficHub(hub_id="hub_home_001")

    result = send_lane_data(hub, "lane_missing", {"message": "payload"})

    assert result.action == "lane_not_found"
    assert result.lane_id == "lane_missing"


def test_send_on_terminated_lane_returns_clean_failure():
    hub = TrafficHub(hub_id="hub_home_001")
    attach_device(hub, Device(device_id="dev_A9F3", label="source"))
    attach_device(hub, Device(device_id="dev_B2C8", label="target"))
    open_result = open_lane(hub, "dev_A9F3", "dev_B2C8", lane_id="lane_001")
    close_result = close_lane(hub, "lane_001")

    result = send_lane_data(hub, "lane_001", {"message": "after close"})

    assert open_result.lane is not None
    assert close_result.action == "lane_terminated"
    assert result.action == "lane_not_active"
    assert open_result.lane.last_sent_sequence == 0
    assert open_result.lane.last_acknowledged_sequence == 0


def test_ack_never_moves_backward():
    hub = TrafficHub(hub_id="hub_home_001")
    attach_device(hub, Device(device_id="dev_A9F3", label="source"))
    attach_device(hub, Device(device_id="dev_B2C8", label="target"))
    open_result = open_lane(hub, "dev_A9F3", "dev_B2C8", lane_id="lane_001")
    send_lane_data(hub, "lane_001", {"message": "first"})
    send_lane_data(hub, "lane_001", {"message": "second"})

    ack_result = acknowledge_lane_packet(hub, "lane_001", 1)

    assert open_result.lane is not None
    assert ack_result.action == "ack_ignored"
    assert open_result.lane.last_acknowledged_sequence == 2
