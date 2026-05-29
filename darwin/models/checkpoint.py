"""Checkpoint packet and state models for symbolic liveness tracking."""

from __future__ import annotations

from dataclasses import dataclass, field

CHECKPOINT_INTERVALS_BY_TIER = {
    0: 1800,
    1: 30,
    2: 5,
    3: 1,
}

CHECKPOINT_STATES = {
    "unknown",
    "online",
    "idle",
    "active",
    "in_transit",
    "timed_out",
    "offline",
    "quarantined",
    "revoked",
    "rejected",
}


@dataclass(slots=True)
class CheckpointState:
    """Registry-owned liveness state for a registered device."""

    device_id: str
    state: str
    checkpoint_tier: int
    last_checkpoint_at: int
    expected_next_checkpoint_at: int
    active_lane_count: int | None = None
    battery_level: int | None = None
    auth_valid: bool = True
    missed_checkpoint_count: int = 0
    status: str = "recorded"


@dataclass(slots=True)
class CheckpointPacket:
    """Symbolic checkpoint packet sent by a device to a hub."""

    packet_id: str
    source_device_id: str
    source_hub_id: str
    state: str
    checkpoint_tier: int
    created_at: int
    packet_class: str = "CHECKPOINT"
    packet_type: str = "device_state_checkpoint"
    active_lane_count: int | None = None
    battery_level: int | None = None
    auth_tag_valid: bool = True
    payload: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CheckpointPolicy:
    """Timeout policy derived from the checkpoint tier."""

    tier: int
    interval: int
    timeout_grace: int = 1

    @property
    def timeout_at(self) -> int:
        """Return the offset after which a checkpoint should be considered timed out."""
        return self.interval + self.timeout_grace


@dataclass(slots=True)
class CheckpointRecordResult:
    """Outcome of applying a checkpoint packet to a RegistryHub."""

    action: str
    device_id: str
    checkpoint: CheckpointState | None = None
    reason: str | None = None

    @property
    def accepted(self) -> bool:
        return self.action == "checkpoint_recorded"


@dataclass(slots=True)
class CheckpointTimeoutResult:
    """Outcome for one device during timeout detection."""

    device_id: str
    action: str
    state: str
    expected_next_checkpoint_at: int
    checked_at: int
    timed_out: bool = False


def checkpoint_interval_for_tier(tier: int) -> int:
    """Return the simulated checkpoint interval for a checkpoint tier."""
    return CHECKPOINT_INTERVALS_BY_TIER.get(tier, CHECKPOINT_INTERVALS_BY_TIER[1])


def checkpoint_policy_for_tier(tier: int) -> CheckpointPolicy:
    """Return the default checkpoint timeout policy for a tier."""
    return CheckpointPolicy(tier=tier, interval=checkpoint_interval_for_tier(tier))


def make_checkpoint_packet(
    device: object,
    hub_id: str,
    state: str,
    current_time: int,
    auth_tag_valid: bool = True,
    active_lane_count: int | None = None,
    battery_level: int | None = None,
) -> CheckpointPacket:
    """Build a symbolic checkpoint packet from a device-like object."""
    device_id = getattr(device, "device_id", str(device))
    checkpoint_tier = getattr(device, "checkpoint_tier", 1)

    return CheckpointPacket(
        packet_id=f"cp_{device_id}_{current_time}",
        source_device_id=device_id,
        source_hub_id=hub_id,
        state=state,
        checkpoint_tier=checkpoint_tier,
        created_at=current_time,
        active_lane_count=active_lane_count,
        battery_level=battery_level,
        auth_tag_valid=auth_tag_valid,
        payload={
            "device_state": state,
            "checkpoint_tier": checkpoint_tier,
            "active_lane_count": active_lane_count,
            "battery_level": battery_level,
        },
    )
