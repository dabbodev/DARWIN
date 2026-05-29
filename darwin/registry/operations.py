"""Registry operation placeholders."""

from __future__ import annotations

from darwin.auth.trust import verify_auth_state, verify_passport
from darwin.models.device import Device
from darwin.models.hub import AttachmentRecord, ConflictRecord, LocalDeviceRecord, RegistryHub
from darwin.models.passport import PassportRecord
from darwin.models.security import AuthState, SecurityEvent, TrustCheckResult
from darwin.registry.metrics import (
    record_label_conflict,
    record_registry_lookup,
    refresh_registry_counts,
)


def assign_temp_label(requested_label: str, device_id: str) -> str:
    """Return the default conflict label for a duplicate local label."""
    return f"{requested_label}_temp_{device_id[-4:]}"


def register_device(
    hub: RegistryHub,
    device: Device,
    requested_label: str | None = None,
    checkpoint_tier: int | None = None,
    passport: PassportRecord | None = None,
    auth_state: AuthState | None = None,
    current_time: int | None = None,
) -> LocalDeviceRecord | TrustCheckResult:
    """Register or update a device in a RegistryHub scope."""
    if auth_state is not None:
        auth_result = verify_auth_state(
            auth_state,
            claimed_device_id=device.device_id,
            hub_id=hub.hub_id,
            timestamp=current_time,
        )
        if not auth_result.success:
            if auth_result.security_event is not None:
                hub.security_events.append(auth_result.security_event)
            return auth_result

    if passport is not None:
        passport_result = verify_passport(passport, hub.hub_id, timestamp=current_time)
        if not passport_result.success:
            if passport_result.security_event is not None:
                hub.security_events.append(passport_result.security_event)
            return passport_result

        if passport.device_id != device.device_id:
            event = SecurityEvent(
                event_type="passport_verification_failed",
                claimed_device_id=device.device_id,
                hub_id=hub.hub_id,
                severity="high",
                action_taken="registration_rejected",
                timestamp=current_time,
                reason="passport_device_id_mismatch",
            )
            hub.security_events.append(event)
            return TrustCheckResult(
                action="registration_rejected",
                success=False,
                claimed_device_id=device.device_id,
                reason="passport_device_id_mismatch",
                security_event=event,
            )

    claim_label = requested_label or device.label
    tier = checkpoint_tier if checkpoint_tier is not None else device.checkpoint_tier
    assigned_label = _assign_available_label(hub, claim_label, device.device_id)

    existing_record = hub.devices.get(device.device_id)
    if (
        existing_record
        and existing_record.current_label != assigned_label
        and hub.labels.get(existing_record.current_label) == device.device_id
    ):
        del hub.labels[existing_record.current_label]

    existing_device_id = hub.labels.get(claim_label)
    if existing_device_id is not None and existing_device_id != device.device_id:
        _record_label_conflict(
            hub=hub,
            requested_label=claim_label,
            existing_device_id=existing_device_id,
            requesting_device_id=device.device_id,
            assigned_temp_label=assigned_label,
        )

    passport_id = passport.passport_id if passport is not None else device.passport_id
    passport_id = passport_id or f"passport_{device.device_id}"
    passport_record = passport or PassportRecord(
        passport_id=passport_id,
        device_id=device.device_id,
        issued_by=hub.hub_id,
        issued_scope=hub.scope_path,
    )
    identity_chain = hub.identity_chain_for(assigned_label)
    record = LocalDeviceRecord(
        device_id=device.device_id,
        requested_label=claim_label,
        current_label=assigned_label,
        identity_chain=identity_chain,
        passport_id=passport_id,
        current_attachment=hub.hub_id,
        current_state="online",
        checkpoint_tier=tier,
    )
    attachment = AttachmentRecord(
        device_id=device.device_id,
        current_attachment=hub.hub_id,
        current_scope=hub.scope_path,
        state="online",
        traffic_hint=f"{hub.hub_id}.local_link",
    )

    hub.devices[device.device_id] = record
    hub.labels[assigned_label] = device.device_id
    hub.passports[passport_id] = passport_record
    hub.attachments[device.device_id] = attachment

    device.label = assigned_label
    device.passport_id = passport_id
    device.current_registry_hub = hub.hub_id
    device.state = "online"
    device.checkpoint_tier = tier
    refresh_registry_counts(hub)

    return record


def resolve_label(hub: RegistryHub, label: str) -> LocalDeviceRecord | None:
    """Resolve a local label to registry information if known."""
    device_id = hub.labels.get(label)
    if device_id is None:
        record_registry_lookup(hub, found=False)
        return None
    record = hub.devices.get(device_id)
    record_registry_lookup(hub, found=record is not None)
    return record


def resolve_device_id(hub: RegistryHub, device_id: str) -> LocalDeviceRecord | None:
    """Resolve a durable device ID to registry information if known."""
    record = hub.devices.get(device_id)
    record_registry_lookup(hub, found=record is not None)
    return record


def _assign_available_label(hub: RegistryHub, requested_label: str, device_id: str) -> str:
    existing_device_id = hub.labels.get(requested_label)
    if existing_device_id is None or existing_device_id == device_id:
        return requested_label

    temp_label = assign_temp_label(requested_label, device_id)
    if hub.labels.get(temp_label) in (None, device_id):
        return temp_label

    suffix = 2
    while hub.labels.get(f"{temp_label}_{suffix}") not in (None, device_id):
        suffix += 1
    return f"{temp_label}_{suffix}"


def _record_label_conflict(
    hub: RegistryHub,
    requested_label: str,
    existing_device_id: str,
    requesting_device_id: str,
    assigned_temp_label: str,
) -> None:
    conflict_id = f"label_conflict:{requested_label}:{requesting_device_id}"
    hub.conflicts[conflict_id] = ConflictRecord(
        conflict_id=conflict_id,
        conflict_type="label_conflict",
        requested_label=requested_label,
        existing_device_id=existing_device_id,
        requesting_device_id=requesting_device_id,
        assigned_temp_label=assigned_temp_label,
    )
    record_label_conflict(hub)
