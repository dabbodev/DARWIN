import pytest

from darwin.auth.hmac_bridge import canonical_json
from darwin.auth.modes import AUTH_MODE_HMAC_SHA256_EXPERIMENTAL
from darwin.auth.move_contract import (
    MoveAuthMaterial,
    attach_move_auth,
    build_move_auth_material,
    compute_move_auth_tag,
    move_auth_material_from_contract,
    verify_move_auth_tag,
)
from darwin.models.device import Device
from darwin.models.hub import RegistryHub
from darwin.registry.operations import register_device
from darwin.registry.relocation import create_move_contract, update_attachment_after_move

TEST_SECRET = "test_move_secret_simulator_only"
WRONG_SECRET = "wrong_move_secret_simulator_only"


def _move_material(**overrides: object) -> dict[str, object]:
    fields = {
        "device_id": "dev_A9F3",
        "passport_id": "passport_dev_A9F3",
        "from_scope": "global.family.home",
        "to_scope": "global.family.office",
        "old_attachment": "hub_home_001",
        "new_attachment": "hub_office_001",
        "move_nonce": "nonce_move_001",
        "session_id": "session_move_001",
        "move_counter": 3,
        "timestamp": 42,
    }
    fields.update(overrides)
    return build_move_auth_material(**fields)


def test_move_auth_material_is_deterministic():
    left = _move_material()
    right = build_move_auth_material(
        move_counter=3,
        session_id="session_move_001",
        move_nonce="nonce_move_001",
        new_attachment="hub_office_001",
        old_attachment="hub_home_001",
        to_scope="global.family.office",
        from_scope="global.family.home",
        passport_id="passport_dev_A9F3",
        device_id="dev_A9F3",
        timestamp=42,
    )
    right_with_extra = dict(right, move_id="ignored_by_helper")

    assert canonical_json(left) == canonical_json(right)
    assert compute_move_auth_tag(TEST_SECRET, left) == compute_move_auth_tag(TEST_SECRET, right)
    assert compute_move_auth_tag(TEST_SECRET, left) == compute_move_auth_tag(
        TEST_SECRET,
        right_with_extra,
    )


def test_compute_and_verify_move_auth_tag_success():
    material = _move_material()

    tag = compute_move_auth_tag(TEST_SECRET, material)

    assert verify_move_auth_tag(TEST_SECRET, material, tag)


def test_move_auth_tag_fails_with_wrong_secret():
    material = _move_material()
    tag = compute_move_auth_tag(TEST_SECRET, material)

    assert not verify_move_auth_tag(WRONG_SECRET, material, tag)


def test_move_auth_tag_fails_when_to_scope_tampered():
    material = _move_material()
    tag = compute_move_auth_tag(TEST_SECRET, material)
    tampered = dict(material, to_scope="global.family.guest")

    assert not verify_move_auth_tag(TEST_SECRET, tampered, tag)


def test_move_auth_tag_fails_when_new_attachment_tampered():
    material = _move_material()
    tag = compute_move_auth_tag(TEST_SECRET, material)
    tampered = dict(material, new_attachment="hub_guest_001")

    assert not verify_move_auth_tag(TEST_SECRET, tampered, tag)


def test_move_auth_tag_fails_when_old_attachment_tampered():
    material = _move_material()
    tag = compute_move_auth_tag(TEST_SECRET, material)
    tampered = dict(material, old_attachment="hub_unknown_001")

    assert not verify_move_auth_tag(TEST_SECRET, tampered, tag)


def test_move_auth_tag_fails_when_nonce_tampered():
    material = _move_material()
    tag = compute_move_auth_tag(TEST_SECRET, material)
    tampered = dict(material, move_nonce="nonce_move_002")

    assert not verify_move_auth_tag(TEST_SECRET, tampered, tag)


def test_move_auth_tag_fails_when_counter_tampered():
    material = _move_material()
    tag = compute_move_auth_tag(TEST_SECRET, material)
    tampered = dict(material, move_counter=4)

    assert not verify_move_auth_tag(TEST_SECRET, tampered, tag)


def test_move_auth_material_from_move_contract():
    contract = create_move_contract(
        device_id="dev_A9F3",
        passport_id="passport_dev_A9F3",
        from_scope="global.family.home",
        to_scope="global.family.office",
        old_attachment="hub_home_001",
        new_attachment="hub_office_001",
        valid=True,
        timestamp=42,
    )

    material = move_auth_material_from_contract(
        contract,
        session_id="session_move_001",
        move_nonce="nonce_move_001",
        move_counter=3,
    )

    assert material == _move_material()


def test_move_auth_material_dataclass_matches_dict_material():
    material = MoveAuthMaterial(
        device_id="dev_A9F3",
        passport_id="passport_dev_A9F3",
        from_scope="global.family.home",
        to_scope="global.family.office",
        old_attachment="hub_home_001",
        new_attachment="hub_office_001",
        move_nonce="nonce_move_001",
        session_id="session_move_001",
        move_counter=3,
        timestamp=42,
    )

    assert material.to_dict() == _move_material()
    assert compute_move_auth_tag(TEST_SECRET, material) == compute_move_auth_tag(
        TEST_SECRET,
        _move_material(),
    )


def test_attach_move_auth_sets_simulator_only_contract_fields():
    contract = create_move_contract(
        device_id="dev_A9F3",
        passport_id="passport_dev_A9F3",
        from_scope="global.family.home",
        to_scope="global.family.office",
        old_attachment="hub_home_001",
        new_attachment="hub_office_001",
        valid=True,
        timestamp=42,
    )

    attach_move_auth(
        contract,
        TEST_SECRET,
        session_id="session_move_001",
        move_nonce="nonce_move_001",
        move_counter=3,
    )

    assert contract.auth_mode == AUTH_MODE_HMAC_SHA256_EXPERIMENTAL
    assert contract.session_id == "session_move_001"
    assert contract.move_nonce == "nonce_move_001"
    assert contract.move_counter == 3
    assert contract.move_auth_tag == compute_move_auth_tag(TEST_SECRET, _move_material())


def test_move_auth_tag_missing_required_fields_fails_cleanly():
    material = _move_material()
    material.pop("move_nonce")
    tag = compute_move_auth_tag(TEST_SECRET, _move_material())

    assert not verify_move_auth_tag(TEST_SECRET, material, tag)
    with pytest.raises(ValueError, match="move_nonce"):
        compute_move_auth_tag(TEST_SECRET, material)


def test_symbolic_move_contract_behavior_unchanged():
    hub = RegistryHub(hub_id="hub_home_001", scope_path="global.family.home")
    register_device(hub, Device(device_id="dev_A9F3", label="phone"))
    contract = create_move_contract(
        device_id="dev_A9F3",
        passport_id="passport_dev_A9F3",
        from_scope="global.family.home",
        to_scope="global.family.office",
        old_attachment="hub_home_001",
        new_attachment="hub_office_001",
        valid=True,
    )

    result = update_attachment_after_move(
        hub,
        "dev_A9F3",
        new_attachment="hub_office_001",
        new_scope="global.family.office",
        move_contract=contract,
    )

    assert result.success
    assert result.action == "attachment_updated"
    assert hub.devices["dev_A9F3"].current_attachment == "hub_office_001"
