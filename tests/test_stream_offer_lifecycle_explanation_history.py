"""Tests for retained RegistryHub-local lifecycle explanation history."""

from __future__ import annotations

import json
from copy import deepcopy

from darwin.models import (
    RegistryHub,
    StreamOffer,
    StreamOfferLifecycleExplanation,
    make_stream_offer,
)
from darwin.registry import (
    apply_stream_offer_lifecycle_plan,
    explain_stream_offer_lifecycle_apply_result,
    explain_stream_offer_lifecycle_plan,
    hold_stream_offer,
    plan_stream_offer_expiration,
    query_stream_offer_lifecycle_explanations,
    record_stream_offer_lifecycle_explanation,
    record_stream_offer_lifecycle_explanations,
    summarize_stream_offer_lifecycle_explanation_history,
)
from darwin.sim.world import World


def test_registry_hub_lifecycle_explanation_history_defaults_empty():
    hub = _hub()

    assert hub.stream_offer_lifecycle_explanation_history == []


def test_explanation_records_can_be_retained_on_registry_hub():
    hub = _hub()
    details = {"labels": ("manual",), "count": 1}

    explanation = record_stream_offer_lifecycle_explanation(
        hub,
        StreamOfferLifecycleExplanation(
            hub_id=hub.hub_id,
            offer_id="offer_001",
            category="active",
            reason="active_by_plan",
            status="active",
            checked_at=3,
            source="lifecycle_plan",
            details=details,
        ),
    )

    assert hub.stream_offer_lifecycle_explanation_history == [explanation]
    assert explanation.details == {"labels": ["manual"], "count": 1}
    assert details == {"labels": ("manual",), "count": 1}


def test_multiple_explanations_are_recorded_and_queried_deterministically():
    hub = _hub()
    first = _explanation(
        hub_id=hub.hub_id,
        offer_id="offer_001",
        category="expired",
        reason="expired_by_plan",
        status="expired",
        checked_at=4,
        source="lifecycle_plan",
    )
    second = _explanation(
        hub_id=hub.hub_id,
        offer_id="offer_002",
        category="applied",
        reason="applied_by_result",
        status="applied",
        checked_at=4,
        source="lifecycle_apply_result",
    )
    third = _explanation(
        hub_id="registry_remote_001",
        offer_id="offer_001",
        category="skipped",
        reason="skipped_by_result",
        status="skipped",
        checked_at=5,
        source="lifecycle_apply_result",
    )

    recorded = record_stream_offer_lifecycle_explanations(
        hub,
        (first, second, third),
    )

    assert recorded == [first, second, third]
    assert hub.stream_offer_lifecycle_explanation_history == [first, second, third]
    assert query_stream_offer_lifecycle_explanations(hub, hub_id=hub.hub_id) == [
        first,
        second,
    ]
    assert query_stream_offer_lifecycle_explanations(hub, offer_id="offer_001") == [
        first,
        third,
    ]
    assert query_stream_offer_lifecycle_explanations(hub, category="applied") == [
        second
    ]
    assert query_stream_offer_lifecycle_explanations(
        hub,
        reason="skipped_by_result",
    ) == [third]
    assert query_stream_offer_lifecycle_explanations(hub, status="expired") == [
        first
    ]
    assert query_stream_offer_lifecycle_explanations(
        hub,
        source="lifecycle_apply_result",
    ) == [second, third]
    assert query_stream_offer_lifecycle_explanations(
        hub,
        offer_id="offer_001",
        category="applied",
    ) == []


def test_explanation_history_summaries_are_json_safe_copied_and_in_order():
    hub = _hub()
    record_stream_offer_lifecycle_explanation(
        hub,
        _explanation(
            hub_id=hub.hub_id,
            offer_id="offer_001",
            category="active",
            reason="active_by_plan",
            status="active",
            checked_at=3,
            source="lifecycle_plan",
            details={"labels": ("inspect",)},
        ),
    )

    summary = summarize_stream_offer_lifecycle_explanation_history(hub)
    summary[0]["details"]["labels"].append("mutated")

    assert summarize_stream_offer_lifecycle_explanation_history(hub) == [
        {
            "hub_id": "registry_chat_001",
            "offer_id": "offer_001",
            "category": "active",
            "reason": "active_by_plan",
            "status": "active",
            "checked_at": 3,
            "source": "lifecycle_plan",
            "details": {"labels": ["inspect"]},
        }
    ]
    json.dumps(summary, sort_keys=True)


