"""RegistryHub-local symbolic encryption registry helpers."""

from __future__ import annotations

from darwin.models.encryption import (
    EncryptedEnvelopeMetadata,
    EncryptionIdentity,
    EncryptionPolicyDecision,
    EncryptionProfile,
    KeyBundleReference,
    KeyBundleStatus,
    MailboxEncryptionBinding,
    MailboxEncryptionPolicy,
    SymbolicEncryptedMessageEnvelope,
    evaluate_mailbox_encryption_policy,
)
from darwin.models.hub import RegistryHub
from darwin.models.lane_signature import LaneSignature, parse_lane_signature


def register_encryption_identity(
    registry_hub: RegistryHub,
    identity: EncryptionIdentity,
) -> EncryptionIdentity:
    """Store or replace a symbolic encryption identity by identity ID."""
    if not isinstance(identity, EncryptionIdentity):
        raise TypeError("identity must be an EncryptionIdentity")
    registry_hub.encryption_identities[identity.encryption_identity_id] = identity
    return identity


def get_encryption_identity(
    registry_hub: RegistryHub,
    encryption_identity_id: str,
) -> EncryptionIdentity | None:
    """Return a registered encryption identity, if present."""
    _validate_required_string(encryption_identity_id, "encryption_identity_id")
    return registry_hub.encryption_identities.get(encryption_identity_id)


def list_encryption_identities(
    registry_hub: RegistryHub,
    *,
    subject_id: str | None = None,
    subject_kind: str | None = None,
    profile: EncryptionProfile | str | None = None,
    status: str | None = None,
) -> list[EncryptionIdentity]:
    """Return encryption identities in deterministic identity ID order."""
    _validate_optional_string(subject_id, "subject_id")
    _validate_optional_string(subject_kind, "subject_kind")
    _validate_optional_string(status, "status")
    profile_key = _profile_key(profile)

    return [
        identity
        for _, identity in sorted(registry_hub.encryption_identities.items())
        if (subject_id is None or identity.subject_id == subject_id)
        and (subject_kind is None or identity.subject_kind == subject_kind)
        and (profile_key is None or identity.profile == profile_key)
        and (status is None or identity.status == status)
    ]


def register_key_bundle_reference(
    registry_hub: RegistryHub,
    key_bundle: KeyBundleReference,
) -> KeyBundleReference:
    """Store or replace a symbolic key bundle reference by bundle ID."""
    if not isinstance(key_bundle, KeyBundleReference):
        raise TypeError("key_bundle must be a KeyBundleReference")
    if key_bundle.encryption_identity_id not in registry_hub.encryption_identities:
        raise KeyError(
            "encryption_identity_id is not registered: "
            f"{key_bundle.encryption_identity_id}"
        )
    registry_hub.key_bundle_references[key_bundle.key_bundle_id] = key_bundle
    return key_bundle


def get_key_bundle_reference(
    registry_hub: RegistryHub,
    key_bundle_id: str,
) -> KeyBundleReference | None:
    """Return a registered key bundle reference, if present."""
    _validate_required_string(key_bundle_id, "key_bundle_id")
    return registry_hub.key_bundle_references.get(key_bundle_id)


def list_key_bundle_references(
    registry_hub: RegistryHub,
    *,
    encryption_identity_id: str | None = None,
    profile: EncryptionProfile | str | None = None,
    status: KeyBundleStatus | str | None = None,
) -> list[KeyBundleReference]:
    """Return key bundle references in deterministic bundle ID order."""
    _validate_optional_string(encryption_identity_id, "encryption_identity_id")
    profile_key = _profile_key(profile)
    status_key = _key_bundle_status_key(status)

    return [
        key_bundle
        for _, key_bundle in sorted(registry_hub.key_bundle_references.items())
        if (
            encryption_identity_id is None
            or key_bundle.encryption_identity_id == encryption_identity_id
        )
        and (profile_key is None or key_bundle.profile == profile_key)
        and (status_key is None or key_bundle.status.status == status_key)
    ]


