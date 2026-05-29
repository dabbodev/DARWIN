from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_DIR = PROJECT_ROOT / "scenarios"
sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    from darwin.sim.runner import run_scenario
    from darwin.sim.scenarios import (
        list_scenario_files,
        load_scenario,
        validate_scenario_file,
    )

    scenario_files = [
        path
        for path in list_scenario_files(SCENARIOS_DIR)
        if path.suffix.lower() in {".yaml", ".yml"}
    ]
    if not scenario_files:
        print(f"No scenario YAML files found in {SCENARIOS_DIR}", file=sys.stderr)
        return 1

    failures = 0
    for scenario_file in scenario_files:
        validation = validate_scenario_file(scenario_file)
        if not validation.passed:
            failures += 1
            print(
                f"{scenario_file.name}  INVALID  "
                f"{'; '.join(validation.errors)}"
            )
            continue

        scenario = load_scenario(scenario_file)
        try:
            result = run_scenario(scenario)
        except Exception as exc:  # pragma: no cover - command-line failure path
            failures += 1
            print(f"{scenario_file.name}  {scenario.scenario_id}  FAIL  raised {exc}")
            continue

        status = "PASS" if result.passed else "FAIL"
        passed_assertions = sum(
            1 for assertion in result.assertion_results if assertion.passed
        )
        total_assertions = len(result.assertion_results)
        print(
            f"{scenario_file.name}  {scenario.scenario_id}  "
            f"{scenario.name}  {status}  {passed_assertions}/{total_assertions}"
        )
        if not result.passed:
            failures += 1

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
