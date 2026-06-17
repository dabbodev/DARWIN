import inspect
import json
from copy import deepcopy

import pytest

import darwin.registry.encryption_registry as encryption_registry
from darwin.models import (
    DEFAULT_ENCRYPTION_PROFILE,
    EncryptionIdentity,
    EncryptionProfile,
    KeyBundleReference,
    MailboxEncryptionBinding,
    MailboxEncryptionPolicy,
    RegistryHub,
    evaluate_mailbox_encryption_policy,
    make_mailbox_encryption_policy,
    make_symbolic_encrypted_envelope_metadata,
    make_symbolic_encryption_identity,
    make_symbolic_key_bundle_reference,
)
from darwin.registry import (
    evaluate_registered_mailbox_encryption_policy,
    get_encryption_identity,
    get_key_bundle_reference,
    get_mailbox_encryption_binding,
    get_mailbox_encryption_policy,
    get_mailbox_encryption_policy_for_mailbox,
    list_encryption_identities,
    list_key_bundle_references,
    list_mailbox_encryption_bindings,
    list_mailbox_encryption_policies,
    make_basic_messaging_mailbox,
    query_encryption_policy_decisions,
    register_encryption_identity,
    register_key_bundle_reference,
    register_mailbox,
    register_mailbox_encryption_binding,
    register_mailbox_encryption_policy,
)
from darwin.sim.world import World


def test_registry_hub_encryption_registries_default_empty():
    hub = _hub()

    assert hub.encryption_identities == {}
    assert hub.key_bundle_references == {}
    assert hub.mailbox_encryption_bindings == {}
    assert hub.mailbox_encryption_policies == {}
    assert hub.encryption_policy_decision_history == []


def test_register_get_and_list_encryption_identity():
    hub = _hub()
    identity = _identity()

    result = register_encryption_identity(hub, identity)

    assert result is identity
    assert get_encryption_identity(hub, "enc_mailbox_neo") is identity
    assert list_encryption_identities(hub) == [identity]


def test_list_encryption_identities_filters_by_subject_profile_and_status():
    hub = _hub()
    active_mailbox = _identity()
    disabled_device = EncryptionIdentity(
        encryption_identity_id="enc_device_sender",
        subject_id="dev_sender",
        subject_kind="device",
        status="disabled",
    )
    register_encryption_identity(hub, disabled_device)
    register_encryption_identity(hub, active_mailbox)

    assert list_encryption_identities(hub, subject_id="mailbox_neo") == [
        active_mailbox
    ]
    assert list_encryption_identities(hub, subject_kind="device") == [
        disabled_device
    ]
    assert list_encryption_identities(
        hub,
        profile=EncryptionProfile(DEFAULT_ENCRYPTION_PROFILE),
    ) == [disabled_device, active_mailbox]
    assert list_encryption_identities(hub, status="disabled") == [disabled_device]


def test_register_key_bundle_for_existing_identity():
    hub = _hub()
    identity = _identity()
    key_bundle = _key_bundle()
    register_encryption_identity(hub, identity)

    result = register_key_bundle_reference(hub, key_bundle)

    assert result is key_bundle
    assert get_key_bundle_reference(hub, "kb_mailbox_neo_001") is key_bundle
    assert list_key_bundle_references(hub) == [key_bundle]


def test_register_key_bundle_missing_identity_is_rejected():
    hub = _hub()

    with pytest.raises(KeyError, match="encryption_identity_id is not registered"):
        register_key_bundle_reference(hub, _key_bundle())


def test_list_key_bundle_references_filters_by_identity_profile_and_status():
    hub = _hub()
    identity = _identity()
    stale = KeyBundleReference(
        key_bundle_id="kb_mailbox_neo_000",
        encryption_identity_id=identity.encryption_identity_id,
        status="stale",
    )
    active = _key_bundle()
    register_encryption_identity(hub, identity)
    register_key_bundle_reference(hub, active)
    register_key_bundle_reference(hub, stale)

    assert list_key_bundle_references(
        hub,
        encryption_identity_id=identity.encryption_identity_id,
    ) == [stale, active]
    assert list_key_bundle_references(hub, profile=DEFAULT_ENCRYPTION_PROFILE) == [
        stale,
        active,
    ]
    assert list_key_bundle_references(hub, status="active") == [active]


