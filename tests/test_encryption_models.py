import inspect
import json
import socket
from copy import deepcopy
from dataclasses import fields

import pytest

import darwin.models.encryption as encryption_models
from darwin.models import (
    DEFAULT_ENCRYPTION_PROFILE,
    DEFAULT_SYMBOLIC_ENVELOPE_ALGORITHM_REF,
    EncryptedEnvelopeMetadata,
    EncryptionEnvelopeStatus,
    EncryptionIdentity,
    EncryptionProfile,
    EncryptionState,
    KeyBundleReference,
    KeyBundleStatus,
    LocalDeviceRecord,
    MailboxCapability,
    MailboxEncryptionBinding,
    MailboxIdentity,
    RegistryHub,
    SymbolicEncryptedMessageEnvelope,
    TrafficHub,
    bind_mailbox_encryption_identity,
    format_mailbox_address,
    is_encryption_identity_active,
    is_encryption_profile_supported,
    is_envelope_ready_for_delivery,
    is_envelope_symbolically_encrypted,
    is_key_bundle_usable,
    make_basic_message_envelope,
    make_basic_messaging_lane_definition,
    make_in_memory_mailbox_endpoint,
    make_symbolic_encrypted_envelope_metadata,
    make_symbolic_encryption_identity,
    make_symbolic_key_bundle_reference,
    wrap_message_symbolically,
)
from darwin.registry import (
    bind_mailbox_capability,
    deliver_message_to_mailbox,
    get_mailbox_inbox,
    register_adapter_endpoint,
    register_lane_definition,
    register_mailbox,
)


def test_create_symbolic_encryption_identity():
    identity = make_symbolic_encryption_identity(
        encryption_identity_id="enc_mailbox_neo",
        subject_id="mailbox_neo",
        subject_kind="mailbox",
    )

    assert identity == EncryptionIdentity(
        encryption_identity_id="enc_mailbox_neo",
        subject_id="mailbox_neo",
        subject_kind="mailbox",
        profile=DEFAULT_ENCRYPTION_PROFILE,
        status="active",
        metadata={"simulator_local": True},
    )


def test_create_symbolic_key_bundle_reference():
    key_bundle = make_symbolic_key_bundle_reference(
        key_bundle_id="kb_mailbox_neo_001",
        encryption_identity_id="enc_mailbox_neo",
        public_ref="symbolic://public/mailbox_neo/001",
    )

    assert key_bundle.key_bundle_id == "kb_mailbox_neo_001"
    assert key_bundle.encryption_identity_id == "enc_mailbox_neo"
    assert key_bundle.profile == DEFAULT_ENCRYPTION_PROFILE
    assert key_bundle.status == KeyBundleStatus("active")
    assert key_bundle.public_ref == "symbolic://public/mailbox_neo/001"
    assert key_bundle.metadata == {
        "simulator_local": True,
        "symbolic_public_ref": True,
    }


def test_create_mailbox_encryption_binding():
    binding = bind_mailbox_encryption_identity(
        mailbox_id="mailbox_neo",
        encryption_identity_id="enc_mailbox_neo",
        key_bundle_id="kb_mailbox_neo_001",
        required_for_lanes=("basic_messaging:v1",),
    )

    assert binding == MailboxEncryptionBinding(
        mailbox_id="mailbox_neo",
        encryption_identity_id="enc_mailbox_neo",
        key_bundle_id="kb_mailbox_neo_001",
        required_for_lanes=("basic_messaging:v1",),
        profile=DEFAULT_ENCRYPTION_PROFILE,
        status="active",
        metadata={"simulator_local": True},
    )


def test_default_profile_is_symbolic_e2ee_v1():
    assert EncryptionProfile().profile == "symbolic_e2ee_v1"
    assert DEFAULT_ENCRYPTION_PROFILE == "symbolic_e2ee_v1"
    assert (
        make_symbolic_encryption_identity(
            encryption_identity_id="enc_mailbox_neo",
            subject_id="mailbox_neo",
            subject_kind="mailbox",
        ).profile
        == "symbolic_e2ee_v1"
    )


