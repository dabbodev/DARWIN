from darwin.models.device import Device
from darwin.models.hub import RegistryHub
from darwin.registry.alias_authority import claim_alias_through_authority_chain
from darwin.registry.aliases import claim_alias, claim_progressive_alias
from darwin.registry.operations import register_device
from darwin.registry.security import quarantine_device


def make_hub(
    hub_id: str,
    scope_path: str,
    parent_hub_id: str | None = None,
) -> RegistryHub:
    return RegistryHub(
        hub_id=hub_id,
        scope_path=scope_path,
        parent_hub_id=parent_hub_id,
    )


def register_test_device(
    hub: RegistryHub,
    device_id: str = "dev_A9F3",
    label: str = "server",
) -> None:
    register_device(hub, Device(device_id=device_id, label=label))


def test_claim_through_chain_approved_alias_creates_alias_on_parent():
    child = make_hub(
        "registry_child_001",
        "global.family.david",
        parent_hub_id="registry_global_001",
    )
    parent = make_hub("registry_global_001", "global")
    register_test_device(child)
    register_test_device(parent)

    result = claim_alias_through_authority_chain(
        {child.hub_id: child, parent.hub_id: parent},
        child.hub_id,
        "global.server",
        "server",
        "dev_A9F3",
    )

    assert result.success
    assert result.status == "claimed"
    assert result.granted_alias == "global.server"
    assert "global.server" in parent.aliases
    assert "global.server" not in child.aliases
    assert result.alias_record is parent.aliases["global.server"]
    assert result.alias_record.approved_by_registry_hub == parent.hub_id
    assert result.alias_record.authority_ceiling == "global"
    assert result.authority_path.final_status == "approved_here"


def test_claim_through_chain_fallback_creates_alias_at_authority_ceiling():
    hub = make_hub("registry_root_001", "global.us")
    register_test_device(hub)

    result = claim_alias_through_authority_chain(
        {hub.hub_id: hub},
        hub.hub_id,
        "global.server",
        "server",
        "dev_A9F3",
    )

    assert result.success
    assert result.status == "fallback_granted"
    assert result.reason == "insufficient_authority"
    assert result.granted_alias == "global.us.server"
    assert "global.server" not in hub.aliases
    assert result.alias_record is hub.aliases["global.us.server"]
    assert result.alias_record.requested_alias == "global.server"
    assert result.alias_record.granted_alias == "global.us.server"
    assert result.alias_record.fallback_reason == "insufficient_authority"
    assert result.alias_record.authority_ceiling == "global.us"


def test_claim_through_chain_name_taken_does_not_overwrite():
    child = make_hub(
        "registry_child_001",
        "global.family.david",
        parent_hub_id="registry_global_001",
    )
    parent = make_hub("registry_global_001", "global")
    register_test_device(child, "dev_B2C8")
    register_test_device(parent, "dev_A9F3")
    register_test_device(parent, "dev_B2C8")
    original = claim_alias(parent, "global.server", "dev_A9F3")

    result = claim_alias_through_authority_chain(
        {child.hub_id: child, parent.hub_id: parent},
        child.hub_id,
        "global.server",
        "server",
        "dev_B2C8",
    )

    assert original.success
    assert not result.success
    assert result.status == "conflict"
    assert result.reason == "alias_conflict"
    assert parent.aliases["global.server"] is original.alias_record
    assert parent.aliases["global.server"].target_device_id == "dev_A9F3"


def test_claim_through_chain_insufficient_authority_no_fallback_fails():
    hub = make_hub("registry_root_001", "global.us")
    register_test_device(hub)

    result = claim_alias_through_authority_chain(
        {hub.hub_id: hub},
        hub.hub_id,
        "global.server",
        "server",
        "dev_A9F3",
        fallback_allowed=False,
    )

    assert not result.success
    assert result.status == "rejected"
    assert result.reason == "insufficient_authority"
    assert not hub.aliases


