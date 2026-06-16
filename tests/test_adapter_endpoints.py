import json
import socket

from darwin.models import (
    AdapterEndpoint,
    AdapterEndpointKind,
    AdapterEndpointStatus,
    HubTopologyAdvertisement,
    RegistryHub,
    TrafficHub,
    make_basic_messaging_lane_definition,
    make_domain_hint_hub_endpoint,
    make_in_memory_mailbox_endpoint,
)
from darwin.registry import (
    get_adapter_endpoint,
    get_hub_topology_advertisement,
    list_adapter_endpoints,
    list_hub_topology_advertisements,
    mailbox_supports_lane,
    register_adapter_endpoint,
    register_hub_topology_advertisement,
    register_lane_definition,
)


def make_hub() -> RegistryHub:
    return RegistryHub(hub_id="hub_chat_001", scope_path="global.chat")


def make_endpoint(
    endpoint_id: str = "endpoint_mailbox_neo",
    *,
    subject_id: str = "mailbox_neo",
    subject_kind: str = "mailbox",
    adapter_kind: str = "in_memory",
    status: str = "available",
    lane_signatures: tuple[str, ...] = ("basic_messaging:v1",),
    scope: str = "global.chat",
) -> AdapterEndpoint:
    return AdapterEndpoint(
        endpoint_id=endpoint_id,
        subject_id=subject_id,
        subject_kind=subject_kind,
        adapter_kind=adapter_kind,
        status=status,
        lane_signatures=lane_signatures,
        scope=scope,
        metadata={"simulator_local": True},
    )


def make_advertisement(
    advertisement_id: str = "topology_hub_chat_001",
    *,
    hub_id: str = "hub_chat_001",
    hub_kind: str = "registry_hub",
    scope: str = "global.chat",
    parent_hub_id: str | None = None,
    endpoint_id: str = "endpoint_hub_chat_001",
    adapter_kind: str = "domain_hint",
    host_hint: str | None = "demo.example.test",
    visibility_tier: int = 0,
    status: str = "available",
) -> HubTopologyAdvertisement:
    return HubTopologyAdvertisement(
        advertisement_id=advertisement_id,
        hub_id=hub_id,
        hub_kind=hub_kind,
        scope=scope,
        parent_hub_id=parent_hub_id,
        endpoint_id=endpoint_id,
        adapter_kind=adapter_kind,
        host_hint=host_hint,
        visibility_tier=visibility_tier,
        status=status,
        metadata={"simulator_local": True, "hint_only": True},
    )


def test_adapter_endpoint_summary_is_json_safe():
    endpoint = AdapterEndpoint(
        endpoint_id="endpoint_mailbox_neo",
        subject_id="mailbox_neo",
        subject_kind="mailbox",
        adapter_kind=AdapterEndpointKind("domain_hint"),
        status=AdapterEndpointStatus("available"),
        lane_signatures=("basic_messaging:v1",),
        scope="global.chat",
        host_hint="chat.example.test",
        port_hint="symbolic-443",
        path_hint="/darwin/mailbox/neo",
        metadata={"labels": ["demo", "mailbox"]},
    )

    summary = endpoint.to_summary()

    assert summary == {
        "endpoint_id": "endpoint_mailbox_neo",
        "subject_id": "mailbox_neo",
        "subject_kind": "mailbox",
        "adapter_kind": "domain_hint",
        "status": "available",
        "lane_signatures": ["basic_messaging:v1"],
        "scope": "global.chat",
        "host_hint": "chat.example.test",
        "port_hint": "symbolic-443",
        "path_hint": "/darwin/mailbox/neo",
        "metadata": {"labels": ["demo", "mailbox"]},
    }
    json.dumps(summary)


def test_hub_topology_advertisement_summary_is_json_safe():
    advertisement = make_advertisement(parent_hub_id="hub_global_001")

    summary = advertisement.to_summary()

    assert summary == {
        "advertisement_id": "topology_hub_chat_001",
        "hub_id": "hub_chat_001",
        "hub_kind": "registry_hub",
        "scope": "global.chat",
        "parent_hub_id": "hub_global_001",
        "endpoint_id": "endpoint_hub_chat_001",
        "adapter_kind": "domain_hint",
        "host_hint": "demo.example.test",
        "visibility_tier": 0,
        "status": "available",
        "metadata": {"simulator_local": True, "hint_only": True},
    }
    json.dumps(summary)


def test_registry_hub_endpoint_registries_default_empty():
    hub = make_hub()

    assert hub.adapter_endpoints == {}
    assert hub.hub_topology_advertisements == {}


def test_register_adapter_endpoint_stores_it():
    hub = make_hub()
    endpoint = make_endpoint()

    result = register_adapter_endpoint(hub, endpoint)

    assert result == endpoint
    assert hub.adapter_endpoints == {"endpoint_mailbox_neo": endpoint}


