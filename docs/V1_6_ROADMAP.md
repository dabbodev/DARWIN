# DARWIN v1.6 Roadmap: Retained Audit Compaction and Replay Summaries

Status: unreleased release-candidate hardening and documentation audit only.
Sprint 1 read-only compaction policy helpers, Sprint 2 read-only replay
summary helpers, Sprint 3 explicit compaction apply helpers, Sprint 4 scenario
DSL coverage, and Sprint 5 detailed snapshot/debug visibility are implemented.
Sprint 6 hardens release-readiness documentation and deterministic scenario
coverage checks without adding feature behavior. v1.6 does not change the
current released version. The latest released version remains
`darwin-sim 1.5.0` on `main`
with the annotated `v1.5.0` tag and GitHub release:
https://github.com/dabbodev/DARWIN/releases/tag/v1.5.0. No package
publication was performed for v1.5.0, and no release assets were uploaded.

Recommended candidate theme: Retained audit compaction and replay summaries.

This roadmap records implemented simulator-only planning slices, the Sprint 6
release-candidate documentation audit, and candidate later work. It does not
authorize a version bump, package publication, release assets, merge, tag, or
release execution.

v1.6 should remain simulator-first and symbolic. It should not become
production networking, a real DDoS protection system, a firewall product, a
privacy or anonymity system, DNS, registrar infrastructure, external service
discovery, a secure messaging protocol, a production cryptography project, a
delivery enforcement layer, a TrafficHub routing change, an automatic cleanup
system, a durable queue, or a live timer system.

## Core Concept

Explore small, deterministic planning surfaces for describing retained audit
history compaction candidates and grouped replay summaries across existing
simulator-retained histories.

v1.5 added lifecycle explanation retention classification, read-only pruning
plans, an explicit caller-driven pruning apply helper limited to retained
lifecycle explanation history, scenario DSL coverage, and detailed debug
snapshot visibility. v1.6 planning should start one step earlier: read-only
policy and summary models over retained audit-style histories, without
deleting, rewriting, routing, delivering, retrying, scheduling, or compacting
anything by default.

The primary planning question is:

```text
Can DARWIN describe retained audit compaction candidates and replay summaries
in compact simulator planning outputs without adding automatic cleanup,
delivery, routing, timer, queue, networking, cryptography, or production
security behavior?
```

## Planning Boundaries

Candidate in scope:

- Read-only audit compaction policy models for retained simulator histories.
- Deterministic compaction-plan helpers that summarize candidates without
  deleting or rewriting retained histories by default.
- Grouped replay-summary helpers for retained lifecycle, poll/admission,
  encrypted delivery, alias, or authority audit histories.
- Explicit opt-in compaction/apply helper only after read-only planning
  helpers are stable and only if the helper remains caller-driven.
- Scenario DSL coverage only after helper and model slices are stable.
- Detailed snapshot visibility only after retained compaction or replay
  action results exist.
- Release-readiness documentation after scenario coverage exists.

Out of scope:

- Real networking, sockets, HTTP, WebSocket, DNS, or service discovery.
- Registrar integration, public CA behavior, external services, or production
  identity proof.
- Live polling, live timers, live clocks, automatic cleanup workers,
  background services, durable queues, or retry loops.
- Delivery enforcement, mailbox delivery behavior changes, encrypted delivery
  behavior changes, or any other delivery behavior changes.
- TrafficHub routing changes.
- Canonical identity rewrites.
- Production DDoS protection, firewall guarantees, abuse mitigation, privacy,
  anonymity, metadata-hiding, or traffic-analysis guarantees.
- Real cryptography, key generation, private key storage, production E2EE, or
  secure messaging.
- Compact `world.snapshot()` changes.
- Compaction behavior beyond explicit simulator helpers.
- Version bumps beyond `1.5.0` during planning.
- Package publication, release assets, merge, tag, or release work.

## Candidate Concepts

Audit compaction policy model:

- A copied JSON-safe symbolic model that describes how retained simulator
  audit histories could be grouped, bounded, aged, or classified for review.
- It should use explicit simulator metadata such as record type, hub ID,
  offer ID, request ID, action result ID, decision status, reason, source, or
  deterministic sequence key.
