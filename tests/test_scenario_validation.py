from pathlib import Path

from darwin.sim.scenarios import list_scenario_files, validate_scenario_dict
from darwin.sim.validation import ASSERTION_REQUIRED_FIELDS, STEP_REQUIRED_FIELDS

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_DIR = PROJECT_ROOT / "scenarios"


def _valid_scenario():
    return {
        "scenario_id": "validation_test",
        "name": "Validation test",
        "setup": {
            "registry_hubs": [
                {"hub_id": "hub_home_001", "scope_path": "global.family.home"}
            ],
            "devices": [{"device_id": "dev_A9F3", "label": "pc"}],
        },
        "steps": [
            {
                "action": "register_device",
                "device": "dev_A9F3",
                "registry_hub": "hub_home_001",
            }
        ],
        "assertions": [
            {
                "type": "device_registered",
                "registry_hub": "hub_home_001",
                "device": "dev_A9F3",
            }
        ],
    }


def test_validation_reports_missing_step_action():
    scenario = _valid_scenario()
    scenario["steps"] = [{"device": "dev_A9F3"}]

    result = validate_scenario_dict(scenario)

    assert not result.valid
    assert result.errors[0].location == "steps[0].action"
    assert "action" in result.errors[0].message


def test_validation_reports_unknown_step_action():
    scenario = _valid_scenario()
    scenario["steps"] = [{"action": "teleport_device"}]

    result = validate_scenario_dict(scenario)

    assert not result.valid
    assert result.errors[0].location == "steps[0].action"
    assert "Unknown scenario step action" in result.errors[0].message
    assert "teleport_device" in result.errors[0].message


def test_validation_reports_missing_required_step_field():
    scenario = _valid_scenario()
    scenario["steps"] = [{"action": "register_device", "device": "dev_A9F3"}]

    result = validate_scenario_dict(scenario)

    assert not result.valid
    assert result.errors[0].location == "steps[0].registry_hub"
    assert "Missing required step field: registry_hub" in result.errors[0].message
    assert result.errors[0].suggestion


def test_validation_reports_unknown_assertion_type():
    scenario = _valid_scenario()
    scenario["assertions"] = [{"type": "magic_assertion"}]

    result = validate_scenario_dict(scenario)

    assert not result.valid
    assert result.errors[0].location == "assertions[0].type"
    assert "Unknown assertion type" in result.errors[0].message
    assert "magic_assertion" in result.errors[0].message


def test_valid_v01_scenarios_still_validate():
    scenario_files = list_scenario_files(SCENARIOS_DIR)

    failures = []
    for scenario_file in scenario_files:
        result = validate_scenario_dict(_load_yaml(scenario_file), path=str(scenario_file))
        if not result.valid:
            failures.append(f"{scenario_file}: {result.errors}")

    assert scenario_files
    assert not failures


def test_validation_tables_cover_expected_v02_minimums():
    assert "register_device" in STEP_REQUIRED_FIELDS
    assert "recommend_traffic_bridge" in STEP_REQUIRED_FIELDS
    assert "device_registered" in ASSERTION_REQUIRED_FIELDS
    assert "recommendation_exists" in ASSERTION_REQUIRED_FIELDS


def _load_yaml(path: Path):
    import yaml

    return yaml.safe_load(path.read_text(encoding="utf-8"))
