"""Upward RegistryHub summary helpers."""

from __future__ import annotations

from dataclasses import dataclass, field

from darwin.models.hub import LocalDeviceRecord, RegistryHub
from darwin.registry.metrics import (
    record_registry_lookup,
    record_summary_generation,
    record_upward_summary_acceptance,
)


@dataclass(slots=True)
class SummaryDeviceEntry:
    """Compact parent-visible device identity and state anchor."""

    device_id: str
    identity_chain: str
    passport_id: str
    current_state: str
    current_attachment: str
    last_checkpoint: int | str | None = None


@dataclass(slots=True)
class UpwardSummary:
    """Summary a child RegistryHub can hand upward to its parent."""

    from_hub_id: str
    scope_path: str
    summary_version: int
    devices: list[SummaryDeviceEntry] = field(default_factory=list)
    generated_at: int | str | None = None


@dataclass(slots=True)
class SummaryLookupResult:
    """Result of a parent lookup answered from child summary state."""

    device_id: str
    identity_chain: str
    passport_id: str
    current_state: str
    current_attachment: str
    last_checkpoint: int | str | None
    from_hub_id: str
    scope_path: str
    summary_version: int
    source: str = "child_summary"


def generate_upward_summary(
    hub: RegistryHub,
    generated_at: int | str | None = None,
) -> UpwardSummary:
    """Generate a deterministic compact summary of a hub's registered devices."""
    hub.summary_version += 1
    record_summary_generation(hub)
    devices = [
        _summary_device_entry(hub.devices[device_id])
        for device_id in sorted(hub.devices)
    ]
    return UpwardSummary(
        from_hub_id=hub.hub_id,
        scope_path=hub.scope_path,
        summary_version=hub.summary_version,
        devices=devices,
        generated_at=generated_at,
    )


def accept_child_summary(parent_hub: RegistryHub, summary: UpwardSummary) -> None:
    """Store a child summary on a parent hub and refresh the parent summary index."""
    previous_summary = parent_hub.child_summaries.get(summary.from_hub_id)
    if previous_summary is not None:
        for device in previous_summary.devices:
            if parent_hub.summary_device_index.get(device.device_id) == device:
                del parent_hub.summary_device_index[device.device_id]

    parent_hub.child_summaries[summary.from_hub_id] = summary
    for device in summary.devices:
        parent_hub.summary_device_index[device.device_id] = device
    record_upward_summary_acceptance(parent_hub)


def resolve_device_id_from_summaries(
    parent_hub: RegistryHub,
    device_id: str,
) -> SummaryLookupResult | None:
    """Resolve a durable device ID using summaries accepted from child hubs."""
    indexed_entry = parent_hub.summary_device_index.get(device_id)
    if indexed_entry is None:
        record_registry_lookup(parent_hub, found=False)
        return None

    for summary in parent_hub.child_summaries.values():
        for device in summary.devices:
            if device.device_id == device_id:
                record_registry_lookup(parent_hub, found=True)
                return SummaryLookupResult(
                    device_id=device.device_id,
                    identity_chain=device.identity_chain,
                    passport_id=device.passport_id,
                    current_state=device.current_state,
                    current_attachment=device.current_attachment,
                    last_checkpoint=device.last_checkpoint,
                    from_hub_id=summary.from_hub_id,
                    scope_path=summary.scope_path,
                    summary_version=summary.summary_version,
                )

    record_registry_lookup(parent_hub, found=False)
    return None


def query_parent(
    child_hub: RegistryHub,
    parent_hub: RegistryHub,
    device_id: str,
) -> SummaryLookupResult | None:
    """Ask a parent hub for a summarized device lookup."""
    return resolve_device_id_from_summaries(parent_hub, device_id)


def _summary_device_entry(record: LocalDeviceRecord) -> SummaryDeviceEntry:
    return SummaryDeviceEntry(
        device_id=record.device_id,
        identity_chain=record.identity_chain,
        passport_id=record.passport_id,
        current_state=record.current_state,
        current_attachment=record.current_attachment,
        last_checkpoint=_last_checkpoint(record),
    )


def _last_checkpoint(record: LocalDeviceRecord) -> int | str | None:
    return getattr(record, "last_checkpoint", None)
