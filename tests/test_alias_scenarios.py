from pathlib import Path

from darwin.registry.aliases import resolve_alias
from darwin.sim.runner import run_scenario
from darwin.sim.scenarios import validate_scenario_dict

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
            {"action": "resolve_alias", "registry_hub": "hub_home_001"},
            {"action": "release_alias", "registry_hub": "hub_home_001"},
        ],
        "assertions": [
            {"type": "alias_resolves_to", "registry_hub": "hub_home_001"},
            {"type": "alias_status", "registry_hub": "hub_home_001"},
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
    assert "steps[1].alias" in locations
    assert "steps[2].alias" in locations
    assert "assertions[0].alias" in locations
    assert "assertions[0].device" in locations
    assert "assertions[1].alias" in locations
    assert "assertions[1].expected" in locations
    assert "assertions[2].alias" in locations
    assert "assertions[3].device" in locations
    assert "assertions[3].expected_identity_chain" in locations


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