def test_create_symbolic_encrypted_envelope_metadata():
    metadata = make_symbolic_encrypted_envelope_metadata(
        envelope_id="env_msg_001",
        message_id="msg_001",
        encryption_identity_id="enc_mailbox_neo",
        key_bundle_id="kb_mailbox_neo_001",
    )

    assert metadata == EncryptedEnvelopeMetadata(
        envelope_id="env_msg_001",
        message_id="msg_001",
        encryption_identity_id="enc_mailbox_neo",
        key_bundle_id="kb_mailbox_neo_001",
        profile=DEFAULT_ENCRYPTION_PROFILE,
        state=EncryptionState("symbolically_encrypted"),
        status=EncryptionEnvelopeStatus("ready"),
        algorithm_ref=DEFAULT_SYMBOLIC_ENVELOPE_ALGORITHM_REF,
        ciphertext_ref="symbolic://ciphertext/env_msg_001",
        plaintext_ref=None,
        metadata={
            "simulator_local": True,
            "symbolic_envelope": True,
            "real_ciphertext": False,
        },
    )


def test_symbolic_encrypted_envelope_defaults_are_symbolic_only():
    metadata = make_symbolic_encrypted_envelope_metadata(
        envelope_id="env_msg_001",
        message_id="msg_001",
        encryption_identity_id="enc_mailbox_neo",
        key_bundle_id="kb_mailbox_neo_001",
        ciphertext_ref="symbolic://ciphertext/custom",
    )

    assert metadata.profile == "symbolic_e2ee_v1"
    assert metadata.algorithm_ref == "symbolic-envelope"
    assert metadata.ciphertext_ref == "symbolic://ciphertext/custom"
    assert metadata.metadata["real_ciphertext"] is False


def test_plaintext_envelope_metadata_can_be_represented():
    metadata = EncryptedEnvelopeMetadata(
        envelope_id="env_msg_001_plaintext",
        message_id="msg_001",
        state="plaintext",
        status="ready",
        plaintext_ref="symbolic://plaintext/msg_001",
        metadata={"simulator_local": True},
    )

    assert metadata.encryption_identity_id is None
    assert metadata.key_bundle_id is None
    assert metadata.algorithm_ref is None
    assert metadata.ciphertext_ref is None
    assert metadata.plaintext_ref == "symbolic://plaintext/msg_001"
    assert is_envelope_symbolically_encrypted(metadata) is False
    assert is_envelope_ready_for_delivery(metadata) is True


def test_wrap_existing_message_symbolically():
    message = make_basic_message_envelope(
        message_id="msg_001",
        sender_id="dev_sender",
        recipient_address="darwin://global.chat.neo/inbox",
        payload="hello",
    )
    metadata = make_symbolic_encrypted_envelope_metadata(
        envelope_id="env_msg_001",
        message_id="msg_001",
        encryption_identity_id="enc_mailbox_neo",
        key_bundle_id="kb_mailbox_neo_001",
    )

    wrapped = wrap_message_symbolically(message, metadata)

    assert wrapped == SymbolicEncryptedMessageEnvelope(
        message_id="msg_001",
        base_message=message,
        encryption_metadata=metadata,
        metadata={"simulator_local": True, "message_mutated": False},
    )
    assert wrapped.base_message is message
    assert wrapped.encryption_metadata is metadata


def test_symbolic_wrap_does_not_mutate_original_message_envelope():
    message = make_basic_message_envelope(
        message_id="msg_001",
        sender_id="dev_sender",
        recipient_address="darwin://global.chat.neo/inbox",
        payload="hello",
    )
    before = deepcopy(message.to_summary())
    metadata = make_symbolic_encrypted_envelope_metadata(
        envelope_id="env_msg_001",
        message_id="msg_001",
        encryption_identity_id="enc_mailbox_neo",
        key_bundle_id="kb_mailbox_neo_001",
    )

    wrap_message_symbolically(message, metadata)

    assert message.to_summary() == before


