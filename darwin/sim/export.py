"""Deterministic export helpers for scenario runs."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from darwin.sim.runner import ScenarioRunResult
from darwin.sim.timeline import (
    export_timeline_json,
    export_timeline_markdown,
    filter_timeline,
    scenario_result_to_timeline,
    timeline_to_jsonable,
    timeline_to_markdown,
)
from darwin.sim.visualize import scenario_result_to_mermaid, write_mermaid

__all__ = [
    "event_log_to_jsonable",
    "snapshot_to_jsonable",
    "result_to_jsonable",
    "export_events",
    "export_snapshot",
    "export_result",
    "export_mermaid",
    "write_json",
    "scenario_result_to_timeline",
    "timeline_to_jsonable",
    "timeline_to_markdown",
    "filter_timeline",
    "export_timeline_json",
    "export_timeline_markdown",
]


def event_log_to_jsonable(result: ScenarioRunResult) -> list[dict[str, object]]:
    """Return structured event log entries in deterministic order."""
    entries = result.world.event_log.entries
    records = timeline_to_jsonable(scenario_result_to_timeline(result))
    for record, entry in zip(records, entries, strict=True):
        record["line"] = entry.render()
    return records


def snapshot_to_jsonable(result: ScenarioRunResult) -> dict[str, object]:
    """Return the final detailed snapshot for JSON export."""
    return result.final_snapshot


def result_to_jsonable(result: ScenarioRunResult) -> dict[str, object]:
    """Return a compact full scenario result summary for JSON export."""
    return {
        "scenario_id": result.scenario_id,
        "passed": result.passed,
        "assertion_results": [
            asdict(assertion_result)
            for assertion_result in result.assertion_results
        ],
        "events": event_log_to_jsonable(result),
        "final_snapshot": snapshot_to_jsonable(result),
    }


def export_events(result: ScenarioRunResult, path: str | Path) -> None:
    write_json(path, event_log_to_jsonable(result))


def export_snapshot(result: ScenarioRunResult, path: str | Path) -> None:
    write_json(path, snapshot_to_jsonable(result))


def export_result(result: ScenarioRunResult, path: str | Path) -> None:
    write_json(path, result_to_jsonable(result))


def export_mermaid(
    result: ScenarioRunResult,
    path: str | Path,
    *,
    include_devices: bool = True,
    include_lanes: bool = True,
) -> None:
    write_mermaid(
        path,
        scenario_result_to_mermaid(
            result,
            include_devices=include_devices,
            include_lanes=include_lanes,
        ),
    )


def write_json(path: str | Path, data: Any) -> None:
    export_path = Path(path)
    export_path.parent.mkdir(parents=True, exist_ok=True)
    export_path.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
