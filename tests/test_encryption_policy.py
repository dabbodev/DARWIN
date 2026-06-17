import json
from copy import deepcopy

from darwin.models import (
    DEFAULT_ENCRYPTION_PROFILE,
    EncryptedEnvelopeMetadata,
    EncryptionIdentity,
    KeyBundleReference,
    MailboxEncryptionPolicy,
    MailboxIdentity,
    evaluate_mailbox_encryption_policy,
    format_mailbox_address,
    is_encryption_policy_decision_accepted,
    is_lane_encryption_required,
    make_basic_message_envelope,
    make_mailbox_encryption_policy,
    make_symbolic_encrypted_envelope_metadata,
)


def test_create_mailbox_encryption_policy():
    policy = make_mailbox_encryption_policy(
        policy_id="policy_mailbox_neo",
        mailbox_id="mailbox_neo",
    )

    assert policy == MailboxEncryptionPolicy(
        policy_id="policy_mailbox_neo",
        mailbox_id="mailbox_neo",
        required_for_lanes=("basic_messaging:v1",),
        allowed_profiles=(DEFAULT_ENCRYPTION_PROFILE,),
        require_active_identity=True,
        require_usable_key_bundle=True,
        allow_plaintext_fallback=False,
        metadata={"simulator_local": True},
    )


def test_mailbox_encryption_policy_summary_is_json_safe():
    policy = MailboxEncryptionPolicy(
        policy_id="policy_mailbox_neo",
        mailbox_id="mailbox_neo",
        required_for_lanes=["basic_messaging:v1"],
        allowed_profiles=["symbolic_e2ee_v1"],
        metadata={"labels": ("symbolic", "policy")},
    )

    summary = policy.to_summary()

    assert summary == {
        "policy_id": "policy_mailbox_neo",
        "mailbox_id": "mailbox_neo",
        "required_for_lanes": ["basic_messaging:v1"],
        "allowed_profiles": ["symbolic_e2ee_v1"],
        "require_active_identity": True,
        "require_usable_key_bundle": True,
        "allow_plaintext_fallback": False,
        "metadata": {"labels": ["symbolic", "policy"]},
    }
    assert policy.to_dict() == summary
    json.dumps(summary)


def test_lane_not_requiring_encryption_allows_plaintext():
    policy = make_mailbox_encryption_policy(
        policy_id="policy_mailbox_neo",
        mailbox_id="mailbox_neo",
        required_for_lanes=("file_transfer:v1",),
    )

    decision = evaluate_mailbox_encryption_policy(
        policy,
        lane_signature="basic_messaging:v1",
        message_id="msg_001",
    )

    assert decision.status.status == "plaintext_allowed"
    assert decision.reason is None
    assert decision.encryption_required is False
    assert decision.envelope_accepted is False
    assert is_lane_encryption_required(policy, "basic_messaging:v1") is False
    assert is_encryption_policy_decision_accepted(decision) is True


def test_required_lane_rejects_missing_envelope_by_default():
    decision = evaluate_mailbox_encryption_policy(
        _default_policy(),
        lane_signature="basic_messaging:v1",
        message_id="msg_001",
    )

    assert decision.status.status == "missing_envelope"
    assert decision.reason.reason == "missing_envelope"
    assert decision.encryption_required is True
    assert decision.envelope_accepted is False
    assert is_encryption_policy_decision_accepted(decision) is False


def test_required_lane_can_allow_plaintext_fallback_when_configured():
    policy = make_mailbox_encryption_policy(
        policy_id="policy_mailbox_neo",
        mailbox_id="mailbox_neo",
        allow_plaintext_fallback=True,
    )

    decision = evaluate_mailbox_encryption_policy(
        policy,
        lane_signature="basic_messaging:v1",
        message_id="msg_001",
    )

    assert decision.status.status == "plaintext_allowed"
    assert decision.reason.reason == "plaintext_fallback_allowed"
    assert decision.encryption_required is True
    assert decision.envelope_accepted is False
    assert is_encryption_policy_decision_accepted(decision) is True


