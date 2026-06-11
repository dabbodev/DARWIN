import json
from copy import deepcopy

from darwin.models.device import Device
from darwin.models.hub import RegistryHub
from darwin.registry.alias_authority import claim_alias_through_authority_chain
from darwin.registry.aliases import claim_alias, resolve_alias
from darwin.registry.authority_audit import summarize_authority_path
from darwin.registry.operations import register_device
from darwin.registry.trace_explain import explain_authority_trace


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


def register_test_device(
    hub: RegistryHub,
    device_id: str = "dev_A9F3",
    label: str = "server",
) -> None:
    register_device(hub, Device(device_id=device_id, label=label))


def test_registry_hub_authority_outcome_history_defaults_to_empty():
    hub = make_hub("registry_home_001", "global.family.david.home")

    assert hub.authority_outcome_history == []


def test_successful_authority_chain_claim_retains_outcome_on_requesting_hub():
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
    assert parent.authority_outcome_history == []
    assert len(child.authority_outcome_history) == 1
    record = child.authority_outcome_history[0]
    assert record.requested_alias == "global.server"
    assert record.granted_alias == "global.server"
    assert record.target_device == "dev_A9F3"
    assert record.requesting_hub == "registry_child_001"
    assert record.final_status == "approved_here"
    assert record.status == "claimed"
    assert record.reason is None
    assert record.authority_ceiling == "global"
    assert record.decision_count == 2
    assert record.path_hubs == ("registry_child_001", "registry_global_001")
    assert record.fallback_used is False
    assert record.conflict_detected is False
    assert record.policy_denied is False
    assert record.path_broken is False


def test_fallback_authority_chain_claim_retains_outcome():
    hub = make_hub("registry_us_001", "global.us")
    register_test_device(hub)

    claim_alias_through_authority_chain(
        {hub.hub_id: hub},
        hub.hub_id,
        "global.server",
        "server",
        "dev_A9F3",
    )

    record = hub.authority_outcome_history[0]
    assert record.requested_alias == "global.server"
    assert record.granted_alias == "global.us.server"
    assert record.final_status == "fallback_granted"
    assert record.status == "fallback_granted"
    assert record.reason == "insufficient_authority"
    assert record.authority_ceiling == "global.us"
    assert record.decision_count == 1
    assert record.path_hubs == ("registry_us_001",)
    assert record.fallback_used is True


def test_name_taken_authority_chain_claim_retains_conflict_outcome():
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

    result = claim_alias_through_authority_chain(
        {child.hub_id: child, parent.hub_id: parent},
        child.hub_id,
        "global.server",
        "server",
        "dev_B2C8",
    )

    assert not result.success
    record = child.authority_outcome_history[0]
    assert record.granted_alias is None
    assert record.final_status == "name_taken"
    assert record.status == "conflict"
    assert record.reason == "alias_conflict"
    assert record.conflict_detected is True
    assert record.path_hubs == ("registry_child_001", "registry_global_001")


def test_policy_denied_authority_chain_claim_retains_outcome():
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

    result = claim_alias_through_authority_chain(
        {child.hub_id: child, parent.hub_id: parent},
        child.hub_id,
        "global.server",
        "server",
        "dev_A9F3",
    )

    assert not result.success
    record = child.authority_outcome_history[0]
    assert record.final_status == "policy_denied"
    assert record.status == "rejected"
    assert record.reason == "pass_up_denied_by_policy"
    assert record.authority_ceiling == "global.family.david"
    assert record.policy_denied is True
    assert record.path_broken is False


def test_broken_parent_authority_chain_claim_retains_outcome():
    child = make_hub(
        "registry_child_001",
        "global.family.david.home",
        parent_hub_id="registry_missing_001",
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
    record = child.authority_outcome_history[0]
    assert record.final_status == "authority_path_broken"
    assert record.status == "authority_path_broken"
    assert record.reason == "parent_hub_not_found"
    assert record.authority_ceiling == "global.family.david.home"
    assert record.path_hubs == ("registry_child_001", "registry_missing_001")
    assert record.path_broken is True


def test_retained_outcome_summary_is_deterministic_and_json_safe():
    hub = make_hub("registry_us_001", "global.us")
    register_test_device(hub)

    claim_alias_through_authority_chain(
        {hub.hub_id: hub},
        hub.hub_id,
        "global.server",
        "server",
        "dev_A9F3",
    )

    summary = hub.authority_outcome_history[0].to_summary()
    assert summary == hub.authority_outcome_history[0].to_dict()
    assert summary["record_id"] == "authority_outcome:registry_us_001:0001"
    assert summary["path_hubs"] == ["registry_us_001"]
    assert summary["decisions"][0]["decision"] == "fallback_available"
    json.dumps(summary, sort_keys=True)


def test_retention_append_order_is_deterministic():
    hub = make_hub("registry_us_001", "global.us")
    register_test_device(hub)

    claim_alias_through_authority_chain(
        {hub.hub_id: hub},
        hub.hub_id,
        "global.zeta",
        "zeta",
        "dev_A9F3",
    )
    claim_alias_through_authority_chain(
        {hub.hub_id: hub},
        hub.hub_id,
        "global.alpha",
        "alpha",
        "dev_A9F3",
    )

    assert [
        record.record_id for record in hub.authority_outcome_history
    ] == [
        "authority_outcome:registry_us_001:0001",
        "authority_outcome:registry_us_001:0002",
    ]
    assert [
        record.requested_alias for record in hub.authority_outcome_history
    ] == [
        "global.zeta",
        "global.alpha",
    ]


def test_retention_does_not_mutate_authority_path_or_existing_explanation():
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

    result = claim_alias_through_authority_chain(
        {child.hub_id: child, parent.hub_id: parent},
        child.hub_id,
        "global.server",
        "server",
        "dev_A9F3",
    )
    before_path = deepcopy(result.authority_path.to_dict())

    explanation = explain_authority_trace(summarize_authority_path(result.authority_path))

    assert result.authority_path.to_dict() == before_path
    assert explanation["outcome"] == "policy_denied"
    assert explanation["summary"] == (
        "Alias global.server was denied by simulator-local policy."
    )


def test_retention_does_not_change_alias_resolution_or_identity_chain():
    hub = make_hub("registry_us_001", "global.us")
    register_test_device(hub)

    result = claim_alias_through_authority_chain(
        {hub.hub_id: hub},
        hub.hub_id,
        "global.server",
        "server",
        "dev_A9F3",
    )
    resolved = resolve_alias(hub, "global.us.server")

    assert result.success
    assert resolved.success
    assert resolved.target_device_id == "dev_A9F3"
    assert resolved.target_identity_chain == "global.us.server"
    assert hub.devices["dev_A9F3"].identity_chain == "global.us.server"
