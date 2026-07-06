# DARWIN v1.6 Roadmap: Retained Audit Compaction and Replay Summaries

Status: planning draft with Sprint 1 read-only compaction policy helpers
implemented and Sprint 2 read-only replay summary helpers implemented. v1.6
is unreleased, has not started release prep, and does not change the current
released version. The latest released version remains `darwin-sim 1.5.0` on
`main` with the annotated `v1.5.0` tag and GitHub release:
https://github.com/dabbodev/DARWIN/releases/tag/v1.5.0. No package
publication was performed for v1.5.0, and no release assets were uploaded.

Recommended candidate theme: Retained audit compaction and replay summaries.

This roadmap is a planning seed only. It proposes candidate slices for a
future v1.6 planning branch without authorizing feature implementation,
version bumps, package publication, release assets, merge, tag, or release
work.

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

Sprint 3 candidate: Broader grouped replay-summary helpers or read-only
compaction-plan refinements.

- Extend retained lifecycle, poll/admission, encrypted delivery, alias, or
  authority audit summaries by explicit simulator metadata if a later sprint
  accepts that scope.
- Consider deterministic compaction-plan refinements only while keeping them
  separate from apply/delete behavior.
- Prefer read-only helper surfaces before scenario or snapshot exposure.
- Keep summaries diagnostic only.

Sprint 4 candidate: Explicit opt-in compaction apply helper.

- Consider only after read-only planning helpers are stable.
- Keep the helper explicit, caller-driven, and simulator-local.
- Limit mutation to the precisely named retained history selected by the
  caller, if this slice is accepted at all.

Sprint 5 candidate: Scenario DSL coverage.

- Add focused scenario actions and assertions only after helper semantics are
  stable.
- Preserve the existing checked-in scenario continuity expectations.
- Keep scenario coverage symbolic and deterministic.

Sprint 6 candidate: Detailed snapshot visibility.

- Add detailed snapshot/debug visibility only after retained compaction or
  replay-summary action results exist.
- Do not change compact `world.snapshot()`.

Sprint 7 candidate: Release-readiness documentation.

- Update release-readiness docs after scenario coverage exists.
- Confirm scenario metadata continuity and final validation expectations.
- Preserve v1.5.0 as the latest released version until explicit release prep
  changes that status.

## Planning Acceptance Targets

- v1.6 content remains clearly marked as planning, draft, and unreleased.
- v1.5.0 remains the latest released version.
- Implemented helper behavior remains limited to explicit read-only planning
  and diagnostic surfaces with focused tests; no scenario behavior or version
  bump is added by these planning sprints.
- Existing mailbox delivery, encrypted delivery, TrafficHub routing, alias,
  identity, stream-offer polling/admission, lifecycle planning/apply, retained
  histories, scenario, detailed snapshot, compact snapshot, and canonical
  identity behavior remains unchanged.
- Compact `world.snapshot()` output remains unchanged.
- No package publication, release assets, merge, tag, release, real
  networking, DNS lookup, external services, real cryptography, production
  E2EE, delivery enforcement, automatic cleanup workers, retry loops, durable
  queues, live timers, delivery changes, TrafficHub routing changes, compact
  snapshot changes, or canonical identity rewrites are introduced.

## Release Status

v1.6 is unreleased planning only. Release prep has not started. No v1.6
implementation scope is locked in by this document, and no package
publication, release assets, merge, tag, GitHub release, or version bump is
authorized by this roadmap seed.

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
