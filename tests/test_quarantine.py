from darwin.models.device import Device
from darwin.models.hub import RegistryHub
from darwin.registry.operations import register_device
from darwin.registry.security import verify_rolling_proof


def make_registry_hub() -> RegistryHub:
    return RegistryHub(hub_id="hub_home_001", scope_path="global.family.david.home")


def test_quarantine_record_has_allowed_and_denied_actions():
    hub = make_registry_hub()
    device = Device(device_id="dev_A9F3", label="phone")
    register_device(hub, device)

    verify_rolling_proof(hub, "dev_A9F3", proof_valid=False)
    record = hub.quarantines["dev_A9F3"]

    assert record.claimed_device_id == "dev_A9F3"
    assert record.status == "active"
    assert "present_passport" in record.allowed_actions
    assert "send_normal_traffic" in record.denied_actions
    assert "open_new_lane" in record.denied_actions
