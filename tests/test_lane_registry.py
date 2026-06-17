import json

from darwin.models import (
    LaneDefinition,
    LaneDeliveryFallbackPolicy,
    LaneTrustContext,
    RegistryHub,
    TrafficHub,
    make_basic_messaging_lane_definition,
    parse_lane_signature,
)
from darwin.registry import (
    can_discover_lane_definition,
    get_lane_definition,
    list_discoverable_lane_definitions,
    list_lane_definitions,
    register_lane_definition,
)


def make_hub() -> RegistryHub:
    return RegistryHub(hub_id="hub_chat_001", scope_path="global.chat")


def make_definition(
    signature: str,
    *,
    scope: str = "global.chat",
    visibility_tier: int = 0,
    status: str = "active",
) -> LaneDefinition:
    lane_signature = parse_lane_signature(signature)
    return LaneDefinition(
        lane_signature=lane_signature,
        scope=scope,
        description=f"{signature} test lane",
        payload_kind=lane_signature.payload_kind,
        schema_ref=f"darwin://schemas/{lane_signature.lane_id}/{lane_signature.version}",
        protocol_ref=(
            f"darwin://protocols/{lane_signature.lane_id}/{lane_signature.version}"
        ),
        visibility_tier=visibility_tier,
        authority_scope=scope,
        adapter_kinds=("mailbox_adapter",),
        status=status,
        metadata={"test": True},
    )


def test_lane_delivery_fallback_policy_summary_is_json_safe():
    policy = LaneDeliveryFallbackPolicy(metadata={"source": "basic_messaging"})

    summary = policy.to_summary()

    assert summary == {
        "unknown_recipient": "bounce",
        "stale_device": "queue_with_expiry",
        "in_transit": "hold_until_relocation_resolves",
        "quarantined": "reject",
        "missing_lane_capability": "reject",
        "adapter_unavailable": "queue_with_retry",
        "metadata": {"source": "basic_messaging"},
    }
    json.dumps(summary)


def test_make_basic_messaging_lane_definition_produces_basic_messaging_v1():
    definition = make_basic_messaging_lane_definition(
        "global.chat",
        authority_scope="global.chat.authority",
    )

    assert definition.lane_signature.signature == "basic_messaging:v1"
    assert definition.scope == "global.chat"
    assert definition.authority_scope == "global.chat.authority"
    assert definition.fallback_policy.unknown_recipient == "bounce"
    assert definition.fallback_policy.adapter_unavailable == "queue_with_retry"


def test_lane_definition_summary_is_json_safe():
    definition = make_basic_messaging_lane_definition("global.chat")

    summary = definition.to_summary()

    assert summary == {
        "lane_signature": "basic_messaging:v1",
        "scope": "global.chat",
        "description": "Simulator-local symbolic mailbox messaging lane.",
        "payload_kind": "symbolic_message_envelope",
        "schema_ref": "darwin://schemas/basic_messaging/v1",
        "protocol_ref": "darwin://protocols/basic_messaging/v1",
        "visibility_tier": 0,
        "authority_scope": "global.chat",
        "adapter_kinds": ["mailbox_adapter"],
        "status": "active",
        "fallback_policy": LaneDeliveryFallbackPolicy().to_summary(),
        "metadata": {"simulator_local": True},
    }
    json.dumps(summary)


def test_registry_hub_lane_registry_defaults_empty():
    hub = make_hub()

    assert hub.lane_registry == {}


def test_register_lane_definition_stores_definition_on_hub():
    hub = make_hub()
    definition = make_basic_messaging_lane_definition("global.chat")

    result = register_lane_definition(hub, definition)

    assert result == definition
    assert hub.lane_registry == {"basic_messaging:v1": definition}


def test_register_lane_definition_replaces_same_signature_deterministically():
    hub = make_hub()
    draft = make_definition("basic_messaging:v1", status="draft")
    active = make_basic_messaging_lane_definition("global.chat")

    register_lane_definition(hub, draft)
    register_lane_definition(hub, active)

    assert list(hub.lane_registry) == ["basic_messaging:v1"]
    assert get_lane_definition(hub, "basic_messaging:v1") == active
    assert get_lane_definition(hub, "basic_messaging:v1").status.status == "active"


def test_get_lane_definition_returns_registered_definition_or_none():
    hub = make_hub()
    definition = make_basic_messaging_lane_definition("global.chat")
    register_lane_definition(hub, definition)

    assert get_lane_definition(hub, parse_lane_signature("basic_messaging:v1")) == definition
    assert get_lane_definition(hub, "missing:v1") is None


def test_list_lane_definitions_preserves_deterministic_signature_ordering():
    hub = make_hub()
    register_lane_definition(hub, make_definition("zeta:v1"))
    register_lane_definition(hub, make_definition("alpha:v1"))
    register_lane_definition(hub, make_definition("basic_messaging:v1"))

    definitions = list_lane_definitions(hub)

    assert [definition.lane_signature.signature for definition in definitions] == [
        "alpha:v1",
        "basic_messaging:v1",
        "zeta:v1",
    ]


