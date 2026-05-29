from darwin.models.checkpoint import checkpoint_interval_for_tier, make_checkpoint_packet
from darwin.models.device import Device
from darwin.models.hub import RegistryHub
from darwin.registry.checkpoints import (
    detect_checkpoint_timeouts,
    get_checkpoint_state,
    record_checkpoint,
)
from darwin.registry.operations import register_device


def make_home_hub() -> RegistryHub:
    return RegistryHub(hub_id="hub_home_001", scope_path="global.family.david.home")


def test_record_checkpoint_updates_registry_state():
    hub = make_home_hub()
    device = Device(device_id="dev_A9F3", label="phone")
    register_device(hub, device, checkpoint_tier=2)
    packet = make_checkpoint_packet(device, hub.hub_id, "online", current_time=10)

    result = record_checkpoint(hub, packet)
    checkpoint = get_checkpoint_state(hub, "dev_A9F3")

    assert result.accepted
    assert "dev_A9F3" in hub.checkpoints
    assert checkpoint is not None
    assert checkpoint.state == "online"
    assert hub.devices["dev_A9F3"].current_state == "online"
    assert checkpoint.expected_next_checkpoint_at == 15


def test_checkpoint_tier_intervals():
    assert checkpoint_interval_for_tier(0) == 1800
    assert checkpoint_interval_for_tier(1) == 30
    assert checkpoint_interval_for_tier(2) == 5
    assert checkpoint_interval_for_tier(3) == 1
    assert checkpoint_interval_for_tier(0) > checkpoint_interval_for_tier(1)
    assert checkpoint_interval_for_tier(1) > checkpoint_interval_for_tier(2)
    assert checkpoint_interval_for_tier(2) > checkpoint_interval_for_tier(3)


def test_invalid_checkpoint_auth_does_not_update_state():
    hub = make_home_hub()
    device = Device(device_id="dev_A9F3", label="phone")
    register_device(hub, device, checkpoint_tier=2)
    record_checkpoint(hub, make_checkpoint_packet(device, hub.hub_id, "online", current_time=0))
    invalid_packet = make_checkpoint_packet(
        device,
        hub.hub_id,
        "active",
        current_time=1,
        auth_tag_valid=False,
    )

    result = record_checkpoint(hub, invalid_packet)
    checkpoint = get_checkpoint_state(hub, "dev_A9F3")

    assert not result.accepted
    assert result.reason == "invalid_auth_tag"
    assert checkpoint is not None
    assert checkpoint.state == "online"
    assert hub.devices["dev_A9F3"].current_state == "online"


def test_checkpoint_timeout_marks_device_timed_out():
    hub = make_home_hub()
    device = Device(device_id="dev_A9F3", label="phone")
    register_device(hub, device, checkpoint_tier=2)
    record_checkpoint(hub, make_checkpoint_packet(device, hub.hub_id, "online", current_time=0))

    results = detect_checkpoint_timeouts(hub, current_time=7)
    checkpoint = get_checkpoint_state(hub, "dev_A9F3")

    assert len(results) == 1
    assert results[0].action == "checkpoint_timed_out"
    assert checkpoint is not None
    assert checkpoint.state == "timed_out"
    assert hub.devices["dev_A9F3"].current_state == "timed_out"


def test_tier_zero_sparse_device_does_not_timeout_too_soon():
    hub = make_home_hub()
    device = Device(device_id="dev_SENSOR", label="sensor", checkpoint_tier=0)
    register_device(hub, device, checkpoint_tier=0)
    record_checkpoint(hub, make_checkpoint_packet(device, hub.hub_id, "idle", current_time=0))

    results = detect_checkpoint_timeouts(hub, current_time=1799)
    checkpoint = get_checkpoint_state(hub, "dev_SENSOR")

    assert len(results) == 1
    assert results[0].action == "checkpoint_ok"
    assert checkpoint is not None
    assert checkpoint.state == "idle"


def test_unknown_device_checkpoint_returns_clean_failure():
    hub = make_home_hub()
    packet = make_checkpoint_packet("dev_UNKNOWN", hub.hub_id, "online", current_time=0)

    result = record_checkpoint(hub, packet)

    assert not result.accepted
    assert result.reason == "unknown_device"
    assert get_checkpoint_state(hub, "dev_UNKNOWN") is None


def test_checkpoint_packet_can_include_optional_metadata():
    hub = make_home_hub()
    device = Device(device_id="dev_A9F3", label="phone")
    register_device(hub, device, checkpoint_tier=2)
    packet = make_checkpoint_packet(
        device,
        hub.hub_id,
        "active",
        current_time=10,
        active_lane_count=3,
        battery_level=91,
    )

    record_checkpoint(hub, packet)
    checkpoint = get_checkpoint_state(hub, "dev_A9F3")

    assert checkpoint is not None
    assert checkpoint.active_lane_count == 3
    assert checkpoint.battery_level == 91
