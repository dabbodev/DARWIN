from __future__ import annotations

import inspect
from pathlib import Path

import darwin.sim.assertions as scenario_assertions
import darwin.sim.runner as scenario_runner
from darwin.models.encrypted_delivery import EncryptedDeliveryResult
from darwin.sim.assertions import evaluate_assertion
from darwin.sim.runner import run_scenario
from darwin.sim.scenarios import list_scenario_files, validate_scenario_dict
from darwin.sim.validation import ASSERTION_REQUIRED_FIELDS, STEP_REQUIRED_FIELDS

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_DIR = PROJECT_ROOT / "scenarios"


def test_v1_1_encrypted_delivery_actions_and_assertions_are_validated():
    assert STEP_REQUIRED_FIELDS["evaluate_encrypted_delivery_request"] == (
        "registry_hub",
        "request_id",
        "message_id",
        "sender_id",
        "recipient_address",
    )
    assert ASSERTION_REQUIRED_FIELDS["encrypted_delivery_result_contains"] == (
        "registry_hub",
    )
    assert ASSERTION_REQUIRED_FIELDS["encrypted_delivery_audit_contains"] == (
        "registry_hub",
    )


def test_v1_1_validation_rejects_missing_fields_booleans_and_counts():
    scenario = _minimal_invalid_validation_scenario()

    result = validate_scenario_dict(scenario)

    assert not result.valid
    assert [error.location for error in result.errors] == [
        "steps[0].recipient_address",
        "steps[0].attempt_delivery",
        "steps[0].retain_policy_decision",
        "assertions[0].delivery_attempted",
        "assertions[1].envelope_accepted",
        "assertions[2].expected_count",
        "assertions[3].min_count",
    ]


def test_v1_1_policy_check_only_action_path_does_not_deliver():
    result = run_scenario(SCENARIOS_DIR / "050_symbolic_encrypted_delivery_policy_check.yaml")
    hub = result.world.registry_hubs["registry_chat_001"]
    wrapped = _encrypted_results(result.world.action_results)

    assert result.passed
    assert wrapped[-1].status.status == "policy_check_only"
    assert wrapped[-1].message_id == "msg_policy_check_only"
    assert wrapped[-1].delivery_allowed is True
    assert wrapped[-1].delivery_attempted is False
    assert hub.message_delivery_results == []
    assert hub.message_inboxes == {}
    assert hub.encryption_policy_decision_history[-1].status.status == "accepted"


def test_v1_1_gate_allowed_no_attempt_and_explicit_attempt_paths():
    result = run_scenario(SCENARIOS_DIR / "051_symbolic_encrypted_delivery_allowed.yaml")
    hub = result.world.registry_hubs["registry_chat_001"]
    wrapped = _encrypted_results(result.world.action_results)

    assert result.passed
    assert wrapped[-2].request_id == "req_encrypted_allowed_no_attempt"
    assert wrapped[-2].status.status == "not_delivered"
    assert wrapped[-2].delivery_allowed is True
    assert wrapped[-2].delivery_attempted is False
    assert wrapped[-2].delivery_result is None
    assert wrapped[-1].request_id == "req_encrypted_allowed_attempt"
    assert wrapped[-1].status.status == "delivered"
    assert wrapped[-1].delivery_attempted is True
    assert wrapped[-1].delivery_result.status.status == "delivered"
    assert [message.message_id for message in hub.message_inboxes["mailbox_neo"]] == [
        "msg_encrypted_allowed_attempt"
    ]
    assert [delivery.message_id for delivery in hub.message_delivery_results] == [
        "msg_encrypted_allowed_attempt"
    ]


def test_v1_1_gate_blocked_path_does_not_mutate_delivery_state():
    result = run_scenario(SCENARIOS_DIR / "052_symbolic_encrypted_delivery_blocked.yaml")
    hub = result.world.registry_hubs["registry_chat_001"]
    wrapped = _encrypted_results(result.world.action_results)

    assert result.passed
    assert wrapped[-1].status.status == "gate_blocked"
    assert wrapped[-1].reason == "unsupported_profile"
    assert wrapped[-1].delivery_allowed is False
    assert wrapped[-1].delivery_attempted is False
    assert wrapped[-1].delivery_result is None
    assert hub.message_delivery_results == []
    assert hub.message_inboxes == {}
    assert hub.encryption_policy_decision_history[-1].status.status == (
        "unsupported_profile"
    )


