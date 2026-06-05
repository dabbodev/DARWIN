from pathlib import Path

from darwin.registry.aliases import resolve_alias
from darwin.sim.assertions import evaluate_assertion
from darwin.sim.library import scenario_metadata_from_dict
from darwin.sim.runner import run_scenario
from darwin.sim.scenarios import (
    list_scenario_files,
    load_scenario_file,
    validate_scenario_dict,
    validate_scenario_file,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_alias_claim_scenario_runs():
    result = run_scenario(PROJECT_ROOT / "scenarios" / "026_alias_claim_success.yaml")

    assert result.passed


def test_alias_conflict_scenario_runs():
    result = run_scenario(PROJECT_ROOT / "scenarios" / "027_alias_claim_conflict.yaml")

    assert result.passed


def test_alias_release_scenario_runs():
    result = run_scenario(
        PROJECT_ROOT / "scenarios" / "028_alias_release_blocks_resolution.yaml"
    )

    assert result.passed


def test_progressive_alias_scenario_runs():
    result = run_scenario(
        PROJECT_ROOT / "scenarios" / "029_progressive_alias_fallback.yaml"
    )

    assert result.passed


def test_alias_bundle_scenario_runs():
    result = run_scenario(
        PROJECT_ROOT / "scenarios" / "030_alias_bundle_delegation.yaml"
    )

    assert result.passed


def test_dns_style_alias_bundle_scenario_runs():
    result = run_scenario(
        PROJECT_ROOT / "scenarios" / "031_dns_style_alias_bundle.yaml"
    )

    assert result.passed


def test_alias_authority_chain_scenarios_run():
    scenario_names = [
        "032_alias_authority_chain_success.yaml",
        "033_alias_authority_chain_fallback.yaml",
        "034_alias_authority_chain_name_taken.yaml",
        "035_alias_authority_chain_policy_denied.yaml",
        "036_alias_authority_chain_broken_parent.yaml",
    ]

    for scenario_name in scenario_names:
        scenario_file = PROJECT_ROOT / "scenarios" / scenario_name
        validation = validate_scenario_file(scenario_file)
        assert validation.passed, scenario_name

        result = run_scenario(scenario_file)
        assert result.passed, scenario_name


def test_alias_authority_chain_scenarios_are_discoverable():
    metadata_by_id = {
        item.scenario_id: item
        for item in (
            scenario_metadata_from_dict(
                load_scenario_file(path),
                path=str(path.relative_to(PROJECT_ROOT)),
            )
            for path in list_scenario_files(PROJECT_ROOT / "scenarios")
        )
    }
    expected_ids = [
        "032_alias_authority_chain_success",
        "033_alias_authority_chain_fallback",
        "034_alias_authority_chain_name_taken",
        "035_alias_authority_chain_policy_denied",
        "036_alias_authority_chain_broken_parent",
    ]

    assert list(metadata_by_id.keys())[31:36] == expected_ids
    for scenario_id in expected_ids:
        metadata = metadata_by_id[scenario_id]
        assert metadata.category == "registry"
        assert "alias_authority_chain" in metadata.tags
        assert metadata.description


def test_dns_style_bundle_metadata_present():
    data = load_scenario_file(
        PROJECT_ROOT / "scenarios" / "031_dns_style_alias_bundle.yaml"
    )
    metadata = scenario_metadata_from_dict(data)

    assert metadata.category == "registry"
    assert "dns_style" in metadata.tags
    assert "public_alias" in metadata.tags


def test_all_scenarios_still_pass():
    scenario_files = list_scenario_files(PROJECT_ROOT / "scenarios")

    for scenario_file in scenario_files:
        validation = validate_scenario_file(scenario_file)
        assert validation.passed, scenario_file.name

        result = run_scenario(scenario_file)
        assert result.passed, scenario_file.name


def test_alias_conflict_preserves_original_owner():
    result = run_scenario(PROJECT_ROOT / "scenarios" / "027_alias_claim_conflict.yaml")

    hub = result.world.registry_hubs["hub_home_001"]
    resolution = resolve_alias(hub, "global.family.david.shared_alias")

    assert result.passed
    assert resolution.success
    assert resolution.target_device_id == "dev_A9F3"
    assert resolution.target_device_id != "dev_B2C8"
    assert hub.aliases["global.family.david.shared_alias"].target_device_id == "dev_A9F3"


def test_released_alias_does_not_resolve_in_scenario():
    result = run_scenario(
        PROJECT_ROOT / "scenarios" / "028_alias_release_blocks_resolution.yaml"
    )

    hub = result.world.registry_hubs["hub_home_001"]
    resolution = resolve_alias(hub, "global.family.david.release_alias")

    assert result.passed
    assert not resolution.success
    assert resolution.status == "released"
    assert resolution.reason == "alias_not_active"
    assert resolution.target_device_id is None


def test_claim_alias_action():
    result = run_scenario({
        "scenario_id": "claim_alias_action",
        "setup": _alias_setup(),
        "steps": [
            {
                "action": "claim_alias",
                "registry_hub": "hub_home_001",
                "alias": "global.family.david_server",
                "target_device": "dev_A9F3",
            }
        ],
        "assertions": [],
    })

    latest_result = result.world.action_results[-1]
    assert latest_result.success
    assert latest_result.status == "active"


def test_claim_progressive_alias_action():
    result = run_scenario({
        "scenario_id": "claim_progressive_alias_action",
        "setup": _alias_setup(),
        "steps": [
            {
                "action": "claim_progressive_alias",
                "registry_hub": "hub_home_001",
                "requested_alias": "global.david_server",
                "local_name": "david_server",
                "target_device": "dev_A9F3",
            }
        ],
        "assertions": [],
    })

    latest_result = result.world.action_results[-1]
    assert latest_result.success
    assert latest_result.status == "fallback_granted"
    assert latest_result.granted_alias == "global.family.home.david_server"


def test_claim_alias_through_authority_chain_action_records_path():
    result = run_scenario({
        "scenario_id": "claim_alias_through_authority_chain_action",
        "setup": _alias_authority_chain_setup(),
        "steps": [
            _register_at("registry_home_001", "dev_A9F3", "server"),
            _register_at("registry_family_001", "dev_A9F3", "server"),
            _register_at("registry_global_001", "dev_A9F3", "server"),
            _claim_alias_through_authority_chain_step(),
        ],
        "assertions": [],
    })

    latest_result = result.world.action_results[-1]
    assert latest_result.success
    assert latest_result.status == "claimed"
    assert latest_result.authority_path.to_summary().path_hubs == [
        "registry_home_001",
        "registry_family_001",
        "registry_global_001",
    ]
    assert result.world.event_log.entries[-1].event_type == (
        "alias_authority_chain_claimed"
    )
    assert result.final_snapshot["alias_authority_claims"][0]["authority_path"][
        "final_status"
    ] == "approved_here"


def test_claim_alias_through_authority_chain_success_event_is_deterministic():
    result = run_scenario({
        "scenario_id": "claim_alias_through_authority_chain_event_success",
        "setup": _alias_authority_chain_setup(),
        "steps": [
            _register_at("registry_home_001", "dev_A9F3", "server"),
            _register_at("registry_family_001", "dev_A9F3", "server"),
            _register_at("registry_global_001", "dev_A9F3", "server"),
            _claim_alias_through_authority_chain_step(),
        ],
        "assertions": [],
    })

    event = result.world.event_log.entries[-1]

    assert event.event_type == "alias_authority_chain_claimed"
    assert event.status == "claimed"
    assert event.hub_id == "registry_home_001"
    assert event.device_id == "dev_A9F3"
    assert event.data["requested_alias"] == "global.server"
    assert event.data["granted_alias"] == "global.server"
    assert event.data["success"] is True
    assert event.data["authority_ceiling"] == "global"
    assert event.data["authority_path_final_status"] == "approved_here"
    assert event.data["decision_count"] == 3
    assert event.data["path_hubs"] == [
        "registry_home_001",
        "registry_family_001",
        "registry_global_001",
    ]
    assert [decision["decision"] for decision in event.data["decisions"]] == [
        "continue_upward",
        "continue_upward",
        "approved_here",
    ]


def test_claim_alias_through_authority_chain_failure_records_path():
    result = run_scenario({
        "scenario_id": "claim_alias_through_authority_chain_failure_action",
        "setup": {
            "registry_hubs": [
                {
                    "hub_id": "registry_home_001",
                    "scope_path": "global.family.david.home",
                    "parent_hub_id": "registry_missing_001",
                }
            ],
            "devices": [{"device_id": "dev_A9F3", "label": "server"}],
        },
        "steps": [
            _register_at("registry_home_001", "dev_A9F3", "server"),
            _claim_alias_through_authority_chain_step(),
        ],
        "assertions": [],
    })

    latest_result = result.world.action_results[-1]
    assert not latest_result.success
    assert latest_result.status == "authority_path_broken"
    assert latest_result.authority_path.to_summary().path_hubs == [
        "registry_home_001",
        "registry_missing_001",
    ]
    assert result.world.event_log.entries[-1].event_type == (
        "alias_authority_chain_failed"
    )
    assert result.final_snapshot["alias_authority_claims"][0]["reason"] == (
        "parent_hub_not_found"
    )


def test_claim_alias_through_authority_chain_failure_event_is_deterministic():
    result = run_scenario(
        PROJECT_ROOT / "scenarios" / "035_alias_authority_chain_policy_denied.yaml"
    )

    event = result.world.event_log.entries[-1]

    assert result.passed
    assert event.event_type == "alias_authority_chain_failed"
    assert event.status == "rejected"
    assert event.hub_id == "registry_home_001"
    assert event.device_id == "dev_A9F3"
    assert event.data["requested_alias"] == "global.server"
    assert event.data["granted_alias"] is None
    assert event.data["success"] is False
    assert event.data["reason"] == "pass_up_denied_by_policy"
    assert event.data["authority_ceiling"] == "global.family.david"
    assert event.data["authority_path_final_status"] == "policy_denied"
    assert event.data["decision_count"] == 2
    assert event.data["path_hubs"] == [
        "registry_home_001",
        "registry_family_001",
    ]
    assert [decision["decision"] for decision in event.data["decisions"]] == [
        "continue_upward",
        "policy_denied",
    ]


def test_alias_authority_chain_snapshot_records_compact_failure_data():
    result = run_scenario(
        PROJECT_ROOT / "scenarios" / "036_alias_authority_chain_broken_parent.yaml"
    )

    claim_snapshot = result.final_snapshot["alias_authority_claims"][0]

    assert result.passed
    assert claim_snapshot == {
        "requested_alias": "global.server",
        "granted_alias": None,
        "status": "authority_path_broken",
        "reason": "parent_hub_not_found",
        "success": False,
        "authority_ceiling": "global.family.david.home",
        "authority_path": {
            "requested_alias": "global.server",
            "granted_alias": None,
            "final_status": "authority_path_broken",
            "authority_ceiling": "global.family.david.home",
            "decision_count": 2,
            "path_hubs": [
                "registry_home_001",
                "registry_missing_001",
            ],
        },
    }


def test_failed_authority_chain_claim_does_not_create_active_aliases():
    result = run_scenario(
        PROJECT_ROOT / "scenarios" / "035_alias_authority_chain_policy_denied.yaml"
    )

    assert result.passed
    for hub in result.world.registry_hubs.values():
        assert not [
            alias
            for alias, record in hub.aliases.items()
            if record.status == "active" and alias.endswith(".server")
        ]


def test_create_alias_bundle_action():
    result = run_scenario({
        "scenario_id": "create_alias_bundle_action",
        "setup": _alias_setup(),
        "steps": [
            {
                "action": "create_alias_bundle",
                "registry_hub": "hub_home_001",
                "bundle_path": "global.family.home.team",
            }
        ],
        "assertions": [],
    })

    latest_result = result.world.action_results[-1]
    assert latest_result.success
    assert latest_result.status == "active"


def test_claim_bundle_alias_action():
    result = run_scenario({
        "scenario_id": "claim_bundle_alias_action",
        "setup": _alias_setup(),
        "steps": [
            {
                "action": "create_alias_bundle",
                "registry_hub": "hub_home_001",
                "bundle_path": "global.family.home.team",
            },
            {
                "action": "claim_bundle_alias",
                "registry_hub": "hub_home_001",
                "bundle_path": "global.family.home.team",
                "child_name": "server",
                "target_device": "dev_A9F3",
            },
        ],
        "assertions": [],
    })

    latest_result = result.world.action_results[-1]
    assert latest_result.success
    assert latest_result.status == "active"
    assert latest_result.bundle_path == "global.family.home.team"


def test_resolve_alias_action():
    result = run_scenario({
        "scenario_id": "resolve_alias_action",
        "setup": _alias_setup(),
        "steps": [
            {
                "action": "claim_alias",
                "registry_hub": "hub_home_001",
                "alias": "global.family.david_server",
                "target_device": "dev_A9F3",
            },
            {
                "action": "resolve_alias",
                "registry_hub": "hub_home_001",
                "alias": "global.family.david_server",
            },
        ],
        "assertions": [],
    })

    latest_result = result.world.action_results[-1]
    assert latest_result.success
    assert latest_result.target_device_id == "dev_A9F3"


def test_alias_resolves_to_assertion():
    result = run_scenario({
        "scenario_id": "alias_resolves_to_assertion",
        "setup": _alias_setup(),
        "steps": [_claim_alias_step()],
        "assertions": [
            {
                "type": "alias_resolves_to",
                "registry_hub": "hub_home_001",
                "alias": "global.family.david_server",
                "device": "dev_A9F3",
            }
        ],
    })

    assert result.passed


def test_alias_status_assertion():
    result = run_scenario({
        "scenario_id": "alias_status_assertion",
        "setup": _alias_setup(),
        "steps": [_claim_alias_step()],
        "assertions": [
            {
                "type": "alias_status",
                "registry_hub": "hub_home_001",
                "alias": "global.family.david_server",
                "expected": "active",
            }
        ],
    })

    assert result.passed


def test_alias_bundle_status_assertion():
    result = run_scenario({
        "scenario_id": "alias_bundle_status_assertion",
        "setup": _alias_setup(),
        "steps": [
            {
                "action": "create_alias_bundle",
                "registry_hub": "hub_home_001",
                "bundle_path": "global.family.home.team",
            }
        ],
        "assertions": [
            {
                "type": "alias_bundle_status",
                "registry_hub": "hub_home_001",
                "bundle_path": "global.family.home.team",
                "expected": "active",
            }
        ],
    })

    assert result.passed


def test_bundle_alias_resolves_to_assertion():
    result = run_scenario({
        "scenario_id": "bundle_alias_resolves_to_assertion",
        "setup": _alias_setup(),
        "steps": [
            {
                "action": "create_alias_bundle",
                "registry_hub": "hub_home_001",
                "bundle_path": "global.family.home.team",
            },
            {
                "action": "claim_bundle_alias",
                "registry_hub": "hub_home_001",
                "bundle_path": "global.family.home.team",
                "child_name": "server",
                "target_device": "dev_A9F3",
            },
        ],
        "assertions": [
            {
                "type": "bundle_alias_resolves_to",
                "registry_hub": "hub_home_001",
                "bundle_path": "global.family.home.team",
                "child_name": "server",
                "device": "dev_A9F3",
            }
        ],
    })

    assert result.passed


def test_alias_granted_as_assertion():
    result = run_scenario({
        "scenario_id": "alias_granted_as_assertion",
        "setup": _alias_setup(),
        "steps": [_claim_progressive_alias_step()],
        "assertions": [
            {
                "type": "alias_granted_as",
                "registry_hub": "hub_home_001",
                "requested_alias": "global.david_server",
                "granted_alias": "global.family.home.david_server",
            }
        ],
    })

    assert result.passed


def test_alias_authority_ceiling_assertion():
    result = run_scenario({
        "scenario_id": "alias_authority_ceiling_assertion",
        "setup": _alias_setup(),
        "steps": [_claim_progressive_alias_step()],
        "assertions": [
            {
                "type": "alias_authority_ceiling",
                "registry_hub": "hub_home_001",
                "alias": "global.family.home.david_server",
                "expected": "global.family.home",
            }
        ],
    })

    assert result.passed


def test_alias_authority_path_summary_assertion_passes():
    result = run_scenario({
        "scenario_id": "alias_authority_path_summary_assertion",
        "setup": _alias_authority_chain_setup(),
        "steps": [
            _register_at("registry_home_001", "dev_A9F3", "server"),
            _register_at("registry_family_001", "dev_A9F3", "server"),
            _register_at("registry_global_001", "dev_A9F3", "server"),
            _claim_alias_through_authority_chain_step(),
        ],
        "assertions": [
            {
                "type": "alias_authority_path_summary",
                "requested_alias": "global.server",
                "final_status": "approved_here",
                "granted_alias": "global.server",
                "authority_ceiling": "global",
                "decision_count": 3,
                "path_hubs": [
                    "registry_home_001",
                    "registry_family_001",
                    "registry_global_001",
                ],
            }
        ],
    })

    assert result.passed


def test_alias_authority_path_summary_assertion_fails_with_actual():
    result = run_scenario({
        "scenario_id": "alias_authority_path_summary_assertion_failure",
        "setup": _alias_authority_chain_setup(),
        "steps": [
            _register_at("registry_home_001", "dev_A9F3", "server"),
            _register_at("registry_family_001", "dev_A9F3", "server"),
            _register_at("registry_global_001", "dev_A9F3", "server"),
            _claim_alias_through_authority_chain_step(),
        ],
        "assertions": [],
    })

    assertion_result = evaluate_assertion(
        result.world,
        {
            "type": "alias_authority_path_summary",
            "requested_alias": "global.server",
            "final_status": "policy_denied",
            "decision_count": 3,
        },
    )

    assert not assertion_result.passed
    assert assertion_result.expected == {
        "final_status": "policy_denied",
        "decision_count": 3,
    }
    assert assertion_result.actual == {
        "final_status": "approved_here",
        "decision_count": 3,
    }


def test_alias_not_resolved_assertion_after_release():
    result = run_scenario({
        "scenario_id": "alias_not_resolved_assertion_after_release",
        "setup": _alias_setup(),
        "steps": [
            _claim_alias_step(),
            {
                "action": "release_alias",
                "registry_hub": "hub_home_001",
                "alias": "global.family.david_server",
                "requested_by_device": "dev_A9F3",
            },
        ],
        "assertions": [
            {
                "type": "alias_not_resolved",
                "registry_hub": "hub_home_001",
                "alias": "global.family.david_server",
            }
        ],
    })

    assert result.passed


def test_canonical_identity_unchanged_assertion():
    result = run_scenario({
        "scenario_id": "canonical_identity_unchanged_assertion",
        "setup": _alias_setup(),
        "steps": [_claim_alias_step()],
        "assertions": [
            {
                "type": "canonical_identity_unchanged",
                "registry_hub": "hub_home_001",
                "device": "dev_A9F3",
                "expected_identity_chain": "global.family.home.project_server",
            }
        ],
    })

    assert result.passed


def test_alias_actions_validate_required_fields():
    result = validate_scenario_dict({
        "scenario_id": "alias_validation",
        "setup": {},
        "steps": [
            {"action": "claim_alias", "registry_hub": "hub_home_001"},
            {"action": "create_alias_bundle"},
            {"action": "claim_bundle_alias", "registry_hub": "hub_home_001"},
            {"action": "claim_progressive_alias", "registry_hub": "hub_home_001"},
            {
                "action": "claim_alias_through_authority_chain",
                "registry_hub": "hub_home_001",
            },
            {"action": "resolve_alias", "registry_hub": "hub_home_001"},
            {"action": "release_alias", "registry_hub": "hub_home_001"},
        ],
        "assertions": [
            {"type": "alias_resolves_to", "registry_hub": "hub_home_001"},
            {"type": "alias_status", "registry_hub": "hub_home_001"},
            {"type": "alias_bundle_status", "registry_hub": "hub_home_001"},
            {"type": "bundle_alias_resolves_to", "registry_hub": "hub_home_001"},
            {"type": "alias_granted_as", "registry_hub": "hub_home_001"},
            {"type": "alias_authority_ceiling", "registry_hub": "hub_home_001"},
            {"type": "alias_authority_path_summary"},
            {"type": "alias_not_resolved", "registry_hub": "hub_home_001"},
            {
                "type": "canonical_identity_unchanged",
                "registry_hub": "hub_home_001",
            },
        ],
    })

    assert not result.valid
    locations = {error.location for error in result.errors}
    assert "steps[0].alias" in locations
    assert "steps[0].target_device" in locations
    assert "steps[1].registry_hub" in locations
    assert "steps[1].bundle_path" in locations
    assert "steps[2].bundle_path" in locations
    assert "steps[2].child_name" in locations
    assert "steps[2].target_device" in locations
    assert "steps[3].requested_alias" in locations
    assert "steps[3].local_name" in locations
    assert "steps[3].target_device" in locations
    assert "steps[4].requested_alias" in locations
    assert "steps[4].local_name" in locations
    assert "steps[4].target_device" in locations
    assert "steps[5].alias" in locations
    assert "steps[6].alias" in locations
    assert "assertions[0].alias" in locations
    assert "assertions[0].device" in locations
    assert "assertions[1].alias" in locations
    assert "assertions[1].expected" in locations
    assert "assertions[2].bundle_path" in locations
    assert "assertions[2].expected" in locations
    assert "assertions[3].bundle_path" in locations
    assert "assertions[3].child_name" in locations
    assert "assertions[3].device" in locations
    assert "assertions[4].requested_alias" in locations
    assert "assertions[4].granted_alias" in locations
    assert "assertions[5].alias" in locations
    assert "assertions[5].expected" in locations
    assert "assertions[6].requested_alias" in locations
    assert "assertions[7].alias" in locations
    assert "assertions[8].device" in locations
    assert "assertions[8].expected_identity_chain" in locations


def _alias_setup():
    return {
        "hybrid_hubs": [
            {
                "hub_id": "hub_home_001",
                "scope_path": "global.family.home",
            }
        ],
        "devices": [
            {
                "device_id": "dev_A9F3",
                "label": "project_server",
                "registry_hub": "hub_home_001",
            }
        ],
    }


def _alias_authority_chain_setup():
    return {
        "registry_hubs": [
            {
                "hub_id": "registry_home_001",
                "scope_path": "global.family.david.home",
                "parent_hub_id": "registry_family_001",
            },
            {
                "hub_id": "registry_family_001",
                "scope_path": "global.family.david",
                "parent_hub_id": "registry_global_001",
            },
            {
                "hub_id": "registry_global_001",
                "scope_path": "global",
            },
        ],
        "devices": [
            {
                "device_id": "dev_A9F3",
                "label": "server",
            }
        ],
    }


def _register_at(registry_hub: str, device: str, label: str):
    return {
        "action": "register_device",
        "registry_hub": registry_hub,
        "device": device,
        "label": label,
    }


def _claim_alias_step():
    return {
        "action": "claim_alias",
        "registry_hub": "hub_home_001",
        "alias": "global.family.david_server",
        "target_device": "dev_A9F3",
    }


def _claim_progressive_alias_step():
    return {
        "action": "claim_progressive_alias",
        "registry_hub": "hub_home_001",
        "requested_alias": "global.david_server",
        "local_name": "david_server",
        "target_device": "dev_A9F3",
    }


def _claim_alias_through_authority_chain_step():
    return {
        "action": "claim_alias_through_authority_chain",
        "registry_hub": "registry_home_001",
        "requested_alias": "global.server",
        "local_name": "server",
        "target_device": "dev_A9F3",
    }
