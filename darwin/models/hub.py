"""Hub model placeholders for DARWIN."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from darwin.models.metrics import RegistryMetrics, TrafficMetrics
from darwin.models.move import FlowControlRecord, MoveContract, RelocationRecord
from darwin.models.passport import PassportRecord
from darwin.models.recommendation import GrowthRecommendation

if TYPE_CHECKING:
    from darwin.models.checkpoint import CheckpointState
    from darwin.models.device import Device
    from darwin.models.lane import LogicalLane
    from darwin.models.route import ForwardingResult, RouteRecord
    from darwin.models.security import QuarantineRecord, SecurityEvent
    from darwin.registry.summaries import SummaryDeviceEntry, UpwardSummary


@dataclass(slots=True)
class LocalDeviceRecord:
    """Registry-local view of a device identity."""

    device_id: str
    requested_label: str
    current_label: str
    identity_chain: str
    passport_id: str
    current_attachment: str
    current_state: str
    checkpoint_tier: int

    @property
    def label(self) -> str:
        """Return the device's current local label."""
        return self.current_label

    @property
    def full_identity_chain(self) -> str:
        """Alias used by the data model docs."""
        return self.identity_chain


@dataclass(slots=True)
class AttachmentRecord:
    """Symbolic attachment state for a device registered at a hub."""

    device_id: str
    current_attachment: str
    current_scope: str
    state: str
    attachment_type: str = "direct_child"
    traffic_hint: str | None = None


@dataclass(slots=True)
class ConflictRecord:
    """A registry conflict that still preserves both device IDs."""

    conflict_id: str
    conflict_type: str
    requested_label: str = ""
    existing_device_id: str = ""
    requesting_device_id: str = ""
    assigned_temp_label: str = ""
    status: str = "pending_resolution"


@dataclass(slots=True)
class RegistryHub:
    """A scoped identity registry for simulated devices."""

    hub_id: str
    scope_path: str
    parent_hub_id: str | None = None
    labels: dict[str, str] = field(default_factory=dict)
    devices: dict[str, LocalDeviceRecord] = field(default_factory=dict)
    passports: dict[str, PassportRecord] = field(default_factory=dict)
    attachments: dict[str, AttachmentRecord] = field(default_factory=dict)
    conflicts: dict[str, ConflictRecord] = field(default_factory=dict)
    checkpoints: dict[str, CheckpointState] = field(default_factory=dict)
    moves: dict[str, list[MoveContract]] = field(default_factory=dict)
    relocations: dict[str, RelocationRecord] = field(default_factory=dict)
    security_events: list[SecurityEvent] = field(default_factory=list)
    quarantines: dict[str, QuarantineRecord] = field(default_factory=dict)
    metrics: RegistryMetrics = field(default_factory=RegistryMetrics)
    summary_version: int = 0
    child_summaries: dict[str, UpwardSummary] = field(default_factory=dict)
    summary_device_index: dict[str, SummaryDeviceEntry] = field(default_factory=dict)

    def identity_chain_for(self, label: str) -> str:
        """Return the full identity chain for a label in this scope."""
        return f"{self.scope_path}.{label}"


@dataclass(slots=True)
class TrafficHub:
    """A packet and lane movement hub for simulated routes."""

    hub_id: str
    neighbors: dict[str, NeighborRecord] = field(default_factory=dict)
    direct_attachments: dict[str, DirectAttachmentRecord] = field(default_factory=dict)
    routes: dict[str, RouteRecord] = field(default_factory=dict)
    lanes: dict[str, LogicalLane] = field(default_factory=dict)
    forwarding_log: list[ForwardingResult] = field(default_factory=list)
    relocations: dict[str, RelocationRecord] = field(default_factory=dict)
    flow_controls: dict[str, FlowControlRecord] = field(default_factory=dict)
    security_events: list[SecurityEvent] = field(default_factory=list)
    quarantines: dict[str, QuarantineRecord] = field(default_factory=dict)
    metrics: TrafficMetrics = field(default_factory=TrafficMetrics)
    growth_recommendations: list[GrowthRecommendation] = field(default_factory=list)
    _cross_tree_branches: set[str] = field(default_factory=set)

    def connect_neighbor(self, other_hub: TrafficHub | str) -> None:
        """Connect this hub to another hub or neighbor hub ID."""
        if isinstance(other_hub, TrafficHub):
            self.neighbors[other_hub.hub_id] = NeighborRecord(hub_id=other_hub.hub_id)
            other_hub.neighbors[self.hub_id] = NeighborRecord(hub_id=self.hub_id)
            return

        self.neighbors[other_hub] = NeighborRecord(hub_id=other_hub)

    def attach_device(self, device: Device | str) -> DirectAttachmentRecord:
        """Attach a device object or device ID to this traffic hub."""
        device_id = device.device_id if not isinstance(device, str) else device
        record = DirectAttachmentRecord(device_id=device_id, hub_id=self.hub_id)
        self.direct_attachments[device_id] = record

        if not isinstance(device, str):
            device.current_traffic_hub = self.hub_id
            if device.state == "unknown":
                device.state = "online"

        return record

    def detach_device(self, device_id: str) -> DirectAttachmentRecord | None:
        """Remove a direct device attachment from this hub."""
        return self.direct_attachments.pop(device_id, None)


@dataclass(slots=True)
class NeighborRecord:
    """Symbolic neighbor connection between traffic hubs."""

    hub_id: str
    status: str = "connected"


@dataclass(slots=True)
class DirectAttachmentRecord:
    """Symbolic record of a device attached to a traffic hub."""

    device_id: str
    hub_id: str
    attachment_type: str = "direct"
    status: str = "attached"