def register_mailbox_encryption_binding(
    registry_hub: RegistryHub,
    binding: MailboxEncryptionBinding,
) -> MailboxEncryptionBinding:
    """Store or replace a mailbox encryption binding by mailbox ID."""
    if not isinstance(binding, MailboxEncryptionBinding):
        raise TypeError("binding must be a MailboxEncryptionBinding")
    if binding.mailbox_id not in registry_hub.mailboxes:
        raise KeyError(f"mailbox_id is not registered: {binding.mailbox_id}")
    if binding.encryption_identity_id not in registry_hub.encryption_identities:
        raise KeyError(
            "encryption_identity_id is not registered: "
            f"{binding.encryption_identity_id}"
        )
    key_bundle = registry_hub.key_bundle_references.get(binding.key_bundle_id)
    if key_bundle is None:
        raise KeyError(f"key_bundle_id is not registered: {binding.key_bundle_id}")
    if key_bundle.encryption_identity_id != binding.encryption_identity_id:
        raise ValueError(
            "binding encryption_identity_id must match the key bundle reference"
        )
    registry_hub.mailbox_encryption_bindings[binding.mailbox_id] = binding
    return binding


def get_mailbox_encryption_binding(
    registry_hub: RegistryHub,
    mailbox_id: str,
) -> MailboxEncryptionBinding | None:
    """Return a registered mailbox encryption binding, if present."""
    _validate_required_string(mailbox_id, "mailbox_id")
    return registry_hub.mailbox_encryption_bindings.get(mailbox_id)


def list_mailbox_encryption_bindings(
    registry_hub: RegistryHub,
    *,
    mailbox_id: str | None = None,
    encryption_identity_id: str | None = None,
    key_bundle_id: str | None = None,
    profile: EncryptionProfile | str | None = None,
    status: str | None = None,
    lane_signature: LaneSignature | str | None = None,
) -> list[MailboxEncryptionBinding]:
    """Return mailbox encryption bindings in deterministic mailbox ID order."""
    _validate_optional_string(mailbox_id, "mailbox_id")
    _validate_optional_string(encryption_identity_id, "encryption_identity_id")
    _validate_optional_string(key_bundle_id, "key_bundle_id")
    _validate_optional_string(status, "status")
    profile_key = _profile_key(profile)
    lane_signature_key = _lane_signature_key(lane_signature)

    return [
        binding
        for _, binding in sorted(registry_hub.mailbox_encryption_bindings.items())
        if (mailbox_id is None or binding.mailbox_id == mailbox_id)
        and (
            encryption_identity_id is None
            or binding.encryption_identity_id == encryption_identity_id
        )
        and (key_bundle_id is None or binding.key_bundle_id == key_bundle_id)
        and (profile_key is None or binding.profile == profile_key)
        and (status is None or binding.status == status)
        and (
            lane_signature_key is None
            or lane_signature_key in binding.required_for_lanes
        )
    ]


def register_mailbox_encryption_policy(
    registry_hub: RegistryHub,
    policy: MailboxEncryptionPolicy,
) -> MailboxEncryptionPolicy:
    """Store or replace a mailbox encryption policy by policy ID."""
    if not isinstance(policy, MailboxEncryptionPolicy):
        raise TypeError("policy must be a MailboxEncryptionPolicy")
    if policy.mailbox_id not in registry_hub.mailboxes:
        raise KeyError(f"mailbox_id is not registered: {policy.mailbox_id}")
    registry_hub.mailbox_encryption_policies[policy.policy_id] = policy
    return policy


def get_mailbox_encryption_policy(
    registry_hub: RegistryHub,
    policy_id: str,
) -> MailboxEncryptionPolicy | None:
    """Return a registered mailbox encryption policy, if present."""
    _validate_required_string(policy_id, "policy_id")
    return registry_hub.mailbox_encryption_policies.get(policy_id)


def get_mailbox_encryption_policy_for_mailbox(
    registry_hub: RegistryHub,
    mailbox_id: str,
) -> MailboxEncryptionPolicy | None:
    """Return the first deterministic encryption policy registered for a mailbox."""
    _validate_required_string(mailbox_id, "mailbox_id")
    for _, policy in sorted(registry_hub.mailbox_encryption_policies.items()):
        if policy.mailbox_id == mailbox_id:
            return policy
    return None


def list_mailbox_encryption_policies(
    registry_hub: RegistryHub,
    *,
    mailbox_id: str | None = None,
    lane_signature: LaneSignature | str | None = None,
    profile: EncryptionProfile | str | None = None,
) -> list[MailboxEncryptionPolicy]:
    """Return mailbox encryption policies in deterministic policy ID order."""
    _validate_optional_string(mailbox_id, "mailbox_id")
    lane_signature_key = _lane_signature_key(lane_signature)
    profile_key = _profile_key(profile)

    return [
        policy
        for _, policy in sorted(registry_hub.mailbox_encryption_policies.items())
        if (mailbox_id is None or policy.mailbox_id == mailbox_id)
        and (
            lane_signature_key is None
            or lane_signature_key in policy.required_for_lanes
        )
        and (profile_key is None or profile_key in policy.allowed_profiles)
    ]


