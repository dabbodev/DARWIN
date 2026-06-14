import json
from copy import deepcopy

from darwin.models.device import Device
from darwin.models.hub import RegistryHub
from darwin.registry.alias_authority import claim_alias_through_authority_chain
from darwin.registry.aliases import claim_alias
from darwin.registry.history_queries import query_authority_outcomes
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


def register_test_device(
    hub: RegistryHub,
    device_id: str = "dev_A9F3",
    label: str = "server",
) -> None:
    register_device(hub, Device(device_id=device_id, label=label))


def test_authority_outcome_query_returns_empty_list_without_retained_outcomes():
    hub = make_hub("registry_home_001", "global.family.david.home")

    assert query_authority_outcomes(hub) == []
    assert query_authority_outcomes(hub, requested_alias="global.server") == []


def test_authority_outcomes_can_be_queried_by_requested_alias():
    hub = build_query_hub()

    results = query_authority_outcomes(
        hub,
        requested_alias="global.family.david.home.server",
    )

    assert len(results) == 1
    assert results[0].requested_alias == "global.family.david.home.server"
    assert results[0].final_status == "approved_here"


def test_authority_outcomes_can_be_queried_by_granted_alias():
    hub = build_query_hub()

    results = query_authority_outcomes(
        hub,
        granted_alias="global.family.david.server",
    )

    assert len(results) == 1
    assert results[0].requested_alias == "global.server"
    assert results[0].fallback_used is True


def test_authority_outcomes_can_be_queried_by_device_id():
    hub = build_query_hub()

    results = query_authority_outcomes(hub, device_id="dev_A9F3")

    assert [result.target_device for result in results] == ["dev_A9F3"] * 5
    assert query_authority_outcomes(hub, device_id="dev_missing") == []


def test_authority_outcomes_can_be_queried_by_requesting_hub():
    hub = build_query_hub()

    results = query_authority_outcomes(hub, requesting_hub="registry_child_001")

    assert len(results) == 5
    assert {result.requesting_hub for result in results} == {"registry_child_001"}


def test_authority_outcomes_can_be_queried_by_final_status():
    hub = build_query_hub()

    results = query_authority_outcomes(hub, final_status="name_taken")

    assert len(results) == 1
    assert results[0].status == "conflict"
    assert results[0].conflict_detected is True


def test_authority_outcomes_can_be_queried_by_status():
    hub = build_query_hub()

    results = query_authority_outcomes(hub, status="fallback_granted")

    assert len(results) == 1
    assert results[0].final_status == "fallback_granted"
    assert results[0].granted_alias == "global.family.david.server"


def test_authority_outcomes_can_be_queried_by_reason():
    hub = build_query_hub()

    results = query_authority_outcomes(hub, reason="alias_conflict")

    assert len(results) == 1
    assert results[0].requested_alias == "global.family.david.taken"
    assert results[0].final_status == "name_taken"


def test_authority_outcomes_can_be_queried_by_authority_ceiling():
    hub = build_query_hub()

    results = query_authority_outcomes(hub, authority_ceiling="global.family.david")

    assert [result.final_status for result in results] == [
        "fallback_granted",
        "name_taken",
        "policy_denied",
    ]


def test_authority_outcomes_can_be_queried_by_fallback_used():
    hub = build_query_hub()

    results = query_authority_outcomes(hub, fallback_used=True)

    assert [result.requested_alias for result in results] == ["global.server"]


def test_authority_outcomes_can_be_queried_by_conflict_detected():
    hub = build_query_hub()

    results = query_authority_outcomes(hub, conflict_detected=True)

    assert [result.final_status for result in results] == ["name_taken"]


def test_authority_outcomes_can_be_queried_by_policy_denied():
    hub = build_query_hub()

    results = query_authority_outcomes(hub, policy_denied=True)

    assert [result.final_status for result in results] == ["policy_denied"]


def test_authority_outcomes_can_be_queried_by_path_broken():
    hub = build_query_hub()

    results = query_authority_outcomes(hub, path_broken=True)

    assert [result.final_status for result in results] == ["authority_path_broken"]
    assert results[0].reason == "parent_hub_not_found"


def test_authority_outcome_filters_are_additive():
    hub = build_query_hub()

    results = query_authority_outcomes(
        hub,
        requested_alias="global.server",
        final_status="fallback_granted",
        fallback_used=True,
    )
    no_matches = query_authority_outcomes(
        hub,
        requested_alias="global.server",
        final_status="approved_here",
    )

    assert [result.granted_alias for result in results] == [
        "global.family.david.server"
    ]
    assert no_matches == []


