from __future__ import annotations

import json
import socket
from pathlib import Path

from darwin.sim.assertions import evaluate_assertion
from darwin.sim.runner import run_scenario
from darwin.sim.scenarios import list_scenario_files, validate_scenario_dict
from darwin.sim.validation import ASSERTION_REQUIRED_FIELDS, STEP_REQUIRED_FIELDS

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_DIR = PROJECT_ROOT / "scenarios"


def _successful_message_scenario() -> dict[str, object]:
    return {
        "scenario_id": "v0_9_message_delivery_test",
        "name": "v0.9 message delivery test",
        "category": "mailbox",
        "setup": {
            "registry_hubs": [
                {"hub_id": "registry_chat_001", "scope_path": "global.chat"}
            ],
            "traffic_hubs": [{"hub_id": "traffic_chat_001"}],
            "devices": [{"device_id": "dev_NEO", "label": "neo"}],
        },
        "steps": [
            {
                "action": "register_device",
                "registry_hub": "registry_chat_001",
                "device": "dev_NEO",
                "label": "neo",
            },
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
                "action": "register_adapter_endpoint",
                "registry_hub": "registry_chat_001",
                "endpoint_id": "endpoint_mailbox_neo",
                "subject_id": "mailbox_neo",
                "subject_kind": "mailbox",
                "adapter_kind": "in_memory",
                "status": "available",
                "lane_signatures": ["basic_messaging:v1"],
                "scope": "global.chat",
            },
            {
                "action": "deliver_message",
                "registry_hub": "registry_chat_001",
                "message_id": "msg_001",
                "sender_id": "dev_TRINITY",
                "recipient_address": "darwin://global.chat.neo/inbox",
                "payload": "wake up",
            },
        ],
        "assertions": [],
    }


def test_v0_9_message_actions_and_assertions_are_validated():
    assert STEP_REQUIRED_FIELDS["register_lane_definition"] == (
        "registry_hub",
        "lane_signature",
    )
    assert STEP_REQUIRED_FIELDS["register_mailbox"] == (
        "registry_hub",
        "mailbox_id",
        "canonical_device_id",
        "local_name",
        "scope",
    )
    assert STEP_REQUIRED_FIELDS["bind_mailbox_capability"] == (
        "registry_hub",
        "mailbox_id",
        "lane_signature",
    )
    assert STEP_REQUIRED_FIELDS["register_adapter_endpoint"] == (
        "registry_hub",
        "endpoint_id",
        "subject_id",
        "subject_kind",
        "adapter_kind",
    )
    assert STEP_REQUIRED_FIELDS["deliver_message"] == (
        "registry_hub",
        "message_id",
        "sender_id",
        "recipient_address",
    )
    assert ASSERTION_REQUIRED_FIELDS["mailbox_registered"] == (
        "registry_hub",
        "mailbox_id",
    )
    assert ASSERTION_REQUIRED_FIELDS["mailbox_supports_lane"] == (
        "registry_hub",
        "mailbox_id",
        "lane_signature",
    )
    assert ASSERTION_REQUIRED_FIELDS["message_delivery_result_contains"] == (
        "registry_hub",
    )
    assert ASSERTION_REQUIRED_FIELDS["mailbox_inbox_contains"] == (
        "registry_hub",
        "mailbox_id",
    )


def test_v0_9_message_validation_rejects_missing_fields_and_invalid_markers():
    scenario = _successful_message_scenario()
    scenario["steps"] = [
        {
            "action": "deliver_message",
            "registry_hub": "registry_chat_001",
            "message_id": "msg_001",
            "sender_id": "dev_TRINITY",
        },
        {
            "action": "bind_mailbox_capability",
            "registry_hub": "registry_chat_001",
            "mailbox_id": "mailbox_neo",
            "lane_signature": "basic_messaging:v1",
            "enabled": "yes",
        },
    ]
    scenario["assertions"] = [
        {
            "type": "mailbox_supports_lane",
            "registry_hub": "registry_chat_001",
            "mailbox_id": "mailbox_neo",
            "lane_signature": "basic_messaging:v1",
            "enabled": "true",
        },
        {
            "type": "message_delivery_result_contains",
            "registry_hub": "registry_chat_001",
            "expected_count": -1,
        },
    ]

    result = validate_scenario_dict(scenario)

    assert not result.valid
    assert [error.location for error in result.errors] == [
        "steps[0].recipient_address",
        "steps[1].enabled",
        "assertions[0].enabled",
        "assertions[1].expected_count",
    ]