def test_encrypted_envelope_metadata_summary_is_json_safe():
    metadata = make_symbolic_encrypted_envelope_metadata(
        envelope_id="env_msg_001",
        message_id="msg_001",
        encryption_identity_id="enc_mailbox_neo",
        key_bundle_id="kb_mailbox_neo_001",
    )

    summary = metadata.to_summary()

    assert summary == {
        "envelope_id": "env_msg_001",
        "message_id": "msg_001",
        "encryption_identity_id": "enc_mailbox_neo",
        "key_bundle_id": "kb_mailbox_neo_001",
        "profile": "symbolic_e2ee_v1",
        "state": "symbolically_encrypted",
        "status": "ready",
        "algorithm_ref": "symbolic-envelope",
        "ciphertext_ref": "symbolic://ciphertext/env_msg_001",
        "plaintext_ref": None,
        "metadata": {
            "simulator_local": True,
            "symbolic_envelope": True,
            "real_ciphertext": False,
        },
    }
    assert metadata.to_dict() == summary
    json.dumps(summary)


def test_symbolic_encrypted_message_envelope_summary_is_json_safe():
    message = make_basic_message_envelope(
        message_id="msg_001",
        sender_id="dev_sender",
        recipient_address="darwin://global.chat.neo/inbox",
        payload="hello",
    )
    metadata = make_symbolic_encrypted_envelope_metadata(
        envelope_id="env_msg_001",
        message_id="msg_001",
        encryption_identity_id="enc_mailbox_neo",
        key_bundle_id="kb_mailbox_neo_001",
    )
    wrapped = wrap_message_symbolically(message, metadata)

    summary = wrapped.to_summary()

    assert summary == {
        "message_id": "msg_001",
        "base_message": message.to_summary(),
        "encryption_metadata": metadata.to_summary(),
        "metadata": {"simulator_local": True, "message_mutated": False},
    }
    assert wrapped.to_dict() == summary
    json.dumps(summary)


def test_symbolic_encrypted_envelope_predicates():
    encrypted = make_symbolic_encrypted_envelope_metadata(
        envelope_id="env_msg_001",
        message_id="msg_001",
        encryption_identity_id="enc_mailbox_neo",
        key_bundle_id="kb_mailbox_neo_001",
    )
    plaintext = EncryptedEnvelopeMetadata(
        envelope_id="env_msg_001_plaintext",
        message_id="msg_001",
        state="plaintext",
        status="ready",
    )
    wrapped = wrap_message_symbolically(
        make_basic_message_envelope(
            message_id="msg_001",
            sender_id="dev_sender",
            recipient_address="darwin://global.chat.neo/inbox",
            payload="hello",
        ),
        encrypted,
    )

    assert is_envelope_symbolically_encrypted(encrypted) is True
    assert is_envelope_symbolically_encrypted(wrapped) is True
    assert is_envelope_symbolically_encrypted(plaintext) is False
    assert is_envelope_ready_for_delivery(encrypted) is True
    assert is_envelope_ready_for_delivery(plaintext) is True


def test_unsupported_profile_envelope_is_not_ready_for_delivery():
    metadata = make_symbolic_encrypted_envelope_metadata(
        envelope_id="env_msg_unsupported",
        message_id="msg_001",
        encryption_identity_id="enc_mailbox_neo",
        key_bundle_id="kb_mailbox_neo_001",
        profile="future_symbolic_profile",
    )

    assert metadata.status.status == "unsupported_profile"
    assert is_encryption_profile_supported("future_symbolic_profile") is False
    assert is_envelope_ready_for_delivery(metadata) is False