def test_list_lane_definitions_filters_by_visibility_tier_and_status():
    hub = make_hub()
    public = make_definition("public_lane:v1", visibility_tier=0)
    private = make_definition("private_lane:v1", visibility_tier=5)
    deprecated = make_definition("deprecated_lane:v1", status="deprecated")
    register_lane_definition(hub, private)
    register_lane_definition(hub, deprecated)
    register_lane_definition(hub, public)

    assert list_lane_definitions(hub, visibility_tier=0) == [deprecated, public]
    assert list_lane_definitions(hub, visibility_tier=5) == [private]
    assert list_lane_definitions(hub, status="deprecated") == [deprecated]


def test_discoverable_lane_definitions_respect_tier_0_public():
    definition = make_definition("public_lane:v1", visibility_tier=0)
    requester = LaneTrustContext(requester_id="anonymous")

    assert can_discover_lane_definition(definition, requester) is True


def test_discoverable_lane_definitions_respect_tier_1_local_scope():
    definition = make_definition("local_lane:v1", visibility_tier=1)
    same_scope = LaneTrustContext(
        requester_id="dev_A9F3",
        requester_scope="global.chat",
    )
    other_scope = LaneTrustContext(
        requester_id="dev_B2C8",
        requester_scope="global.remote",
    )

    assert can_discover_lane_definition(definition, same_scope) is True
    assert can_discover_lane_definition(definition, other_scope) is False


def test_discoverable_lane_definitions_respect_tier_2_authenticated():
    definition = make_definition("authenticated_lane:v1", visibility_tier=2)
    unauthenticated = LaneTrustContext(requester_id="dev_A9F3")
    authenticated = LaneTrustContext(requester_id="dev_A9F3", authenticated=True)

    assert can_discover_lane_definition(definition, unauthenticated) is False
    assert can_discover_lane_definition(definition, authenticated) is True


def test_discoverable_lane_definitions_respect_tier_3_scoped_trust():
    definition = make_definition("trusted_lane:v1", visibility_tier=3)
    untrusted = LaneTrustContext(requester_id="dev_A9F3")
    trusted = LaneTrustContext(
        requester_id="dev_A9F3",
        trusted_scopes=("global.chat",),
    )

    assert can_discover_lane_definition(definition, untrusted) is False
    assert can_discover_lane_definition(definition, trusted) is True


def test_discoverable_lane_definitions_respect_tier_4_delegated_trust():
    definition = make_definition("delegated_lane:v1", visibility_tier=4)
    undelegated = LaneTrustContext(requester_id="dev_A9F3")
    delegated = LaneTrustContext(
        requester_id="dev_A9F3",
        requester_scope="global.remote",
        delegated_trust_paths=("global.remote->global.chat",),
    )

    assert can_discover_lane_definition(definition, undelegated) is False
    assert can_discover_lane_definition(definition, delegated) is True


def test_discoverable_lane_definitions_respect_tier_5_explicit_private():
    definition = make_definition("private_lane:v1", visibility_tier=5)
    denied = LaneTrustContext(requester_id="dev_B2C8")
    allowed_by_signature = LaneTrustContext(
        requester_id="dev_A9F3",
        explicit_permissions=("private_lane:v1",),
    )
    allowed_by_scoped_signature = LaneTrustContext(
        requester_id="dev_C7D1",
        explicit_permissions=("global.chat:private_lane:v1",),
    )

    assert can_discover_lane_definition(definition, denied) is False
    assert can_discover_lane_definition(definition, allowed_by_signature) is True
    assert can_discover_lane_definition(definition, allowed_by_scoped_signature) is True


def test_list_discoverable_lane_definitions_filters_by_visibility():
    hub = make_hub()
    register_lane_definition(hub, make_definition("private_lane:v1", visibility_tier=5))
    register_lane_definition(hub, make_definition("public_lane:v1", visibility_tier=0))
    requester = LaneTrustContext(requester_id="anonymous")

    definitions = list_discoverable_lane_definitions(hub, requester)

    assert [definition.lane_signature.signature for definition in definitions] == [
        "public_lane:v1"
    ]


def test_discovery_does_not_imply_lane_use_authorization():
    definition = make_basic_messaging_lane_definition("global.chat")
    requester = LaneTrustContext(requester_id="anonymous")

    assert can_discover_lane_definition(definition, requester) is True
    assert definition.lane_signature.auth_policy == "authorization_required"
    assert definition.lane_signature.required_capability == "basic_messaging"


def test_lane_registry_helpers_do_not_alter_unrelated_simulator_state():
    registry_hub = make_hub()
    traffic_hub = TrafficHub(hub_id="traffic_chat_001")
    definition = make_basic_messaging_lane_definition("global.chat")

    register_lane_definition(registry_hub, definition)
    list_discoverable_lane_definitions(
        registry_hub,
        LaneTrustContext(requester_id="anonymous"),
    )

    assert registry_hub.devices == {}
    assert registry_hub.aliases == {}
    assert registry_hub.alias_bundles == {}
    assert registry_hub.conflicts == {}
    assert registry_hub.authority_outcome_history == []
    assert traffic_hub.routes == {}
    assert traffic_hub.lanes == {}
    assert traffic_hub.forwarding_log == []
