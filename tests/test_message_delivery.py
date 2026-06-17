import json
import socket

from darwin.models import (
    AdapterEndpoint,
    LocalDeviceRecord,
    MailboxCapability,
    MailboxIdentity,
    MessageDeliveryResult,
    MessageEnvelope,
    RegistryHub,
    TrafficHub,
    format_mailbox_address,
    make_basic_message_envelope,
    make_basic_messaging_lane_definition,
    make_in_memory_mailbox_endpoint,
)
from darwin.registry import (
    bind_mailbox_capability,
    deliver_message_to_mailbox,
    get_mailbox_inbox,
    list_message_delivery_results,
    register_adapter_endpoint,
    register_lane_definition,
    register_mailbox,
)


def make_hub() -> RegistryHub:
    return RegistryHub(hub_id="hub_chat_001", scope_path="global.chat")


def make_mailbox(
    mailbox_id: str = "mailbox_neo",
    *,
    canonical_device_id: str = "dev_A9F3",
    local_name: str = "neo",
    capabilities: tuple[MailboxCapability, ...] = (),
) -> MailboxIdentity:
    return MailboxIdentity(
        mailbox_id=mailbox_id,
        canonical_device_id=canonical_device_id,
        local_name=local_name,
        scope="global.chat",
        address=format_mailbox_address("global.chat", local_name),
        capabilities=capabilities,
    )


def make_basic_capability(*, enabled: bool = True) -> MailboxCapability:
    return MailboxCapability(
        capability_id="cap_basic_messaging",
        lane_signature="basic_messaging:v1",
        enabled=enabled,
        metadata={"simulator_local": True},
    )


def make_message(
    message_id: str = "msg_001",
    *,
    recipient_address: str = "darwin://global.chat.neo/inbox",
) -> MessageEnvelope:
    return make_basic_message_envelope(
        message_id=message_id,
        sender_id="dev_sender",
        recipient_address=recipient_address,
        payload="hello",
    )


def register_basic_lane_mailbox_and_endpoint(
    hub: RegistryHub,
    *,
    capability_enabled: bool = True,
    endpoint_status: str = "available",
) -> MailboxIdentity:
    register_lane_definition(hub, make_basic_messaging_lane_definition("global.chat"))
    mailbox = register_mailbox(hub, make_mailbox())
    bind_mailbox_capability(
        hub,
        "mailbox_neo",
        make_basic_capability(enabled=capability_enabled),
    )
    register_adapter_endpoint(
        hub,
        make_in_memory_mailbox_endpoint(
            endpoint_id="endpoint_mailbox_neo",
            mailbox_id="mailbox_neo",
            scope="global.chat",
            status=endpoint_status,
        ),
    )
    return mailbox


def test_message_envelope_summary_is_json_safe():
    envelope = make_message()

    summary = envelope.to_summary()

    assert summary == {
        "message_id": "msg_001",
        "sender_id": "dev_sender",
        "recipient_address": "darwin://global.chat.neo/inbox",
        "lane_signature": "basic_messaging:v1",
        "payload_kind": "text",
        "payload": "hello",
        "metadata": {"simulator_local": True},
    }
    json.dumps(summary)


def test_delivery_result_summary_is_json_safe():
    result = MessageDeliveryResult(
        message_id="msg_001",
        recipient_address="darwin://global.chat.neo/inbox",
        resolved_mailbox_id="mailbox_neo",
        target_device_id="dev_A9F3",
        lane_signature="basic_messaging:v1",
        endpoint_id="endpoint_mailbox_neo",
        status="delivered",
        audit_path=("parsed_recipient_address", "delivered_to_in_memory_inbox"),
        metadata={"simulator_local": True},
    )

    summary = result.to_summary()

    assert summary == {
        "message_id": "msg_001",
        "recipient_address": "darwin://global.chat.neo/inbox",
        "resolved_mailbox_id": "mailbox_neo",
        "target_device_id": "dev_A9F3",
        "lane_signature": "basic_messaging:v1",
        "endpoint_id": "endpoint_mailbox_neo",
        "status": "delivered",
        "reason": None,
        "fallback_action": None,
        "audit_path": [
            "parsed_recipient_address",
            "delivered_to_in_memory_inbox",
        ],
        "metadata": {"simulator_local": True},
    }
    json.dumps(summary)


def test_registry_hub_message_storage_defaults_empty():
    hub = make_hub()

    assert hub.message_inboxes == {}
    assert hub.message_delivery_results == []