def test_v1_1_encrypted_delivery_result_assertion_passes_and_fails_by_count():
    result = run_scenario(SCENARIOS_DIR / "051_symbolic_encrypted_delivery_allowed.yaml")

    passing = evaluate_assertion(
        result.world,
        {
            "type": "encrypted_delivery_result_contains",
            "registry_hub": "registry_chat_001",
            "request_id": "req_encrypted_allowed_attempt",
            "status": "delivered",
            "delivery_attempted": True,
            "delivery_allowed": True,
            "gate_status": "allowed",
            "delivery_status": "delivered",
            "endpoint_id": "endpoint_mailbox_neo",
            "expected_count": 1,
        },
    )
    failing = evaluate_assertion(
        result.world,
        {
            "type": "encrypted_delivery_result_contains",
            "registry_hub": "registry_chat_001",
            "gate_status": "allowed",
            "expected_count": 3,
        },
    )

    assert passing.passed
    assert passing.actual["records"][0]["metadata"]["registry_hub"] == (
        "registry_chat_001"
    )
    assert not failing.passed
    assert failing.actual["count"] == 2
    assert failing.expected["expected_count"] == 3


def test_v1_1_encrypted_delivery_audit_assertion_is_read_only():
    result = run_scenario(SCENARIOS_DIR / "052_symbolic_encrypted_delivery_blocked.yaml")
    before_action_result_count = len(result.world.action_results)

    assertion = evaluate_assertion(
        result.world,
        {
            "type": "encrypted_delivery_audit_contains",
            "registry_hub": "registry_chat_001",
            "request_id": "req_encrypted_blocked_profile",
            "gate_status": "policy_check_failed",
            "delivery_status": "not_attempted",
            "envelope_accepted": False,
            "expected_count": 1,
        },
    )

    assert assertion.passed
    assert assertion.actual["records"][0]["metadata"]["registry_hub"] == (
        "registry_chat_001"
    )
    assert len(result.world.action_results) == before_action_result_count


def test_v1_1_checked_in_encrypted_delivery_scenarios_validate_and_run():
    scenario_files = [
        path
        for path in list_scenario_files(SCENARIOS_DIR)
        if path.name[:3] in {"050", "051", "052"}
    ]

    failures = []
    for scenario_file in scenario_files:
        validation = validate_scenario_dict(
            _load_yaml(scenario_file),
            path=str(scenario_file),
        )
        if not validation.valid:
            failures.append(f"{scenario_file}: {validation.errors}")
            continue
        result = run_scenario(scenario_file)
        if not result.passed:
            failures.append(f"{scenario_file}: {result.assertion_results}")

    assert [path.name[:3] for path in scenario_files] == ["050", "051", "052"]
    assert not failures


def test_v1_1_scenario_sweep_remains_contiguous_001_through_052():
    scenario_numbers = sorted(
        int(path.name[:3])
        for path in list_scenario_files(SCENARIOS_DIR)
        if path.name[:3].isdigit()
    )

    assert scenario_numbers == list(range(1, 53))


def test_v1_1_existing_plaintext_delivery_scenario_still_passes():
    result = run_scenario(SCENARIOS_DIR / "044_mailbox_basic_message_delivery.yaml")

    assert result.passed
    assert result.world.registry_hubs["registry_chat_001"].message_delivery_results[
        0
    ].status.status == "delivered"


def test_v1_1_scenario_dsl_does_not_import_crypto_libraries():
    source = inspect.getsource(scenario_runner) + inspect.getsource(scenario_assertions)

    assert "import secrets" not in source
    assert "import cryptography" not in source
    assert "from cryptography" not in source


def _encrypted_results(action_results: list[object]) -> list[EncryptedDeliveryResult]:
    return [
        result
        for result in action_results
        if isinstance(result, EncryptedDeliveryResult)
    ]


def _minimal_invalid_validation_scenario() -> dict[str, object]:
    return {
        "scenario_id": "v1_1_invalid_encrypted_delivery_validation",
        "name": "v1.1 invalid encrypted delivery validation",
        "category": "encryption",
        "setup": {"registry_hubs": [{"hub_id": "registry_chat_001", "scope_path": "global.chat"}]},
        "steps": [
            {
                "action": "evaluate_encrypted_delivery_request",
                "registry_hub": "registry_chat_001",
                "request_id": "req_invalid",
                "message_id": "msg_invalid",
                "sender_id": "dev_TRINITY",
                "attempt_delivery": "true",
                "retain_policy_decision": "yes",
            }
        ],
        "assertions": [
            {
                "type": "encrypted_delivery_result_contains",
                "registry_hub": "registry_chat_001",
                "delivery_attempted": "false",
            },
            {
                "type": "encrypted_delivery_audit_contains",
                "registry_hub": "registry_chat_001",
                "envelope_accepted": "false",
            },
            {
                "type": "encrypted_delivery_result_contains",
                "registry_hub": "registry_chat_001",
                "expected_count": "one",
            },
            {
                "type": "encrypted_delivery_audit_contains",
                "registry_hub": "registry_chat_001",
                "min_count": -1,
            },
        ],
    }


def _load_yaml(path: Path):
    import yaml

    return yaml.safe_load(path.read_text(encoding="utf-8"))