def test_authority_outcome_query_preserves_append_order():
    hub = build_query_hub()

    assert [result.requested_alias for result in query_authority_outcomes(hub)] == [
        "global.family.david.home.server",
        "global.server",
        "global.family.david.taken",
        "global.other.blocked",
        "global.missing.path",
    ]


def test_authority_outcome_query_result_is_json_safe():
    hub = build_query_hub()

    summary = query_authority_outcomes(hub, fallback_used=True)[0].to_dict()

    assert summary == {
        "record_id": "authority_outcome:registry_child_001:0002",
        "requested_alias": "global.server",
        "granted_alias": "global.family.david.server",
        "target_device": "dev_A9F3",
        "requesting_hub": "registry_child_001",
        "authority_ceiling": "global.family.david",
        "final_status": "fallback_granted",
        "status": "fallback_granted",
        "reason": "insufficient_authority",
        "decision_count": 2,
        "path_hubs": ["registry_child_001", "registry_family_001"],
        "decisions": [
            {
                "hub_id": "registry_child_001",
                "scope_path": "global.family.david.home",
                "decision": "continue_upward",
                "reason": "insufficient_authority",
                "alias": "global.server",
                "fallback_alias": None,
                "authority_ceiling": "global.family.david.home",
                "can_continue_upward": True,
            },
            {
                "hub_id": "registry_family_001",
                "scope_path": "global.family.david",
                "decision": "fallback_available",
                "reason": "insufficient_authority",
                "alias": "global.server",
                "fallback_alias": "global.family.david.server",
                "authority_ceiling": "global.family.david",
                "can_continue_upward": False,
            },
        ],
        "fallback_used": True,
        "conflict_detected": False,
        "policy_denied": False,
        "path_broken": False,
    }
    json.dumps(summary, sort_keys=True)


def test_authority_outcome_queries_do_not_mutate_retained_history_or_hub_state():
    hub = build_query_hub()
    before = _hub_history_state(hub)

    results = query_authority_outcomes(hub)
    results[0].to_dict()["decisions"][0]["reason"] = "mutated_copy"

    assert _hub_history_state(hub) == before


def test_all_retained_authority_outcome_types_can_be_queried():
    hub = build_query_hub()

    assert query_authority_outcomes(hub, final_status="approved_here")
    assert query_authority_outcomes(hub, final_status="fallback_granted")
    assert query_authority_outcomes(hub, final_status="name_taken")
    assert query_authority_outcomes(hub, final_status="policy_denied")
    assert query_authority_outcomes(hub, final_status="authority_path_broken")


def build_query_hub() -> RegistryHub:
    child = make_hub(
        "registry_child_001",
        "global.family.david.home",
        parent_hub_id="registry_family_001",
    )
    parent = make_hub("registry_family_001", "global.family.david")
    register_test_device(child)
    register_test_device(parent)
    register_test_device(parent, "dev_B2C8", "tablet")

    registry_hubs = {child.hub_id: child, parent.hub_id: parent}
    claim_alias_through_authority_chain(
        registry_hubs,
        child.hub_id,
        "global.family.david.home.server",
        "server",
        "dev_A9F3",
    )
    claim_alias_through_authority_chain(
        registry_hubs,
        child.hub_id,
        "global.server",
        "server",
        "dev_A9F3",
    )
    claim_alias(parent, "global.family.david.taken", "dev_B2C8")
    claim_alias_through_authority_chain(
        registry_hubs,
        child.hub_id,
        "global.family.david.taken",
        "taken",
        "dev_A9F3",
    )
    parent.alias_authority_policy = {
        "allow_pass_up": False,
        "allow_fallback": False,
    }
    claim_alias_through_authority_chain(
        registry_hubs,
        child.hub_id,
        "global.other.blocked",
        "blocked",
        "dev_A9F3",
    )
    child.parent_hub_id = "registry_missing_001"
    claim_alias_through_authority_chain(
        registry_hubs,
        child.hub_id,
        "global.missing.path",
        "path",
        "dev_A9F3",
    )
    return child


def _hub_history_state(hub: RegistryHub) -> dict[str, object]:
    return {
        "aliases": deepcopy(hub.aliases),
        "authority_outcome_history": deepcopy(hub.authority_outcome_history),
        "conflicts": deepcopy(hub.conflicts),
        "devices": deepcopy(hub.devices),
        "parent_hub_id": hub.parent_hub_id,
    }
