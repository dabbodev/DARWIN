"""Opt-in symbolic encrypted delivery result wrappers."""

from __future__ import annotations

from typing import Any

from darwin.models.encrypted_delivery import (
    EncryptedDeliveryAuditEntry,
    EncryptedDeliveryGateDecision,
    EncryptedDeliveryRequest,
    EncryptedDeliveryResult,
)
from darwin.models.hub import RegistryHub
from darwin.models.message import MessageDeliveryResult, MessageEnvelope
from darwin.registry.encrypted_delivery_policy import (
    evaluate_encrypted_delivery_request_policy,
)
from darwin.registry.message_delivery import deliver_message_to_mailbox


def evaluate_encrypted_delivery_request(
    registry_hub: RegistryHub,
    request: EncryptedDeliveryRequest,
    *,
    attempt_delivery: bool = False,
    retain_policy_decision: bool = True,
) -> EncryptedDeliveryResult:
    """Evaluate a symbolic delivery request and optionally attempt delivery."""
    if not isinstance(registry_hub, RegistryHub):
        raise TypeError("registry_hub must be a RegistryHub")
    if not isinstance(request, EncryptedDeliveryRequest):
        raise TypeError("request must be an EncryptedDeliveryRequest")
    if not isinstance(attempt_delivery, bool):
        raise TypeError("attempt_delivery must be a boolean")
    if not isinstance(retain_policy_decision, bool):
        raise TypeError("retain_policy_decision must be a boolean")

    gate_decision = evaluate_encrypted_delivery_request_policy(
        registry_hub,
        request,
        retain_decision=retain_policy_decision,
    )

    if request.mode.mode == "policy_check_only":
        return _make_result(
            request=request,
            gate_decision=gate_decision,
            delivery_result=None,
            status="policy_check_only",
            reason=gate_decision.reason.reason,
            delivery_attempted=False,
            metadata=_result_metadata(
                gate_decision=gate_decision,
                attempt_delivery=attempt_delivery,
                delivery_result=None,
                note="policy_check_only",
            ),
        )

    if not gate_decision.delivery_allowed:
        return _make_result(
            request=request,
            gate_decision=gate_decision,
            delivery_result=None,
            status=_blocked_status(gate_decision),
            reason=gate_decision.reason.reason,
            delivery_attempted=False,
            metadata=_result_metadata(
                gate_decision=gate_decision,
                attempt_delivery=attempt_delivery,
                delivery_result=None,
                note="gate_blocked",
            ),
        )

    if not attempt_delivery:
        return _make_result(
            request=request,
            gate_decision=gate_decision,
            delivery_result=None,
            status="not_delivered",
            reason="delivery_not_attempted",
            delivery_attempted=False,
            metadata=_result_metadata(
                gate_decision=gate_decision,
                attempt_delivery=False,
                delivery_result=None,
                note="delivery_not_attempted",
            ),
        )

    if not isinstance(request.message_envelope, MessageEnvelope):
        return _make_result(
            request=request,
            gate_decision=gate_decision,
            delivery_result=None,
            status="invalid_request",
            reason="missing_envelope",
            delivery_attempted=False,
            metadata=_result_metadata(
                gate_decision=gate_decision,
                attempt_delivery=True,
                delivery_result=None,
                note="missing_message_envelope",
            ),
        )

    delivery_result = deliver_message_to_mailbox(registry_hub, request.message_envelope)
    return _make_result(
        request=request,
        gate_decision=gate_decision,
        delivery_result=delivery_result,
        status=_status_from_delivery_result(delivery_result),
        reason=_reason_from_delivery_result(delivery_result),
        delivery_attempted=True,
        metadata=_result_metadata(
            gate_decision=gate_decision,
            attempt_delivery=True,
            delivery_result=delivery_result,
            note="delivery_attempted",
        ),
    )


def summarize_encrypted_delivery_result(
    result: EncryptedDeliveryResult,
) -> dict[str, object]:
    """Return a deterministic JSON-safe wrapped delivery result summary."""
    if not isinstance(result, EncryptedDeliveryResult):
        raise TypeError("result must be an EncryptedDeliveryResult")
    return result.to_summary()


