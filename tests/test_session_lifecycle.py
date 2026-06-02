from pathlib import Path

from darwin.auth.hmac_bridge import compute_hmac_tag, rolling_proof_material
from darwin.models.checkpoint import make_checkpoint_packet
from darwin.models.device import Device
from darwin.models.hub import RegistryHub, TrafficHub
from darwin.models.packet import DarwinPacket
from darwin.registry.checkpoints import record_checkpoint
from darwin.registry.operations import register_device
from darwin.registry.security import verify_rolling_proof
from darwin.registry.sessions import (
    create_local_session,
    expire_local_sessions,
    rotate_local_session,
    verify_hmac_rolling_proof_for_session,
)
from darwin.sim.runner import run_scenario
from darwin.sim.scenarios import validate_scenario_file
from darwin.traffic.security import verify_packet_auth

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OLD_SECRET = "old_test_secret_simulator_only"
NEW_SECRET = "new_test_secret_simulator_only"


def _registered_hub() -> RegistryHub:
    hub = RegistryHub(hub_id="hub_home_001", scope_path="global.family.home")
    register_device(hub, Device(device_id="dev_A9F3", label="phone"))
    return hub


def _proof(
    hub: RegistryHub,
    session_id: str,
    counter: int,
    nonce: str,
    capability: str,
    secret: str,
) -> str:
    session = hub.local_sessions[session_id]
    return compute_hmac_tag(
        secret,
        rolling_proof_material(
            device_id=session.device_id,
            hub_id=hub.hub_id,
            session_id=session_id,
            counter=counter,
            nonce=nonce,
            capability=capability,
        ),
    )


def test_create_local_session_for_registered_device():
    hub = _registered_hub()

    result = create_local_session(
        hub,
        "dev_A9F3",
        OLD_SECRET,
        session_id="session_001",
        current_time=10,
        ttl=5,
    )

    assert result.success
    assert result.status == "session_created"
    assert "session_001" in hub.local_sessions
    session = hub.local_sessions["session_001"]
    assert session.device_id == "dev_A9F3"
    assert session.hub_id == hub.hub_id
    assert session.scope == hub.scope_path
    assert session.secret == OLD_SECRET
    assert session.current_counter == 0
    assert session.created_at == 10
    assert session.expires_at == 15
    assert session.state == "active"


def test_create_local_session_unknown_device_fails():
    hub = RegistryHub(hub_id="hub_home_001", scope_path="global.family.home")

    result = create_local_session(hub, "dev_missing", OLD_SECRET, session_id="session_001")

    assert not result.success
    assert result.reason == "unknown_device"
    assert hub.local_sessions == {}


def test_session_expiration_blocks_verification():
    hub = _registered_hub()
    create_local_session(
        hub,
        "dev_A9F3",
        OLD_SECRET,
        session_id="session_001",
        current_time=1,
        ttl=3,
    )
    expire_local_sessions(hub, current_time=4)
    proof = _proof(hub, "session_001", 1, "nonce_001", "send_normal_traffic", OLD_SECRET)

    result = verify_hmac_rolling_proof_for_session(
        hub,
        "session_001",
        1,
        "nonce_001",
        "send_normal_traffic",
        proof,
        current_time=4,
    )

    assert not result.success
    assert result.reason == "session_expired"
    assert hub.local_sessions["session_001"].state == "expired"


def test_session_rotation_invalidates_old_secret():
    hub = _registered_hub()
    create_local_session(hub, "dev_A9F3", OLD_SECRET, session_id="session_001")

    rotate_result = rotate_local_session(hub, "session_001", NEW_SECRET, current_time=5)
    old_proof = _proof(hub, "session_001", 1, "nonce_old", "send_normal_traffic", OLD_SECRET)
    old_result = verify_hmac_rolling_proof_for_session(
        hub,
        "session_001",
        1,
        "nonce_old",
        "send_normal_traffic",
        old_proof,
    )
    new_proof = _proof(hub, "session_001", 1, "nonce_new", "send_normal_traffic", NEW_SECRET)
    new_result = verify_hmac_rolling_proof_for_session(
        hub,
        "session_001",
        1,
        "nonce_new",
        "send_normal_traffic",
        new_proof,
    )

    assert rotate_result.success
    assert hub.local_sessions["session_001"].rotation_index == 1
    assert not old_result.success
    assert old_result.reason == "invalid_auth_tag"
    assert new_result.success
    assert hub.local_sessions["session_001"].current_counter == 1