def test_get_adapter_endpoint_by_id():
    hub = make_hub()
    endpoint = make_endpoint()
    register_adapter_endpoint(hub, endpoint)

    assert get_adapter_endpoint(hub, "endpoint_mailbox_neo") == endpoint
    assert get_adapter_endpoint(hub, "missing_endpoint") is None


def test_list_adapter_endpoints_deterministic_ordering():
    hub = make_hub()
    register_adapter_endpoint(hub, make_endpoint("endpoint_zeta"))
    register_adapter_endpoint(hub, make_endpoint("endpoint_alpha"))
    register_adapter_endpoint(hub, make_endpoint("endpoint_basic"))

    assert [endpoint.endpoint_id for endpoint in list_adapter_endpoints(hub)] == [
        "endpoint_alpha",
        "endpoint_basic",
        "endpoint_zeta",
    ]


def test_list_adapter_endpoints_additive_filters():
    hub = make_hub()
    mailbox = make_endpoint("endpoint_mailbox_neo")
    stale = make_endpoint(
        "endpoint_mailbox_trinity",
        subject_id="mailbox_trinity",
        status="stale",
        scope="global.remote",
    )
    hub_endpoint = make_endpoint(
        "endpoint_hub_chat",
        subject_id="hub_chat_001",
        subject_kind="registry_hub",
        adapter_kind="domain_hint",
        lane_signatures=("control_plane:v1",),
    )
    register_adapter_endpoint(hub, stale)
    register_adapter_endpoint(hub, hub_endpoint)
    register_adapter_endpoint(hub, mailbox)

    assert list_adapter_endpoints(hub, subject_id="mailbox_neo") == [mailbox]
    assert list_adapter_endpoints(hub, subject_kind="registry_hub") == [hub_endpoint]
    assert list_adapter_endpoints(hub, adapter_kind="domain_hint") == [hub_endpoint]
    assert list_adapter_endpoints(hub, status="stale") == [stale]
    assert list_adapter_endpoints(hub, lane_signature="basic_messaging:v1") == [
        mailbox,
        stale,
    ]
    assert list_adapter_endpoints(hub, scope="global.remote") == [stale]
    assert list_adapter_endpoints(
        hub,
        subject_kind="mailbox",
        status="available",
        scope="global.chat",
    ) == [mailbox]


def test_duplicate_endpoint_id_replaces_deterministically():
    hub = make_hub()
    original = make_endpoint(status="available")
    replacement = make_endpoint(status="disabled")

    register_adapter_endpoint(hub, original)
    register_adapter_endpoint(hub, replacement)

    assert list(hub.adapter_endpoints) == ["endpoint_mailbox_neo"]
    assert get_adapter_endpoint(hub, "endpoint_mailbox_neo") == replacement
    assert list_adapter_endpoints(hub, status="available") == []
    assert list_adapter_endpoints(hub, status="disabled") == [replacement]


def test_register_hub_topology_advertisement_stores_it():
    hub = make_hub()
    advertisement = make_advertisement()

    result = register_hub_topology_advertisement(hub, advertisement)

    assert result == advertisement
    assert hub.hub_topology_advertisements == {
        "topology_hub_chat_001": advertisement
    }


def test_get_hub_topology_advertisement_by_id():
    hub = make_hub()
    advertisement = make_advertisement()
    register_hub_topology_advertisement(hub, advertisement)

    assert (
        get_hub_topology_advertisement(hub, "topology_hub_chat_001")
        == advertisement
    )
    assert get_hub_topology_advertisement(hub, "missing_topology") is None


def test_list_topology_advertisements_deterministic_ordering():
    hub = make_hub()
    register_hub_topology_advertisement(hub, make_advertisement("topology_zeta"))
    register_hub_topology_advertisement(hub, make_advertisement("topology_alpha"))
    register_hub_topology_advertisement(hub, make_advertisement("topology_basic"))

    assert [
        advertisement.advertisement_id
        for advertisement in list_hub_topology_advertisements(hub)
    ] == ["topology_alpha", "topology_basic", "topology_zeta"]


def test_list_topology_advertisements_additive_filters():
    hub = make_hub()
    local = make_advertisement()
    remote = make_advertisement(
        "topology_hub_remote_001",
        hub_id="hub_remote_001",
        scope="global.remote",
        adapter_kind="loopback_placeholder",
        host_hint=None,
        visibility_tier=1,
        status="stale",
    )
    traffic = make_advertisement(
        "topology_traffic_chat_001",
        hub_id="traffic_chat_001",
        hub_kind="traffic_hub",
        scope="global.chat",
        visibility_tier=5,
        status="disabled",
    )
    register_hub_topology_advertisement(hub, remote)
    register_hub_topology_advertisement(hub, traffic)
    register_hub_topology_advertisement(hub, local)

    assert list_hub_topology_advertisements(hub, hub_id="hub_chat_001") == [local]
    assert list_hub_topology_advertisements(hub, hub_kind="traffic_hub") == [
        traffic
    ]
    assert list_hub_topology_advertisements(hub, scope="global.remote") == [
        remote
    ]
    assert list_hub_topology_advertisements(hub, adapter_kind="domain_hint") == [
        local,
        traffic,
    ]
    assert list_hub_topology_advertisements(hub, status="stale") == [remote]
    assert list_hub_topology_advertisements(hub, visibility_tier=5) == [traffic]
    assert list_hub_topology_advertisements(
        hub,
        scope="global.chat",
        adapter_kind="domain_hint",
        status="available",
    ) == [local]


