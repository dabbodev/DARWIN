from __future__ import annotations

import inspect
from pathlib import Path

import yaml

import darwin.sim.assertions as scenario_assertions
import darwin.sim.runner as scenario_runner
from darwin.models import (
    LaneAdmissionDecision,
    RendezvousPollResult,
    StreamOffer,
    TrafficHub,
)
from darwin.sim.assertions import evaluate_assertion
from darwin.sim.runner import run_scenario
from darwin.sim.scenarios import list_scenario_files, validate_scenario_dict
from darwin.sim.validation import ASSERTION_REQUIRED_FIELDS, STEP_REQUIRED_FIELDS

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_DIR = PROJECT_ROOT / "scenarios"


def test_v1_2_stream_offer_actions_and_assertions_are_validated():
    assert STEP_REQUIRED_FIELDS["hold_stream_offer"] == (
        "registry_hub",
        "offer_id",
        "requester_id",
        "target_handle",
        "lane_signature",
    )
    assert STEP_REQUIRED_FIELDS["poll_held_stream_offers"] == (
        "registry_hub",
        "request_id",
        "offer_id",
        "polling_hub_id",
        "requester_id",
        "target_scope",
    )
    assert STEP_REQUIRED_FIELDS["evaluate_lane_admission_policy"] == (
        "registry_hub",
        "policy_id",
        "hub_id",
        "offer_id",
    )
    assert ASSERTION_REQUIRED_FIELDS["held_stream_offer_contains"] == (
        "registry_hub",
    )
    assert ASSERTION_REQUIRED_FIELDS["rendezvous_poll_result_contains"] == (
        "registry_hub",
    )
    assert ASSERTION_REQUIRED_FIELDS["lane_admission_decision_contains"] == (
        "registry_hub",
    )


def test_v1_2_validation_rejects_missing_fields_booleans_lists_and_counts():
    result = validate_scenario_dict(_minimal_invalid_validation_scenario())

    assert not result.valid
    assert [error.location for error in result.errors] == [
        "steps[0].target_handle",
        "steps[0].replace_existing",
        "steps[0].visibility_tier",
        "steps[1].active_only",
        "steps[1].current_order",
        "steps[2].require_discoverable",
        "steps[2].allowed_lane_signatures[1]",
        "assertions[0].expected_count",
        "assertions[1].visibility_tier",
        "assertions[2].matched_offer_ids[1]",
        "assertions[3].allowed",
    ]


def test_v1_2_hold_poll_and_admission_action_execution():
    result = run_scenario(SCENARIOS_DIR / "053_stream_offer_rendezvous_allowed.yaml")
    hub = result.world.registry_hubs["registry_chat_001"]
    offers = [item for item in result.world.action_results if isinstance(item, StreamOffer)]
    polls = [
        item
        for item in result.world.action_results
        if isinstance(item, RendezvousPollResult)
    ]
    decisions = [
        item
        for item in result.world.action_results
        if isinstance(item, LaneAdmissionDecision)
    ]

    assert result.passed
    assert [offer.offer_id for offer in hub.held_stream_offers] == ["offer_chat_001"]
    assert offers[0].status.status == "held"
    assert polls[0].status.status == "matched"
    assert list(polls[0].matched_offer_ids) == ["offer_chat_001"]
    assert decisions[0].status.status == "pass_down"
    assert decisions[0].reason.reason == "accepted"
    assert decisions[0].allowed is True
    assert hub.message_delivery_results == []
    assert hub.message_inboxes == {}


def test_v1_2_assertions_pass_and_fail_by_count():
    result = run_scenario(SCENARIOS_DIR / "053_stream_offer_rendezvous_allowed.yaml")

    passing = evaluate_assertion(
        result.world,
        {
            "type": "rendezvous_poll_result_contains",
            "registry_hub": "registry_chat_001",
            "request_id": "poll_req_chat_001",
            "matched_offer_ids": ["offer_chat_001"],
            "expected_count": 1,
        },
    )
    failing = evaluate_assertion(
        result.world,
        {
            "type": "lane_admission_decision_contains",
            "registry_hub": "registry_chat_001",
            "status": "pass_down",
            "expected_count": 2,
        },
    )

    assert passing.passed
    assert passing.actual["records"][0]["matched_offer_ids"] == ["offer_chat_001"]
    assert not failing.passed
    assert failing.actual["count"] == 1
    assert failing.expected["expected_count"] == 2


