# DARWIN v1.4 Roadmap Draft: Lifecycle Policy Explanation and Stream-Offer Audit Summaries

Status: release-prep candidate with Sprint 1 through Sprint 6 work on
the v1.4 planning branch. DARWIN v1.4.0 is unreleased, untagged, and not
merged to `main`. The branch package and CLI version are `darwin-sim 1.4.0`;
the latest published release remains `darwin-sim 1.3.0`.

Recommended candidate theme: Lifecycle policy explanation and stream-offer
audit summaries.

This roadmap records the v1.4 planning and release-prep scope. It does not
authorize additional feature implementation, package publication, a release, or
a commitment beyond the explicit branch release-prep version bump.

v1.4 should remain simulator-first and symbolic. It should not become
production networking, a real DDoS protection system, a firewall product, a
privacy or anonymity system, DNS, registrar infrastructure, external service
discovery, a secure messaging protocol, a production cryptography project, or
a delivery enforcement layer.

## Core Concept

Explore small, deterministic explanation and summary surfaces around the
stream-offer lifecycle helpers introduced in v1.3.

v1.3 added retained lifecycle transition history, read-only lifecycle planning,
an explicit lifecycle plan apply helper, scenario DSL coverage, and detailed
snapshot visibility for lifecycle artifacts. A possible v1.4 line could make
those lifecycle decisions easier to inspect by adding concise explanation
helpers and grouped audit summaries without changing the underlying lifecycle,
delivery, routing, identity, networking, or cryptography behavior.

The primary planning question is:

```text
Can DARWIN explain stream-offer lifecycle plans, apply results, and retained
audit metadata in compact simulator summaries without adding new enforcement,
delivery, routing, timer, queue, networking, or production security behavior?
```

## Planning Boundaries

Candidate in scope:

- Read-only explanation helpers for stream-offer lifecycle plans.
- Read-only explanation helpers for lifecycle apply results.
- Summarized lifecycle audit views grouped by hub, offer, status, and reason.
- Retained explanation records only if they fit existing RegistryHub-local
  audit-history patterns and remain opt-in or explicitly recorded.
- Scenario DSL coverage only after helper and model slices are stable.
- Detailed snapshot visibility only after retained explanation or summary data
  exists.
- Release-readiness documentation after scenario coverage exists.

Out of scope:

- Real networking, sockets, HTTP, WebSocket, DNS, or service discovery.
- Registrar integration, public CA behavior, external services, or production
  identity proof.
- Live polling, live timers, live clocks, automatic cleanup workers,
  background services, durable queues, or retry loops.
- Delivery enforcement, mailbox delivery behavior changes, or delivery
  behavior changes.
- TrafficHub routing changes.
- Canonical identity rewrites.
- Production DDoS protection, firewall guarantees, abuse mitigation,
  privacy, anonymity, metadata-hiding, or traffic-analysis guarantees.
- Real cryptography, key generation, private key storage, production E2EE, or
  secure messaging.
- Version bumps beyond `1.4.0` during release prep.
- Merge, tag, GitHub release, package publication, or release assets.

## Candidate Concepts

Lifecycle plan explanation:

- A copied JSON-safe read-only explanation of why a lifecycle plan classified
  offers as expired, active, cleanup candidates, ignored, or ineligible.
- It should describe helper decisions already present in plan metadata rather
  than recomputing policy from live clocks or external state.
- It should not mutate offers, record transitions, delete data, deliver
  messages, or enforce policy.

Lifecycle apply-result explanation:

- A copied JSON-safe read-only explanation of which planned offers were
  applied, skipped, stale, terminal, or missing.
- It should make existing apply result summaries easier to inspect without
  changing apply semantics.
- It should not turn lifecycle apply into a retry service, cleanup daemon,
  durable queue, delivery mechanism, or production audit log.

Grouped lifecycle audit summary:

- A deterministic summary over retained stream-offer lifecycle transition
  metadata, grouped by explicit simulator dimensions such as hub ID, offer ID,
  status, and reason.
- It should preserve append-order detail where useful and avoid claims of
  compliance-grade auditability.

Retained explanation records:

- Optional retained records may be considered only if they follow existing
  RegistryHub-local history patterns.
