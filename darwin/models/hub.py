"""Hub model placeholders for DARWIN."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from darwin.models.alias import AliasBundle, AliasRecord
from darwin.models.metrics import RegistryMetrics, TrafficMetrics
from darwin.models.move import FlowControlRecord, MoveContract, RelocationRecord
from darwin.models.passport import PassportRecord
from darwin.models.recommendation import GrowthRecommendation
from darwin.models.route import LinkMetrics
from darwin.models.session import LocalAuthSession

if TYPE_CHECKING:
    from darwin.models.adapter_endpoint import AdapterEndpoint, HubTopologyAdvertisement
    from darwin.models.alias_authority import AliasAuthorityOutcomeRecord
    from darwin.models.checkpoint import CheckpointState
    from darwin.models.device import Device
    from darwin.models.encrypted_delivery import EncryptedDeliveryResult
    from darwin.models.encryption import (
        EncryptionIdentity,
        EncryptionPolicyDecision,
        KeyBundleReference,
        MailboxEncryptionBinding,
        MailboxEncryptionPolicy,
    )
    from darwin.models.lane import LogicalLane
    from darwin.models.lane_signature import LaneDefinition
    from darwin.models.mailbox import MailboxIdentity
    from darwin.models.message import MessageDeliveryResult, MessageEnvelope
    from darwin.models.route import ForwardingResult, RouteRecord
    from darwin.models.security import QuarantineRecord, SecurityEvent
    from darwin.models.stream_offer import (
        LaneAdmissionDecision,
        RendezvousPollResult,
        StreamOffer,
        StreamOfferLifecycleExplanation,
        StreamOfferStatusTransition,
    )
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
    alias_authority_policy: dict[str, object] = field(default_factory=dict)
    labels: dict[str, str] = field(default_factory=dict)
    devices: dict[str, LocalDeviceRecord] = field(default_factory=dict)
    passports: dict[str, PassportRecord] = field(default_factory=dict)
    attachments: dict[str, AttachmentRecord] = field(default_factory=dict)
    aliases: dict[str, AliasRecord] = field(default_factory=dict)
    alias_bundles: dict[str, AliasBundle] = field(default_factory=dict)
    authority_outcome_history: list[AliasAuthorityOutcomeRecord] = field(
        default_factory=list
    )
    conflicts: dict[str, ConflictRecord] = field(default_factory=dict)
    checkpoints: dict[str, CheckpointState] = field(default_factory=dict)
    moves: dict[str, list[MoveContract]] = field(default_factory=dict)
    relocations: dict[str, RelocationRecord] = field(default_factory=dict)
    security_events: list[SecurityEvent] = field(default_factory=list)
    quarantines: dict[str, QuarantineRecord] = field(default_factory=dict)
    local_sessions: dict[str, LocalAuthSession] = field(default_factory=dict)
    lane_registry: dict[str, LaneDefinition] = field(default_factory=dict)
    mailboxes: dict[str, MailboxIdentity] = field(default_factory=dict)
    mailbox_address_index: dict[str, str] = field(default_factory=dict)
    encryption_identities: dict[str, EncryptionIdentity] = field(default_factory=dict)
    key_bundle_references: dict[str, KeyBundleReference] = field(default_factory=dict)
    mailbox_encryption_bindings: dict[str, MailboxEncryptionBinding] = field(
        default_factory=dict
    )
    mailbox_encryption_policies: dict[str, MailboxEncryptionPolicy] = field(
        default_factory=dict
    )
    encryption_policy_decision_history: list[EncryptionPolicyDecision] = field(
        default_factory=list
    )
    encrypted_delivery_result_history: list[EncryptedDeliveryResult] = field(
        default_factory=list
    )
    held_stream_offers: list[StreamOffer] = field(default_factory=list)
    rendezvous_poll_result_history: list[RendezvousPollResult] = field(
        default_factory=list
    )
    lane_admission_decision_history: list[LaneAdmissionDecision] = field(
        default_factory=list
    )
    stream_offer_status_transition_history: list[StreamOfferStatusTransition] = field(
        default_factory=list
    )
    stream_offer_lifecycle_explanation_history: list[
        StreamOfferLifecycleExplanation
    ] = field(default_factory=list)
    adapter_endpoints: dict[str, AdapterEndpoint] = field(default_factory=dict)
    hub_topology_advertisements: dict[str, HubTopologyAdvertisement] = field(
        default_factory=dict
    )
    message_inboxes: dict[str, list[MessageEnvelope]] = field(default_factory=dict)
    message_delivery_results: list[MessageDeliveryResult] = field(
        default_factory=list
    )
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

    def connect_neighbor(
        self,
        other_hub: TrafficHub | str,
        metrics: LinkMetrics | None = None,
        *,
        latency_ms: int | None = None,
        congestion: str | None = None,
        trust: str | None = None,
        stability: str | None = None,
    ) -> None:
        """Connect this hub to another hub or neighbor hub ID."""
        link_metrics = _link_metrics_from_args(
            metrics,
            latency_ms=latency_ms,
            congestion=congestion,
            trust=trust,
            stability=stability,
        )
        if isinstance(other_hub, TrafficHub):
            self.neighbors[other_hub.hub_id] = NeighborRecord(
                hub_id=other_hub.hub_id,
                metrics=link_metrics,
            )
            other_hub.neighbors[self.hub_id] = NeighborRecord(
                hub_id=self.hub_id,
                metrics=link_metrics,
            )
            return

        self.neighbors[other_hub] = NeighborRecord(hub_id=other_hub, metrics=link_metrics)

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
    metrics: LinkMetrics = field(default_factory=LinkMetrics)


@dataclass(slots=True)
class DirectAttachmentRecord:
    """Symbolic record of a device attached to a traffic hub."""

    device_id: str
    hub_id: str
    attachment_type: str = "direct"
    status: str = "attached"


def _link_metrics_from_args(
    metrics: LinkMetrics | None,
    *,
    latency_ms: int | None,
    congestion: str | None,
    trust: str | None,
    stability: str | None,
) -> LinkMetrics:
    if metrics is not None and all(
        value is None for value in (latency_ms, congestion, trust, stability)
    ):
        return metrics

    base = metrics or LinkMetrics()
    return LinkMetrics(
        latency_ms=base.latency_ms if latency_ms is None else int(latency_ms),
        congestion=base.congestion if congestion is None else str(congestion),
        trust=base.trust if trust is None else str(trust),
        stability=base.stability if stability is None else str(stability),
    )
