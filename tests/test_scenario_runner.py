from pathlib import Path

import pytest

from darwin.models.device import Device
from darwin.sim.runner import run_scenario
from darwin.sim.scenarios import YamlSupportMissingError
from darwin.sim.world import World


def test_world_can_create_hubs_devices_and_links():
    world = World()
    world.create_traffic_hub("hub_1")
    world.create_traffic_hub("hub_2")
    world.connect_traffic_hubs("hub_1", "hub_2")
    world.add_device(Device(device_id="dev_A9F3", label="source"))
    world.attach_device_to_traffic("dev_A9F3", "hub_1")

    assert "hub_2" in world.traffic_hubs["hub_1"].neighbors
    assert "hub_1" in world.traffic_hubs["hub_2"].neighbors
    assert "dev_A9F3" in world.devices
    assert "dev_A9F3" in world.traffic_hubs["hub_1"].direct_attachments


def test_run_basic_registration_scenario_dict():
    result = run_scenario({
        "scenario_id": "basic_registration",
        "setup": {
            "registry_hubs": [
                {"hub_id": "hub_home_001", "scope_path": "global.family.david.home"}
            ],
            "devices": [{"device_id": "dev_A9F3", "label": "my_pc"}],
        },
        "steps": [
            {
                "action": "register_device",
                "device": "dev_A9F3",
                "registry_hub": "hub_home_001",
                "label": "my_pc",
            }
        ],
        "assertions": [
            {
                "type": "device_registered",
                "registry_hub": "hub_home_001",
                "device": "dev_A9F3",
            },
            {
                "type": "label_maps_to",
                "registry_hub": "hub_home_001",
                "label": "my_pc",
                "device": "dev_A9F3",
            },
        ],
    })

    assert result.passed
    assert "dev_A9F3" in result.final_snapshot["devices"]


def test_run_name_conflict_scenario_dict():
    result = run_scenario({
        "scenario_id": "name_conflict",
        "setup": {
            "registry_hubs": [
                {"hub_id": "hub_home_001", "scope_path": "global.family.david.home"}
            ],
            "devices": [
                {"device_id": "dev_A9F3", "label": "my_pc"},
                {"device_id": "dev_B2C8", "label": "my_pc"},
            ],
        },
        "steps": [
            {
                "action": "register_device",
                "device": "dev_A9F3",
                "registry_hub": "hub_home_001",
                "label": "my_pc",
            },
            {
                "action": "register_device",
                "device": "dev_B2C8",
                "registry_hub": "hub_home_001",
                "label": "my_pc",
            },
        ],
        "assertions": [
            {
                "type": "label_maps_to",
                "registry_hub": "hub_home_001",
                "label": "my_pc_temp_B2C8",
                "device": "dev_B2C8",
            },
            {
                "type": "conflict_exists",
                "registry_hub": "hub_home_001",
                "conflict_type": "label_conflict",
            },
        ],
    })

    assert result.passed


def test_run_lane_open_and_send_scenario_dict():
    result = run_scenario({
        "scenario_id": "lane_open_and_send",
        "setup": _lane_setup(),
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
            },
            {
                "type": "lane_sequence",
                "traffic_hub": "hub_1",
                "lane": "lane_001",
                "last_sent": 1,
                "last_acknowledged": 1,
            },
        ],
    })

    assert result.passed


def test_run_relocation_pause_resume_scenario_dict():
    result = run_scenario({
        "scenario_id": "relocation_pause_resume",
        "setup": {
            "registry_hubs": [
                {"hub_id": "registry_home", "scope_path": "global.family.home"},
                {"hub_id": "registry_office", "scope_path": "global.family.office"},
            ],
            **_lane_setup(include_hub_4=True),
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
            {
                "action": "mark_in_transit",
                "device": "dev_B2C8",
                "registry_hub": "registry_home",
            },
            {
                "action": "pause_lanes_for_relocation",
                "traffic_hub": "hub_1",
                "device": "dev_B2C8",
            },
            {
                "action": "move_device",
                "device": "dev_B2C8",
                "old_registry_hub": "registry_home",
                "new_registry_hub": "registry_office",
                "old_traffic_hub": "hub_3",
                "new_traffic_hub": "hub_4",
            },
            {
                "action": "resume_lanes_after_relocation",
                "traffic_hub": "hub_1",
                "device": "dev_B2C8",
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
    })

    assert result.passed
    assert result.final_snapshot["lanes"]["lane_001"]["route"] == ["hub_1", "hub_2", "hub_4"]


def test_run_symbolic_spoof_failure_scenario_dict():
    result = run_scenario({
        "scenario_id": "symbolic_spoof_failure",
        "setup": {
            "registry_hubs": [
                {"hub_id": "hub_home_001", "scope_path": "global.family.david.home"}
            ],
            "devices": [{"device_id": "dev_A9F3", "label": "phone"}],
        },
        "steps": [
            {
                "action": "register_device",
                "device": "dev_A9F3",
                "registry_hub": "hub_home_001",
                "label": "phone",
            },
            {
                "action": "verify_rolling_proof",
                "registry_hub": "hub_home_001",
                "device": "dev_A9F3",
                "proof_valid": False,
            },
        ],
        "assertions": [
            {
                "type": "quarantine_exists",
                "registry_hub": "hub_home_001",
                "device": "dev_A9F3",
            }
        ],
    })

    assert result.passed


def test_run_growth_recommendation_scenario_dict():
    result = run_scenario({
        "scenario_id": "growth_recommendation",
        "setup": {"traffic_hubs": [{"hub_id": "traffic_home_001"}]},
        "steps": [
            {
                "action": "record_cross_tree_packet",
                "traffic_hub": "traffic_home_001",
                "from_branch": "global.family.home",
                "to_branch": "global.family.office",
                "count": 11,
            },
            {"action": "recommend_traffic_bridge", "traffic_hub": "traffic_home_001"},
        ],
        "assertions": [
            {
                "type": "recommendation_exists",
                "traffic_hub": "traffic_home_001",
                "recommendation_type": "create_traffic_bridge",
            }
        ],
    })

    assert result.passed


def test_yaml_scenario_file_can_load_if_yaml_supported():
    try:
        result = run_scenario(Path("scenarios/001_basic_registration.yaml"))
    except YamlSupportMissingError:
        pytest.skip("PyYAML is not installed")

    assert result.passed


def _lane_setup(include_hub_4: bool = False):
    traffic_hubs = [{"hub_id": "hub_1"}, {"hub_id": "hub_2"}, {"hub_id": "hub_3"}]
    links = [{"from": "hub_1", "to": "hub_2"}, {"from": "hub_2", "to": "hub_3"}]
    devices = [
        {"device_id": "dev_A9F3", "label": "source", "traffic_hub": "hub_1"},
        {"device_id": "dev_B2C8", "label": "target", "traffic_hub": "hub_3"},
    ]
    if include_hub_4:
        traffic_hubs.append({"hub_id": "hub_4"})
        links.append({"from": "hub_2", "to": "hub_4"})
        devices[1]["registry_hub"] = "registry_home"
    return {
        "traffic_hubs": traffic_hubs,
        "links": links,
        "devices": devices,
    }
