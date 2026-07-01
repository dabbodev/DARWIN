# DARWIN v1.5 Roadmap: Lifecycle Explanation Retention Policy and Audit Pruning Summaries

Status: draft planning seed for an unreleased v1.5 line. DARWIN v1.4.0
remains the latest released version on `main` as `darwin-sim 1.4.0`. The
annotated `v1.4.0` tag and GitHub release exist:
https://github.com/dabbodev/DARWIN/releases/tag/v1.4.0. No package
publication was performed, and no release assets were uploaded.

Recommended candidate theme: Lifecycle explanation retention policy and audit
pruning summaries.

This roadmap records candidate planning scope and the implemented Sprint 1
read-only retention policy/classification slice. It does not authorize version
bumps, package publication, release assets, tagging, release creation, or
changes to released v1.4 behavior.

v1.5 should remain simulator-first and symbolic. It should not become
production networking, a real DDoS protection system, a firewall product, a
privacy or anonymity system, DNS, registrar infrastructure, external service
discovery, a secure messaging protocol, a production cryptography project, a
delivery enforcement layer, or a background cleanup system.

## Core Concept

Explore small, deterministic retention-policy and pruning-summary surfaces
around the v1.4 lifecycle explanation history and lifecycle audit summary
helpers.

v1.4 added read-only lifecycle plan/apply explanations, grouped lifecycle audit
summaries, explicitly retained RegistryHub-local explanation history, scenario
DSL coverage, and detailed snapshot/debug visibility. v1.5 Sprint 1 starts by
modeling symbolic retention policy and producing read-only retention
classification decisions without deleting anything.

The primary planning question is:

```text
Can DARWIN describe lifecycle explanation retention and audit pruning
candidates in compact simulator summaries without adding automatic cleanup,
delivery, routing, timer, queue, networking, cryptography, or production
security behavior?
```

## Planning Boundaries

Candidate in scope:

- Read-only retention-policy models for lifecycle explanation history.
- Deterministic pruning-plan helpers that identify candidates without deleting
  anything by default.
- Grouped retention and audit summaries by hub, offer, category, reason, age
  bucket, source, or other explicit simulator metadata.
- Explicit opt-in prune/apply helper only after read-only planning helpers are
  stable and only if the helper remains caller-driven.
- Scenario DSL coverage only after helper and model slices are stable.
- Detailed snapshot visibility only after retained policy/pruning data exists.
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
- Version bumps beyond the released `1.4.0` until an explicit release-prep
  sprint.
- Package publication, release assets, merge to `main`, tags, or GitHub
  releases.

## Candidate Concepts

Retention-policy model:

- A copied JSON-safe symbolic model that describes how retained lifecycle
  explanation records would be grouped, aged, capped, or classified for review.
- It should describe policy intent using explicit simulator metadata rather
  than wall-clock timers, background services, or external storage.
- It should not mutate retained histories, delete data, compact snapshots,
  deliver messages, route traffic, enforce policy, or claim compliance-grade
  retention guarantees.

Read-only pruning plan:

- A deterministic helper that identifies retained explanation records that
  would be kept, reviewed, or considered pruning candidates under a provided
  symbolic retention policy.
- It should return copied JSON-safe planning metadata and preserve deterministic
  ordering.
- It should not delete records, schedule cleanup, retry work, run timers, or
  behave like a durable queue.

Grouped retention and audit summaries:

- A deterministic summary over retained explanation history and pruning-plan
  metadata, grouped by explicit simulator dimensions such as hub ID, offer ID,
  explanation category, lifecycle reason, source, or age bucket.
- It should make retained simulator diagnostics easier to inspect without
  claiming production auditability, privacy protection, or security telemetry.

Explicit prune/apply helper:

- A later opt-in helper may be considered only after read-only policy and
  pruning-plan helpers are stable.
- If added, it should be caller-driven and explicit, with copied summaries of
  what was removed or skipped.
- It should not become automatic cleanup, a background worker, a retry loop, a
  durable queue, a live timer, or production retention enforcement.

## Sprint 1: Read-Only Retention-Policy Models

