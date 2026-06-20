from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from darwin.models import (
    LaneAdmissionDecision,
    RegistryHub,
    RendezvousPollResult,
    TrafficHub,
    make_lane_admission_policy,
    make_rendezvous_request,
    make_stream_offer,
)
from darwin.registry import (
    evaluate_lane_admission_policy,
    hold_stream_offer,
    poll_held_stream_offers,
    query_lane_admission_decisions,
    query_rendezvous_poll_results,
    record_lane_admission_decision,
    record_rendezvous_poll_result,
    summarize_lane_admission_decisions,
    summarize_rendezvous_poll_results,
)
from darwin.sim.assertions import evaluate_assertion
from darwin.sim.runner import run_scenario
from darwin.sim.world import World

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_DIR = PROJECT_ROOT / "scenarios"


def test_registry_hub_audit_histories_default_empty():
    hub = _hub()

    assert hub.rendezvous_poll_result_history == []
    assert hub.lane_admission_decision_history == []


def test_record_rendezvous_poll_result_appends_in_order():
    hub = _hub()
    first = _poll_result(hub, request_id="poll_req_001")
    second = _poll_result(hub, request_id="poll_req_002")

    assert record_rendezvous_poll_result(hub, first) is first
    assert record_rendezvous_poll_result(hub, second) is second
    assert hub.rendezvous_poll_result_history == [first, second]


def test_record_lane_admission_decision_appends_in_order():
    hub = _hub()
    first = _decision(hub, decision_id="decision_001")
    second = _decision(hub, decision_id="decision_002")

    assert record_lane_admission_decision(hub, first) is first
    assert record_lane_admission_decision(hub, second) is second
    assert hub.lane_admission_decision_history == [first, second]


def test_scenario_actions_record_poll_and_admission_histories():
    result = run_scenario(SCENARIOS_DIR / "053_stream_offer_rendezvous_allowed.yaml")
    hub = result.world.registry_hubs["registry_chat_001"]
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

    assert hub.rendezvous_poll_result_history == polls
    assert hub.lane_admission_decision_history == decisions
    assert polls[0].status.status == "matched"
    assert decisions[0].status.status == "pass_down"
    assert hub.message_delivery_results == []
    assert hub.message_inboxes == {}


def test_query_rendezvous_poll_results_filters_additively():
    hub = _hub()
    matched = _poll_result(
        hub,
        request_id="poll_req_match",
        polling_hub_id="hub_private_child",
        target_scope="global.chat",
        visibility_tier=1,
    )
    empty = _poll_result(
        hub,
        request_id="poll_req_empty",
        polling_hub_id="hub_other_child",
        target_scope="global.remote",
        visibility_tier=2,
    )
    record_rendezvous_poll_result(hub, matched)
    record_rendezvous_poll_result(hub, empty)

    assert query_rendezvous_poll_results(hub, request_id="poll_req_match") == [matched]
    assert query_rendezvous_poll_results(
        hub,
        polling_hub_id="hub_private_child",
    ) == [matched]
    assert query_rendezvous_poll_results(
        hub,
        parent_hub_id="registry_chat_001",
    ) == [matched, empty]
    assert query_rendezvous_poll_results(hub, target_scope="global.chat") == [matched]
    assert query_rendezvous_poll_results(hub, visibility_tier=2) == [empty]
    assert query_rendezvous_poll_results(hub, status="matched") == [matched]
    assert query_rendezvous_poll_results(hub, reason="offers_available") == [matched]
    assert query_rendezvous_poll_results(
        hub,
        matched_offer_id="offer_001",
    ) == [matched]
    assert query_rendezvous_poll_results(
        hub,
        target_scope="global.chat",
        status="empty",
    ) == []


def test_query_rendezvous_poll_results_is_read_only_and_summaries_are_copied():
    hub = _hub()
    record_rendezvous_poll_result(hub, _poll_result(hub))
    before = deepcopy(
        [result.to_summary() for result in hub.rendezvous_poll_result_history]
    )

    query_rendezvous_poll_results(hub).clear()
    summary = summarize_rendezvous_poll_results(hub)
    summary[0]["matched_offers"][0]["metadata"]["labels"].append("mutated")

    assert [
        result.to_summary()
        for result in hub.rendezvous_poll_result_history
    ] == before
    assert summarize_rendezvous_poll_results(hub)[0]["matched_offers"][0][
        "metadata"
    ] == {"labels": ["demo"]}
    json.dumps(summary)


