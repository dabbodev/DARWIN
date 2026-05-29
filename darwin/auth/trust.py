"""Symbolic trust helpers for DARWIN v0.1."""

from __future__ import annotations

from darwin.models.passport import PassportRecord
from darwin.models.security import AuthState, SecurityEvent, TrustCheckResult


def verify_passport(
    passport: PassportRecord,
    hub_id: str,
    timestamp: int | None = None,
) -> TrustCheckResult:
    """Verify a passport symbolically without real signatures or key storage."""
    failure_reason = _passport_failure_reason(passport)
    if failure_reason is None:
        return TrustCheckResult(
            action="passport_verified",
            success=True,
            claimed_device_id=passport.device_id,
        )

    event_type = {
        "invalid_passport": "passport_verification_failed",
        "revoked_passport": "revoked_passport_presented",
        "issuer_unknown": "issuer_unknown",
    }[failure_reason]
    event = SecurityEvent(
        event_type=event_type,
        claimed_device_id=passport.device_id,
        hub_id=hub_id,
        severity="high",
        action_taken="registration_rejected",
        timestamp=timestamp,
        reason=failure_reason,
    )
    return TrustCheckResult(
        action="registration_rejected",
        success=False,
        claimed_device_id=passport.device_id,
        reason=failure_reason,
        security_event=event,
    )


def verify_auth_state(
    auth_state: AuthState,
    claimed_device_id: str,
    hub_id: str,
    timestamp: int | None = None,
) -> TrustCheckResult:
    """Verify symbolic registration trust booleans."""
    failure_reason = _auth_state_failure_reason(auth_state)
    if failure_reason is None:
        return TrustCheckResult(
            action="passport_verified",
            success=True,
            claimed_device_id=claimed_device_id,
        )

    event_type = {
        "invalid_passport": "passport_verification_failed",
        "revoked_passport": "revoked_passport_presented",
        "issuer_unknown": "issuer_unknown",
    }[failure_reason]
    event = SecurityEvent(
        event_type=event_type,
        claimed_device_id=claimed_device_id,
        hub_id=hub_id,
        severity="high",
        action_taken="registration_rejected",
        timestamp=timestamp,
        reason=failure_reason,
    )
    return TrustCheckResult(
        action="registration_rejected",
        success=False,
        claimed_device_id=claimed_device_id,
        reason=failure_reason,
        security_event=event,
    )


def _passport_failure_reason(passport: PassportRecord) -> str | None:
    if passport.revoked:
        return "revoked_passport"
    if not passport.issuer_trusted:
        return "issuer_unknown"
    if not passport.valid:
        return "invalid_passport"
    return None


def _auth_state_failure_reason(auth_state: AuthState) -> str | None:
    if auth_state.revoked:
        return "revoked_passport"
    if not auth_state.issuer_trusted:
        return "issuer_unknown"
    if not auth_state.passport_valid:
        return "invalid_passport"
    return None