def evaluate_registered_mailbox_encryption_policy(
    registry_hub: RegistryHub,
    *,
    mailbox_id: str,
    lane_signature: LaneSignature | str,
    message_id: str | None = None,
    envelope_metadata: (
        EncryptedEnvelopeMetadata | SymbolicEncryptedMessageEnvelope | None
    ) = None,
    retain: bool = True,
) -> EncryptionPolicyDecision:
    """Evaluate a registered policy and optionally retain the decision on the hub."""
    _validate_required_string(mailbox_id, "mailbox_id")
    _validate_optional_string(message_id, "message_id")
    if not isinstance(retain, bool):
        raise TypeError("retain must be a boolean")
    lane_signature_key = _required_lane_signature_key(lane_signature)
    metadata = _envelope_metadata(envelope_metadata)
    if metadata is not None:
        if message_id is None:
            message_id = metadata.message_id
        elif message_id != metadata.message_id:
            raise ValueError("message_id must match envelope metadata")

    policy = get_mailbox_encryption_policy_for_mailbox(registry_hub, mailbox_id)
    if policy is None:
        decision = EncryptionPolicyDecision(
            policy_id="no_registered_policy",
            mailbox_id=mailbox_id,
            lane_signature=lane_signature_key,
            message_id=message_id,
            status="plaintext_allowed",
            reason=None,
            encryption_required=False,
            envelope_accepted=False,
            profile=None,
            encryption_identity_id=None,
            key_bundle_id=None,
            metadata={
                "simulator_local": True,
                "message_mutated": False,
                "registry_hub_mutated": retain,
                "retained_in_registry_hub": retain,
                "delivery_behavior_changed": False,
                "registry_hub": registry_hub.hub_id,
                "note": "no_registered_policy",
            },
        )
        if retain:
            registry_hub.encryption_policy_decision_history.append(decision)
        return decision

    binding = get_mailbox_encryption_binding(registry_hub, mailbox_id)
    identity = None
    key_bundle = None
    if binding is not None:
        identity = get_encryption_identity(
            registry_hub,
            binding.encryption_identity_id,
        )
        key_bundle = get_key_bundle_reference(registry_hub, binding.key_bundle_id)

    decision = evaluate_mailbox_encryption_policy(
        policy,
        lane_signature=lane_signature_key,
        message_id=message_id,
        envelope_metadata=metadata,
        encryption_identity=identity,
        key_bundle=key_bundle,
    )
    decision = _decision_with_registry_retention_metadata(
        decision,
        registry_hub_id=registry_hub.hub_id,
        retain=retain,
    )
    if retain:
        registry_hub.encryption_policy_decision_history.append(decision)
    return decision


def query_encryption_policy_decisions(
    registry_hub: RegistryHub,
    *,
    policy_id: str | None = None,
    mailbox_id: str | None = None,
    lane_signature: LaneSignature | str | None = None,
    message_id: str | None = None,
    status: str | None = None,
    reason: str | None = None,
    encryption_required: bool | None = None,
    envelope_accepted: bool | None = None,
    profile: EncryptionProfile | str | None = None,
    encryption_identity_id: str | None = None,
    key_bundle_id: str | None = None,
) -> list[EncryptionPolicyDecision]:
    """Query retained encryption policy decisions without mutating hub state."""
    _validate_optional_string(policy_id, "policy_id")
    _validate_optional_string(mailbox_id, "mailbox_id")
    lane_signature_key = _lane_signature_key(lane_signature)
    _validate_optional_string(message_id, "message_id")
    _validate_optional_string(status, "status")
    _validate_optional_string(reason, "reason")
    _validate_optional_bool(encryption_required, "encryption_required")
    _validate_optional_bool(envelope_accepted, "envelope_accepted")
    profile_key = _profile_key(profile)
    _validate_optional_string(encryption_identity_id, "encryption_identity_id")
    _validate_optional_string(key_bundle_id, "key_bundle_id")

    return [
        decision
        for decision in registry_hub.encryption_policy_decision_history
        if (policy_id is None or decision.policy_id == policy_id)
        and (mailbox_id is None or decision.mailbox_id == mailbox_id)
        and (
            lane_signature_key is None
            or decision.lane_signature == lane_signature_key
        )
        and (message_id is None or decision.message_id == message_id)
        and (status is None or decision.status.status == status)
        and (
            reason is None
            or (decision.reason is not None and decision.reason.reason == reason)
        )
        and (
            encryption_required is None
            or decision.encryption_required is encryption_required
        )
        and (
            envelope_accepted is None
            or decision.envelope_accepted is envelope_accepted
        )
        and (profile_key is None or decision.profile == profile_key)
        and (
            encryption_identity_id is None
            or decision.encryption_identity_id == encryption_identity_id
        )
        and (key_bundle_id is None or decision.key_bundle_id == key_bundle_id)
    ]