def test_register_mailbox_encryption_binding_for_existing_references():
    hub = _prepared_hub()
    binding = _binding()

    result = register_mailbox_encryption_binding(hub, binding)

    assert result is binding
    assert get_mailbox_encryption_binding(hub, "mailbox_neo") is binding
    assert list_mailbox_encryption_bindings(hub) == [binding]


def test_register_mailbox_encryption_binding_missing_mailbox_is_rejected():
    hub = _hub_with_identity_and_key()

    with pytest.raises(KeyError, match="mailbox_id is not registered"):
        register_mailbox_encryption_binding(hub, _binding())


def test_register_mailbox_encryption_binding_missing_identity_is_rejected():
    hub = _hub()
    _register_mailbox(hub)

    with pytest.raises(KeyError, match="encryption_identity_id is not registered"):
        register_mailbox_encryption_binding(hub, _binding())


def test_register_mailbox_encryption_binding_missing_key_bundle_is_rejected():
    hub = _hub()
    _register_mailbox(hub)
    register_encryption_identity(hub, _identity())

    with pytest.raises(KeyError, match="key_bundle_id is not registered"):
        register_mailbox_encryption_binding(hub, _binding())


def test_list_mailbox_encryption_bindings_filters_by_mailbox_identity_key_profile_lane():
    hub = _prepared_hub()
    binding = _binding()
    register_mailbox_encryption_binding(hub, binding)

    assert list_mailbox_encryption_bindings(hub, mailbox_id="mailbox_neo") == [
        binding
    ]
    assert list_mailbox_encryption_bindings(
        hub,
        encryption_identity_id="enc_mailbox_neo",
    ) == [binding]
    assert list_mailbox_encryption_bindings(hub, key_bundle_id="kb_mailbox_neo_001") == [
        binding
    ]
    assert list_mailbox_encryption_bindings(
        hub,
        profile=DEFAULT_ENCRYPTION_PROFILE,
    ) == [binding]
    assert list_mailbox_encryption_bindings(hub, status="active") == [binding]
    assert list_mailbox_encryption_bindings(
        hub,
        lane_signature="basic_messaging:v1",
    ) == [binding]


def test_register_get_and_list_mailbox_encryption_policy():
    hub = _hub()
    _register_mailbox(hub)
    policy = _policy()

    result = register_mailbox_encryption_policy(hub, policy)

    assert result is policy
    assert get_mailbox_encryption_policy(hub, "policy_mailbox_neo") is policy
    assert get_mailbox_encryption_policy_for_mailbox(hub, "mailbox_neo") is policy
    assert list_mailbox_encryption_policies(hub) == [policy]


def test_register_mailbox_encryption_policy_missing_mailbox_is_rejected():
    hub = _hub()

    with pytest.raises(KeyError, match="mailbox_id is not registered"):
        register_mailbox_encryption_policy(hub, _policy())


def test_list_mailbox_encryption_policies_filters_by_mailbox_lane_and_profile():
    hub = _hub()
    _register_mailbox(hub)
    policy = _policy()
    register_mailbox_encryption_policy(hub, policy)

    assert list_mailbox_encryption_policies(hub, mailbox_id="mailbox_neo") == [
        policy
    ]
    assert list_mailbox_encryption_policies(
        hub,
        lane_signature="basic_messaging:v1",
    ) == [policy]
    assert list_mailbox_encryption_policies(
        hub,
        profile=DEFAULT_ENCRYPTION_PROFILE,
    ) == [policy]


def test_duplicate_registration_replaces_by_deterministic_registry_key():
    hub = _prepared_hub()
    replacement_identity = EncryptionIdentity(
        encryption_identity_id="enc_mailbox_neo",
        subject_id="mailbox_neo",
        subject_kind="mailbox",
        status="disabled",
    )
    replacement_key = KeyBundleReference(
        key_bundle_id="kb_mailbox_neo_001",
        encryption_identity_id="enc_mailbox_neo",
        status="stale",
    )
    replacement_binding = MailboxEncryptionBinding(
        mailbox_id="mailbox_neo",
        encryption_identity_id="enc_mailbox_neo",
        key_bundle_id="kb_mailbox_neo_001",
        required_for_lanes=("file_transfer:v1",),
    )
    replacement_policy = MailboxEncryptionPolicy(
        policy_id="policy_mailbox_neo",
        mailbox_id="mailbox_neo",
        required_for_lanes=("file_transfer:v1",),
    )

    register_encryption_identity(hub, replacement_identity)
    register_key_bundle_reference(hub, replacement_key)
    register_mailbox_encryption_binding(hub, replacement_binding)
    register_mailbox_encryption_policy(hub, _policy())
    register_mailbox_encryption_policy(hub, replacement_policy)

    assert get_encryption_identity(hub, "enc_mailbox_neo") is replacement_identity
    assert get_key_bundle_reference(hub, "kb_mailbox_neo_001") is replacement_key
    assert get_mailbox_encryption_binding(hub, "mailbox_neo") is replacement_binding
    assert get_mailbox_encryption_policy(hub, "policy_mailbox_neo") is (
        replacement_policy
    )


