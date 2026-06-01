"""Registry-owned symbolic trust failure handling."""

from __future__ import annotations

from darwin.auth.hmac_bridge import (
    verify_rolling_proof_tag,
)
from darwin.auth.modes import AUTH_MODE_HMAC_SHA256_EXPERIMENTAL, AUTH_MODE_SYMBOLIC
from darwin.models.hub import ConflictRecord, RegistryHub
from darwin.models.security import (
    DuplicateIdentityConflict,
    QuarantineRecord,
    QuarantineResult,
    RollingProofResult,
    SecurityEvent,
)
from darwin.registry.metrics import record_duplicate_device_conflict, refresh_registry_counts
from darwin.registry.relocation import get_latest_move


def log_security_event(
    registry_hub: RegistryHub,
    event_type: str,
    claimed_device_id: str | None,
    severity: str,
    action_taken: str,
    reason: str | None = None,
    timestamp: int | None = None,
) -> SecurityEvent:
    """Append a deterministic security event to a RegistryHub."""
    event = SecurityEvent(
        event_type=event_type,
        claimed_device_id=claimed_device_id,
        hub_id=registry_hub.hub_id,
        severity=severity,
        action_taken=action_taken,
        timestamp=timestamp,
        reason=reason,
    )
    registry_hub.security_events.append(event)
    return event


def quarantine_device(
    registry_hub: RegistryHub,
    claimed_device_id: str,
    reason: str,
    source_hub_id: str | None = None,
    current_time: int | None = None,
    event_type: str = "device_quarantined",
) -> QuarantineResult:
    """Create or refresh symbolic quarantine state for a claimed device ID."""
    record = QuarantineRecord(
        claimed_device_id=claimed_device_id,
        reason=reason,
        source_hub_id=source_hub_id,
        created_at=current_time,
    )
    registry_hub.quarantines[claimed_device_id] = record

    device = registry_hub.devices.get(claimed_device_id)
    if device is not None:
        device.current_state = "quarantined"

    checkpoint = registry_hub.checkpoints.get(claimed_device_id)
    if checkpoint is not None:
        checkpoint.state = "quarantined"

    attachment = registry_hub.attachments.get(claimed_device_id)
    if attachment is not None:
        attachment.state = "quarantined"
    refresh_registry_counts(registry_hub)

    event = log_security_event(
        registry_hub=registry_hub,
        event_type=event_type,
        claimed_device_id=claimed_device_id,
        severity="high",
        action_taken="quarantined",
        reason=reason,
        timestamp=current_time,
    )
    return QuarantineResult(
        action="quarantined",
        claimed_device_id=claimed_device_id,
        record=record,
        security_event=event,
    )


def verify_rolling_proof(
    registry_hub: RegistryHub,
    device_id: str,
    proof_valid: bool,
    source_hub_id: str | None = None,
    current_time: int | None = None,
    auth_mode: str = AUTH_MODE_SYMBOLIC,
    auth_secret: str | bytes | None = None,
    auth_tag: str | None = None,
    session_id: str | None = None,
    counter: int | None = None,
    nonce: str | None = None,
    capability: str | None = None,
) -> RollingProofResult:
    """Check same-network continuity and quarantine on failure."""
    if auth_mode == AUTH_MODE_HMAC_SHA256_EXPERIMENTAL:
        proof_valid = _hmac_rolling_proof_valid(
            registry_hub=registry_hub,
            device_id=device_id,
            auth_secret=auth_secret,
            auth_tag=auth_tag,
            session_id=session_id,
            counter=counter,
            nonce=nonce,
            capability=capability,
        )

    if proof_valid:
        return RollingProofResult(
            action="rolling_proof_verified",
            device_id=device_id,
            success=True,
        )

    quarantine = quarantine_device(
        registry_hub=registry_hub,
        claimed_device_id=device_id,
        reason="rolling_proof_failed",
        source_hub_id=source_hub_id,
        current_time=current_time,
        event_type="rolling_proof_failed",
    )
    return RollingProofResult(
        action="quarantined",
        device_id=device_id,
        success=False,
        quarantine=quarantine.record,
        security_event=quarantine.security_event,
        reason="rolling_proof_failed",
    )


