from darwin.models.device import Device
from darwin.models.hub import RegistryHub
from darwin.registry.alias_authority import evaluate_alias_authority_chain
from darwin.registry.aliases import claim_alias
from darwin.registry.operations import register_device
from darwin.registry.security import quarantine_device


def make_hub(
    hub_id: str,
    scope_path: str,
    parent_hub_id: str | None = None,
    alias_authority_policy: dict[str, object] | None = None,
) -> RegistryHub:
    return RegistryHub(
        hub_id=hub_id,
        scope_path=scope_path,
        parent_hub_id=parent_hub_id,
        alias_authority_policy=(
            {} if alias_authority_policy is None else alias_authority_policy
        ),
    )


def register_test_device(hub: RegistryHub, device_id: str = "dev_A9F3") -> None:
    register_device(hub, Device(device_id=device_id, label="server"))


def test_authority_chain_start_hub_not_found():
    path = evaluate_alias_authority_chain(
        {},
        "registry_missing",
        "global.server",
        "server",
        "dev_A9F3",
    )

    assert path.final_status == "authority_path_broken"
    assert len(path.decisions) == 1
    assert path.decisions[0].reason == "start_hub_not_found"


def test_authority_chain_approves_at_start_hub():
    hub = make_hub("registry_home_001", "global.family.david")
    register_test_device(hub)

    path = evaluate_alias_authority_chain(
        {hub.hub_id: hub},
        hub.hub_id,
        "global.family.david.server",
        "server",
        "dev_A9F3",
    )

    assert len(path.decisions) == 1
    assert path.final_status == "approved_here"
    assert path.granted_alias == "global.family.david.server"
    assert path.authority_ceiling == "global.family.david"


def test_authority_chain_continues_to_parent_and_approves():
    child = make_hub(
        "registry_child_001",
        "global.family.david",
        parent_hub_id="registry_global_001",
    )
    parent = make_hub("registry_global_001", "global")
    register_test_device(child)
    register_test_device(parent)

    path = evaluate_alias_authority_chain(
        {child.hub_id: child, parent.hub_id: parent},
        child.hub_id,
        "global.server",
        "server",
        "dev_A9F3",
    )

    assert [decision.decision for decision in path.decisions] == [
        "continue_upward",
        "approved_here",
    ]
    assert [decision.hub_id for decision in path.decisions] == [
        child.hub_id,
        parent.hub_id,
    ]
    assert path.final_status == "approved_here"
    assert path.granted_alias == "global.server"
    assert path.authority_ceiling == "global"


def test_authority_chain_empty_policy_preserves_parent_approval():
    child = make_hub(
        "registry_child_001",
        "global.family.david",
        parent_hub_id="registry_global_001",
        alias_authority_policy={},
    )
    parent = make_hub(
        "registry_global_001",
        "global",
        alias_authority_policy={},
    )
    register_test_device(child)
    register_test_device(parent)

    path = evaluate_alias_authority_chain(
        {child.hub_id: child, parent.hub_id: parent},
        child.hub_id,
        "global.server",
        "server",
        "dev_A9F3",
    )

    assert [decision.decision for decision in path.decisions] == [
        "continue_upward",
        "approved_here",
    ]
    assert path.final_status == "approved_here"
    assert path.granted_alias == "global.server"


def test_authority_chain_fallback_at_root_without_parent():
    hub = make_hub("registry_root_001", "global.us")
    register_test_device(hub)

    path = evaluate_alias_authority_chain(
        {hub.hub_id: hub},
        hub.hub_id,
        "global.server",
        "server",
        "dev_A9F3",
    )

    assert len(path.decisions) == 1
    assert path.decisions[0].decision == "fallback_available"
    assert path.final_status == "fallback_granted"
    assert path.granted_alias == "global.us.server"
    assert path.authority_ceiling == "global.us"


def test_authority_chain_without_fallback_rejects():
    hub = make_hub("registry_root_001", "global.us")
    register_test_device(hub)

    path = evaluate_alias_authority_chain(
        {hub.hub_id: hub},
        hub.hub_id,
        "global.server",
        "server",
        "dev_A9F3",
        fallback_allowed=False,
    )

    assert len(path.decisions) == 1
    assert path.final_status == "insufficient_authority"
    assert path.granted_alias is None
    assert path.authority_ceiling == "global.us"


def test_authority_chain_broken_parent_path():
    child = make_hub(
        "registry_child_001",
        "global.family.david",
        parent_hub_id="registry_missing",
    )
    register_test_device(child)

    path = evaluate_alias_authority_chain(
        {child.hub_id: child},
        child.hub_id,
        "global.server",
        "server",
        "dev_A9F3",
    )

    assert [decision.decision for decision in path.decisions] == [
        "continue_upward",
        "authority_path_broken",
    ]
    assert path.decisions[-1].hub_id == "registry_missing"
    assert path.decisions[-1].reason == "parent_hub_not_found"
    assert path.final_status == "authority_path_broken"