Status: implemented as read-only model/helper work.

Goal: define the smallest symbolic policy model for explaining lifecycle
explanation history retention and classify explicit lifecycle explanation
records without mutating retained history.

Implemented:

- `StreamOfferLifecycleExplanationRetentionPolicy`.
- `StreamOfferLifecycleExplanationRetentionDecision`.
- Retention decision categories: `kept`, `prune_candidate`, and `ignored`.
- `make_stream_offer_lifecycle_explanation_retention_policy(...)`.
- `classify_stream_offer_lifecycle_explanations_for_retention(...)`.
- `summarize_stream_offer_lifecycle_explanation_retention_decision(...)`.
- Deterministic sequence-style explanation keys derived from explicit input
  order and explanation fields.
- Documented precedence: retain filters beat prune filters, then `max_records`
  caps otherwise kept matching-hub records deterministically.
- Sprint 1 documentation:
  `docs/STREAM_OFFER_LIFECYCLE_EXPLANATION_RETENTION_v1_5.md`.

Acceptance targets:

- Existing lifecycle explanation history behavior remains unchanged.
- Policy models and classification helpers are read-only and do not mutate
  retained histories.
- No real networking, DNS lookup, external services, live timers, automatic
  cleanup workers, durable queues, retry loops, delivery enforcement,
  TrafficHub routing changes, canonical identity rewrites, real cryptography,
  compact snapshot changes, or version bump beyond released `1.4.0` is added.

## Sprint 2: Deterministic Read-Only Pruning Plans

Status: implemented as read-only model/helper work.

Goal: identify pruning candidates without deleting anything by default.

Implemented:

- `StreamOfferLifecycleExplanationPruningPlan`.
- `plan_stream_offer_lifecycle_explanation_pruning(...)`.
- `summarize_stream_offer_lifecycle_explanation_pruning_plan(...)`.
- `summarize_stream_offer_lifecycle_explanation_pruning_by_reason(...)`.
- `summarize_stream_offer_lifecycle_explanation_pruning_by_category(...)`.
- Read-only plan helpers that map Sprint 1 retention decisions into retained,
  candidate, and ignored explanation keys under explicit simulator policy.
- Preserve deterministic ordering and copied JSON-safe summary shapes.
- Include non-mutating totals by hub, policy, decision category, candidate
  category, candidate reason, and candidate source.
- Keep the helper separate from any apply/delete behavior.
- Sprint 2 documentation:
  `docs/STREAM_OFFER_LIFECYCLE_EXPLANATION_PRUNING_v1_5.md`.

Acceptance targets:

- Planning helpers do not delete or rewrite retained explanation records.
- Existing lifecycle plan/apply, audit summary, scenario, delivery, routing,
  identity, and compact snapshot behavior remains unchanged.
- The helper does not schedule cleanup, run timers, retry work, create durable
  queues, contact networks, use DNS, call external services, or add real
  cryptography.

## Candidate Sprint 3: Grouped Retention and Audit Summaries

Status: draft planning only; not implemented.

Goal: make retained lifecycle explanation and pruning-plan metadata easier to
inspect through grouped summaries.

Possible future work:

- Summarize retained explanation history by hub, offer, category, reason,
  source, and age bucket.
- Summarize pruning-plan candidates by keep/review/prune classification.
- Preserve append-order detail where useful and deterministic group ordering
  everywhere.
- Keep grouped summaries as simulator-local diagnostics, not durable audit
  trails or production telemetry.

Acceptance targets:

- Summary helpers are read-only.
- Summary output is copied and JSON-safe.
- Existing retained histories remain RegistryHub-local simulator state, not
  production logs or compliance records.
- Compact `world.snapshot()` output remains unchanged.

## Candidate Sprint 4: Explicit Opt-In Prune Apply Helper

Status: draft planning only; not implemented.

Goal: consider an explicit caller-driven prune/apply helper only after
read-only policy, plan, and summary helpers are stable.

Possible future work:

- Add an apply helper that accepts an explicit pruning plan and removes only
  records selected by that plan.
