from pathlib import Path

from darwin.models.device import Device
from darwin.models.hub import RegistryHub
from darwin.registry.aliases import claim_alias, claim_progressive_alias, resolve_alias
from darwin.registry.operations import register_device
from darwin.registry.security import quarantine_device, revoke_device
from darwin.sim.runner import run_scenario

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def make_registry_hub() -> RegistryHub:
    return RegistryHub(
        hub_id="registry_xfinity_301",
        scope_path="global.us.west1.dist25.sf2.xfinity_301",
    )


def register_test_device(
    hub: RegistryHub,
    device_id: str = "dev_A9F3",
    label: str = "project_server",
):
    device = Device(device_id=device_id, label=label)
    record = register_device(hub, device)
    return device, record


def test_progressive_alias_within_authority_claims_requested_alias():
    hub = make_registry_hub()
    register_test_device(hub)
    requested_alias = "global.us.west1.dist25.sf2.xfinity_301.project_server"

    result = claim_progressive_alias(
        hub,
        requested_alias=requested_alias,
        local_name="project_server",
        target_device_id="dev_A9F3",
    )

    assert result.success
    assert result.status == "claimed"
    assert result.granted_alias == requested_alias
    assert result.alias_record is hub.aliases[requested_alias]
    assert result.alias_record.status == "active"


def test_progressive_alias_fallback_grants_scope_alias():
    hub = make_registry_hub()
    register_test_device(hub)

    result = claim_progressive_alias(
        hub,
        requested_alias="global.david_server",
        local_name="david_server",
        target_device_id="dev_A9F3",
    )

    assert result.success
    assert result.status == "fallback_granted"
    assert result.reason == "insufficient_authority"
    assert (
        result.granted_alias
        == "global.us.west1.dist25.sf2.xfinity_301.david_server"
    )
    assert result.alias_record is not None
    assert result.alias_record.requested_alias == "global.david_server"
    assert result.alias_record.granted_alias == result.granted_alias
    assert result.alias_record.fallback_reason == "insufficient_authority"


def test_progressive_alias_fallback_preserves_authority_ceiling():
    hub = make_registry_hub()
    register_test_device(hub)

    result = claim_progressive_alias(
        hub,
        requested_alias="global.david_server",
        local_name="david_server",
        target_device_id="dev_A9F3",
    )

    assert result.success
    assert result.authority_ceiling == hub.scope_path
    assert result.alias_record is not None
    assert result.alias_record.authority_ceiling == hub.scope_path
    assert result.alias_record.authority_scope == hub.scope_path


def test_progressive_alias_without_fallback_fails():
    hub = make_registry_hub()
    register_test_device(hub)

    result = claim_progressive_alias(
        hub,
        requested_alias="global.david_server",
        local_name="david_server",
        target_device_id="dev_A9F3",
        fallback_allowed=False,
    )

    assert not result.success
    assert result.status == "rejected"
    assert result.reason == "insufficient_authority"
    assert result.granted_alias is None
    assert not hub.aliases


def test_progressive_alias_fallback_conflict_fails():
    hub = make_registry_hub()
    register_test_device(hub, device_id="dev_A9F3", label="project_server")
    register_test_device(hub, device_id="dev_B2C8", label="tablet")
    fallback_alias = "global.us.west1.dist25.sf2.xfinity_301.david_server"

    first_result = claim_alias(hub, fallback_alias, "dev_A9F3")
    conflict_result = claim_progressive_alias(
        hub,
        requested_alias="global.david_server",
        local_name="david_server",
        target_device_id="dev_B2C8",
    )

    assert first_result.success
    assert not conflict_result.success
    assert conflict_result.status == "conflict"
    assert conflict_result.reason == "alias_conflict"
    assert conflict_result.conflict_id in hub.conflicts
    resolution = resolve_alias(hub, fallback_alias)
    assert resolution.success
    assert resolution.target_device_id == "dev_A9F3"


def test_progressive_alias_quarantined_device_fails():
    hub = make_registry_hub()
    register_test_device(hub)
    quarantine_device(hub, "dev_A9F3", reason="test_quarantine")

    result = claim_progressive_alias(
        hub,
        requested_alias="global.david_server",
        local_name="david_server",
        target_device_id="dev_A9F3",
    )

    assert not result.success
    assert result.status == "rejected"
    assert result.reason == "device_quarantined"
    assert not hub.aliases


def test_progressive_alias_revoked_device_fails():
    hub = make_registry_hub()
    register_test_device(hub)
    revoke_device(hub, "dev_A9F3", reason="test_revocation")

    result = claim_progressive_alias(
        hub,
        requested_alias="global.david_server",
        local_name="david_server",
        target_device_id="dev_A9F3",
    )

    assert not result.success
    assert result.status == "rejected"
    assert result.reason == "device_revoked"
    assert not hub.aliases


def test_progressive_alias_scenario_runs():
    result = run_scenario(
        PROJECT_ROOT / "scenarios" / "029_progressive_alias_fallback.yaml"
    )

    assert result.passed