def test_registered_policy_evaluation_accepts_ready_symbolic_envelope():
    hub = _prepared_hub_with_binding_and_policy()

    decision = evaluate_registered_mailbox_encryption_policy(
        hub,
        mailbox_id="mailbox_neo",
        lane_signature="basic_messaging:v1",
        envelope_metadata=_ready_envelope(),
    )

    assert decision.status.status == "accepted"
    assert decision.reason is None
    assert decision.encryption_required is True
    assert decision.envelope_accepted is True
    assert decision.encryption_identity_id == "enc_mailbox_neo"
    assert decision.key_bundle_id == "kb_mailbox_neo_001"
    assert hub.encryption_policy_decision_history == [decision]
    assert decision.metadata["retained_in_registry_hub"] is True


def test_registered_policy_evaluation_can_skip_retention():
    hub = _prepared_hub_with_binding_and_policy()

    decision = evaluate_registered_mailbox_encryption_policy(
        hub,
        mailbox_id="mailbox_neo",
        lane_signature="basic_messaging:v1",
        envelope_metadata=_ready_envelope(),
        retain=False,
    )

    assert decision.status.status == "accepted"
    assert decision.metadata["retained_in_registry_hub"] is False
    assert hub.encryption_policy_decision_history == []


def test_registered_policy_evaluation_preserves_decision_append_order():
    hub = _prepared_hub_with_binding_and_policy()

    first = evaluate_registered_mailbox_encryption_policy(
        hub,
        mailbox_id="mailbox_neo",
        lane_signature="basic_messaging:v1",
        message_id="msg_001",
    )
    second = evaluate_registered_mailbox_encryption_policy(
        hub,
        mailbox_id="mailbox_neo",
        lane_signature="basic_messaging:v1",
        envelope_metadata=_ready_envelope("msg_002"),
    )

    assert hub.encryption_policy_decision_history == [first, second]
    assert [
        decision.message_id for decision in hub.encryption_policy_decision_history
    ] == ["msg_001", "msg_002"]


def test_pure_policy_evaluation_does_not_mutate_decision_history():
    hub = _prepared_hub_with_binding_and_policy()
    before_history = list(hub.encryption_policy_decision_history)

    evaluate_mailbox_encryption_policy(
        _policy(),
        lane_signature="basic_messaging:v1",
        envelope_metadata=_ready_envelope(),
        encryption_identity=_identity(),
        key_bundle=_key_bundle(),
    )

    assert hub.encryption_policy_decision_history == before_history


def test_registered_policy_evaluation_rejects_missing_envelope_for_required_lane():
    hub = _prepared_hub_with_binding_and_policy()

    decision = evaluate_registered_mailbox_encryption_policy(
        hub,
        mailbox_id="mailbox_neo",
        lane_signature="basic_messaging:v1",
        message_id="msg_001",
    )

    assert decision.status.status == "missing_envelope"
    assert decision.reason.reason == "missing_envelope"
    assert decision.encryption_required is True
    assert decision.envelope_accepted is False


def test_query_encryption_policy_decisions_filters_retained_history():
    hub = _prepared_hub_with_binding_and_policy()
    missing = evaluate_registered_mailbox_encryption_policy(
        hub,
        mailbox_id="mailbox_neo",
        lane_signature="basic_messaging:v1",
        message_id="msg_missing",
    )
    accepted = evaluate_registered_mailbox_encryption_policy(
        hub,
        mailbox_id="mailbox_neo",
        lane_signature="basic_messaging:v1",
        envelope_metadata=_ready_envelope("msg_accepted"),
    )
    before_history = list(hub.encryption_policy_decision_history)

    assert query_encryption_policy_decisions(hub, policy_id="policy_mailbox_neo") == [
        missing,
        accepted,
    ]
    assert query_encryption_policy_decisions(hub, mailbox_id="mailbox_neo") == [
        missing,
        accepted,
    ]
    assert query_encryption_policy_decisions(
        hub,
        lane_signature="basic_messaging:v1",
    ) == [missing, accepted]
    assert query_encryption_policy_decisions(hub, message_id="msg_missing") == [
        missing
    ]
    assert query_encryption_policy_decisions(
        hub,
        status="missing_envelope",
        reason="missing_envelope",
    ) == [missing]
    assert query_encryption_policy_decisions(
        hub,
        encryption_required=True,
        envelope_accepted=True,
        profile=DEFAULT_ENCRYPTION_PROFILE,
        encryption_identity_id="enc_mailbox_neo",
        key_bundle_id="kb_mailbox_neo_001",
    ) == [accepted]
    assert query_encryption_policy_decisions(
        hub,
        mailbox_id="mailbox_neo",
        status="accepted",
        message_id="msg_missing",
    ) == []
    assert hub.encryption_policy_decision_history == before_history


