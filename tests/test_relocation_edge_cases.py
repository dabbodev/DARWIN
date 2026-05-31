from darwin.models.device import Device
from darwin.models.hub import RegistryHub, TrafficHub
from darwin.registry.operations import register_device
from darwin.registry.relocation import (
    create_move_contract,
    mark_in_transit,
    update_attachment_after_move,
)
from darwin.registry.security import detect_duplicate_device_claim
from darwin.traffic.lanes import open_lane, send_lane_data
from darwin.traffic.relocation import (
    expire_relocation_hold,
    pause_lanes_for_relocation,
    resume_lanes_after_relocation,
)
from darwin.traffic.routing import attach_device, connect_neighbor, detach_device


def test_relocation_timeout_marks_relocation_failed():
    hub = TrafficHub(hub_id="hub_1")
    attach_device(hub, Device(device_id="dev_A9F3", label="source"))
    attach_device(hub, Device(device_id="dev_B2C8", label="target"))
    open_lane(hub, "dev_A9F3", "dev_B2C8", lane_id="lane_001")
    pause_lanes_for_relocation(hub, "dev_B2C8")

    result = expire_relocation_hold(hub, "dev_B2C8", current_time=50)

    assert result.action == "relocation_failed"
    assert result.reason == "relocation_timeout"
    assert result.failed_lanes == ["lane_001"]
    assert hub.relocations["dev_B2C8"].state == "failed"
    assert hub.relocations["dev_B2C8"].updated_at == 50
    assert hub.lanes["lane_001"].state == "paused_relocation"
    assert "lane_001" in hub.flow_controls


def test_invalid_move_contract_keeps_old_attachment_and_paused_lane():
    registry_hub = RegistryHub(hub_id="registry_home", scope_path="global.family.home")
    traffic_hub = TrafficHub(hub_id="hub_1")
    device = Device(device_id="dev_A9F3", label="phone")
    register_device(registry_hub, device)
    attach_device(traffic_hub, Device(device_id="dev_SRC", label="source"))
    attach_device(traffic_hub, device)
    open_lane(traffic_hub, "dev_SRC", "dev_A9F3", lane_id="lane_001")
    mark_in_transit(registry_hub, "dev_A9F3", current_time=10)
    pause_lanes_for_relocation(traffic_hub, "dev_A9F3")
    contract = create_move_contract(
        device_id="dev_A9F3",
        passport_id="passport_dev_A9F3",
        from_scope="global.family.home",
        to_scope="global.family.office",
        old_attachment="registry_home",
        new_attachment="registry_office",
        valid=False,
        timestamp=11,
    )

    result = update_attachment_after_move(
        registry_hub,
        "dev_A9F3",
        new_attachment="registry_office",
        new_scope="global.family.office",
        move_contract=contract,
    )

    assert result.action == "move_contract_rejected"
    assert result.reason == "invalid_move_contract"
    assert registry_hub.devices["dev_A9F3"].current_attachment == "registry_home"
    assert registry_hub.attachments["dev_A9F3"].current_attachment == "registry_home"
    assert "dev_A9F3" not in registry_hub.moves
    assert traffic_hub.lanes["lane_001"].state == "paused_relocation"


def test_duplicate_claim_during_relocation_preserves_original_attachment():
    hub = RegistryHub(hub_id="registry_home", scope_path="global.family.home")
    device = Device(device_id="dev_A9F3", label="phone")
    register_device(hub, device)
    mark_in_transit(hub, "dev_A9F3", current_time=10)

    result = detect_duplicate_device_claim(
        hub,
        "dev_A9F3",
        claiming_attachment_id="registry_office",
        current_time=11,
    )

    assert result.action == "duplicate_device_id_conflict"
    assert result.conflict_id in hub.conflicts
    assert hub.devices["dev_A9F3"].current_attachment == "registry_home"
    assert hub.attachments["dev_A9F3"].current_attachment == "registry_home"
    assert hub.relocations["dev_A9F3"].state == "in_transit"


def test_unreachable_resume_keeps_flow_control():
    hub_1, hub_2 = TrafficHub(hub_id="hub_1"), TrafficHub(hub_id="hub_2")
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
    assert hub_1.flow_controls["lane_001"].hold_new_packets is True
    assert hub_1.lanes["lane_001"].state == "awaiting_verification"


def test_paused_send_scenario_asserts_no_sequence_increment():
    hub = TrafficHub(hub_id="hub_1")
    attach_device(hub, Device(device_id="dev_A9F3", label="source"))
    attach_device(hub, Device(device_id="dev_B2C8", label="target"))
    open_lane(hub, "dev_A9F3", "dev_B2C8", lane_id="lane_001")
    send_lane_data(hub, "lane_001", {"message": "first"})
    pause_lanes_for_relocation(hub, "dev_B2C8")

    result = send_lane_data(hub, "lane_001", {"message": "second"})

    assert result.action == "lane_paused_relocation"
    assert hub.lanes["lane_001"].last_sent_sequence == 1
    assert hub.lanes["lane_001"].last_acknowledged_sequence == 1


def test_source_device_relocation_pauses_and_resumes_lane():
    hub_1 = TrafficHub(hub_id="hub_1")
    hub_2 = TrafficHub(hub_id="hub_2")
    hub_3 = TrafficHub(hub_id="hub_3")
    hub_4 = TrafficHub(hub_id="hub_4")
    hubs = {hub.hub_id: hub for hub in [hub_1, hub_2, hub_3, hub_4]}
    connect_neighbor(hub_1, hub_2)
    connect_neighbor(hub_2, hub_3)
    connect_neighbor(hub_2, hub_4)
    source = Device(device_id="dev_A9F3", label="source")
    attach_device(hub_1, source)
    attach_device(hub_3, Device(device_id="dev_B2C8", label="target"))
    open_lane(hub_1, "dev_A9F3", "dev_B2C8", hubs, lane_id="lane_001")
    send_lane_data(hub_1, "lane_001", {"message": "first"}, hubs)

    pause_result = pause_lanes_for_relocation(hub_1, "dev_A9F3")
    detach_device(hub_1, "dev_A9F3")
    attach_device(hub_4, source)
    resume_result = resume_lanes_after_relocation(hub_1, "dev_A9F3", all_hubs=hubs)

    assert pause_result.action == "lanes_paused"
    assert resume_result.action == "lanes_resumed"
    assert hub_1.lanes["lane_001"].state == "active"
    assert hub_1.lanes["lane_001"].current_route == ["hub_1", "hub_2", "hub_3"]
    assert hub_1.lanes["lane_001"].last_sent_sequence == 1
    assert hub_1.lanes["lane_001"].last_acknowledged_sequence == 1
    assert "lane_001" not in hub_1.flow_controls