- They should remain simulator audit metadata, not durable evidence,
  production logs, security telemetry, or privacy-preserving traces.

## Candidate Sprint 1: Lifecycle Plan Explanation Helpers

Status: implemented on the v1.4 planning branch.

Goal: add the smallest read-only helper surface for explaining lifecycle plan
classification results.

Possible future work:

- Review existing `StreamOfferLifecyclePlan` summary fields and v1.3 planning
  helper boundaries.
- Added compact `StreamOfferLifecycleExplanation` metadata for plan and apply
  explanations.
- Added deterministic helpers that explain provided plan/apply result models
  without mutating hub state.
- Kept explanations copied and JSON-safe.
- Documented that explanation metadata is simulator-local diagnostics, not
  policy enforcement.

Acceptance targets:

- Existing lifecycle plan behavior remains unchanged.
- Explanation helpers are read-only and caller-driven.
- No real networking, DNS lookup, external services, live timers, automatic
  cleanup workers, durable queues, retry loops, delivery enforcement,
  TrafficHub routing changes, canonical identity rewrites, real cryptography,
  or version bump beyond `1.4.0` is added.

## Candidate Sprint 2: Grouped Stream-Offer Lifecycle Audit Summaries

Status: implemented on the v1.4 planning branch.

Goal: provide deterministic read-only summaries over retained lifecycle audit
metadata.

Possible future work:

- Added `StreamOfferLifecycleAuditSummary` grouped diagnostic metadata.
- Added grouped summaries by offer, status, reason, and optional explanation
  category.
- Preserved deterministic ordering and copied JSON-safe summary shapes.
- Kept detailed per-record access separate from grouped summary output.
- Documented that audit summaries are simulator-local diagnostics, not
  policy enforcement, cleanup, retry, delivery, security, privacy, firewall,
  DDoS, network, DNS, or cryptography infrastructure.

Acceptance targets:

- Summary helpers do not mutate retained histories.
- Summary output is copied and JSON-safe.
- Existing retained transition histories remain RegistryHub-local simulator
  state, not production logs or durable audit trails.
- Existing lifecycle plan/apply semantics remain unchanged.
- Compact `world.snapshot()` output remains unchanged.

## Candidate Sprint 3: Optional Retained Explanation Records

Status: implemented on the v1.4 planning branch.

Goal: consider retained explanation records only if they clearly fit existing
audit-history patterns.

Possible future work:

- Added `RegistryHub.stream_offer_lifecycle_explanation_history` as explicitly
  recorded RegistryHub-local simulator metadata.
- Added record, query, and summary helpers for retained
  `StreamOfferLifecycleExplanation` records.
- Preserved deterministic append ordering and copied JSON-safe summaries.
- Added detailed snapshot visibility for the retained history while keeping
  compact `world.snapshot()` output unchanged.
- Kept explanation retention separate from production logging, compliance
  evidence, delivery records, security telemetry, cleanup, retry, delivery,
  networking, DNS, TrafficHub routing, and cryptography behavior.

Acceptance targets:

- No automatic retention worker, cleanup worker, retry loop, live timer, or
  durable queue is introduced.
- Retention does not change lifecycle planning, lifecycle apply, delivery,
  TrafficHub routing, or canonical identity behavior.
- Detailed snapshot visibility is limited to copied retained explanation
  summaries; compact snapshots remain unchanged.

## Candidate Sprint 4: Scenario DSL Coverage

Status: implemented on the v1.4 planning branch.

Goal: expose stable explanation and summary helpers through scenario YAML only
after helper behavior is covered by focused tests.

Implemented work:

- Added read-only scenario actions for lifecycle plan explanations.
- Added read-only scenario actions for lifecycle apply-result explanations.
- Added an explicit scenario action for retained explanation recording.
- Added a read-only scenario action for grouped lifecycle audit summaries.
- Added focused assertions for lifecycle explanations, retained explanation
  history, and grouped lifecycle audit summaries.
- Added scenarios `061` through `063` after helper/model behavior was stable.
- Kept scenario output explicit that explanations and summaries are symbolic
  simulator metadata.

Acceptance targets:

