from copy import deepcopy

from darwin.models.device import Device
from darwin.models.hub import RegistryHub
from darwin.registry.alias_authority import (
    claim_alias_through_authority_chain,
    evaluate_alias_authority_chain,
)
from darwin.registry.aliases import claim_alias
from darwin.registry.authority_audit import (
    build_authority_audit_trace,
    summarize_authority_decision,
    summarize_authority_path,
)
from darwin.registry.operations import register_device


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


def test_authority_audit_trace_returns_empty_list_without_retained_grants():
    hub = make_hub("registry_home_001", "global.family.david.home")

    assert build_authority_audit_trace(hub) == []


def test_successful_authority_chain_claim_can_be_summarized_from_retained_grant():
    child = make_hub(
        "registry_child_001",
        "global.family.david",
        parent_hub_id="registry_global_001",
    )
    parent = make_hub("registry_global_001", "global")
    register_test_device(child)
    register_test_device(parent)

    claim_alias_through_authority_chain(
        {child.hub_id: child, parent.hub_id: parent},
        child.hub_id,
        "global.server",
        "server",
        "dev_A9F3",
    )

    traces = build_authority_audit_trace(parent)

    assert traces == [
        {
            "requested_alias": "global.server",
            "granted_alias": "global.server",
            "target_device": "dev_A9F3",
            "final_status": "approved_here",
            "status": "active",
            "reason": None,
            "authority_ceiling": "global",
            "decision_count": 1,
            "path_hubs": ["registry_global_001"],
            "decisions": [
                {
                    "hub_id": "registry_global_001",
                    "scope_path": "global",
                    "status": "approved_here",
                    "reason": None,
                    "alias": "global.server",
                    "fallback_alias": None,
                    "authority_ceiling": "global",
                }
            ],
            "fallback_used": False,
            "conflict_detected": False,
            "policy_denied": False,
            "path_broken": False,
            "summary": "approved at registry_global_001",
        }
    ]


def test_fallback_authority_chain_claim_can_be_summarized_from_retained_grant():
    hub = make_hub("registry_us_001", "global.us")
    register_test_device(hub)

    claim_alias_through_authority_chain(
        {hub.hub_id: hub},
        hub.hub_id,
        "global.server",
        "server",
        "dev_A9F3",
    )

    traces = build_authority_audit_trace(hub)

    assert len(traces) == 1
    assert traces[0]["requested_alias"] == "global.server"
    assert traces[0]["granted_alias"] == "global.us.server"
    assert traces[0]["final_status"] == "fallback_granted"
    assert traces[0]["reason"] == "insufficient_authority"
    assert traces[0]["fallback_used"] is True
    assert traces[0]["summary"] == "fallback granted at registry_us_001"
    assert traces[0]["decisions"][0]["fallback_alias"] == "global.us.server"


def test_authority_path_summary_includes_name_taken_outcome():
    child = make_hub(
        "registry_child_001",
        "global.family.david",
        parent_hub_id="registry_global_001",
    )
    parent = make_hub("registry_global_001", "global")
    register_test_device(child)
    register_test_device(parent)
    claim_alias(parent, "global.server", "dev_A9F3")

    result = claim_alias_through_authority_chain(
        {child.hub_id: child, parent.hub_id: parent},
        child.hub_id,
        "global.server",
        "server",
        "dev_A9F3",
    )

    summary = summarize_authority_path(result.authority_path)

    assert result.success is False
    assert build_authority_audit_trace(parent, requested_alias="global.server") == [
        {
            "requested_alias": "global.server",
            "granted_alias": "global.server",
            "target_device": "dev_A9F3",
            "final_status": "approved_here",
            "status": "active",
            "reason": None,
            "authority_ceiling": "global",
            "decision_count": 1,
            "path_hubs": ["registry_global_001"],
            "decisions": [
                {
                    "hub_id": "registry_global_001",
                    "scope_path": "global",
                    "status": "approved_here",
                    "reason": None,
                    "alias": "global.server",
                    "fallback_alias": None,
                    "authority_ceiling": "global",
                }
            ],
            "fallback_used": False,
            "conflict_detected": False,
            "policy_denied": False,
            "path_broken": False,
            "summary": "approved at registry_global_001",
        }
    ]
    assert summary["final_status"] == "name_taken"
    assert summary["conflict_detected"] is True
    assert summary["summary"] == "denied because alias was already taken"
    assert summary["path_hubs"] == ["registry_child_001", "registry_global_001"]


def test_authority_path_summary_includes_policy_denied_outcome():
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

    summary = summarize_authority_path(result.authority_path)

    assert build_authority_audit_trace(parent) == []
    assert summary["final_status"] == "policy_denied"
    assert summary["policy_denied"] is True
    assert summary["reason"] == "pass_up_denied_by_policy"
    assert summary["summary"] == "denied by simulator-local policy"


def test_authority_path_summary_includes_broken_parent_outcome():
    child = make_hub(
        "registry_child_001",
        "global.family.david",
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

    summary = summarize_authority_path(result.authority_path)

    assert build_authority_audit_trace(child) == []
    assert summary["final_status"] == "authority_path_broken"
    assert summary["path_broken"] is True
    assert summary["reason"] == "parent_hub_not_found"
    assert summary["summary"] == "authority path broken at registry_missing_001"


def test_authority_audit_trace_filters_by_requested_granted_device_and_final_status():
    hub = make_hub("registry_us_001", "global.us")
    register_test_device(hub, "dev_A9F3")
    register_test_device(hub, "dev_B2C8")

    claim_alias_through_authority_chain(
        {hub.hub_id: hub},
        hub.hub_id,
        "global.alpha",
        "alpha",
        "dev_A9F3",
    )
    claim_alias_through_authority_chain(
        {hub.hub_id: hub},
        hub.hub_id,
        "global.beta",
        "beta",
        "dev_B2C8",
    )

    assert [
        trace["granted_alias"]
        for trace in build_authority_audit_trace(
            hub,
            requested_alias="global.alpha",
        )
    ] == ["global.us.alpha"]
    assert [
        trace["requested_alias"]
        for trace in build_authority_audit_trace(
            hub,
            granted_alias="global.us.beta",
        )
    ] == ["global.beta"]
    assert [
        trace["requested_alias"]
        for trace in build_authority_audit_trace(
            hub,
            device_id="dev_A9F3",
            final_status="fallback_granted",
        )
    ] == ["global.alpha"]
    assert build_authority_audit_trace(hub, final_status="approved_here") == []


def test_authority_audit_trace_ordering_is_deterministic_by_granted_alias():
    hub = make_hub("registry_us_001", "global.us")
    register_test_device(hub, "dev_A9F3")
    register_test_device(hub, "dev_B2C8")

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
        "dev_B2C8",
    )

    assert [
        trace["granted_alias"] for trace in build_authority_audit_trace(hub)
    ] == [
        "global.us.alpha",
        "global.us.zeta",
    ]


def test_authority_audit_helpers_do_not_mutate_registry_or_paths():
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
    claim_alias_through_authority_chain(
        {child.hub_id: child, parent.hub_id: parent},
        child.hub_id,
        "global.server",
        "server",
        "dev_A9F3",
    )
    before = {
        "child": deepcopy(child),
        "parent": deepcopy(parent),
        "path": deepcopy(path.to_dict()),
    }

    summarize_authority_decision(path.decisions[0])
    summarize_authority_path(path)
    build_authority_audit_trace(parent)

    assert child == before["child"]
    assert parent == before["parent"]
    assert path.to_dict() == before["path"]
