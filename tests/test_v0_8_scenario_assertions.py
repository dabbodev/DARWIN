from copy import deepcopy
from pathlib import Path

from darwin.sim.assertions import evaluate_assertion
from darwin.sim.runner import run_scenario
from darwin.sim.scenarios import list_scenario_files, validate_scenario_dict
from darwin.sim.validation import ASSERTION_REQUIRED_FIELDS

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_DIR = PROJECT_ROOT / "scenarios"


def test_v0_8_authority_outcome_history_assertion_is_validated():
    assert ASSERTION_REQUIRED_FIELDS["authority_outcome_history_contains"] == (
        "registry_hub",
    )


def test_v0_8_assertion_validation_requires_registry_hub():
    scenario = _base_scenario()
    scenario["assertions"] = [
        {
            "type": "authority_outcome_history_contains",
            "requested_alias": "global.server",
        }
    ]

    result = validate_scenario_dict(scenario)

    assert not result.valid
    assert result.errors[0].location == "assertions[0].registry_hub"
    assert "Missing required assertion field: registry_hub" in result.errors[0].message


def test_v0_8_assertion_validation_rejects_invalid_counts():
    scenario = _base_scenario()
    scenario["assertions"] = [
        {
            "type": "authority_outcome_history_contains",
            "registry_hub": "registry_home_001",
            "expected_count": "one",
        },
        {
            "type": "authority_outcome_history_contains",
            "registry_hub": "registry_home_001",
            "min_count": -1,
        },
    ]

    result = validate_scenario_dict(scenario)

    assert not result.valid
    assert [error.location for error in result.errors] == [
        "assertions[0].expected_count",
        "assertions[1].min_count",
    ]
    assert all("non-negative integer" in error.message for error in result.errors)


def test_v0_8_assertion_validation_rejects_invalid_boolean_markers():
    scenario = _base_scenario()
    scenario["assertions"] = [
        {
            "type": "authority_outcome_history_contains",
            "registry_hub": "registry_home_001",
            "fallback_used": "true",
        },
        {
            "type": "authority_outcome_history_contains",
            "registry_hub": "registry_home_001",
            "conflict_detected": 1,
        },
        {
            "type": "authority_outcome_history_contains",
            "registry_hub": "registry_home_001",
            "policy_denied": "false",
        },
        {
            "type": "authority_outcome_history_contains",
            "registry_hub": "registry_home_001",
            "path_broken": 0,
        },
    ]

    result = validate_scenario_dict(scenario)

    assert not result.valid
    assert [error.location for error in result.errors] == [
        "assertions[0].fallback_used",
        "assertions[1].conflict_detected",
        "assertions[2].policy_denied",
        "assertions[3].path_broken",
    ]
    assert all("must be a boolean" in error.message for error in result.errors)


def test_authority_outcome_history_contains_passes_for_approved_outcome():
    result = run_scenario(_approved_scenario())

    assert result.passed
    assertion = result.assertion_results[0]
    assert assertion.actual["count"] == 1
    assert assertion.actual["records"][0]["final_status"] == "approved_here"


def test_authority_outcome_history_contains_passes_for_fallback_outcome():
    result = run_scenario(_fallback_scenario())

    assert result.passed
    assertion = result.assertion_results[0]
    assert assertion.actual["records"][0]["fallback_used"] is True


def test_authority_outcome_history_contains_passes_for_conflict_outcome():
    result = run_scenario(_conflict_scenario())

    assert result.passed
    assertion = result.assertion_results[0]
    assert assertion.actual["records"][0]["conflict_detected"] is True


def test_authority_outcome_history_contains_passes_for_policy_denied_outcome():
    result = run_scenario(_policy_denied_scenario())

    assert result.passed
    assertion = result.assertion_results[0]
    assert assertion.actual["records"][0]["policy_denied"] is True


def test_authority_outcome_history_contains_passes_for_broken_path_outcome():
    result = run_scenario(_broken_path_scenario())

    assert result.passed
    assertion = result.assertion_results[0]
    assert assertion.actual["records"][0]["path_broken"] is True


def test_authority_outcome_history_contains_fails_with_expected_actual_context():
    scenario = _approved_scenario()
    scenario["assertions"] = [
        {
            "type": "authority_outcome_history_contains",
            "registry_hub": "registry_home_001",
            "requested_alias": "global.missing",
            "final_status": "approved_here",
        }
    ]

    result = run_scenario(scenario)

    assert not result.passed
    assertion = result.assertion_results[0]
    assert assertion.expected == {
        "min_count": 1,
        "filters": {
            "requested_alias": "global.missing",
            "granted_alias": None,
            "device_id": None,
            "requesting_hub": None,
            "final_status": "approved_here",
            "status": None,
            "reason": None,
            "authority_ceiling": None,
            "fallback_used": None,
            "conflict_detected": None,
            "policy_denied": None,
            "path_broken": None,
        },
    }
    assert assertion.actual == {
        "count": 0,
        "records": [],
        "registry_hub": "registry_home_001",
        "registry_hub_found": True,
    }


