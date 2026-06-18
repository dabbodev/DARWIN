import inspect
import json
import socket
from copy import deepcopy

import darwin.models.encrypted_delivery as encrypted_delivery_models
import darwin.registry.encrypted_delivery as encrypted_delivery_registry
from darwin.models import (
    EncryptedDeliveryAuditEntry,
    EncryptedDeliveryResult,
    EncryptedDeliveryResultStatus,
    EncryptionIdentity,
    KeyBundleReference,
    LocalDeviceRecord,
    MailboxCapability,
    MailboxEncryptionBinding,
    RegistryHub,
    is_encrypted_delivery_result_allowed,
    is_encrypted_delivery_result_blocked,
    is_encrypted_delivery_result_delivered,
    make_basic_message_envelope,
    make_basic_messaging_lane_definition,
    make_in_memory_mailbox_endpoint,
    make_mailbox_encryption_policy,
    make_plaintext_delivery_request,
    make_policy_check_only_delivery_request,
    make_symbolic_encrypted_delivery_request,
    make_symbolic_encrypted_envelope_metadata,
    make_symbolic_encryption_identity,
    make_symbolic_key_bundle_reference,
)
from darwin.registry import (
    bind_mailbox_capability,
    build_encrypted_delivery_audit_entry,
    deliver_message_to_mailbox,
    evaluate_encrypted_delivery_request,
    get_mailbox_inbox,
    make_basic_messaging_mailbox,
    register_adapter_endpoint,
    register_encryption_identity,
    register_key_bundle_reference,
    register_lane_definition,
    register_mailbox,
    register_mailbox_encryption_binding,
    register_mailbox_encryption_policy,
    summarize_encrypted_delivery_result,
)


def test_gate_blocked_request_returns_no_delivery_attempt():
    hub = _prepared_delivery_and_policy_hub(key_bundle=_key_bundle(status="stale"))
    request = _encrypted_request()

    result = evaluate_encrypted_delivery_request(hub, request)

    assert result.status == EncryptedDeliveryResultStatus("gate_blocked")
    assert result.reason == "key_bundle_unusable"
    assert result.delivery_allowed is False
    assert result.delivery_attempted is False
    assert result.delivery_result is None
    assert result.gate_decision.status.status == "policy_check_failed"
    assert get_mailbox_inbox(hub, "mailbox_neo") == []
    assert hub.message_delivery_results == []


def test_policy_check_only_request_returns_no_delivery_attempt():
    hub = _prepared_policy_hub()
    request = make_policy_check_only_delivery_request(
        request_id="req_policy_only",
        mailbox_id="mailbox_neo",
        policy_id="policy_mailbox_neo",
    )

    result = evaluate_encrypted_delivery_request(hub, request)

    assert result.status.status == "policy_check_only"
    assert result.delivery_attempted is False
    assert result.delivery_result is None
    assert result.metadata["attempt_delivery_requested"] is False
    assert hub.message_inboxes == {}
    assert hub.message_delivery_results == []


def test_gate_allowed_without_attempt_returns_not_delivered_result():
    hub = _prepared_delivery_and_policy_hub()
    request = _encrypted_request()
    before = _delivery_state(hub)

    result = evaluate_encrypted_delivery_request(hub, request, attempt_delivery=False)

    assert result.status.status == "not_delivered"
    assert result.reason == "delivery_not_attempted"
    assert result.delivery_allowed is True
    assert result.delivery_attempted is False
    assert result.delivery_result is None
    assert result.metadata["delivery_result_created"] is False
    assert _delivery_state(hub) == before


def test_gate_allowed_with_attempt_uses_existing_delivery_helper():
    hub = _prepared_delivery_and_policy_hub()
    request = _encrypted_request()

    result = evaluate_encrypted_delivery_request(hub, request, attempt_delivery=True)

    assert result.status.status == "delivered"
    assert result.reason is None
    assert result.delivery_allowed is True
    assert result.delivery_attempted is True
    assert result.delivery_result.status.status == "delivered"
    assert get_mailbox_inbox(hub, "mailbox_neo") == [request.message_envelope]
    assert hub.message_delivery_results == [result.delivery_result]
    assert result.metadata["delivery_result_created"] is True
    assert result.metadata["message_delivery_results_mutated"] is True
    assert result.metadata["inbox_mutated"] is True


