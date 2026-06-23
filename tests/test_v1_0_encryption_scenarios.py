from __future__ import annotations

import inspect
import socket
from pathlib import Path

import pytest

import darwin.sim.assertions as scenario_assertions
import darwin.sim.runner as scenario_runner
from darwin.models.encryption import EncryptionPolicyDecision
from darwin.sim.assertions import evaluate_assertion
from darwin.sim.runner import run_scenario
from darwin.sim.scenarios import list_scenario_files, validate_scenario_dict
from darwin.sim.validation import ASSERTION_REQUIRED_FIELDS, STEP_REQUIRED_FIELDS

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_DIR = PROJECT_ROOT / "scenarios"


def _successful_policy_scenario() -> dict[str, object]:
    return {
        "scenario_id": "v1_0_encryption_policy_test",
        "name": "v1.0 encryption policy test",
        "category": "encryption",
        "setup": {
            "registry_hubs": [
                {"hub_id": "registry_chat_001", "scope_path": "global.chat"}
            ],
            "devices": [{"device_id": "dev_NEO", "label": "neo"}],
        },
        "steps": [
            {
                "action": "register_lane_definition",
                "registry_hub": "registry_chat_001",
                "lane_signature": "basic_messaging:v1",
            },
            {
                "action": "register_mailbox",
                "registry_hub": "registry_chat_001",
                "mailbox_id": "mailbox_neo",
                "canonical_device_id": "dev_NEO",
                "local_name": "neo",
                "scope": "global.chat",
            },
            {
                "action": "bind_mailbox_capability",
                "registry_hub": "registry_chat_001",
                "mailbox_id": "mailbox_neo",
                "lane_signature": "basic_messaging:v1",
            },
            {
                "action": "register_encryption_identity",
                "registry_hub": "registry_chat_001",
                "encryption_identity_id": "enc_mailbox_neo",
                "subject_id": "mailbox_neo",
                "subject_kind": "mailbox",
            },
            {
                "action": "register_key_bundle_reference",
                "registry_hub": "registry_chat_001",
                "key_bundle_id": "kb_mailbox_neo_001",
                "encryption_identity_id": "enc_mailbox_neo",
            },
            {
                "action": "register_mailbox_encryption_binding",
                "registry_hub": "registry_chat_001",
                "mailbox_id": "mailbox_neo",
                "encryption_identity_id": "enc_mailbox_neo",
                "key_bundle_id": "kb_mailbox_neo_001",
                "required_for_lanes": ["basic_messaging:v1"],
            },
            {
                "action": "register_mailbox_encryption_policy",
                "registry_hub": "registry_chat_001",
                "policy_id": "policy_mailbox_neo",
                "mailbox_id": "mailbox_neo",
            },
            {
                "action": "evaluate_mailbox_encryption_policy",
                "registry_hub": "registry_chat_001",
                "mailbox_id": "mailbox_neo",
                "lane_signature": "basic_messaging:v1",
                "message_id": "msg_symbolic_001",
                "envelope_id": "env_msg_symbolic_001",
                "encryption_identity_id": "enc_mailbox_neo",
                "key_bundle_id": "kb_mailbox_neo_001",
            },
        ],
        "assertions": [],
    }


def test_v1_0_encryption_actions_and_assertions_are_validated():
    assert STEP_REQUIRED_FIELDS["register_encryption_identity"] == (
        "registry_hub",
        "encryption_identity_id",
        "subject_id",
        "subject_kind",
    )
    assert STEP_REQUIRED_FIELDS["register_key_bundle_reference"] == (
        "registry_hub",
        "key_bundle_id",
        "encryption_identity_id",
    )
    assert STEP_REQUIRED_FIELDS["register_mailbox_encryption_binding"] == (
        "registry_hub",
        "mailbox_id",
        "encryption_identity_id",
        "key_bundle_id",
    )
    assert STEP_REQUIRED_FIELDS["register_mailbox_encryption_policy"] == (
        "registry_hub",
        "policy_id",
        "mailbox_id",
    )
    assert STEP_REQUIRED_FIELDS["evaluate_mailbox_encryption_policy"] == (
        "registry_hub",
        "mailbox_id",
        "lane_signature",
    )
    assert ASSERTION_REQUIRED_FIELDS["encryption_identity_registered"] == (
        "registry_hub",
        "encryption_identity_id",
    )
    assert ASSERTION_REQUIRED_FIELDS["key_bundle_registered"] == (
        "registry_hub",
        "key_bundle_id",
    )
    assert ASSERTION_REQUIRED_FIELDS["mailbox_encryption_binding_registered"] == (
        "registry_hub",
        "mailbox_id",
    )
    assert ASSERTION_REQUIRED_FIELDS["mailbox_encryption_policy_registered"] == (
        "registry_hub",
        "policy_id",
    )
    assert ASSERTION_REQUIRED_FIELDS["encryption_policy_decision_contains"] == (
        "registry_hub",
    )


