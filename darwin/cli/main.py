"""Minimal command-line entry point for DARWIN simulator."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import darwin
from darwin.sim.export import export_events, export_result, export_snapshot
from darwin.sim.runner import ScenarioRunResult, run_scenario
from darwin.sim.scenarios import (
    ScenarioLoadError,
    list_scenario_files,
    load_scenario,
    validate_scenario_file,
)


def _default_scenarios_dir() -> Path:
    cwd_scenarios = Path.cwd() / "scenarios"
    if cwd_scenarios.exists():
        return cwd_scenarios
    return Path(__file__).resolve().parents[2] / "scenarios"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="darwin-sim")
    parser.add_argument("--version", action="store_true", help="print version and exit")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="run a scenario file")
    run_parser.add_argument("scenario", help="path to a YAML or JSON scenario file")
    run_parser.add_argument(
        "--dump-snapshot",
        action="store_true",
        help="print the final deterministic JSON snapshot",
    )
    run_parser.add_argument(
        "--export-snapshot",
        metavar="PATH",
        help="write the final deterministic JSON snapshot to PATH",
    )
    run_parser.add_argument(
        "--export-events",
        metavar="PATH",
        help="write the structured event log JSON to PATH",
    )
    run_parser.add_argument(
        "--export-result",
        metavar="PATH",
        help="write the full scenario result summary JSON to PATH",
    )

    list_parser = subparsers.add_parser("list-scenarios", help="list available scenarios")
    list_parser.add_argument(
        "--directory",
        default=str(_default_scenarios_dir()),
        help="directory containing scenario files",
    )

    validate_parser = subparsers.add_parser(
        "validate-scenario",
        help="validate a scenario file without running it",
    )
    validate_parser.add_argument("scenario", help="path to a YAML or JSON scenario file")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(f"darwin-sim {darwin.__version__}")
        return 0

    if args.command == "run":
        return _run_command(
            args.scenario,
            dump_snapshot=args.dump_snapshot,
            export_snapshot_path=args.export_snapshot,
            export_events_path=args.export_events,
            export_result_path=args.export_result,
        )

    if args.command == "list-scenarios":
        return _list_scenarios_command(Path(args.directory))

    if args.command == "validate-scenario":
        return _validate_scenario_command(args.scenario)

    parser.print_help()
    return 0


def _list_scenarios_command(directory: Path) -> int:
    files = list_scenario_files(directory)
    if not files:
        print(f"No scenarios found in {directory}")
        return 1

    for path in files:
        result = validate_scenario_file(path)
        label = str(_display_path(path))
        if result.scenario_id is not None:
            label = f"{label}  {result.scenario_id}"
            if result.name:
                label = f"{label} - {result.name}"
        print(label)
    return 0


def _validate_scenario_command(scenario_path: str) -> int:
    result = validate_scenario_file(scenario_path)
    if result.passed:
        heading = result.scenario_id or scenario_path
        suffix = f" - {result.name}" if result.name else ""
        print(f"VALID {heading}{suffix}")
        for warning in result.warnings:
            print(f"warning: {warning.render()}")
        return 0

    print(f"INVALID {scenario_path}", file=sys.stderr)
    for error in result.errors:
        print(f"error: {error.render()}", file=sys.stderr)
    return 1


def _display_path(path: Path) -> Path:
    try:
        return path.relative_to(Path.cwd())
    except ValueError:
        return path


def _run_command(
    scenario_path: str,
    *,
    dump_snapshot: bool,
    export_snapshot_path: str | None = None,
    export_events_path: str | None = None,
    export_result_path: str | None = None,
) -> int:
    validation = validate_scenario_file(scenario_path)
    if not validation.passed:
        print(f"INVALID {scenario_path}", file=sys.stderr)
        for error in validation.errors:
            print(f"error: {error.render()}", file=sys.stderr)
        return 1

    try:
        scenario = load_scenario(scenario_path)
        result = run_scenario(scenario)
        _write_exports(
            result,
            export_snapshot_path=export_snapshot_path,
            export_events_path=export_events_path,
            export_result_path=export_result_path,
        )
    except (OSError, ScenarioLoadError, KeyError, TypeError, ValueError) as exc:
        print(f"RUN FAILED {scenario_path}", file=sys.stderr)
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(_render_run_result(result, scenario.name, dump_snapshot=dump_snapshot))
    return 0 if result.passed else 1


def _write_exports(
    result: ScenarioRunResult,
    *,
    export_snapshot_path: str | None,
    export_events_path: str | None,
    export_result_path: str | None,
) -> None:
    if export_snapshot_path is not None:
        export_snapshot(result, export_snapshot_path)
    if export_events_path is not None:
        export_events(result, export_events_path)
    if export_result_path is not None:
        export_result(result, export_result_path)


def _render_run_result(
    result: ScenarioRunResult,
    scenario_name: str,
    *,
    dump_snapshot: bool,
) -> str:
    status = "PASS" if result.passed else "FAIL"
    title = result.scenario_id
    if scenario_name:
        title = f"{title} - {scenario_name}"

    assertion_count = len(result.assertion_results)
    passed_count = sum(1 for assertion in result.assertion_results if assertion.passed)
    lines = [
        f"Scenario: {title}",
        f"Result: {status}",
        f"Assertions: {passed_count}/{assertion_count} passed",
        "",
        "Assertion results:",
    ]

    if result.assertion_results:
        for assertion in result.assertion_results:
            assertion_status = "PASS" if assertion.passed else "FAIL"
            lines.append(f"- {assertion_status} {assertion.assertion_type}: {assertion.message}")
    else:
        lines.append("- (none)")

    lines.extend(["", "Event log:"])
    lines.extend(result.event_log or ["(no events)"])

    if dump_snapshot:
        lines.extend(
            [
                "",
                "Final snapshot:",
                json.dumps(result.final_snapshot, indent=2, sort_keys=True),
            ]
        )

    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
