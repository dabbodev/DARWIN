from pathlib import Path

from darwin.auth.hmac_bridge import (
    canonical_json,
    checkpoint_auth_material,
    compute_hmac_tag,
    packet_auth_material,
    rolling_proof_material,
    verify_hmac_tag,
    verify_rolling_proof_tag,
)
from darwin.auth.modes import AUTH_MODE_HMAC_SHA256_EXPERIMENTAL
from darwin.models.checkpoint import make_checkpoint_packet
from darwin.models.device import Device
from darwin.models.hub import RegistryHub, TrafficHub
from darwin.models.packet import DarwinPacket
from darwin.registry.checkpoints import get_checkpoint_state, record_checkpoint
from darwin.registry.operations import register_device
from darwin.sim.runner import run_scenario
from darwin.sim.scenarios import validate_scenario_file
from darwin.traffic.lanes import open_lane, send_lane_data
from darwin.traffic.routing import attach_device
from darwin.traffic.security import verify_packet_auth

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEST_SECRET = "test_secret_simulator_only"


def test_canonical_json_is_deterministic():
    left = {"device": "dev_A9F3", "payload": {"b": 2, "a": 1}}
    right = {"payload": {"a": 1, "b": 2}, "device": "dev_A9F3"}

    assert canonical_json(left) == canonical_json(right)


def test_compute_and_verify_hmac_tag_success():
    material = {"packet_id": "pkt_001", "payload": {"message": "hello"}}

    tag = compute_hmac_tag(TEST_SECRET, material)

    assert verify_hmac_tag(TEST_SECRET, material, tag)


def test_verify_hmac_tag_failure():
    material = {"packet_id": "pkt_001", "payload": {"message": "hello"}}
    tag = compute_hmac_tag(TEST_SECRET, material)

    assert not verify_hmac_tag("wrong_test_secret", material, tag)
    assert not verify_hmac_tag(TEST_SECRET, material, "0" * 64)


def test_packet_hmac_auth_success():
    hub = TrafficHub(hub_id="hub_home_001")
    packet = DarwinPacket(
        packet_id="pkt_001",
        packet_class="DATA",
        packet_type="data_payload",
        source_device_id="dev_A9F3",
        target_device_id="dev_B2C8",
        source_hub_id=hub.hub_id,
        payload={"message": "hello"},
        auth_mode=AUTH_MODE_HMAC_SHA256_EXPERIMENTAL,
    )
    packet.auth_tag = compute_hmac_tag(TEST_SECRET, packet_auth_material(packet))

    result = verify_packet_auth(hub, packet, auth_secret=TEST_SECRET)

    assert result.success
    assert result.action == "packet_auth_verified"


def test_packet_hmac_auth_failure_blocks_delivery():
    hub = TrafficHub(hub_id="hub_home_001")
    attach_device(hub, Device(device_id="dev_A9F3", label="source"))
    attach_device(hub, Device(device_id="dev_B2C8", label="target"))
    open_lane(hub, "dev_A9F3", "dev_B2C8", lane_id="lane_001")

    result = send_lane_data(
        hub,
        "lane_001",
        {"message": "bad auth"},
        auth_mode=AUTH_MODE_HMAC_SHA256_EXPERIMENTAL,
        auth_secret=TEST_SECRET,
        tamper_auth_tag=True,
    )

    assert result.action == "invalid_auth_tag"
    assert hub.lanes["lane_001"].last_sent_sequence == 0
    assert hub.lanes["lane_001"].last_acknowledged_sequence == 0
    assert hub.forwarding_log[-1].action == "invalid_auth_tag"


