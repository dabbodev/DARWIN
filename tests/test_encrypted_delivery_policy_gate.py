import inspect
import json
from copy import deepcopy

import darwin.registry.encrypted_delivery_policy as encrypted_delivery_policy
from darwin.models import (
    EncryptedEnvelopeMetadata,
    EncryptionIdentity,
    KeyBundleReference,
    LocalDeviceRecord,
    MailboxCapability,
    MailboxEncryptionBinding,
    RegistryHub,
    is_encrypted_delivery_gate_allowed,
    is_encrypted_delivery_gate_blocked,
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
    deliver_message_to_mailbox,
    evaluate_encrypted_delivery_request_policy,
    get_mailbox_inbox,
    make_basic_messaging_mailbox,
    register_adapter_endpoint,
    register_encryption_identity,
    register_key_bundle_reference,
    register_lane_definition,
    register_mailbox,
    register_mailbox_encryption_binding,
    register_mailbox_encryption_policy,
)


def test_plaintext_request_with_no_policy_required_is_allowed():
    hub = _registered_mailbox_hub()
    request = make_plaintext_delivery_request(
        request_id="req_msg_001",
        message_envelope=_message(),
        mailbox_id="mailbox_neo",
    )

    decision = evaluate_encrypted_delivery_request_policy(hub, request)

    assert decision.status.status == "plaintext_allowed"
    assert decision.reason.reason == "plaintext_no_policy_required"
    assert decision.delivery_allowed is True
    assert decision.policy_required is False
    assert decision.policy_decision is None
    assert decision.metadata["delivery_result_created"] is False
    assert hub.encryption_policy_decision_history == []


def test_request_requiring_policy_with_no_policy_is_blocked_deterministically():
    hub = _registered_mailbox_hub()
    request = make_policy_check_only_delivery_request(
        request_id="req_policy_only",
        mailbox_id="mailbox_neo",
        policy_id=None,
    )

    decision = evaluate_encrypted_delivery_request_policy(hub, request)

    assert decision.status.status == "policy_missing"
    assert decision.reason.reason == "policy_not_found"
    assert decision.delivery_allowed is False
    assert decision.policy_required is True
    assert decision.policy_decision is None
    assert hub.encryption_policy_decision_history == []


def test_symbolic_encrypted_request_with_registered_policy_is_allowed():
    hub = _prepared_policy_hub()
    request = _encrypted_request()

    decision = evaluate_encrypted_delivery_request_policy(hub, request)

    assert decision.status.status == "allowed"
    assert decision.reason.reason == "accepted"
    assert decision.delivery_allowed is True
    assert decision.envelope_accepted is True
    assert decision.policy_decision.status.status == "accepted"
    assert hub.encryption_policy_decision_history == [decision.policy_decision]


def test_missing_envelope_for_required_lane_is_blocked():
    hub = _prepared_policy_hub()
    request = make_policy_check_only_delivery_request(
        request_id="req_policy_only",
        mailbox_id="mailbox_neo",
        policy_id="policy_mailbox_neo",
    )

    decision = evaluate_encrypted_delivery_request_policy(hub, request)

    assert decision.status.status == "policy_check_failed"
    assert decision.reason.reason == "missing_envelope"
    assert decision.delivery_allowed is False
    assert decision.policy_decision.status.status == "missing_envelope"


def test_unsupported_profile_is_blocked():
    hub = _prepared_policy_hub()
    request = _encrypted_request(
        encryption_metadata=make_symbolic_encrypted_envelope_metadata(
            envelope_id="env_msg_001",
            message_id="msg_001",
            encryption_identity_id="enc_mailbox_neo",
            key_bundle_id="kb_mailbox_neo_001",
            profile="future_symbolic_profile",
        ),
    )

    decision = evaluate_encrypted_delivery_request_policy(hub, request)

    assert decision.status.status == "policy_check_failed"
    assert decision.reason.reason == "unsupported_profile"
    assert decision.delivery_allowed is False


def test_inactive_identity_is_blocked():
    hub = _prepared_policy_hub(
        identity=EncryptionIdentity(
            encryption_identity_id="enc_mailbox_neo",
            subject_id="mailbox_neo",
            subject_kind="mailbox",
            status="disabled",
        ),
    )

    decision = evaluate_encrypted_delivery_request_policy(hub, _encrypted_request())

    assert decision.status.status == "policy_check_failed"
    assert decision.reason.reason == "identity_inactive"
    assert decision.delivery_allowed is False


def test_unusable_key_bundle_is_blocked():
    hub = _prepared_policy_hub(
        key_bundle=KeyBundleReference(
            key_bundle_id="kb_mailbox_neo_001",
            encryption_identity_id="enc_mailbox_neo",
            status="stale",
        ),
    )

    decision = evaluate_encrypted_delivery_request_policy(hub, _encrypted_request())

    assert decision.status.status == "policy_check_failed"
    assert decision.reason.reason == "key_bundle_unusable"
    assert decision.delivery_allowed is False


