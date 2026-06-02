from pathlib import Path

from darwin.auth.hmac_bridge import (
    checkpoint_auth_material,
    compute_hmac_tag,
    rolling_proof_material,
)
from darwin.auth.modes import AUTH_MODE_HMAC_SHA256_EXPERIMENTAL, AUTH_MODE_SYMBOLIC
from darwin.models.checkpoint import make_checkpoint_packet
from darwin.models.device import Device
from darwin.models.hub import RegistryHub
from darwin.models.packet import DarwinPacket
from darwin.registry.checkpoints import get_checkpoint_state, record_checkpoint
from darwin.registry.operations import register_device
from darwin.registry.security import quarantine_device, revoke_device, verify_rolling_proof
from darwin.registry.sessions import (
    create_local_session,
    revoke_device_sessions,
    revoke_local_session,
    verify_hmac_rolling_proof_for_session,
)
from darwin.sim.runner import run_scenario
from darwin.sim.scenarios import validate_scenario_file

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEST_SECRET = "test_secret_simulator_only"


def _registered_hub() -> RegistryHub:
    hub = RegistryHub(hub_id="hub_home_001", scope_path="global.family.home")
    register_device(hub, Device(device_id="dev_A9F3", label="phone"), checkpoint_tier=2)
    return hub


def _proof(
    hub: RegistryHub,
    session_id: str,
    counter: int = 1,
    nonce: str = "nonce_001",
    capability: str = "send_normal_traffic",
) -> str:
    session = hub.local_sessions[session_id]
    return compute_hmac_tag(
        session.secret,
        rolling_proof_material(
            device_id=session.device_id,
            hub_id=hub.hub_id,
            session_id=session_id,
            counter=counter,
            nonce=nonce,
            capability=capability,
        ),
    )


def _valid_hmac_checkpoint(hub: RegistryHub, device: Device, state: str = "online"):
    packet = make_checkpoint_packet(
        device,
        hub.hub_id,
        state,
        current_time=10,
        auth_mode=AUTH_MODE_HMAC_SHA256_EXPERIMENTAL,
    )
    packet.auth_tag = compute_hmac_tag(TEST_SECRET, checkpoint_auth_material(packet))
    return packet


def test_revoke_local_session_blocks_hmac_proof():
    hub = _registered_hub()
    create_local_session(hub, "dev_A9F3", TEST_SECRET, session_id="session_001")
    revoke_result = revoke_local_session(hub, "session_001", reason="test_revocation")
    proof = _proof(hub, "session_001")

    result = verify_hmac_rolling_proof_for_session(
        hub,
        "session_001",
        1,
        "nonce_001",
        "send_normal_traffic",
        proof,
    )

    assert revoke_result.success
    assert not result.success
    assert result.reason == "session_revoked"
    assert hub.local_sessions["session_001"].state == "revoked"


def test_revoke_device_sessions_blocks_all_device_sessions():
    hub = _registered_hub()
    create_local_session(hub, "dev_A9F3", TEST_SECRET, session_id="session_001")
    create_local_session(hub, "dev_A9F3", TEST_SECRET, session_id="session_002")
    proof_1 = _proof(hub, "session_001")
    proof_2 = _proof(hub, "session_002")

    results = revoke_device_sessions(hub, "dev_A9F3", reason="device_test_revocation")
    verify_1 = verify_hmac_rolling_proof_for_session(
        hub,
        "session_001",
        1,
        "nonce_001",
        "send_normal_traffic",
        proof_1,
    )
    verify_2 = verify_hmac_rolling_proof_for_session(
        hub,
        "session_002",
        1,
        "nonce_001",
        "send_normal_traffic",
        proof_2,
    )

    assert [result.session.session_id for result in results if result.session] == [
        "session_001",
        "session_002",
    ]
    assert hub.local_sessions["session_001"].state == "revoked"
    assert hub.local_sessions["session_002"].state == "revoked"
    assert not verify_1.success
    assert verify_1.reason == "session_revoked"
    assert not verify_2.success
    assert verify_2.reason == "session_revoked"