def test_unsupported_profile_is_rejected():
    envelope_metadata = make_symbolic_encrypted_envelope_metadata(
        envelope_id="env_msg_001",
        message_id="msg_001",
        encryption_identity_id="enc_mailbox_neo",
        key_bundle_id="kb_mailbox_neo_001",
        profile="future_symbolic_profile",
    )

    decision = evaluate_mailbox_encryption_policy(
        _default_policy(),
        lane_signature="basic_messaging:v1",
        envelope_metadata=envelope_metadata,
    )

    assert decision.status.status == "unsupported_profile"
    assert decision.reason.reason == "unsupported_profile"
    assert decision.profile == "future_symbolic_profile"
    assert decision.envelope_accepted is False


def test_plaintext_envelope_on_required_lane_needs_encryption():
    envelope_metadata = EncryptedEnvelopeMetadata(
        envelope_id="env_msg_001_plaintext",
        message_id="msg_001",
        state="plaintext",
        status="ready",
        plaintext_ref="symbolic://plaintext/msg_001",
    )

    decision = evaluate_mailbox_encryption_policy(
        _default_policy(),
        lane_signature="basic_messaging:v1",
        envelope_metadata=envelope_metadata,
    )

    assert decision.status.status == "needs_encryption"
    assert decision.reason.reason == "needs_encryption"
    assert decision.envelope_accepted is False


def test_missing_identity_is_rejected_when_required():
    decision = evaluate_mailbox_encryption_policy(
        _default_policy(),
        lane_signature="basic_messaging:v1",
        envelope_metadata=_ready_envelope(),
    )

    assert decision.status.status == "missing_identity"
    assert decision.reason.reason == "missing_identity"
    assert decision.encryption_identity_id == "enc_mailbox_neo"


def test_inactive_identity_is_rejected_when_required():
    decision = evaluate_mailbox_encryption_policy(
        _default_policy(),
        lane_signature="basic_messaging:v1",
        envelope_metadata=_ready_envelope(),
        encryption_identity=_identity(status="disabled"),
    )

    assert decision.status.status == "identity_inactive"
    assert decision.reason.reason == "identity_inactive"
    assert decision.envelope_accepted is False


def test_missing_key_bundle_is_rejected_when_required():
    decision = evaluate_mailbox_encryption_policy(
        _default_policy(),
        lane_signature="basic_messaging:v1",
        envelope_metadata=_ready_envelope(),
        encryption_identity=_identity(),
    )

    assert decision.status.status == "missing_key_bundle"
    assert decision.reason.reason == "missing_key_bundle"
    assert decision.key_bundle_id == "kb_mailbox_neo_001"


def test_unusable_key_bundle_is_rejected_when_required():
    decision = evaluate_mailbox_encryption_policy(
        _default_policy(),
        lane_signature="basic_messaging:v1",
        envelope_metadata=_ready_envelope(),
        encryption_identity=_identity(),
        key_bundle=_key_bundle(status="stale"),
    )

    assert decision.status.status == "key_bundle_unusable"
    assert decision.reason.reason == "key_bundle_unusable"
    assert decision.envelope_accepted is False


def test_not_ready_envelope_is_rejected():
    envelope_metadata = EncryptedEnvelopeMetadata(
        envelope_id="env_msg_001",
        message_id="msg_001",
        encryption_identity_id="enc_mailbox_neo",
        key_bundle_id="kb_mailbox_neo_001",
        state="symbolically_encrypted",
        status="stale_key_bundle",
        algorithm_ref="symbolic-envelope",
        ciphertext_ref="symbolic://ciphertext/env_msg_001",
    )

    decision = evaluate_mailbox_encryption_policy(
        _default_policy(),
        lane_signature="basic_messaging:v1",
        envelope_metadata=envelope_metadata,
        encryption_identity=_identity(),
        key_bundle=_key_bundle(),
    )

    assert decision.status.status == "envelope_not_ready"
    assert decision.reason.reason == "envelope_not_ready"
    assert decision.envelope_accepted is False


