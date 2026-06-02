"""Registry-owned simulator-local auth session lifecycle."""

from __future__ import annotations

from darwin.auth.hmac_bridge import verify_rolling_proof_tag
from darwin.auth.modes import AUTH_MODE_HMAC_SHA256_EXPERIMENTAL
from darwin.models.hub import RegistryHub
from darwin.models.session import LocalAuthSession, SessionResult


def create_local_session(
    registry_hub: RegistryHub,
    device_id: str,
    secret: str,
    session_id: str | None = None,
    current_time: int | None = None,
    ttl: int | None = None,
    auth_mode: str = AUTH_MODE_HMAC_SHA256_EXPERIMENTAL,
) -> SessionResult:
    """Create a deterministic simulator-local session for a registered device."""
    local_record = registry_hub.devices.get(device_id)
    if local_record is None:
        return SessionResult(
            status="session_rejected",
            success=False,
            reason="unknown_device",
        )
    if local_record.current_state in {"quarantined", "revoked"}:
        return SessionResult(
            status="session_rejected",
            success=False,
            reason=f"device_{local_record.current_state}",
        )

    resolved_session_id = session_id or f"{registry_hub.hub_id}:{device_id}:session"
    expires_at = None
    if current_time is not None and ttl is not None:
        expires_at = current_time + ttl

    session = LocalAuthSession(
        session_id=resolved_session_id,
        device_id=device_id,
        hub_id=registry_hub.hub_id,
        scope=registry_hub.scope_path,
        auth_mode=auth_mode,
        secret=secret,
        created_at=current_time,
        expires_at=expires_at,
    )
    registry_hub.local_sessions[resolved_session_id] = session
    return SessionResult(status="session_created", success=True, session=session)


def get_local_session(
    registry_hub: RegistryHub,
    session_id: str,
) -> LocalAuthSession | None:
    """Return a local session record if the RegistryHub owns it."""
    return registry_hub.local_sessions.get(session_id)


def rotate_local_session(
    registry_hub: RegistryHub,
    session_id: str,
    new_secret: str,
    current_time: int | None = None,
    ttl: int | None = None,
) -> SessionResult:
    """Replace a simulator session secret and reset its rolling counter."""
    session = get_local_session(registry_hub, session_id)
    if session is None:
        return SessionResult(
            status="session_rejected",
            success=False,
            reason="unknown_session",
        )

    if _is_expired(session, current_time):
        session.state = "expired"
        return SessionResult(
            status="session_rejected",
            success=False,
            reason="session_expired",
            session=session,
        )

    if session.state != "active":
        return SessionResult(
            status="session_rejected",
            success=False,
            reason=f"session_{session.state}",
            session=session,
        )

    session.secret = new_secret
    session.current_counter = 0
    session.rotation_index += 1
    session.state = "active"
    if current_time is not None:
        session.created_at = current_time
    if ttl is not None:
        session.expires_at = None if current_time is None else current_time + ttl
    return SessionResult(status="session_rotated", success=True, session=session)


def expire_local_sessions(
    registry_hub: RegistryHub,
    current_time: int,
) -> list[LocalAuthSession]:
    """Mark all local sessions expired when simulated time reaches expires_at."""
    expired: list[LocalAuthSession] = []
    for session in registry_hub.local_sessions.values():
        if session.state == "active" and _is_expired(session, current_time):
            session.state = "expired"
            expired.append(session)
    return expired


def revoke_local_session(
    registry_hub: RegistryHub,
    session_id: str,
    reason: str | None = None,
) -> SessionResult:
    """Revoke one simulator-local session without deleting its audit state."""
    session = get_local_session(registry_hub, session_id)
    if session is None:
        return SessionResult(
            status="session_rejected",
            success=False,
            reason="unknown_session",
        )

    session.state = "revoked"
    return SessionResult(
        status="session_revoked",
        success=True,
        reason=reason,
        session=session,
    )


def revoke_device_sessions(
    registry_hub: RegistryHub,
    device_id: str,
    reason: str | None = None,
) -> list[SessionResult]:
    """Revoke every simulator-local session owned by a device."""
    results: list[SessionResult] = []
    for session in sorted(
        registry_hub.local_sessions.values(),
        key=lambda item: item.session_id,
    ):
        if session.device_id == device_id:
            session.state = "revoked"
            results.append(
                SessionResult(
                    status="session_revoked",
                    success=True,
                    reason=reason,
                    session=session,
                )
            )
    return results


def quarantine_device_sessions(
    registry_hub: RegistryHub,
    device_id: str,
    reason: str | None = None,
) -> list[SessionResult]:
    """Mark active simulator-local sessions for a quarantined device as blocked."""
    results: list[SessionResult] = []
    for session in sorted(
        registry_hub.local_sessions.values(),
        key=lambda item: item.session_id,
    ):
        if session.device_id == device_id and session.state == "active":
            session.state = "quarantined"
            results.append(
                SessionResult(
                    status="session_quarantined",
                    success=True,
                    reason=reason,
                    session=session,
                )
            )
    return results


def verify_session_counter(session: LocalAuthSession, counter: int) -> bool:
    """Return whether a rolling proof counter is strictly newer."""
    return counter > session.current_counter


def advance_session_counter(session: LocalAuthSession, counter: int) -> None:
    """Advance a local session counter after successful proof verification."""
    session.current_counter = counter


def verify_hmac_rolling_proof_for_session(
    registry_hub: RegistryHub,
    session_id: str,
    counter: int,
    nonce: str,
    requested_capability: str,
    proof: str,
    current_time: int | None = None,
) -> SessionResult:
    """Verify an experimental HMAC rolling proof against a local session record."""
    session = get_local_session(registry_hub, session_id)
    if session is None:
        return SessionResult(
            status="rolling_proof_rejected",
            success=False,
            reason="unknown_session",
        )

    if session.auth_mode != AUTH_MODE_HMAC_SHA256_EXPERIMENTAL:
        return SessionResult(
            status="rolling_proof_rejected",
            success=False,
            reason="unsupported_auth_mode",
            session=session,
        )

    local_record = registry_hub.devices.get(session.device_id)
    if local_record is not None and local_record.current_state in {"quarantined", "revoked"}:
        if session.state == "active":
            session.state = local_record.current_state
        return SessionResult(
            status="rolling_proof_rejected",
            success=False,
            reason=f"device_{local_record.current_state}",
            session=session,
        )

    if session.state == "active" and _is_expired(session, current_time):
        session.state = "expired"
        return SessionResult(
            status="rolling_proof_rejected",
            success=False,
            reason="session_expired",
            session=session,
        )

    if session.state != "active":
        return SessionResult(
            status="rolling_proof_rejected",
            success=False,
            reason=f"session_{session.state}",
            session=session,
        )

    if not verify_session_counter(session, counter):
        return SessionResult(
            status="rolling_proof_rejected",
            success=False,
            reason="stale_counter",
            session=session,
        )

    verification = verify_rolling_proof_tag(
        session.secret,
        device_id=session.device_id,
        hub_id=registry_hub.hub_id,
        session_id=session.session_id,
        counter=counter,
        nonce=nonce,
        capability=requested_capability,
        expected_tag=proof,
    )
    if not verification.success:
        return SessionResult(
            status="rolling_proof_rejected",
            success=False,
            reason=verification.reason,
            session=session,
        )

    advance_session_counter(session, counter)
    return SessionResult(
        status="rolling_proof_verified",
        success=True,
        session=session,
    )


def _is_expired(session: LocalAuthSession, current_time: int | None) -> bool:
    return (
        current_time is not None
        and session.expires_at is not None
        and current_time >= session.expires_at
    )
