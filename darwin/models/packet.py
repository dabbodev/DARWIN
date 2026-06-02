"""DARWIN packet data object for simulator scenarios."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from darwin.auth.modes import AUTH_MODE_SYMBOLIC


@dataclass(slots=True)
class DarwinPacket:
    packet_id: str
    packet_class: str
    packet_type: str
    source_device_id: str | None = None
    target_device_id: str | None = None
    source_hub_id: str | None = None
    target_hub_hint: str | None = None
    lane_id: str | None = None
    sequence_number: int | None = None
    payload: Any = field(default_factory=dict)
    auth_tag_valid: bool = True
    auth_mode: str = AUTH_MODE_SYMBOLIC
    auth_tag: str | None = None
