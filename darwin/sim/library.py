"""Scenario library discovery and documentation helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from darwin.sim.presets import ScenarioPresetError, expand_scenario
from darwin.sim.scenarios import list_scenario_files, load_scenario_file
from darwin.sim.validation import ScenarioValidationResult, validate_scenario_data


@dataclass(frozen=True, slots=True)
class ScenarioMetadata:
    scenario_id: str
    name: str
    path: str | None = None
    category: str | None = None
    description: str | None = None
    tags: list[str] = field(default_factory=list)
    demonstrates: list[str] = field(default_factory=list)
    expected_result: str | None = None


@dataclass(frozen=True, slots=True)
class ScenarioDescription:
    metadata: ScenarioMetadata
    setup_counts: dict[str, int]
    step_count: int
    assertion_count: int
    uses_presets: bool
    validation_result: ScenarioValidationResult


def scenario_metadata_from_dict(
    scenario: dict[str, Any],
    path: str | None = None,
) -> ScenarioMetadata:
    """Extract optional library metadata from a raw scenario mapping."""
    scenario_id = _required_text(scenario.get("scenario_id") or scenario.get("id"))
    raw_name = scenario.get("name")
    name = raw_name.strip() if isinstance(raw_name, str) and raw_name.strip() else ""
    if not name:
        name = _infer_name(scenario_id)

    return ScenarioMetadata(
        scenario_id=scenario_id,
        name=name,
        path=path,
        category=_optional_text(scenario.get("category")),
        description=_optional_text(scenario.get("description")),
        tags=_string_list(scenario.get("tags")),
        demonstrates=_string_list(scenario.get("demonstrates")),
        expected_result=_optional_text(scenario.get("expected_result")),
    )


def discover_scenario_metadata(directory: Path) -> list[ScenarioMetadata]:
    """Return metadata for parseable scenario files in deterministic order."""
    metadata: list[ScenarioMetadata] = []
    for path in list_scenario_files(directory):
        data = load_scenario_file(path)
        metadata.append(scenario_metadata_from_dict(data, path=str(path)))
    return sorted(metadata, key=_metadata_sort_key)


def describe_scenario(path: Path) -> ScenarioDescription:
    """Describe one scenario using raw metadata and expanded setup counts."""
    data = load_scenario_file(path)
    metadata = scenario_metadata_from_dict(data, path=str(path))

    try:
        expanded = expand_scenario(data)
    except ScenarioPresetError as exc:
        validation_result = ScenarioValidationResult(
            valid=False,
            errors=exc.errors,
            scenario_id=metadata.scenario_id,
            name=metadata.name,
            path=str(path),
        )
        expanded = data
    else:
        validation_result = validate_scenario_data(expanded, path=str(path))

    return ScenarioDescription(
        metadata=metadata,
        setup_counts=_setup_counts(expanded.get("setup")),
        step_count=_count_list(expanded.get("steps")),
        assertion_count=_count_list(expanded.get("assertions")),
        uses_presets=_uses_presets(data.get("use")),
        validation_result=validation_result,
    )


def scenario_index_markdown(metadata: list[ScenarioMetadata]) -> str:
    """Render a deterministic Markdown scenario index."""
    lines = [
        "# DARWIN Scenario Index",
        "",
        "Scenarios are deterministic, v0.2 supports presets through `use`, "
        "and scenarios are simulator-only.",
        "",
        "| Scenario | Category | Description | Tags |",
        "| --- | --- | --- | --- |",
    ]
    for item in sorted(metadata, key=_metadata_sort_key):
        scenario_label = f"`{_escape_table(item.scenario_id)}` - {_escape_table(item.name)}"
        tags = ", ".join(f"`{_escape_table(tag)}`" for tag in item.tags)
        lines.append(
            "| "
            + " | ".join(
                (
                    scenario_label,
                    _escape_table(item.category or ""),
                    _escape_table(item.description or ""),
                    tags,
                )
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def _setup_counts(setup: Any) -> dict[str, int]:
    if not isinstance(setup, dict):
        return {}
    return {
        section_name: _count_setup_section(section_value)
        for section_name, section_value in sorted(setup.items())
    }


def _count_setup_section(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, list | dict):
        return len(value)
    return 1


def _count_list(value: Any) -> int:
    return len(value) if isinstance(value, list) else 0


def _uses_presets(value: Any) -> bool:
    if isinstance(value, list):
        return bool(value)
    return value is not None


def _required_text(value: Any) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return ""


def _optional_text(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _metadata_sort_key(metadata: ScenarioMetadata) -> tuple[str, str]:
    return (metadata.path or "", metadata.scenario_id)


def _escape_table(value: str) -> str:
    return value.replace("|", r"\|")


def _infer_name(scenario_id: str) -> str:
    candidate = scenario_id
    if "_" in candidate:
        first, rest = candidate.split("_", 1)
        if first.isdigit() and rest:
            candidate = rest
    return candidate.replace("_", " ").strip().title() or scenario_id
