# DARWIN v1.4 Roadmap Draft: Lifecycle Policy Explanation and Stream-Offer Audit Summaries

Status: planning draft only. DARWIN v1.4 is unreleased, untagged, and not
merged to `main`. The latest released version remains `darwin-sim 1.3.0`.

Recommended candidate theme: Lifecycle policy explanation and stream-offer
audit summaries.

This roadmap seeds possible v1.4 work. It does not authorize feature
implementation, package publication, a version bump, a release, or a commitment
to the exact sprint order below.

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
- Delivery enforcement or mailbox delivery behavior changes.
- TrafficHub routing changes.
- Canonical identity rewrites.
- Production DDoS protection, firewall guarantees, abuse mitigation,
  privacy, anonymity, metadata-hiding, or traffic-analysis guarantees.
- Real cryptography, key generation, private key storage, production E2EE, or
  secure messaging.
- Version bumps beyond `1.3.0` during planning.
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

Status: candidate planning only.

Goal: add the smallest read-only helper surface for explaining lifecycle plan
classification results.

Possible future work:

- Review existing `StreamOfferLifecyclePlan` summary fields and v1.3 planning
  helper boundaries.
- Add a compact explanation model only if the existing plan summary is not
  enough.
- Add a deterministic helper that explains a provided plan without mutating
  hub state.
- Keep explanations copied and JSON-safe.
- Document that explanation text is simulator-local metadata, not policy
  enforcement.

Acceptance targets:

- Existing lifecycle plan behavior remains unchanged.
- Explanation helpers are read-only and caller-driven.
- No real networking, DNS lookup, external services, live timers, automatic
  cleanup workers, durable queues, retry loops, delivery enforcement,
  TrafficHub routing changes, canonical identity rewrites, real cryptography,
  or version bump beyond `1.3.0` is added.

## Candidate Sprint 2: Lifecycle Apply-Result Explanation Helpers

Status: candidate planning only.

Goal: make explicit lifecycle apply outcomes easier to inspect without
changing apply behavior.

Possible future work:

- Explain applied, skipped, stale, terminal, and missing offer outcomes from
  existing apply result metadata.
- Preserve deterministic ordering and copied summary shapes.
- Keep default lifecycle planning read-only until the existing explicit apply
  helper is called.
- Document that explanations do not imply delivery, cleanup, retry, or
  retention guarantees.

Acceptance targets:

- Existing lifecycle apply semantics remain unchanged.
- No held offers are deleted by explanation helpers.
- Transition history remains simulator audit metadata only.
- Compact `world.snapshot()` output remains unchanged unless a later approved
  sprint explicitly scopes otherwise.

## Candidate Sprint 3: Grouped Stream-Offer Lifecycle Audit Summaries

Status: candidate planning only.

Goal: provide deterministic read-only summaries over retained lifecycle audit
metadata.

Possible future work:

- Add grouped summaries by hub, offer, status, and reason.
- Preserve additive filtering and deterministic append-order behavior
  consistent with existing query helpers.
- Keep detailed per-record access separate from grouped summary output.
- Avoid compliance, security, privacy, firewall, DDoS, and delivery claims.

Acceptance targets:

- Summary helpers do not mutate retained histories.
- Summary output is copied and JSON-safe.
- Existing retained transition histories remain RegistryHub-local simulator
  state, not production logs or durable audit trails.

## Candidate Sprint 4: Optional Retained Explanation Records

Status: candidate planning only.

Goal: consider retained explanation records only if they clearly fit existing
audit-history patterns.

Possible future work:

- Decide whether explanation records should be retained at all.
- If retained, keep records explicitly created, deterministic, compact, and
  RegistryHub-local.
- Add query and summarize helpers before any scenario DSL exposure.
- Keep explanation retention separate from production logging, compliance
  evidence, delivery records, or security telemetry.

Acceptance targets:

- No automatic retention worker, cleanup worker, retry loop, live timer, or
  durable queue is introduced.
- Retention does not change lifecycle planning, lifecycle apply, delivery,
  TrafficHub routing, or canonical identity behavior.
- Detailed snapshot visibility is deferred until retained data exists and its
  shape is stable.

## Candidate Sprint 5: Scenario DSL Coverage

Status: candidate planning only.

Goal: expose stable explanation and summary helpers through scenario YAML only
after helper behavior is covered by focused tests.

Possible future work:

- Add read-only scenario actions for lifecycle plan explanations.
- Add read-only scenario actions for lifecycle apply-result explanations.
- Add read-only assertions for grouped lifecycle audit summaries.
- Add scenarios only after helper/model behavior is stable.
- Keep scenario output explicit that explanations and summaries are symbolic
  simulator metadata.

Acceptance targets:

- Existing scenarios `001` through `060` continue to pass unchanged.
- New scenarios, if added in a later implementation sprint, remain contiguous
  and documented.
- Scenario actions do not deliver messages, change TrafficHub routes, open
  sockets, perform DNS lookup, contact external services, generate keys,
  encrypt payloads, enforce delivery, or claim production security.

## Candidate Sprint 6: Detailed Snapshot Visibility and Release Readiness

Status: candidate planning only.

Goal: add visibility and release-readiness docs only after retained data,
summary shapes, and scenario coverage exist.

Possible future work:

- Add detailed snapshot visibility for retained explanation records only if
  retained data exists.
- Keep compact `world.snapshot()` unchanged unless explicitly scoped later.
- Refresh scenario index, documentation links, and release-readiness checks.
- Convert draft release notes to release-facing language only during explicit
  release prep.
- Run full validation before any release decision.

Acceptance targets:

- No package publication, merge, tag, GitHub release, release assets, or
  version bump is performed by planning work.
- v1.3.0 remains the latest released version until a later explicit release
  prep changes that status.
- Docs avoid production networking, DNS, external service, cryptography,
  delivery, privacy, anonymity, firewall, DDoS, cleanup, queue, timer,
  TrafficHub, and canonical identity claims.

## Recommended First Implementation Sprint

Start with Candidate Sprint 1 only if v1.4 implementation is later approved.
Lifecycle plan explanation is the smallest safe slice because it can operate
over already-existing copied plan metadata without changing lifecycle apply,
retained histories, scenario DSL, snapshots, delivery behavior, TrafficHub
routing, canonical identity, networking, or cryptography.

## Release Status

v1.4 is a planning draft only. No v1.4 code, tests for new behavior, scenarios,
version bump, merge, tag, GitHub release, package publication, or release
assets are part of this roadmap seed.

The latest released DARWIN version remains `darwin-sim 1.3.0` with annotated
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
  bump beyond `1.3.0` during planning.
