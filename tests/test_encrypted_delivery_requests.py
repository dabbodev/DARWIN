import inspect
import json
from copy import deepcopy

import darwin.models.encrypted_delivery as encrypted_delivery_models
from darwin.models import (
    EncryptedDeliveryRequest,
    EncryptedDeliveryRequestMode,
    EncryptedDeliveryRequestStatus,
    LocalDeviceRecord,
    MailboxCapability,
    MailboxIdentity,
    RegistryHub,
    delivery_request_requires_policy,
    delivery_request_status,
    format_mailbox_address,
    is_delivery_request_plaintext,
    is_delivery_request_symbolically_encrypted,
    make_basic_message_envelope,
    make_basic_messaging_lane_definition,
    make_in_memory_mailbox_endpoint,
    make_plaintext_delivery_request,
    make_policy_check_only_delivery_request,
    make_symbolic_encrypted_delivery_request,
    make_symbolic_encrypted_envelope_metadata,
)
from darwin.registry import (
    bind_mailbox_capability,
    deliver_message_to_mailbox,
    get_mailbox_inbox,
    register_adapter_endpoint,
    register_lane_definition,
    register_mailbox,
)


def test_create_plaintext_delivery_request():
    message = _message()

    request = make_plaintext_delivery_request(
        request_id="req_msg_001",
        message_envelope=message,
        mailbox_id="mailbox_neo",
    )

    assert request == EncryptedDeliveryRequest(
        request_id="req_msg_001",
        message_envelope=message,
        encryption_metadata=None,
        mode=EncryptedDeliveryRequestMode("plaintext"),
        policy_required=False,
        policy_id=None,
        mailbox_id="mailbox_neo",
        lane_signature="basic_messaging:v1",
        metadata={
            "simulator_local": True,
            "request_only": True,
            "delivery_behavior_changed": False,
        },
    )
    assert request.encryption_metadata is None
    assert is_delivery_request_plaintext(request) is True
    assert is_delivery_request_symbolically_encrypted(request) is False
    assert delivery_request_requires_policy(request) is False
    assert delivery_request_status(request) == EncryptedDeliveryRequestStatus(
        "plaintext"
    )


def test_create_symbolic_encrypted_delivery_request():
    message = _message()
    metadata = _metadata()

    request = make_symbolic_encrypted_delivery_request(
        request_id="req_msg_001_encrypted",
        message_envelope=message,
        encryption_metadata=metadata,
        mailbox_id="mailbox_neo",
        policy_id="policy_mailbox_neo",
    )

    assert request.message_envelope is message
    assert request.encryption_metadata is metadata
    assert request.mode == EncryptedDeliveryRequestMode("symbolic_encrypted")
    assert request.policy_required is True
    assert request.policy_id == "policy_mailbox_neo"
    assert request.mailbox_id == "mailbox_neo"
    assert request.lane_signature == "basic_messaging:v1"
    assert is_delivery_request_plaintext(request) is False
    assert is_delivery_request_symbolically_encrypted(request) is True
    assert delivery_request_requires_policy(request) is True
    assert delivery_request_status(request) == EncryptedDeliveryRequestStatus(
        "symbolic_encrypted"
    )


def test_delivery_request_summary_is_json_safe():
    message = _message()
    metadata = _metadata()
    request = make_symbolic_encrypted_delivery_request(
        request_id="req_msg_001_encrypted",
        message_envelope=message,
        encryption_metadata=metadata,
        mailbox_id="mailbox_neo",
        policy_id="policy_mailbox_neo",
    )

    summary = request.to_summary()

    assert summary == {
        "request_id": "req_msg_001_encrypted",
        "message_envelope": message.to_summary(),
        "encryption_metadata": metadata.to_summary(),
        "mode": "symbolic_encrypted",
        "policy_required": True,
        "policy_id": "policy_mailbox_neo",
        "mailbox_id": "mailbox_neo",
        "lane_signature": "basic_messaging:v1",
        "metadata": {
            "simulator_local": True,
            "request_only": True,
            "delivery_behavior_changed": False,
            "real_ciphertext": False,
        },
    }
    assert request.to_dict() == summary
    json.dumps(summary)


