from __future__ import annotations

from pathlib import Path
from typing import Any

from darwin.sim.runner import ScenarioRunResult, run_scenario
from darwin.sim.scenarios import list_scenario_files, validate_scenario_file

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_DIR = PROJECT_ROOT / "scenarios"


def test_all_scenario_files_validate():
    scenario_files = _scenario_yaml_files()

    failures = []
    for scenario_file in scenario_files:
        result = validate_scenario_file(scenario_file)
        if not result.passed:
            failures.append(f"{scenario_file}: {'; '.join(result.errors)}")

    assert scenario_files, f"No scenario YAML files found in {SCENARIOS_DIR}"
    assert not failures, "Scenario validation failed:\n" + "\n".join(failures)


def test_all_scenario_files_run_successfully():
    scenario_files = _scenario_yaml_files()

    failures = []
    for scenario_file in scenario_files:
        try:
            result = run_scenario(scenario_file)
        except Exception as exc:  # pragma: no cover - exercised only on failure
            failures.append(f"{scenario_file}: raised {type(exc).__name__}: {exc}")
            continue

        if not result.passed:
            failures.append(
                f"{scenario_file}: failed assertions:\n{_format_failed_assertions(result)}"
            )

    assert scenario_files, f"No scenario YAML files found in {SCENARIOS_DIR}"
    assert not failures, "Scenario runs failed:\n" + "\n".join(failures)


def test_key_scenario_relocation_has_expected_final_state():
    result = _run_key_scenario("004_relocation_pause_resume.yaml")
    snapshot = result.final_snapshot

    moved_device = _snapshot_section(snapshot, "devices")["dev_B2C8"]
    assert moved_device["state"] == "online"
    assert moved_device["current_registry_hub"] == "registry_office"
    assert moved_device["current_traffic_hub"] == "hub_4"

    lane = _snapshot_section(snapshot, "lanes")["lane_001"]
    assert lane["state"] == "active"
    assert lane["route"] == ["hub_1", "hub_2", "hub_4"]
    assert lane["last_sent_sequence"] == 1
    assert lane["last_acknowledged_sequence"] == 1

    hub_4_attachments = _snapshot_section(snapshot, "traffic_hubs")["hub_4"][
        "direct_attachments"
    ]
    assert hub_4_attachments["dev_B2C8"]["status"] == "attached"

    event_log = result.world.event_log
    assert event_log.has_event_type("marked_in_transit")
    assert event_log.has_event_type("lanes_paused")
    assert event_log.has_event_type("device_moved")
    assert event_log.has_event_type("lanes_resumed")


def test_key_scenario_growth_recommendation_exists():
    result = _run_key_scenario("007_congestion_bridge_recommendation.yaml")
    snapshot = result.final_snapshot

    recommendations = _snapshot_section(snapshot, "recommendations")["traffic_home_001"]
    assert recommendations == [
        {
            "recommendation_id": (
                "traffic_home_001:create_traffic_bridge:sustained_cross_tree_traffic"
            ),
            "recommendation_type": "create_traffic_bridge",
            "affected_hubs": ["traffic_home_001"],
            "affected_branches": ["global.family.home", "global.family.office"],
            "reason": "sustained_cross_tree_traffic",
            "confidence": "high",
            "status": "proposed",
        }
    ]
    assert result.world.event_log.has_event_type("create_traffic_bridge")


def _scenario_yaml_files() -> list[Path]:
    return [
        path
        for path in list_scenario_files(SCENARIOS_DIR)
        if path.suffix.lower() == ".yaml"
    ]


def _run_key_scenario(filename: str) -> ScenarioRunResult:
    scenario_path = SCENARIOS_DIR / filename
    result = run_scenario(scenario_path)
    assert result.passed, (
        f"{scenario_path} did not pass:\n{_format_failed_assertions(result)}"
    )
    return result


def _format_failed_assertions(result: ScenarioRunResult) -> str:
    failed = [assertion for assertion in result.assertion_results if not assertion.passed]
    if not failed:
        return "(scenario marked failed without failed assertion details)"

    return "\n".join(
        (
            f"- {assertion.assertion_type}: {assertion.message} "
            f"(expected={assertion.expected!r}, actual={assertion.actual!r})"
        )
        for assertion in failed
    )


def _snapshot_section(snapshot: dict[str, object], key: str) -> dict[str, Any]:
    section = snapshot[key]
    assert isinstance(section, dict)
    return section
