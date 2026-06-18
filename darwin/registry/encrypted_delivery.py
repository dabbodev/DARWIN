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
from darwin.models.lane_signature import LaneSignature, parse_lane_signature
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
    retain_result: bool = True,
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
    if not isinstance(retain_result, bool):
        raise TypeError("retain_result must be a boolean")

    gate_decision = evaluate_encrypted_delivery_request_policy(
        registry_hub,
        request,
        retain_decision=retain_policy_decision,
    )

    if request.mode.mode == "policy_check_only":
        return _make_retained_result(
            registry_hub=registry_hub,
            retain_result=retain_result,
            request=request,
            gate_decision=gate_decision,
            delivery_result=None,
            status="policy_check_only",
            reason=gate_decision.reason.reason,
            delivery_attempted=False,
            metadata=_result_metadata(
                registry_hub_id=registry_hub.hub_id,
                gate_decision=gate_decision,
                attempt_delivery=attempt_delivery,
                delivery_result=None,
                note="policy_check_only",
                retain_result=retain_result,
            ),
        )

    if not gate_decision.delivery_allowed:
        return _make_retained_result(
            registry_hub=registry_hub,
            retain_result=retain_result,
            request=request,
            gate_decision=gate_decision,
            delivery_result=None,
            status=_blocked_status(gate_decision),
            reason=gate_decision.reason.reason,
            delivery_attempted=False,
            metadata=_result_metadata(
                registry_hub_id=registry_hub.hub_id,
                gate_decision=gate_decision,
                attempt_delivery=attempt_delivery,
                delivery_result=None,
                note="gate_blocked",
                retain_result=retain_result,
            ),
        )

    if not attempt_delivery:
        return _make_retained_result(
            registry_hub=registry_hub,
            retain_result=retain_result,
            request=request,
            gate_decision=gate_decision,
            delivery_result=None,
            status="not_delivered",
            reason="delivery_not_attempted",
            delivery_attempted=False,
            metadata=_result_metadata(
                registry_hub_id=registry_hub.hub_id,
                gate_decision=gate_decision,
                attempt_delivery=False,
                delivery_result=None,
                note="delivery_not_attempted",
                retain_result=retain_result,
            ),
        )

    if not isinstance(request.message_envelope, MessageEnvelope):
        return _make_retained_result(
            registry_hub=registry_hub,
            retain_result=retain_result,
            request=request,
            gate_decision=gate_decision,
            delivery_result=None,
            status="invalid_request",
            reason="missing_envelope",
            delivery_attempted=False,
            metadata=_result_metadata(
                registry_hub_id=registry_hub.hub_id,
                gate_decision=gate_decision,
                attempt_delivery=True,
                delivery_result=None,
                note="missing_message_envelope",
                retain_result=retain_result,
            ),
        )

    delivery_result = deliver_message_to_mailbox(registry_hub, request.message_envelope)
    return _make_retained_result(
        registry_hub=registry_hub,
        retain_result=retain_result,
        request=request,
        gate_decision=gate_decision,
        delivery_result=delivery_result,
        status=_status_from_delivery_result(delivery_result),
        reason=_reason_from_delivery_result(delivery_result),
        delivery_attempted=True,
        metadata=_result_metadata(
            registry_hub_id=registry_hub.hub_id,
            gate_decision=gate_decision,
            attempt_delivery=True,
            delivery_result=delivery_result,
            note="delivery_attempted",
            retain_result=retain_result,
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
            "persistent_wrapped_history": _result_retained(result),
        },
    )


def query_encrypted_delivery_results(
    registry_hub: RegistryHub,
    *,
    request_id: str | None = None,
    message_id: str | None = None,
    mailbox_id: str | None = None,
    lane_signature: LaneSignature | str | None = None,
    status: str | None = None,
    reason: str | None = None,
    delivery_attempted: bool | None = None,
    delivery_allowed: bool | None = None,
    policy_required: bool | None = None,
    gate_status: str | None = None,
    gate_reason: str | None = None,
    delivery_status: str | None = None,
    delivery_reason: str | None = None,
    endpoint_id: str | None = None,
) -> list[EncryptedDeliveryResult]:
    """Query retained wrapped encrypted delivery results without mutation."""
    if not isinstance(registry_hub, RegistryHub):
        raise TypeError("registry_hub must be a RegistryHub")
    _validate_optional_string(request_id, "request_id")
    _validate_optional_string(message_id, "message_id")
    _validate_optional_string(mailbox_id, "mailbox_id")
    lane_signature_key = _lane_signature_key(lane_signature)
    _validate_optional_string(status, "status")
    _validate_optional_string(reason, "reason")
    _validate_optional_bool(delivery_attempted, "delivery_attempted")
    _validate_optional_bool(delivery_allowed, "delivery_allowed")
    _validate_optional_bool(policy_required, "policy_required")
    _validate_optional_string(gate_status, "gate_status")
    _validate_optional_string(gate_reason, "gate_reason")
    _validate_optional_string(delivery_status, "delivery_status")
    _validate_optional_string(delivery_reason, "delivery_reason")
    _validate_optional_string(endpoint_id, "endpoint_id")

    return [
        result
        for result in registry_hub.encrypted_delivery_result_history
        if (request_id is None or result.request_id == request_id)
        and (message_id is None or result.message_id == message_id)
        and (mailbox_id is None or result.mailbox_id == mailbox_id)
        and (
            lane_signature_key is None
            or result.lane_signature == lane_signature_key
        )
        and (status is None or result.status.status == status)
        and (reason is None or result.reason == reason)
        and (
            delivery_attempted is None
            or result.delivery_attempted is delivery_attempted
        )
        and (
            delivery_allowed is None
            or result.delivery_allowed is delivery_allowed
        )
        and (
            policy_required is None
            or result.policy_required is policy_required
        )
        and _result_nested_filters_match(
            result,
            gate_status=gate_status,
            gate_reason=gate_reason,
            delivery_status=delivery_status,
            delivery_reason=delivery_reason,
            endpoint_id=endpoint_id,
        )
    ]


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