def test_request_can_store_json_safe_summaries():
    message = _message().to_summary()
    metadata = _metadata().to_summary()

    request = EncryptedDeliveryRequest(
        request_id="req_msg_001_summary",
        message_envelope=message,
        encryption_metadata=metadata,
        mode="symbolic_encrypted",
        policy_required=True,
        policy_id="policy_mailbox_neo",
        mailbox_id="mailbox_neo",
        metadata={"labels": ("summary",)},
    )

    assert request.message_envelope == message
    assert request.encryption_metadata == metadata
    assert request.lane_signature == "basic_messaging:v1"
    assert request.to_summary()["metadata"] == {"labels": ["summary"]}
    json.dumps(request.to_summary())


def test_policy_check_only_request_has_no_message_or_encryption_metadata():
    request = make_policy_check_only_delivery_request(
        request_id="req_policy_only",
        mailbox_id="mailbox_neo",
        policy_id="policy_mailbox_neo",
    )

    assert request.message_envelope is None
    assert request.encryption_metadata is None
    assert request.mode == EncryptedDeliveryRequestMode("policy_check_only")
    assert request.policy_required is True
    assert request.lane_signature == "basic_messaging:v1"
    assert delivery_request_status(request) == EncryptedDeliveryRequestStatus(
        "policy_check_only"
    )


def test_default_lane_signature_is_preserved_from_message_envelope():
    message = make_basic_message_envelope(
        message_id="msg_001",
        sender_id="dev_sender",
        recipient_address="darwin://global.chat.neo/inbox",
        payload="hello",
    )

    request = make_plaintext_delivery_request(
        request_id="req_msg_001",
        message_envelope=message,
    )

    assert request.lane_signature == message.lane_signature
    assert request.lane_signature == "basic_messaging:v1"


def test_request_construction_does_not_mutate_message_or_encryption_metadata():
    message = _message()
    metadata = _metadata()
    before = {
        "message": deepcopy(message.to_summary()),
        "metadata": deepcopy(metadata.to_summary()),
    }

    make_symbolic_encrypted_delivery_request(
        request_id="req_msg_001_encrypted",
        message_envelope=message,
        encryption_metadata=metadata,
        mailbox_id="mailbox_neo",
        policy_id="policy_mailbox_neo",
    )

    assert message.to_summary() == before["message"]
    assert metadata.to_summary() == before["metadata"]


def test_request_construction_does_not_deliver_or_mutate_registry_hub():
    hub = _registered_delivery_hub()
    message = _message()

    make_plaintext_delivery_request(
        request_id="req_msg_001",
        message_envelope=message,
        mailbox_id="mailbox_neo",
    )

    assert hub.message_inboxes == {}
    assert hub.message_delivery_results == []


def test_existing_plaintext_delivery_behavior_remains_unchanged():
    hub = _registered_delivery_hub()
    message = _message()

    result = deliver_message_to_mailbox(hub, message)

    assert result.status.status == "delivered"
    assert result.reason is None
    assert get_mailbox_inbox(hub, "mailbox_neo") == [message]
    assert hub.message_delivery_results == [result]
    assert result.metadata["networking"] is False
    assert result.metadata["traffic_hub_routing"] is False


def test_encrypted_delivery_model_does_not_import_crypto_libraries():
    source = inspect.getsource(encrypted_delivery_models)

    assert "import hmac" not in source
    assert "import hashlib" not in source
    assert "import secrets" not in source
    assert "import cryptography" not in source
    assert "from cryptography" not in source


def _message():
    return make_basic_message_envelope(
        message_id="msg_001",
        sender_id="dev_sender",
        recipient_address="darwin://global.chat.neo/inbox",
        payload="hello",
    )


def _metadata():
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
        MailboxIdentity(
            mailbox_id="mailbox_neo",
            canonical_device_id="dev_A9F3",
            local_name="neo",
            scope="global.chat",
            address=format_mailbox_address("global.chat", "neo"),
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
