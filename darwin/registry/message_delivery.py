"""Simulator-local in-memory mailbox delivery helpers."""

from __future__ import annotations

from darwin.models.adapter_endpoint import AdapterEndpoint
from darwin.models.hub import RegistryHub
from darwin.models.lane_signature import LaneSignature, parse_lane_signature
from darwin.models.mailbox import MailboxCapability
from darwin.models.message import (
    MessageDeliveryFailureReason,
    MessageDeliveryResult,
    MessageDeliveryStatus,
    MessageEnvelope,
)
from darwin.registry.adapter_endpoints import list_adapter_endpoints
from darwin.registry.lane_registry import get_lane_definition
from darwin.registry.mailbox_registry import resolve_mailbox_address


def deliver_message_to_mailbox(
    registry_hub: RegistryHub,
    message_envelope: MessageEnvelope,
) -> MessageDeliveryResult:
    """Resolve and deliver one envelope to a RegistryHub-local in-memory inbox."""
    if not isinstance(message_envelope, MessageEnvelope):
        raise TypeError("message_envelope must be a MessageEnvelope")

    audit_path = ["parsed_recipient_address"]
    lane_signature = _lane_signature_key(message_envelope.lane_signature)
    mailbox = resolve_mailbox_address(registry_hub, message_envelope.recipient_address)
    lane_definition = get_lane_definition(registry_hub, lane_signature)

    if lane_definition is None:
        return _retain_result(
            registry_hub,
            message_envelope,
            status="rejected",
            reason="lane_not_registered",
            audit_path=(
                *audit_path,
                f"missing_lane_definition:{lane_signature}",
            ),
            fallback_action="reject",
            metadata={
                "simulator_local": True,
                "limitation": "no registered fallback policy exists for this lane",
            },
        )

    audit_path.append(f"resolved_lane:{lane_signature}")

    if not _payload_kind_matches(
        lane_payload_kind=lane_definition.payload_kind,
        envelope_payload_kind=message_envelope.payload_kind,
    ):
        return _retain_result(
            registry_hub,
            message_envelope,
            status="rejected",
            reason="payload_kind_mismatch",
            fallback_action="reject",
            audit_path=(
                *audit_path,
                f"payload_kind_mismatch:{message_envelope.payload_kind}",
            ),
            metadata={"lane_payload_kind": lane_definition.payload_kind},
        )

    if mailbox is None:
        fallback_action = lane_definition.fallback_policy.unknown_recipient
        return _retain_result(
            registry_hub,
            message_envelope,
            status=_status_from_fallback_action(fallback_action),
            reason="mailbox_not_found",
            fallback_action=fallback_action,
            audit_path=(
                *audit_path,
                f"mailbox_not_found:{message_envelope.recipient_address}",
            ),
        )

    audit_path.append(f"resolved_mailbox:{mailbox.mailbox_id}")

    device_state = _target_device_state(registry_hub, mailbox.canonical_device_id)
    if device_state == "quarantined":
        fallback_action = lane_definition.fallback_policy.quarantined
        return _retain_result(
            registry_hub,
            message_envelope,
            resolved_mailbox_id=mailbox.mailbox_id,
            target_device_id=mailbox.canonical_device_id,
            status=_status_from_fallback_action(fallback_action),
            reason="recipient_quarantined",
            fallback_action=fallback_action,
            audit_path=(
                *audit_path,
                f"target_device_state:{device_state}",
            ),
        )

    if device_state == "in_transit":
        fallback_action = lane_definition.fallback_policy.in_transit
        return _retain_result(
            registry_hub,
            message_envelope,
            resolved_mailbox_id=mailbox.mailbox_id,
            target_device_id=mailbox.canonical_device_id,
            status=_status_from_fallback_action(fallback_action),
            reason="device_in_transit",
            fallback_action=fallback_action,
            audit_path=(
                *audit_path,
                f"target_device_state:{device_state}",
            ),
            metadata={"queued_message": False, "background_retry": False},
        )

    capability_status = _mailbox_capability_status(
        mailbox.capabilities,
        lane_signature,
    )
    if capability_status == "missing":
        fallback_action = lane_definition.fallback_policy.missing_lane_capability
        return _retain_result(
            registry_hub,
            message_envelope,
            resolved_mailbox_id=mailbox.mailbox_id,
            target_device_id=mailbox.canonical_device_id,
            status=_status_from_fallback_action(fallback_action),
            reason="mailbox_missing_capability",
            fallback_action=fallback_action,
            audit_path=(
                *audit_path,
                f"mailbox_missing_capability:{lane_signature}",
            ),
        )

    if capability_status == "disabled":
        fallback_action = lane_definition.fallback_policy.missing_lane_capability
        return _retain_result(
            registry_hub,
            message_envelope,
            resolved_mailbox_id=mailbox.mailbox_id,
            target_device_id=mailbox.canonical_device_id,
            status=_status_from_fallback_action(fallback_action),
            reason="capability_disabled",
            fallback_action=fallback_action,
            audit_path=(
                *audit_path,
                f"capability_disabled:{lane_signature}",
            ),
        )

    audit_path.append(f"verified_mailbox_capability:{lane_signature}")

    endpoint_result = _select_in_memory_endpoint(
        registry_hub,
        mailbox.mailbox_id,
        lane_signature,
    )
    if endpoint_result.reason is not None:
        fallback_action = lane_definition.fallback_policy.adapter_unavailable
        return _retain_result(
            registry_hub,
            message_envelope,
            resolved_mailbox_id=mailbox.mailbox_id,
            target_device_id=mailbox.canonical_device_id,
            endpoint_id=endpoint_result.endpoint_id,
            status=_status_from_fallback_action(fallback_action),
            reason=endpoint_result.reason,
            fallback_action=fallback_action,
            audit_path=(
                *audit_path,
                *endpoint_result.audit_path,
            ),
            metadata={"queued_message": False, "background_retry": False},
        )

    endpoint = endpoint_result.endpoint
    if endpoint is None:
        raise AssertionError("endpoint selection returned no endpoint or reason")

    registry_hub.message_inboxes.setdefault(mailbox.mailbox_id, []).append(
        message_envelope
    )
    return _retain_result(
        registry_hub,
        message_envelope,
        resolved_mailbox_id=mailbox.mailbox_id,
        target_device_id=mailbox.canonical_device_id,
        endpoint_id=endpoint.endpoint_id,
        status="delivered",
        reason=None,
        fallback_action=None,
        audit_path=(
            *audit_path,
            f"selected_endpoint:{endpoint.endpoint_id}",
            f"delivered_to_in_memory_inbox:{mailbox.mailbox_id}",
        ),
        metadata={"simulator_local": True, "durable_storage": False},
    )


