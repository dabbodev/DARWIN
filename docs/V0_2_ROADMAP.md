# DARWIN v0.2 Roadmap

## Goals

DARWIN v0.2 should make the simulator easier to inspect, extend, and trust as a behavioral model. The release should improve scenario expressiveness, export quality, route-cost modeling, relocation coverage, visualization, and testing depth while preserving deterministic in-memory execution.

## Completed Workstreams

1. Scenario validation and export polish
   - Structured validation now reports precise locations and suggestions for common scenario issues.
   - Snapshot, event, and result JSON exports are available from scenario runs.
   - Existing v0.1 scenarios remain compatible.

2. Route-cost modeling
   - Route-cost fields and deterministic routing policy behavior are modeled without real networking.
   - Scenario and unit coverage exercise cost-aware route selection.

3. Visualization output: Mermaid
   - Scenario runs can export deterministic Mermaid topology text.
   - The export is plain text only; it does not render images, mutate topology, or add a UI.

4. Relocation edge cases
   - Additional scenarios cover relocation timeout, invalid move contracts, duplicate device claims, and unreachable relocation resume paths.
   - These scenarios harden existing relocation behavior without changing the simulator into a distributed runtime.

5. Trace and timeline export
   - Scenario timelines can be exported as JSON or Markdown.
   - Filters can narrow traces by event type, device, hub, or lane.

6. Scenario DSL presets
   - Built-in setup presets reduce repeated YAML for common topology shapes.
   - Presets expand to ordinary setup data before validation and execution.

7. Scenario library indexing
   - Scenario metadata supports generated Markdown indexing and CLI description output.
   - The checked-in scenario index documents all current simulator scenarios.

## Remaining Candidates

1. DOT export, if still wanted
   - Mermaid is implemented; DOT can remain optional if Graphviz-oriented workflows become useful.
   - Keep any future graph export deterministic and text-based.

2. Optional actual HMAC-style experimental auth bridge
   - Add an optional, clearly labeled bridge that maps symbolic auth checks to standard library HMAC-style verification.
   - Treat it as simulator instrumentation, not a production crypto system.
   - Avoid custom cryptography, production key-management claims, and security guarantees.

3. Property-based or randomized scenario tests, if kept simple
   - Use small deterministic seeds if randomized tests are added.
   - Focus on invariants such as unique scoped labels, stable device IDs, and lane sequence monotonicity.

4. Richer route policies
   - Expand symbolic route policies only where they clarify deterministic routing behavior.
   - Avoid modeling real network performance or adaptive distributed routing in v0.2.

5. Visualization refinements
   - Improve Mermaid readability if current output becomes hard to inspect.
   - Consider DOT only as a text export, not a rendering pipeline or UI.

6. v0.2 release cleanup
   - Refresh release notes, changelog, checklist, and README links.
   - Re-run tests, Ruff, scenario regression, and representative CLI export checks.

## Non-Goals

- No production networking, sockets, packet capture, or distributed hub runtime.
- No full crypto system, custom cryptography, key lifecycle, or security claims.
- No DNS bridge unless explicitly chosen as the main v0.2 theme.
- No package publishing or automatic release process unless requested separately.
- No web UI as a v0.2 requirement.

## Suggested Milestone Order

1. Completed: freeze v0.1 release notes and architecture docs.
2. Completed: tighten scenario validation and add focused invalid-scenario tests.
3. Completed: stabilize machine-readable snapshot, event, and result exports.
4. Completed: add route-cost policy hooks and deterministic cost tests.
5. Completed: expand relocation edge-case scenarios and tests.
6. Completed: add Mermaid graph export for scenarios and final snapshots.
7. Completed: add timeline trace export in JSON and Markdown.
8. Completed: add scenario presets and scenario library indexing.
9. Remaining: evaluate whether a minimal HMAC-style auth bridge belongs in v0.2 or should wait.
10. Remaining: add simple invariant/property tests only after the core scenario DSL is stable.
11. Remaining: perform v0.2 release cleanup and final validation.

## Risks

- Scenario DSL changes can break existing demos if compatibility is not preserved.
- Route-cost features can become vague unless each cost has a deterministic test.
- Auth bridge work can be mistaken for production cryptography unless docs and naming stay explicit.
- Visualization work can sprawl if it tries to become a UI.
- Randomized tests can become flaky unless seeds and invariants are tightly controlled.

## Testing Plan

- Keep `python -m pytest` as the primary local test command.
- Keep `python -m ruff check .` passing.
- Keep `python scripts/run_all_scenarios.py` as the executable scenario regression pass.
- Add targeted tests for scenario validation errors and export formats.
- Add scenario files for relocation edge cases only when they are useful as demos or regressions.
- For visualization outputs, test stable text fragments rather than rendered diagrams.
- For any optional HMAC-style bridge, test standard-library behavior with deterministic fixtures and document it as non-production.