def test_registered_policy_evaluation_rejects_inactive_identity():
    hub = _prepared_hub(identity=EncryptionIdentity(
        encryption_identity_id="enc_mailbox_neo",
        subject_id="mailbox_neo",
        subject_kind="mailbox",
        status="disabled",
    ))
    register_mailbox_encryption_binding(hub, _binding())
    register_mailbox_encryption_policy(hub, _policy())

    decision = evaluate_registered_mailbox_encryption_policy(
        hub,
        mailbox_id="mailbox_neo",
        lane_signature="basic_messaging:v1",
        envelope_metadata=_ready_envelope(),
    )

    assert decision.status.status == "identity_inactive"
    assert decision.reason.reason == "identity_inactive"


def test_registered_policy_evaluation_rejects_unusable_key_bundle():
    hub = _prepared_hub(key_bundle=KeyBundleReference(
        key_bundle_id="kb_mailbox_neo_001",
        encryption_identity_id="enc_mailbox_neo",
        status="stale",
    ))
    register_mailbox_encryption_binding(hub, _binding())
    register_mailbox_encryption_policy(hub, _policy())

    decision = evaluate_registered_mailbox_encryption_policy(
        hub,
        mailbox_id="mailbox_neo",
        lane_signature="basic_messaging:v1",
        envelope_metadata=_ready_envelope(),
    )

    assert decision.status.status == "key_bundle_unusable"
    assert decision.reason.reason == "key_bundle_unusable"


def test_registered_policy_no_policy_behavior_is_deterministic_plaintext_allowed():
    hub = _prepared_hub()

    decision = evaluate_registered_mailbox_encryption_policy(
        hub,
        mailbox_id="mailbox_neo",
        lane_signature="basic_messaging:v1",
        envelope_metadata=_ready_envelope(),
    )

    assert decision.policy_id == "no_registered_policy"
    assert decision.status.status == "plaintext_allowed"
    assert decision.reason is None
    assert decision.encryption_required is False
    assert decision.envelope_accepted is False
    assert decision.message_id == "msg_001"
    assert decision.metadata["delivery_behavior_changed"] is False
    assert hub.encryption_policy_decision_history == [decision]


def test_registered_policy_evaluation_does_not_mutate_delivery_or_existing_registries():
    hub = _prepared_hub_with_binding_and_policy()
    before = {
        "mailboxes": deepcopy(
            {key: value.to_summary() for key, value in hub.mailboxes.items()}
        ),
        "mailbox_address_index": deepcopy(hub.mailbox_address_index),
        "lane_registry": deepcopy(hub.lane_registry),
        "adapter_endpoints": deepcopy(hub.adapter_endpoints),
        "message_inboxes": deepcopy(hub.message_inboxes),
        "message_delivery_results": deepcopy(hub.message_delivery_results),
        "aliases": deepcopy(hub.aliases),
        "devices": deepcopy(hub.devices),
        "decision_history_length": len(hub.encryption_policy_decision_history),
    }

    decision = evaluate_registered_mailbox_encryption_policy(
        hub,
        mailbox_id="mailbox_neo",
        lane_signature="basic_messaging:v1",
        envelope_metadata=_ready_envelope(),
    )

    assert {
        key: value.to_summary() for key, value in hub.mailboxes.items()
    } == before["mailboxes"]
    assert hub.mailbox_address_index == before["mailbox_address_index"]
    assert hub.lane_registry == before["lane_registry"]
    assert hub.adapter_endpoints == before["adapter_endpoints"]
    assert hub.message_inboxes == before["message_inboxes"]
    assert hub.message_delivery_results == before["message_delivery_results"]
    assert hub.aliases == before["aliases"]
    assert hub.devices == before["devices"]
    assert hub.encryption_policy_decision_history == [decision]
    assert len(hub.encryption_policy_decision_history) == (
        before["decision_history_length"] + 1
    )


