import json

from darwin.cli.main import main
from darwin.sim.runner import run_scenario
from darwin.sim.timeline import (
    export_timeline_json,
    export_timeline_markdown,
    filter_timeline,
    scenario_result_to_timeline,
    timeline_to_markdown,
)


def _simple_scenario():
    return {
        "scenario_id": "timeline_test",
        "name": "Timeline test",
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


def _lane_scenario():
    return {
        "scenario_id": "timeline_lane_test",
        "setup": {
            "traffic_hubs": [
                {"hub_id": "hub_1"},
                {"hub_id": "hub_2"},
                {"hub_id": "hub_3"},
            ],
            "links": [{"from": "hub_1", "to": "hub_2"}, {"from": "hub_2", "to": "hub_3"}],
            "devices": [
                {"device_id": "dev_A9F3", "label": "source", "traffic_hub": "hub_1"},
                {"device_id": "dev_B2C8", "label": "target", "traffic_hub": "hub_3"},
            ],
        },
        "steps": [
            {
                "action": "open_lane",
                "source": "dev_A9F3",
                "target": "dev_B2C8",
                "traffic_hub": "hub_1",
                "lane_id": "lane_001",
            },
            {
                "action": "send_lane_data",
                "traffic_hub": "hub_1",
                "lane": "lane_001",
                "payload": {"message": "first"},
            },
        ],
        "assertions": [
            {
                "type": "lane_state",
                "traffic_hub": "hub_1",
                "lane": "lane_001",
                "expected": "active",
            }
        ],
    }


def test_scenario_result_to_timeline_records_events():
    result = run_scenario(_simple_scenario())

    timeline = scenario_result_to_timeline(result)

    assert timeline
    assert isinstance(timeline[0].time, int)
    assert timeline[0].message


def test_timeline_markdown_contains_table():
    result = run_scenario(_simple_scenario())
    timeline = scenario_result_to_timeline(result)

    markdown = timeline_to_markdown(timeline, title="Timeline: timeline_test")

    assert "| time | event type | actor/target | status | message |" in markdown
    assert "Timeline: timeline_test" in markdown
    assert "registered dev_A9F3" in markdown


def test_timeline_json_export(tmp_path):
    result = run_scenario(_simple_scenario())
    export_path = tmp_path / "timeline.json"

    export_timeline_json(result, export_path)

    data = json.loads(export_path.read_text(encoding="utf-8"))
    assert export_path.exists()
    assert isinstance(data, list)
    assert data[0]["message"]


def test_timeline_markdown_export(tmp_path):
    result = run_scenario(_simple_scenario())
    export_path = tmp_path / "timeline.md"

    export_timeline_markdown(result, export_path)

    markdown = export_path.read_text(encoding="utf-8")
    assert export_path.exists()
    assert "| time | event type | actor/target | status | message |" in markdown
    assert "registered dev_A9F3" in markdown


def test_timeline_filter_by_event_type():
    result = run_scenario(_lane_scenario())
    timeline = scenario_result_to_timeline(result)

    filtered = filter_timeline(timeline, event_type="lane_opened")

    assert filtered
    assert all(record.event_type == "lane_opened" for record in filtered)


def test_timeline_filter_by_lane():
    result = run_scenario(_lane_scenario())
    timeline = scenario_result_to_timeline(result)

    filtered = filter_timeline(timeline, lane_id="lane_001")

    assert filtered
    assert all(
        record.lane_id == "lane_001" or "lane_001" in json.dumps(record.data, sort_keys=True)
        for record in filtered
    )


def test_cli_run_with_timeline_exports(tmp_path, capsys):
    json_path = tmp_path / "timeline" / "trace.json"
    markdown_path = tmp_path / "timeline" / "trace.md"

    exit_code = main(
        [
            "run",
            "scenarios/003_lane_open_and_send.yaml",
            "--export-timeline-json",
            str(json_path),
            "--export-timeline-md",
            str(markdown_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Result: PASS" in captured.out
    assert json_path.exists()
    assert markdown_path.exists()
    assert isinstance(json.loads(json_path.read_text(encoding="utf-8")), list)
    assert "| time | event type | actor/target | status | message |" in markdown_path.read_text(
        encoding="utf-8"
    )
