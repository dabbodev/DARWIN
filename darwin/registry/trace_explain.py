"""Deterministic explanation helpers for registry history and audit traces."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def explain_authority_trace(trace_entry: object) -> dict[str, object]:
    """Return a compact explanation for one authority audit trace summary."""
    entry = _entry_dict(trace_entry)
    requested_alias = _optional_str(entry.get("requested_alias"))
    granted_alias = _optional_str(entry.get("granted_alias"))
    target_device = _optional_str(entry.get("target_device"))
    authority_ceiling = _optional_str(entry.get("authority_ceiling"))
    path_hubs = _string_list(entry.get("path_hubs"))
    final_status = _optional_str(entry.get("final_status") or entry.get("status"))

    outcome, reason, summary = _authority_outcome(
        final_status=final_status,
        requested_alias=requested_alias,
        granted_alias=granted_alias,
        terminal_location=_terminal_location(path_hubs, authority_ceiling),
        conflict_detected=bool(entry.get("conflict_detected")),
        policy_denied=bool(entry.get("policy_denied")),
        path_broken=bool(entry.get("path_broken")),
    )
    return {
        "category": "authority_trace",
        "outcome": outcome,
        "summary": summary,
        "reason": reason,
        "requested_alias": requested_alias,
        "granted_alias": granted_alias,
        "target_device": target_device,
        "authority_ceiling": authority_ceiling,
        "path_hubs": path_hubs,
    }


def explain_authority_traces(trace_entries: list[object]) -> list[dict[str, object]]:
    """Return deterministic explanations for authority audit trace summaries."""
    return [explain_authority_trace(trace_entry) for trace_entry in trace_entries]


def explain_alias_history_entry(history_entry: object) -> dict[str, object]:
    """Return a compact explanation for one alias history query result."""
    entry = _entry_dict(history_entry)
    alias = _optional_str(entry.get("alias"))
    target_device = _optional_str(entry.get("target_device_id"))
    status = _optional_str(entry.get("status"))

    if status == "active":
        outcome = "claimed"
        reason = "alias_claimed"
        summary = f"Alias {_display_alias(alias)} was claimed for {_display_device(target_device)}."
    elif status == "released":
        outcome = "released"
        reason = "alias_released"
        summary = f"Alias {_display_alias(alias)} was released."
    elif alias is not None:
        outcome = "partial"
        reason = "partial"
        summary = f"Alias {alias} has an incomplete history explanation."
    else:
        outcome = "partial"
        reason = "partial"
        summary = "Alias <unknown> has an incomplete history explanation."

    return {
        "category": "alias_history",
        "outcome": outcome,
        "summary": summary,
        "reason": reason,
        "alias": alias,
        "target_device": target_device,
        "status": status,
        "approved_by_registry_hub": _optional_str(
            entry.get("approved_by_registry_hub")
        ),
        "requested_alias": _optional_str(entry.get("requested_alias")),
        "granted_alias": _optional_str(entry.get("granted_alias")),
    }


def explain_alias_conflict_entry(conflict_entry: object) -> dict[str, object]:
    """Return a compact explanation for one alias conflict query result."""
    entry = _entry_dict(conflict_entry)
    alias = _optional_str(entry.get("alias"))
    existing_device = _optional_str(entry.get("existing_device_id"))
    requesting_device = _optional_str(entry.get("requesting_device_id"))
    return {
        "category": "alias_conflict",
        "outcome": "conflict",
        "summary": (
            f"Alias {_display_alias(alias)} conflict was observed between "
            f"{_display_device(existing_device)} and {_display_device(requesting_device)}."
        ),
        "reason": "alias_conflict",
        "conflict_id": _optional_str(entry.get("conflict_id")),
        "alias": alias,
        "existing_device": existing_device,
        "requesting_device": requesting_device,
        "status": _optional_str(entry.get("status")),
    }


def explain_quarantine_event_entry(quarantine_entry: object) -> dict[str, object]:
    """Return a compact explanation for one quarantine history query result."""
    entry = _entry_dict(quarantine_entry)
    device_id = _optional_str(entry.get("device_id"))
    reason = _optional_str(entry.get("reason"))
    return {
        "category": "quarantine_event",
        "outcome": "observed",
        "summary": (
            f"Device {_display_device(device_id)} was quarantined for "
            f"{_display_reason(reason)}."
        ),
        "reason": reason,
        "quarantine_key": _optional_str(entry.get("quarantine_key")),
        "device_id": device_id,
        "source_hub_id": _optional_str(entry.get("source_hub_id")),
        "status": _optional_str(entry.get("status")),
        "event_type": _optional_str(entry.get("event_type")),
    }


def _authority_outcome(
    *,
    final_status: str | None,
    requested_alias: str | None,
    granted_alias: str | None,
    terminal_location: str | None,
    conflict_detected: bool,
    policy_denied: bool,
    path_broken: bool,
) -> tuple[str, str, str]:
    alias = _display_alias(requested_alias)
    location = _display_location(terminal_location)
    if final_status == "approved_here":
        return (
            "approved",
            "approved_here",
            f"Alias {alias} was approved at {location}.",
        )
    if final_status == "fallback_granted":
        return (
            "fallback",
            "fallback_granted",
            f"Alias {alias} fell back to {_display_alias(granted_alias)} at {location}.",
        )
    if final_status == "name_taken" or conflict_detected:
        return (
            "conflict",
            "name_taken",
            f"Alias {alias} was denied because it was already taken.",
        )
    if final_status == "policy_denied" or policy_denied:
        return (
            "policy_denied",
            "policy_denied",
            f"Alias {alias} was denied by simulator-local policy.",
        )
    if final_status == "authority_path_broken" or path_broken:
        return (
            "path_broken",
            "authority_path_broken",
            f"Alias {alias} could not be evaluated because the authority path was broken.",
        )
    return (
        "partial",
        "partial",
        f"Alias {alias} has an incomplete authority trace.",
    )


def _entry_dict(entry: object) -> dict[str, Any]:
    if isinstance(entry, Mapping):
        return dict(entry)
    to_dict = getattr(entry, "to_dict", None)
    if callable(to_dict):
        result = to_dict()
        if isinstance(result, Mapping):
            return dict(result)
    return {}


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _terminal_location(
    path_hubs: list[str],
    authority_ceiling: str | None,
) -> str | None:
    if path_hubs:
        return path_hubs[-1]
    return authority_ceiling


def _display_alias(alias: str | None) -> str:
    return alias if alias is not None else "<unknown>"


def _display_device(device_id: str | None) -> str:
    return device_id if device_id is not None else "<unknown>"


def _display_location(location: str | None) -> str:
    return location if location is not None else "<unknown>"


def _display_reason(reason: str | None) -> str:
    return reason if reason is not None else "<unknown>"
