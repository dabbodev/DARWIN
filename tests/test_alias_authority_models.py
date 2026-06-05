import json

from darwin.models.alias_authority import (
    AliasAuthorityDecision,
    AliasAuthorityPath,
)
from darwin.models.device import Device
from darwin.models.hub import RegistryHub
from darwin.registry.aliases import claim_alias
from darwin.registry.operations import register_device


def make_decision(
    hub_id: str = "registry_xfinity_301",
    scope_path: str = "global.us.west1.dist25.sf2.xfinity_301",
    decision: str = "continue_upward",
) -> AliasAuthorityDecision:
    return AliasAuthorityDecision(
        hub_id=hub_id,
        scope_path=scope_path,
        decision=decision,
        reason="insufficient_authority",
        alias="global.david_server",
        fallback_alias=f"{scope_path}.david_server",
        authority_ceiling=scope_path,
        can_continue_upward=True,
    )


def test_alias_authority_decision_to_dict():
    decision = make_decision()

    assert decision.to_dict() == {
        "hub_id": "registry_xfinity_301",
        "scope_path": "global.us.west1.dist25.sf2.xfinity_301",
        "decision": "continue_upward",
        "reason": "insufficient_authority",
        "alias": "global.david_server",
        "fallback_alias": (
            "global.us.west1.dist25.sf2.xfinity_301.david_server"
        ),
        "authority_ceiling": "global.us.west1.dist25.sf2.xfinity_301",
        "can_continue_upward": True,
    }


def test_alias_authority_path_adds_decisions():
    path = AliasAuthorityPath(
        requested_alias="global.david_server",
        target_device_id="dev_A9F3",
        requesting_hub_id="registry_xfinity_301",
    )
    first = make_decision()
    second = make_decision(
        hub_id="registry_sf2",
        scope_path="global.us.west1.dist25.sf2",
        decision="fallback_available",
    )

    path.add_decision(first)
    path.add_decision(second)

    assert path.decisions == [first, second]
    assert path.to_dict()["decisions"] == [first.to_dict(), second.to_dict()]


def test_alias_authority_path_latest_decision():
    path = AliasAuthorityPath(
        requested_alias="global.david_server",
        target_device_id="dev_A9F3",
        requesting_hub_id="registry_xfinity_301",
    )
    first = make_decision()
    second = make_decision(
        hub_id="registry_sf2",
        scope_path="global.us.west1.dist25.sf2",
        decision="fallback_available",
    )

    assert path.latest_decision() is None

    path.add_decision(first)
    path.add_decision(second)

    assert path.latest_decision() is second


def test_alias_authority_path_summary():
    path = AliasAuthorityPath(
        requested_alias="global.david_server",
        target_device_id="dev_A9F3",
        requesting_hub_id="registry_xfinity_301",
        final_status="fallback_granted",
        granted_alias="global.us.west1.dist25.sf2.xfinity_301.david_server",
        authority_ceiling="global.us.west1.dist25.sf2.xfinity_301",
    )
    path.add_decision(make_decision())
    path.add_decision(
        make_decision(
            hub_id="registry_sf2",
            scope_path="global.us.west1.dist25.sf2",
            decision="fallback_available",
        )
    )

    summary = path.to_summary()

    assert summary.requested_alias == "global.david_server"
    assert (
        summary.granted_alias
        == "global.us.west1.dist25.sf2.xfinity_301.david_server"
    )
    assert summary.final_status == "fallback_granted"
    assert summary.authority_ceiling == "global.us.west1.dist25.sf2.xfinity_301"
    assert summary.decision_count == 2
    assert summary.path_hubs == ["registry_xfinity_301", "registry_sf2"]


def test_alias_authority_path_json_safe():
    path = AliasAuthorityPath(
        requested_alias="global.david_server",
        target_device_id="dev_A9F3",
        requesting_hub_id="registry_xfinity_301",
        final_status="continue_upward",
    )
    path.add_decision(make_decision())

    json.dumps(path.to_dict())


def test_alias_authority_models_do_not_affect_existing_alias_claim():
    hub = RegistryHub(
        hub_id="hub_home_001",
        scope_path="global.family.david.home",
    )
    device = Device(device_id="dev_A9F3", label="phone")
    record = register_device(hub, device)

    result = claim_alias(hub, "david_phone", "dev_A9F3")

    assert result.success
    assert result.status == "active"
    assert result.alias_record is not None
    assert result.alias_record.target_device_id == "dev_A9F3"
    assert result.alias_record.target_identity_chain == record.identity_chain
    assert hub.aliases["david_phone"] is result.alias_record