def _hmac_rolling_proof_valid(
    *,
    registry_hub: RegistryHub,
    device_id: str,
    auth_secret: str | bytes | None,
    auth_tag: str | None,
    session_id: str | None,
    counter: int | None,
    nonce: str | None,
    capability: str | None,
) -> bool:
    if (
        auth_secret is None
        or auth_tag is None
        or session_id is None
        or counter is None
        or nonce is None
        or capability is None
    ):
        return False
    result = verify_rolling_proof_tag(
        auth_secret,
        device_id=device_id,
        hub_id=registry_hub.hub_id,
        session_id=session_id,
        counter=counter,
        nonce=nonce,
        capability=capability,
        expected_tag=auth_tag,
    )
    return result.success


def detect_duplicate_device_claim(
    registry_hub: RegistryHub,
    device_id: str,
    claiming_attachment_id: str | None = None,
    claiming_hub_ids: list[str] | None = None,
    current_time: int | None = None,
) -> DuplicateIdentityConflict:
    """Detect duplicate active durable-ID claims without overwriting trusted state."""
    device = registry_hub.devices.get(device_id)
    if device is None:
        return DuplicateIdentityConflict(
            action="device_not_found",
            device_id=device_id,
            reason="unknown_device",
        )

    claiming_attachment = _claiming_attachment(claiming_attachment_id, claiming_hub_ids)
    existing_attachment = device.current_attachment
    if claiming_attachment is None or claiming_attachment == existing_attachment:
        return DuplicateIdentityConflict(
            action="no_conflict",
            device_id=device_id,
            existing_attachment=existing_attachment,
            claiming_attachment=claiming_attachment,
        )

    latest_move = get_latest_move(registry_hub, device_id)
    if (
        latest_move is not None
        and latest_move.valid
        and latest_move.new_attachment == claiming_attachment
    ):
        return DuplicateIdentityConflict(
            action="no_conflict",
            device_id=device_id,
            existing_attachment=existing_attachment,
            claiming_attachment=claiming_attachment,
        )

    conflict_id = f"duplicate_device_id:{device_id}:{claiming_attachment}"
    registry_hub.conflicts[conflict_id] = ConflictRecord(
        conflict_id=conflict_id,
        conflict_type="duplicate_device_id",
        requested_label=device_id,
        existing_device_id=device_id,
        requesting_device_id=device_id,
        assigned_temp_label=f"quarantine_{device_id}",
        status="quarantined",
    )
    record_duplicate_device_conflict(registry_hub)

    quarantine = QuarantineRecord(
        claimed_device_id=device_id,
        reason="duplicate_active_device_id",
        source_hub_id=claiming_attachment,
        created_at=current_time,
    )
    registry_hub.quarantines[f"{device_id}:{claiming_attachment}"] = quarantine
    event = log_security_event(
        registry_hub=registry_hub,
        event_type="duplicate_device_id_conflict",
        claimed_device_id=device_id,
        severity="critical",
        action_taken="duplicate_claim_quarantined",
        reason="duplicate_active_device_id",
        timestamp=current_time,
    )
    return DuplicateIdentityConflict(
        action="duplicate_device_id_conflict",
        device_id=device_id,
        existing_attachment=existing_attachment,
        claiming_attachment=claiming_attachment,
        conflict_id=conflict_id,
        quarantine=quarantine,
        security_event=event,
        reason="duplicate_active_device_id",
    )


def _claiming_attachment(
    claiming_attachment_id: str | None,
    claiming_hub_ids: list[str] | None,
) -> str | None:
    if claiming_attachment_id is not None:
        return claiming_attachment_id
    if claiming_hub_ids:
        return claiming_hub_ids[-1]
    return None
