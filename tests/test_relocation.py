from darwin.models.checkpoint import make_checkpoint_packet
from darwin.models.device import Device
from darwin.models.hub import RegistryHub, TrafficHub
from darwin.registry.checkpoints import record_checkpoint
from darwin.registry.operations import register_device
from darwin.registry.relocation import (
    create_move_contract,
    get_latest_move,
    mark_in_transit,
    update_attachment_after_move,
)
from darwin.traffic.lanes import open_lane, send_lane_data
from darwin.traffic.relocation import pause_lanes_for_relocation, resume_lanes_after_relocation
from darwin.traffic.routing import attach_device, connect_neighbor, detach_device


def make_registry_hub() -> RegistryHub:
    return RegistryHub(hub_id="hub_home_001", scope_path="global.family.david.home")


def test_mark_in_transit_updates_registry_state():
    hub = make_registry_hub()
    device = Device(device_id="dev_A9F3", label="phone")
    register_device(hub, device, checkpoint_tier=2)
    record_checkpoint(hub, make_checkpoint_packet(device, hub.hub_id, "online", current_time=10))

    result = mark_in_transit(hub, "dev_A9F3", current_time=11)

    assert result.success
    assert result.action == "marked_in_transit"
    assert hub.devices["dev_A9F3"].current_state == "in_transit"
    assert hub.checkpoints["dev_A9F3"].state == "in_transit"
    assert hub.attachments["dev_A9F3"].state == "in_transit"
    assert hub.attachments["dev_A9F3"].attachment_type == "in_transit"


def test_pause_lanes_for_relocation_marks_lane_paused():
    hub = TrafficHub(hub_id="hub_home_001")
    attach_device(hub, Device(device_id="dev_A9F3", label="source"))
    attach_device(hub, Device(device_id="dev_B2C8", label="target"))
    open_lane(hub, "dev_A9F3", "dev_B2C8", lane_id="lane_001")

    result = pause_lanes_for_relocation(hub, "dev_B2C8")

    assert result.action == "lanes_paused"
    assert result.affected_lanes == ["lane_001"]
    assert hub.lanes["lane_001"].state == "paused_relocation"
    assert "lane_001" in hub.flow_controls
    assert hub.flow_controls["lane_001"].hold_new_packets is True
    assert hub.flow_controls["lane_001"].reason == "recipient_in_transit"


def test_send_on_paused_relocation_lane_does_not_increment_sequence():
    hub = TrafficHub(hub_id="hub_home_001")
    attach_device(hub, Device(device_id="dev_A9F3", label="source"))
    attach_device(hub, Device(device_id="dev_B2C8", label="target"))
    open_lane(hub, "dev_A9F3", "dev_B2C8", lane_id="lane_001")
    first_result = send_lane_data(hub, "lane_001", {"message": "first"})
    pause_lanes_for_relocation(hub, "dev_B2C8")

    paused_result = send_lane_data(hub, "lane_001", {"message": "second"})

    assert first_result.action == "delivered"
    assert paused_result.action == "lane_paused_relocation"
    assert hub.lanes["lane_001"].last_sent_sequence == 1
    assert hub.lanes["lane_001"].last_acknowledged_sequence == 1


def test_create_valid_move_contract():
    contract = create_move_contract(
        device_id="dev_A9F3",
        passport_id="passport_dev_A9F3",
        from_scope="global.family.david.home",
        to_scope="global.family.david.office",
        old_attachment="hub_home_001",
        new_attachment="hub_office_001",
        valid=True,
        timestamp=42,
    )

    assert contract.device_id == "dev_A9F3"
    assert contract.old_attachment == "hub_home_001"
    assert contract.new_attachment == "hub_office_001"
    assert contract.valid is True
    assert contract.move_id == "move_dev_A9F3_hub_office_001"


def test_update_attachment_after_valid_move_records_move():
    hub = make_registry_hub()
    device = Device(device_id="dev_A9F3", label="phone")
    register_device(hub, device)
    contract = create_move_contract(
        device_id="dev_A9F3",
        passport_id="passport_dev_A9F3",
        from_scope="global.family.david.home",
        to_scope="global.family.david.office",
        old_attachment="hub_home_001",
        new_attachment="hub_office_001",
    )

    result = update_attachment_after_move(
        hub,
        "dev_A9F3",
        new_attachment="hub_office_001",
        new_scope="global.family.david.office",
        move_contract=contract,
    )

    assert result.success
    assert hub.devices["dev_A9F3"].current_attachment == "hub_office_001"
    assert hub.devices["dev_A9F3"].current_state == "online"
    assert hub.attachments["dev_A9F3"].current_scope == "global.family.david.office"
    assert get_latest_move(hub, "dev_A9F3") == contract


