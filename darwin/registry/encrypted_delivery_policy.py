"""Opt-in symbolic encrypted delivery policy gate helpers."""

from __future__ import annotations

from typing import Any

from darwin.models.encrypted_delivery import (
    EncryptedDeliveryGateDecision,
    EncryptedDeliveryRequest,
    delivery_request_status,
)
from darwin.models.encryption import (
    EncryptedEnvelopeMetadata,
    EncryptionPolicyDecision,
    is_encryption_policy_decision_accepted,
)
from darwin.models.hub import RegistryHub
from darwin.models.message import MessageEnvelope
from darwin.registry.encryption_registry import (
    evaluate_registered_mailbox_encryption_policy,
    get_mailbox_encryption_policy,
    get_mailbox_encryption_policy_for_mailbox,
)
from darwin.registry.mailbox_registry import resolve_mailbox_address


def evaluate_encrypted_delivery_request_policy(
    registry_hub: RegistryHub,
    request: EncryptedDeliveryRequest,
    *,
    retain_decision: bool = True,
) -> EncryptedDeliveryGateDecision:
    """Evaluate an encrypted delivery request against registered symbolic policy."""
    if not isinstance(registry_hub, RegistryHub):
        raise TypeError("registry_hub must be a RegistryHub")
    if not isinstance(request, EncryptedDeliveryRequest):
        raise TypeError("request must be an EncryptedDeliveryRequest")
    if not isinstance(retain_decision, bool):
        raise TypeError("retain_decision must be a boolean")

    message_id = _request_message_id(request)
    mailbox_id = _request_mailbox_id(registry_hub, request)
    lane_signature = request.lane_signature
    structural_status = delivery_request_status(request)

    if structural_status.status == "invalid":
        return _make_gate_decision(
            request=request,
            message_id=message_id,
            mailbox_id=mailbox_id,
            lane_signature=lane_signature,
            policy_id=request.policy_id,
            status="invalid_request",
            reason="invalid_request",
            delivery_allowed=False,
            policy_required=request.policy_required or request.policy_id is not None,
            envelope_accepted=False,
            retain_decision=retain_decision,
        )

    if mailbox_id is None:
        return _make_gate_decision(
            request=request,
            message_id=message_id,
            mailbox_id=None,
            lane_signature=lane_signature,
            policy_id=request.policy_id,
            status="invalid_request",
            reason="missing_mailbox_reference",
            delivery_allowed=False,
            policy_required=request.policy_required or request.policy_id is not None,
            envelope_accepted=False,
            retain_decision=retain_decision,
        )

    if lane_signature is None:
        return _make_gate_decision(
            request=request,
            message_id=message_id,
            mailbox_id=mailbox_id,
            lane_signature=None,
            policy_id=request.policy_id,
            status="invalid_request",
            reason="invalid_request",
            delivery_allowed=False,
            policy_required=request.policy_required or request.policy_id is not None,
            envelope_accepted=False,
            retain_decision=retain_decision,
        )

    policy = None
    if request.policy_id is not None:
        policy = get_mailbox_encryption_policy(registry_hub, request.policy_id)
        if policy is None:
            return _make_gate_decision(
                request=request,
                message_id=message_id,
                mailbox_id=mailbox_id,
                lane_signature=lane_signature,
                policy_id=request.policy_id,
                status="policy_missing",
                reason="missing_policy_reference",
                delivery_allowed=False,
                policy_required=True,
                envelope_accepted=False,
                retain_decision=retain_decision,
            )
        if policy.mailbox_id != mailbox_id:
            return _make_gate_decision(
                request=request,
                message_id=message_id,
                mailbox_id=mailbox_id,
                lane_signature=lane_signature,
                policy_id=request.policy_id,
                status="invalid_request",
                reason="invalid_request",
                delivery_allowed=False,
                policy_required=True,
                envelope_accepted=False,
                retain_decision=retain_decision,
            )
    else:
        policy = get_mailbox_encryption_policy_for_mailbox(registry_hub, mailbox_id)

    policy_required = request.policy_required or request.policy_id is not None
    if not policy_required and policy is None:
        return _make_gate_decision(
            request=request,
            message_id=message_id,
            mailbox_id=mailbox_id,
            lane_signature=lane_signature,
            policy_id=None,
            status="plaintext_allowed",
            reason="plaintext_no_policy_required",
            delivery_allowed=True,
            policy_required=False,
            envelope_accepted=False,
            retain_decision=retain_decision,
        )

    if policy_required and policy is None:
        return _make_gate_decision(
            request=request,
            message_id=message_id,
            mailbox_id=mailbox_id,
            lane_signature=lane_signature,
            policy_id=request.policy_id,
            status="policy_missing",
            reason="policy_not_found",
            delivery_allowed=False,
            policy_required=True,
            envelope_accepted=False,
            retain_decision=retain_decision,
        )

    policy_decision = evaluate_registered_mailbox_encryption_policy(
        registry_hub,
        mailbox_id=mailbox_id,
        lane_signature=lane_signature,
        message_id=message_id,
        envelope_metadata=_request_envelope_metadata(request),
        retain=retain_decision,
    )
    delivery_allowed = is_encryption_policy_decision_accepted(policy_decision)
    return _make_gate_decision(
        request=request,
        message_id=policy_decision.message_id,
        mailbox_id=mailbox_id,
        lane_signature=policy_decision.lane_signature,
        policy_id=policy_decision.policy_id,
        status=_gate_status_from_policy_decision(policy_decision),
        reason=_gate_reason_from_policy_decision(policy_decision),
        policy_decision=policy_decision,
        delivery_allowed=delivery_allowed,
        policy_required=policy_required or policy_decision.encryption_required,
        envelope_accepted=policy_decision.envelope_accepted,
        retain_decision=retain_decision,
    )


