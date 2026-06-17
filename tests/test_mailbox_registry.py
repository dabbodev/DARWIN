import json

import pytest

from darwin.models import (
    MailboxCapability,
    MailboxIdentity,
    RegistryHub,
    TrafficHub,
    format_mailbox_address,
    make_basic_messaging_lane_definition,
    parse_lane_signature,
)
from darwin.registry import (
    bind_mailbox_capability,
    get_lane_definition,
    get_mailbox,
    list_mailbox_capabilities,
    list_mailboxes,
    mailbox_supports_lane,
    make_basic_messaging_mailbox,
    register_lane_definition,
    register_mailbox,
    resolve_mailbox_address,
)


def make_hub() -> RegistryHub:
    return RegistryHub(hub_id="hub_chat_001", scope_path="global.chat")


def make_mailbox(
    mailbox_id: str = "mailbox_neo",
    *,
    canonical_device_id: str = "dev_A9F3",
    local_name: str = "neo",
    scope: str = "global.chat",
    capabilities: tuple[MailboxCapability, ...] = (),
) -> MailboxIdentity:
    return MailboxIdentity(
        mailbox_id=mailbox_id,
        canonical_device_id=canonical_device_id,
        local_name=local_name,
        scope=scope,
        address=format_mailbox_address(scope, local_name),
        capabilities=capabilities,
    )


def make_basic_capability(
    capability_id: str = "cap_basic_messaging",
    *,
    enabled: bool = True,
) -> MailboxCapability:
    return MailboxCapability(
        capability_id=capability_id,
        lane_signature="basic_messaging:v1",
        enabled=enabled,
        metadata={"simulator_local": True},
    )


def test_registry_hub_mailbox_registry_defaults_empty():
    hub = make_hub()

    assert hub.mailboxes == {}
    assert hub.mailbox_address_index == {}


def test_register_mailbox_stores_identity_and_address_index():
    hub = make_hub()
    mailbox = make_mailbox()

    result = register_mailbox(hub, mailbox)

    assert result == mailbox
    assert hub.mailboxes == {"mailbox_neo": mailbox}
    assert hub.mailbox_address_index == {
        "darwin://global.chat.neo/inbox": "mailbox_neo"
    }


def test_get_mailbox_returns_registered_mailbox_or_none():
    hub = make_hub()
    mailbox = make_mailbox()
    register_mailbox(hub, mailbox)

    assert get_mailbox(hub, "mailbox_neo") == mailbox
    assert get_mailbox(hub, "missing_mailbox") is None


def test_resolve_mailbox_address_uses_raw_darwin_address():
    hub = make_hub()
    mailbox = make_mailbox()
    register_mailbox(hub, mailbox)

    assert resolve_mailbox_address(hub, "darwin://global.chat.neo/inbox") == mailbox
    assert (
        resolve_mailbox_address(hub, format_mailbox_address("global.chat", "missing"))
        is None
    )


def test_list_mailboxes_preserves_deterministic_mailbox_id_ordering():
    hub = make_hub()
    trinity = make_mailbox("mailbox_trinity", local_name="trinity")
    neo = make_mailbox("mailbox_neo", local_name="neo")
    morpheus = make_mailbox("mailbox_morpheus", local_name="morpheus")

    register_mailbox(hub, trinity)
    register_mailbox(hub, neo)
    register_mailbox(hub, morpheus)

    assert [mailbox.mailbox_id for mailbox in list_mailboxes(hub)] == [
        "mailbox_morpheus",
        "mailbox_neo",
        "mailbox_trinity",
    ]


def test_list_mailboxes_filters_by_scope():
    hub = make_hub()
    local = make_mailbox("mailbox_neo", local_name="neo", scope="global.chat")
    remote = make_mailbox(
        "mailbox_neo_remote",
        local_name="neo",
        scope="global.remote",
    )
    register_mailbox(hub, remote)
    register_mailbox(hub, local)

    assert list_mailboxes(hub, scope="global.chat") == [local]
    assert list_mailboxes(hub, scope="global.remote") == [remote]


def test_list_mailboxes_filters_by_canonical_device_id():
    hub = make_hub()
    neo = make_mailbox("mailbox_neo", canonical_device_id="dev_A9F3")
    trinity = make_mailbox(
        "mailbox_trinity",
        canonical_device_id="dev_B2C8",
        local_name="trinity",
    )
    register_mailbox(hub, trinity)
    register_mailbox(hub, neo)

    assert list_mailboxes(hub, canonical_device_id="dev_A9F3") == [neo]


def test_list_mailboxes_filters_by_capability_id_or_lane_signature():
    hub = make_hub()
    basic = make_mailbox("mailbox_neo", capabilities=(make_basic_capability(),))
    empty = make_mailbox("mailbox_trinity", local_name="trinity")
    register_mailbox(hub, empty)
    register_mailbox(hub, basic)

    assert list_mailboxes(hub, capability="cap_basic_messaging") == [basic]
    assert list_mailboxes(hub, capability="basic_messaging:v1") == [basic]


def test_duplicate_mailbox_id_replaces_identity_and_old_address_index():
    hub = make_hub()
    original = make_mailbox("mailbox_neo", local_name="neo")
    replacement = make_mailbox("mailbox_neo", local_name="anderson")

    register_mailbox(hub, original)
    register_mailbox(hub, replacement)

    assert list(hub.mailboxes) == ["mailbox_neo"]
    assert get_mailbox(hub, "mailbox_neo") == replacement
    assert resolve_mailbox_address(hub, "darwin://global.chat.neo/inbox") is None
    assert resolve_mailbox_address(hub, "darwin://global.chat.anderson/inbox") == (
        replacement
    )


