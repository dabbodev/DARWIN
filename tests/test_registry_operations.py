from darwin.models.device import Device
from darwin.models.hub import RegistryHub
from darwin.registry.operations import register_device, resolve_device_id, resolve_label


def make_home_hub() -> RegistryHub:
    return RegistryHub(hub_id="hub_home_001", scope_path="global.family.david.home")


def test_register_device_assigns_identity_chain():
    hub = make_home_hub()
    device = Device(device_id="dev_A9F3", label="my_pc")

    record = register_device(hub, device, checkpoint_tier=2)

    assert hub.labels["my_pc"] == "dev_A9F3"
    assert hub.devices["dev_A9F3"] == record
    assert record.identity_chain == "global.family.david.home.my_pc"
    assert record.current_label == "my_pc"
    assert record.checkpoint_tier == 2
    assert record.passport_id in hub.passports
    assert hub.passports[record.passport_id].usable
    assert hub.attachments["dev_A9F3"].current_attachment == "hub_home_001"


def test_duplicate_label_assigns_temp_label():
    hub = make_home_hub()
    first = Device(device_id="dev_A9F3", label="my_pc")
    second = Device(device_id="dev_B2C8", label="my_pc")

    first_record = register_device(hub, first)
    second_record = register_device(hub, second)

    assert first_record.current_label == "my_pc"
    assert second_record.current_label == "my_pc_temp_B2C8"
    assert hub.labels["my_pc"] == "dev_A9F3"
    assert hub.labels["my_pc_temp_B2C8"] == "dev_B2C8"
    assert hub.devices["dev_A9F3"].current_label == "my_pc"
    assert hub.devices["dev_B2C8"].current_label == "my_pc_temp_B2C8"
    assert any(conflict.conflict_type == "label_conflict" for conflict in hub.conflicts.values())


def test_resolve_label_returns_registered_device():
    hub = make_home_hub()
    device = Device(device_id="dev_A9F3", label="my_pc")
    register_device(hub, device)

    record = resolve_label(hub, "my_pc")

    assert record is not None
    assert record.device_id == "dev_A9F3"
    assert record.identity_chain == "global.family.david.home.my_pc"


def test_resolve_device_id_returns_registered_device():
    hub = make_home_hub()
    device = Device(device_id="dev_A9F3", label="my_pc")
    register_device(hub, device, checkpoint_tier=2)

    record = resolve_device_id(hub, "dev_A9F3")

    assert record is not None
    assert record.current_label == "my_pc"
    assert record.identity_chain == "global.family.david.home.my_pc"
    assert record.current_state == "online"
    assert record.checkpoint_tier == 2


def test_unknown_label_or_device_id_not_found():
    hub = make_home_hub()

    assert resolve_label(hub, "missing") is None
    assert resolve_device_id(hub, "dev_MISSING") is None