def test_authority_outcome_history_contains_expected_count_behavior():
    result = run_scenario({
        **_approved_scenario(),
        "assertions": [
            {
                "type": "authority_outcome_history_contains",
                "registry_hub": "registry_home_001",
                "requested_alias": "global.server",
                "expected_count": 1,
            },
            {
                "type": "authority_outcome_history_contains",
                "registry_hub": "registry_home_001",
                "requested_alias": "global.server",
                "expected_count": 2,
            },
        ],
    })

    assert not result.passed
    assert result.assertion_results[0].passed
    assert not result.assertion_results[1].passed
    assert result.assertion_results[1].actual["count"] == 1


def test_authority_outcome_history_contains_min_count_behavior():
    result = run_scenario({
        **_approved_scenario(),
        "assertions": [
            {
                "type": "authority_outcome_history_contains",
                "registry_hub": "registry_home_001",
                "requested_alias": "global.server",
                "min_count": 1,
            },
            {
                "type": "authority_outcome_history_contains",
                "registry_hub": "registry_home_001",
                "requested_alias": "global.server",
                "min_count": 2,
            },
        ],
    })

    assert not result.passed
    assert result.assertion_results[0].passed
    assert not result.assertion_results[1].passed
    assert result.assertion_results[1].expected["min_count"] == 2


def test_authority_outcome_history_assertion_is_read_only():
    result = run_scenario({**_approved_scenario(), "assertions": []})
    hub = result.world.registry_hubs["registry_home_001"]
    before_history = deepcopy(hub.authority_outcome_history)
    before_aliases = deepcopy(hub.aliases)
    before_action_result_count = len(result.world.action_results)

    assertion_result = evaluate_assertion(
        result.world,
        {
            "type": "authority_outcome_history_contains",
            "registry_hub": "registry_home_001",
            "requested_alias": "global.server",
            "final_status": "approved_here",
            "expected_count": 1,
        },
    )

    assert assertion_result.passed
    assert hub.authority_outcome_history == before_history
    assert hub.aliases == before_aliases
    assert len(result.world.action_results) == before_action_result_count


def test_v0_8_authority_outcome_history_scenarios_validate_and_run():
    scenario_files = [
        path for path in list_scenario_files(SCENARIOS_DIR) if path.name[:3] >= "042"
    ]

    failures = []
    for scenario_file in scenario_files:
        validation = validate_scenario_dict(_load_yaml(scenario_file), path=str(scenario_file))
        if not validation.valid:
            failures.append(f"{scenario_file}: {validation.errors}")
            continue
        result = run_scenario(scenario_file)
        if not result.passed:
            failures.append(f"{scenario_file}: {result.assertion_results}")

    assert scenario_files
    assert not failures


def _base_scenario():
    return {
        "scenario_id": "v0_8_assertion_test",
        "name": "v0.8 assertion test",
        "setup": {
            "registry_hubs": [
                {"hub_id": "registry_home_001", "scope_path": "global.family.david.home"}
            ],
            "devices": [{"device_id": "dev_A9F3", "label": "server"}],
        },
        "steps": [],
        "assertions": [],
    }


def _approved_scenario():
    return {
        "scenario_id": "authority_outcome_history_approved",
        "name": "Authority outcome history approved",
        "setup": {
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
                {"hub_id": "registry_global_001", "scope_path": "global"},
            ],
            "devices": [{"device_id": "dev_A9F3", "label": "server"}],
        },
        "steps": [
            _register("registry_home_001", "dev_A9F3", "server"),
            _register("registry_family_001", "dev_A9F3", "server"),
            _register("registry_global_001", "dev_A9F3", "server"),
            _claim_authority("global.server", "server", "dev_A9F3"),
        ],
        "assertions": [
            {
                "type": "authority_outcome_history_contains",
                "registry_hub": "registry_home_001",
                "requested_alias": "global.server",
                "granted_alias": "global.server",
                "device_id": "dev_A9F3",
                "requesting_hub": "registry_home_001",
                "final_status": "approved_here",
                "status": "claimed",
                "authority_ceiling": "global",
                "fallback_used": False,
                "expected_count": 1,
            }
        ],
    }