def _make_retained_result(
    *,
    registry_hub: RegistryHub,
    retain_result: bool,
    request: EncryptedDeliveryRequest,
    gate_decision: EncryptedDeliveryGateDecision,
    delivery_result: MessageDeliveryResult | None,
    status: str,
    reason: str | None,
    delivery_attempted: bool,
    metadata: dict[str, Any],
) -> EncryptedDeliveryResult:
    result = _make_result(
        request=request,
        gate_decision=gate_decision,
        delivery_result=delivery_result,
        status=status,
        reason=reason,
        delivery_attempted=delivery_attempted,
        metadata=metadata,
    )
    if retain_result:
        registry_hub.encrypted_delivery_result_history.append(result)
    return result


def _result_metadata(
    *,
    registry_hub_id: str,
    gate_decision: EncryptedDeliveryGateDecision,
    attempt_delivery: bool,
    delivery_result: MessageDeliveryResult | None,
    note: str,
    retain_result: bool,
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
        "persistent_wrapped_history": retain_result,
        "registry_hub_mutated": retain_result,
        "retained_in_registry_hub": retain_result,
        "registry_hub": registry_hub_id,
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


def _result_nested_filters_match(
    result: EncryptedDeliveryResult,
    *,
    gate_status: str | None,
    gate_reason: str | None,
    delivery_status: str | None,
    delivery_reason: str | None,
    endpoint_id: str | None,
) -> bool:
    gate_decision = _result_gate_decision_summary(result.gate_decision)
    if gate_status is not None and gate_decision.get("status") != gate_status:
        return False
    if gate_reason is not None and gate_decision.get("reason") != gate_reason:
        return False

    delivery_result = _result_delivery_summary(result.delivery_result)
    if (
        delivery_status is not None
        and _nested_delivery_value(delivery_result, "status") != delivery_status
    ):
        return False
    if (
        delivery_reason is not None
        and _nested_delivery_value(delivery_result, "reason") != delivery_reason
    ):
        return False
    return not (
        endpoint_id is not None
        and _nested_delivery_value(delivery_result, "endpoint_id") != endpoint_id
    )


def _nested_delivery_value(
    delivery_result: dict[str, object] | None,
    field_name: str,
) -> object | None:
    if delivery_result is None:
        return None
    return delivery_result.get(field_name)


def _result_gate_decision_summary(
    gate_decision: EncryptedDeliveryGateDecision | dict[str, Any],
) -> dict[str, object]:
    if isinstance(gate_decision, EncryptedDeliveryGateDecision):
        return gate_decision.to_summary()
    if isinstance(gate_decision, dict):
        return dict(gate_decision)
    raise TypeError("result gate_decision must be a gate decision or dict")


def _result_delivery_summary(
    delivery_result: MessageDeliveryResult | dict[str, Any] | None,
) -> dict[str, object] | None:
    if delivery_result is None:
        return None
    if isinstance(delivery_result, MessageDeliveryResult):
        return delivery_result.to_summary()
    if isinstance(delivery_result, dict):
        return dict(delivery_result)
    raise TypeError("result delivery_result must be a delivery result, dict, or None")


def _result_retained(result: EncryptedDeliveryResult) -> bool:
    metadata = result.metadata if isinstance(result.metadata, dict) else {}
    return metadata.get("retained_in_registry_hub") is True


def _lane_signature_key(lane_signature: LaneSignature | str | None) -> str | None:
    if lane_signature is None:
        return None
    if isinstance(lane_signature, LaneSignature):
        return lane_signature.signature
    if isinstance(lane_signature, str):
        return parse_lane_signature(lane_signature).signature
    raise TypeError("lane_signature must be a LaneSignature, string, or None")


def _validate_optional_string(value: str | None, field_name: str) -> None:
    if value is None:
        return
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string or None")
    if not value:
        raise ValueError(f"{field_name} must not be empty")


def _validate_optional_bool(value: bool | None, field_name: str) -> None:
    if value is None:
        return
    if not isinstance(value, bool):
        raise TypeError(f"{field_name} must be a boolean or None")


__all__ = [
    "build_encrypted_delivery_audit_entry",
    "evaluate_encrypted_delivery_request",
    "query_encrypted_delivery_results",
    "summarize_encrypted_delivery_result",
]
