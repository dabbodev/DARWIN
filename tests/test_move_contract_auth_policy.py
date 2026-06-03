from darwin.auth.modes import AUTH_MODE_HMAC_SHA256_EXPERIMENTAL, AUTH_MODE_SYMBOLIC
from darwin.auth.move_contract import attach_move_auth, verify_move_contract_auth
from darwin.models.device import Device
from darwin.models.hub import RegistryHub
from darwin.models.move import MoveContract
from darwin.registry.operations import register_device
from darwin.registry.security import quarantine_device, revoke_device
from darwin.registry.sessions import create_local_session, expire_local_sessions

TEST_SECRET = "test_move_policy_secret_simulator_only"
WRONG_SECRET = "wrong_move_policy_secret_simulator_only"


def _registered_hub() -> RegistryHub:
    hub = RegistryHub(hub_id="hub_home_001", scope_path="global.family.home")
    register_device(hub, Device(device_id="dev_A9F3", label="phone"))
    return hub


def _move_contract(
    *,
    device_id: str = "dev_A9F3",
    passport_id: str = "passport_dev_A9F3",
    valid: bool = True,
) -> MoveContract:
    return MoveContract(
        move_id=f"move_{device_id}_hub_office_001",
        passport_id=passport_id,
        device_id=device_id,
        from_scope="global.family.home",
        to_scope="global.family.office",
        old_attachment="hub_home_001",
        new_attachment="hub_office_001",
        valid=valid,
        timestamp=42,
    )


def _create_session(hub: RegistryHub, session_id: str = "session_move_001") -> None:
    create_local_session(
        hub,
        "dev_A9F3",
        TEST_SECRET,
        session_id=session_id,
        current_time=1,
        ttl=10,
    )


def _hmac_contract(
    hub: RegistryHub,
    *,
    session_id: str = "session_move_001",
    move_counter: int = 1,
    secret: str = TEST_SECRET,
) -> MoveContract:
    contract = _move_contract()
    if session_id not in hub.local_sessions:
        _create_session(hub, session_id=session_id)
    return attach_move_auth(
        contract,
        secret,
        session_id=session_id,
        move_nonce="nonce_move_001",
        move_counter=move_counter,
    )


def test_symbolic_move_contract_auth_valid_passes():
    hub = _registered_hub()
    contract = _move_contract(valid=True)

    result = verify_move_contract_auth(hub, contract)

    assert result.success
    assert result.status == "move_auth_verified"
    assert result.reason is None
    assert result.auth_mode == AUTH_MODE_SYMBOLIC
    assert result.session_id is None
    assert result.move_counter is None


def test_symbolic_move_contract_auth_invalid_fails():
    hub = _registered_hub()
    contract = _move_contract(valid=False)

    result = verify_move_contract_auth(hub, contract)

    assert not result.success
    assert result.reason == "symbolic_move_invalid"
    assert result.auth_mode == AUTH_MODE_SYMBOLIC


def test_hmac_move_auth_success_with_active_session():
    hub = _registered_hub()
    _create_session(hub)
    contract = _hmac_contract(hub, move_counter=1)

    result = verify_move_contract_auth(hub, contract)

    assert result.success
    assert result.status == "move_auth_verified"
    assert result.reason is None
    assert result.auth_mode == AUTH_MODE_HMAC_SHA256_EXPERIMENTAL
    assert result.session_id == "session_move_001"
    assert result.move_counter == 1
    assert hub.local_sessions["session_move_001"].current_counter == 1


def test_hmac_move_auth_missing_session_id_fails():
    hub = _registered_hub()
    contract = _move_contract()
    contract.auth_mode = AUTH_MODE_HMAC_SHA256_EXPERIMENTAL
    contract.move_nonce = "nonce_move_001"
    contract.move_counter = 1
    contract.move_auth_tag = "unused_without_session"

    result = verify_move_contract_auth(hub, contract)

    assert not result.success
    assert result.reason == "missing_move_session"
    assert result.session_id is None
    assert result.move_counter == 1