def test_v1_2_checked_in_stream_offer_scenarios_validate_and_run():
    scenario_files = [
        path
        for path in list_scenario_files(SCENARIOS_DIR)
        if path.name[:3] in {"053", "054", "055", "056", "057"}
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

    assert [path.name[:3] for path in scenario_files] == [
        "053",
        "054",
        "055",
        "056",
        "057",
    ]
    assert not failures


def test_v1_2_scenario_sweep_remains_contiguous_001_through_060():
    scenario_numbers = sorted(
        int(path.name[:3])
        for path in list_scenario_files(SCENARIOS_DIR)
        if path.name[:3].isdigit()
    )

    assert scenario_numbers == list(range(1, 61))


def test_v1_2_existing_scenarios_001_through_052_still_pass():
    failures = []
    for scenario_file in list_scenario_files(SCENARIOS_DIR):
        if not scenario_file.name[:3].isdigit() or int(scenario_file.name[:3]) > 52:
            continue
        result = run_scenario(scenario_file)
        if not result.passed:
            failures.append(f"{scenario_file}: {result.assertion_results}")

    assert not failures


def test_v1_2_stream_offer_scenario_actions_do_not_deliver_or_route():
    result = run_scenario(SCENARIOS_DIR / "057_stream_offer_rendezvous_quarantined.yaml")
    registry_hub = result.world.registry_hubs["registry_chat_001"]
    traffic_hub = TrafficHub(hub_id="traffic_chat_001")

    assert result.passed
    assert registry_hub.message_delivery_results == []
    assert registry_hub.message_inboxes == {}
    assert traffic_hub.routes == {}
    assert traffic_hub.lanes == {}


def test_v1_2_scenario_dsl_does_not_import_networking_dns_or_socket_libraries():
    source = inspect.getsource(scenario_runner) + inspect.getsource(scenario_assertions)

    assert "import socket" not in source
    assert "import http" not in source
    assert "import urllib" not in source
    assert "import requests" not in source
    assert "getaddrinfo" not in source
    assert "websocket" not in source.lower()


def _minimal_invalid_validation_scenario() -> dict[str, object]:
    return {
        "scenario_id": "v1_2_invalid_stream_offer_validation",
        "name": "v1.2 invalid stream offer validation",
        "category": "stream_offer",
        "setup": {
            "registry_hubs": [
                {"hub_id": "registry_chat_001", "scope_path": "global.chat"}
            ]
        },
        "steps": [
            {
                "action": "hold_stream_offer",
                "registry_hub": "registry_chat_001",
                "offer_id": "offer_invalid",
                "requester_id": "dev_TRINITY",
                "lane_signature": "basic_messaging:v1",
                "replace_existing": "false",
                "visibility_tier": -1,
            },
            {
                "action": "poll_held_stream_offers",
                "registry_hub": "registry_chat_001",
                "request_id": "poll_invalid",
                "offer_id": "offer_invalid",
                "polling_hub_id": "hub_private_child",
                "requester_id": "hub_private_child",
                "target_scope": "global.chat",
                "active_only": "true",
                "current_order": "later",
            },
            {
                "action": "evaluate_lane_admission_policy",
                "registry_hub": "registry_chat_001",
                "policy_id": "policy_invalid",
                "hub_id": "registry_chat_001",
                "offer_id": "offer_invalid",
                "require_discoverable": "yes",
                "allowed_lane_signatures": ["basic_messaging:v1", 42],
            },
        ],
        "assertions": [
            {
                "type": "held_stream_offer_contains",
                "registry_hub": "registry_chat_001",
                "expected_count": -1,
            },
            {
                "type": "held_stream_offer_contains",
                "registry_hub": "registry_chat_001",
                "visibility_tier": "private",
            },
            {
                "type": "rendezvous_poll_result_contains",
                "registry_hub": "registry_chat_001",
                "matched_offer_ids": ["offer_invalid", 42],
            },
            {
                "type": "lane_admission_decision_contains",
                "registry_hub": "registry_chat_001",
                "allowed": "false",
            },
        ],
    }


def _load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))