def _fallback_scenario():
    scenario = _approved_scenario()
    scenario["scenario_id"] = "authority_outcome_history_fallback"
    scenario["setup"]["registry_hubs"][1]["alias_authority_policy"] = {
        "allow_pass_up": False,
        "allow_fallback": True,
    }
    scenario["steps"] = [
        _register("registry_home_001", "dev_A9F3", "server"),
        _register("registry_family_001", "dev_A9F3", "server"),
        _claim_authority("global.server", "server", "dev_A9F3"),
    ]
    scenario["assertions"] = [
        {
            "type": "authority_outcome_history_contains",
            "registry_hub": "registry_home_001",
            "requested_alias": "global.server",
            "granted_alias": "global.family.david.server",
            "device_id": "dev_A9F3",
            "final_status": "fallback_granted",
            "status": "fallback_granted",
            "reason": "pass_up_denied_by_policy",
            "authority_ceiling": "global.family.david",
            "fallback_used": True,
            "expected_count": 1,
        }
    ]
    return scenario


def _conflict_scenario():
    scenario = _approved_scenario()
    scenario["scenario_id"] = "authority_outcome_history_conflict"
    scenario["setup"]["devices"].append({"device_id": "dev_B2C8", "label": "backup"})
    scenario["steps"] = [
        _register("registry_global_001", "dev_A9F3", "server"),
        _register("registry_home_001", "dev_B2C8", "backup"),
        _register("registry_family_001", "dev_B2C8", "backup"),
        _register("registry_global_001", "dev_B2C8", "backup"),
        {
            "action": "claim_alias",
            "registry_hub": "registry_global_001",
            "alias": "global.server",
            "target_device": "dev_A9F3",
        },
        _claim_authority("global.server", "server", "dev_B2C8"),
    ]
    scenario["assertions"] = [
        {
            "type": "authority_outcome_history_contains",
            "registry_hub": "registry_home_001",
            "requested_alias": "global.server",
            "device_id": "dev_B2C8",
            "final_status": "name_taken",
            "status": "conflict",
            "reason": "alias_conflict",
            "conflict_detected": True,
            "expected_count": 1,
        }
    ]
    return scenario


def _policy_denied_scenario():
    scenario = _approved_scenario()
    scenario["scenario_id"] = "authority_outcome_history_policy_denied"
    scenario["setup"]["registry_hubs"][1]["alias_authority_policy"] = {
        "allow_pass_up": False,
        "allow_fallback": False,
    }
    scenario["steps"] = [
        _register("registry_home_001", "dev_A9F3", "server"),
        _register("registry_family_001", "dev_A9F3", "server"),
        _claim_authority("global.server", "server", "dev_A9F3"),
    ]
    scenario["assertions"] = [
        {
            "type": "authority_outcome_history_contains",
            "registry_hub": "registry_home_001",
            "requested_alias": "global.server",
            "device_id": "dev_A9F3",
            "final_status": "policy_denied",
            "status": "rejected",
            "reason": "pass_up_denied_by_policy",
            "authority_ceiling": "global.family.david",
            "policy_denied": True,
            "expected_count": 1,
        }
    ]
    return scenario


def _broken_path_scenario():
    return {
        "scenario_id": "authority_outcome_history_broken_path",
        "name": "Authority outcome history broken path",
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
            _register("registry_home_001", "dev_A9F3", "server"),
            _claim_authority("global.server", "server", "dev_A9F3"),
        ],
        "assertions": [
            {
                "type": "authority_outcome_history_contains",
                "registry_hub": "registry_home_001",
                "requested_alias": "global.server",
                "device_id": "dev_A9F3",
                "final_status": "authority_path_broken",
                "status": "authority_path_broken",
                "reason": "parent_hub_not_found",
                "authority_ceiling": "global.family.david.home",
                "path_broken": True,
                "expected_count": 1,
            }
        ],
    }


def _register(registry_hub: str, device: str, label: str) -> dict[str, str]:
    return {
        "action": "register_device",
        "registry_hub": registry_hub,
        "device": device,
        "label": label,
    }


def _claim_authority(
    requested_alias: str,
    local_name: str,
    target_device: str,
) -> dict[str, object]:
    return {
        "action": "claim_alias_through_authority_chain",
        "registry_hub": "registry_home_001",
        "requested_alias": requested_alias,
        "local_name": local_name,
        "target_device": target_device,
        "requested_by_device": target_device,
        "fallback_allowed": True,
        "visibility": "scope_local",
    }


def _load_yaml(path: Path):
    import yaml

    return yaml.safe_load(path.read_text(encoding="utf-8"))