def test_authority_chain_policy_can_stop_pass_up_with_fallback():
    child = make_hub(
        "registry_child_001",
        "global.family.david.home",
        parent_hub_id="registry_family_001",
    )
    parent = make_hub(
        "registry_family_001",
        "global.family.david",
        parent_hub_id="registry_global_001",
        alias_authority_policy={
            "allow_pass_up": False,
            "allow_fallback": True,
        },
    )
    register_test_device(child)
    register_test_device(parent)

    path = evaluate_alias_authority_chain(
        {child.hub_id: child, parent.hub_id: parent},
        child.hub_id,
        "global.server",
        "server",
        "dev_A9F3",
    )

    assert [decision.decision for decision in path.decisions] == [
        "continue_upward",
        "fallback_available",
    ]
    assert path.decisions[-1].reason == "pass_up_denied_by_policy"
    assert path.final_status == "fallback_granted"
    assert path.granted_alias == "global.family.david.server"


def test_authority_chain_policy_can_deny_pass_up_and_fallback():
    child = make_hub(
        "registry_child_001",
        "global.family.david.home",
        parent_hub_id="registry_family_001",
    )
    parent = make_hub(
        "registry_family_001",
        "global.family.david",
        parent_hub_id="registry_global_001",
        alias_authority_policy={
            "allow_pass_up": False,
            "allow_fallback": False,
        },
    )
    register_test_device(child)
    register_test_device(parent)

    path = evaluate_alias_authority_chain(
        {child.hub_id: child, parent.hub_id: parent},
        child.hub_id,
        "global.server",
        "server",
        "dev_A9F3",
    )

    assert [decision.decision for decision in path.decisions] == [
        "continue_upward",
        "policy_denied",
    ]
    assert path.decisions[-1].reason == "pass_up_denied_by_policy"
    assert path.final_status == "policy_denied"
    assert path.granted_alias is None
    assert path.authority_ceiling == "global.family.david"


def test_authority_chain_policy_can_deny_approval():
    hub = make_hub(
        "registry_global_001",
        "global",
        alias_authority_policy={"allow_approval": False},
    )
    register_test_device(hub)

    path = evaluate_alias_authority_chain(
        {hub.hub_id: hub},
        hub.hub_id,
        "global.server",
        "server",
        "dev_A9F3",
    )

    assert len(path.decisions) == 1
    assert path.decisions[0].decision == "policy_denied"
    assert path.decisions[0].reason == "approval_denied_by_policy"
    assert path.final_status == "policy_denied"
    assert path.granted_alias is None
    assert path.authority_ceiling == "global"


def test_authority_chain_name_taken_stops():
    child = make_hub(
        "registry_child_001",
        "global.family.david",
        parent_hub_id="registry_global_001",
    )
    parent = make_hub("registry_global_001", "global")
    register_test_device(child)
    register_test_device(parent)
    claim_alias(parent, "global.server", "dev_A9F3")

    path = evaluate_alias_authority_chain(
        {child.hub_id: child, parent.hub_id: parent},
        child.hub_id,
        "global.server",
        "server",
        "dev_A9F3",
    )

    assert [decision.decision for decision in path.decisions] == [
        "continue_upward",
        "name_taken",
    ]
    assert path.final_status == "name_taken"
    assert path.decisions[-1].reason == "alias_conflict"


def test_authority_chain_device_blocked_stops_before_parent():
    child = make_hub(
        "registry_child_001",
        "global.family.david",
        parent_hub_id="registry_global_001",
    )
    parent = make_hub("registry_global_001", "global")
    register_test_device(child)
    register_test_device(parent)
    quarantine_device(child, "dev_A9F3", reason="test_quarantine")

    path = evaluate_alias_authority_chain(
        {child.hub_id: child, parent.hub_id: parent},
        child.hub_id,
        "global.server",
        "server",
        "dev_A9F3",
    )

    assert len(path.decisions) == 1
    assert path.final_status == "device_blocked"
    assert path.decisions[0].reason == "device_quarantined"


def test_authority_chain_unknown_device_stops_before_parent():
    child = make_hub(
        "registry_child_001",
        "global.family.david",
        parent_hub_id="registry_global_001",
    )
    parent = make_hub("registry_global_001", "global")
    register_test_device(parent)

    path = evaluate_alias_authority_chain(
        {child.hub_id: child, parent.hub_id: parent},
        child.hub_id,
        "global.server",
        "server",
        "dev_missing",
    )

    assert len(path.decisions) == 1
    assert path.final_status == "device_blocked"
    assert path.decisions[0].reason == "unknown_device"


def test_authority_chain_does_not_mutate_aliases():
    child = make_hub(
        "registry_child_001",
        "global.family.david",
        parent_hub_id="registry_global_001",
    )
    parent = make_hub("registry_global_001", "global")
    register_test_device(child)
    register_test_device(parent)
    claim_alias(parent, "global.existing", "dev_A9F3")
    child_aliases_before = dict(child.aliases)
    parent_aliases_before = dict(parent.aliases)

    evaluate_alias_authority_chain(
        {child.hub_id: child, parent.hub_id: parent},
        child.hub_id,
        "global.server",
        "server",
        "dev_A9F3",
    )

    assert child.aliases == child_aliases_before
    assert parent.aliases == parent_aliases_before


def test_authority_chain_summary_contains_path_hubs():
    child = make_hub(
        "registry_child_001",
        "global.family.david",
        parent_hub_id="registry_global_001",
    )
    parent = make_hub("registry_global_001", "global")
    register_test_device(child)
    register_test_device(parent)

    path = evaluate_alias_authority_chain(
        {child.hub_id: child, parent.hub_id: parent},
        child.hub_id,
        "global.server",
        "server",
        "dev_A9F3",
    )

    summary = path.to_summary()

    assert summary.path_hubs == [child.hub_id, parent.hub_id]
    assert summary.decision_count == 2