- It should not mutate retained histories, delete data, compact snapshots,
  deliver messages, route traffic, enforce policy, or claim compliance-grade
  audit retention.

Read-only compaction plan:

- A deterministic helper that identifies retained audit records that would be
  kept, summarized, reviewed, or considered compaction candidates under a
  provided symbolic policy.
- It should return copied JSON-safe planning metadata and preserve
  deterministic ordering.
- It should not delete records, rewrite records, schedule cleanup, retry work,
  run timers, behave like a durable queue, or apply storage enforcement.

Grouped replay summaries:

- Deterministic summaries over retained simulator histories and optional
  compaction-plan metadata.
- Candidate groupings may include lifecycle status transitions, lifecycle
  explanation records, stream-offer poll results, lane admission decisions,
  symbolic encrypted delivery results, retained alias records, alias
  conflicts, authority traces, or authority outcomes.
- The summaries should help inspect existing simulator diagnostics without
  claiming production auditability, privacy protection, security telemetry,
  traffic-analysis resistance, or compliance behavior.

Explicit compaction/apply helper:

- A later opt-in helper may be considered only after read-only policy,
  compaction-plan, and replay-summary helpers are stable.
- If added, it should be caller-driven and explicit, with copied summaries of
  what was compacted, retained, skipped, or missing.
- It should not become automatic cleanup, a background worker, a retry loop, a
  durable queue, a live timer, production retention enforcement, or compact
  snapshot mutation.

## Candidate Sprint Order

Sprint 1 implemented on the v1.6 planning branch: Read-only audit compaction
policy models.

- Define the smallest symbolic policy model for retained simulator audit
  histories.
- Classify explicit retained records without mutating retained history.
- Keep candidate status labels descriptive and deterministic.
- Document that the model is planning-only and read-only.
- Initial support is intentionally narrow: stream-offer lifecycle explanation
  history and stream-offer lifecycle transition history. Other retained audit
  families remain future work.

Sprint 2 implemented on the v1.6 planning branch: Deterministic read-only
replay-summary helpers.

- Define `RetainedAuditReplaySummary` for explicit retained audit records.
- Preserve deterministic record-key ordering and copied JSON-safe summary
  shapes.
- Group supported retained audit records by history type, status, reason,
  source, and offer ID where available.
- Optionally filter replay summaries through existing retained or
  compaction-candidate record keys from a `RetainedAuditCompactionDecision`.
- Keep replay summaries separate from apply/delete/compact behavior.
- Initial support remains intentionally narrow: stream-offer lifecycle
  explanation history and stream-offer lifecycle transition history.

Sprint 3 implemented on the v1.6 planning branch: Explicit retained audit
compaction apply helper.

- Define `RetainedAuditCompactionApplyResult` for caller-driven apply
  outcomes.
- Add `apply_retained_audit_compaction_decision(...)` for explicit
  simulator-local mutation of only the selected retained audit history.
- Remove only currently matching compaction-candidate records and preserve
  remaining retained history order.
- Report compacted, retained, ignored, missing, and unsupported record keys
  deterministically.
- Keep support intentionally narrow: stream-offer lifecycle explanation
  history and stream-offer lifecycle transition history.
- Keep scenario DSL coverage, detailed snapshot changes, and compact
  `world.snapshot()` changes out of this sprint.

Sprint 4 implemented on the v1.6 planning branch: Scenario DSL coverage.

- Add explicit scenario actions for retained audit classification, replay
  summaries, and compaction apply using the existing helper semantics.
- Keep classification and replay-summary actions read-only.
- Require the apply action to reference a prior typed compaction decision and
  mutate only the decision's single supported retained history.
- Add deterministic action-result assertions for decision, replay summary,
  and apply-result keys, counts, and small grouped fields.
- Add scenarios `067` through `069` for retain-filter precedence, replay
  history/reason grouping and category filtering, explicit selected-history
  apply, unsupported keys, missing keys, and no compaction without apply.
- Preserve compact and detailed snapshot shapes and keep the package/CLI
  version at `darwin-sim 1.5.0`.

