"""Simulator-local auth session models."""

from __future__ import annotations

from dataclasses import dataclass

from darwin.auth.modes import AUTH_MODE_HMAC_SHA256_EXPERIMENTAL


@dataclass(slots=True)
class LocalAuthSession:
    """Registry-owned simulator session secret record.

    Secrets are deterministic test/demo fixtures only. This model does not
    represent production key exchange, key storage, or device-held secrets.
    """

    session_id: str
    device_id: str
    hub_id: str
    scope: str | None
    auth_mode: str
    secret: str
    current_counter: int = 0
    created_at: int | None = None
    expires_at: int | None = None
    state: str = "active"
    rotation_index: int = 0


@dataclass(slots=True)
class SessionResult:
    """Outcome of a simulator-local session operation."""

    status: str
    success: bool
    reason: str | None = None
    session: LocalAuthSession | None = None

    @property
    def action(self) -> str:
        """Compatibility alias for scenario latest-step assertions."""
        return self.status


def default_session_auth_mode() -> str:
    """Return the default auth mode for local sessions."""
    return AUTH_MODE_HMAC_SHA256_EXPERIMENTAL
