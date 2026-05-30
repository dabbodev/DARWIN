"""Simple human-readable simulator event log."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class EventLogEntry:
    """One deterministic simulator event."""

    time: int
    message: str
    event_type: str | None = None
    actor: str | None = None
    target: str | None = None
    device_id: str | None = None
    hub_id: str | None = None
    lane_id: str | None = None
    status: str | None = None
    data: dict[str, Any] = field(default_factory=dict)

    def render(self) -> str:
        return f"[t={self.time}] {self.message}"


@dataclass(slots=True)
class EventLog:
    entries: list[EventLogEntry] = field(default_factory=list)

    @property
    def lines(self) -> list[str]:
        return [entry.render() for entry in self.entries]

    def write(
        self,
        time: int,
        message: str,
        event_type: str | None = None,
        *,
        actor: str | None = None,
        target: str | None = None,
        device_id: str | None = None,
        hub_id: str | None = None,
        lane_id: str | None = None,
        status: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        self.entries.append(
            EventLogEntry(
                time=time,
                message=message,
                event_type=event_type,
                actor=actor,
                target=target,
                device_id=device_id,
                hub_id=hub_id,
                lane_id=lane_id,
                status=status,
                data={} if data is None else dict(data),
            )
        )

    def has_event_type(self, event_type: str) -> bool:
        return any(
            entry.event_type == event_type or event_type in entry.message
            for entry in self.entries
        )

    def render(self) -> str:
        return "\n".join(self.lines)
