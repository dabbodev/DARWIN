from pathlib import Path

from darwin.sim.runner import run_scenario
from darwin.sim.scenarios import list_scenario_files, validate_scenario_dict
from darwin.sim.validation import ASSERTION_REQUIRED_FIELDS

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_DIR = PROJECT_ROOT / "scenarios"


def test_v0_7_history_assertions_are_validated():
    for assertion_type in (
        "alias_history_contains",
        "alias_conflict_history_contains",
        "authority_audit_trace_contains",
        "quarantine_history_contains",
    ):
        assert ASSERTION_REQUIRED_FIELDS[assertion_type] == ("registry_hub",)


def test_v0_7_assertion_validation_requires_registry_hub():
    scenario = _base_scenario()
    scenario["assertions"] = [{"type": "alias_history_contains", "alias": "shared"}]

    result = validate_scenario_dict(scenario)

    assert not result.valid
    assert result.errors[0].location == "assertions[0].registry_hub"
    assert "Missing required assertion field: registry_hub" in result.errors[0].message


def test_alias_history_contains_passes_and_reports_counts():
    result = run_scenario({
        **_base_scenario(),
        "steps": [
            {
                "action": "claim_alias",
                "registry_hub": "registry_home_001",
                "alias": "global.family.david.home.server",
                "target_device": "dev_A9F3",
            },
            {
                "action": "release_alias",
                "registry_hub": "registry_home_001",
                "alias": "global.family.david.home.server",
            },
        ],
        "assertions": [
            {
                "type": "alias_history_contains",
                "registry_hub": "registry_home_001",
                "alias": "global.family.david.home.server",
                "device_id": "dev_A9F3",
                "status": "released",
                "expected_count": 1,
            }
        ],
    })

    assert result.passed
    assert result.assertion_results[0].actual["count"] == 1


def test_alias_history_contains_fails_for_missing_record():
    result = run_scenario({
        **_base_scenario(),
        "steps": [],
        "assertions": [
            {
                "type": "alias_history_contains",
                "registry_hub": "registry_home_001",
                "alias": "missing",
            }
        ],
    })

    assert not result.passed
    assert result.assertion_results[0].actual == {"count": 0, "records": []}


def test_alias_conflict_history_contains_passes_and_fails_by_count():
    scenario = {
        **_base_scenario(),
        "steps": [
            {
                "action": "claim_alias",
                "registry_hub": "registry_home_001",
                "alias": "shared",
                "target_device": "dev_A9F3",
            },
            {
                "action": "claim_alias",
                "registry_hub": "registry_home_001",
                "alias": "shared",
                "target_device": "dev_B2C8",
            },
        ],
        "assertions": [
            {
                "type": "alias_conflict_history_contains",
                "registry_hub": "registry_home_001",
                "alias": "shared",
                "device_id": "dev_B2C8",
                "expected_count": 1,
            },
            {
                "type": "alias_conflict_history_contains",
                "registry_hub": "registry_home_001",
                "alias": "shared",
                "expected_count": 2,
            },
        ],
    }

    result = run_scenario(scenario)

    assert not result.passed
    assert result.assertion_results[0].passed
    assert not result.assertion_results[1].passed
    assert result.assertion_results[1].actual["count"] == 1


def test_authority_audit_trace_contains_retained_success_and_fallback():
    result = run_scenario({
        "scenario_id": "authority_audit_trace_assertions",
        "name": "Authority audit trace assertions",
        "setup": {
            "registry_hubs": [
                {
                    "hub_id": "registry_home_001",
                    "scope_path": "global.family.david.home",
                    "parent_hub_id": "registry_global_001",
                },
                {"hub_id": "registry_global_001", "scope_path": "global"},
                {"hub_id": "registry_us_001", "scope_path": "global.us"},
            ],
            "devices": [{"device_id": "dev_A9F3", "label": "server"}],
        },
        "steps": [
            {
                "action": "register_device",
                "registry_hub": "registry_home_001",
                "device": "dev_A9F3",
                "label": "server",
            },
            {
                "action": "register_device",
                "registry_hub": "registry_global_001",
                "device": "dev_A9F3",
                "label": "server",
            },
            {
                "action": "register_device",
                "registry_hub": "registry_us_001",
                "device": "dev_A9F3",
                "label": "server",
            },
            {
                "action": "claim_alias_through_authority_chain",
                "registry_hub": "registry_home_001",
                "requested_alias": "global.server",
                "local_name": "server",
                "target_device": "dev_A9F3",
            },
            {
                "action": "claim_alias_through_authority_chain",
                "registry_hub": "registry_us_001",
                "requested_alias": "global.edge",
                "local_name": "edge",
                "target_device": "dev_A9F3",
            },
        ],
        "assertions": [
            {
                "type": "authority_audit_trace_contains",
                "registry_hub": "registry_global_001",
                "requested_alias": "global.server",
                "granted_alias": "global.server",
                "device_id": "dev_A9F3",
                "final_status": "approved_here",
                "outcome": "approved",
                "summary_contains": "approved at registry_global_001",
                "expected_count": 1,
            },
            {
                "type": "authority_audit_trace_contains",
                "registry_hub": "registry_us_001",
                "requested_alias": "global.edge",
                "granted_alias": "global.us.edge",
                "final_status": "fallback_granted",
                "outcome": "fallback",
                "expected_count": 1,
            },
        ],
    })

    assert result.passed


