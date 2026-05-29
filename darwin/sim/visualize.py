"""Plain-text Mermaid visualization helpers for DARWIN simulator state."""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def snapshot_to_mermaid(
    snapshot: dict[str, object],
    include_devices: bool = True,
    include_lanes: bool = True,
) -> str:
    """Render a deterministic Mermaid flowchart from a detailed world snapshot."""
    traffic_hubs = _section_as_mapping(snapshot.get("traffic_hubs"))
    devices = _section_as_mapping(snapshot.get("devices"))
    lanes = _section_as_mapping(snapshot.get("lanes"))

    hub_ids = _collect_hub_ids(traffic_hubs)
    attachments = _collect_attachments(traffic_hubs, devices) if include_devices else []
    device_ids = sorted({device_id for _, device_id in attachments})

    ids = _MermaidIds()
    for hub_id in hub_ids:
        ids.node_id("hub", hub_id)
    for device_id in device_ids:
        ids.node_id("device", device_id)

    lines = ["flowchart LR"]
    for hub_id in hub_ids:
        lines.append(
            f'  {ids.node_id("hub", hub_id)}["{_escape_label(f"TrafficHub: {hub_id}")}"]'
        )

    if include_devices:
        for device_id in device_ids:
            lines.append(
                f'  {ids.node_id("device", device_id)}["{_escape_label(f"Device: {device_id}")}"]'
            )

    for from_hub_id, to_hub_id in _collect_links(traffic_hubs):
        lines.append(
            f"  {ids.node_id('hub', from_hub_id)} --- {ids.node_id('hub', to_hub_id)}"
        )

    if include_devices:
        for hub_id, device_id in attachments:
            lines.append(
                f"  {ids.node_id('hub', hub_id)} --> {ids.node_id('device', device_id)}"
            )

    if include_lanes:
        lane_comments = _lane_comments(lanes)
        if lane_comments:
            lines.extend(lane_comments)

    return "\n".join(lines) + "\n"


def world_to_mermaid(
    world: Any,
    include_devices: bool = True,
    include_lanes: bool = True,
) -> str:
    """Render a deterministic Mermaid flowchart from a World-like object."""
    return snapshot_to_mermaid(
        world.snapshot(detailed=True),
        include_devices=include_devices,
        include_lanes=include_lanes,
    )


def scenario_result_to_mermaid(
    result: Any,
    include_devices: bool = True,
    include_lanes: bool = True,
) -> str:
    """Render a deterministic Mermaid flowchart from a ScenarioRunResult-like object."""
    return snapshot_to_mermaid(
        result.final_snapshot,
        include_devices=include_devices,
        include_lanes=include_lanes,
    )


def write_mermaid(path: str | Path, mermaid_text: str) -> None:
    """Write Mermaid text as UTF-8, creating parent directories as needed."""
    export_path = Path(path)
    export_path.parent.mkdir(parents=True, exist_ok=True)
    export_path.write_text(mermaid_text, encoding="utf-8")


class _MermaidIds:
    def __init__(self) -> None:
        self._by_raw: dict[tuple[str, str], str] = {}
        self._used: set[str] = set()

    def node_id(self, node_type: str, raw_id: str) -> str:
        key = (node_type, raw_id)
        if key in self._by_raw:
            return self._by_raw[key]

        base = _sanitize_node_id(raw_id)
        candidate = base
        suffix = 2
        while candidate in self._used:
            candidate = f"{base}_{suffix}"
            suffix += 1

        self._by_raw[key] = candidate
        self._used.add(candidate)
        return candidate


def _sanitize_node_id(raw_id: str) -> str:
    safe = re.sub(r"[^0-9A-Za-z_]", "_", raw_id).strip("_")
    if not safe:
        safe = "node"
    if not re.match(r"[A-Za-z_]", safe):
        safe = f"n_{safe}"
    if safe in {"end", "flowchart", "graph", "subgraph"}:
        safe = f"n_{safe}"
    return safe


def _escape_label(label: str) -> str:
    return label.replace("\\", "\\\\").replace('"', '\\"')


def _section_as_mapping(value: object) -> dict[str, object]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    if isinstance(value, list):
        return {str(item): {} for item in value}
    return {}


def _collect_hub_ids(traffic_hubs: Mapping[str, object]) -> list[str]:
    hub_ids = set(traffic_hubs)
    for hub_data in traffic_hubs.values():
        for neighbor_id in _neighbor_ids(hub_data):
            hub_ids.add(neighbor_id)
    return sorted(hub_ids)


def _collect_links(traffic_hubs: Mapping[str, object]) -> list[tuple[str, str]]:
    links: set[tuple[str, str]] = set()
    for hub_id, hub_data in traffic_hubs.items():
        for neighbor_id in _neighbor_ids(hub_data):
            links.add(tuple(sorted((hub_id, neighbor_id))))
    return sorted(links)


def _neighbor_ids(hub_data: object) -> list[str]:
    if not isinstance(hub_data, Mapping):
        return []

    neighbors = hub_data.get("neighbors")
    if isinstance(neighbors, Mapping):
        return sorted(str(neighbor_id) for neighbor_id in neighbors)
    if isinstance(neighbors, list):
        return sorted(str(neighbor_id) for neighbor_id in neighbors)

    neighbor_details = hub_data.get("neighbor_details")
    if isinstance(neighbor_details, Mapping):
        return sorted(str(neighbor_id) for neighbor_id in neighbor_details)
    return []


def _collect_attachments(
    traffic_hubs: Mapping[str, object],
    devices: Mapping[str, object],
) -> list[tuple[str, str]]:
    attachments: set[tuple[str, str]] = set()

    for hub_id, hub_data in traffic_hubs.items():
        if not isinstance(hub_data, Mapping):
            continue

        direct_attachments = hub_data.get("direct_attachments")
        if isinstance(direct_attachments, (Mapping, list)):
            direct_attachment_ids = direct_attachments
        else:
            direct_attachment_ids = []

        for device_id in direct_attachment_ids:
            attachments.add((hub_id, str(device_id)))

    for device_id, device_data in devices.items():
        if not isinstance(device_data, Mapping):
            continue
        current_traffic_hub = device_data.get("current_traffic_hub")
        if current_traffic_hub:
            attachments.add((str(current_traffic_hub), device_id))

    return sorted(attachments)


def _lane_comments(lanes: Mapping[str, object]) -> list[str]:
    comments: list[str] = []
    for lane_id, lane_data in sorted(lanes.items()):
        if not isinstance(lane_data, Mapping):
            continue

        state = str(lane_data.get("state", "unknown"))
        source = str(lane_data.get("source", "unknown"))
        target = str(lane_data.get("target", "unknown"))
        route = [str(hub_id) for hub_id in _list_value(lane_data.get("route"))]

        route_text = " -> ".join(route) if route else "(no route)"
        cost = lane_data.get("route_total_cost")
        cost_text = "" if cost is None else f" cost={cost}"
        comments.append(
            f"  %% Lane {lane_id} ({state}): {source} -> {target} route {route_text}{cost_text}"
        )
    return comments


def _list_value(value: object) -> list[object]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []
