"""Symbolic authentication checks for simulator v0.1.

These helpers deliberately do not implement production cryptography.
They let scenarios model trust success and trust failure before real
signatures, MACs, or key exchange are introduced.
"""

from __future__ import annotations

from dataclasses import dataclass

from darwin.models.security import AuthState


@dataclass(slots=True)
class SymbolicAuthState(AuthState):
    """Backward-compatible symbolic auth state name."""

    move_contract_valid: bool = True

    @property
    def all_valid(self) -> bool:
        return AuthState.all_valid.fget(self) and self.move_contract_valid