def test_authority_audit_trace_contains_explains_in_memory_denial():
    result = run_scenario({
        "scenario_id": "authority_audit_trace_denial_assertion",
        "name": "Authority audit trace denial assertion",
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
                    "alias_authority_policy": {
                        "allow_pass_up": False,
                        "allow_fallback": False,
                    },
                },
            ],
            "devices": [{"device_id": "dev_A9F3", "label": "server"}],
        },
        "steps": [
            {
                "action": "register_device",
                "registry_hub": "registry_home_001",
                "device": "dev_A9F3",
                "label": "server",
            },
            {
                "action": "register_device",
                "registry_hub": "registry_family_001",
                "device": "dev_A9F3",
                "label": "server",
            },
            {
                "action": "claim_alias_through_authority_chain",
                "registry_hub": "registry_home_001",
                "requested_alias": "global.server",
                "local_name": "server",
                "target_device": "dev_A9F3",
            },
        ],
        "assertions": [
            {
                "type": "authority_audit_trace_contains",
                "registry_hub": "registry_family_001",
                "requested_alias": "global.server",
                "device_id": "dev_A9F3",
                "final_status": "policy_denied",
                "outcome": "policy_denied",
                "summary_contains": "simulator-local policy",
                "expected_count": 1,
            }
        ],
    })

    assert result.passed
    assert (
        result.assertion_results[0].actual["records"][0]["source"]
        == "in_memory_authority_path"
    )


def test_authority_audit_trace_contains_fails_for_missing_outcome():
    result = run_scenario({
        **_base_scenario(),
        "steps": [],
        "assertions": [
            {
                "type": "authority_audit_trace_contains",
                "registry_hub": "registry_home_001",
                "outcome": "approved",
            }
        ],
    })

    assert not result.passed
    assert result.assertion_results[0].actual["count"] == 0


def test_quarantine_history_contains_passes():
    result = run_scenario({
        **_base_scenario(),
        "steps": [
            {
                "action": "verify_rolling_proof",
                "registry_hub": "registry_home_001",
                "device": "dev_A9F3",
                "proof_valid": False,
            }
        ],
        "assertions": [
            {
                "type": "quarantine_history_contains",
                "registry_hub": "registry_home_001",
                "device_id": "dev_A9F3",
                "reason": "rolling_proof_failed",
                "min_count": 1,
            }
        ],
    })

    assert result.passed


def test_v0_7_scenarios_validate_and_run():
    scenario_files = [
        path for path in list_scenario_files(SCENARIOS_DIR) if path.name[:3] >= "037"
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
        "scenario_id": "v0_7_assertion_test",
        "name": "v0.7 assertion test",
        "setup": {
            "registry_hubs": [
                {"hub_id": "registry_home_001", "scope_path": "global.family.david.home"}
            ],
            "devices": [
                {
                    "device_id": "dev_A9F3",
                    "label": "server",
                    "registry_hub": "registry_home_001",
                },
                {
                    "device_id": "dev_B2C8",
                    "label": "tablet",
                    "registry_hub": "registry_home_001",
                },
            ],
        },
        "steps": [],
        "assertions": [],
    }


def _load_yaml(path: Path):
    import yaml

    return yaml.safe_load(path.read_text(encoding="utf-8"))
