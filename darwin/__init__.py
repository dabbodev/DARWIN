"""DARWIN simulator package.

DARWIN stands for Direct-Access Registration Window Interface Network.
This package is intentionally simulator-first: behavior now, real networking
and production cryptography later.
"""

from darwin.models.device import Device
from darwin.models.hub import RegistryHub, TrafficHub
from darwin.sim.runner import ScenarioRunResult, run_scenario
from darwin.sim.scenarios import (
    Scenario,
    ScenarioStep,
    ScenarioValidationResult,
    load_scenario,
    validate_scenario_dict,
    validate_scenario_file,
)
from darwin.sim.world import World

__all__ = [
    "Device",
    "RegistryHub",
    "Scenario",
    "ScenarioRunResult",
    "ScenarioStep",
    "ScenarioValidationResult",
    "TrafficHub",
    "World",
    "__version__",
    "load_scenario",
    "run_scenario",
    "validate_scenario_dict",
    "validate_scenario_file",
]

__version__ = "0.1.0"
