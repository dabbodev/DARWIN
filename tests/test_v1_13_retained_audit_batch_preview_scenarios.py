from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from darwin.models import (
    RetainedAuditCompactionApplyResult,
    RetainedAuditCompactionBatchApplyResult,
    RetainedAuditCompactionBatchPreviewResult,
    RetainedAuditCompactionPreviewResult,
)
from darwin.sim.assertions import evaluate_assertion
from darwin.sim.runner import run_scenario
from darwin.sim.scenarios import list_scenario_files, validate_scenario_dict

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_DIR = PROJECT_ROOT / "scenarios"
V1_13_SCENARIO_NAMES = (
    "088_retained_audit_batch_preview_success.yaml",
    "089_retained_audit_batch_preview_stale.yaml",
    "090_retained_audit_batch_preview_isolation.yaml",
)


def test_v1_13_batch_preview_scenarios_validate():
    for scenario_name in V1_13_SCENARIO_NAMES:
        validation = validate_scenario_dict(
            _load_yaml(SCENARIOS_DIR / scenario_name),
            path=scenario_name,
        )
        assert validation.valid, validation.errors


@pytest.mark.parametrize(
    ("field_name", "value", "expected_location"),
    [
        ("decision_policy_ids", "not-a-mapping", "steps[17].decision_policy_ids"),
        (
            "decision_policy_ids",
            {"message_delivery_result": "policy_message"},
            "steps[17].decision_policy_ids",
        ),
        (
            "decision_policy_ids",
            {
                "message_delivery_result": "policy_message",
                "unsupported_history": "policy_unsupported",
            },
            "steps[17].decision_policy_ids.unsupported_history",
        ),
        ("batch_id", "", "steps[17].batch_id"),
        ("metadata", [], "steps[17].metadata"),
    ],
)
def test_v1_13_batch_preview_step_validation_rejects_malformed_mappings(
    field_name,
    value,
    expected_location,
):
    invalid = _load_yaml(SCENARIOS_DIR / V1_13_SCENARIO_NAMES[0])
    preview_step = next(
        step
        for step in invalid["steps"]
        if step.get("action") == "preview_retained_audit_compaction_batch"
    )
    preview_step[field_name] = value

    validation = validate_scenario_dict(invalid)

    assert not validation.valid
    assert expected_location in {error.location for error in validation.errors}


def test_v1_13_batch_preview_assertion_validation_rejects_nested_filter_errors():
    invalid = _load_yaml(SCENARIOS_DIR / V1_13_SCENARIO_NAMES[0])
    assertion = invalid["assertions"][0]
    assertion["would_compact_count"] = -1
    assertion["history_missing_count"] = -1
    assertion["history_retained_record_key"] = 7
    assertion["policy_id"] = "policy_without_history"

    validation = validate_scenario_dict(invalid)

    assert not validation.valid
    locations = {error.location for error in validation.errors}
    assert {
        "assertions[0].would_compact_count",
        "assertions[0].history_missing_count",
        "assertions[0].history_retained_record_key",
        "assertions[0].history_type",
    } <= locations


def test_v1_13_batch_preview_requires_exact_prior_decision_references():
    invalid = _load_yaml(SCENARIOS_DIR / V1_13_SCENARIO_NAMES[0])
    preview_step = next(
        step
        for step in invalid["steps"]
        if step.get("action") == "preview_retained_audit_compaction_batch"
    )
    preview_step["decision_policy_ids"]["authority_outcome"] = "missing_policy"
    invalid["assertions"] = []

    with pytest.raises(KeyError, match="prior compaction decision"):
        run_scenario(invalid)


def test_v1_13_success_has_exact_preview_apply_parity_and_aggregate_only_streams():
    result = run_scenario(SCENARIOS_DIR / V1_13_SCENARIO_NAMES[0])
    previews = _results(result, RetainedAuditCompactionBatchPreviewResult)
    applies = _results(result, RetainedAuditCompactionBatchApplyResult)

    assert result.passed
    assert len(previews) == 1
    assert len(applies) == 1
    assert not _results(result, RetainedAuditCompactionPreviewResult)
    assert not _results(result, RetainedAuditCompactionApplyResult)
    preview = previews[0]
    applied = applies[0]
    assert preview.batch_id == applied.batch_id == "retained_audit_batch_088"
    assert preview.history_types == applied.history_types == (
        "message_delivery_result",
        "authority_outcome",
    )
    assert preview.metadata["caller_order"] == "reverse_canonical"
    assert preview.metadata["canonical_batch_order"] is True
    assert preview.metadata["batch_id_correlation_only"] is True
    assert preview.metadata["apply_parity_requires_unchanged_state"] is True
    for preview_result, apply_result in zip(
        preview.preview_results,
        applied.apply_results,
        strict=True,
    ):
        assert preview_result.policy_id == apply_result.policy_id
        assert preview_result.history_type == apply_result.history_type
        assert (
            preview_result.would_compact_record_keys
            == apply_result.compacted_record_keys
        )
        for category in ("retained", "ignored", "missing", "unsupported"):
            assert getattr(preview_result, f"{category}_record_keys") == getattr(
                apply_result,
                f"{category}_record_keys",
            )


