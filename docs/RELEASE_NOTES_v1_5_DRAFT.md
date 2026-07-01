# DARWIN v1.5 Draft Release Notes

Status: draft planning placeholder for an unreleased v1.5 line. DARWIN v1.4.0
remains the latest released version on `main` as `darwin-sim 1.4.0`. The
annotated `v1.4.0` tag and GitHub release exist:
https://github.com/dabbodev/DARWIN/releases/tag/v1.4.0. No package
publication was performed, and no release assets were uploaded.

Sprint 1 read-only retention policy/classification helpers have been added on
the v1.5 planning branch. No v1.5 scenario coverage, release-candidate work,
version bump, merge to `main`, tag, GitHub release, package publication, or
release assets exist yet. These notes remain a draft placeholder for future
release-facing scope.

This possible release line must remain symbolic simulator metadata flow only.
It must not become real networking, a network service, production DDoS
protection, a firewall, a privacy or anonymity system, DNS, an external
service, real cryptography, production E2EE, a delivery enforcement layer, or
a background cleanup system.

## Draft Release Theme

Lifecycle explanation retention policy and audit pruning summaries.

Candidate v1.5 work may include:

- Read-only retention-policy models for lifecycle explanation history.
- Deterministic pruning-plan helpers that identify candidates without deleting
  anything by default.
- Grouped retention and audit summaries by hub, offer, category, reason, age
  bucket, source, or other explicit simulator metadata.
- An explicit opt-in prune/apply helper only after read-only planning helpers
  are stable.
- Scenario DSL coverage only after helper/model slices are stable.
- Detailed snapshot visibility only after retained policy/pruning data exists.
- Release-readiness documentation after scenario coverage exists.

## Compatibility Target

Future v1.5 work should preserve these compatibility expectations unless a
later sprint explicitly narrows and documents an exception:

- Existing mailbox delivery behavior remains unchanged.
- Existing encrypted delivery behavior remains unchanged.
- Existing TrafficHub routing behavior remains unchanged.
- Existing alias, identity, stream-offer polling/admission, lifecycle
  planning, lifecycle apply, retained-history, explanation, audit summary,
  snapshot, and scenario behavior remains unchanged outside explicitly scoped
  v1.5 helper surfaces.
- Compact `world.snapshot()` output remains unchanged.
- Existing scenarios `001` through `063` continue to pass unchanged until any
  future scenario additions are intentionally added and documented.
- The package and CLI version remain `darwin-sim 1.4.0` during planning.

## Draft Sprint Summary

Sprint 1 adds read-only retention-policy models and classification helpers for
lifecycle explanation history:

- `StreamOfferLifecycleExplanationRetentionPolicy`
- `StreamOfferLifecycleExplanationRetentionDecision`
- `make_stream_offer_lifecycle_explanation_retention_policy(...)`
- `classify_stream_offer_lifecycle_explanations_for_retention(...)`
- `summarize_stream_offer_lifecycle_explanation_retention_decision(...)`

The helpers classify explicit `StreamOfferLifecycleExplanation` records as
`kept`, `prune_candidate`, or `ignored` using deterministic sequence-style
keys. Retain filters take precedence over prune filters; `max_records` is then
applied deterministically to otherwise kept matching-hub records. Sprint 1 is
diagnostic only and does not mutate retained histories, delete data, run
cleanup, schedule retries, contact networks, use DNS, call external services,
change compact snapshots, change delivery, change TrafficHub routing, rewrite
canonical identity, or add real cryptography.

Sprint 2 adds deterministic read-only pruning-plan helpers for lifecycle
explanation history:

- `StreamOfferLifecycleExplanationPruningPlan`
- `plan_stream_offer_lifecycle_explanation_pruning(...)`
- `summarize_stream_offer_lifecycle_explanation_pruning_plan(...)`
- `summarize_stream_offer_lifecycle_explanation_pruning_by_reason(...)`
- `summarize_stream_offer_lifecycle_explanation_pruning_by_category(...)`

The helpers map Sprint 1 retention decisions into retained, pruning-candidate,
and ignored explanation keys, with deterministic candidate counts by category,
reason, and source when explicit explanation records are supplied. Sprint 2 is
diagnostic only and does not delete, prune, mutate retained histories, schedule
cleanup, run workers, retry work, create queues, use live timers, contact
networks, use DNS, call external services, change compact snapshots, change
delivery, change TrafficHub routing, rewrite canonical identity, or add real
cryptography.

Sprint 3 adds an explicit opt-in pruning apply helper for retained lifecycle
explanation history:

- `StreamOfferLifecycleExplanationPruningApplyResult`
- `apply_stream_offer_lifecycle_explanation_pruning_plan(...)`
- `summarize_stream_offer_lifecycle_explanation_pruning_apply_result(...)`

The helper requires an explicit `RegistryHub` and explicit pruning plan. It
removes only currently retained explanation-history records whose deterministic
keys match plan candidates, preserves the order of remaining history, and
reports pruned, retained, ignored, and missing candidate keys. It only mutates
`RegistryHub.stream_offer_lifecycle_explanation_history`; it does not mutate
held offers, lifecycle plans, lifecycle apply results, transition history,
polling or admission history, delivery state, TrafficHub state or routing,
canonical identity, or compact snapshots.

Sprint 3 remains simulator-local and caller-driven. It does not add automatic
cleanup, a background worker, retry loop, durable queue, live timer, live
clock, delivery enforcement, networking, DNS, external service integration,
real cryptography, production E2EE, production data-retention infrastructure,
privacy guarantees, anonymity guarantees, firewall guarantees, or DDoS
guarantees.

Sprint 4 may add grouped retention and audit summaries over retained
explanation history and pruning-plan metadata. The summaries should remain
simulator-local diagnostics, not durable audit trails, production telemetry,
security evidence, privacy guarantees, or compliance records.

Sprint 5 may add scenario DSL coverage only after helper and model behavior is
stable. Scenario actions should remain explicit that retention and pruning
metadata is symbolic simulator metadata.

Sprint 6 may add detailed snapshot/debug visibility only after retained
policy, pruning-plan, or summary data exists. Compact `world.snapshot()` output
should remain unchanged.

Sprint 7 may harden release-readiness documentation only after scenario
coverage exists. Planning work must not create release assets, package
publication, tags, GitHub releases, or version bumps.

## Scenario Coverage

No v1.5 scenarios exist yet. The released scenario set remains contiguous from
`001` through `063` for v1.4.0.

Future v1.5 scenarios, if added later, should be introduced only after the
corresponding helper/model behavior is stable and should remain contiguous and
documented.

## Current Limitations

- v1.5 is unreleased.
- Only Sprint 1 read-only retention policy/classification helpers have been
  implemented.
- Focused Sprint 1 helper tests have been added.
- No v1.5 scenarios for new behavior have been added.
- No version bump has been performed.
- No merge to `main`, tag, GitHub release, package publication, or release
  asset upload has been performed for v1.5.
- DARWIN v1.4.0 remains the latest released version and reports
  `darwin-sim 1.4.0`.

## Non-Goals

v1.5 planning does not add:

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
- merge to `main`;
- tags or GitHub releases;
- version bumps beyond released `1.4.0`.

## Release Readiness

Release readiness has not started for v1.5. This placeholder should be updated
only after implementation, scenario coverage, and release-candidate validation
exist.

Planning validation should continue to pass `python -m ruff check .`,
`python -m pytest`, `python scripts/run_all_scenarios.py`, and
`python -m darwin.cli.main --version` with the CLI still reporting
`darwin-sim 1.4.0`.