def test_claim_through_chain_broken_parent_fails_without_alias():
    child = make_hub(
        "registry_child_001",
        "global.family.david",
        parent_hub_id="registry_missing",
    )
    register_test_device(child)

    result = claim_alias_through_authority_chain(
        {child.hub_id: child},
        child.hub_id,
        "global.server",
        "server",
        "dev_A9F3",
    )

    assert not result.success
    assert result.status == "authority_path_broken"
    assert result.reason == "parent_hub_not_found"
    assert not child.aliases


def test_claim_through_chain_device_blocked_fails_without_alias():
    child = make_hub(
        "registry_child_001",
        "global.family.david",
        parent_hub_id="registry_global_001",
    )
    parent = make_hub("registry_global_001", "global")
    register_test_device(child)
    register_test_device(parent)
    quarantine_device(child, "dev_A9F3", reason="test_quarantine")

    result = claim_alias_through_authority_chain(
        {child.hub_id: child, parent.hub_id: parent},
        child.hub_id,
        "global.server",
        "server",
        "dev_A9F3",
    )

    assert not result.success
    assert result.status == "rejected"
    assert result.reason == "device_quarantined"
    assert not child.aliases
    assert not parent.aliases


def test_claim_through_chain_records_authority_path():
    child = make_hub(
        "registry_home_001",
        "global.family.david.home",
        parent_hub_id="registry_family_001",
    )
    parent = make_hub(
        "registry_family_001",
        "global.family.david",
        parent_hub_id="registry_global_001",
    )
    grandparent = make_hub("registry_global_001", "global")
    hubs = {
        child.hub_id: child,
        parent.hub_id: parent,
        grandparent.hub_id: grandparent,
    }
    for hub in hubs.values():
        register_test_device(hub)

    result = claim_alias_through_authority_chain(
        hubs,
        child.hub_id,
        "global.server",
        "server",
        "dev_A9F3",
    )

    assert result.success
    assert result.authority_path.to_summary().path_hubs == [
        child.hub_id,
        parent.hub_id,
        grandparent.hub_id,
    ]
    assert [decision.decision for decision in result.authority_path.decisions] == [
        "continue_upward",
        "continue_upward",
        "approved_here",
    ]
    assert result.authority_path.final_status == "approved_here"
    assert result.authority_path.granted_alias == "global.server"


def test_claim_through_chain_does_not_mutate_on_failure():
    child = make_hub(
        "registry_child_001",
        "global.family.david",
        parent_hub_id="registry_global_001",
    )
    parent = make_hub("registry_global_001", "global")
    register_test_device(child, "dev_B2C8")
    register_test_device(parent, "dev_A9F3")
    register_test_device(parent, "dev_B2C8")
    claim_alias(parent, "global.server", "dev_A9F3")
    child_aliases_before = dict(child.aliases)
    parent_aliases_before = dict(parent.aliases)
    parent_conflicts_before = dict(parent.conflicts)

    result = claim_alias_through_authority_chain(
        {child.hub_id: child, parent.hub_id: parent},
        child.hub_id,
        "global.server",
        "server",
        "dev_B2C8",
    )

    assert not result.success
    assert child.aliases == child_aliases_before
    assert parent.aliases == parent_aliases_before
    assert parent.conflicts == parent_conflicts_before


def test_existing_direct_and_progressive_alias_still_work():
    hub = make_hub("registry_home_001", "global.family.david")
    register_test_device(hub)

    direct = claim_alias(hub, "david_phone", "dev_A9F3")
    progressive = claim_progressive_alias(
        hub,
        requested_alias="global.server",
        local_name="server",
        target_device_id="dev_A9F3",
    )

    assert direct.success
    assert direct.alias_record is hub.aliases["david_phone"]
    assert progressive.success
    assert progressive.status == "fallback_granted"
    assert progressive.alias_record is hub.aliases["global.family.david.server"]