def test_v1_13_preview_plural_key_filters_use_contains_semantics():
    result = run_scenario(SCENARIOS_DIR / V1_13_SCENARIO_NAMES[0])
    result.world.action_results.append(
        RetainedAuditCompactionBatchPreviewResult(
            hub_id="registry_home_088",
            batch_id="retained_audit_batch_subset_088",
            preview_results=[
                RetainedAuditCompactionPreviewResult(
                    hub_id="registry_home_088",
                    policy_id="retained_audit_message_delivery_subset_088",
                    history_type="message_delivery_result",
                    would_compact_record_keys=["message:first", "message:second"],
                    would_compact_count=2,
                ),
                RetainedAuditCompactionPreviewResult(
                    hub_id="registry_home_088",
                    policy_id="retained_audit_authority_subset_088",
                    history_type="authority_outcome",
                ),
            ],
        )
    )

    assertion = evaluate_assertion(
        result.world,
        {
            "type": "retained_audit_compaction_batch_preview_result_contains",
            "registry_hub": "registry_home_088",
            "batch_id": "retained_audit_batch_subset_088",
            "history_type": "message_delivery_result",
            "history_would_compact_record_keys": ["message:second"],
            "expected_count": 1,
        },
    )

    assert assertion.passed


def test_v1_13_stale_preview_is_repeatable_and_does_not_mutate_selected_histories():
    scenario = _load_yaml(SCENARIOS_DIR / V1_13_SCENARIO_NAMES[1])
    preview_index = next(
        index
        for index, step in enumerate(scenario["steps"])
        if step.get("action") == "preview_retained_audit_compaction_batch"
    )
    before_data = deepcopy(scenario)
    before_data["scenario_id"] = "089_before_retained_audit_batch_preview"
    before_data["steps"] = before_data["steps"][:preview_index]
    before_data["assertions"] = []

    before = run_scenario(before_data)
    result = run_scenario(SCENARIOS_DIR / V1_13_SCENARIO_NAMES[1])
    previews = _results(result, RetainedAuditCompactionBatchPreviewResult)

    assert result.passed
    assert len(previews) == 2
    assert previews[0].to_summary() == previews[1].to_summary()
    assert previews[0].would_compact_count == 1
    assert previews[0].missing_count == 1
    assert result.world.registry_hubs == before.world.registry_hubs
    assert result.world.devices == before.world.devices
    assert not _results(result, RetainedAuditCompactionBatchApplyResult)


def test_v1_13_isolation_preserves_registry_traffic_identity_and_compact_snapshot():
    scenario = _load_yaml(SCENARIOS_DIR / V1_13_SCENARIO_NAMES[2])
    preview_index = next(
        index
        for index, step in enumerate(scenario["steps"])
        if step.get("action") == "preview_retained_audit_compaction_batch"
    )
    before_data = deepcopy(scenario)
    before_data["scenario_id"] = "090_before_retained_audit_batch_preview"
    before_data["steps"] = before_data["steps"][:preview_index]
    before_data["assertions"] = []

    before = run_scenario(before_data)
    result = run_scenario(SCENARIOS_DIR / V1_13_SCENARIO_NAMES[2])

    assert result.passed
    assert result.world.registry_hubs == before.world.registry_hubs
    assert result.world.devices == before.world.devices
    assert result.world.traffic_hubs == before.world.traffic_hubs
    assert result.world.lanes == before.world.lanes
    compact_before = before.world.snapshot()
    compact_after = result.world.snapshot()
    assert compact_after["time"] == compact_before["time"] + 1
    assert {key: value for key, value in compact_after.items() if key != "time"} == {
        key: value for key, value in compact_before.items() if key != "time"
    }
    assert len(_results(result, RetainedAuditCompactionBatchPreviewResult)) == 1
    assert not _results(result, RetainedAuditCompactionPreviewResult)


def test_v1_13_detailed_snapshot_adds_only_copied_batch_preview_results():
    result = run_scenario(SCENARIOS_DIR / V1_13_SCENARIO_NAMES[0])
    compact = result.world.snapshot()
    detailed = result.world.detailed_snapshot()

    assert "retained_audit_compaction_batch_preview_results" not in compact
    assert len(detailed["retained_audit_compaction_batch_preview_results"]) == 1
    snapshot = detailed["retained_audit_compaction_batch_preview_results"][0]
    snapshot["history_types"].reverse()
    snapshot["preview_results"][0]["would_compact_record_keys"].append("mutated")

    fresh = result.world.detailed_snapshot()
    assert fresh["retained_audit_compaction_batch_preview_results"][0][
        "history_types"
    ] == ["message_delivery_result", "authority_outcome"]
    assert "mutated" not in fresh["retained_audit_compaction_batch_preview_results"][0][
        "preview_results"
    ][0]["would_compact_record_keys"]


def test_v1_13_checked_in_scenarios_run_and_extend_contiguous_sweep():
    scenario_files = [
        path
        for path in list_scenario_files(SCENARIOS_DIR)
        if path.name[:3] in {"088", "089", "090"}
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
        scenario_result = run_scenario(scenario_file)
        if not scenario_result.passed:
            failures.append(f"{scenario_file}: {scenario_result.assertion_results}")

    scenario_numbers = sorted(
        int(path.name[:3])
        for path in list_scenario_files(SCENARIOS_DIR)
        if path.name[:3].isdigit()
    )
    assert [path.name[:3] for path in scenario_files] == ["088", "089", "090"]
    assert scenario_numbers == list(range(1, 91))
    assert not failures


def _load_yaml(path: Path) -> dict[str, object]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _results(result: object, result_type: type) -> list[object]:
    return [
        item
        for item in result.world.action_results
        if isinstance(item, result_type)
    ]
