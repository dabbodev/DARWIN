"""Registry-owned checkpoint operations."""

from __future__ import annotations

from darwin.auth.hmac_bridge import (
    checkpoint_auth_material,
    verify_hmac_tag,
)
from darwin.auth.modes import AUTH_MODE_HMAC_SHA256_EXPERIMENTAL, AUTH_MODE_SYMBOLIC
from darwin.models.checkpoint import (
    CHECKPOINT_STATES,
    CheckpointPacket,
    CheckpointRecordResult,
    CheckpointState,
    CheckpointTimeoutResult,
    checkpoint_policy_for_tier,
)
from darwin.models.hub import RegistryHub
from darwin.registry.metrics import record_checkpoint_update


def record_checkpoint(
    registry_hub: RegistryHub,
    checkpoint_packet: CheckpointPacket,
    auth_secret: str | bytes | None = None,
) -> CheckpointRecordResult:
    """Record a symbolic device checkpoint on a RegistryHub."""
    device_id = checkpoint_packet.source_device_id
    local_record = registry_hub.devices.get(device_id)

    if local_record is None:
        return CheckpointRecordResult(
            action="checkpoint_rejected",
            device_id=device_id,
            reason="unknown_device",
        )

    previous_checkpoint = registry_hub.checkpoints.get(device_id)
    if local_record.current_state in {"quarantined", "revoked"}:
        return CheckpointRecordResult(
            action="checkpoint_rejected",
            device_id=device_id,
            checkpoint=previous_checkpoint,
            reason=f"device_{local_record.current_state}",
        )

    if not _checkpoint_auth_valid(checkpoint_packet, auth_secret):
        return CheckpointRecordResult(
            action="checkpoint_rejected",
            device_id=device_id,
            checkpoint=previous_checkpoint,
            reason="invalid_auth_tag",
        )

    if checkpoint_packet.state not in CHECKPOINT_STATES:
        return CheckpointRecordResult(
            action="checkpoint_rejected",
            device_id=device_id,
            checkpoint=previous_checkpoint,
            reason="unknown_checkpoint_state",
        )

    tier = checkpoint_packet.checkpoint_tier
    interval = checkpoint_policy_for_tier(tier).interval
    checkpoint = CheckpointState(
        device_id=device_id,
        state=checkpoint_packet.state,
        checkpoint_tier=tier,
        last_checkpoint_at=checkpoint_packet.created_at,
        expected_next_checkpoint_at=checkpoint_packet.created_at + interval,
        active_lane_count=checkpoint_packet.active_lane_count,
        battery_level=checkpoint_packet.battery_level,
        auth_valid=True,
    )
    registry_hub.checkpoints[device_id] = checkpoint
    local_record.current_state = checkpoint.state

    attachment = registry_hub.attachments.get(device_id)
    if attachment is not None:
        attachment.state = checkpoint.state
    record_checkpoint_update(registry_hub)

    return CheckpointRecordResult(
        action="checkpoint_recorded",
        device_id=device_id,
        checkpoint=checkpoint,
    )


def _checkpoint_auth_valid(
    checkpoint_packet: CheckpointPacket,
    auth_secret: str | bytes | None,
) -> bool:
    auth_mode = checkpoint_packet.auth_mode or AUTH_MODE_SYMBOLIC
    if auth_mode == AUTH_MODE_SYMBOLIC:
        return checkpoint_packet.auth_tag_valid
    if auth_mode == AUTH_MODE_HMAC_SHA256_EXPERIMENTAL:
        if auth_secret is None or checkpoint_packet.auth_tag is None:
            return False
        return verify_hmac_tag(
            auth_secret,
            checkpoint_auth_material(checkpoint_packet),
            checkpoint_packet.auth_tag,
        )
    return False


def get_checkpoint_state(registry_hub: RegistryHub, device_id: str) -> CheckpointState | None:
    """Return the checkpoint state for a registered device, if one exists."""
    return registry_hub.checkpoints.get(device_id)


def detect_checkpoint_timeouts(
    registry_hub: RegistryHub,
    current_time: int,
) -> list[CheckpointTimeoutResult]:
    """Mark checkpoint records as timed out when simulated time exceeds policy."""
    results: list[CheckpointTimeoutResult] = []

    for device_id, checkpoint in sorted(registry_hub.checkpoints.items()):
        policy = checkpoint_policy_for_tier(checkpoint.checkpoint_tier)
        timeout_after = checkpoint.expected_next_checkpoint_at + policy.timeout_grace

        if current_time > timeout_after and checkpoint.state != "timed_out":
            checkpoint.state = "timed_out"
            checkpoint.missed_checkpoint_count += 1
            local_record = registry_hub.devices.get(device_id)
            if local_record is not None:
                local_record.current_state = "timed_out"
            attachment = registry_hub.attachments.get(device_id)
            if attachment is not None:
                attachment.state = "timed_out"
            results.append(
                CheckpointTimeoutResult(
                    device_id=device_id,
                    action="checkpoint_timed_out",
                    state=checkpoint.state,
                    expected_next_checkpoint_at=checkpoint.expected_next_checkpoint_at,
                    checked_at=current_time,
                    timed_out=True,
                )
            )
            continue

        results.append(
            CheckpointTimeoutResult(
                device_id=device_id,
                action="checkpoint_ok",
                state=checkpoint.state,
                expected_next_checkpoint_at=checkpoint.expected_next_checkpoint_at,
                checked_at=current_time,
            )
        )

    return results