def test_invalid_move_contract_does_not_update_attachment():
    hub = make_registry_hub()
    device = Device(device_id="dev_A9F3", label="phone")
    register_device(hub, device)
    contract = create_move_contract(
        device_id="dev_A9F3",
        passport_id="passport_dev_A9F3",
        from_scope="global.family.david.home",
        to_scope="global.family.david.office",
        old_attachment="hub_home_001",
        new_attachment="hub_office_001",
        valid=False,
    )

    result = update_attachment_after_move(
        hub,
        "dev_A9F3",
        new_attachment="hub_office_001",
        new_scope="global.family.david.office",
        move_contract=contract,
    )

    assert not result.success
    assert result.action == "move_contract_rejected"
    assert result.reason == "invalid_move_contract"
    assert hub.devices["dev_A9F3"].current_attachment == "hub_home_001"
    assert "dev_A9F3" not in hub.moves


def test_relocation_resume_updates_lane_route_and_preserves_sequences():
    hub_1 = TrafficHub(hub_id="hub_1")
    hub_2 = TrafficHub(hub_id="hub_2")
    hub_3 = TrafficHub(hub_id="hub_3")
    hub_4 = TrafficHub(hub_id="hub_4")
    hubs = {hub.hub_id: hub for hub in [hub_1, hub_2, hub_3, hub_4]}
    connect_neighbor(hub_1, hub_2)
    connect_neighbor(hub_2, hub_3)
    connect_neighbor(hub_2, hub_4)
    attach_device(hub_1, Device(device_id="dev_A9F3", label="source"))
    target = Device(device_id="dev_B2C8", label="target")
    attach_device(hub_3, target)
    open_lane(hub_1, "dev_A9F3", "dev_B2C8", hubs, lane_id="lane_001")
    send_lane_data(hub_1, "lane_001", {"message": "first"}, hubs)
    send_lane_data(hub_1, "lane_001", {"message": "second"}, hubs)
    pause_lanes_for_relocation(hub_1, "dev_B2C8")
    detach_device(hub_3, "dev_B2C8")
    attach_device(hub_4, target)

    result = resume_lanes_after_relocation(hub_1, "dev_B2C8", all_hubs=hubs)

    assert result.action == "lanes_resumed"
    assert hub_1.lanes["lane_001"].state == "active"
    assert hub_1.lanes["lane_001"].current_route == ["hub_1", "hub_2", "hub_4"]
    assert hub_1.lanes["lane_001"].last_sent_sequence == 2
    assert hub_1.lanes["lane_001"].last_acknowledged_sequence == 2
    assert "lane_001" not in hub_1.flow_controls


def test_resume_without_reachable_new_route_returns_clean_failure():
    hub_1 = TrafficHub(hub_id="hub_1")
    hub_2 = TrafficHub(hub_id="hub_2")
    hubs = {hub.hub_id: hub for hub in [hub_1, hub_2]}
    connect_neighbor(hub_1, hub_2)
    attach_device(hub_1, Device(device_id="dev_A9F3", label="source"))
    attach_device(hub_2, Device(device_id="dev_B2C8", label="target"))
    open_lane(hub_1, "dev_A9F3", "dev_B2C8", hubs, lane_id="lane_001")
    pause_lanes_for_relocation(hub_1, "dev_B2C8")
    detach_device(hub_2, "dev_B2C8")

    result = resume_lanes_after_relocation(hub_1, "dev_B2C8", all_hubs=hubs)

    assert result.action == "route_unavailable"
    assert result.failed_lanes == ["lane_001"]
    assert hub_1.lanes["lane_001"].state in {"paused_relocation", "awaiting_verification"}
    assert "lane_001" in hub_1.flow_controls


def test_unknown_device_mark_in_transit_returns_clean_failure():
    hub = make_registry_hub()

    result = mark_in_transit(hub, "dev_MISSING")

    assert not result.success
    assert result.action == "device_not_found"
    assert result.reason == "unknown_device"
    assert hub.devices == {}
    assert hub.relocations == {}