def test_query_lane_admission_decisions_filters_additively():
    hub = _hub()
    allowed = _decision(hub, decision_id="decision_allowed")
    denied = _decision(
        hub,
        decision_id="decision_denied",
        offer_id="offer_002",
        policy_id="policy_chat_002",
        request_id="poll_req_002",
        requester_id="dev_BLOCKED",
        target_handle="alias:trinity",
        target_scope="global.remote",
        lane_signature="control:v1",
        status="deny",
        reason="explicit_requester_denied",
        allowed=False,
    )
    record_lane_admission_decision(hub, allowed)
    record_lane_admission_decision(hub, denied)

    assert query_lane_admission_decisions(hub, decision_id="decision_allowed") == [
        allowed
    ]
    assert query_lane_admission_decisions(hub, policy_id="policy_chat_002") == [
        denied
    ]
    assert query_lane_admission_decisions(hub, offer_id="offer_001") == [allowed]
    assert query_lane_admission_decisions(hub, request_id="poll_req_002") == [denied]
    assert query_lane_admission_decisions(hub, hub_id="registry_chat_001") == [
        allowed,
        denied,
    ]
    assert query_lane_admission_decisions(hub, requester_id="dev_BLOCKED") == [
        denied
    ]
    assert query_lane_admission_decisions(hub, target_handle="alias:trinity") == [
        denied
    ]
    assert query_lane_admission_decisions(hub, target_scope="global.remote") == [
        denied
    ]
    assert query_lane_admission_decisions(hub, lane_signature="control:v1") == [
        denied
    ]
    assert query_lane_admission_decisions(hub, status="pass_down") == [allowed]
    assert query_lane_admission_decisions(hub, reason="accepted") == [allowed]
    assert query_lane_admission_decisions(hub, allowed=False) == [denied]
    assert query_lane_admission_decisions(
        hub,
        requester_id="dev_BLOCKED",
        status="pass_down",
    ) == []


def test_query_lane_admission_decisions_is_read_only_and_summaries_are_copied():
    hub = _hub()
    record_lane_admission_decision(
        hub,
        _decision(hub, metadata={"labels": ("accepted",)}),
    )
    before = deepcopy(
        [decision.to_summary() for decision in hub.lane_admission_decision_history]
    )

    query_lane_admission_decisions(hub).clear()
    summary = summarize_lane_admission_decisions(hub)
    summary[0]["metadata"]["labels"].append("mutated")

    assert [
        decision.to_summary()
        for decision in hub.lane_admission_decision_history
    ] == before
    assert summarize_lane_admission_decisions(hub)[0]["metadata"][
        "labels"
    ] == ["accepted"]
    json.dumps(summary)


def test_assertions_prefer_retained_history_over_action_results():
    world = World()
    hub = world.create_registry_hub("registry_chat_001", "global.chat")
    retained = _poll_result(hub, request_id="poll_req_retained")
    action_only = _poll_result(hub, request_id="poll_req_action")
    record_rendezvous_poll_result(hub, retained)
    world.action_results.append(action_only)

    result = evaluate_assertion(
        world,
        {
            "type": "rendezvous_poll_result_contains",
            "registry_hub": "registry_chat_001",
            "request_id": "poll_req_action",
            "expected_count": 0,
        },
    )

    assert result.passed
    assert result.actual["source"] == "retained_history"
    assert result.actual["records"] == []


def test_assertions_fall_back_to_action_results_when_retained_history_is_empty():
    world = World()
    hub = world.create_registry_hub("registry_chat_001", "global.chat")
    world.action_results.append(_decision(hub))

    result = evaluate_assertion(
        world,
        {
            "type": "lane_admission_decision_contains",
            "registry_hub": "registry_chat_001",
            "decision_id": "decision_001",
            "expected_count": 1,
        },
    )

    assert result.passed
    assert result.actual["source"] == "action_results"


def test_detailed_snapshot_includes_audit_histories_and_compact_snapshot_does_not():
    result = run_scenario(SCENARIOS_DIR / "053_stream_offer_rendezvous_allowed.yaml")
    compact = result.world.snapshot()
    snapshot = result.final_snapshot
    hub_snapshot = snapshot["registry_hubs"]["registry_chat_001"]

    json.dumps(snapshot, sort_keys=True)
    assert "rendezvous_poll_result_history" not in compact
    assert "lane_admission_decision_history" not in compact
    assert hub_snapshot["held_stream_offers"][0]["offer_id"] == "offer_chat_001"
    assert hub_snapshot["rendezvous_poll_result_history"][0]["request_id"] == (
        "poll_req_chat_001"
    )
    assert hub_snapshot["lane_admission_decision_history"][0]["status"] == "pass_down"