def test_detailed_snapshot_includes_encryption_registry_summaries():
    world = World()
    hub = _prepared_hub_with_binding_and_policy()
    decision = evaluate_registered_mailbox_encryption_policy(
        hub,
        mailbox_id="mailbox_neo",
        lane_signature="basic_messaging:v1",
        envelope_metadata=_ready_envelope(),
    )
    world.add_registry_hub(hub)

    snapshot = world.detailed_snapshot()
    hub_snapshot = snapshot["registry_hubs"]["hub_chat_001"]

    assert hub_snapshot["encryption_identities"] == {
        "enc_mailbox_neo": _identity().to_summary()
    }
    assert hub_snapshot["key_bundle_references"] == {
        "kb_mailbox_neo_001": _key_bundle().to_summary()
    }
    assert hub_snapshot["mailbox_encryption_bindings"] == {
        "mailbox_neo": _binding().to_summary()
    }
    assert hub_snapshot["mailbox_encryption_policies"] == {
        "policy_mailbox_neo": _policy().to_summary()
    }
    assert hub_snapshot["encryption_policy_decision_history"] == [
        decision.to_summary()
    ]
    json.dumps(snapshot, sort_keys=True)
    assert "encryption_identities" not in world.snapshot()
    assert "encryption_policy_decision_history" not in world.snapshot()


def test_detailed_snapshot_decision_history_is_a_json_safe_copy():
    world = World()
    hub = _prepared_hub_with_binding_and_policy()
    decision = evaluate_registered_mailbox_encryption_policy(
        hub,
        mailbox_id="mailbox_neo",
        lane_signature="basic_messaging:v1",
        envelope_metadata=_ready_envelope(),
    )
    world.add_registry_hub(hub)

    snapshot = world.snapshot(detailed=True)
    history = snapshot["registry_hubs"]["hub_chat_001"][
        "encryption_policy_decision_history"
    ]
    history[0]["metadata"]["retained_in_registry_hub"] = "mutated_snapshot_copy"

    assert hub.encryption_policy_decision_history == [decision]
    assert hub.encryption_policy_decision_history[0].metadata[
        "retained_in_registry_hub"
    ] is True


def test_encryption_registry_module_does_not_import_crypto_libraries():
    source = inspect.getsource(encryption_registry)

    assert "import hmac" not in source
    assert "import hashlib" not in source
    assert "import secrets" not in source
    assert "import cryptography" not in source
    assert "from cryptography" not in source


def _hub() -> RegistryHub:
    return RegistryHub(hub_id="hub_chat_001", scope_path="global.chat")


def _register_mailbox(hub: RegistryHub) -> None:
    register_mailbox(
        hub,
        make_basic_messaging_mailbox(
            mailbox_id="mailbox_neo",
            canonical_device_id="dev_A9F3",
            local_name="neo",
            scope="global.chat",
        ),
    )


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


def _policy() -> MailboxEncryptionPolicy:
    return make_mailbox_encryption_policy(
        policy_id="policy_mailbox_neo",
        mailbox_id="mailbox_neo",
    )


def _ready_envelope(message_id: str = "msg_001"):
    return make_symbolic_encrypted_envelope_metadata(
        envelope_id=f"env_{message_id}",
        message_id=message_id,
        encryption_identity_id="enc_mailbox_neo",
        key_bundle_id="kb_mailbox_neo_001",
    )


def _hub_with_identity_and_key() -> RegistryHub:
    hub = _hub()
    register_encryption_identity(hub, _identity())
    register_key_bundle_reference(hub, _key_bundle())
    return hub


def _prepared_hub(
    *,
    identity: EncryptionIdentity | None = None,
    key_bundle: KeyBundleReference | None = None,
) -> RegistryHub:
    hub = _hub()
    _register_mailbox(hub)
    register_encryption_identity(hub, _identity() if identity is None else identity)
    register_key_bundle_reference(hub, _key_bundle() if key_bundle is None else key_bundle)
    return hub


def _prepared_hub_with_binding_and_policy() -> RegistryHub:
    hub = _prepared_hub()
    register_mailbox_encryption_binding(hub, _binding())
    register_mailbox_encryption_policy(hub, _policy())
    return hub