def test_duplicate_topology_advertisement_id_replaces_deterministically():
    hub = make_hub()
    original = make_advertisement(status="available")
    replacement = make_advertisement(status="disabled")

    register_hub_topology_advertisement(hub, original)
    register_hub_topology_advertisement(hub, replacement)

    assert list(hub.hub_topology_advertisements) == ["topology_hub_chat_001"]
    assert (
        get_hub_topology_advertisement(hub, "topology_hub_chat_001")
        == replacement
    )
    assert list_hub_topology_advertisements(hub, status="available") == []
    assert list_hub_topology_advertisements(hub, status="disabled") == [
        replacement
    ]


def test_domain_and_host_hints_remain_inert_metadata():
    endpoint = make_domain_hint_hub_endpoint(
        endpoint_id="endpoint_top_level",
        hub_id="hub_global_public",
        hub_kind="registry_hub",
        scope="global",
        host_hint="darwin-demo.example.test",
        path_hint="/registry",
    )
    advertisement = make_advertisement(
        hub_id="hub_global_public",
        scope="global",
        endpoint_id="endpoint_top_level",
        host_hint="darwin-demo.example.test",
    )

    assert endpoint.host_hint == "darwin-demo.example.test"
    assert endpoint.path_hint == "/registry"
    assert endpoint.adapter_kind.kind == "domain_hint"
    assert endpoint.metadata == {"simulator_local": True, "hint_only": True}
    assert advertisement.host_hint == "darwin-demo.example.test"


def test_helpers_do_not_perform_dns_lookup_or_open_sockets(monkeypatch):
    def fail_dns(*args, **kwargs):
        raise AssertionError("DNS lookup should not run")

    def fail_socket(*args, **kwargs):
        raise AssertionError("socket should not open")

    monkeypatch.setattr(socket, "getaddrinfo", fail_dns)
    monkeypatch.setattr(socket, "socket", fail_socket)
    hub = make_hub()

    endpoint = make_domain_hint_hub_endpoint(
        endpoint_id="endpoint_top_level",
        hub_id="hub_global_public",
        hub_kind="registry_hub",
        scope="global",
        host_hint="darwin-demo.example.test",
    )
    mailbox_endpoint = make_in_memory_mailbox_endpoint(
        endpoint_id="endpoint_mailbox_neo",
        mailbox_id="mailbox_neo",
        scope="global.chat",
    )
    advertisement = make_advertisement(
        hub_id="hub_global_public",
        scope="global",
        endpoint_id="endpoint_top_level",
        host_hint="darwin-demo.example.test",
    )

    register_adapter_endpoint(hub, endpoint)
    register_adapter_endpoint(hub, mailbox_endpoint)
    register_hub_topology_advertisement(hub, advertisement)

    assert list_adapter_endpoints(hub, adapter_kind="domain_hint") == [endpoint]
    assert list_hub_topology_advertisements(hub, hub_id="hub_global_public") == [
        advertisement
    ]


def test_endpoint_records_do_not_imply_delivery_authorization():
    hub = make_hub()
    register_lane_definition(hub, make_basic_messaging_lane_definition("global.chat"))
    endpoint = make_endpoint()
    register_adapter_endpoint(hub, endpoint)

    assert mailbox_supports_lane(hub, "mailbox_neo", "basic_messaging:v1") is False
    assert endpoint.lane_signatures == ("basic_messaging:v1",)


def test_helpers_do_not_alter_unrelated_simulator_state():
    registry_hub = make_hub()
    traffic_hub = TrafficHub(hub_id="traffic_chat_001")
    definition = make_basic_messaging_lane_definition("global.chat")
    register_lane_definition(registry_hub, definition)

    endpoint = make_endpoint()
    advertisement = make_advertisement()
    register_adapter_endpoint(registry_hub, endpoint)
    register_hub_topology_advertisement(registry_hub, advertisement)

    assert registry_hub.devices == {}
    assert registry_hub.aliases == {}
    assert registry_hub.alias_bundles == {}
    assert registry_hub.conflicts == {}
    assert registry_hub.authority_outcome_history == []
    assert registry_hub.mailboxes == {}
    assert registry_hub.mailbox_address_index == {}
    assert registry_hub.lane_registry == {"basic_messaging:v1": definition}
    assert traffic_hub.routes == {}
    assert traffic_hub.lanes == {}
    assert traffic_hub.forwarding_log == []