- Existing scenarios `001` through `060` continue to pass unchanged.
- New scenarios remain contiguous through `063` and are documented.
- Scenario actions do not deliver messages, change TrafficHub routes, open
  sockets, perform DNS lookup, contact external services, generate keys,
  encrypt payloads, enforce delivery, or claim production security.

## Candidate Sprint 5: Detailed Snapshot Visibility and Release Readiness

Status: implemented on the v1.4 planning branch.

Goal: add visibility and release-readiness docs only after retained data,
summary shapes, and scenario coverage exist.

Implemented work:

- Confirmed detailed snapshot visibility for retained explanation records under
  each RegistryHub.
- Confirmed top-level detailed snapshot visibility for recent lifecycle
  explanation action results.
- Confirmed top-level detailed snapshot visibility for recent lifecycle audit
  summary action results.
- Added focused snapshot/debug tests for copied summaries, deterministic
  ordering, JSON-safe detailed output, and unchanged compact
  `world.snapshot()` output.
- Refreshed v1.4 documentation and draft release notes for release-prep
  status without claiming merge, tag, GitHub release, package publication, or
  release assets.

Acceptance targets:

- No package publication, merge, tag, GitHub release, or release assets are
  performed by planning or release-prep work.
- v1.3.0 remains the latest published release until a later explicit merge,
  tag, and GitHub release changes that status.
- Compact `world.snapshot()` output remains unchanged.
- Docs avoid production networking, DNS, external service, cryptography,
  delivery, privacy, anonymity, firewall, DDoS, cleanup, queue, timer,
  TrafficHub, and canonical identity claims.

## Candidate Sprint 6: Release-Candidate Hardening and Documentation Audit

Status: implemented on the v1.4 planning branch.

Goal: harden release-readiness checks and audit documentation without adding
new feature behavior.

Implemented work:

- Included v1.4 roadmap, draft release notes, lifecycle explanation docs,
  audit summary docs, and retained explanation history docs in
  documentation readiness/link coverage.
- Confirmed checked-in scenario metadata remains contiguous from `001` through
  `063`.
- Confirmed `docs/SCENARIO_INDEX.md` remains generated from deterministic
  scenario metadata.
- Refreshed README, release checklist, roadmap, and draft release notes for
  v1.4 release-candidate and release-prep status without claiming merge, tag,
  GitHub release, package publication, or release assets.

Acceptance targets:

- No version bump beyond `1.4.0`, merge, tag, GitHub release, release assets,
  package publication, or final release publication language is added.
- No new scenarios are added unless needed to fix deterministic scenario
  index/readiness consistency.
- No new feature behavior, lifecycle mutation behavior, compact snapshot
  change, delivery behavior change, TrafficHub routing change, canonical
  identity rewrite, networking, DNS lookup, external service, real
  cryptography, cleanup worker, retry loop, durable queue, or live timer is
  added.

## Recommended First Implementation Sprint

Sprint 1 is the first implementation slice. Lifecycle plan/apply-result
explanation is the smallest safe slice because it operates over already-existing
copied lifecycle metadata without changing lifecycle apply semantics, retained
histories, scenario DSL, snapshots, delivery behavior, TrafficHub routing,
canonical identity, networking, or cryptography.

## Release Status

v1.4.0 remains unreleased release-prep work on `v1.4/planning`. Sprint 1 code
and tests for read-only stream-offer lifecycle explanations exist on the
planning branch. Sprint 2 code and tests for grouped lifecycle audit summaries
also exist on the planning branch. Sprint 3 retained explanation history,
Sprint 4 scenario DSL coverage, Sprint 5 detailed snapshot/debug visibility,
and Sprint 6 release-candidate documentation audit also exist on the planning
branch. The branch package and CLI version are `darwin-sim 1.4.0`; no merge,
tag, GitHub release, package publication, or release assets are part of this
release-prep step.

The latest published DARWIN release remains `darwin-sim 1.3.0` with annotated
tag `v1.3.0` and GitHub release:
https://github.com/dabbodev/DARWIN/releases/tag/v1.3.0.

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
- Compact snapshot changes unless explicitly scoped by a later sprint.
- Canonical identity rewrites.
- Package publication, release assets, merge, tag, GitHub release, or version
  bump beyond `1.4.0` during release prep.
