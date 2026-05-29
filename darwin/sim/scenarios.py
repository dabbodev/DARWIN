"""Scenario parsing for the deterministic v0.1 runner."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from darwin.sim.validation import (
    ScenarioValidationResult,
    ValidationIssue,
    validate_scenario_data,
)


class ScenarioLoadError(ValueError):
    """Raised when scenario input cannot be parsed."""


class YamlSupportMissingError(ScenarioLoadError):
    """Raised when a YAML file is requested but PyYAML is unavailable."""


@dataclass(frozen=True, slots=True)
class ScenarioStep:
    action: str
    fields: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Scenario:
    scenario_id: str
    name: str = ""
    setup: dict[str, Any] = field(default_factory=dict)
    steps: list[ScenarioStep] = field(default_factory=list)
    assertions: list[dict[str, Any]] = field(default_factory=list)


def load_scenario(source: Scenario | dict[str, Any] | str | Path) -> Scenario:
    """Load a scenario from a dataclass, Python dict, JSON file, or YAML file."""
    if isinstance(source, Scenario):
        return source
    if isinstance(source, dict):
        return scenario_from_dict(source)

    path = Path(source)
    data = load_scenario_file(path)
    return scenario_from_dict(data)


def load_scenario_file(path: str | Path) -> dict[str, Any]:
    scenario_path = Path(path)
    if not scenario_path.exists():
        raise FileNotFoundError(scenario_path)

    suffix = scenario_path.suffix.lower()
    text = scenario_path.read_text(encoding="utf-8")
    if suffix == ".json":
        data = json.loads(text)
    elif suffix in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError as exc:
            raise YamlSupportMissingError(
                "PyYAML is required to load YAML scenario files"
            ) from exc
        data = yaml.safe_load(text)
    else:
        raise ScenarioLoadError(f"Unsupported scenario file extension: {suffix}")

    if not isinstance(data, dict):
        raise ScenarioLoadError("Scenario file must contain a mapping at the top level")
    return data


def validate_scenario_file(path: str | Path) -> ScenarioValidationResult:
    """Parse and validate a scenario file without executing it."""
    scenario_path = Path(path)
    try:
        data = load_scenario_file(scenario_path)
    except (OSError, json.JSONDecodeError, ScenarioLoadError) as exc:
        return ScenarioValidationResult(
            valid=False,
            errors=(
                ValidationIssue(str(exc), location="$"),
            ),
            path=str(scenario_path),
        )
    return validate_scenario_dict(data, path=str(scenario_path))


def validate_scenario_dict(
    data: dict[str, Any],
    *,
    path: str | None = None,
) -> ScenarioValidationResult:
    """Validate the v0.1 scenario shape without running scenario steps."""
    return validate_scenario_data(data, path=path)


def list_scenario_files(directory: str | Path) -> list[Path]:
    """Return scenario YAML and JSON files from a directory in deterministic order."""
    scenario_dir = Path(directory)
    if not scenario_dir.exists():
        return []
    return sorted(
        path
        for path in scenario_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".yaml", ".yml", ".json"}
    )


def scenario_from_dict(data: dict[str, Any]) -> Scenario:
    scenario_id = data.get("scenario_id") or data.get("id")
    if not isinstance(scenario_id, str) or not scenario_id:
        raise ScenarioLoadError("Scenario requires a non-empty scenario_id")

    return Scenario(
        scenario_id=scenario_id,
        name=str(data.get("name", "")),
        setup=_mapping(data.get("setup", {}), "setup"),
        steps=[_step_from_dict(step) for step in _list(data.get("steps", []), "steps")],
        assertions=[
            _mapping(assertion, "assertion")
            for assertion in _list(data.get("assertions", []), "assertions")
        ],
    )


def _step_from_dict(data: Any) -> ScenarioStep:
    step = _mapping(data, "step")
    action = step.get("action")
    if not isinstance(action, str) or not action:
        raise ScenarioLoadError("Scenario step requires a non-empty action")

    fields = dict(step)
    del fields["action"]
    return ScenarioStep(action=action, fields=fields)


def _mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ScenarioLoadError(f"Scenario {name} must be a mapping")
    return value


def _list(value: Any, name: str) -> list[Any]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ScenarioLoadError(f"Scenario {name} must be a list")
    return value


def _infer_name(scenario_id: str) -> str:
    candidate = scenario_id
    if "_" in candidate:
        first, rest = candidate.split("_", 1)
        if first.isdigit() and rest:
            candidate = rest
    return candidate.replace("_", " ").strip().title() or scenario_id
