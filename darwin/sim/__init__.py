"""Public simulator helpers for DARWIN v0.1."""

from darwin.sim.assertions import AssertionResult, evaluate_assertions
from darwin.sim.presets import (
    expand_scenario,
    get_builtin_preset,
    list_builtin_presets,
    merge_scenario_setup,
)
from darwin.sim.runner import ScenarioRunResult, run_scenario, run_scenario_dict
from darwin.sim.scenarios import (
    Scenario,
    ScenarioLoadError,
    ScenarioStep,
    ScenarioValidationResult,
    list_scenario_files,
    load_scenario,
    load_scenario_file,
    validate_scenario_dict,
    validate_scenario_file,
)
from darwin.sim.visualize import scenario_result_to_mermaid, snapshot_to_mermaid, world_to_mermaid
from darwin.sim.world import World

__all__ = [
    "AssertionResult",
    "Scenario",
    "ScenarioLoadError",
    "ScenarioRunResult",
    "ScenarioStep",
    "ScenarioValidationResult",
    "World",
    "evaluate_assertions",
    "expand_scenario",
    "get_builtin_preset",
    "list_scenario_files",
    "list_builtin_presets",
    "load_scenario",
    "load_scenario_file",
    "merge_scenario_setup",
    "run_scenario",
    "run_scenario_dict",
    "scenario_result_to_mermaid",
    "snapshot_to_mermaid",
    "validate_scenario_dict",
    "validate_scenario_file",
    "world_to_mermaid",
]