def test_quarantine_device_marks_sessions_quarantined():
    hub = _registered_hub()
    create_local_session(hub, "dev_A9F3", TEST_SECRET, session_id="session_001")
    proof = _proof(hub, "session_001")

    quarantine_result = verify_rolling_proof(hub, "dev_A9F3", proof_valid=False)
    verify_result = verify_hmac_rolling_proof_for_session(
        hub,
        "session_001",
        1,
        "nonce_001",
        "send_normal_traffic",
        proof,
    )

    assert not quarantine_result.success
    assert quarantine_result.action == "quarantined"
    assert hub.devices["dev_A9F3"].current_state == "quarantined"
    assert hub.local_sessions["session_001"].state == "quarantined"
    assert not verify_result.success
    assert verify_result.reason == "device_quarantined"


def test_hmac_checkpoint_from_quarantined_device_rejected():
    hub = _registered_hub()
    device = Device(device_id="dev_A9F3", label="phone", checkpoint_tier=2)
    quarantine_device(hub, "dev_A9F3", reason="test_quarantine")
    packet = _valid_hmac_checkpoint(hub, device, state="online")

    result = record_checkpoint(hub, packet, auth_secret=TEST_SECRET)

    assert not result.accepted
    assert result.reason == "device_quarantined"
    assert get_checkpoint_state(hub, "dev_A9F3") is None
    assert hub.devices["dev_A9F3"].current_state == "quarantined"


def test_hmac_checkpoint_from_revoked_device_rejected():
    hub = _registered_hub()
    device = Device(device_id="dev_A9F3", label="phone", checkpoint_tier=2)
    revoke_device(hub, "dev_A9F3", reason="test_revocation")
    packet = _valid_hmac_checkpoint(hub, device, state="online")

    result = record_checkpoint(hub, packet, auth_secret=TEST_SECRET)

    assert not result.accepted
    assert result.reason == "device_revoked"
    assert get_checkpoint_state(hub, "dev_A9F3") is None
    assert hub.devices["dev_A9F3"].current_state == "revoked"


def test_hmac_rolling_proof_from_revoked_device_does_not_quarantine():
    hub = _registered_hub()
    create_local_session(hub, "dev_A9F3", TEST_SECRET, session_id="session_001")
    revoke_device(hub, "dev_A9F3", reason="device_test_revocation")

    result = verify_rolling_proof(
        hub,
        "dev_A9F3",
        proof_valid=True,
        auth_mode=AUTH_MODE_HMAC_SHA256_EXPERIMENTAL,
        session_id="session_001",
        counter=1,
        nonce="nonce_001",
        capability="send_normal_traffic",
        auth_tag="unused_after_revocation_guard",
    )

    assert not result.success
    assert result.reason == "device_revoked"
    assert hub.devices["dev_A9F3"].current_state == "revoked"
    assert "dev_A9F3" not in hub.quarantines
    assert hub.local_sessions["session_001"].state == "revoked"


def test_symbolic_auth_still_default_after_revocation_changes():
    device = Device(device_id="dev_A9F3", label="phone")
    packet = DarwinPacket(
        packet_id="pkt_001",
        packet_class="DATA",
        packet_type="data_payload",
    )
    checkpoint = make_checkpoint_packet(device, "hub_home_001", "online", current_time=0)

    assert packet.auth_mode == AUTH_MODE_SYMBOLIC
    assert checkpoint.auth_mode == AUTH_MODE_SYMBOLIC


def test_hmac_revocation_scenarios_validate_and_run():
    for filename in (
        "019_hmac_revoked_session_failure.yaml",
        "020_hmac_quarantine_blocks_checkpoint.yaml",
    ):
        scenario_path = PROJECT_ROOT / "scenarios" / filename

        validation = validate_scenario_file(scenario_path)
        result = run_scenario(scenario_path)

        assert validation.passed
        assert result.passed