def test_existing_direct_delivery_behavior_remains_unchanged():
    hub = _prepared_delivery_and_policy_hub()
    message = _message()

    result = deliver_message_to_mailbox(hub, message)

    assert result.status.status == "delivered"
    assert result.reason is None
    assert get_mailbox_inbox(hub, "mailbox_neo") == [message]
    assert hub.message_delivery_results == [result]


def test_wrapped_result_summary_is_json_safe_and_predicates_work():
    hub = _prepared_delivery_and_policy_hub()
    result = evaluate_encrypted_delivery_request(hub, _encrypted_request())

    summary = summarize_encrypted_delivery_result(result)

    assert summary["request_id"] == "req_msg_001_encrypted"
    assert summary["message_id"] == "msg_001"
    assert summary["mailbox_id"] == "mailbox_neo"
    assert summary["lane_signature"] == "basic_messaging:v1"
    assert summary["gate_decision"]["status"] == "allowed"
    assert summary["delivery_result"] is None
    assert summary["status"] == "not_delivered"
    assert result.to_dict() == summary
    json.dumps(summary, sort_keys=True)
    assert is_encrypted_delivery_result_allowed(result) is True
    assert is_encrypted_delivery_result_blocked(result) is False
    assert is_encrypted_delivery_result_delivered(result) is False


def test_audit_entry_summary_is_json_safe():
    hub = _prepared_delivery_and_policy_hub()
    result = evaluate_encrypted_delivery_request(
        hub,
        _encrypted_request(),
        attempt_delivery=True,
    )

    audit_entry = build_encrypted_delivery_audit_entry(result)

    assert isinstance(audit_entry, EncryptedDeliveryAuditEntry)
    summary = audit_entry.to_summary()
    assert summary == {
        "request_id": "req_msg_001_encrypted",
        "message_id": "msg_001",
        "mailbox_id": "mailbox_neo",
        "lane_signature": "basic_messaging:v1",
        "gate_status": "allowed",
        "gate_reason": "accepted",
        "delivery_status": "delivered",
        "delivery_reason": None,
        "policy_id": "policy_mailbox_neo",
        "encryption_required": True,
        "envelope_accepted": True,
        "metadata": {
            "simulator_local": True,
            "wrapped_result": True,
            "delivery_attempted": True,
            "delivery_allowed": True,
            "policy_required": True,
            "persistent_wrapped_history": False,
        },
    }
    json.dumps(summary, sort_keys=True)


def test_blocked_request_does_not_mutate_inboxes_or_delivery_results():
    hub = _prepared_delivery_and_policy_hub(identity=_identity(status="disabled"))
    before = _delivery_state(hub)

    result = evaluate_encrypted_delivery_request(
        hub,
        _encrypted_request(),
        attempt_delivery=True,
    )

    assert result.status.status == "gate_blocked"
    assert result.delivery_attempted is False
    assert _delivery_state(hub) == before


def test_allowed_no_attempt_does_not_mutate_inboxes_or_delivery_results():
    hub = _prepared_delivery_and_policy_hub()
    before = _delivery_state(hub)

    result = evaluate_encrypted_delivery_request(
        hub,
        _encrypted_request(),
        attempt_delivery=False,
    )

    assert result.delivery_allowed is True
    assert result.delivery_attempted is False
    assert _delivery_state(hub) == before


def test_allowed_attempt_mutates_only_normal_delivery_state():
    hub = _prepared_delivery_and_policy_hub()
    message = _message()
    request = make_symbolic_encrypted_delivery_request(
        request_id="req_msg_001_encrypted",
        message_envelope=message,
        encryption_metadata=_ready_envelope(),
        mailbox_id="mailbox_neo",
        policy_id="policy_mailbox_neo",
    )
    before_devices = deepcopy(hub.devices)
    before_mailboxes = deepcopy(hub.mailboxes)
    before_policies = deepcopy(hub.mailbox_encryption_policies)

    result = evaluate_encrypted_delivery_request(
        hub,
        request,
        attempt_delivery=True,
    )

    assert result.status.status == "delivered"
    assert get_mailbox_inbox(hub, "mailbox_neo") == [message]
    assert hub.message_delivery_results == [result.delivery_result]
    assert hub.devices == before_devices
    assert hub.mailboxes == before_mailboxes
    assert hub.mailbox_encryption_policies == before_policies