def test_hmac_move_auth_session_not_found_fails():
    hub = _registered_hub()
    contract = _move_contract()
    attach_move_auth(
        contract,
        TEST_SECRET,
        session_id="session_missing",
        move_nonce="nonce_move_001",
        move_counter=1,
    )

    result = verify_move_contract_auth(hub, contract)

    assert not result.success
    assert result.reason == "move_session_not_found"


def test_hmac_move_auth_expired_session_fails():
    hub = _registered_hub()
    _create_session(hub)
    expire_local_sessions(hub, current_time=11)
    contract = _hmac_contract(hub, move_counter=1)

    result = verify_move_contract_auth(hub, contract)

    assert not result.success
    assert result.reason == "move_session_inactive"
    assert hub.local_sessions["session_move_001"].state == "expired"
    assert hub.local_sessions["session_move_001"].current_counter == 0


def test_hmac_move_auth_device_mismatch_fails():
    hub = _registered_hub()
    register_device(hub, Device(device_id="dev_B2C8", label="tablet"))
    create_local_session(
        hub,
        "dev_B2C8",
        TEST_SECRET,
        session_id="session_move_001",
    )
    contract = _hmac_contract(hub, move_counter=1)

    result = verify_move_contract_auth(hub, contract)

    assert not result.success
    assert result.reason == "move_session_device_mismatch"
    assert hub.local_sessions["session_move_001"].current_counter == 0


def test_hmac_move_auth_quarantined_device_fails():
    hub = _registered_hub()
    _create_session(hub)
    contract = _hmac_contract(hub, move_counter=1)
    quarantine_device(hub, "dev_A9F3", reason="test_quarantine")
    hub.local_sessions["session_move_001"].state = "active"

    result = verify_move_contract_auth(hub, contract)

    assert not result.success
    assert result.reason == "device_quarantined"
    assert hub.local_sessions["session_move_001"].current_counter == 0


def test_hmac_move_auth_revoked_device_fails():
    hub = _registered_hub()
    _create_session(hub)
    contract = _hmac_contract(hub, move_counter=1)
    revoke_device(hub, "dev_A9F3", reason="test_revocation")
    hub.local_sessions["session_move_001"].state = "active"

    result = verify_move_contract_auth(hub, contract)

    assert not result.success
    assert result.reason == "device_revoked"
    assert hub.local_sessions["session_move_001"].current_counter == 0


def test_hmac_move_auth_stale_counter_fails():
    hub = _registered_hub()
    _create_session(hub)
    session = hub.local_sessions["session_move_001"]
    session.current_counter = 5
    same_counter_contract = _hmac_contract(hub, move_counter=5)
    older_counter_contract = _hmac_contract(hub, move_counter=4)

    same_result = verify_move_contract_auth(hub, same_counter_contract)
    older_result = verify_move_contract_auth(hub, older_counter_contract)

    assert not same_result.success
    assert same_result.reason == "stale_move_counter"
    assert not older_result.success
    assert older_result.reason == "stale_move_counter"
    assert session.current_counter == 5


def test_hmac_move_auth_invalid_tag_fails():
    hub = _registered_hub()
    _create_session(hub)
    contract = _hmac_contract(hub, move_counter=1, secret=WRONG_SECRET)

    result = verify_move_contract_auth(hub, contract)

    assert not result.success
    assert result.reason == "invalid_move_auth_tag"
    assert hub.local_sessions["session_move_001"].current_counter == 0


def test_hmac_move_auth_success_advances_counter_only_once():
    hub = _registered_hub()
    _create_session(hub)
    contract = _hmac_contract(hub, move_counter=1)

    first_result = verify_move_contract_auth(hub, contract)
    second_result = verify_move_contract_auth(hub, contract)

    assert first_result.success
    assert not second_result.success
    assert second_result.reason == "stale_move_counter"
    assert hub.local_sessions["session_move_001"].current_counter == 1
