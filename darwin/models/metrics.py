"""Symbolic pressure metrics for DARWIN simulator hubs."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RegistryMetrics:
    """Counters for RegistryHub identity and state pressure."""

    device_count: int = 0
    active_device_count: int = 0
    lookup_count: int = 0
    lookup_miss_count: int = 0
    label_conflict_count: int = 0
    duplicate_device_conflict_count: int = 0
    move_contract_count: int = 0
    checkpoint_update_count: int = 0
    summary_generation_count: int = 0
    upward_summary_accept_count: int = 0


@dataclass(slots=True)
class TrafficMetrics:
    """Counters for TrafficHub forwarding, lane, relocation, and auth pressure."""

    packets_forwarded: int = 0
    packets_delivered: int = 0
    packets_dropped: int = 0
    route_unavailable_count: int = 0
    invalid_packet_auth_count: int = 0
    lane_open_count: int = 0
    lane_send_count: int = 0
    lane_pause_count: int = 0
    lane_resume_count: int = 0
    relocation_count: int = 0
    flow_hold_count: int = 0
    cross_tree_packet_count: int = 0
    route_selection_count: int = 0
