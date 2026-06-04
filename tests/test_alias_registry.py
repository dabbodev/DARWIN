from darwin.models.device import Device
from darwin.models.hub import RegistryHub
from darwin.registry.aliases import alias_exists, claim_alias, release_alias, resolve_alias
from darwin.registry.operations import register_device
from darwin.registry.security import quarantine_device, revoke_device


def make_registry_hub() -> RegistryHub:
    return RegistryHub(hub_id="hub_home_001", scope_path="global.family.david.home")


def register_test_device(
    hub: RegistryHub,
    device_id: str = "dev_A9F3",
    label: str = "phone",
):
    device = Device(device_id=device_id, label=label)
    record = register_device(hub, device)
    return device, record


def test_claim_alias_for_registered_device():
    hub = make_registry_hub()
    _, record = register_test_device(hub)

    result = claim_alias(hub, "david_phone", "dev_A9F3")

    assert result.success
    assert result.status == "active"
    assert result.alias_record is not None
    assert hub.aliases["david_phone"] == result.alias_record
    assert result.alias_record.target_device_id == "dev_A9F3"
    assert result.alias_record.target_identity_chain == record.identity_chain
    assert result.alias_record.approved_by_registry_hub == "hub_home_001"
    assert result.alias_record.authority_scope == "global.family.david.home"


def test_resolve_alias_returns_target_identity():
    hub = make_registry_hub()
    _, record = register_test_device(hub)
    claim_alias(hub, "david_phone", "dev_A9F3")

    result = resolve_alias(hub, "david_phone")

    assert result.success
    assert result.status == "active"
    assert result.target_device_id == "dev_A9F3"
    assert result.target_identity_chain == record.identity_chain
    assert result.alias_record == hub.aliases["david_phone"]


def test_claim_alias_unknown_device_fails():
    hub = make_registry_hub()

    result = claim_alias(hub, "missing_phone", "dev_MISSING")

    assert not result.success
    assert result.reason == "unknown_device"
    assert "missing_phone" not in hub.aliases


def test_claim_alias_conflict_fails():
    hub = make_registry_hub()
    register_test_device(hub, device_id="dev_A9F3", label="phone")
    register_test_device(hub, device_id="dev_B2C8", label="tablet")

    first_result = claim_alias(hub, "shared_alias", "dev_A9F3")
    conflict_result = claim_alias(hub, "shared_alias", "dev_B2C8")

    assert first_result.success
    assert not conflict_result.success
    assert conflict_result.status == "conflict"
    assert conflict_result.reason == "alias_conflict"
    assert conflict_result.conflict_id in hub.conflicts
    assert hub.aliases["shared_alias"].target_device_id == "dev_A9F3"


def test_claim_alias_quarantined_device_fails():
    hub = make_registry_hub()
    register_test_device(hub)
    quarantine_device(hub, "dev_A9F3", reason="test_quarantine")

    result = claim_alias(hub, "david_phone", "dev_A9F3")

    assert not result.success
    assert result.reason == "device_quarantined"
    assert "david_phone" not in hub.aliases


def test_claim_alias_revoked_device_fails():
    hub = make_registry_hub()
    register_test_device(hub)
    revoke_device(hub, "dev_A9F3", reason="test_revocation")

    result = claim_alias(hub, "david_phone", "dev_A9F3")

    assert not result.success
    assert result.reason == "device_revoked"
    assert "david_phone" not in hub.aliases


def test_release_alias_blocks_resolution():
    hub = make_registry_hub()
    register_test_device(hub)
    claim_alias(hub, "david_phone", "dev_A9F3")

    release_result = release_alias(hub, "david_phone", requested_by_device_id="dev_A9F3")
    resolve_result = resolve_alias(hub, "david_phone")

    assert release_result.success
    assert release_result.status == "released"
    assert not resolve_result.success
    assert resolve_result.status == "released"
    assert resolve_result.target_device_id is None
    assert not alias_exists(hub, "david_phone")


def test_claim_alias_does_not_mutate_canonical_identity():
    hub = make_registry_hub()
    device, record = register_test_device(hub)
    original_label = record.current_label
    original_identity_chain = record.identity_chain
    original_passport_id = record.passport_id
    original_attachment = record.current_attachment

    claim_alias(hub, "david_phone", "dev_A9F3")

    assert device.label == original_label
    assert record.current_label == original_label
    assert record.identity_chain == original_identity_chain
    assert record.full_identity_chain == original_identity_chain
    assert record.passport_id == original_passport_id
    assert record.current_attachment == original_attachment


def test_alias_visibility_and_ttl_stored():
    hub = make_registry_hub()
    register_test_device(hub)

    result = claim_alias(
        hub,
        "david_phone",
        "dev_A9F3",
        visibility="scope_local",
        ttl=3600,
    )

    assert result.success
    assert result.alias_record is not None
    assert result.alias_record.visibility == "scope_local"
    assert result.alias_record.ttl == 3600


def test_alias_symbolic_default():
    hub = make_registry_hub()
    register_test_device(hub)

    result = claim_alias(hub, "david_phone", "dev_A9F3")

    assert result.success
    assert result.alias_record is not None
    assert result.alias_record.alias_type == "device_alias"
    assert result.alias_record.status == "active"
    assert result.alias_record.conflict_id is None
