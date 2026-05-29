import darwin
from darwin.cli.main import main
from darwin.sim.scenarios import validate_scenario_dict


def _minimal_scenario():
    return {
        "scenario_id": "minimal",
        "name": "Minimal",
        "setup": {},
        "steps": [{"action": "advance_time", "ticks": 1}],
        "assertions": [],
    }


def test_validate_valid_scenario_dict():
    result = validate_scenario_dict(_minimal_scenario())

    assert result.passed
    assert result.errors == ()
    assert result.scenario_id == "minimal"


def test_validate_scenario_missing_action_fails():
    scenario = _minimal_scenario()
    scenario["steps"] = [{"ticks": 1}]

    result = validate_scenario_dict(scenario)

    assert not result.passed
    assert "Scenario step 1 requires a non-empty action" in result.errors


def test_cli_list_scenarios(capsys):
    exit_code = main(["list-scenarios"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "001_basic_registration" in captured.out
    assert "Basic registration" in captured.out


def test_cli_validate_scenario(capsys):
    exit_code = main(["validate-scenario", "scenarios/001_basic_registration.yaml"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "VALID 001_basic_registration" in captured.out


def test_cli_run_scenario(capsys):
    exit_code = main(["run", "scenarios/001_basic_registration.yaml"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Result: PASS" in captured.out
    assert "Assertions: 3/3 passed" in captured.out


def test_version_exists():
    assert getattr(darwin, "__version__", "")