def _decision_with_registry_retention_metadata(
    decision: EncryptionPolicyDecision,
    *,
    registry_hub_id: str,
    retain: bool,
) -> EncryptionPolicyDecision:
    metadata = dict(decision.metadata or {})
    metadata["registry_hub_mutated"] = retain
    metadata["retained_in_registry_hub"] = retain
    metadata["registry_hub"] = registry_hub_id
    return EncryptionPolicyDecision(
        policy_id=decision.policy_id,
        mailbox_id=decision.mailbox_id,
        lane_signature=decision.lane_signature,
        message_id=decision.message_id,
        status=decision.status,
        reason=decision.reason,
        encryption_required=decision.encryption_required,
        envelope_accepted=decision.envelope_accepted,
        profile=decision.profile,
        encryption_identity_id=decision.encryption_identity_id,
        key_bundle_id=decision.key_bundle_id,
        metadata=metadata,
    )


def _profile_key(profile: EncryptionProfile | str | None) -> str | None:
    if profile is None:
        return None
    if isinstance(profile, EncryptionProfile):
        return profile.profile
    if isinstance(profile, str):
        return EncryptionProfile(profile).profile
    raise TypeError("profile must be an EncryptionProfile, string, or None")


def _key_bundle_status_key(status: KeyBundleStatus | str | None) -> str | None:
    if status is None:
        return None
    if isinstance(status, KeyBundleStatus):
        return status.status
    if isinstance(status, str):
        return KeyBundleStatus(status).status
    raise TypeError("status must be a KeyBundleStatus, string, or None")


def _lane_signature_key(lane_signature: LaneSignature | str | None) -> str | None:
    if lane_signature is None:
        return None
    return _required_lane_signature_key(lane_signature)


def _required_lane_signature_key(lane_signature: LaneSignature | str) -> str:
    if isinstance(lane_signature, LaneSignature):
        return lane_signature.signature
    if isinstance(lane_signature, str):
        return parse_lane_signature(lane_signature).signature
    raise TypeError("lane_signature must be a LaneSignature or string")


def _envelope_metadata(
    envelope_metadata: (
        EncryptedEnvelopeMetadata | SymbolicEncryptedMessageEnvelope | None
    ),
) -> EncryptedEnvelopeMetadata | None:
    if envelope_metadata is None:
        return None
    if isinstance(envelope_metadata, SymbolicEncryptedMessageEnvelope):
        return envelope_metadata.encryption_metadata
    if isinstance(envelope_metadata, EncryptedEnvelopeMetadata):
        return envelope_metadata
    raise TypeError(
        "envelope_metadata must be encrypted metadata, a symbolic envelope, or None"
    )


def _validate_required_string(value: str, field_name: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} is required")
    if value.strip() != value or any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")


def _validate_optional_string(value: str | None, field_name: str) -> None:
    if value is None:
        return
    _validate_required_string(value, field_name)


def _validate_optional_bool(value: bool | None, field_name: str) -> None:
    if value is None:
        return
    if not isinstance(value, bool):
        raise TypeError(f"{field_name} must be a boolean or None")


__all__ = [
    "evaluate_registered_mailbox_encryption_policy",
    "get_encryption_identity",
    "get_key_bundle_reference",
    "get_mailbox_encryption_binding",
    "get_mailbox_encryption_policy",
    "get_mailbox_encryption_policy_for_mailbox",
    "list_encryption_identities",
    "list_key_bundle_references",
    "list_mailbox_encryption_bindings",
    "list_mailbox_encryption_policies",
    "query_encryption_policy_decisions",
    "register_encryption_identity",
    "register_key_bundle_reference",
    "register_mailbox_encryption_binding",
    "register_mailbox_encryption_policy",
]