@pytest.mark.parametrize(
    "status",
    [
        "missing_key_bundle",
        "stale_key_bundle",
        "disabled_identity",
        "unsupported_profile",
    ],
)
def test_non_ready_envelope_statuses_are_not_ready_for_delivery(status):
    metadata = EncryptedEnvelopeMetadata(
        envelope_id=f"env_msg_001_{status}",
        message_id="msg_001",
        encryption_identity_id="enc_mailbox_neo",
        key_bundle_id="kb_mailbox_neo_001",
        state="symbolically_encrypted",
        status=status,
        algorithm_ref="symbolic-envelope",
        ciphertext_ref=f"symbolic://ciphertext/{status}",
    )

    assert is_envelope_ready_for_delivery(metadata) is False


def test_encryption_identity_summary_is_json_safe():
    identity = EncryptionIdentity(
        encryption_identity_id="enc_mailbox_neo",
        subject_id="mailbox_neo",
        subject_kind="mailbox",
        metadata={"labels": ("mailbox", "symbolic")},
    )

    summary = identity.to_summary()

    assert summary == {
        "encryption_identity_id": "enc_mailbox_neo",
        "subject_id": "mailbox_neo",
        "subject_kind": "mailbox",
        "profile": "symbolic_e2ee_v1",
        "status": "active",
        "metadata": {"labels": ["mailbox", "symbolic"]},
    }
    assert identity.to_dict() == summary
    json.dumps(summary)


def test_key_bundle_reference_summary_is_json_safe():
    key_bundle = KeyBundleReference(
        key_bundle_id="kb_mailbox_neo_002",
        encryption_identity_id="enc_mailbox_neo",
        status="stale",
        public_ref="symbolic://public/mailbox_neo/002",
        created_order=2,
        rotated_from="kb_mailbox_neo_001",
        metadata={"labels": ("rotated",)},
    )

    summary = key_bundle.to_summary()

    assert summary == {
        "key_bundle_id": "kb_mailbox_neo_002",
        "encryption_identity_id": "enc_mailbox_neo",
        "profile": "symbolic_e2ee_v1",
        "status": "stale",
        "public_ref": "symbolic://public/mailbox_neo/002",
        "created_order": 2,
        "rotated_from": "kb_mailbox_neo_001",
        "metadata": {"labels": ["rotated"]},
    }
    assert key_bundle.to_dict() == summary
    json.dumps(summary)


def test_mailbox_encryption_binding_summary_is_json_safe():
    binding = MailboxEncryptionBinding(
        mailbox_id="mailbox_neo",
        encryption_identity_id="enc_mailbox_neo",
        key_bundle_id="kb_mailbox_neo_001",
        required_for_lanes=["basic_messaging:v1"],
        metadata={"future_policy": {"required": True}},
    )

    summary = binding.to_summary()

    assert summary == {
        "mailbox_id": "mailbox_neo",
        "encryption_identity_id": "enc_mailbox_neo",
        "key_bundle_id": "kb_mailbox_neo_001",
        "required_for_lanes": ["basic_messaging:v1"],
        "profile": "symbolic_e2ee_v1",
        "status": "active",
        "metadata": {"future_policy": {"required": True}},
    }
    assert binding.to_dict() == summary
    json.dumps(summary)


def test_no_private_key_material_fields_exist():
    model_fields = {
        field.name
        for model in (
            EncryptionIdentity,
            KeyBundleReference,
            MailboxEncryptionBinding,
            EncryptedEnvelopeMetadata,
            SymbolicEncryptedMessageEnvelope,
        )
        for field in fields(model)
    }

    assert "private_key" not in model_fields
    assert "private_ref" not in model_fields
    assert "secret" not in model_fields
    assert "secret_material" not in model_fields
    assert "key_material" not in model_fields


def test_public_refs_are_symbolic_metadata_only():
    key_bundle = make_symbolic_key_bundle_reference(
        key_bundle_id="kb_mailbox_neo_001",
        encryption_identity_id="enc_mailbox_neo",
        public_ref="symbolic://public/mailbox_neo/001",
    )

    assert key_bundle.public_ref == "symbolic://public/mailbox_neo/001"
    assert key_bundle.metadata["symbolic_public_ref"] is True