Sprint 5 implemented on the v1.6 planning branch: Detailed snapshot/debug
visibility for retained-audit action results.

- Add top-level detailed snapshot fields for retained audit compaction
  decisions, replay summaries, and compaction apply results.
- Serialize existing action results through their deterministic copied summary
  helpers without changing classification, replay, or apply semantics.
- Keep compact `world.snapshot()` structure unchanged.
- Add focused coverage for detailed visibility, action-result ordering, and
  snapshot-copy isolation.

Sprint 6: Release-Candidate Hardening and Documentation Audit (implemented on
the v1.6 planning branch).

- Include the roadmap, draft release notes, compaction-policy, replay-summary,
  and compaction-apply docs in documentation link/readiness checks.
- Confirm checked-in scenario coverage is contiguous from `001` through `069`
  and that `docs/SCENARIO_INDEX.md` is exactly generated from deterministic
  scenario metadata.
- Update release-candidate documentation to summarize Sprints 1 through 5 and
  preserve the simulator-local, symbolic boundaries of the implemented work.
- Keep the package and CLI version at `darwin-sim 1.5.0`; do not add a
  `CHANGELOG.md` v1.6 release entry, merge, tag, GitHub release, release
  assets, or package publication.
- Do not change compaction classification precedence, replay-summary
  semantics, compaction-apply semantics, compact `world.snapshot()`, existing
  delivery behavior, TrafficHub routing, or canonical identity behavior.
- Do not add scenarios unless required to repair deterministic scenario
  index/readiness consistency.

Future candidate: Broader grouped replay-summary helpers or read-only
compaction-plan refinements.

- Extend retained lifecycle, poll/admission, encrypted delivery, alias, or
  authority audit summaries only if a later sprint explicitly accepts that
  scope.
- Consider deterministic compaction-plan refinements only while keeping them
  separate from additional apply/delete behavior.
- Keep summaries diagnostic only.

## Planning Acceptance Targets

- v1.6 content remains clearly marked as planning, draft, and unreleased.
- v1.5.0 remains the latest released version.
- Implemented helper behavior remains limited to explicit read-only planning,
  diagnostic summaries, and caller-driven selected-history apply, with
  focused tests and simulator-only scenarios; no version bump is added by
  these planning sprints.
- Existing mailbox delivery, encrypted delivery, TrafficHub routing, alias,
  identity, stream-offer polling/admission, lifecycle planning/apply, retained
  histories, scenario, detailed snapshot, compact snapshot, and canonical
  identity behavior remains unchanged.
- Compact `world.snapshot()` output remains unchanged.
- No package publication, release assets, merge, tag, release, real
  networking, DNS lookup, external services, real cryptography, production
  E2EE, delivery enforcement, automatic cleanup workers, retry loops, durable
  queues, live timers, compaction behavior beyond explicit simulator helpers,
  delivery changes, TrafficHub routing changes, compact snapshot changes, or
  canonical identity rewrites are introduced.

## Release Status

v1.6 is unreleased. Sprint 6 is release-candidate hardening and documentation
audit only; it is not final release preparation or release execution. No v1.6
release scope is locked in by this document, and no package publication,
release assets, merge, tag, GitHub release, or version bump is authorized by
this roadmap.

The latest released version remains v1.5.0 as `darwin-sim 1.5.0`.

## Intentionally Deferred Work

- Real networking, sockets, HTTP/WebSocket behavior, DNS lookup, and external
  services.
- Registrar integration, public CA behavior, production identity proof, and
  public infrastructure behavior.
- Live polling, live timers, live clocks, automatic cleanup workers,
  background services, durable queues, retry loops, or wall-clock schedulers.
- Production DDoS protection, firewall guarantees, abuse mitigation, privacy,
  anonymity, metadata hiding, or traffic-analysis guarantees.
- Real cryptography, key generation, private key storage, production E2EE, and
  secure messaging protocols.
- Delivery enforcement or delivery behavior changes.
- TrafficHub routing changes.
- Compact snapshot changes.
- Canonical identity rewrites.
- Package publication, release assets, merge, tag, release, or version bump
  beyond `1.5.0` during planning.
