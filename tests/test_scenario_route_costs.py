from darwin.sim.runner import run_scenario
from darwin.sim.scenarios import validate_scenario_dict


def _route_cost_scenario():
    return {
        "scenario_id": "route_cost_selection",
        "name": "Route cost selection",
        "setup": {
            "traffic_hubs": [
                {"hub_id": "hub_1"},
                {"hub_id": "hub_2"},
                {"hub_id": "hub_3"},
                {"hub_id": "hub_4"},
                {"hub_id": "hub_5"},
            ],
            "links": [
                {
                    "from": "hub_1",
                    "to": "hub_2",
                    "latency_ms": 100,
                    "congestion": "high",
                    "trust": "verified",
                    "stability": "stable",
                },
                {
                    "from": "hub_2",
                    "to": "hub_4",
                    "latency_ms": 100,
                    "congestion": "high",
                    "trust": "verified",
                    "stability": "stable",
                },
                {
                    "from": "hub_1",
                    "to": "hub_3",
                    "latency_ms": 1,
                    "congestion": "low",
                    "trust": "verified",
                    "stability": "stable",
                },
                {
                    "from": "hub_3",
                    "to": "hub_5",
                    "latency_ms": 1,
                    "congestion": "low",
                    "trust": "verified",
                    "stability": "stable",
                },
                {
                    "from": "hub_5",
                    "to": "hub_4",
                    "latency_ms": 1,
                    "congestion": "low",
                    "trust": "verified",
                    "stability": "stable",
                },
            ],
            "devices": [
                {"device_id": "dev_source", "label": "source", "traffic_hub": "hub_1"},
                {"device_id": "dev_target", "label": "target", "traffic_hub": "hub_4"},
            ],
        },
        "steps": [
            {
                "action": "open_lane",
                "source": "dev_source",
                "target": "dev_target",
                "traffic_hub": "hub_1",
                "lane_id": "lane_001",
            }
        ],
        "assertions": [
            {
                "type": "route_for_lane",
                "traffic_hub": "hub_1",
                "lane": "lane_001",
                "expected_route": ["hub_1", "hub_3", "hub_5", "hub_4"],
            }
        ],
    }


def test_scenario_link_metrics_validate():
    result = validate_scenario_dict(_route_cost_scenario())

    assert result.valid


def test_scenario_route_cost_selection():
    result = run_scenario(_route_cost_scenario())

    assert result.passed
    lane = result.final_snapshot["lanes"]["lane_001"]
    assert lane["route"] == ["hub_1", "hub_3", "hub_5", "hub_4"]
    assert lane["route_total_cost"] is not None
    assert lane["route_total_cost"] < 20
