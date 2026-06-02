"""Registry-owned symbolic relocation operations."""

from __future__ import annotations

from darwin.auth.modes import AUTH_MODE_HMAC_SHA256_EXPERIMENTAL, AUTH_MODE_SYMBOLIC
from darwin.auth.move_contract import verify_move_contract_auth
from darwin.models.hub import AttachmentRecord, RegistryHub
from darwin.models.move import (
    MarkInTransitResult,
    MoveContract,
    MoveVerificationResult,
    RelocationRecord,
)
from darwin.registry.metrics import record_move_contract, refresh_registry_counts


def mark_in_transit(
    registry_hub: RegistryHub,
    device_id: str,
    current_time: int | None = None,
) -> MarkInTransitResult:
    """Mark a registered device as explicitly relocating."""
    device_record = registry_hub.devices.get(device_id)
    if device_record is None:
        return MarkInTransitResult(
            action="device_not_found",
            device_id=device_id,
            reason="unknown_device",
        )

    device_record.current_state = "in_transit"

    checkpoint = registry_hub.checkpoints.get(device_id)
    if checkpoint is not None:
        checkpoint.state = "in_transit"

    attachment = registry_hub.attachments.get(device_id)
    if attachment is not None:
        attachment.state = "in_transit"
        attachment.attachment_type = "in_transit"

    relocation = RelocationRecord(
        device_id=device_id,
        state="in_transit",
        old_attachment=device_record.current_attachment,
        from_scope=registry_hub.scope_path,
        started_at=current_time,
        updated_at=current_time,
    )
    registry_hub.relocations[device_id] = relocation
    refresh_registry_counts(registry_hub)

    return MarkInTransitResult(
        action="marked_in_transit",
        device_id=device_id,
        device=device_record,
        attachment=attachment,
        checkpoint=checkpoint,
        relocation=relocation,
    )


def create_move_contract(
    device_id: str,
    passport_id: str,
    from_scope: str,
    to_scope: str,
    old_attachment: str,
    new_attachment: str,
    valid: bool = True,
    timestamp: int | None = None,
) -> MoveContract:
    """Create a symbolic move contract without cryptographic verification."""
    return MoveContract(
        move_id=f"move_{device_id}_{new_attachment}",
        passport_id=passport_id,
        device_id=device_id,
        from_scope=from_scope,
        to_scope=to_scope,
        old_attachment=old_attachment,
        new_attachment=new_attachment,
        valid=valid,
        timestamp=timestamp,
    )


def update_attachment_after_move(
    registry_hub: RegistryHub,
    device_id: str,
    new_attachment: str,
    new_scope: str,
    move_contract: MoveContract,
) -> MoveVerificationResult:
    """Apply a valid move contract to registry attachment state."""
    device_record = registry_hub.devices.get(device_id)
    if device_record is None:
        return MoveVerificationResult(
            action="device_not_found",
            device_id=device_id,
            move_contract=move_contract,
            reason="unknown_device",
        )

    validation_failure = _move_contract_failure_reason(
        device_record.passport_id,
        device_id,
        move_contract,
    )
    if validation_failure is not None:
        return MoveVerificationResult(
            action="move_contract_rejected",
            device_id=device_id,
            move_contract=move_contract,
            attachment=registry_hub.attachments.get(device_id),
            reason=validation_failure,
        )

    auth_mode = move_contract.auth_mode or AUTH_MODE_SYMBOLIC
    if auth_mode == AUTH_MODE_HMAC_SHA256_EXPERIMENTAL:
        hmac_target_failure = _hmac_move_target_failure_reason(
            registry_hub,
            device_record.current_attachment,
            new_attachment,
            new_scope,
            move_contract,
        )
        if hmac_target_failure is not None:
            return MoveVerificationResult(
                action="move_contract_rejected",
                device_id=device_id,
                move_contract=move_contract,
                attachment=registry_hub.attachments.get(device_id),
                reason=hmac_target_failure,
            )

        auth_result = verify_move_contract_auth(registry_hub, move_contract)
        if not auth_result.success:
            return MoveVerificationResult(
                action="move_contract_rejected",
                device_id=device_id,
                move_contract=move_contract,
                attachment=registry_hub.attachments.get(device_id),
                reason=auth_result.reason,
            )

    device_record.current_attachment = new_attachment
    device_record.current_state = "online"

    attachment = registry_hub.attachments.get(device_id)
    if attachment is None:
        attachment = AttachmentRecord(
            device_id=device_id,
            current_attachment=new_attachment,
            current_scope=new_scope,
            state="online",
        )
        registry_hub.attachments[device_id] = attachment
    else:
        attachment.current_attachment = new_attachment
        attachment.current_scope = new_scope
        attachment.state = "online"
        attachment.attachment_type = "direct_child"
        attachment.traffic_hint = f"{new_attachment}.local_link"

    checkpoint = registry_hub.checkpoints.get(device_id)
    if checkpoint is not None:
        checkpoint.state = "online"

    registry_hub.moves.setdefault(device_id, []).append(move_contract)
    registry_hub.relocations[device_id] = RelocationRecord(
        device_id=device_id,
        state="resumed",
        old_attachment=move_contract.old_attachment,
        new_attachment=new_attachment,
        from_scope=move_contract.from_scope,
        to_scope=new_scope,
        started_at=move_contract.timestamp,
        updated_at=move_contract.timestamp,
    )
    record_move_contract(registry_hub)

    return MoveVerificationResult(
        action="attachment_updated",
        device_id=device_id,
        move_contract=move_contract,
        attachment=attachment,
    )


def get_latest_move(registry_hub: RegistryHub, device_id: str) -> MoveContract | None:
    """Return the latest recorded symbolic move contract for a device."""
    moves = registry_hub.moves.get(device_id, [])
    if not moves:
        return None
    return moves[-1]


def _move_contract_failure_reason(
    passport_id: str,
    device_id: str,
    move_contract: MoveContract,
) -> str | None:
    if not move_contract.valid:
        return "invalid_move_contract"
    if move_contract.device_id != device_id:
        return "device_id_mismatch"
    if move_contract.passport_id != passport_id:
        return "passport_id_mismatch"
    return None


def _hmac_move_target_failure_reason(
    registry_hub: RegistryHub,
    current_attachment: str,
    new_attachment: str,
    new_scope: str,
    move_contract: MoveContract,
) -> str | None:
    if move_contract.from_scope != registry_hub.scope_path:
        return "invalid_move_auth_tag"
    if move_contract.old_attachment != current_attachment:
        return "invalid_move_auth_tag"
    if move_contract.to_scope != new_scope:
        return "invalid_move_auth_tag"
    if move_contract.new_attachment != new_attachment:
        return "invalid_move_auth_tag"
    return None
