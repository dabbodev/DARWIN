"""Symbolic relocation and flow-control models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from darwin.models.checkpoint import CheckpointState
    from darwin.models.hub import AttachmentRecord, LocalDeviceRecord


@dataclass(slots=True)
class MoveContract:
    """Symbolic v0.1 authorization to move a durable device identity."""

    move_id: str
    passport_id: str
    device_id: str
    from_scope: str
    to_scope: str
    old_attachment: str
    new_attachment: str
    valid: bool = True
    timestamp: int | None = None


@dataclass(slots=True)
class RelocationRecord:
    """Current relocation state for a device."""

    device_id: str
    state: str
    old_attachment: str | None = None
    new_attachment: str | None = None
    from_scope: str | None = None
    to_scope: str | None = None
    started_at: int | None = None
    updated_at: int | None = None
    affected_lanes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class FlowControlRecord:
    """Sender-side flow control for a lane paused by relocation."""

    lane_id: str
    device_id: str
    reason: str
    hold_new_packets: bool = True
    hold_window: int = 3000


@dataclass(slots=True)
class MarkInTransitResult:
    """Outcome of marking a registered device as relocating."""

    action: str
    device_id: str
    device: LocalDeviceRecord | None = None
    attachment: AttachmentRecord | None = None
    checkpoint: CheckpointState | None = None
    relocation: RelocationRecord | None = None
    reason: str | None = None

    @property
    def success(self) -> bool:
        return self.action == "marked_in_transit"


@dataclass(slots=True)
class MoveVerificationResult:
    """Outcome of applying a symbolic move contract."""

    action: str
    device_id: str
    move_contract: MoveContract | None = None
    attachment: AttachmentRecord | None = None
    reason: str | None = None

    @property
    def success(self) -> bool:
        return self.action == "attachment_updated"


@dataclass(slots=True)
class LanePauseResult:
    """Outcome of pausing lanes affected by relocation."""

    action: str
    device_id: str
    affected_lanes: list[str] = field(default_factory=list)
    flow_controls: list[FlowControlRecord] = field(default_factory=list)
    relocation: RelocationRecord | None = None
    reason: str | None = None

    @property
    def success(self) -> bool:
        return self.action in {"lanes_paused", "no_lanes_affected"}


@dataclass(slots=True)
class LaneResumeResult:
    """Outcome of rerouting and resuming relocation-paused lanes."""

    action: str
    device_id: str
    resumed_lanes: list[str] = field(default_factory=list)
    failed_lanes: list[str] = field(default_factory=list)
    routes: dict[str, list[str]] = field(default_factory=dict)
    reason: str | None = None

    @property
    def success(self) -> bool:
        return self.action == "lanes_resumed"


@dataclass(slots=True)
class RelocationExpiryResult:
    """Outcome of expiring a relocation flow-control hold."""

    action: str
    device_id: str
    failed_lanes: list[str] = field(default_factory=list)
    relocation: RelocationRecord | None = None
    reason: str | None = None

    @property
    def success(self) -> bool:
        return self.action == "relocation_failed"