def get_mailbox_inbox(
    registry_hub: RegistryHub,
    mailbox_id: str,
) -> list[MessageEnvelope]:
    """Return a copy of the RegistryHub-local inbox for a mailbox."""
    _validate_required_string(mailbox_id, "mailbox_id")
    return list(registry_hub.message_inboxes.get(mailbox_id, []))


def list_message_delivery_results(
    registry_hub: RegistryHub,
    *,
    message_id: str | None = None,
    recipient_address: str | None = None,
    mailbox_id: str | None = None,
    status: MessageDeliveryStatus | str | None = None,
    reason: MessageDeliveryFailureReason | str | None = None,
    lane_signature: LaneSignature | str | None = None,
) -> list[MessageDeliveryResult]:
    """Return retained message delivery results in deterministic append order."""
    _validate_optional_string(message_id, "message_id")
    _validate_optional_string(recipient_address, "recipient_address")
    _validate_optional_string(mailbox_id, "mailbox_id")
    status_key = _status_key(status)
    reason_key = _reason_key(reason)
    lane_signature_key = _optional_lane_signature_key(lane_signature)

    return [
        result
        for result in registry_hub.message_delivery_results
        if (message_id is None or result.message_id == message_id)
        and (recipient_address is None or result.recipient_address == recipient_address)
        and (mailbox_id is None or result.resolved_mailbox_id == mailbox_id)
        and (status_key is None or result.status.status == status_key)
        and (
            reason_key is None
            or (
                result.reason is not None
                and result.reason.reason == reason_key
            )
        )
        and (
            lane_signature_key is None
            or result.lane_signature == lane_signature_key
        )
    ]


class _EndpointSelectionResult:
    def __init__(
        self,
        *,
        endpoint: AdapterEndpoint | None = None,
        reason: str | None = None,
        endpoint_id: str | None = None,
        audit_path: tuple[str, ...] = (),
    ) -> None:
        self.endpoint = endpoint
        self.reason = reason
        self.endpoint_id = endpoint_id
        self.audit_path = audit_path