def test_encryption_module_does_not_import_crypto_libraries():
    source = inspect.getsource(encryption_models)

    assert "import hmac" not in source
    assert "import hashlib" not in source
    assert "import secrets" not in source
    assert "import cryptography" not in source
    assert "from cryptography" not in source


def test_active_identity_predicate():
    identity = make_symbolic_encryption_identity(
        encryption_identity_id="enc_mailbox_neo",
        subject_id="mailbox_neo",
        subject_kind="mailbox",
    )

    assert is_encryption_identity_active(identity) is True


def test_usable_key_bundle_predicate():
    key_bundle = make_symbolic_key_bundle_reference(
        key_bundle_id="kb_mailbox_neo_001",
        encryption_identity_id="enc_mailbox_neo",
    )

    assert is_key_bundle_usable(key_bundle) is True


@pytest.mark.parametrize(
    ("status", "identity_active", "key_bundle_usable", "binding_active"),
    [
        ("active", True, True, True),
        ("stale", False, False, False),
        ("revoked", False, False, False),
        ("disabled", False, False, False),
    ],
)
def test_inactive_stale_revoked_disabled_statuses_are_deterministic(
    status,
    identity_active,
    key_bundle_usable,
    binding_active,
):
    identity = EncryptionIdentity(
        encryption_identity_id=f"enc_mailbox_neo_{status}",
        subject_id="mailbox_neo",
        subject_kind="mailbox",
        status=status,
    )
    key_bundle = KeyBundleReference(
        key_bundle_id=f"kb_mailbox_neo_{status}",
        encryption_identity_id=identity.encryption_identity_id,
        status=status,
    )
    binding = MailboxEncryptionBinding(
        mailbox_id="mailbox_neo",
        encryption_identity_id=identity.encryption_identity_id,
        key_bundle_id=key_bundle.key_bundle_id,
        status=status,
    )

    assert is_encryption_identity_active(identity) is identity_active
    assert is_key_bundle_usable(key_bundle) is key_bundle_usable
    assert (binding.status == "active") is binding_active


def test_mailbox_binding_can_require_basic_messaging():
    binding = bind_mailbox_encryption_identity(
        mailbox_id="mailbox_neo",
        encryption_identity_id="enc_mailbox_neo",
        key_bundle_id="kb_mailbox_neo_001",
        required_for_lanes=("basic_messaging:v1",),
    )

    assert binding.required_for_lanes == ("basic_messaging:v1",)


def test_helpers_are_pure_and_deterministic():
    first_identity = make_symbolic_encryption_identity(
        encryption_identity_id="enc_mailbox_neo",
        subject_id="mailbox_neo",
        subject_kind="mailbox",
    )
    second_identity = make_symbolic_encryption_identity(
        encryption_identity_id="enc_mailbox_neo",
        subject_id="mailbox_neo",
        subject_kind="mailbox",
    )
    first_key_bundle = make_symbolic_key_bundle_reference(
        key_bundle_id="kb_mailbox_neo_001",
        encryption_identity_id="enc_mailbox_neo",
        public_ref="symbolic://public/mailbox_neo/001",
    )
    second_key_bundle = make_symbolic_key_bundle_reference(
        key_bundle_id="kb_mailbox_neo_001",
        encryption_identity_id="enc_mailbox_neo",
        public_ref="symbolic://public/mailbox_neo/001",
    )
    first_binding = bind_mailbox_encryption_identity(
        mailbox_id="mailbox_neo",
        encryption_identity_id="enc_mailbox_neo",
        key_bundle_id="kb_mailbox_neo_001",
        required_for_lanes=("basic_messaging:v1",),
    )
    second_binding = bind_mailbox_encryption_identity(
        mailbox_id="mailbox_neo",
        encryption_identity_id="enc_mailbox_neo",
        key_bundle_id="kb_mailbox_neo_001",
        required_for_lanes=("basic_messaging:v1",),
    )

    assert first_identity == second_identity
    assert first_key_bundle == second_key_bundle
    assert first_binding == second_binding