def test_duplicate_mailbox_address_resolves_to_latest_registered_mailbox():
    hub = make_hub()
    original = make_mailbox(
        "mailbox_neo",
        canonical_device_id="dev_A9F3",
        local_name="neo",
    )
    replacement = make_mailbox(
        "mailbox_neo_shadow",
        canonical_device_id="dev_B2C8",
        local_name="neo",
    )

    register_mailbox(hub, original)
    register_mailbox(hub, replacement)

    assert get_mailbox(hub, "mailbox_neo") == original
    assert get_mailbox(hub, "mailbox_neo_shadow") == replacement
    assert resolve_mailbox_address(hub, "darwin://global.chat.neo/inbox") == (
        replacement
    )
    assert hub.mailbox_address_index == {
        "darwin://global.chat.neo/inbox": "mailbox_neo_shadow"
    }


def test_binding_capability_requires_registered_lane_definition():
    hub = make_hub()
    register_mailbox(hub, make_mailbox())

    with pytest.raises(ValueError, match="registered before mailbox binding"):
        bind_mailbox_capability(hub, "mailbox_neo", make_basic_capability())


def test_binding_basic_messaging_works_after_lane_definition_registration():
    hub = make_hub()
    mailbox = make_mailbox()
    definition = make_basic_messaging_lane_definition("global.chat")
    register_mailbox(hub, mailbox)
    register_lane_definition(hub, definition)

    updated = bind_mailbox_capability(
        hub,
        "mailbox_neo",
        make_basic_capability(),
    )

    assert updated.mailbox_id == "mailbox_neo"
    assert updated.capabilities == (make_basic_capability(),)
    assert get_mailbox(hub, "mailbox_neo") == updated
    assert get_lane_definition(hub, "basic_messaging:v1") == definition


def test_mailbox_supports_enabled_lane():
    hub = make_hub()
    register_mailbox(hub, make_mailbox())
    register_lane_definition(hub, make_basic_messaging_lane_definition("global.chat"))
    bind_mailbox_capability(hub, "mailbox_neo", make_basic_capability())

    assert mailbox_supports_lane(hub, "mailbox_neo", "basic_messaging:v1") is True
    assert mailbox_supports_lane(
        hub,
        "mailbox_neo",
        parse_lane_signature("basic_messaging:v1"),
    ) is True
    assert mailbox_supports_lane(hub, "missing_mailbox", "basic_messaging:v1") is False


def test_disabled_capability_does_not_count_as_supported_lane():
    hub = make_hub()
    register_mailbox(hub, make_mailbox())
    register_lane_definition(hub, make_basic_messaging_lane_definition("global.chat"))
    bind_mailbox_capability(
        hub,
        "mailbox_neo",
        make_basic_capability(enabled=False),
    )

    assert mailbox_supports_lane(hub, "mailbox_neo", "basic_messaging:v1") is False


def test_duplicate_capability_binding_replaces_by_capability_id():
    hub = make_hub()
    register_mailbox(hub, make_mailbox())
    register_lane_definition(hub, make_basic_messaging_lane_definition("global.chat"))
    enabled = make_basic_capability(enabled=True)
    disabled = make_basic_capability(enabled=False)

    bind_mailbox_capability(hub, "mailbox_neo", enabled)
    updated = bind_mailbox_capability(hub, "mailbox_neo", disabled)

    assert updated.capabilities == (disabled,)
    assert list_mailbox_capabilities(hub, "mailbox_neo") == [disabled]
    assert mailbox_supports_lane(hub, "mailbox_neo", "basic_messaging:v1") is False


def test_mailbox_capability_summaries_remain_json_safe_after_binding():
    hub = make_hub()
    register_mailbox(hub, make_mailbox())
    register_lane_definition(hub, make_basic_messaging_lane_definition("global.chat"))
    updated = bind_mailbox_capability(
        hub,
        "mailbox_neo",
        make_basic_capability(),
    )

    summary = updated.to_summary()

    assert summary["capabilities"] == [make_basic_capability().to_summary()]
    json.dumps(summary)


def test_make_basic_messaging_mailbox_is_pure_and_does_not_register():
    hub = make_hub()

    mailbox = make_basic_messaging_mailbox(
        mailbox_id="mailbox_neo",
        canonical_device_id="dev_A9F3",
        local_name="neo",
        scope="global.chat",
    )

    assert mailbox.address.raw == "darwin://global.chat.neo/inbox"
    assert mailbox.capabilities == (make_basic_capability(),)
    assert hub.mailboxes == {}


def test_helpers_do_not_mutate_canonical_device_identity_or_unrelated_state():
    registry_hub = make_hub()
    traffic_hub = TrafficHub(hub_id="traffic_chat_001")
    mailbox = make_mailbox()
    definition = make_basic_messaging_lane_definition("global.chat")
    register_mailbox(registry_hub, mailbox)
    register_lane_definition(registry_hub, definition)

    updated = bind_mailbox_capability(
        registry_hub,
        "mailbox_neo",
        make_basic_capability(),
    )

    assert updated.canonical_device_id == "dev_A9F3"
    assert get_mailbox(registry_hub, "mailbox_neo").canonical_device_id == "dev_A9F3"
    assert registry_hub.devices == {}
    assert registry_hub.aliases == {}
    assert registry_hub.alias_bundles == {}
    assert registry_hub.conflicts == {}
    assert registry_hub.authority_outcome_history == []
    assert registry_hub.lane_registry == {"basic_messaging:v1": definition}
    assert traffic_hub.routes == {}
    assert traffic_hub.lanes == {}
    assert traffic_hub.forwarding_log == []