- Return copied JSON-safe summaries for removed, skipped, stale, missing, or
  ineligible records.
- Keep the helper separate from background cleanup, live timers, retry loops,
  durable queues, delivery, routing, networking, DNS, external services, and
  cryptography.

Acceptance targets:

- No automatic pruning or background cleanup exists.
- Apply behavior is explicit, caller-driven, and simulator-local.
- Existing lifecycle explanation, audit summary, delivery, TrafficHub routing,
  canonical identity, and compact snapshot behavior remains unchanged outside
  the explicitly scoped helper.

## Candidate Sprint 5: Scenario DSL Coverage

Status: draft planning only; not implemented.

Goal: expose stable retention-policy, pruning-plan, and grouped-summary helpers
through scenario YAML only after focused helper/model tests exist.

Possible future work:

- Add read-only scenario actions for retention-policy planning and pruning-plan
  summaries.
- Add assertions for grouped retention and audit summaries.
- Add explicit prune/apply scenario coverage only if the opt-in helper exists.
- Keep scenario output explicit that retention and pruning metadata is symbolic
  simulator metadata.

Acceptance targets:

- Existing scenarios `001` through `063` continue to pass unchanged.
- New scenarios, if added later, remain contiguous and documented.
- Scenario actions do not deliver messages, change TrafficHub routes, open
  sockets, perform DNS lookup, contact external services, generate keys,
  encrypt payloads, enforce delivery, run cleanup workers, or claim production
  security.

## Candidate Sprint 6: Detailed Snapshot Visibility

Status: draft planning only; not implemented.

Goal: add detailed snapshot/debug visibility only after retained policy,
pruning-plan, or summary data exists.

Possible future work:

- Consider detailed snapshot visibility for recent retention policies, pruning
  plans, and grouped retention summaries.
- Keep detailed output copied, JSON-safe, deterministic, and explicitly
  diagnostic.
- Preserve compact `world.snapshot()` output unchanged.

Acceptance targets:

- No compact snapshot change is introduced.
- Detailed snapshot data does not imply production privacy, security,
  compliance, storage, delivery, routing, networking, DNS, or cryptography
  behavior.

## Candidate Sprint 7: Release-Readiness Documentation

Status: draft planning only; not implemented.

Goal: harden release-readiness checks and documentation only after scenario
coverage exists.

Possible future work:

- Refresh README, release checklist, roadmap, draft release notes, scenario
  index, and related docs after implementation scope is known.
- Confirm scenario metadata remains contiguous after any new scenario coverage.
- Keep release-readiness docs clear that v1.5 remains simulator-local and
  symbolic.

Acceptance targets:

- No package publication, release assets, merge, tag, GitHub release, or
  version bump is performed by planning work.
- No new feature behavior is added by documentation readiness work.
- Documentation avoids production networking, DNS, external service,
  cryptography, delivery, privacy, anonymity, firewall, DDoS, cleanup, queue,
  timer, TrafficHub, compact snapshot, and canonical identity claims.

## Recommended First Implementation Sprint

If v1.5 implementation begins later, Sprint 1 is the smallest safe first
slice. Read-only retention-policy models can operate over explicit simulator
metadata without mutating retained explanation history, applying pruning,
changing lifecycle behavior, changing delivery, changing TrafficHub routing,
rewriting canonical identity, contacting networks, using DNS, adding real
cryptography, changing compact snapshots, or bumping the released version.

## Release Status

v1.5 is unreleased. Sprint 1 read-only retention policy/classification helpers
exist on the planning branch, but no v1.5 scenario coverage, release-candidate
work, version bump, merge to `main`, tag, GitHub release, package publication,
or release assets exist.

v1.4.0 remains the latest released version on `main` as
`darwin-sim 1.4.0`. The annotated `v1.4.0` tag and GitHub release exist:
https://github.com/dabbodev/DARWIN/releases/tag/v1.4.0. No package
publication was performed, and no release assets were uploaded.

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
- Package publication, release assets, merge to `main`, tags, GitHub releases,
  or version bump beyond released `1.4.0`.
