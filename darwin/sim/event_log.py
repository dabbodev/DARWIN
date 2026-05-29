"""Simple human-readable simulator event log."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class EventLogEntry:
    """One deterministic simulator event."""

    time: int
    message: str
    event_type: str | None = None

    def render(self) -> str:
        return f"[t={self.time}] {self.message}"


@dataclass(slots=True)
class EventLog:
    entries: list[EventLogEntry] = field(default_factory=list)

    @property
    def lines(self) -> list[str]:
        return [entry.render() for entry in self.entries]

    def write(self, time: int, message: str, event_type: str | None = None) -> None:
        self.entries.append(EventLogEntry(time=time, message=message, event_type=event_type))

    def has_event_type(self, event_type: str) -> bool:
        return any(
            entry.event_type == event_type or event_type in entry.message
            for entry in self.entries
        )

    def render(self) -> str:
        return "\n".join(self.lines)
