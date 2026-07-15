# DARWIN v1.6 Draft Release Notes

Status: unreleased release-candidate draft. v1.6 Sprint 6 is
release-candidate hardening and documentation audit only; final release
preparation and release execution have not started. The latest released
version remains `darwin-sim 1.5.0` on `main` with the annotated `v1.5.0` tag
and GitHub release:
https://github.com/dabbodev/DARWIN/releases/tag/v1.5.0. No package
publication was performed for v1.5.0, and no release assets were uploaded.

This draft remains planning-only and is not final release language. It must
not be treated as a version bump, a changelog release entry, a package
publication plan, or a GitHub release plan.

Implemented planning work remains symbolic simulator metadata flow only. It
must not become real networking, a network service, production DDoS
protection, a firewall, a privacy or anonymity system, DNS, an external
service, real cryptography, production E2EE, a delivery enforcement layer, a
TrafficHub routing change, or a background cleanup system.

## Draft Release Theme

Retained audit compaction and replay summaries.

Implemented v1.6 planning work now includes:

- Read-only audit compaction policy and decision models for retained simulator
  histories.
- Deterministic classification helpers that summarize candidates without
  deleting or rewriting retained histories.
- Grouped replay-summary helpers for lifecycle explanation and status-
  transition histories only.
- Explicit opt-in compaction/apply for a decision's single supported retained
  history.
- Focused scenario DSL coverage for the stable helper and model slices.
- Detailed debug-snapshot visibility for retained-audit compaction decisions,
  replay summaries, and compaction apply results.

Broader retained-history families remain later candidates. Sprint 6 adds only
release-candidate hardening and documentation audit work.

## Compatibility Target

Any future v1.6 implementation should preserve these compatibility
expectations unless a later sprint explicitly and narrowly says otherwise:

- Existing mailbox delivery behavior remains unchanged.
- Existing encrypted delivery behavior remains unchanged.
- Existing TrafficHub routing behavior remains unchanged.
- Existing alias, identity, stream-offer polling/admission, lifecycle
  planning, lifecycle apply, retained-history, explanation, audit summary,
  snapshot, and scenario behavior remains unchanged outside explicitly scoped
  v1.6 planning/helper surfaces.
- Compact `world.snapshot()` output remains unchanged.
- The checked-in scenario set is contiguous from `001` through `069` after
  the intentional Sprint 4 scenario additions.
- The package and CLI version continue to report `darwin-sim 1.5.0` during
  planning.

## Draft Sprint Notes

Sprints 1 through 5 implement the retained-audit helper, scenario, and
detailed-snapshot slices summarized below. Sprint 6 does not add feature
behavior; its release-candidate hardening is documented separately after the
implemented sprint notes.

Sprint 1 on the v1.6 planning branch adds read-only retained audit compaction
policy and decision metadata:

- `RetainedAuditCompactionPolicy`
- `RetainedAuditCompactionDecision`
- pure helpers to classify explicit retained audit records and summarize the
  resulting decision

The initial supported retained-history families are stream-offer lifecycle
explanation history and stream-offer lifecycle transition history. Unsupported
retained-history families are ignored deterministically and remain future work.

Sprint 1 does not add deletion, compaction, mutation, rewriting, cleanup
scheduling, delivery behavior, TrafficHub routing changes, scenario DSL
coverage, detailed snapshot changes, compact `world.snapshot()` changes, live
timers, retry loops, durable queues, networking, DNS, external services, real
cryptography, production security infrastructure, release behavior, or a
version bump.

Sprint 2 on the v1.6 planning branch adds read-only retained audit replay
summary metadata:

- `RetainedAuditReplaySummary`
- pure helpers to summarize explicit retained audit records, group by retained
  history type and reason, and optionally filter through retained or
  compaction-candidate record keys from a
  `RetainedAuditCompactionDecision`

The Sprint 2 supported retained-history families remain stream-offer
lifecycle explanation history and stream-offer lifecycle transition history.
Unsupported retained-history families are handled deterministically and remain
future work for broader replay summaries.

Sprint 2 does not delete, compact, mutate, rewrite, replace, schedule cleanup,
replay network traffic, trigger delivery, add scenario DSL coverage, add
detailed snapshot changes, change compact `world.snapshot()`, add live
timers, retry loops, durable queues, networking, DNS, external services, real
cryptography, production security infrastructure, release behavior, or a
version bump.

Sprint 3 on the v1.6 planning branch adds an explicit retained audit
compaction apply helper:

- `RetainedAuditCompactionApplyResult`
- `apply_retained_audit_compaction_decision(...)`
- `summarize_retained_audit_compaction_apply_result(...)`

The Sprint 3 helper accepts an explicit `RegistryHub` and explicit
`RetainedAuditCompactionDecision`, mutates only the selected retained history
for supported stream-offer lifecycle explanation or status-transition records,
removes only currently matching compaction-candidate records, preserves
remaining retained history order, and reports compacted, retained, ignored,
missing, and unsupported keys deterministically.

