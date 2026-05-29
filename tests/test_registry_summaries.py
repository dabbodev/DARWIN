from darwin.models.device import Device
from darwin.models.hub import RegistryHub
from darwin.registry.operations import register_device
from darwin.registry.summaries import (
    accept_child_summary,
    generate_upward_summary,
    resolve_device_id_from_summaries,
)


def make_parent_hub() -> RegistryHub:
    return RegistryHub(hub_id="hub_david_001", scope_path="global.family.david")


def make_child_hub() -> RegistryHub:
    return RegistryHub(
        hub_id="hub_home_001",
        scope_path="global.family.david.home",
        parent_hub_id="hub_david_001",
    )


def test_generate_upward_summary_contains_registered_device():
    child_hub = make_child_hub()
    device = Device(device_id="dev_A9F3", label="my_pc")
    register_device(child_hub, device)

    summary = generate_upward_summary(child_hub)

    assert summary.from_hub_id == "hub_home_001"
    assert summary.scope_path == "global.family.david.home"
    assert summary.summary_version == 1
    assert len(summary.devices) == 1
    assert summary.devices[0].device_id == "dev_A9F3"
    assert summary.devices[0].identity_chain == "global.family.david.home.my_pc"
    assert summary.devices[0].passport_id == "passport_dev_A9F3"
    assert summary.devices[0].current_state == "online"
    assert summary.devices[0].current_attachment == "hub_home_001"
    assert summary.devices[0].last_checkpoint is None


def test_summary_version_increments():
    child_hub = make_child_hub()

    first_summary = generate_upward_summary(child_hub)
    second_summary = generate_upward_summary(child_hub)

    assert second_summary.summary_version > first_summary.summary_version


def test_parent_accepts_child_summary():
    parent_hub = make_parent_hub()
    child_hub = make_child_hub()
    device = Device(device_id="dev_A9F3", label="my_pc")
    register_device(child_hub, device)

    summary = generate_upward_summary(child_hub)
    accept_child_summary(parent_hub, summary)

    assert parent_hub.child_summaries["hub_home_001"] == summary


def test_parent_resolves_device_from_child_summary():
    parent_hub = make_parent_hub()
    child_hub = make_child_hub()
    device = Device(device_id="dev_A9F3", label="my_pc")
    register_device(child_hub, device)
    accept_child_summary(parent_hub, generate_upward_summary(child_hub))

    result = resolve_device_id_from_summaries(parent_hub, "dev_A9F3")

    assert result is not None
    assert result.identity_chain == "global.family.david.home.my_pc"
    assert result.source == "child_summary"
    assert result.from_hub_id == "hub_home_001"
    assert result.scope_path == "global.family.david.home"


def test_parent_returns_none_for_unknown_summary_device():
    parent_hub = make_parent_hub()
    child_hub = make_child_hub()
    device = Device(device_id="dev_A9F3", label="my_pc")
    register_device(child_hub, device)
    accept_child_summary(parent_hub, generate_upward_summary(child_hub))

    result = resolve_device_id_from_summaries(parent_hub, "dev_MISSING")

    assert result is None
