from pathlib import Path

from darwin.registry.aliases import resolve_alias
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
    assert "steps[4].alias" in locations
    assert "steps[5].alias" in locations
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
    assert "assertions[6].alias" in locations
    assert "assertions[7].device" in locations
    assert "assertions[7].expected_identity_chain" in locations


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
