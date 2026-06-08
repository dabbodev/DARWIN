from copy import deepcopy

from darwin.models.device import Device
from darwin.models.hub import RegistryHub
from darwin.registry.alias_authority import claim_alias_through_authority_chain
from darwin.registry.aliases import claim_alias, release_alias
from darwin.registry.history_queries import (
    query_alias_conflicts,
    query_alias_history,
    query_authority_decisions,
    query_quarantine_events,
)
from darwin.registry.operations import register_device
from darwin.registry.security import quarantine_device


def make_hub(
    hub_id: str = "registry_home_001",
    scope_path: str = "global.family.david.home",
) -> RegistryHub:
    return RegistryHub(hub_id=hub_id, scope_path=scope_path)


def register_test_device(
    hub: RegistryHub,
    device_id: str = "dev_A9F3",
    label: str = "server",
) -> None:
    register_device(hub, Device(device_id=device_id, label=label))


def test_history_queries_return_empty_lists_without_matching_history():
    hub = make_hub()

    assert query_alias_history(hub) == []
    assert query_alias_conflicts(hub) == []
    assert query_authority_decisions(hub) == []
    assert query_quarantine_events(hub) == []


def test_alias_claim_history_can_be_queried_by_alias():
    hub = make_hub()
    register_test_device(hub)
    claim_alias(hub, "global.family.david.home.server", "dev_A9F3")

    results = query_alias_history(hub, alias="global.family.david.home.server")

    assert len(results) == 1
    assert results[0].alias == "global.family.david.home.server"
    assert results[0].target_device_id == "dev_A9F3"
    assert results[0].status == "active"
    assert results[0].to_dict()["approved_by_registry_hub"] == "registry_home_001"


def test_alias_claim_history_can_be_queried_by_device_id():
    hub = make_hub()
    register_test_device(hub, "dev_A9F3", "server")
    register_test_device(hub, "dev_B2C8", "tablet")
    claim_alias(hub, "global.family.david.home.server", "dev_A9F3")
    claim_alias(hub, "global.family.david.home.tablet", "dev_B2C8")

    results = query_alias_history(hub, device_id="dev_B2C8")

    assert [result.alias for result in results] == ["global.family.david.home.tablet"]


def test_alias_history_filters_are_additive_and_ordered():
    hub = make_hub()
    register_test_device(hub, "dev_A9F3", "server")
    register_test_device(hub, "dev_B2C8", "tablet")
    claim_alias(hub, "zeta", "dev_A9F3")
    claim_alias(hub, "alpha", "dev_A9F3")
    claim_alias(hub, "middle", "dev_B2C8")
    release_alias(hub, "zeta")

    assert [result.alias for result in query_alias_history(hub)] == [
        "alpha",
        "middle",
        "zeta",
    ]
    assert [result.alias for result in query_alias_history(hub, device_id="dev_A9F3")] == [
        "alpha",
        "zeta",
    ]
    assert [
        result.alias
        for result in query_alias_history(
            hub,
            device_id="dev_A9F3",
            status="released",
        )
    ] == ["zeta"]


def test_alias_conflict_history_can_be_queried():
    hub = make_hub()
    register_test_device(hub, "dev_A9F3", "server")
    register_test_device(hub, "dev_B2C8", "tablet")
    claim_alias(hub, "shared", "dev_A9F3")
    claim_alias(hub, "shared", "dev_B2C8")

    results = query_alias_conflicts(hub, alias="shared", device_id="dev_B2C8")

    assert len(results) == 1
    assert results[0].alias == "shared"
    assert results[0].existing_device_id == "dev_A9F3"
    assert results[0].requesting_device_id == "dev_B2C8"
    assert results[0].status == "pending_resolution"
    assert results[0].to_dict()["conflict_id"] == "alias_conflict:shared:dev_B2C8"


def test_authority_decisions_query_persisted_fallback_result():
    hub = RegistryHub(hub_id="registry_us_001", scope_path="global.us")
    register_test_device(hub)
    claim_alias_through_authority_chain(
        {hub.hub_id: hub},
        hub.hub_id,
        "global.server",
        "server",
        "dev_A9F3",
    )

    results = query_authority_decisions(
        hub,
        requested_alias="global.server",
        final_status="fallback_granted",
    )

    assert len(results) == 1
    assert results[0].requested_alias == "global.server"
    assert results[0].granted_alias == "global.us.server"
    assert results[0].device_id == "dev_A9F3"
    assert results[0].fallback_reason == "insufficient_authority"
    assert results[0].to_dict()["authority_ceiling"] == "global.us"


def test_quarantine_events_can_be_queried_by_device_and_reason():
    hub = make_hub()
    register_test_device(hub)
    quarantine_device(
        hub,
        "dev_A9F3",
        reason="test_quarantine",
        source_hub_id="hub_guest_001",
        current_time=42,
    )

    results = query_quarantine_events(
        hub,
        device_id="dev_A9F3",
        reason="test_quarantine",
    )

    assert len(results) == 1
    assert results[0].quarantine_key == "dev_A9F3"
    assert results[0].device_id == "dev_A9F3"
    assert results[0].source_hub_id == "hub_guest_001"
    assert results[0].created_at == 42
    assert results[0].event_type == "device_quarantined"
    assert results[0].action_taken == "quarantined"


def test_history_queries_do_not_mutate_registry_hub_state():
    hub = make_hub()
    register_test_device(hub, "dev_A9F3", "server")
    register_test_device(hub, "dev_B2C8", "tablet")
    claim_alias(hub, "shared", "dev_A9F3")
    claim_alias(hub, "shared", "dev_B2C8")
    quarantine_device(hub, "dev_B2C8", reason="test_quarantine")
    before = _hub_history_state(hub)

    query_alias_history(hub)
    query_alias_conflicts(hub)
    query_authority_decisions(hub)
    query_quarantine_events(hub)

    assert _hub_history_state(hub) == before


def _hub_history_state(hub: RegistryHub) -> dict[str, object]:
    return {
        "aliases": deepcopy(hub.aliases),
        "conflicts": deepcopy(hub.conflicts),
        "security_events": deepcopy(hub.security_events),
        "quarantines": deepcopy(hub.quarantines),
        "devices": deepcopy(hub.devices),
    }