def test_explanation_history_is_explicit_and_does_not_mutate_lifecycle_state():
    hub = _hub()
    hold_stream_offer(hub, _offer(offer_id="offer_expired", expires_order=1))
    hold_stream_offer(hub, _offer(offer_id="offer_active", expires_order=9))
    held_before = deepcopy([offer.to_summary() for offer in hub.held_stream_offers])
    transition_history_before = list(hub.stream_offer_status_transition_history)

    plan = plan_stream_offer_expiration(hub, checked_at=5)
    plan_before = plan.to_summary()
    plan_explanations = explain_stream_offer_lifecycle_plan(plan)

    assert hub.stream_offer_lifecycle_explanation_history == []

    result = apply_stream_offer_lifecycle_plan(hub, plan, record_transition=False)
    result_before = result.to_summary()
    held_after_apply = deepcopy([offer.to_summary() for offer in hub.held_stream_offers])
    apply_explanations = explain_stream_offer_lifecycle_apply_result(result)

    assert hub.stream_offer_lifecycle_explanation_history == []

    record_stream_offer_lifecycle_explanations(hub, plan_explanations)
    record_stream_offer_lifecycle_explanations(hub, apply_explanations)
    query_stream_offer_lifecycle_explanations(hub, offer_id="offer_expired")
    summarize_stream_offer_lifecycle_explanation_history(hub)

    assert held_before[0]["status"] == "held"
    assert [offer.to_summary() for offer in hub.held_stream_offers] == held_after_apply
    assert plan.to_summary() == plan_before
    assert result.to_summary() == result_before
    assert hub.stream_offer_status_transition_history == transition_history_before


def test_detailed_snapshot_includes_copied_explanation_history_but_compact_does_not():
    world = World()
    hub = world.create_registry_hub(
        hub_id="registry_chat_001",
        scope_path="global.chat",
    )
    record_stream_offer_lifecycle_explanation(
        hub,
        _explanation(
            hub_id=hub.hub_id,
            offer_id="offer_001",
            category="active",
            reason="active_by_plan",
            status="active",
            checked_at=3,
            source="lifecycle_plan",
            details={"labels": ("snapshot",)},
        ),
    )

    compact = world.snapshot()
    detailed = world.snapshot(detailed=True)
    hub_snapshot = detailed["registry_hubs"]["registry_chat_001"]
    hub_snapshot["stream_offer_lifecycle_explanation_history"][0]["details"][
        "labels"
    ].append("mutated")

    fresh = world.snapshot(detailed=True)["registry_hubs"]["registry_chat_001"]

    assert compact == {
        "time": 0,
        "devices": [],
        "registry_hubs": ["registry_chat_001"],
        "traffic_hubs": [],
        "lanes": [],
    }
    assert "stream_offer_lifecycle_explanation_history" not in compact
    assert fresh["stream_offer_lifecycle_explanation_history"][0]["details"] == {
        "labels": ["snapshot"]
    }


def _hub() -> RegistryHub:
    return RegistryHub(hub_id="registry_chat_001", scope_path="global.chat")


def _offer(
    *,
    offer_id: str,
    status: str = "held",
    created_order: int = 0,
    expires_order: int | None = None,
) -> StreamOffer:
    offer = make_stream_offer(
        offer_id=offer_id,
        requester_id="dev_A9F3",
        target_handle="alias:neo",
        lane_signature="basic_messaging:v1",
        rendezvous_scope="global.chat",
        created_order=created_order,
        expires_order=expires_order,
    )
    return StreamOffer(
        offer_id=offer.offer_id,
        requester_id=offer.requester_id,
        target_handle=offer.target_handle,
        lane_signature=offer.lane_signature,
        requested_mode=offer.requested_mode,
        visibility_tier=offer.visibility_tier,
        status=status,
        rendezvous_scope=offer.rendezvous_scope,
        created_order=offer.created_order,
        expires_order=offer.expires_order,
        metadata=offer.metadata,
    )


def _explanation(
    *,
    hub_id: str,
    offer_id: str,
    category: str,
    reason: str,
    status: str,
    checked_at: int | None = None,
    source: str | None = None,
    details: dict[str, object] | None = None,
) -> StreamOfferLifecycleExplanation:
    return StreamOfferLifecycleExplanation(
        hub_id=hub_id,
        offer_id=offer_id,
        category=category,
        reason=reason,
        status=status,
        checked_at=checked_at,
        source=source,
        details=details,
    )
