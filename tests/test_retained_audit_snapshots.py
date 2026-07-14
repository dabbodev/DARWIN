from __future__ import annotations

import json
from pathlib import Path

from darwin.models import (
    RetainedAuditCompactionApplyResult,
    RetainedAuditCompactionDecision,
    RetainedAuditReplaySummary,
)
from darwin.sim.runner import run_scenario
from darwin.sim.world import World

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_DIR = PROJECT_ROOT / "scenarios"


def test_detailed_snapshot_exposes_retained_audit_action_results():
    result = run_scenario(
        SCENARIOS_DIR / "069_retained_audit_compaction_apply.yaml"
    )
    compact = result.world.snapshot()
    detailed = result.final_snapshot

    json.dumps(detailed, sort_keys=True)
    assert compact == {
        "time": 10,
        "devices": [],
        "registry_hubs": ["registry_chat_001"],
        "traffic_hubs": [],
        "lanes": [],
    }
    assert "retained_audit_compaction_decisions" not in compact
    assert "retained_audit_replay_summaries" not in compact
    assert "retained_audit_compaction_apply_results" not in compact
    assert [
        decision["policy_id"]
        for decision in detailed["retained_audit_compaction_decisions"]
    ] == ["retained_audit_mixed_policy_069", "retained_audit_apply_policy_069"]
    assert detailed["retained_audit_replay_summaries"] == []
    assert [
        result["compacted_count"]
        for result in detailed["retained_audit_compaction_apply_results"]
    ] == [0, 1, 0]
    assert detailed["retained_audit_compaction_apply_results"][1][
        "history_type"
    ] == "stream_offer_lifecycle_explanation"


def test_detailed_snapshot_exposes_retained_audit_replay_summaries():
    result = run_scenario(
        SCENARIOS_DIR / "068_retained_audit_replay_summary.yaml"
    )
    detailed = result.final_snapshot

    assert [summary["history_type"] for summary in detailed[
        "retained_audit_replay_summaries"
    ]] == [
        "mixed",
        "stream_offer_lifecycle_explanation",
        "stream_offer_status_transition",
    ]
    assert detailed["retained_audit_replay_summaries"][0]["record_count"] == 2
    assert detailed["retained_audit_replay_summaries"][0]["metadata"][
        "by_history_type"
    ] == {
        "stream_offer_lifecycle_explanation": 1,
        "stream_offer_status_transition": 1,
    }


def test_retained_audit_snapshot_ordering_and_copies_are_stable():
    world = World()
    world.action_results.extend(
        [
            RetainedAuditCompactionDecision(
                hub_id="registry_b",
                policy_id="policy_b",
                history_type="stream_offer_lifecycle_explanation",
                retained_record_keys=("retained_b",),
                metadata={"labels": ("decision_b",)},
            ),
            RetainedAuditReplaySummary(
                hub_id="registry_b",
                history_type="stream_offer_status_transition",
                record_count=1,
                record_keys=("replay_b",),
                metadata={"labels": ("summary_b",)},
            ),
            RetainedAuditCompactionApplyResult(
                hub_id="registry_a",
                policy_id="policy_a",
                history_type="stream_offer_lifecycle_explanation",
                compacted_record_keys=("compacted_a",),
                compacted_count=1,
                metadata={"labels": ("apply_a",)},
            ),
            RetainedAuditCompactionDecision(
                hub_id="registry_a",
                policy_id="policy_a",
                history_type="stream_offer_status_transition",
                compaction_candidate_record_keys=("candidate_a",),
            ),
            RetainedAuditReplaySummary(
                hub_id="registry_a",
                history_type="stream_offer_lifecycle_explanation",
                record_count=1,
                record_keys=("replay_a",),
            ),
            RetainedAuditCompactionApplyResult(
                hub_id="registry_b",
                policy_id="policy_b",
                history_type="stream_offer_status_transition",
                retained_record_keys=("retained_b",),
                retained_count=1,
            ),
        ]
    )

    snapshot = world.snapshot(detailed=True)
    snapshot["retained_audit_compaction_decisions"][0][
        "retained_record_keys"
    ].append("mutated")
    snapshot["retained_audit_compaction_decisions"][0]["metadata"][
        "labels"
    ].append("mutated")
    snapshot["retained_audit_replay_summaries"][0]["record_keys"].append(
        "mutated"
    )
    snapshot["retained_audit_replay_summaries"][0]["metadata"]["labels"].append(
        "mutated"
    )
    snapshot["retained_audit_compaction_apply_results"][0][
        "compacted_record_keys"
    ].append("mutated")
    snapshot["retained_audit_compaction_apply_results"][0]["metadata"][
        "labels"
    ].append("mutated")
    fresh = world.snapshot(detailed=True)

    assert [
        decision["hub_id"] for decision in fresh["retained_audit_compaction_decisions"]
    ] == ["registry_b", "registry_a"]
    assert [
        summary["hub_id"] for summary in fresh["retained_audit_replay_summaries"]
    ] == ["registry_b", "registry_a"]
    assert [
        result["hub_id"]
        for result in fresh["retained_audit_compaction_apply_results"]
    ] == ["registry_a", "registry_b"]
    assert fresh["retained_audit_compaction_decisions"][0][
        "retained_record_keys"
    ] == ["retained_b"]
    assert fresh["retained_audit_compaction_decisions"][0]["metadata"] == {
        "labels": ["decision_b"]
    }
    assert fresh["retained_audit_replay_summaries"][0]["record_keys"] == ["replay_b"]
    assert fresh["retained_audit_replay_summaries"][0]["metadata"] == {
        "labels": ["summary_b"]
    }
    assert fresh["retained_audit_compaction_apply_results"][0][
        "compacted_record_keys"
    ] == ["compacted_a"]
    assert fresh["retained_audit_compaction_apply_results"][0]["metadata"] == {
        "labels": ["apply_a"]
    }
