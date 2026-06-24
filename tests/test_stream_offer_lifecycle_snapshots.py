from __future__ import annotations

import json
from pathlib import Path

from darwin.models import (
    StreamOfferLifecycleApplyResult,
    StreamOfferLifecyclePlan,
)
from darwin.sim.runner import run_scenario
from darwin.sim.world import World

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_DIR = PROJECT_ROOT / "scenarios"


def test_lifecycle_scenario_detailed_snapshot_exposes_lifecycle_artifacts():
    result = run_scenario(
        SCENARIOS_DIR / "059_stream_offer_lifecycle_apply_records_transition.yaml"
    )
    compact = result.world.snapshot()
    snapshot = result.final_snapshot
    hub_snapshot = snapshot["registry_hubs"]["registry_chat_001"]

    json.dumps(snapshot, sort_keys=True)
    assert compact == {
        "time": 4,
        "devices": [],
        "registry_hubs": ["registry_chat_001"],
        "traffic_hubs": [],
        "lanes": [],
    }
    assert "stream_offer_lifecycle_plans" not in compact
    assert "stream_offer_lifecycle_apply_results" not in compact
    assert "stream_offer_status_transition_history" not in compact

    assert snapshot["stream_offer_lifecycle_plans"][0]["hub_id"] == (
        "registry_chat_001"
    )
    assert snapshot["stream_offer_lifecycle_plans"][0]["checked_at"] == 5
    assert snapshot["stream_offer_lifecycle_plans"][0]["expired_offer_ids"] == [
        "offer_lifecycle_apply_recorded"
    ]
    assert snapshot["stream_offer_lifecycle_apply_results"][0][
        "applied_offer_ids"
    ] == ["offer_lifecycle_apply_recorded"]
    assert snapshot["stream_offer_lifecycle_apply_results"][0][
        "recorded_transition_count"
    ] == 1
    assert hub_snapshot["stream_offer_status_transition_history"] == [
        {
            "offer_id": "offer_lifecycle_apply_recorded",
            "previous_status": "held",
            "new_status": "expired",
            "reason": "expired",
            "hub_id": "registry_chat_001",
            "actor_id": "ops_local",
            "request_id": "lifecycle_apply_001",
            "metadata": {"source": "scenario_059"},
            "sequence": None,
        }
    ]


def test_lifecycle_action_result_snapshot_ordering_and_copies_are_stable():
    world = World()
    world.action_results.extend(
        [
            StreamOfferLifecyclePlan(hub_id="registry_b", checked_at=2),
            StreamOfferLifecycleApplyResult(
                hub_id="registry_a",
                plan_checked_at=1,
                applied_offer_ids=("offer_a",),
                recorded_transition_count=1,
                metadata={"labels": ("apply_a",)},
            ),
            StreamOfferLifecyclePlan(
                hub_id="registry_a",
                checked_at=1,
                expired_offer_ids=("offer_a",),
                metadata={"labels": ("plan_a",)},
            ),
            StreamOfferLifecycleApplyResult(
                hub_id="registry_b",
                plan_checked_at=2,
                applied_offer_ids=("offer_b",),
            ),
        ]
    )

    snapshot = world.snapshot(detailed=True)
    snapshot["stream_offer_lifecycle_plans"][1]["expired_offer_ids"].append(
        "mutated"
    )
    snapshot["stream_offer_lifecycle_plans"][1]["metadata"]["labels"].append(
        "mutated"
    )
    snapshot["stream_offer_lifecycle_apply_results"][0]["metadata"]["labels"].append(
        "mutated"
    )
    fresh = world.snapshot(detailed=True)

    assert [plan["hub_id"] for plan in fresh["stream_offer_lifecycle_plans"]] == [
        "registry_b",
        "registry_a",
    ]
    assert [
        result["hub_id"]
        for result in fresh["stream_offer_lifecycle_apply_results"]
    ] == ["registry_a", "registry_b"]
    assert fresh["stream_offer_lifecycle_plans"][1]["expired_offer_ids"] == [
        "offer_a"
    ]
    assert fresh["stream_offer_lifecycle_plans"][1]["metadata"] == {
        "labels": ["plan_a"]
    }
    assert fresh["stream_offer_lifecycle_apply_results"][0]["metadata"] == {
        "labels": ["apply_a"]
    }
    assert "stream_offer_lifecycle_plans" not in world.snapshot()
