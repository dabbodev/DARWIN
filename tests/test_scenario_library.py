from __future__ import annotations

from pathlib import Path

from darwin.cli.main import main
from darwin.sim.library import (
    describe_scenario,
    discover_scenario_metadata,
    scenario_index_markdown,
    scenario_metadata_from_dict,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_DIR = PROJECT_ROOT / "scenarios"


def test_scenario_metadata_from_dict():
    metadata = scenario_metadata_from_dict(
        {
            "scenario_id": "metadata_test",
            "name": "Metadata test",
            "category": "registry",
            "description": "Exercises metadata extraction.",
            "tags": ["registry", "docs"],
            "demonstrates": ["Metadata extraction."],
            "expected_result": "Metadata fields are available.",
        },
        path="scenarios/metadata_test.yaml",
    )

    assert metadata.scenario_id == "metadata_test"
    assert metadata.name == "Metadata test"
    assert metadata.path == "scenarios/metadata_test.yaml"
    assert metadata.category == "registry"
    assert metadata.description == "Exercises metadata extraction."
    assert metadata.tags == ["registry", "docs"]
    assert metadata.demonstrates == ["Metadata extraction."]
    assert metadata.expected_result == "Metadata fields are available."


def test_discover_scenario_metadata_lists_checked_in_scenarios():
    metadata = discover_scenario_metadata(SCENARIOS_DIR)

    scenario_ids = {item.scenario_id for item in metadata}
    assert "001_basic_registration" in scenario_ids
    assert "004_relocation_pause_resume" in scenario_ids
    assert "011_preset_lane_demo" in scenario_ids


def test_discover_scenario_metadata_has_contiguous_001_through_043():
    metadata = discover_scenario_metadata(SCENARIOS_DIR)

    scenario_numbers = sorted(
        int(item.scenario_id[:3])
        for item in metadata
        if item.scenario_id[:3].isdigit()
    )

    assert scenario_numbers == list(range(1, 44))


def test_describe_scenario_includes_counts_and_validation():
    description = describe_scenario(SCENARIOS_DIR / "004_relocation_pause_resume.yaml")

    assert description.metadata.scenario_id == "004_relocation_pause_resume"
    assert description.metadata.category == "relocation"
    assert description.step_count == 6
    assert description.assertion_count == 2
    assert description.setup_counts["registry_hubs"] == 2
    assert description.validation_result.passed


def test_list_scenarios_output_includes_category(capsys):
    exit_code = main(["list-scenarios"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "001_basic_registration" in captured.out
    assert "[registry]" in captured.out


def test_describe_scenario_cli(capsys):
    exit_code = main(
        ["describe-scenario", "scenarios/004_relocation_pause_resume.yaml"]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Scenario: 004_relocation_pause_resume - Relocation pause and resume" in captured.out
    assert "Category: relocation" in captured.out
    assert "Validation: PASS" in captured.out


def test_scenario_index_markdown():
    metadata = discover_scenario_metadata(SCENARIOS_DIR)
    markdown = scenario_index_markdown(metadata)

    assert "| Scenario | Category | Description | Tags |" in markdown
    assert "`001_basic_registration` - Basic registration" in markdown
    assert "| registry |" in markdown


def test_scenario_index_cli(capsys):
    exit_code = main(["scenario-index"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "# DARWIN Scenario Index" in captured.out
    assert "`011_preset_lane_demo` - Preset lane demo" in captured.out