def test_policy_decision_retention_respects_retain_policy_decision():
    hub = _prepared_policy_hub()

    retained = evaluate_encrypted_delivery_request(
        hub,
        _encrypted_request(),
        retain_policy_decision=True,
    )

    assert hub.encryption_policy_decision_history == [
        retained.gate_decision.policy_decision
    ]
    assert retained.metadata["policy_decision_retained"] is True

    hub = _prepared_policy_hub()
    not_retained = evaluate_encrypted_delivery_request(
        hub,
        _encrypted_request(),
        retain_policy_decision=False,
    )

    assert not_retained.gate_decision.policy_decision.status.status == "accepted"
    assert hub.encryption_policy_decision_history == []
    assert not_retained.metadata["policy_decision_retained"] is False


def test_plaintext_allowed_no_policy_request_does_not_enforce_delivery_by_default():
    hub = _registered_delivery_hub()
    request = make_plaintext_delivery_request(
        request_id="req_msg_001_plaintext",
        message_envelope=_message(),
        mailbox_id="mailbox_neo",
    )

    result = evaluate_encrypted_delivery_request(hub, request)

    assert result.gate_decision.status.status == "plaintext_allowed"
    assert result.status.status == "not_delivered"
    assert result.delivery_allowed is True
    assert result.delivery_attempted is False
    assert get_mailbox_inbox(hub, "mailbox_neo") == []
    assert hub.message_delivery_results == []


def test_wrapped_result_models_can_store_json_safe_summaries():
    hub = _prepared_delivery_and_policy_hub()
    result = evaluate_encrypted_delivery_request(hub, _encrypted_request())
    summary = result.to_summary()

    copied = EncryptedDeliveryResult(
        request_id=result.request_id,
        message_id=result.message_id,
        mailbox_id=result.mailbox_id,
        lane_signature=result.lane_signature,
        gate_decision=summary["gate_decision"],
        delivery_result=summary["delivery_result"],
        status=summary["status"],
        reason=summary["reason"],
        delivery_attempted=summary["delivery_attempted"],
        delivery_allowed=summary["delivery_allowed"],
        policy_required=summary["policy_required"],
        metadata={"labels": ("summary",)},
    )

    assert copied.gate_decision == summary["gate_decision"]
    assert copied.metadata == {"labels": ["summary"]}
    json.dumps(copied.to_summary(), sort_keys=True)


def test_no_real_crypto_networking_dns_or_socket_behavior(monkeypatch):
    def fail_dns(*args, **kwargs):
        raise AssertionError("DNS lookup should not run")

    def fail_socket(*args, **kwargs):
        raise AssertionError("socket should not open")

    monkeypatch.setattr(socket, "getaddrinfo", fail_dns)
    monkeypatch.setattr(socket, "socket", fail_socket)
    hub = _prepared_delivery_and_policy_hub()

    result = evaluate_encrypted_delivery_request(
        hub,
        _encrypted_request(),
        attempt_delivery=True,
    )

    assert result.status.status == "delivered"
    assert result.metadata["networking"] is False
    assert result.metadata["dns_lookup"] is False

    model_source = inspect.getsource(encrypted_delivery_models)
    registry_source = inspect.getsource(encrypted_delivery_registry)
    combined_source = model_source + registry_source
    assert "import hmac" not in combined_source
    assert "import hashlib" not in combined_source
    assert "import secrets" not in combined_source
    assert "import cryptography" not in combined_source
    assert "from cryptography" not in combined_source
    assert "socket.getaddrinfo" not in registry_source
    assert "socket.socket" not in registry_source


def _message():
    return make_basic_message_envelope(
        message_id="msg_001",
        sender_id="dev_sender",
        recipient_address="darwin://global.chat.neo/inbox",
        payload="hello",
    )


def _encrypted_request():
    return make_symbolic_encrypted_delivery_request(
        request_id="req_msg_001_encrypted",
        message_envelope=_message(),
        encryption_metadata=_ready_envelope(),
        mailbox_id="mailbox_neo",
        policy_id="policy_mailbox_neo",
    )


def _ready_envelope():
    return make_symbolic_encrypted_envelope_metadata(
        envelope_id="env_msg_001",
        message_id="msg_001",
        encryption_identity_id="enc_mailbox_neo",
        key_bundle_id="kb_mailbox_neo_001",
    )


