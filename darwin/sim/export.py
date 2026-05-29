"""Deterministic JSON export helpers for scenario runs."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from darwin.sim.runner import ScenarioRunResult


def event_log_to_jsonable(result: ScenarioRunResult) -> list[dict[str, object]]:
    """Return structured event log entries in deterministic order."""
    return [
        {
            "time": entry.time,
            "event_type": entry.event_type,
            "message": entry.message,
            "line": entry.render(),
        }
        for entry in result.world.event_log.entries
    ]


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


def write_json(path: str | Path, data: Any) -> None:
    export_path = Path(path)
    export_path.parent.mkdir(parents=True, exist_ok=True)
    export_path.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
