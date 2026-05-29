# DARWIN v0.2 Roadmap

## Goals

DARWIN v0.2 should make the simulator easier to inspect, extend, and trust as a behavioral model. The release should improve scenario expressiveness, export quality, route-cost modeling, relocation coverage, visualization, and testing depth while preserving deterministic in-memory execution.

## Recommended Workstreams

1. Better scenario DSL and validation
   - Add stricter validation for supported actions, required fields, unknown fields, and assertion types.
   - Keep YAML readable and avoid a heavy schema tool unless the DSL grows enough to justify it.

2. Event log and snapshot export polish
   - Stabilize event names and payloads.
   - Add optional JSON export for event logs and snapshots.
   - Keep CLI output compact for demos and regression runs.

3. More route-cost modeling
   - Expand symbolic route costs beyond hop count.
   - Model congestion, hub preference, and explicit route penalties without real networking.
   - Keep route selection deterministic.

4. Optional actual HMAC-style symbolic-to-real auth bridge
   - Add an optional, clearly labeled bridge that maps symbolic auth checks to standard library HMAC-style verification.
   - Treat it as simulator instrumentation, not a production crypto system.
   - Avoid custom cryptography and avoid key-management claims.

5. More relocation edge cases
   - Cover route unavailable after move, multiple lanes, source relocation, target relocation, repeated moves, failed move contracts, and timeout-like flows.
   - Keep state transitions explicit and inspectable.

6. Visualization outputs such as Mermaid or DOT
   - Export hub graphs, registry paths, lane routes, and relocation flows.
   - Prefer text outputs that are easy to diff in tests.

7. Property-based or randomized scenario tests, if kept simple
   - Use small deterministic seeds if randomized tests are added.
   - Focus on invariants such as unique scoped labels, stable device IDs, and lane sequence monotonicity.

## Non-Goals

- No production networking, sockets, packet capture, or distributed hub runtime.
- No full crypto system, custom cryptography, key lifecycle, or security claims.
- No DNS bridge unless explicitly chosen as the main v0.2 theme.
- No package publishing or automatic release process unless requested separately.
- No web UI as a v0.2 requirement.

## Suggested Milestone Order

1. Freeze v0.1 release notes and architecture docs.
2. Tighten scenario validation and add focused invalid-scenario tests.
3. Stabilize event names and add optional machine-readable exports.
4. Add route-cost policy hooks and deterministic cost tests.
5. Expand relocation edge-case scenarios and tests.
6. Add Mermaid or DOT graph export for scenarios and final snapshots.
7. Evaluate whether a minimal HMAC-style auth bridge belongs in v0.2 or should wait.
8. Add simple invariant/property tests only after the core scenario DSL is stable.

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
