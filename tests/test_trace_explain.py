from copy import deepcopy

from darwin.models.device import Device
from darwin.models.hub import RegistryHub
from darwin.registry.alias_authority import claim_alias_through_authority_chain
from darwin.registry.aliases import claim_alias, release_alias
from darwin.registry.authority_audit import (
    build_authority_audit_trace,
    summarize_authority_path,
)
from darwin.registry.history_queries import (
    query_alias_conflicts,
    query_alias_history,
    query_quarantine_events,
)
from darwin.registry.operations import register_device
from darwin.registry.security import quarantine_device
from darwin.registry.trace_explain import (
    explain_alias_conflict_entry,
    explain_alias_history_entry,
    explain_authority_trace,
    explain_authority_traces,
    explain_quarantine_event_entry,
)


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


def test_explaining_empty_trace_list_returns_empty_list():
    assert explain_authority_traces([]) == []


def test_approved_authority_trace_explanation():
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

    explanation = explain_authority_trace(build_authority_audit_trace(parent)[0])

    assert explanation == {
        "category": "authority_trace",
        "outcome": "approved",
        "summary": "Alias global.server was approved at registry_global_001.",
        "reason": "approved_here",
        "requested_alias": "global.server",
        "granted_alias": "global.server",
        "target_device": "dev_A9F3",
        "authority_ceiling": "global",
        "path_hubs": ["registry_global_001"],
    }


def test_fallback_authority_trace_explanation():
    hub = make_hub("registry_us_001", "global.us")
    register_test_device(hub)

    claim_alias_through_authority_chain(
        {hub.hub_id: hub},
        hub.hub_id,
        "global.server",
        "server",
        "dev_A9F3",
    )

    explanation = explain_authority_trace(build_authority_audit_trace(hub)[0])

    assert explanation["outcome"] == "fallback"
    assert explanation["reason"] == "fallback_granted"
    assert (
        explanation["summary"]
        == "Alias global.server fell back to global.us.server at registry_us_001."
    )
    assert explanation["granted_alias"] == "global.us.server"


def test_conflict_name_taken_authority_trace_explanation():
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

    explanation = explain_authority_trace(summarize_authority_path(result.authority_path))

    assert explanation["outcome"] == "conflict"
    assert explanation["reason"] == "name_taken"
    assert explanation["summary"] == (
        "Alias global.server was denied because it was already taken."
    )
    assert explanation["path_hubs"] == ["registry_child_001", "registry_global_001"]


def test_policy_denied_authority_trace_explanation():
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

    explanation = explain_authority_trace(summarize_authority_path(result.authority_path))

    assert explanation["outcome"] == "policy_denied"
    assert explanation["reason"] == "policy_denied"
    assert explanation["summary"] == (
        "Alias global.server was denied by simulator-local policy."
    )


def test_broken_parent_authority_trace_explanation():
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

    explanation = explain_authority_trace(summarize_authority_path(result.authority_path))

    assert explanation["outcome"] == "path_broken"
    assert explanation["reason"] == "authority_path_broken"
    assert explanation["summary"] == (
        "Alias global.server could not be evaluated because the authority path was broken."
    )


def test_unknown_or_partial_authority_trace_explanation():
    assert explain_authority_trace({}) == {
        "category": "authority_trace",
        "outcome": "partial",
        "summary": "Alias <unknown> has an incomplete authority trace.",
        "reason": "partial",
        "requested_alias": None,
        "granted_alias": None,
        "target_device": None,
        "authority_ceiling": None,
        "path_hubs": [],
    }


def test_alias_claim_and_release_history_explanations():
    hub = make_hub("registry_home_001", "global.family.david.home")
    register_test_device(hub)
    claim_alias(hub, "global.family.david.home.server", "dev_A9F3")

    claimed = explain_alias_history_entry(query_alias_history(hub)[0])

    assert claimed == {
        "category": "alias_history",
        "outcome": "claimed",
        "summary": "Alias global.family.david.home.server was claimed for dev_A9F3.",
        "reason": "alias_claimed",
        "alias": "global.family.david.home.server",
        "target_device": "dev_A9F3",
        "status": "active",
        "approved_by_registry_hub": "registry_home_001",
        "requested_alias": "global.family.david.home.server",
        "granted_alias": "global.family.david.home.server",
    }

    release_alias(hub, "global.family.david.home.server")
    released = explain_alias_history_entry(query_alias_history(hub)[0])

    assert released["outcome"] == "released"
    assert released["summary"] == "Alias global.family.david.home.server was released."


def test_alias_conflict_explanation():
    hub = make_hub("registry_home_001", "global.family.david.home")
    register_test_device(hub, "dev_A9F3")
    register_test_device(hub, "dev_B2C8")
    claim_alias(hub, "shared", "dev_A9F3")
    claim_alias(hub, "shared", "dev_B2C8")

    explanation = explain_alias_conflict_entry(query_alias_conflicts(hub)[0])

    assert explanation == {
        "category": "alias_conflict",
        "outcome": "conflict",
        "summary": "Alias shared conflict was observed between dev_A9F3 and dev_B2C8.",
        "reason": "alias_conflict",
        "conflict_id": "alias_conflict:shared:dev_B2C8",
        "alias": "shared",
        "existing_device": "dev_A9F3",
        "requesting_device": "dev_B2C8",
        "status": "pending_resolution",
    }


def test_quarantine_event_explanation():
    hub = make_hub("registry_home_001", "global.family.david.home")
    register_test_device(hub)
    quarantine_device(
        hub,
        "dev_A9F3",
        reason="rolling_proof_failed",
        source_hub_id="hub_guest_001",
        current_time=42,
    )

    explanation = explain_quarantine_event_entry(query_quarantine_events(hub)[0])

    assert explanation == {
        "category": "quarantine_event",
        "outcome": "observed",
        "summary": "Device dev_A9F3 was quarantined for rolling_proof_failed.",
        "reason": "rolling_proof_failed",
        "quarantine_key": "dev_A9F3",
        "device_id": "dev_A9F3",
        "source_hub_id": "hub_guest_001",
        "status": "active",
        "event_type": "device_quarantined",
    }


def test_trace_explanations_are_deterministic_and_read_only():
    hub = make_hub("registry_us_001", "global.us")
    register_test_device(hub)
    claim_alias_through_authority_chain(
        {hub.hub_id: hub},
        hub.hub_id,
        "global.server",
        "server",
        "dev_A9F3",
    )
    trace = build_authority_audit_trace(hub)[0]
    history = query_alias_history(hub)[0]
    before = {
        "hub": deepcopy(hub),
        "trace": deepcopy(trace),
        "history": deepcopy(history.to_dict()),
    }

    first_trace_explanation = explain_authority_trace(trace)
    second_trace_explanation = explain_authority_trace(trace)
    first_history_explanation = explain_alias_history_entry(history)
    second_history_explanation = explain_alias_history_entry(history)

    assert first_trace_explanation == second_trace_explanation
    assert first_history_explanation == second_history_explanation
    assert hub == before["hub"]
    assert trace == before["trace"]
    assert history.to_dict() == before["history"]
