from darwin.auth.move_contract import attach_move_auth
from darwin.models.device import Device
from darwin.models.hub import RegistryHub
from darwin.registry.operations import register_device
from darwin.registry.relocation import (
    create_move_contract,
    get_latest_move,
    update_attachment_after_move,
)
from darwin.registry.security import quarantine_device, revoke_device
from darwin.registry.sessions import create_local_session, expire_local_sessions

TEST_SECRET = "test_move_integration_secret_simulator_only"


def _registered_hub() -> RegistryHub:
    hub = RegistryHub(hub_id="hub_home_001", scope_path="global.family.home")
    register_device(hub, Device(device_id="dev_A9F3", label="phone"))
    return hub


def _create_session(hub: RegistryHub) -> None:
    create_local_session(
        hub,
        "dev_A9F3",
        TEST_SECRET,
        session_id="session_move_001",
        current_time=1,
        ttl=10,
    )


def _move_contract(*, valid: bool = True):
    return create_move_contract(
        device_id="dev_A9F3",
        passport_id="passport_dev_A9F3",
        from_scope="global.family.home",
        to_scope="global.family.office",
        old_attachment="hub_home_001",
        new_attachment="hub_office_001",
        valid=valid,
        timestamp=42,
    )


def _hmac_contract(hub: RegistryHub, *, move_counter: int = 1):
    if "session_move_001" not in hub.local_sessions:
        _create_session(hub)
    return attach_move_auth(
        _move_contract(),
        TEST_SECRET,
        session_id="session_move_001",
        move_nonce="nonce_move_001",
        move_counter=move_counter,
    )


def test_update_attachment_after_hmac_move_success():
    hub = _registered_hub()
    _create_session(hub)
    contract = _hmac_contract(hub, move_counter=1)

    result = update_attachment_after_move(
        hub,
        "dev_A9F3",
        new_attachment="hub_office_001",
        new_scope="global.family.office",
        move_contract=contract,
    )

    assert result.success
    assert result.reason is None
    assert hub.devices["dev_A9F3"].current_attachment == "hub_office_001"
    assert hub.devices["dev_A9F3"].current_state == "online"
    assert get_latest_move(hub, "dev_A9F3") == contract
    assert hub.local_sessions["session_move_001"].current_counter == 1


def test_hmac_move_tampered_new_attachment_fails():
    hub = _registered_hub()
    _create_session(hub)
    contract = _hmac_contract(hub, move_counter=1)
    contract.new_attachment = "hub_guest_001"

    result = update_attachment_after_move(
        hub,
        "dev_A9F3",
        new_attachment="hub_guest_001",
        new_scope="global.family.office",
        move_contract=contract,
    )

    assert not result.success
    assert result.action == "move_contract_rejected"
    assert result.reason == "invalid_move_auth_tag"
    assert hub.devices["dev_A9F3"].current_attachment == "hub_home_001"
    assert "dev_A9F3" not in hub.moves
    assert hub.local_sessions["session_move_001"].current_counter == 0


def test_hmac_move_expired_session_fails():
    hub = _registered_hub()
    _create_session(hub)
    expire_local_sessions(hub, current_time=11)
    contract = _hmac_contract(hub, move_counter=1)

    result = update_attachment_after_move(
        hub,
        "dev_A9F3",
        new_attachment="hub_office_001",
        new_scope="global.family.office",
        move_contract=contract,
    )

    assert not result.success
    assert result.reason == "move_session_inactive"
    assert hub.devices["dev_A9F3"].current_attachment == "hub_home_001"
    assert "dev_A9F3" not in hub.moves
    assert hub.local_sessions["session_move_001"].current_counter == 0


def test_hmac_move_revoked_device_fails():
    hub = _registered_hub()
    _create_session(hub)
    contract = _hmac_contract(hub, move_counter=1)
    revoke_device(hub, "dev_A9F3", reason="test_revocation")

    result = update_attachment_after_move(
        hub,
        "dev_A9F3",
        new_attachment="hub_office_001",
        new_scope="global.family.office",
        move_contract=contract,
    )

    assert not result.success
    assert result.reason == "device_revoked"
    assert hub.devices["dev_A9F3"].current_attachment == "hub_home_001"
    assert "dev_A9F3" not in hub.moves
    assert hub.local_sessions["session_move_001"].current_counter == 0


def test_hmac_move_quarantined_device_fails():
    hub = _registered_hub()
    _create_session(hub)
    contract = _hmac_contract(hub, move_counter=1)
    quarantine_device(hub, "dev_A9F3", reason="test_quarantine")

    result = update_attachment_after_move(
        hub,
        "dev_A9F3",
        new_attachment="hub_office_001",
        new_scope="global.family.office",
        move_contract=contract,
    )

    assert not result.success
    assert result.reason == "device_quarantined"
    assert hub.devices["dev_A9F3"].current_attachment == "hub_home_001"
    assert "dev_A9F3" not in hub.moves
    assert hub.local_sessions["session_move_001"].current_counter == 0


def test_hmac_move_stale_counter_fails():
    hub = _registered_hub()
    _create_session(hub)
    session = hub.local_sessions["session_move_001"]
    session.current_counter = 1
    contract = _hmac_contract(hub, move_counter=1)

    result = update_attachment_after_move(
        hub,
        "dev_A9F3",
        new_attachment="hub_office_001",
        new_scope="global.family.office",
        move_contract=contract,
    )

    assert not result.success
    assert result.reason == "stale_move_counter"
    assert hub.devices["dev_A9F3"].current_attachment == "hub_home_001"
    assert "dev_A9F3" not in hub.moves
    assert session.current_counter == 1


def test_symbolic_update_attachment_after_move_still_works():
    hub = _registered_hub()
    contract = _move_contract(valid=True)

    result = update_attachment_after_move(
        hub,
        "dev_A9F3",
        new_attachment="hub_office_001",
        new_scope="global.family.office",
        move_contract=contract,
    )

    assert result.success
    assert hub.devices["dev_A9F3"].current_attachment == "hub_office_001"
    assert get_latest_move(hub, "dev_A9F3") == contract


def test_symbolic_invalid_move_still_fails():
    hub = _registered_hub()
    contract = _move_contract(valid=False)

    result = update_attachment_after_move(
        hub,
        "dev_A9F3",
        new_attachment="hub_office_001",
        new_scope="global.family.office",
        move_contract=contract,
    )

    assert not result.success
    assert result.reason == "invalid_move_contract"
    assert hub.devices["dev_A9F3"].current_attachment == "hub_home_001"
    assert "dev_A9F3" not in hub.moves