def _make_gate_decision(
    *,
    request: EncryptedDeliveryRequest,
    message_id: str | None,
    mailbox_id: str | None,
    lane_signature: str | None,
    policy_id: str | None,
    status: str,
    reason: str,
    delivery_allowed: bool,
    policy_required: bool,
    envelope_accepted: bool,
    retain_decision: bool,
    policy_decision: EncryptionPolicyDecision | None = None,
) -> EncryptedDeliveryGateDecision:
    return EncryptedDeliveryGateDecision(
        request_id=request.request_id,
        message_id=message_id,
        mailbox_id=mailbox_id,
        lane_signature=lane_signature,
        policy_id=policy_id,
        status=status,
        reason=reason,
        policy_decision=policy_decision,
        delivery_allowed=delivery_allowed,
        policy_required=policy_required,
        envelope_accepted=envelope_accepted,
        metadata={
            "simulator_local": True,
            "gate_only": True,
            "gate_decision_retained": False,
            "policy_decision_retained": retain_decision and policy_decision is not None,
            "message_mutated": False,
            "inbox_mutated": False,
            "delivery_result_created": False,
            "delivery_behavior_changed": False,
            "real_ciphertext": False,
        },
    )


def _request_message_id(request: EncryptedDeliveryRequest) -> str | None:
    message_envelope = request.message_envelope
    if isinstance(message_envelope, MessageEnvelope):
        return message_envelope.message_id
    if isinstance(message_envelope, dict):
        value = message_envelope.get("message_id")
        if value is not None and not isinstance(value, str):
            raise TypeError("message_envelope message_id must be a string")
        return value
    metadata = request.encryption_metadata
    if isinstance(metadata, EncryptedEnvelopeMetadata):
        return metadata.message_id
    if isinstance(metadata, dict):
        value = metadata.get("message_id")
        if value is not None and not isinstance(value, str):
            raise TypeError("encryption_metadata message_id must be a string")
        return value
    return None


def _request_mailbox_id(
    registry_hub: RegistryHub,
    request: EncryptedDeliveryRequest,
) -> str | None:
    if request.mailbox_id is not None:
        return request.mailbox_id
    recipient_address = _request_recipient_address(request)
    if recipient_address is None:
        return None
    mailbox = resolve_mailbox_address(registry_hub, recipient_address)
    if mailbox is None:
        return None
    return mailbox.mailbox_id


def _request_recipient_address(request: EncryptedDeliveryRequest) -> str | None:
    message_envelope = request.message_envelope
    if isinstance(message_envelope, MessageEnvelope):
        return message_envelope.recipient_address
    if isinstance(message_envelope, dict):
        value = message_envelope.get("recipient_address")
        if value is not None and not isinstance(value, str):
            raise TypeError("message_envelope recipient_address must be a string")
        return value
    return None


def _request_envelope_metadata(
    request: EncryptedDeliveryRequest,
) -> EncryptedEnvelopeMetadata | None:
    metadata = request.encryption_metadata
    if metadata is None:
        return None
    if isinstance(metadata, EncryptedEnvelopeMetadata):
        return metadata
    if isinstance(metadata, dict):
        return EncryptedEnvelopeMetadata(**_metadata_constructor_values(metadata))
    raise TypeError("encryption_metadata must be encrypted metadata, dict, or None")


def _metadata_constructor_values(metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "envelope_id": metadata["envelope_id"],
        "message_id": metadata["message_id"],
        "encryption_identity_id": metadata.get("encryption_identity_id"),
        "key_bundle_id": metadata.get("key_bundle_id"),
        "profile": metadata.get("profile", "symbolic_e2ee_v1"),
        "state": metadata.get("state", "plaintext"),
        "status": metadata.get("status", "ready"),
        "algorithm_ref": metadata.get("algorithm_ref"),
        "ciphertext_ref": metadata.get("ciphertext_ref"),
        "plaintext_ref": metadata.get("plaintext_ref"),
        "metadata": metadata.get("metadata", {}),
    }


def _gate_status_from_policy_decision(decision: EncryptionPolicyDecision) -> str:
    if decision.status.status == "accepted":
        return "allowed"
    if decision.status.status == "plaintext_allowed":
        return "plaintext_allowed"
    return "policy_check_failed"


def _gate_reason_from_policy_decision(decision: EncryptionPolicyDecision) -> str:
    if decision.status.status == "accepted":
        return "accepted"
    if decision.reason is not None:
        return decision.reason.reason
    if decision.status.status == "plaintext_allowed":
        return "plaintext_no_policy_required"
    return "invalid_request"


__all__ = ["evaluate_encrypted_delivery_request_policy"]