def test_v0_9_successful_delivery_action_path_does_not_touch_unrelated_state(
    monkeypatch,
):
    def fail_dns(*args, **kwargs):
        raise AssertionError("DNS lookup should not run")

    def fail_socket(*args, **kwargs):
        raise AssertionError("socket should not open")

    monkeypatch.setattr(socket, "getaddrinfo", fail_dns)
    monkeypatch.setattr(socket, "socket", fail_socket)

    result = run_scenario(_successful_message_scenario())
    hub = result.world.registry_hubs["registry_chat_001"]
    traffic_hub = result.world.traffic_hubs["traffic_chat_001"]

    assert result.passed
    assert hub.message_delivery_results[0].status.status == "delivered"
    assert hub.message_delivery_results[0].metadata["networking"] is False
    assert hub.message_delivery_results[0].metadata["dns_lookup"] is False
    assert hub.message_delivery_results[0].metadata["traffic_hub_routing"] is False
    assert [envelope.message_id for envelope in hub.message_inboxes["mailbox_neo"]] == [
        "msg_001"
    ]
    assert hub.aliases == {}
    assert hub.alias_bundles == {}
    assert hub.conflicts == {}
    assert hub.authority_outcome_history == []
    assert traffic_hub.routes == {}
    assert traffic_hub.lanes == {}
    assert traffic_hub.forwarding_log == []


def test_v0_9_delivery_result_assertion_passes_and_fails_by_count():
    result = run_scenario(_successful_message_scenario())

    passing = evaluate_assertion(
        result.world,
        {
            "type": "message_delivery_result_contains",
            "registry_hub": "registry_chat_001",
            "message_id": "msg_001",
            "mailbox_id": "mailbox_neo",
            "status": "delivered",
            "endpoint_id": "endpoint_mailbox_neo",
            "expected_count": 1,
        },
    )
    failing = evaluate_assertion(
        result.world,
        {
            "type": "message_delivery_result_contains",
            "registry_hub": "registry_chat_001",
            "message_id": "msg_001",
            "expected_count": 2,
        },
    )

    assert passing.passed
    assert passing.actual["records"][0]["status"] == "delivered"
    assert not failing.passed
    assert failing.actual["count"] == 1
    assert failing.expected["expected_count"] == 2


def test_v0_9_inbox_assertion_passes_and_fails_by_payload():
    result = run_scenario(_successful_message_scenario())

    passing = evaluate_assertion(
        result.world,
        {
            "type": "mailbox_inbox_contains",
            "registry_hub": "registry_chat_001",
            "mailbox_id": "mailbox_neo",
            "message_id": "msg_001",
            "sender_id": "dev_TRINITY",
            "payload": "wake up",
            "expected_count": 1,
        },
    )
    failing = evaluate_assertion(
        result.world,
        {
            "type": "mailbox_inbox_contains",
            "registry_hub": "registry_chat_001",
            "mailbox_id": "mailbox_neo",
            "payload": "wrong",
        },
    )

    assert passing.passed
    assert passing.actual["records"][0]["payload"] == "wake up"
    assert not failing.passed
    assert failing.actual["count"] == 0
    assert failing.expected["min_count"] == 1


def test_v0_9_detailed_snapshot_exposes_message_state_as_json_safe_copies():
    result = run_scenario(_successful_message_scenario())
    hub = result.world.registry_hubs["registry_chat_001"]
    compact_snapshot = result.world.snapshot()
    snapshot = result.final_snapshot

    json.dumps(snapshot, sort_keys=True)
    assert "message_inboxes" not in compact_snapshot
    assert "message_delivery_results" not in compact_snapshot

    hub_snapshot = snapshot["registry_hubs"]["registry_chat_001"]
    assert hub_snapshot["message_inboxes"]["mailbox_neo"][0]["message_id"] == "msg_001"
    assert hub_snapshot["message_delivery_results"][0]["status"] == "delivered"
    assert hub_snapshot["message_delivery_results"][0]["metadata"] == {
        "simulator_local": True,
        "networking": False,
        "dns_lookup": False,
        "traffic_hub_routing": False,
        "durable_queue": False,
        "durable_storage": False,
    }

    hub_snapshot["message_inboxes"]["mailbox_neo"][0]["payload"] = "mutated"
    hub_snapshot["message_delivery_results"][0]["metadata"]["networking"] = True

    assert hub.message_inboxes["mailbox_neo"][0].payload == "wake up"
    assert hub.message_delivery_results[0].metadata["networking"] is False


def test_v0_9_checked_in_message_scenarios_validate_and_run():
    scenario_files = [
        path
        for path in list_scenario_files(SCENARIOS_DIR)
        if path.name[:3] in {"044", "045", "046"}
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

    assert [path.name[:3] for path in scenario_files] == ["044", "045", "046"]
    assert not failures


def test_scenario_sweep_remains_contiguous_001_through_057():
    scenario_numbers = sorted(
        int(path.name[:3])
        for path in list_scenario_files(SCENARIOS_DIR)
        if path.name[:3].isdigit()
    )

    assert scenario_numbers == list(range(1, 58))


def _load_yaml(path: Path):
    import yaml

    return yaml.safe_load(path.read_text(encoding="utf-8"))
