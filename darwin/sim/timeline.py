"""Structured timeline adapters and deterministic trace exports."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Any

from darwin.sim.assertions import AssertionResult
from darwin.sim.runner import ScenarioRunResult


@dataclass(frozen=True, slots=True)
class TimelineRecord:
    """One structured, JSON-safe trace event."""

    time: int
    event_type: str
    message: str
    actor: str | None = None
    target: str | None = None
    device_id: str | None = None
    hub_id: str | None = None
    lane_id: str | None = None
    status: str | None = None
    data: dict[str, Any] | None = None


def scenario_result_to_timeline(result: ScenarioRunResult) -> list[TimelineRecord]:
    """Convert a scenario run result into deterministic timeline records."""
    records: list[TimelineRecord] = []
    for entry in result.world.event_log.entries:
        records.append(
            TimelineRecord(
                time=entry.time,
                event_type=entry.event_type or "event",
                actor=entry.actor,
                target=entry.target,
                device_id=entry.device_id,
                hub_id=entry.hub_id,
                lane_id=entry.lane_id,
                status=entry.status,
                message=entry.message,
                data=_json_safe_dict(entry.data),
            )
        )
    return records


def timeline_to_jsonable(timeline: list[TimelineRecord]) -> list[dict[str, Any]]:
    """Return timeline records as deterministic JSON-safe dictionaries."""
    return [
        {
            "time": record.time,
            "event_type": record.event_type,
            "actor": record.actor,
            "target": record.target,
            "device_id": record.device_id,
            "hub_id": record.hub_id,
            "lane_id": record.lane_id,
            "status": record.status,
            "message": record.message,
            "data": _json_safe_dict(record.data or {}),
        }
        for record in timeline
    ]


def timeline_to_markdown(
    timeline: list[TimelineRecord],
    title: str | None = None,
    *,
    failed_assertions: list[AssertionResult] | None = None,
) -> str:
    """Render a concise timeline table as Markdown."""
    heading = title or "Timeline"
    lines = [
        f"# {_escape_markdown_text(heading)}",
        "",
        "| time | event type | actor/target | status | message |",
        "| ---: | --- | --- | --- | --- |",
    ]

    for record in timeline:
        actor_target = _actor_target(record.actor, record.target)
        lines.append(
            "| "
            f"{record.time} | "
            f"{_escape_table_cell(record.event_type)} | "
            f"{_escape_table_cell(actor_target)} | "
            f"{_escape_table_cell(record.status or '')} | "
            f"{_escape_table_cell(record.message)} |"
        )

    failed = [assertion for assertion in failed_assertions or [] if not assertion.passed]
    if failed:
        lines.extend([
            "",
            "## Failed Assertions",
            "",
            "| assertion | expected | actual | message |",
            "| --- | --- | --- | --- |",
        ])
        for assertion in failed:
            lines.append(
                "| "
                f"{_escape_table_cell(assertion.assertion_type)} | "
                f"{_escape_table_cell(_json_safe(assertion.expected))} | "
                f"{_escape_table_cell(_json_safe(assertion.actual))} | "
                f"{_escape_table_cell(assertion.message)} |"
            )

    return "\n".join(lines) + "\n"


def filter_timeline(
    timeline: list[TimelineRecord],
    *,
    event_type: str | None = None,
    device_id: str | None = None,
    lane_id: str | None = None,
    hub_id: str | None = None,
) -> list[TimelineRecord]:
    """Return records matching all supplied simple trace filters."""
    return [
        record
        for record in timeline
        if _matches_event_type(record, event_type)
        and _matches_identifier(record, "device_id", device_id)
        and _matches_identifier(record, "lane_id", lane_id)
        and _matches_identifier(record, "hub_id", hub_id)
    ]


def export_timeline_json(
    result: ScenarioRunResult,
    path: str | Path,
    **filters: str | None,
) -> None:
    """Write a deterministic structured timeline JSON export."""
    timeline = filter_timeline(scenario_result_to_timeline(result), **filters)
    _write_json(path, timeline_to_jsonable(timeline))


def export_timeline_markdown(
    result: ScenarioRunResult,
    path: str | Path,
    **filters: str | None,
) -> None:
    """Write a deterministic structured timeline Markdown export."""
    timeline = filter_timeline(scenario_result_to_timeline(result), **filters)
    title = f"Timeline: {result.scenario_id}"
    failed_assertions = None if result.passed else result.assertion_results
    export_path = Path(path)
    export_path.parent.mkdir(parents=True, exist_ok=True)
    export_path.write_text(
        timeline_to_markdown(
            timeline,
            title=title,
            failed_assertions=failed_assertions,
        ),
        encoding="utf-8",
    )


def _matches_event_type(record: TimelineRecord, event_type: str | None) -> bool:
    return event_type is None or record.event_type == event_type


def _matches_identifier(record: TimelineRecord, field_name: str, expected: str | None) -> bool:
    if expected is None:
        return True
    structured_value = getattr(record, field_name)
    if structured_value == expected:
        return True
    if field_name == "device_id" and expected in {record.actor, record.target}:
        return True
    return _contains_value(record.data or {}, expected)


def _contains_value(value: Any, expected: str) -> bool:
    if value == expected:
        return True
    if isinstance(value, dict):
        return any(_contains_value(item, expected) for item in value.values())
    if isinstance(value, list | tuple | set):
        return any(_contains_value(item, expected) for item in value)
    return False


def _actor_target(actor: str | None, target: str | None) -> str:
    if actor and target:
        return f"{actor} -> {target}"
    return actor or target or ""


def _write_json(path: str | Path, data: Any) -> None:
    export_path = Path(path)
    export_path.parent.mkdir(parents=True, exist_ok=True)
    export_path.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _json_safe_dict(value: dict[str, Any] | None) -> dict[str, Any]:
    return dict(_json_safe(value or {}))


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if is_dataclass(value) and not isinstance(value, type):
        return _json_safe(asdict(value))
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in sorted(value.items())}
    if isinstance(value, list | tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return sorted(_json_safe(item) for item in value)
    return str(value)


def _escape_markdown_text(value: Any) -> str:
    return str(value).replace("\n", " ")


def _escape_table_cell(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", "<br>")