def test_checkpoint_hmac_auth_success_updates_state():
    hub = RegistryHub(hub_id="hub_home_001", scope_path="global.family.home")
    device = Device(device_id="dev_A9F3", label="phone")
    register_device(hub, device, checkpoint_tier=2)
    packet = make_checkpoint_packet(
        device,
        hub.hub_id,
        "online",
        current_time=10,
        auth_mode=AUTH_MODE_HMAC_SHA256_EXPERIMENTAL,
    )
    packet.auth_tag = compute_hmac_tag(TEST_SECRET, checkpoint_auth_material(packet))

    result = record_checkpoint(hub, packet, auth_secret=TEST_SECRET)
    checkpoint = get_checkpoint_state(hub, "dev_A9F3")

    assert result.accepted
    assert checkpoint is not None
    assert checkpoint.state == "online"


def test_checkpoint_hmac_auth_failure_does_not_update_state():
    hub = RegistryHub(hub_id="hub_home_001", scope_path="global.family.home")
    device = Device(device_id="dev_A9F3", label="phone")
    register_device(hub, device, checkpoint_tier=2)
    valid_packet = make_checkpoint_packet(device, hub.hub_id, "online", current_time=0)
    record_checkpoint(hub, valid_packet)
    invalid_packet = make_checkpoint_packet(
        device,
        hub.hub_id,
        "active",
        current_time=1,
        auth_mode=AUTH_MODE_HMAC_SHA256_EXPERIMENTAL,
        auth_tag="0" * 64,
    )

    result = record_checkpoint(hub, invalid_packet, auth_secret=TEST_SECRET)
    checkpoint = get_checkpoint_state(hub, "dev_A9F3")

    assert not result.accepted
    assert result.reason == "invalid_auth_tag"
    assert checkpoint is not None
    assert checkpoint.state == "online"
    assert hub.devices["dev_A9F3"].current_state == "online"


def test_rolling_proof_hmac_success():
    material = rolling_proof_material(
        device_id="dev_A9F3",
        hub_id="hub_home_001",
        session_id="session_001",
        counter=7,
        nonce="nonce_001",
        capability="send_normal_traffic",
    )
    tag = compute_hmac_tag(TEST_SECRET, material)

    result = verify_rolling_proof_tag(
        TEST_SECRET,
        device_id="dev_A9F3",
        hub_id="hub_home_001",
        session_id="session_001",
        counter=7,
        nonce="nonce_001",
        capability="send_normal_traffic",
        expected_tag=tag,
    )

    assert result.success


def test_rolling_proof_hmac_failure():
    material = rolling_proof_material(
        device_id="dev_A9F3",
        hub_id="hub_home_001",
        session_id="session_001",
        counter=7,
        nonce="nonce_001",
        capability="send_normal_traffic",
    )
    tag = compute_hmac_tag(TEST_SECRET, material)

    result = verify_rolling_proof_tag(
        TEST_SECRET,
        device_id="dev_A9F3",
        hub_id="hub_home_001",
        session_id="session_001",
        counter=8,
        nonce="nonce_001",
        capability="send_normal_traffic",
        expected_tag=tag,
    )

    assert not result.success
    assert result.reason == "invalid_auth_tag"


def test_symbolic_auth_existing_behavior_unchanged():
    hub = TrafficHub(hub_id="hub_home_001")
    packet = DarwinPacket(
        packet_id="pkt_001",
        packet_class="DATA",
        packet_type="data_payload",
        source_device_id="dev_A9F3",
        auth_tag_valid=False,
    )

    result = verify_packet_auth(hub, packet)

    assert not result.success
    assert result.action == "invalid_auth_tag"
    assert result.reason == "invalid_auth_tag"


def test_hmac_scenarios_validate_and_run():
    scenario_paths = [
        PROJECT_ROOT / "scenarios" / "012_hmac_checkpoint_success.yaml",
        PROJECT_ROOT / "scenarios" / "013_hmac_packet_auth_failure.yaml",
    ]

    for scenario_path in scenario_paths:
        validation = validate_scenario_file(scenario_path)
        result = run_scenario(scenario_path)

        assert validation.passed
        assert result.passed
