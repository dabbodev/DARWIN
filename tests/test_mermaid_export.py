from darwin.cli.main import main
from darwin.sim.export import export_events, export_mermaid, export_result, export_snapshot
from darwin.sim.runner import run_scenario
from darwin.sim.visualize import snapshot_to_mermaid


def _traffic_snapshot():
    return {
        "traffic_hubs": {
            "hub_1": {
                "neighbors": ["hub_2"],
                "direct_attachments": {
                    "dev_A9F3": {
                        "hub_id": "hub_1",
                        "status": "attached",
                        "attachment_type": "direct",
                    }
                },
            },
            "hub_2": {"neighbors": ["hub_1"], "direct_attachments": {}},
        },
        "devices": {
            "dev_A9F3": {
                "current_traffic_hub": "hub_1",
            }
        },
        "lanes": {},
    }


def test_snapshot_to_mermaid_contains_flowchart():
    mermaid = snapshot_to_mermaid(_traffic_snapshot())

    assert mermaid.startswith("flowchart LR")


def test_mermaid_includes_traffic_hubs_and_links():
    mermaid = snapshot_to_mermaid(_traffic_snapshot())

    assert 'hub_1["TrafficHub: hub_1"]' in mermaid
    assert 'hub_2["TrafficHub: hub_2"]' in mermaid
    assert "hub_1 --- hub_2" in mermaid


def test_mermaid_includes_attached_devices():
    mermaid = snapshot_to_mermaid(_traffic_snapshot())

    assert 'dev_A9F3["Device: dev_A9F3"]' in mermaid
    assert "hub_1 --> dev_A9F3" in mermaid


def test_mermaid_includes_lane_route_when_available():
    result = run_scenario("scenarios/003_lane_open_and_send.yaml")

    mermaid = snapshot_to_mermaid(result.final_snapshot, include_lanes=True)

    assert "%% Lane lane_001 (active)" in mermaid
    assert "route hub_1 -> hub_2 -> hub_3" in mermaid


def test_mermaid_sanitizes_node_ids():
    snapshot = {
        "traffic_hubs": {
            "hub.alpha-1": {
                "neighbors": [],
                "direct_attachments": {"dev-A.1": {}},
            }
        },
        "devices": {},
        "lanes": {},
    }

    mermaid = snapshot_to_mermaid(snapshot)

    assert 'hub_alpha_1["TrafficHub: hub.alpha-1"]' in mermaid
    assert 'dev_A_1["Device: dev-A.1"]' in mermaid
    assert "hub.alpha-1[" not in mermaid


def test_export_mermaid_file(tmp_path):
    result = run_scenario("scenarios/003_lane_open_and_send.yaml")
    export_path = tmp_path / "nested" / "diagram.mmd"

    export_mermaid(result, export_path)

    assert export_path.exists()
    assert export_path.read_text(encoding="utf-8").startswith("flowchart LR")


def test_cli_run_with_export_mermaid(tmp_path, capsys):
    export_path = tmp_path / "cli" / "diagram.mmd"

    exit_code = main(
        [
            "run",
            "scenarios/003_lane_open_and_send.yaml",
            "--export-mermaid",
            str(export_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Result: PASS" in captured.out
    assert export_path.exists()
    assert export_path.read_text(encoding="utf-8").startswith("flowchart LR")


def test_existing_scenario_exports_still_work(tmp_path):
    result = run_scenario("scenarios/001_basic_registration.yaml")
    snapshot_path = tmp_path / "snapshot.json"
    events_path = tmp_path / "events.json"
    result_path = tmp_path / "result.json"

    export_snapshot(result, snapshot_path)
    export_events(result, events_path)
    export_result(result, result_path)

    assert snapshot_path.exists()
    assert events_path.exists()
    assert result_path.exists()