def _registered_delivery_hub() -> RegistryHub:
    hub = RegistryHub(hub_id="hub_chat_001", scope_path="global.chat")
    register_lane_definition(hub, make_basic_messaging_lane_definition("global.chat"))
    register_mailbox(
        hub,
        make_basic_messaging_mailbox(
            mailbox_id="mailbox_neo",
            canonical_device_id="dev_A9F3",
            local_name="neo",
            scope="global.chat",
        ),
    )
    bind_mailbox_capability(
        hub,
        "mailbox_neo",
        MailboxCapability(
            capability_id="cap_basic_messaging",
            lane_signature="basic_messaging:v1",
        ),
    )
    register_adapter_endpoint(
        hub,
        make_in_memory_mailbox_endpoint(
            endpoint_id="endpoint_mailbox_neo",
            mailbox_id="mailbox_neo",
            scope="global.chat",
        ),
    )
    hub.devices["dev_A9F3"] = LocalDeviceRecord(
        device_id="dev_A9F3",
        requested_label="neo",
        current_label="neo",
        identity_chain="global.chat.neo",
        passport_id="passport_neo",
        current_attachment="hub_chat_001",
        current_state="online",
        checkpoint_tier=1,
    )
    return hub


def _prepared_policy_hub(
    *,
    identity: EncryptionIdentity | None = None,
    key_bundle: KeyBundleReference | None = None,
) -> RegistryHub:
    hub = RegistryHub(hub_id="hub_chat_001", scope_path="global.chat")
    register_mailbox(
        hub,
        make_basic_messaging_mailbox(
            mailbox_id="mailbox_neo",
            canonical_device_id="dev_A9F3",
            local_name="neo",
            scope="global.chat",
        ),
    )
    register_encryption_identity(hub, _identity() if identity is None else identity)
    register_key_bundle_reference(
        hub,
        _key_bundle() if key_bundle is None else key_bundle,
    )
    register_mailbox_encryption_binding(hub, _binding())
    register_mailbox_encryption_policy(
        hub,
        make_mailbox_encryption_policy(
            policy_id="policy_mailbox_neo",
            mailbox_id="mailbox_neo",
        ),
    )
    return hub


def _prepared_delivery_and_policy_hub(
    *,
    identity: EncryptionIdentity | None = None,
    key_bundle: KeyBundleReference | None = None,
) -> RegistryHub:
    hub = _prepared_policy_hub(identity=identity, key_bundle=key_bundle)
    register_lane_definition(hub, make_basic_messaging_lane_definition("global.chat"))
    bind_mailbox_capability(
        hub,
        "mailbox_neo",
        MailboxCapability(
            capability_id="cap_basic_messaging",
            lane_signature="basic_messaging:v1",
        ),
    )
    register_adapter_endpoint(
        hub,
        make_in_memory_mailbox_endpoint(
            endpoint_id="endpoint_mailbox_neo",
            mailbox_id="mailbox_neo",
            scope="global.chat",
        ),
    )
    hub.devices["dev_A9F3"] = LocalDeviceRecord(
        device_id="dev_A9F3",
        requested_label="neo",
        current_label="neo",
        identity_chain="global.chat.neo",
        passport_id="passport_neo",
        current_attachment="hub_chat_001",
        current_state="online",
        checkpoint_tier=1,
    )
    return hub


def _identity(status: str = "active") -> EncryptionIdentity:
    identity = make_symbolic_encryption_identity(
        encryption_identity_id="enc_mailbox_neo",
        subject_id="mailbox_neo",
        subject_kind="mailbox",
    )
    if status == "active":
        return identity
    return EncryptionIdentity(
        encryption_identity_id="enc_mailbox_neo",
        subject_id="mailbox_neo",
        subject_kind="mailbox",
        status=status,
    )


def _key_bundle(status: str = "active") -> KeyBundleReference:
    if status == "active":
        return make_symbolic_key_bundle_reference(
            key_bundle_id="kb_mailbox_neo_001",
            encryption_identity_id="enc_mailbox_neo",
            public_ref="symbolic://public/mailbox_neo/001",
        )
    return KeyBundleReference(
        key_bundle_id="kb_mailbox_neo_001",
        encryption_identity_id="enc_mailbox_neo",
        status=status,
    )


def _binding() -> MailboxEncryptionBinding:
    return MailboxEncryptionBinding(
        mailbox_id="mailbox_neo",
        encryption_identity_id="enc_mailbox_neo",
        key_bundle_id="kb_mailbox_neo_001",
        required_for_lanes=("basic_messaging:v1",),
    )


def _delivery_state(hub: RegistryHub) -> dict[str, object]:
    return {
        "message_inboxes": deepcopy(hub.message_inboxes),
        "message_delivery_results": deepcopy(hub.message_delivery_results),
    }