def test_validation_rejects_invalid_symbolic_records():
    with pytest.raises(ValueError, match="subject_kind"):
        make_symbolic_encryption_identity(
            encryption_identity_id="enc_mailbox_neo",
            subject_id="mailbox_neo",
            subject_kind="person",
        )

    with pytest.raises(ValueError, match="key bundle status"):
        KeyBundleReference(
            key_bundle_id="kb_mailbox_neo_001",
            encryption_identity_id="enc_mailbox_neo",
            status="missing",
        )

    with pytest.raises(ValueError, match="required_for_lanes"):
        MailboxEncryptionBinding(
            mailbox_id="mailbox_neo",
            encryption_identity_id="enc_mailbox_neo",
            key_bundle_id="kb_mailbox_neo_001",
            required_for_lanes=("bad-lane",),
        )


def test_encryption_metadata_rejects_non_json_safe_values():
    with pytest.raises(TypeError):
        EncryptionIdentity(
            encryption_identity_id="enc_mailbox_neo",
            subject_id="mailbox_neo",
            subject_kind="mailbox",
            metadata={"bad": object()},
        )

    with pytest.raises(TypeError):
        KeyBundleReference(
            key_bundle_id="kb_mailbox_neo_001",
            encryption_identity_id="enc_mailbox_neo",
            metadata={"bad": object()},
        )

    with pytest.raises(TypeError):
        MailboxEncryptionBinding(
            mailbox_id="mailbox_neo",
            encryption_identity_id="enc_mailbox_neo",
            key_bundle_id="kb_mailbox_neo_001",
            metadata={"bad": object()},
        )


def test_existing_mailbox_message_delivery_helpers_are_not_affected(monkeypatch):
    def fail_dns(*args, **kwargs):
        raise AssertionError("DNS lookup should not run")

    def fail_socket(*args, **kwargs):
        raise AssertionError("socket should not open")

    monkeypatch.setattr(socket, "getaddrinfo", fail_dns)
    monkeypatch.setattr(socket, "socket", fail_socket)

    registry_hub = RegistryHub(hub_id="hub_chat_001", scope_path="global.chat")
    traffic_hub = TrafficHub(hub_id="traffic_chat_001")
    register_lane_definition(
        registry_hub,
        make_basic_messaging_lane_definition("global.chat"),
    )
    register_mailbox(
        registry_hub,
        MailboxIdentity(
            mailbox_id="mailbox_neo",
            canonical_device_id="dev_A9F3",
            local_name="neo",
            scope="global.chat",
            address=format_mailbox_address("global.chat", "neo"),
        ),
    )
    bind_mailbox_capability(
        registry_hub,
        "mailbox_neo",
        MailboxCapability(
            capability_id="cap_basic_messaging",
            lane_signature="basic_messaging:v1",
        ),
    )
    register_adapter_endpoint(
        registry_hub,
        make_in_memory_mailbox_endpoint(
            endpoint_id="endpoint_mailbox_neo",
            mailbox_id="mailbox_neo",
            scope="global.chat",
        ),
    )
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
    message = make_basic_message_envelope(
        message_id="msg_001",
        sender_id="dev_sender",
        recipient_address="darwin://global.chat.neo/inbox",
        payload="hello",
    )

    result = deliver_message_to_mailbox(registry_hub, message)

    assert result.status.status == "delivered"
    assert result.reason is None
    assert get_mailbox_inbox(registry_hub, "mailbox_neo") == [message]
    assert registry_hub.devices["dev_A9F3"].current_state == "online"
    assert traffic_hub.routes == {}
    assert traffic_hub.lanes == {}
    assert result.metadata["networking"] is False
    assert result.metadata["dns_lookup"] is False
    assert result.metadata["traffic_hub_routing"] is False