def test_not_ready_envelope_is_blocked():
    hub = _prepared_policy_hub()
    request = _encrypted_request(
        encryption_metadata=EncryptedEnvelopeMetadata(
            envelope_id="env_msg_001",
            message_id="msg_001",
            encryption_identity_id="enc_mailbox_neo",
            key_bundle_id="kb_mailbox_neo_001",
            state="symbolically_encrypted",
            status="stale_key_bundle",
            algorithm_ref="symbolic-envelope",
            ciphertext_ref="symbolic://ciphertext/env_msg_001",
        ),
    )

    decision = evaluate_encrypted_delivery_request_policy(hub, request)

    assert decision.status.status == "policy_check_failed"
    assert decision.reason.reason == "envelope_not_ready"
    assert decision.delivery_allowed is False


def test_retain_decision_true_appends_one_policy_decision():
    hub = _prepared_policy_hub()

    decision = evaluate_encrypted_delivery_request_policy(
        hub,
        _encrypted_request(),
        retain_decision=True,
    )

    assert hub.encryption_policy_decision_history == [decision.policy_decision]
    assert decision.metadata["policy_decision_retained"] is True


def test_retain_decision_false_does_not_append_policy_decision():
    hub = _prepared_policy_hub()

    decision = evaluate_encrypted_delivery_request_policy(
        hub,
        _encrypted_request(),
        retain_decision=False,
    )

    assert decision.policy_decision.status.status == "accepted"
    assert hub.encryption_policy_decision_history == []
    assert decision.metadata["policy_decision_retained"] is False


def test_gate_decision_summary_is_json_safe_and_predicates_work():
    hub = _prepared_policy_hub()
    decision = evaluate_encrypted_delivery_request_policy(hub, _encrypted_request())

    summary = decision.to_summary()

    assert summary["request_id"] == "req_msg_001_encrypted"
    assert summary["message_id"] == "msg_001"
    assert summary["mailbox_id"] == "mailbox_neo"
    assert summary["lane_signature"] == "basic_messaging:v1"
    assert summary["policy_id"] == "policy_mailbox_neo"
    assert summary["status"] == "allowed"
    assert summary["reason"] == "accepted"
    assert summary["policy_decision"]["status"] == "accepted"
    assert summary["delivery_allowed"] is True
    assert summary["policy_required"] is True
    assert summary["envelope_accepted"] is True
    assert decision.to_dict() == summary
    json.dumps(summary, sort_keys=True)
    assert is_encrypted_delivery_gate_allowed(decision) is True
    assert is_encrypted_delivery_gate_blocked(decision) is False


def test_gate_helper_does_not_mutate_inboxes_or_delivery_results():
    hub = _prepared_delivery_and_policy_hub()
    request = _encrypted_request()
    before = {
        "message_inboxes": deepcopy(hub.message_inboxes),
        "message_delivery_results": deepcopy(hub.message_delivery_results),
    }

    evaluate_encrypted_delivery_request_policy(hub, request)

    assert hub.message_inboxes == before["message_inboxes"]
    assert hub.message_delivery_results == before["message_delivery_results"]


def test_gate_helper_does_not_call_delivery_helper():
    source = inspect.getsource(encrypted_delivery_policy)

    assert "deliver_message_to_mailbox" not in source


def test_existing_plaintext_delivery_helper_remains_unchanged():
    hub = _prepared_delivery_and_policy_hub()
    message = _message()

    result = deliver_message_to_mailbox(hub, message)

    assert result.status.status == "delivered"
    assert result.reason is None
    assert get_mailbox_inbox(hub, "mailbox_neo") == [message]
    assert hub.message_delivery_results == [result]


def test_encrypted_delivery_policy_gate_does_not_import_crypto_libraries():
    source = inspect.getsource(encrypted_delivery_policy)

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


def _encrypted_request(encryption_metadata=None):
    return make_symbolic_encrypted_delivery_request(
        request_id="req_msg_001_encrypted",
        message_envelope=_message(),
        encryption_metadata=(
            _ready_envelope() if encryption_metadata is None else encryption_metadata
        ),
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


def _registered_mailbox_hub() -> RegistryHub:
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
    return hub


def _prepared_policy_hub(
    *,
    identity: EncryptionIdentity | None = None,
    key_bundle: KeyBundleReference | None = None,
) -> RegistryHub:
    hub = _registered_mailbox_hub()
    register_encryption_identity(
        hub,
        _identity() if identity is None else identity,
    )
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


def _prepared_delivery_and_policy_hub() -> RegistryHub:
    hub = _prepared_policy_hub()
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


def _identity() -> EncryptionIdentity:
    return make_symbolic_encryption_identity(
        encryption_identity_id="enc_mailbox_neo",
        subject_id="mailbox_neo",
        subject_kind="mailbox",
    )


def _key_bundle() -> KeyBundleReference:
    return make_symbolic_key_bundle_reference(
        key_bundle_id="kb_mailbox_neo_001",
        encryption_identity_id="enc_mailbox_neo",
        public_ref="symbolic://public/mailbox_neo/001",
    )


def _binding() -> MailboxEncryptionBinding:
    return MailboxEncryptionBinding(
        mailbox_id="mailbox_neo",
        encryption_identity_id="enc_mailbox_neo",
        key_bundle_id="kb_mailbox_neo_001",
        required_for_lanes=("basic_messaging:v1",),
    )
