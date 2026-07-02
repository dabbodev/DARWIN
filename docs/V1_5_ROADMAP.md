# DARWIN v1.5 Roadmap: Lifecycle Explanation Retention Policy and Audit Pruning Summaries

Status: released on `main` as `darwin-sim 1.5.0`. The annotated `v1.5.0` tag
and GitHub release exist:
https://github.com/dabbodev/DARWIN/releases/tag/v1.5.0. No package
publication was performed, and no release assets were uploaded.

Recommended candidate theme: Lifecycle explanation retention policy and audit
pruning summaries.

This roadmap records candidate planning scope, the implemented Sprint 1
through Sprint 6 slices, and the explicit v1.5.0 version bump. It does not
authorize package publication, release assets, or changes to released v1.5
behavior.

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
- Version bumps beyond `1.5.0`.
- Package publication or release assets.

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
  compact snapshot changes, or version bump beyond `1.5.0` is added.

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

## Sprint 3: Explicit Opt-In Prune Apply Helper

Status: implemented on `v1.5/planning`.

Goal: add a caller-driven helper that applies a pruning plan to retained
lifecycle explanation history only.

Implemented:

- `StreamOfferLifecycleExplanationPruningApplyResult`.
- `apply_stream_offer_lifecycle_explanation_pruning_plan(...)`.
- `summarize_stream_offer_lifecycle_explanation_pruning_apply_result(...)`.
- Explicit removal of currently retained explanation-history records whose
  deterministic keys match pruning-plan candidate keys.
- Deterministic reporting of pruned, retained, ignored, and missing candidate
  keys.

Acceptance targets:

- No automatic pruning or background cleanup exists.
- Apply behavior is explicit, caller-driven, and simulator-local.
- Only `RegistryHub.stream_offer_lifecycle_explanation_history` is mutated.
- Held offers, lifecycle plans, lifecycle apply results, transition history,
  delivery, TrafficHub routing, canonical identity, and compact snapshot
  behavior remain unchanged outside the explicitly scoped helper.
- Compact `world.snapshot()` output remains unchanged.

## Sprint 4: Scenario DSL Coverage

Status: implemented on `v1.5/planning`.

Goal: expose stable lifecycle explanation retention classification,
pruning-plan, and explicit pruning-apply helpers through focused scenario YAML.

Implemented:

- Scenario actions:
  `classify_stream_offer_lifecycle_explanations_for_retention`,
  `plan_stream_offer_lifecycle_explanation_pruning`, and
  `apply_stream_offer_lifecycle_explanation_pruning_plan`.
- Scenario assertions:
  `stream_offer_lifecycle_retention_decision_contains`,
  `stream_offer_lifecycle_pruning_plan_contains`, and
  `stream_offer_lifecycle_pruning_apply_result_contains`.
- Scenarios `064` through `066` covering retention classification, read-only
  pruning plans, and explicit pruning apply.
- Contiguous checked-in scenario metadata through `066`.
- `docs/SCENARIO_INDEX.md` regenerated from deterministic scenario metadata.

Acceptance targets:

- Classification and pruning-plan scenario actions are read-only.
- Pruning apply remains explicit and mutates only
  `RegistryHub.stream_offer_lifecycle_explanation_history`.
- Retain filters continue to take precedence over prune filters.
- No pruning occurs without the explicit apply action.
- Compact `world.snapshot()` output remains unchanged.
- No automatic cleanup workers, retry loops, durable queues, live timers,
  live clocks, networking, DNS lookup, external services, real cryptography,
  delivery changes, TrafficHub routing changes, or canonical identity rewrites
  are introduced.

## Sprint 5: Detailed Snapshot Visibility

Status: implemented on `v1.5/planning`.

Goal: add detailed snapshot/debug visibility only after retained policy,
pruning-plan, or summary data exists.

Implemented:

- Top-level detailed snapshot field
  `stream_offer_lifecycle_retention_decisions`.
- Top-level detailed snapshot field `stream_offer_lifecycle_pruning_plans`.
- Top-level detailed snapshot field
  `stream_offer_lifecycle_pruning_apply_results`.
- Copied JSON-safe summaries for existing v1.5 action results.
- Deterministic action-result ordering matching existing detailed lifecycle
  snapshot conventions.

Acceptance targets:

- No compact snapshot change is introduced.
- Detailed snapshot data does not imply production privacy, security,
  compliance, storage, delivery, routing, networking, DNS, or cryptography
  behavior.

## Sprint 6: Release-Candidate Hardening and Documentation Audit

Status: implemented on `v1.5/planning`.

Goal: harden release-readiness and documentation checks after scenario coverage
exists, without adding new feature behavior.

Implemented:

- v1.5 roadmap, draft release notes, retention docs, and pruning docs are
  included in documentation readiness and link checks.
- Release-readiness checks assert v1.5 reports package and CLI version
  `darwin-sim 1.5.0`.
- Checked-in scenario metadata is confirmed contiguous from `001` through
  `066`.
- `docs/SCENARIO_INDEX.md` remains exactly generated from deterministic
  scenario metadata.
- README and release checklist carry v1.5 release-candidate status without
  claiming package publication or release assets.

Acceptance targets:

- Sprint 6 is release-candidate hardening and documentation audit only.
- No package publication, release assets, or version bump beyond `1.5.0` is
  performed by release-prep work.
- No new feature behavior or new scenarios are added by documentation
  readiness work unless required to fix deterministic scenario index
  consistency.
- Documentation states that v1.5 remains simulator-local and symbolic.
- Documentation avoids production networking, sockets, HTTP/WebSocket
  behavior, DNS lookup, registrar integration, public CA behavior, external
  services, real cryptography, key generation, private key storage, production
  E2EE, delivery enforcement, automatic cleanup workers, retry loops, durable
  queues, live timers, live clocks, live polling, retention/pruning behavior
  beyond explicit simulator helpers, delivery behavior changes, TrafficHub
  routing changes, compact snapshot changes, canonical identity rewrites, and
  production anonymity/privacy/firewall/DDoS guarantees.

## Release Prep

Status: complete and released on `main`.

Release prep set the package and CLI version to `darwin-sim 1.5.0`, updated
release notes, updated the changelog release entry, and updated readiness
tests and docs. Package publication or release asset upload requires a
separate explicit request.

## Release Status

v1.5.0 is released on `main` as `darwin-sim 1.5.0`. Sprint 1 through Sprint 6
work is released, including focused v1.5 scenario coverage through `066` and
release-candidate documentation hardening. The annotated `v1.5.0` tag and
GitHub release exist:
https://github.com/dabbodev/DARWIN/releases/tag/v1.5.0. No package
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
- Package publication, release assets, or version bump beyond `1.5.0`.
