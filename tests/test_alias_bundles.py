from pathlib import Path

from darwin.models.device import Device
from darwin.models.hub import RegistryHub
from darwin.registry.aliases import (
    claim_bundle_alias,
    create_alias_bundle,
    resolve_alias,
)
from darwin.registry.operations import register_device
from darwin.registry.security import quarantine_device, revoke_device
from darwin.sim.runner import run_scenario

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def make_registry_hub() -> RegistryHub:
    return RegistryHub(hub_id="hub_gov_001", scope_path="global.us.gov")


def register_test_device(
    hub: RegistryHub,
    device_id: str = "dev_CA_SITE",
    label: str = "ca_website_server",
):
    device = Device(device_id=device_id, label=label)
    record = register_device(hub, device)
    return device, record


def test_create_alias_bundle_success():
    hub = make_registry_hub()

    result = create_alias_bundle(hub, "global.us.gov.ca")

    assert result.success
    assert result.status == "active"
    assert result.bundle is hub.alias_bundles["global.us.gov.ca"]
    assert result.bundle.delegated_to_registry_hub == "hub_gov_001"
    assert result.bundle.approved_by_registry_hub == "hub_gov_001"
    assert result.bundle.authority_scope == "global.us.gov"
    assert result.bundle.allowed_record_types == ["device_alias"]


def test_create_alias_bundle_conflict_fails():
    hub = make_registry_hub()

    first_result = create_alias_bundle(hub, "global.us.gov.ca")
    conflict_result = create_alias_bundle(hub, "global.us.gov.ca")

    assert first_result.success
    assert not conflict_result.success
    assert conflict_result.status == "conflict"
    assert conflict_result.reason == "bundle_conflict"
    assert hub.alias_bundles["global.us.gov.ca"] is first_result.bundle


def test_claim_bundle_alias_success():
    hub = make_registry_hub()
    _, record = register_test_device(hub)
    create_alias_bundle(hub, "global.us.gov.ca")

    result = claim_bundle_alias(
        hub,
        "global.us.gov.ca",
        "website",
        "dev_CA_SITE",
    )
    resolution = resolve_alias(hub, "global.us.gov.ca.website")

    assert result.success
    assert result.status == "active"
    assert result.bundle_path == "global.us.gov.ca"
    assert result.alias_record is hub.aliases["global.us.gov.ca.website"]
    assert resolution.success
    assert resolution.target_device_id == "dev_CA_SITE"
    assert resolution.target_identity_chain == record.identity_chain


def test_claim_bundle_alias_missing_bundle_fails():
    hub = make_registry_hub()
    register_test_device(hub)

    result = claim_bundle_alias(
        hub,
        "global.us.gov.ca",
        "website",
        "dev_CA_SITE",
    )

    assert not result.success
    assert result.status == "not_found"
    assert result.reason == "bundle_not_found"
    assert not hub.aliases


def test_claim_bundle_alias_conflict_fails():
    hub = make_registry_hub()
    register_test_device(hub, device_id="dev_CA_SITE", label="ca_website_server")
    register_test_device(hub, device_id="dev_CA_DMV", label="ca_dmv_server")
    create_alias_bundle(hub, "global.us.gov.ca")

    first_result = claim_bundle_alias(
        hub,
        "global.us.gov.ca",
        "website",
        "dev_CA_SITE",
    )
    conflict_result = claim_bundle_alias(
        hub,
        "global.us.gov.ca",
        "website",
        "dev_CA_DMV",
    )

    assert first_result.success
    assert not conflict_result.success
    assert conflict_result.status == "conflict"
    assert conflict_result.reason == "alias_conflict"
    assert hub.aliases["global.us.gov.ca.website"].target_device_id == "dev_CA_SITE"


def test_claim_bundle_alias_quarantined_device_fails():
    hub = make_registry_hub()
    register_test_device(hub)
    create_alias_bundle(hub, "global.us.gov.ca")
    quarantine_device(hub, "dev_CA_SITE", reason="test_quarantine")

    result = claim_bundle_alias(
        hub,
        "global.us.gov.ca",
        "website",
        "dev_CA_SITE",
    )

    assert not result.success
    assert result.status == "rejected"
    assert result.reason == "device_quarantined"
    assert "global.us.gov.ca.website" not in hub.aliases


def test_claim_bundle_alias_revoked_device_fails():
    hub = make_registry_hub()
    register_test_device(hub)
    create_alias_bundle(hub, "global.us.gov.ca")
    revoke_device(hub, "dev_CA_SITE", reason="test_revocation")

    result = claim_bundle_alias(
        hub,
        "global.us.gov.ca",
        "website",
        "dev_CA_SITE",
    )

    assert not result.success
    assert result.status == "rejected"
    assert result.reason == "device_revoked"
    assert "global.us.gov.ca.website" not in hub.aliases


def test_claim_bundle_alias_inactive_bundle_fails():
    hub = make_registry_hub()
    register_test_device(hub)
    create_alias_bundle(hub, "global.us.gov.ca")
    hub.alias_bundles["global.us.gov.ca"].status = "suspended"

    result = claim_bundle_alias(
        hub,
        "global.us.gov.ca",
        "website",
        "dev_CA_SITE",
    )

    assert not result.success
    assert result.status == "suspended"
    assert result.reason == "bundle_not_active"
    assert "global.us.gov.ca.website" not in hub.aliases


def test_bundle_alias_does_not_mutate_canonical_identity():
    hub = make_registry_hub()
    device, record = register_test_device(hub)
    original_label = record.current_label
    original_identity_chain = record.identity_chain
    original_passport_id = record.passport_id
    original_attachment = record.current_attachment
    create_alias_bundle(hub, "global.us.gov.ca")

    claim_bundle_alias(hub, "global.us.gov.ca", "website", "dev_CA_SITE")

    assert device.label == original_label
    assert record.current_label == original_label
    assert record.identity_chain == original_identity_chain
    assert record.full_identity_chain == original_identity_chain
    assert record.passport_id == original_passport_id
    assert record.current_attachment == original_attachment


def test_alias_bundle_scenario_runs():
    result = run_scenario(
        PROJECT_ROOT / "scenarios" / "030_alias_bundle_delegation.yaml"
    )

    assert result.passed