def test_detailed_snapshot_audit_histories_are_copied():
    result = run_scenario(SCENARIOS_DIR / "053_stream_offer_rendezvous_allowed.yaml")
    snapshot = result.final_snapshot
    hub_snapshot = snapshot["registry_hubs"]["registry_chat_001"]

    hub_snapshot["rendezvous_poll_result_history"][0]["matched_offer_ids"].append(
        "mutated"
    )
    hub_snapshot["lane_admission_decision_history"][0]["metadata"][
        "networking"
    ] = True
    fresh = result.world.snapshot(detailed=True)["registry_hubs"]["registry_chat_001"]

    assert fresh["rendezvous_poll_result_history"][0]["matched_offer_ids"] == [
        "offer_chat_001"
    ]
    assert fresh["lane_admission_decision_history"][0]["metadata"][
        "networking"
    ] is False


def test_audit_history_helpers_do_not_deliver_or_mutate_traffic_hub():
    registry_hub = _hub()
    traffic_hub = TrafficHub(hub_id="traffic_chat_001")
    traffic_before = deepcopy(traffic_hub)

    record_rendezvous_poll_result(registry_hub, _poll_result(registry_hub))
    record_lane_admission_decision(registry_hub, _decision(registry_hub))
    query_rendezvous_poll_results(registry_hub)
    query_lane_admission_decisions(registry_hub)

    assert registry_hub.message_inboxes == {}
    assert registry_hub.message_delivery_results == []
    assert traffic_hub == traffic_before


def _hub() -> RegistryHub:
    return RegistryHub(hub_id="registry_chat_001", scope_path="global.chat")


def _poll_result(
    hub: RegistryHub,
    *,
    request_id: str = "poll_req_001",
    offer_id: str = "offer_001",
    polling_hub_id: str = "hub_private_child",
    target_scope: str = "global.chat",
    visibility_tier: int = 1,
) -> RendezvousPollResult:
    hold_stream_offer(
        hub,
        make_stream_offer(
            offer_id=offer_id,
            requester_id="dev_A9F3",
            target_handle="alias:neo",
            lane_signature="basic_messaging:v1",
            visibility_tier=1,
            rendezvous_scope="global.chat",
            metadata={"labels": ("demo",)},
        ),
        replace_existing=True,
    )
    request = make_rendezvous_request(
        request_id=request_id,
        offer_id=offer_id,
        polling_hub_id=polling_hub_id,
        requester_id=polling_hub_id,
        target_scope=target_scope,
        visibility_tier=visibility_tier,
    )
    return poll_held_stream_offers(hub, request)


def _decision(
    hub: RegistryHub,
    *,
    decision_id: str = "decision_001",
    offer_id: str = "offer_001",
    policy_id: str = "policy_chat_001",
    request_id: str = "poll_req_001",
    requester_id: str = "dev_A9F3",
    target_handle: str = "alias:neo",
    target_scope: str = "global.chat",
    lane_signature: str = "basic_messaging:v1",
    status: str = "pass_down",
    reason: str = "accepted",
    allowed: bool = True,
    metadata: dict[str, object] | None = None,
) -> LaneAdmissionDecision:
    offer = hold_stream_offer(
        hub,
        make_stream_offer(
            offer_id=offer_id,
            requester_id=requester_id,
            target_handle=target_handle,
            lane_signature=lane_signature,
            rendezvous_scope=target_scope,
        ),
        replace_existing=True,
    )
    request = make_rendezvous_request(
        request_id=request_id,
        offer_id=offer_id,
        polling_hub_id="hub_private_child",
        requester_id=requester_id,
        target_scope=target_scope,
        visibility_tier=1,
    )
    policy = make_lane_admission_policy(
        policy_id=policy_id,
        hub_id=hub.hub_id,
        default_status=status,
    )
    if reason == "accepted":
        return evaluate_lane_admission_policy(
            policy,
            offer,
            request=request,
            decision_id=decision_id,
            metadata=metadata,
        )
    return LaneAdmissionDecision(
        decision_id=decision_id,
        policy_id=policy_id,
        offer_id=offer_id,
        request_id=request_id,
        hub_id=hub.hub_id,
        requester_id=requester_id,
        target_handle=target_handle,
        target_scope=target_scope,
        lane_signature=lane_signature,
        status=status,
        reason=reason,
        allowed=allowed,
        metadata=metadata,
    )
