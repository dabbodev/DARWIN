from darwin.models.checkpoint import make_checkpoint_packet
from darwin.models.device import Device
from darwin.models.hub import RegistryHub, TrafficHub
from darwin.models.packet import DarwinPacket
from darwin.models.passport import PassportRecord
from darwin.registry.checkpoints import record_checkpoint
from darwin.registry.operations import register_device
from darwin.registry.security import detect_duplicate_device_claim, verify_rolling_proof
from darwin.traffic.lanes import open_lane, send_lane_data
from darwin.traffic.routing import attach_device, forward_packet


def make_registry_hub() -> RegistryHub:
    return RegistryHub(hub_id="hub_home_001", scope_path="global.family.david.home")


def make_passport(
    device_id: str,
    valid: bool = True,
    revoked: bool = False,
    issuer_trusted: bool = True,
) -> PassportRecord:
    return PassportRecord(
        passport_id=f"passport_{device_id}",
        device_id=device_id,
        issued_by="issuer_symbolic",
        issued_scope="global.family.david.home",
        valid=valid,
        revoked=revoked,
        issuer_trusted=issuer_trusted,
    )


def test_invalid_passport_registration_rejected():
    hub = make_registry_hub()
    device = Device(device_id="dev_A9F3", label="phone")
    passport = make_passport("dev_A9F3", valid=False)

    result = register_device(hub, device, passport=passport)

    assert not result.success
    assert result.action == "registration_rejected"
    assert result.reason == "invalid_passport"
    assert "dev_A9F3" not in hub.devices
    assert "passport_dev_A9F3" not in hub.passports
    assert hub.security_events[-1].event_type == "passport_verification_failed"


def test_revoked_passport_registration_rejected():
    hub = make_registry_hub()
    device = Device(device_id="dev_A9F3", label="phone")
    passport = make_passport("dev_A9F3", revoked=True)

    result = register_device(hub, device, passport=passport)

    assert not result.success
    assert result.reason == "revoked_passport"
    assert "dev_A9F3" not in hub.devices
    assert hub.security_events[-1].event_type == "revoked_passport_presented"


def test_failed_rolling_proof_quarantines_device():
    hub = make_registry_hub()
    device = Device(device_id="dev_A9F3", label="phone")
    register_device(hub, device, checkpoint_tier=2)
    record_checkpoint(hub, make_checkpoint_packet(device, hub.hub_id, "online", current_time=10))

    result = verify_rolling_proof(hub, "dev_A9F3", proof_valid=False, current_time=11)

    assert not result.success
    assert result.action == "quarantined"
    assert "dev_A9F3" in hub.quarantines
    assert hub.devices["dev_A9F3"].current_state == "quarantined"
    assert hub.checkpoints["dev_A9F3"].state == "quarantined"
    assert hub.security_events[-1].event_type == "rolling_proof_failed"


def test_valid_rolling_proof_keeps_device_active():
    hub = make_registry_hub()
    device = Device(device_id="dev_A9F3", label="phone")
    register_device(hub, device)

    result = verify_rolling_proof(hub, "dev_A9F3", proof_valid=True)

    assert result.success
    assert result.action == "rolling_proof_verified"
    assert "dev_A9F3" not in hub.quarantines
    assert hub.devices["dev_A9F3"].current_state != "quarantined"


def test_bad_packet_auth_is_not_delivered():
    hub = TrafficHub(hub_id="hub_home_001")
    attach_device(hub, Device(device_id="dev_A9F3", label="source"))
    attach_device(hub, Device(device_id="dev_B2C8", label="target"))
    packet = DarwinPacket(
        packet_id="pkt_bad_auth",
        packet_class="traffic",
        packet_type="message",
        source_device_id="dev_A9F3",
        target_device_id="dev_B2C8",
        auth_tag_valid=False,
    )

    result = forward_packet(hub, packet)

    assert result.action == "invalid_auth_tag"
    assert result.action != "delivered"
    assert hub.forwarding_log[-1].action == "invalid_auth_tag"
    assert hub.security_events[-1].event_type == "packet_auth_failed"


def test_send_lane_data_with_bad_auth_fails_cleanly():
    hub = TrafficHub(hub_id="hub_home_001")
    attach_device(hub, Device(device_id="dev_A9F3", label="source"))
    attach_device(hub, Device(device_id="dev_B2C8", label="target"))
    open_lane(hub, "dev_A9F3", "dev_B2C8", lane_id="lane_001")

    result = send_lane_data(
        hub,
        "lane_001",
        {"message": "bad auth"},
        auth_tag_valid=False,
    )

    assert result.action == "invalid_auth_tag"
    assert hub.lanes["lane_001"].last_sent_sequence == 0
    assert hub.lanes["lane_001"].last_acknowledged_sequence == 0
    assert hub.security_events[-1].event_type == "packet_auth_failed"


def test_duplicate_device_id_conflict_does_not_overwrite_attachment():
    hub = make_registry_hub()
    device = Device(device_id="dev_A9F3", label="phone")
    register_device(hub, device)

    result = detect_duplicate_device_claim(
        hub,
        "dev_A9F3",
        claiming_attachment_id="hub_office_007",
    )

    assert result.action == "duplicate_device_id_conflict"
    assert result.conflict_id in hub.conflicts
    assert hub.devices["dev_A9F3"].current_attachment == "hub_home_001"
    assert result.existing_attachment == "hub_home_001"
    assert result.claiming_attachment == "hub_office_007"
