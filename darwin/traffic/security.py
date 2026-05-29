"""Traffic-owned symbolic packet trust handling."""

from __future__ import annotations

from darwin.models.hub import TrafficHub
from darwin.models.packet import DarwinPacket
from darwin.models.security import PacketAuthResult, QuarantineRecord, SecurityEvent
from darwin.traffic.metrics import record_invalid_packet_auth


def log_security_event(
    traffic_hub: TrafficHub,
    event_type: str,
    claimed_device_id: str | None,
    severity: str,
    action_taken: str,
    reason: str | None = None,
    timestamp: int | None = None,
) -> SecurityEvent:
    """Append a deterministic security event to a TrafficHub."""
    event = SecurityEvent(
        event_type=event_type,
        claimed_device_id=claimed_device_id,
        hub_id=traffic_hub.hub_id,
        severity=severity,
        action_taken=action_taken,
        timestamp=timestamp,
        reason=reason,
    )
    traffic_hub.security_events.append(event)
    return event


def verify_packet_auth(
    traffic_hub: TrafficHub,
    packet: DarwinPacket,
    current_time: int | None = None,
) -> PacketAuthResult:
    """Validate a packet's symbolic auth tag before delivery."""
    claimed_device_id = packet.source_device_id
    if packet.auth_tag_valid:
        return PacketAuthResult(
            action="packet_auth_verified",
            packet_id=packet.packet_id,
            success=True,
            claimed_device_id=claimed_device_id,
        )
    record_invalid_packet_auth(traffic_hub)

    quarantine: QuarantineRecord | None = None
    if claimed_device_id is not None:
        quarantine = QuarantineRecord(
            claimed_device_id=claimed_device_id,
            reason="invalid_auth_tag",
            source_hub_id=packet.source_hub_id or traffic_hub.hub_id,
            created_at=current_time,
        )
        traffic_hub.quarantines[claimed_device_id] = quarantine
        attachment = traffic_hub.direct_attachments.get(claimed_device_id)
        if attachment is not None:
            attachment.status = "quarantined"

    event = log_security_event(
        traffic_hub=traffic_hub,
        event_type="packet_auth_failed",
        claimed_device_id=claimed_device_id,
        severity="high",
        action_taken="packet_rejected",
        reason="invalid_auth_tag",
        timestamp=current_time,
    )
    return PacketAuthResult(
        action="invalid_auth_tag",
        packet_id=packet.packet_id,
        success=False,
        claimed_device_id=claimed_device_id,
        security_event=event,
        quarantine=quarantine,
        reason="invalid_auth_tag",
    )


def is_quarantined_for_normal_traffic(traffic_hub: TrafficHub, device_id: str | None) -> bool:
    """Return whether a local direct attachment is blocked for normal traffic."""
    if device_id is None:
        return False
    attachment = traffic_hub.direct_attachments.get(device_id)
    return attachment is not None and attachment.status == "quarantined"