Sprint 3 does not run automatically, schedule cleanup, add workers, retry
loops, durable queues, live timers, live clocks, networking, DNS, external
services, real cryptography, delivery changes, TrafficHub routing changes,
scenario DSL coverage, detailed snapshot changes, compact
`world.snapshot()` changes, canonical identity rewrites, release behavior, or
a version bump.

Sprint 4 on the v1.6 planning branch adds scenario DSL coverage for the
existing retained audit helper semantics:

- `classify_retained_audit_records_for_compaction`
- `summarize_retained_audit_replay`
- `apply_retained_audit_compaction_decision`
- `retained_audit_compaction_decision_contains`
- `retained_audit_replay_summary_contains`
- `retained_audit_compaction_apply_result_contains`

Classification and replay-summary actions are read-only. The apply action
requires an explicit prior compaction decision action result, delegates to the
existing apply helper, and mutates only the decision's selected supported
retained history. Scenario record inputs are enumerated deterministically so
single-history decision keys remain compatible with explicit apply.

Sprint 4 adds scenarios `067` through `069` for classification categories,
retain-filter precedence, replay grouping by retained history type and reason,
replay filtering by decision category, explicit selected-history apply,
unsupported and missing record-key reporting, and the absence of automatic
compaction.

Sprint 4 does not add detailed or compact snapshot changes, automatic cleanup,
workers, retry loops, durable queues, live timers, live clocks, networking,
DNS, external services, real cryptography, delivery changes, TrafficHub
routing changes, canonical identity rewrites, release behavior, or a version
bump.

Sprint 5 on the v1.6 planning branch exposes existing retained-audit scenario
action results in detailed debug snapshots:

- `retained_audit_compaction_decisions`
- `retained_audit_replay_summaries`
- `retained_audit_compaction_apply_results`

These top-level fields use the existing deterministic, JSON-safe action-result
summaries and are isolated copies. Sprint 5 does not change compact
`world.snapshot()`, compaction classification precedence, replay-summary
semantics, compaction-apply semantics, scenarios, the package version, or any
delivery, TrafficHub routing, cleanup-worker, retry-loop, durable-queue,
timer, networking, DNS, external-service, cryptography, or canonical-identity
behavior.

## Sprint 6: Release-Candidate Hardening and Documentation Audit

Sprint 6 is release-candidate hardening and documentation audit only. It:

- includes the v1.6 roadmap, draft release notes, compaction-policy,
  replay-summary, and compaction-apply docs in documentation
  readiness/link checks;
- verifies the checked-in scenario library is contiguous from `001` through
  `069` and that `docs/SCENARIO_INDEX.md` is exactly generated from
  deterministic scenario metadata; and
- records the implemented Sprints 1 through 5 scope and its
  simulator-local, symbolic limitations without claiming v1.6 has released.

Sprint 6 does not add scenarios unless needed to repair deterministic index
consistency. It does not change classification precedence, replay-summary
semantics, compaction-apply semantics, compact `world.snapshot()`, mailbox or
encrypted delivery behavior, TrafficHub routing, or canonical identity
behavior. It adds no automatic cleanup workers, retry loops, durable queues,
live timers, live clocks, live polling, networking, DNS, external services,
real cryptography, production E2EE, production privacy, anonymity, firewall,
DDoS, compliance, or data-retention guarantees.

## Scenario Coverage

Checked-in v1.6 planning scenarios:

- `067_retained_audit_compaction_classification`
- `068_retained_audit_replay_summary`
- `069_retained_audit_compaction_apply`

The checked-in scenario library is contiguous from `001` through `069`. The
latest released version remains v1.5.0, and the package and CLI continue to
report `darwin-sim 1.5.0`.

## Current Limitations

- v1.6 is unreleased planning only.
- v1.6 work remains limited to retained audit compaction classification,
  replay summary helpers, the explicit simulator-local compaction apply
  helper, focused Sprint 4 scenario DSL coverage, and Sprint 5 detailed
  snapshot visibility.
- Sprint 6 changes release-readiness checks and documentation only; it adds no
  compaction behavior beyond explicit simulator helpers.
- No package publication or release asset upload is planned by this document.
- The package and CLI version remain `darwin-sim 1.5.0`.

## Non-Goals

v1.6 planning does not add:

- real networking;
- sockets;
- HTTP or WebSocket behavior;
- DNS lookup;
- registrar integration;
- public CA behavior;
- external services;
- live polling loops;
- automatic cleanup workers;
- retry loops;
- durable queues;
- live timers;
- live clocks;
- production DDoS guarantees;
- production firewall guarantees;
- production privacy guarantees;
- production anonymity guarantees;
- real cryptography;
- key generation;
- private key storage;
- encryption or decryption;
- production E2EE;
- delivery enforcement;
- delivery behavior changes;
- mailbox delivery behavior changes;
- encrypted delivery behavior changes;
- TrafficHub routing changes;
- compact snapshot changes;
- canonical identity rewrites;
- package publication;
- release assets;
- version bumps beyond `1.5.0` during planning.

## Release Readiness

Sprint 6 hardens release-candidate documentation and readiness checks only.
Final release validation, `CHANGELOG.md` release updates, version bumps,
merge, tag, GitHub release, release assets, and package publication remain out
of scope until explicitly requested later.
