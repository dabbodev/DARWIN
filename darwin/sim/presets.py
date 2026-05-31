"""Built-in scenario setup presets for the v0.2 scenario DSL."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from darwin.sim.validation import ValidationIssue


class ScenarioPresetError(ValueError):
    """Raised when a scenario cannot be expanded from its presets."""

    def __init__(self, errors: list[ValidationIssue]) -> None:
        super().__init__("Scenario preset expansion failed")
        self.errors = tuple(errors)


SETUP_MERGE_KEYS = {
    "devices": ("device_id",),
    "registry_hubs": ("hub_id",),
    "traffic_hubs": ("hub_id",),
    "hybrid_hubs": ("hub_id",),
    "links": ("from", "to"),
}


_BUILTIN_PRESETS: dict[str, dict[str, Any]] = {
    "single_home_network": {
        "setup": {
            "hybrid_hubs": [
                {
                    "hub_id": "hub_home_001",
                    "scope_path": "global.family.home",
                }
            ],
            "devices": [
                {
                    "device_id": "dev_A9F3",
                    "label": "phone",
                    "registry_hub": "hub_home_001",
                    "traffic_hub": "hub_home_001",
                },
                {
                    "device_id": "dev_B2C8",
                    "label": "laptop",
                    "registry_hub": "hub_home_001",
                    "traffic_hub": "hub_home_001",
                },
            ],
        }
    },
    "two_branch_network": {
        "setup": {
            "registry_hubs": [
                {
                    "hub_id": "registry_home",
                    "scope_path": "global.family.home",
                },
                {
                    "hub_id": "registry_office",
                    "scope_path": "global.family.office",
                },
            ],
            "traffic_hubs": [
                {"hub_id": "hub_1"},
                {"hub_id": "hub_2"},
                {"hub_id": "hub_3"},
            ],
            "links": [
                {"from": "hub_1", "to": "hub_2"},
                {"from": "hub_2", "to": "hub_3"},
            ],
            "devices": [
                {
                    "device_id": "dev_A9F3",
                    "label": "phone",
                    "registry_hub": "registry_home",
                    "traffic_hub": "hub_1",
                },
                {
                    "device_id": "dev_B2C8",
                    "label": "laptop",
                    "registry_hub": "registry_office",
                    "traffic_hub": "hub_3",
                },
            ],
        }
    },
    "relocation_network": {
        "setup": {
            "registry_hubs": [
                {
                    "hub_id": "registry_home",
                    "scope_path": "global.family.home",
                },
                {
                    "hub_id": "registry_office",
                    "scope_path": "global.family.office",
                },
            ],
            "traffic_hubs": [
                {"hub_id": "hub_1"},
                {"hub_id": "hub_2"},
                {"hub_id": "hub_3"},
                {"hub_id": "hub_4"},
            ],
            "links": [
                {"from": "hub_1", "to": "hub_2"},
                {"from": "hub_2", "to": "hub_3"},
                {"from": "hub_2", "to": "hub_4"},
            ],
            "devices": [
                {
                    "device_id": "dev_A9F3",
                    "label": "source",
                    "traffic_hub": "hub_1",
                },
                {
                    "device_id": "dev_B2C8",
                    "label": "target",
                    "registry_hub": "registry_home",
                    "traffic_hub": "hub_3",
                },
            ],
        }
    },
}


def list_builtin_presets() -> list[str]:
    """Return available built-in preset names in deterministic order."""
    return sorted(_BUILTIN_PRESETS)


def get_builtin_preset(name: str) -> dict[str, Any]:
    """Return a deep copy of a built-in preset by name."""
    try:
        return deepcopy(_BUILTIN_PRESETS[name])
    except KeyError as exc:
        raise KeyError(f"Unknown scenario preset: {name}") from exc


def expand_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    """Return a deterministic scenario copy with built-in presets expanded."""
    expanded = deepcopy(scenario)
    preset_names = _preset_names(expanded.get("use"))
    if not preset_names:
        return expanded

    setup: dict[str, Any] = {}
    for preset_name in preset_names:
        preset = get_builtin_preset(preset_name)
        setup = merge_scenario_setup(setup, preset.get("setup", {}))

    explicit_setup = expanded.get("setup", {})
    if explicit_setup is None:
        explicit_setup = {}
    if not isinstance(explicit_setup, dict):
        raise ScenarioPresetError(
            [
                ValidationIssue(
                    "Scenario setup must be a mapping",
                    location="setup",
                )
            ]
        )

    expanded["setup"] = merge_scenario_setup(setup, explicit_setup)
    return expanded


def merge_scenario_setup(
    base_setup: dict[str, Any],
    scenario_setup: dict[str, Any],
) -> dict[str, Any]:
    """Merge setup mappings, with scenario entries overriding base entries."""
    merged = deepcopy(base_setup)

    for section_name, section_value in scenario_setup.items():
        if section_name not in SETUP_MERGE_KEYS:
            merged[section_name] = deepcopy(section_value)
            continue

        merged[section_name] = _merge_setup_section(
            merged.get(section_name),
            section_value,
            SETUP_MERGE_KEYS[section_name],
        )

    return merged


def _preset_names(value: Any) -> list[str]:
    if value is None:
        return []

    errors: list[ValidationIssue] = []
    if not isinstance(value, list):
        errors.append(
            ValidationIssue(
                "Scenario use must be a list of preset names",
                location="use",
            )
        )
    else:
        for index, preset_name in enumerate(value):
            location = f"use[{index}]"
            if not isinstance(preset_name, str) or not preset_name.strip():
                errors.append(
                    ValidationIssue(
                        "Scenario preset name must be a non-empty string",
                        location=location,
                    )
                )
                continue
            if preset_name not in _BUILTIN_PRESETS:
                errors.append(
                    ValidationIssue(
                        f"Unknown scenario preset: {preset_name}",
                        location=location,
                        suggestion="Use one of: " + ", ".join(list_builtin_presets()),
                    )
                )

    if errors:
        raise ScenarioPresetError(errors)

    return [preset_name.strip() for preset_name in value]


def _merge_setup_section(
    base_value: Any,
    scenario_value: Any,
    key_fields: tuple[str, ...],
) -> Any:
    if not _is_setup_collection(scenario_value) or not _has_only_mapping_items(
        scenario_value
    ):
        return deepcopy(scenario_value)

    entries: list[dict[str, Any]] = []
    index_by_key: dict[tuple[str, ...], int] = {}

    for entry in _setup_entries(base_value, key_fields):
        index_by_key[_entry_key(entry, key_fields)] = len(entries)
        entries.append(entry)

    for entry in _setup_entries(scenario_value, key_fields):
        key = _entry_key(entry, key_fields)
        if key in index_by_key:
            entries[index_by_key[key]] = entry
        else:
            index_by_key[key] = len(entries)
            entries.append(entry)

    return entries


def _is_setup_collection(value: Any) -> bool:
    return value is None or isinstance(value, list | dict)


def _has_only_mapping_items(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, list):
        return all(isinstance(item, dict) for item in value)
    if isinstance(value, dict):
        return all(isinstance(item, dict) for item in value.values())
    return False


def _setup_entries(value: Any, key_fields: tuple[str, ...]) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, list):
        return [deepcopy(item) for item in value]
    if isinstance(value, dict):
        key_field = key_fields[0]
        entries = []
        for key, raw_item in value.items():
            item = deepcopy(raw_item) if isinstance(raw_item, dict) else {}
            item.setdefault(key_field, key)
            entries.append(item)
        return entries
    return []


def _entry_key(entry: dict[str, Any], key_fields: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(str(entry.get(field_name, "")) for field_name in key_fields)
