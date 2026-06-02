from darwin.auth.hmac_bridge import (
    checkpoint_auth_material,
    compute_hmac_tag,
    packet_auth_material,
    rolling_proof_material,
    verify_hmac_tag,
    verify_rolling_proof_tag,
)
from darwin.auth.modes import AUTH_MODE_HMAC_SHA256_EXPERIMENTAL, AUTH_MODE_SYMBOLIC
from darwin.models.checkpoint import make_checkpoint_packet
from darwin.models.device import Device
from darwin.models.hub import RegistryHub, TrafficHub
from darwin.models.packet import DarwinPacket
from darwin.registry.checkpoints import get_checkpoint_state, record_checkpoint
from darwin.registry.operations import register_device
from darwin.traffic.lanes import open_lane, send_lane_data
from darwin.traffic.routing import attach_device

TEST_SECRET = "test_secret_simulator_only"
OTHER_SECRET = "other_test_secret_simulator_only"


def test_hmac_wrong_secret_fails():
    material = {"packet_id": "pkt_001", "payload": {"message": "hello"}}
    tag = compute_hmac_tag(TEST_SECRET, material)

    assert not verify_hmac_tag(OTHER_SECRET, material, tag)


def test_hmac_tampered_payload_fails():
    packet = DarwinPacket(
        packet_id="pkt_001",
        packet_class="DATA",
        packet_type="data_payload",
        source_device_id="dev_A9F3",
        target_device_id="dev_B2C8",
        source_hub_id="hub_home_001",
        payload={"message": "original"},
        auth_mode=AUTH_MODE_HMAC_SHA256_EXPERIMENTAL,
    )
    tag = compute_hmac_tag(TEST_SECRET, packet_auth_material(packet))

    packet.payload = {"message": "tampered"}

    assert not verify_hmac_tag(TEST_SECRET, packet_auth_material(packet), tag)


def test_checkpoint_hmac_tamper_does_not_update_state():
    hub = RegistryHub(hub_id="hub_home_001", scope_path="global.family.home")
    device = Device(device_id="dev_A9F3", label="phone")
    register_device(hub, device, checkpoint_tier=2)
    valid_packet = make_checkpoint_packet(
        device,
        hub.hub_id,
        "online",
        current_time=0,
        auth_mode=AUTH_MODE_HMAC_SHA256_EXPERIMENTAL,
    )
    valid_packet.auth_tag = compute_hmac_tag(
        TEST_SECRET,
        checkpoint_auth_material(valid_packet),
    )
    record_checkpoint(hub, valid_packet, auth_secret=TEST_SECRET)

    tampered_packet = make_checkpoint_packet(
        device,
        hub.hub_id,
        "active",
        current_time=1,
        auth_mode=AUTH_MODE_HMAC_SHA256_EXPERIMENTAL,
    )
    tampered_packet.auth_tag = compute_hmac_tag(
        TEST_SECRET,
        checkpoint_auth_material(tampered_packet),
    )
    tampered_packet.payload["device_state"] = "quarantined"

    result = record_checkpoint(hub, tampered_packet, auth_secret=TEST_SECRET)
    checkpoint = get_checkpoint_state(hub, "dev_A9F3")

    assert not result.accepted
    assert result.reason == "invalid_auth_tag"
    assert checkpoint is not None
    assert checkpoint.state == "online"
    assert hub.devices["dev_A9F3"].current_state == "online"


def test_packet_hmac_missing_secret_fails_cleanly():
    hub = TrafficHub(hub_id="hub_home_001")
    attach_device(hub, Device(device_id="dev_A9F3", label="source"))
    attach_device(hub, Device(device_id="dev_B2C8", label="target"))
    open_lane(hub, "dev_A9F3", "dev_B2C8", lane_id="lane_001")

    result = send_lane_data(
        hub,
        "lane_001",
        {"message": "missing secret"},
        auth_mode=AUTH_MODE_HMAC_SHA256_EXPERIMENTAL,
    )

    assert result.action == "invalid_auth_tag"
    assert hub.lanes["lane_001"].last_sent_sequence == 0
    assert hub.lanes["lane_001"].last_acknowledged_sequence == 0
    assert hub.forwarding_log[-1].action == "invalid_auth_tag"


def test_rolling_proof_wrong_nonce_fails():
    material = rolling_proof_material(
        device_id="dev_A9F3",
        hub_id="hub_home_001",
        session_id="session_001",
        counter=1,
        nonce="nonce_a",
        capability="send_normal_traffic",
    )
    tag = compute_hmac_tag(TEST_SECRET, material)

    result = verify_rolling_proof_tag(
        TEST_SECRET,
        device_id="dev_A9F3",
        hub_id="hub_home_001",
        session_id="session_001",
        counter=1,
        nonce="nonce_b",
        capability="send_normal_traffic",
        expected_tag=tag,
    )

    assert not result.success
    assert result.reason == "invalid_auth_tag"


def test_rolling_proof_wrong_counter_fails():
    material = rolling_proof_material(
        device_id="dev_A9F3",
        hub_id="hub_home_001",
        session_id="session_001",
        counter=1,
        nonce="nonce_001",
        capability="send_normal_traffic",
    )
    tag = compute_hmac_tag(TEST_SECRET, material)

    result = verify_rolling_proof_tag(
        TEST_SECRET,
        device_id="dev_A9F3",
        hub_id="hub_home_001",
        session_id="session_001",
        counter=2,
        nonce="nonce_001",
        capability="send_normal_traffic",
        expected_tag=tag,
    )

    assert not result.success
    assert result.reason == "invalid_auth_tag"


def test_symbolic_auth_default_still_symbolic():
    device = Device(device_id="dev_A9F3", label="phone")
    packet = DarwinPacket(
        packet_id="pkt_001",
        packet_class="DATA",
        packet_type="data_payload",
    )
    checkpoint = make_checkpoint_packet(device, "hub_home_001", "online", current_time=0)

    assert packet.auth_mode == AUTH_MODE_SYMBOLIC
    assert checkpoint.auth_mode == AUTH_MODE_SYMBOLIC


def test_quarantined_source_with_valid_hmac_is_still_blocked():
    hub = TrafficHub(hub_id="hub_home_001")
    attach_device(hub, Device(device_id="dev_A9F3", label="source"))
    attach_device(hub, Device(device_id="dev_B2C8", label="target"))
    open_lane(hub, "dev_A9F3", "dev_B2C8", lane_id="lane_001")
    hub.direct_attachments["dev_A9F3"].status = "quarantined"

    result = send_lane_data(
        hub,
        "lane_001",
        {"message": "valid hmac from quarantined source"},
        auth_mode=AUTH_MODE_HMAC_SHA256_EXPERIMENTAL,
        auth_secret=TEST_SECRET,
    )

    assert result.action == "source_quarantined"
    assert hub.lanes["lane_001"].last_sent_sequence == 0
    assert hub.forwarding_log[-1].action == "source_quarantined"
