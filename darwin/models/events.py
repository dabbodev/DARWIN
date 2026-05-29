"""Event objects for deterministic simulation runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Event:
    event_id: str
    time: int
    event_type: str
    actor: str | None = None
    target: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