def test_basic_successful_in_memory_delivery():
    hub = make_hub()
    register_basic_lane_mailbox_and_endpoint(hub)
    message = make_message()

    result = deliver_message_to_mailbox(hub, message)

    assert result.status.status == "delivered"
    assert result.reason is None
    assert result.resolved_mailbox_id == "mailbox_neo"
    assert result.target_device_id == "dev_A9F3"
    assert result.endpoint_id == "endpoint_mailbox_neo"
    assert get_mailbox_inbox(hub, "mailbox_neo") == [message]
    assert hub.message_delivery_results == [result]
    assert result.metadata["networking"] is False
    assert result.metadata["traffic_hub_routing"] is False


def test_delivery_to_unknown_mailbox_uses_lane_fallback_policy():
    hub = make_hub()
    register_lane_definition(hub, make_basic_messaging_lane_definition("global.chat"))

    result = deliver_message_to_mailbox(
        hub,
        make_message(recipient_address="darwin://global.chat.missing/inbox"),
    )

    assert result.status.status == "bounced"
    assert result.reason.reason == "mailbox_not_found"
    assert result.fallback_action == "bounce"
    assert hub.message_inboxes == {}
    assert hub.message_delivery_results == [result]


def test_missing_lane_definition_fails_clearly():
    hub = make_hub()
    register_mailbox(
        hub,
        make_mailbox(capabilities=(make_basic_capability(),)),
    )

    result = deliver_message_to_mailbox(hub, make_message())

    assert result.status.status == "rejected"
    assert result.reason.reason == "lane_not_registered"
    assert result.fallback_action == "reject"
    assert get_mailbox_inbox(hub, "mailbox_neo") == []


def test_mailbox_missing_capability_fails_clearly():
    hub = make_hub()
    register_lane_definition(hub, make_basic_messaging_lane_definition("global.chat"))
    register_mailbox(hub, make_mailbox())

    result = deliver_message_to_mailbox(hub, make_message())

    assert result.status.status == "rejected"
    assert result.reason.reason == "mailbox_missing_capability"
    assert result.fallback_action == "reject"
    assert get_mailbox_inbox(hub, "mailbox_neo") == []


def test_disabled_capability_fails_clearly():
    hub = make_hub()
    register_basic_lane_mailbox_and_endpoint(hub, capability_enabled=False)

    result = deliver_message_to_mailbox(hub, make_message())

    assert result.status.status == "rejected"
    assert result.reason.reason == "capability_disabled"
    assert result.fallback_action == "reject"
    assert get_mailbox_inbox(hub, "mailbox_neo") == []


def test_missing_endpoint_fails_clearly():
    hub = make_hub()
    register_lane_definition(hub, make_basic_messaging_lane_definition("global.chat"))
    register_mailbox(hub, make_mailbox())
    bind_mailbox_capability(hub, "mailbox_neo", make_basic_capability())

    result = deliver_message_to_mailbox(hub, make_message())

    assert result.status.status == "queued"
    assert result.reason.reason == "endpoint_not_found"
    assert result.fallback_action == "queue_with_retry"
    assert result.metadata["background_retry"] is False
    assert get_mailbox_inbox(hub, "mailbox_neo") == []


def test_unavailable_endpoint_fails_clearly():
    hub = make_hub()
    register_basic_lane_mailbox_and_endpoint(hub, endpoint_status="stale")

    result = deliver_message_to_mailbox(hub, make_message())

    assert result.status.status == "queued"
    assert result.reason.reason == "endpoint_unavailable"
    assert result.endpoint_id == "endpoint_mailbox_neo"
    assert result.fallback_action == "queue_with_retry"
    assert get_mailbox_inbox(hub, "mailbox_neo") == []


def test_endpoint_without_matching_lane_fails_clearly():
    hub = make_hub()
    register_lane_definition(hub, make_basic_messaging_lane_definition("global.chat"))
    register_mailbox(hub, make_mailbox())
    bind_mailbox_capability(hub, "mailbox_neo", make_basic_capability())
    register_adapter_endpoint(
        hub,
        AdapterEndpoint(
            endpoint_id="endpoint_mailbox_neo",
            subject_id="mailbox_neo",
            subject_kind="mailbox",
            adapter_kind="in_memory",
            status="available",
            lane_signatures=("control_plane:v1",),
            scope="global.chat",
        ),
    )

    result = deliver_message_to_mailbox(hub, make_message())

    assert result.status.status == "queued"
    assert result.reason.reason == "endpoint_lane_mismatch"
    assert result.endpoint_id == "endpoint_mailbox_neo"
    assert get_mailbox_inbox(hub, "mailbox_neo") == []