def _select_in_memory_endpoint(
    registry_hub: RegistryHub,
    mailbox_id: str,
    lane_signature: str,
) -> _EndpointSelectionResult:
    mailbox_endpoints = list_adapter_endpoints(
        registry_hub,
        subject_id=mailbox_id,
        subject_kind="mailbox",
        adapter_kind="in_memory",
    )
    if not mailbox_endpoints:
        return _EndpointSelectionResult(
            reason="endpoint_not_found",
            audit_path=("in_memory_endpoint_not_found",),
        )

    lane_endpoints = [
        endpoint
        for endpoint in mailbox_endpoints
        if lane_signature in endpoint.lane_signatures
    ]
    if not lane_endpoints:
        return _EndpointSelectionResult(
            reason="endpoint_lane_mismatch",
            endpoint_id=mailbox_endpoints[0].endpoint_id,
            audit_path=(f"endpoint_lane_mismatch:{lane_signature}",),
        )

    available = [
        endpoint
        for endpoint in lane_endpoints
        if endpoint.status.status == "available"
    ]
    if available:
        return _EndpointSelectionResult(endpoint=available[0])

    endpoint = lane_endpoints[0]
    return _EndpointSelectionResult(
        reason="endpoint_unavailable",
        endpoint_id=endpoint.endpoint_id,
        audit_path=(f"endpoint_unavailable:{endpoint.status.status}",),
    )


def _retain_result(
    registry_hub: RegistryHub,
    message_envelope: MessageEnvelope,
    *,
    status: str,
    reason: str | None,
    audit_path: tuple[str, ...] | list[str],
    resolved_mailbox_id: str | None = None,
    target_device_id: str | None = None,
    endpoint_id: str | None = None,
    fallback_action: str | None = None,
    metadata: dict[str, object] | None = None,
) -> MessageDeliveryResult:
    result_metadata = {
        "simulator_local": True,
        "networking": False,
        "dns_lookup": False,
        "traffic_hub_routing": False,
        "durable_queue": False,
    }
    if metadata:
        result_metadata.update(metadata)
    result = MessageDeliveryResult(
        message_id=message_envelope.message_id,
        recipient_address=message_envelope.recipient_address,
        resolved_mailbox_id=resolved_mailbox_id,
        target_device_id=target_device_id,
        lane_signature=message_envelope.lane_signature,
        endpoint_id=endpoint_id,
        status=status,
        reason=reason,
        fallback_action=fallback_action,
        audit_path=audit_path,
        metadata=result_metadata,
    )
    registry_hub.message_delivery_results.append(result)
    return result


def _payload_kind_matches(
    *,
    lane_payload_kind: str,
    envelope_payload_kind: str,
) -> bool:
    if lane_payload_kind == "symbolic_message_envelope":
        return True
    return lane_payload_kind == envelope_payload_kind


def _mailbox_capability_status(
    capabilities: tuple[MailboxCapability, ...],
    lane_signature: str,
) -> str:
    matches = [
        capability
        for capability in capabilities
        if capability.lane_signature == lane_signature
    ]
    if not matches:
        return "missing"
    if not any(capability.enabled for capability in matches):
        return "disabled"
    return "enabled"


def _target_device_state(registry_hub: RegistryHub, device_id: str) -> str | None:
    device = registry_hub.devices.get(device_id)
    if device is not None:
        return device.current_state
    checkpoint = registry_hub.checkpoints.get(device_id)
    if checkpoint is not None:
        return checkpoint.state
    attachment = registry_hub.attachments.get(device_id)
    if attachment is not None:
        return attachment.state
    return None


def _status_from_fallback_action(fallback_action: str) -> str:
    if fallback_action == "reject":
        return "rejected"
    if fallback_action == "bounce":
        return "bounced"
    if fallback_action in {"queue", "queue_with_expiry", "queue_with_retry"}:
        return "queued"
    if fallback_action in {
        "hold_until_relocation_resolves",
        "manual_resolution_required",
    }:
        return "held"
    return "failed"


def _status_key(status: MessageDeliveryStatus | str | None) -> str | None:
    if status is None:
        return None
    if isinstance(status, MessageDeliveryStatus):
        return status.status
    if isinstance(status, str):
        return MessageDeliveryStatus(status).status
    raise TypeError("status must be a MessageDeliveryStatus, string, or None")


def _reason_key(reason: MessageDeliveryFailureReason | str | None) -> str | None:
    if reason is None:
        return None
    if isinstance(reason, MessageDeliveryFailureReason):
        return reason.reason
    if isinstance(reason, str):
        return MessageDeliveryFailureReason(reason).reason
    raise TypeError(
        "reason must be a MessageDeliveryFailureReason, string, or None"
    )


def _lane_signature_key(lane_signature: LaneSignature | str) -> str:
    if isinstance(lane_signature, LaneSignature):
        return lane_signature.signature
    if isinstance(lane_signature, str):
        return parse_lane_signature(lane_signature).signature
    raise TypeError("lane_signature must be a LaneSignature or string")


def _optional_lane_signature_key(
    lane_signature: LaneSignature | str | None,
) -> str | None:
    if lane_signature is None:
        return None
    return _lane_signature_key(lane_signature)


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