def build_encrypted_delivery_audit_entry(
    result: EncryptedDeliveryResult,
) -> EncryptedDeliveryAuditEntry:
    """Build compact audit metadata from a wrapped encrypted delivery result."""
    if not isinstance(result, EncryptedDeliveryResult):
        raise TypeError("result must be an EncryptedDeliveryResult")
    gate_decision = _result_gate_decision(result)
    delivery_result = _result_delivery_result(result)
    return EncryptedDeliveryAuditEntry(
        request_id=result.request_id,
        message_id=result.message_id,
        mailbox_id=result.mailbox_id,
        lane_signature=result.lane_signature,
        gate_status=gate_decision.status.status,
        gate_reason=gate_decision.reason.reason,
        delivery_status=_audit_delivery_status(result, delivery_result),
        delivery_reason=_audit_delivery_reason(result, delivery_result),
        policy_id=gate_decision.policy_id,
        encryption_required=gate_decision.policy_required,
        envelope_accepted=gate_decision.envelope_accepted,
        metadata={
            "simulator_local": True,
            "wrapped_result": True,
            "delivery_attempted": result.delivery_attempted,
            "delivery_allowed": result.delivery_allowed,
            "policy_required": result.policy_required,
            "persistent_wrapped_history": False,
        },
    )


def _make_result(
    *,
    request: EncryptedDeliveryRequest,
    gate_decision: EncryptedDeliveryGateDecision,
    delivery_result: MessageDeliveryResult | None,
    status: str,
    reason: str | None,
    delivery_attempted: bool,
    metadata: dict[str, Any],
) -> EncryptedDeliveryResult:
    return EncryptedDeliveryResult(
        request_id=request.request_id,
        message_id=gate_decision.message_id,
        mailbox_id=gate_decision.mailbox_id,
        lane_signature=gate_decision.lane_signature,
        gate_decision=gate_decision,
        delivery_result=delivery_result,
        status=status,
        reason=reason,
        delivery_attempted=delivery_attempted,
        delivery_allowed=gate_decision.delivery_allowed,
        policy_required=gate_decision.policy_required,
        metadata=metadata,
    )


def _result_metadata(
    *,
    gate_decision: EncryptedDeliveryGateDecision,
    attempt_delivery: bool,
    delivery_result: MessageDeliveryResult | None,
    note: str,
) -> dict[str, Any]:
    inbox_mutated = (
        delivery_result is not None and delivery_result.status.status == "delivered"
    )
    return {
        "simulator_local": True,
        "wrapped_result": True,
        "symbolic_policy_gate": True,
        "attempt_delivery_requested": attempt_delivery,
        "delivery_result_created": delivery_result is not None,
        "message_delivery_results_mutated": delivery_result is not None,
        "inbox_mutated": inbox_mutated,
        "message_mutated": False,
        "delivery_behavior_changed": False,
        "persistent_wrapped_history": False,
        "real_ciphertext": False,
        "networking": False,
        "dns_lookup": False,
        "durable_queue": False,
        "policy_decision_retained": gate_decision.metadata.get(
            "policy_decision_retained",
            False,
        ),
        "note": note,
    }


def _blocked_status(gate_decision: EncryptedDeliveryGateDecision) -> str:
    if gate_decision.status.status == "invalid_request":
        return "invalid_request"
    return "gate_blocked"


def _status_from_delivery_result(delivery_result: MessageDeliveryResult) -> str:
    if delivery_result.status.status == "delivered":
        return "delivered"
    return "not_delivered"


def _reason_from_delivery_result(delivery_result: MessageDeliveryResult) -> str | None:
    if delivery_result.reason is not None:
        return delivery_result.reason.reason
    if delivery_result.status.status == "delivered":
        return None
    return delivery_result.status.status


def _result_gate_decision(
    result: EncryptedDeliveryResult,
) -> EncryptedDeliveryGateDecision:
    gate_decision = result.gate_decision
    if not isinstance(gate_decision, EncryptedDeliveryGateDecision):
        raise TypeError("result must carry an EncryptedDeliveryGateDecision")
    return gate_decision


def _result_delivery_result(
    result: EncryptedDeliveryResult,
) -> MessageDeliveryResult | None:
    delivery_result = result.delivery_result
    if delivery_result is None:
        return None
    if not isinstance(delivery_result, MessageDeliveryResult):
        raise TypeError("result delivery_result must be a MessageDeliveryResult")
    return delivery_result


def _audit_delivery_status(
    result: EncryptedDeliveryResult,
    delivery_result: MessageDeliveryResult | None,
) -> str:
    if delivery_result is not None:
        return delivery_result.status.status
    if result.delivery_attempted:
        return "not_delivered"
    return "not_attempted"


def _audit_delivery_reason(
    result: EncryptedDeliveryResult,
    delivery_result: MessageDeliveryResult | None,
) -> str | None:
    if delivery_result is not None and delivery_result.reason is not None:
        return delivery_result.reason.reason
    if delivery_result is not None:
        return _reason_from_delivery_result(delivery_result)
    return result.reason


__all__ = [
    "build_encrypted_delivery_audit_entry",
    "evaluate_encrypted_delivery_request",
    "summarize_encrypted_delivery_result",
]
