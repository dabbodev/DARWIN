from darwin.models.device import Device
from darwin.models.hub import RegistryHub
from darwin.registry.alias_authority import (
    evaluate_alias_authority_step,
    fallback_alias_for_scope,
    is_alias_within_scope,
)
from darwin.registry.aliases import claim_alias
from darwin.registry.operations import register_device
from darwin.registry.security import quarantine_device, revoke_device


def make_hub(
    scope_path: str = "global.family.david",
    parent_hub_id: str | None = None,
) -> RegistryHub:
    return RegistryHub(
        hub_id="registry_home_001",
        scope_path=scope_path,
        parent_hub_id=parent_hub_id,
    )


def register_test_device(hub: RegistryHub, device_id: str = "dev_A9F3") -> None:
    register_device(hub, Device(device_id=device_id, label="server"))


def test_is_alias_within_scope():
    assert is_alias_within_scope("global.us.server", "global.us")
    assert is_alias_within_scope("global.us", "global.us")
    assert not is_alias_within_scope("global.us2.server", "global.us")


def test_fallback_alias_for_scope():
    assert (
        fallback_alias_for_scope("global.family.david", "server")
        == "global.family.david.server"
    )


def test_evaluate_alias_inside_scope_approves_here():
    hub = make_hub()
    register_test_device(hub)

    decision = evaluate_alias_authority_step(
        hub,
        "global.family.david.server",
        "server",
        "dev_A9F3",
    )

    assert decision.decision == "approved_here"
    assert decision.alias == "global.family.david.server"
    assert decision.authority_ceiling == "global.family.david"
    assert not decision.can_continue_upward


def test_evaluate_alias_outside_scope_with_parent_continues_upward():
    hub = make_hub(
        scope_path="global.us.west1",
        parent_hub_id="registry_us_001",
    )
    register_test_device(hub)

    decision = evaluate_alias_authority_step(
        hub,
        "global.david_server",
        "david_server",
        "dev_A9F3",
    )

    assert decision.decision == "continue_upward"
    assert decision.reason == "insufficient_authority"
    assert decision.can_continue_upward


def test_evaluate_alias_outside_scope_without_parent_fallback_available():
    hub = make_hub(scope_path="global.us.west1")
    register_test_device(hub)

    decision = evaluate_alias_authority_step(
        hub,
        "global.david_server",
        "david_server",
        "dev_A9F3",
    )

    assert decision.decision == "fallback_available"
    assert decision.reason == "insufficient_authority"
    assert decision.fallback_alias == "global.us.west1.david_server"
    assert decision.authority_ceiling == "global.us.west1"


def test_evaluate_alias_outside_scope_without_fallback_rejects():
    hub = make_hub(scope_path="global.us.west1")
    register_test_device(hub)

    decision = evaluate_alias_authority_step(
        hub,
        "global.david_server",
        "david_server",
        "dev_A9F3",
        fallback_allowed=False,
    )

    assert decision.decision == "insufficient_authority"
    assert decision.reason == "insufficient_authority"
    assert decision.fallback_alias is None
    assert not decision.can_continue_upward


def test_evaluate_alias_unknown_device_blocked():
    hub = make_hub()

    decision = evaluate_alias_authority_step(
        hub,
        "global.family.david.server",
        "server",
        "dev_missing",
    )

    assert decision.decision == "device_blocked"
    assert decision.reason == "unknown_device"


def test_evaluate_alias_quarantined_device_blocked():
    hub = make_hub()
    register_test_device(hub)
    quarantine_device(hub, "dev_A9F3", reason="test_quarantine")

    decision = evaluate_alias_authority_step(
        hub,
        "global.family.david.server",
        "server",
        "dev_A9F3",
    )

    assert decision.decision == "device_blocked"
    assert decision.reason == "device_quarantined"


def test_evaluate_alias_revoked_device_blocked():
    hub = make_hub()
    register_test_device(hub)
    revoke_device(hub, "dev_A9F3")

    decision = evaluate_alias_authority_step(
        hub,
        "global.family.david.server",
        "server",
        "dev_A9F3",
    )

    assert decision.decision == "device_blocked"
    assert decision.reason == "device_revoked"


def test_evaluate_alias_name_taken():
    hub = make_hub()
    register_test_device(hub)
    claim_alias(hub, "global.family.david.server", "dev_A9F3")

    decision = evaluate_alias_authority_step(
        hub,
        "global.family.david.server",
        "server",
        "dev_A9F3",
    )

    assert decision.decision == "name_taken"
    assert decision.reason == "alias_conflict"
    assert decision.alias == "global.family.david.server"


def test_evaluate_alias_fallback_name_taken():
    hub = make_hub(scope_path="global.us.west1")
    register_test_device(hub)
    claim_alias(hub, "global.us.west1.david_server", "dev_A9F3")

    decision = evaluate_alias_authority_step(
        hub,
        "global.david_server",
        "david_server",
        "dev_A9F3",
    )

    assert decision.decision == "name_taken"
    assert decision.reason == "fallback_alias_conflict"
    assert decision.fallback_alias == "global.us.west1.david_server"


def test_authority_step_helpers_do_not_mutate_aliases():
    hub = make_hub(scope_path="global.us.west1")
    register_test_device(hub)
    claim_alias(hub, "global.us.west1.existing", "dev_A9F3")
    aliases_before = dict(hub.aliases)

    evaluate_alias_authority_step(
        hub,
        "global.david_server",
        "david_server",
        "dev_A9F3",
    )

    assert hub.aliases == aliases_before
