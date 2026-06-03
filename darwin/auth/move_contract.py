"""Experimental move-contract HMAC helpers for simulator-only auth tests.

This module binds deterministic move material to the v0.3 HMAC bridge. It is
not production cryptography and does not provide key exchange, signatures, or
secure storage.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from darwin.auth.hmac_bridge import compute_hmac_tag, verify_hmac_tag
from darwin.auth.modes import AUTH_MODE_HMAC_SHA256_EXPERIMENTAL, AUTH_MODE_SYMBOLIC
from darwin.models.move import MoveAuthVerificationResult
from darwin.registry.sessions import advance_session_counter, verify_session_counter

if TYPE_CHECKING:
    from darwin.models.hub import RegistryHub
    from darwin.models.move import MoveContract

REQUIRED_MOVE_AUTH_FIELDS = (
    "device_id",
    "passport_id",
    "from_scope",
    "to_scope",
    "old_attachment",
    "new_attachment",
    "move_nonce",
    "session_id",
    "move_counter",
)


@dataclass(frozen=True, slots=True)
class MoveAuthMaterial:
    """Plain simulator data covered by an experimental move HMAC tag."""

    device_id: str
    passport_id: str
    from_scope: str
    to_scope: str
    old_attachment: str
    new_attachment: str
    move_nonce: str
    session_id: str
    move_counter: int
    timestamp: int | None = None

    def to_dict(self) -> dict[str, object]:
        """Return deterministic move auth fields, omitting absent timestamp."""
        return build_move_auth_material(
            device_id=self.device_id,
            passport_id=self.passport_id,
            from_scope=self.from_scope,
            to_scope=self.to_scope,
            old_attachment=self.old_attachment,
            new_attachment=self.new_attachment,
            move_nonce=self.move_nonce,
            session_id=self.session_id,
            move_counter=self.move_counter,
            timestamp=self.timestamp,
        )


@dataclass(frozen=True, slots=True)
class MoveAuthResult:
    """Outcome shape for future move-contract auth integration tests."""

    success: bool
    status: str
    reason: str | None = None
    auth_mode: str = AUTH_MODE_HMAC_SHA256_EXPERIMENTAL
    expected_tag: str | None = None
    actual_tag: str | None = None


def build_move_auth_material(
    *,
    device_id: str,
    passport_id: str,
    from_scope: str,
    to_scope: str,
    old_attachment: str,
    new_attachment: str,
    move_nonce: str,
    session_id: str,
    move_counter: int,
    timestamp: int | None = None,
) -> dict[str, object]:
    """Return deterministic move fields covered by experimental HMAC auth."""
    material: dict[str, object] = {
        "device_id": device_id,
        "passport_id": passport_id,
        "from_scope": from_scope,
        "to_scope": to_scope,
        "old_attachment": old_attachment,
        "new_attachment": new_attachment,
        "move_nonce": move_nonce,
        "session_id": session_id,
        "move_counter": move_counter,
    }
    if timestamp is not None:
        material["timestamp"] = timestamp
    return _validate_move_auth_material(material)


def move_auth_material_from_contract(
    move_contract: object,
    session_id: str,
    move_nonce: str,
    move_counter: int,
    timestamp: int | None = None,
) -> dict[str, object]:
    """Build deterministic move auth material from an existing move contract."""
    resolved_timestamp = timestamp
    if resolved_timestamp is None:
        resolved_timestamp = getattr(move_contract, "timestamp", None)

    return build_move_auth_material(
        device_id=getattr(move_contract, "device_id", None),
        passport_id=getattr(move_contract, "passport_id", None),
        from_scope=getattr(move_contract, "from_scope", None),
        to_scope=getattr(move_contract, "to_scope", None),
        old_attachment=getattr(move_contract, "old_attachment", None),
        new_attachment=getattr(move_contract, "new_attachment", None),
        move_nonce=move_nonce,
        session_id=session_id,
        move_counter=move_counter,
        timestamp=resolved_timestamp,
    )


def compute_move_auth_tag(
    secret: str | bytes,
    move_auth_material: MoveAuthMaterial | dict[str, object],
) -> str:
    """Compute an experimental HMAC tag for deterministic move auth material."""
    material = _coerce_move_auth_material(move_auth_material)
    return compute_hmac_tag(secret, material)


def verify_move_auth_tag(
    secret: str | bytes,
    move_auth_material: MoveAuthMaterial | dict[str, object],
    expected_tag: str,
) -> bool:
    """Verify an experimental move HMAC tag, returning False for bad material."""
    try:
        material = _coerce_move_auth_material(move_auth_material)
    except ValueError:
        return False
    return verify_hmac_tag(secret, material, expected_tag)


def attach_move_auth(
    move_contract: object,
    secret: str | bytes,
    session_id: str,
    move_nonce: str,
    move_counter: int,
    timestamp: int | None = None,
) -> object:
    """Attach experimental auth fields to a move contract and return it."""
    material = move_auth_material_from_contract(
        move_contract,
        session_id=session_id,
        move_nonce=move_nonce,
        move_counter=move_counter,
        timestamp=timestamp,
    )
    tag = compute_move_auth_tag(secret, material)

    move_contract.auth_mode = AUTH_MODE_HMAC_SHA256_EXPERIMENTAL
    move_contract.session_id = session_id
    move_contract.move_nonce = move_nonce
    move_contract.move_counter = move_counter
    move_contract.move_auth_tag = tag
    return move_contract


def verify_move_contract_auth(
    registry_hub: RegistryHub,
    move_contract: MoveContract,
) -> MoveAuthVerificationResult:
    """Verify symbolic or experimental HMAC auth policy for a move contract.

    This helper intentionally does not apply relocation attachment updates. For
    HMAC mode, the only mutation is advancing the owning session counter after
    all checks pass.
    """
    auth_mode = move_contract.auth_mode or AUTH_MODE_SYMBOLIC
    if auth_mode == AUTH_MODE_SYMBOLIC:
        if move_contract.valid:
            return MoveAuthVerificationResult(
                success=True,
                status="move_auth_verified",
                auth_mode=AUTH_MODE_SYMBOLIC,
            )
        return MoveAuthVerificationResult(
            success=False,
            status="move_auth_rejected",
            reason="symbolic_move_invalid",
            auth_mode=AUTH_MODE_SYMBOLIC,
        )

    if auth_mode != AUTH_MODE_HMAC_SHA256_EXPERIMENTAL:
        return _move_auth_rejected(
            reason="unsupported_move_auth_mode",
            auth_mode=auth_mode,
            session_id=move_contract.session_id,
            move_counter=move_contract.move_counter,
        )

    session_id = move_contract.session_id
    move_counter = move_contract.move_counter
    if not session_id:
        return _move_auth_rejected(
            reason="missing_move_session",
            auth_mode=auth_mode,
            session_id=session_id,
            move_counter=move_counter,
        )
    if (
        move_contract.move_nonce is None
        or move_counter is None
        or isinstance(move_counter, bool)
        or move_contract.move_auth_tag is None
    ):
        return _move_auth_rejected(
            reason="missing_move_auth_fields",
            auth_mode=auth_mode,
            session_id=session_id,
            move_counter=move_counter,
        )

    session = registry_hub.local_sessions.get(session_id)
    if session is None:
        return _move_auth_rejected(
            reason="move_session_not_found",
            auth_mode=auth_mode,
            session_id=session_id,
            move_counter=move_counter,
        )

    local_record = registry_hub.devices.get(move_contract.device_id)
    if local_record is not None and local_record.current_state in {"quarantined", "revoked"}:
        return _move_auth_rejected(
            reason=f"device_{local_record.current_state}",
            auth_mode=auth_mode,
            session_id=session_id,
            move_counter=move_counter,
        )

    if session.state != "active":
        return _move_auth_rejected(
            reason="move_session_inactive",
            auth_mode=auth_mode,
            session_id=session_id,
            move_counter=move_counter,
        )

    if session.device_id != move_contract.device_id:
        return _move_auth_rejected(
            reason="move_session_device_mismatch",
            auth_mode=auth_mode,
            session_id=session_id,
            move_counter=move_counter,
        )

    if not verify_session_counter(session, move_counter):
        return _move_auth_rejected(
            reason="stale_move_counter",
            auth_mode=auth_mode,
            session_id=session_id,
            move_counter=move_counter,
        )

    material = move_auth_material_from_contract(
        move_contract,
        session_id=session_id,
        move_nonce=move_contract.move_nonce,
        move_counter=move_counter,
    )
    if not verify_move_auth_tag(session.secret, material, move_contract.move_auth_tag):
        return _move_auth_rejected(
            reason="invalid_move_auth_tag",
            auth_mode=auth_mode,
            session_id=session_id,
            move_counter=move_counter,
        )

    advance_session_counter(session, move_counter)
    return MoveAuthVerificationResult(
        success=True,
        status="move_auth_verified",
        auth_mode=auth_mode,
        session_id=session_id,
        move_counter=move_counter,
    )


def _coerce_move_auth_material(
    move_auth_material: MoveAuthMaterial | dict[str, object],
) -> dict[str, object]:
    if isinstance(move_auth_material, MoveAuthMaterial):
        return move_auth_material.to_dict()
    return _validate_move_auth_material(move_auth_material)


def _validate_move_auth_material(material: dict[str, Any]) -> dict[str, object]:
    missing_fields = [
        field_name for field_name in REQUIRED_MOVE_AUTH_FIELDS if material.get(field_name) is None
    ]
    if missing_fields:
        missing = ", ".join(missing_fields)
        raise ValueError(f"missing required move auth material: {missing}")

    validated = {field_name: material[field_name] for field_name in REQUIRED_MOVE_AUTH_FIELDS}
    if material.get("timestamp") is not None:
        validated["timestamp"] = material["timestamp"]
    return validated


def _move_auth_rejected(
    *,
    reason: str,
    auth_mode: str,
    session_id: str | None,
    move_counter: int | None,
) -> MoveAuthVerificationResult:
    return MoveAuthVerificationResult(
        success=False,
        status="move_auth_rejected",
        reason=reason,
        auth_mode=auth_mode,
        session_id=session_id,
        move_counter=move_counter,
    )