def test_ready_envelope_with_active_identity_and_usable_key_bundle_is_accepted():
    decision = evaluate_mailbox_encryption_policy(
        _default_policy(),
        lane_signature="basic_messaging:v1",
        envelope_metadata=_ready_envelope(),
        encryption_identity=_identity(),
        key_bundle=_key_bundle(),
    )

    assert decision.status.status == "accepted"
    assert decision.reason is None
    assert decision.encryption_required is True
    assert decision.envelope_accepted is True
    assert decision.profile == DEFAULT_ENCRYPTION_PROFILE
    assert decision.encryption_identity_id == "enc_mailbox_neo"
    assert decision.key_bundle_id == "kb_mailbox_neo_001"
    assert is_lane_encryption_required(_default_policy(), "basic_messaging:v1") is True
    assert is_encryption_policy_decision_accepted(decision) is True


def test_policy_decision_summary_is_json_safe():
    decision = evaluate_mailbox_encryption_policy(
        _default_policy(),
        lane_signature="basic_messaging:v1",
        envelope_metadata=_ready_envelope(),
        encryption_identity=_identity(),
        key_bundle=_key_bundle(),
    )

    summary = decision.to_summary()

    assert summary == {
        "policy_id": "policy_mailbox_neo",
        "mailbox_id": "mailbox_neo",
        "lane_signature": "basic_messaging:v1",
        "message_id": "msg_001",
        "status": "accepted",
        "reason": None,
        "encryption_required": True,
        "envelope_accepted": True,
        "profile": "symbolic_e2ee_v1",
        "encryption_identity_id": "enc_mailbox_neo",
        "key_bundle_id": "kb_mailbox_neo_001",
        "metadata": {
            "simulator_local": True,
            "message_mutated": False,
            "registry_hub_mutated": False,
            "delivery_behavior_changed": False,
        },
    }
    assert decision.to_dict() == summary
    json.dumps(summary)


def test_policy_evaluation_does_not_mutate_supplied_records():
    policy = _default_policy()
    envelope_metadata = _ready_envelope()
    identity = _identity()
    key_bundle = _key_bundle()
    mailbox = MailboxIdentity(
        mailbox_id="mailbox_neo",
        canonical_device_id="dev_A9F3",
        local_name="neo",
        scope="global.chat",
        address=format_mailbox_address("global.chat", "neo"),
    )
    message = make_basic_message_envelope(
        message_id="msg_001",
        sender_id="dev_sender",
        recipient_address="darwin://global.chat.neo/inbox",
        payload="hello",
    )
    before = {
        "policy": deepcopy(policy.to_summary()),
        "envelope": deepcopy(envelope_metadata.to_summary()),
        "identity": deepcopy(identity.to_summary()),
        "key_bundle": deepcopy(key_bundle.to_summary()),
        "mailbox": deepcopy(mailbox.to_summary()),
        "message": deepcopy(message.to_summary()),
    }

    evaluate_mailbox_encryption_policy(
        policy,
        lane_signature=message.lane_signature,
        message_id=message.message_id,
        envelope_metadata=envelope_metadata,
        encryption_identity=identity,
        key_bundle=key_bundle,
    )

    assert policy.to_summary() == before["policy"]
    assert envelope_metadata.to_summary() == before["envelope"]
    assert identity.to_summary() == before["identity"]
    assert key_bundle.to_summary() == before["key_bundle"]
    assert mailbox.to_summary() == before["mailbox"]
    assert message.to_summary() == before["message"]


def _default_policy() -> MailboxEncryptionPolicy:
    return make_mailbox_encryption_policy(
        policy_id="policy_mailbox_neo",
        mailbox_id="mailbox_neo",
    )


def _ready_envelope() -> EncryptedEnvelopeMetadata:
    return make_symbolic_encrypted_envelope_metadata(
        envelope_id="env_msg_001",
        message_id="msg_001",
        encryption_identity_id="enc_mailbox_neo",
        key_bundle_id="kb_mailbox_neo_001",
    )


def _identity(status: str = "active") -> EncryptionIdentity:
    return EncryptionIdentity(
        encryption_identity_id="enc_mailbox_neo",
        subject_id="mailbox_neo",
        subject_kind="mailbox",
        status=status,
    )


def _key_bundle(status: str = "active") -> KeyBundleReference:
    return KeyBundleReference(
        key_bundle_id="kb_mailbox_neo_001",
        encryption_identity_id="enc_mailbox_neo",
        status=status,
    )
