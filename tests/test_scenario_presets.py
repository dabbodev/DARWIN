from copy import deepcopy
from pathlib import Path

from darwin.cli.main import main
from darwin.sim.presets import expand_scenario, list_builtin_presets
from darwin.sim.runner import run_scenario
from darwin.sim.scenarios import list_scenario_files, load_scenario_file, validate_scenario_dict

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_DIR = PROJECT_ROOT / "scenarios"


def test_list_builtin_presets():
    assert "two_branch_network" in list_builtin_presets()


def test_expand_scenario_with_preset_adds_setup():
    expanded = expand_scenario(
        {
            "scenario_id": "preset_test",
            "name": "Preset test",
            "use": ["two_branch_network"],
            "steps": [],
            "assertions": [],
        }
    )

    setup = expanded["setup"]
    assert {"hub_id": "registry_home", "scope_path": "global.family.home"} in setup[
        "registry_hubs"
    ]
    assert {"hub_id": "hub_2"} in setup["traffic_hubs"]
    assert {"from": "hub_1", "to": "hub_2"} in setup["links"]
    assert any(device["device_id"] == "dev_A9F3" for device in setup["devices"])


def test_explicit_setup_overrides_preset_device():
    expanded = expand_scenario(
        {
            "scenario_id": "preset_override_test",
            "name": "Preset override test",
            "use": ["two_branch_network"],
            "setup": {
                "devices": [
                    {
                        "device_id": "dev_A9F3",
                        "label": "tablet",
                        "registry_hub": "registry_home",
                        "traffic_hub": "hub_1",
                    }
                ]
            },
            "steps": [],
            "assertions": [],
        }
    )

    devices = {
        device["device_id"]: device
        for device in expanded["setup"]["devices"]
    }
    assert devices["dev_A9F3"]["label"] == "tablet"


def test_unknown_preset_validation_fails():
    result = validate_scenario_dict(
        {
            "scenario_id": "missing_preset_test",
            "name": "Missing preset test",
            "use": ["missing_preset"],
            "steps": [],
            "assertions": [],
        }
    )

    assert not result.valid
    assert result.errors[0].location == "use[0]"
    assert "Unknown scenario preset" in result.errors[0].message


def test_existing_scenarios_still_validate_and_run():
    failures = []
    for scenario_file in list_scenario_files(SCENARIOS_DIR):
        validation = validate_scenario_dict(load_scenario_file(scenario_file))
        if not validation.valid:
            failures.append(f"{scenario_file}: {validation.errors}")
            continue

        result = run_scenario(scenario_file)
        if not result.passed:
            failures.append(f"{scenario_file}: scenario failed")

    assert not failures


def test_preset_scenario_runs():
    result = run_scenario(SCENARIOS_DIR / "011_preset_lane_demo.yaml")

    assert result.passed


def test_cli_list_presets(capsys):
    exit_code = main(["list-presets"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "two_branch_network" in captured.out


def test_cli_expand_scenario(capsys):
    exit_code = main(["expand-scenario", "scenarios/011_preset_lane_demo.yaml"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "setup:" in captured.out or '"setup"' in captured.out
    assert "registry_home" in captured.out
    assert "hub_2" in captured.out


def test_expand_does_not_mutate_original_scenario():
    scenario = {
        "scenario_id": "mutation_test",
        "name": "Mutation test",
        "use": ["two_branch_network"],
        "setup": {
            "devices": [
                {
                    "device_id": "dev_A9F3",
                    "label": "tablet",
                    "registry_hub": "registry_home",
                    "traffic_hub": "hub_1",
                }
            ]
        },
        "steps": [],
        "assertions": [],
    }
    original = deepcopy(scenario)

    expand_scenario(scenario)

    assert scenario == original