def test_quarantined_target_device_uses_quarantine_fallback():
    hub = make_hub()
    register_basic_lane_mailbox_and_endpoint(hub)
    hub.devices["dev_A9F3"] = LocalDeviceRecord(
        device_id="dev_A9F3",
        requested_label="neo",
        current_label="neo",
        identity_chain="global.chat.neo",
        passport_id="passport_neo",
        current_attachment="hub_chat_001",
        current_state="quarantined",
        checkpoint_tier=1,
    )

    result = deliver_message_to_mailbox(hub, make_message())

    assert result.status.status == "rejected"
    assert result.reason.reason == "recipient_quarantined"
    assert result.fallback_action == "reject"
    assert get_mailbox_inbox(hub, "mailbox_neo") == []


def test_in_transit_target_device_uses_in_transit_fallback():
    hub = make_hub()
    register_basic_lane_mailbox_and_endpoint(hub)
    hub.devices["dev_A9F3"] = LocalDeviceRecord(
        device_id="dev_A9F3",
        requested_label="neo",
        current_label="neo",
        identity_chain="global.chat.neo",
        passport_id="passport_neo",
        current_attachment="hub_chat_001",
        current_state="in_transit",
        checkpoint_tier=1,
    )

    result = deliver_message_to_mailbox(hub, make_message())

    assert result.status.status == "held"
    assert result.reason.reason == "device_in_transit"
    assert result.fallback_action == "hold_until_relocation_resolves"
    assert result.metadata["background_retry"] is False
    assert get_mailbox_inbox(hub, "mailbox_neo") == []


def test_list_delivery_results_by_filters_and_append_order():
    hub = make_hub()
    register_basic_lane_mailbox_and_endpoint(hub)
    first = deliver_message_to_mailbox(hub, make_message("msg_001"))
    second = deliver_message_to_mailbox(hub, make_message("msg_002"))
    missing = deliver_message_to_mailbox(
        hub,
        make_message("msg_003", recipient_address="darwin://global.chat.missing/inbox"),
    )

    assert list_message_delivery_results(hub, message_id="msg_001") == [first]
    assert list_message_delivery_results(
        hub,
        recipient_address="darwin://global.chat.missing/inbox",
    ) == [missing]
    assert list_message_delivery_results(hub, mailbox_id="mailbox_neo") == [
        first,
        second,
    ]
    assert list_message_delivery_results(hub, status="delivered") == [first, second]
    assert list_message_delivery_results(hub, reason="mailbox_not_found") == [missing]
    assert list_message_delivery_results(
        hub,
        lane_signature="basic_messaging:v1",
    ) == [first, second, missing]


def test_delivery_helper_does_not_network_route_or_mutate_identity(monkeypatch):
    def fail_dns(*args, **kwargs):
        raise AssertionError("DNS lookup should not run")

    def fail_socket(*args, **kwargs):
        raise AssertionError("socket should not open")

    monkeypatch.setattr(socket, "getaddrinfo", fail_dns)
    monkeypatch.setattr(socket, "socket", fail_socket)
    registry_hub = make_hub()
    traffic_hub = TrafficHub(hub_id="traffic_chat_001")
    register_basic_lane_mailbox_and_endpoint(registry_hub)
    registry_hub.devices["dev_A9F3"] = LocalDeviceRecord(
        device_id="dev_A9F3",
        requested_label="neo",
        current_label="neo",
        identity_chain="global.chat.neo",
        passport_id="passport_neo",
        current_attachment="hub_chat_001",
        current_state="online",
        checkpoint_tier=1,
    )

    result = deliver_message_to_mailbox(registry_hub, make_message())

    assert result.status.status == "delivered"
    assert registry_hub.devices["dev_A9F3"].current_state == "online"
    assert registry_hub.aliases == {}
    assert registry_hub.alias_bundles == {}
    assert registry_hub.conflicts == {}
    assert registry_hub.authority_outcome_history == []
    assert traffic_hub.routes == {}
    assert traffic_hub.lanes == {}
    assert traffic_hub.forwarding_log == []
    assert result.metadata["networking"] is False
    assert result.metadata["dns_lookup"] is False
    assert result.metadata["traffic_hub_routing"] is False