def test_session_counter_reuse_fails():
    hub = _registered_hub()
    create_local_session(hub, "dev_A9F3", OLD_SECRET, session_id="session_001")

    proof_1 = _proof(hub, "session_001", 1, "nonce_1", "send_normal_traffic", OLD_SECRET)
    result_1 = verify_hmac_rolling_proof_for_session(
        hub,
        "session_001",
        1,
        "nonce_1",
        "send_normal_traffic",
        proof_1,
    )
    proof_1_reuse = _proof(
        hub,
        "session_001",
        1,
        "nonce_1_reuse",
        "send_normal_traffic",
        OLD_SECRET,
    )
    result_1_reuse = verify_hmac_rolling_proof_for_session(
        hub,
        "session_001",
        1,
        "nonce_1_reuse",
        "send_normal_traffic",
        proof_1_reuse,
    )
    proof_0 = _proof(hub, "session_001", 0, "nonce_0", "send_normal_traffic", OLD_SECRET)
    result_0 = verify_hmac_rolling_proof_for_session(
        hub,
        "session_001",
        0,
        "nonce_0",
        "send_normal_traffic",
        proof_0,
    )
    proof_2 = _proof(hub, "session_001", 2, "nonce_2", "send_normal_traffic", OLD_SECRET)
    result_2 = verify_hmac_rolling_proof_for_session(
        hub,
        "session_001",
        2,
        "nonce_2",
        "send_normal_traffic",
        proof_2,
    )

    assert result_1.success
    assert not result_1_reuse.success
    assert result_1_reuse.reason == "stale_counter"
    assert not result_0.success
    assert result_0.reason == "stale_counter"
    assert result_2.success


def test_session_counter_advances_on_success():
    hub = _registered_hub()
    create_local_session(hub, "dev_A9F3", OLD_SECRET, session_id="session_001")
    proof = _proof(hub, "session_001", 5, "nonce_5", "send_normal_traffic", OLD_SECRET)

    result = verify_hmac_rolling_proof_for_session(
        hub,
        "session_001",
        5,
        "nonce_5",
        "send_normal_traffic",
        proof,
    )

    assert result.success
    assert hub.local_sessions["session_001"].current_counter == 5


def test_symbolic_auth_unaffected_by_session_lifecycle():
    registry_hub = _registered_hub()
    device = Device(device_id="dev_A9F3", label="phone")
    checkpoint = make_checkpoint_packet(device, registry_hub.hub_id, "online", current_time=0)
    checkpoint_result = record_checkpoint(registry_hub, checkpoint)
    rolling_result = verify_rolling_proof(
        registry_hub,
        "dev_A9F3",
        proof_valid=True,
    )
    packet_result = verify_packet_auth(
        TrafficHub(hub_id="traffic_home_001"),
        DarwinPacket(packet_id="pkt_001", packet_class="DATA", packet_type="data_payload"),
    )

    assert checkpoint_result.accepted
    assert rolling_result.success
    assert packet_result.success


def test_hmac_session_rotation_scenario():
    scenario_path = PROJECT_ROOT / "scenarios" / "017_hmac_session_rotation.yaml"

    validation = validate_scenario_file(scenario_path)
    result = run_scenario(scenario_path)

    assert validation.passed
    assert result.passed


def test_hmac_session_expiration_scenario():
    scenario_path = PROJECT_ROOT / "scenarios" / "018_hmac_session_expiration.yaml"

    validation = validate_scenario_file(scenario_path)
    result = run_scenario(scenario_path)

    assert validation.passed
    assert result.passed