def test_v1_0_encryption_validation_rejects_missing_fields_counts_and_booleans():
    scenario = _successful_policy_scenario()
    scenario["steps"] = [
        {
            "action": "register_encryption_identity",
            "registry_hub": "registry_chat_001",
            "encryption_identity_id": "enc_mailbox_neo",
            "subject_id": "mailbox_neo",
        },
        {
            "action": "register_mailbox_encryption_policy",
            "registry_hub": "registry_chat_001",
            "policy_id": "policy_mailbox_neo",
            "mailbox_id": "mailbox_neo",
            "allow_plaintext_fallback": "false",
        },
    ]
    scenario["assertions"] = [
        {
            "type": "mailbox_encryption_policy_registered",
            "registry_hub": "registry_chat_001",
            "policy_id": "policy_mailbox_neo",
            "allow_plaintext_fallback": "false",
        },
        {
            "type": "encryption_policy_decision_contains",
            "registry_hub": "registry_chat_001",
            "encryption_required": "true",
        },
        {
            "type": "encryption_policy_decision_contains",
            "registry_hub": "registry_chat_001",
            "expected_count": "one",
        },
        {
            "type": "encryption_policy_decision_contains",
            "registry_hub": "registry_chat_001",
            "min_count": -1,
        },
    ]

    result = validate_scenario_dict(scenario)

    assert not result.valid
    assert [error.location for error in result.errors] == [
        "steps[0].subject_kind",
        "steps[1].allow_plaintext_fallback",
        "assertions[0].allow_plaintext_fallback",
        "assertions[1].encryption_required",
        "assertions[2].expected_count",
        "assertions[3].min_count",
    ]


def test_v1_0_successful_policy_action_path_does_not_deliver_or_use_network(
    monkeypatch: pytest.MonkeyPatch,
):
    def fail_dns(*args, **kwargs):
        raise AssertionError("DNS lookup should not run")

    def fail_socket(*args, **kwargs):
        raise AssertionError("socket should not open")

    monkeypatch.setattr(socket, "getaddrinfo", fail_dns)
    monkeypatch.setattr(socket, "socket", fail_socket)

    result = run_scenario(_successful_policy_scenario())
    hub = result.world.registry_hubs["registry_chat_001"]
    decisions = [
        action_result
        for action_result in result.world.action_results
        if isinstance(action_result, EncryptionPolicyDecision)
    ]

    assert result.passed
    assert decisions[-1].status.status == "accepted"
    assert decisions[-1].metadata["registry_hub"] == "registry_chat_001"
    assert decisions[-1].metadata["delivery_behavior_changed"] is False
    assert hub.encryption_policy_decision_history[-1].status.status == "accepted"
    assert hub.message_delivery_results == []
    assert hub.message_inboxes == {}


def test_v1_0_encryption_registration_assertions_pass():
    result = run_scenario(_successful_policy_scenario())

    assertions = [
        {
            "type": "encryption_identity_registered",
            "registry_hub": "registry_chat_001",
            "encryption_identity_id": "enc_mailbox_neo",
            "subject_id": "mailbox_neo",
            "subject_kind": "mailbox",
            "status": "active",
        },
        {
            "type": "key_bundle_registered",
            "registry_hub": "registry_chat_001",
            "key_bundle_id": "kb_mailbox_neo_001",
            "encryption_identity_id": "enc_mailbox_neo",
            "status": "active",
        },
        {
            "type": "mailbox_encryption_binding_registered",
            "registry_hub": "registry_chat_001",
            "mailbox_id": "mailbox_neo",
            "lane_signature": "basic_messaging:v1",
        },
        {
            "type": "mailbox_encryption_policy_registered",
            "registry_hub": "registry_chat_001",
            "policy_id": "policy_mailbox_neo",
            "lane_signature": "basic_messaging:v1",
            "profile": "symbolic_e2ee_v1",
            "allow_plaintext_fallback": False,
        },
    ]

    evaluated = [evaluate_assertion(result.world, assertion) for assertion in assertions]

    assert all(assertion_result.passed for assertion_result in evaluated)


def test_v1_0_policy_decision_assertion_passes_and_fails_by_count():
    result = run_scenario(_successful_policy_scenario())

    passing = evaluate_assertion(
        result.world,
        {
            "type": "encryption_policy_decision_contains",
            "registry_hub": "registry_chat_001",
            "policy_id": "policy_mailbox_neo",
            "message_id": "msg_symbolic_001",
            "status": "accepted",
            "encryption_required": True,
            "envelope_accepted": True,
            "expected_count": 1,
        },
    )
    failing = evaluate_assertion(
        result.world,
        {
            "type": "encryption_policy_decision_contains",
            "registry_hub": "registry_chat_001",
            "status": "accepted",
            "expected_count": 2,
        },
    )

    assert passing.passed
    assert passing.actual["source"] == "retained_history"
    assert passing.actual["records"][0]["metadata"]["registry_hub"] == (
        "registry_chat_001"
    )
    assert not failing.passed
    assert failing.actual["count"] == 1
    assert failing.expected["expected_count"] == 2


def test_v1_0_checked_in_encryption_scenarios_validate_and_run():
    scenario_files = [
        path
        for path in list_scenario_files(SCENARIOS_DIR)
        if path.name[:3] in {"047", "048", "049"}
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

    assert [path.name[:3] for path in scenario_files] == ["047", "048", "049"]
    assert not failures


def test_scenario_sweep_remains_contiguous_001_through_057():
    scenario_numbers = sorted(
        int(path.name[:3])
        for path in list_scenario_files(SCENARIOS_DIR)
        if path.name[:3].isdigit()
    )

    assert scenario_numbers == list(range(1, 58))


def test_v1_0_scenario_dsl_does_not_import_crypto_libraries():
    source = inspect.getsource(scenario_runner) + inspect.getsource(scenario_assertions)

    assert "import secrets" not in source
    assert "import cryptography" not in source
    assert "from cryptography" not in source


def _load_yaml(path: Path):
    import yaml

    return yaml.safe_load(path.read_text(encoding="utf-8"))
