"""Symbolic passport records for DARWIN v0.1 simulation."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class PassportRecord:
    passport_id: str
    device_id: str
    issued_by: str
    issued_scope: str
    valid: bool = True
    revoked: bool = False
    issuer_trusted: bool = True
    permissions: dict[str, bool] = field(default_factory=dict)

    @property
    def usable(self) -> bool:
        return self.valid and self.issuer_trusted and not self.revoked
