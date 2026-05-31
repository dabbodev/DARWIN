import json

from darwin.cli.main import main
from darwin.sim.export import export_events, export_result, export_snapshot
from darwin.sim.runner import run_scenario


def _simple_scenario():
    return {
        "scenario_id": "export_test",
        "name": "Export test",
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


def test_export_snapshot_json(tmp_path):
    result = run_scenario(_simple_scenario())
    export_path = tmp_path / "nested" / "snapshot.json"

    export_snapshot(result, export_path)

    data = json.loads(export_path.read_text(encoding="utf-8"))
    assert data["current_time"] == 1
    assert "dev_A9F3" in data["devices"]


def test_export_events_json(tmp_path):
    result = run_scenario(_simple_scenario())
    export_path = tmp_path / "events.json"

    export_events(result, export_path)

    data = json.loads(export_path.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert data
    assert data[0]["event_type"] == "registered_device"


def test_export_result_json(tmp_path):
    result = run_scenario(_simple_scenario())
    export_path = tmp_path / "result.json"

    export_result(result, export_path)

    data = json.loads(export_path.read_text(encoding="utf-8"))
    assert data["scenario_id"] == "export_test"
    assert data["passed"] is True
    assert data["events"]
    assert data["final_snapshot"]["current_time"] == 1


def test_cli_run_with_export_snapshot(tmp_path, capsys):
    export_path = tmp_path / "cli" / "snapshot.json"

    exit_code = main(
        [
            "run",
            "scenarios/001_basic_registration.yaml",
            "--export-snapshot",
            str(export_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Result: PASS" in captured.out
    assert export_path.exists()


def test_invalid_scenario_does_not_export(tmp_path, capsys):
    scenario_path = tmp_path / "invalid.json"
    export_path = tmp_path / "snapshot.json"
    scenario_path.write_text(
        json.dumps(
            {
                "scenario_id": "invalid_export",
                "setup": {},
                "steps": [{"device": "dev_A9F3"}],
                "assertions": [],
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "run",
            str(scenario_path),
            "--export-snapshot",
            str(export_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "INVALID" in captured.err
    assert not export_path.exists()
