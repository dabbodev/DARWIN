# DARWIN v1.5 Draft Release Notes

Status: release-facing notes for the v1.5.0 release-prep branch.
DARWIN v1.5.0 has been prepared on `v1.5/planning` as `darwin-sim 1.5.0`.
DARWIN v1.4.0 remains the latest tagged GitHub release on `main` until a
separate merge, tag, and release step is explicitly performed. The annotated
`v1.4.0` tag and GitHub release exist:
https://github.com/dabbodev/DARWIN/releases/tag/v1.4.0. No package
publication was performed for v1.4.0 or by this v1.5.0 release-prep sprint,
and no release assets were uploaded.

Sprint 1 through Sprint 6 planning work has been added on the v1.5 planning
branch, including focused scenario DSL coverage through `066` and
release-candidate hardening for documentation/readiness checks. Release prep
sets the package and CLI version to `darwin-sim 1.5.0`. No merge to `main`,
tag, GitHub release, package publication, or release asset upload is performed
by this sprint.

This possible release line must remain symbolic simulator metadata flow only.
It must not become real networking, a network service, production DDoS
protection, a firewall, a privacy or anonymity system, DNS, an external
service, real cryptography, production E2EE, a delivery enforcement layer, or
a background cleanup system.

## Draft Release Theme

Lifecycle explanation retention policy and audit pruning summaries.

Implemented v1.5 planning work includes:

- Read-only retention-policy models for lifecycle explanation history.
- Deterministic pruning-plan helpers that identify candidates without deleting
  anything by default.
- Grouped pruning summaries by explicit simulator metadata such as candidate
  category, reason, and source.
- An explicit opt-in prune/apply helper after read-only planning helpers
  stabilized.
- Scenario DSL coverage for retention classification, pruning plans, and
  explicit pruning apply.
- Detailed snapshot visibility after retained policy/pruning data exists.
- Release-readiness documentation and checks after scenario coverage exists.

## Compatibility Target

v1.5 planning work preserves these compatibility expectations:

- Existing mailbox delivery behavior remains unchanged.
- Existing encrypted delivery behavior remains unchanged.
- Existing TrafficHub routing behavior remains unchanged.
- Existing alias, identity, stream-offer polling/admission, lifecycle
  planning, lifecycle apply, retained-history, explanation, audit summary,
  snapshot, and scenario behavior remains unchanged outside explicitly scoped
  v1.5 helper surfaces.
- Compact `world.snapshot()` output remains unchanged.
- Existing scenarios `001` through `063` continue to pass unchanged, and
  Scenarios `064` through `066` are intentionally added and documented.
- The checked-in scenario set is contiguous from `001` through `066`.
- The package and CLI version report `darwin-sim 1.5.0` after release prep.

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

Sprint 4 adds scenario DSL coverage for lifecycle explanation retention and
pruning:

- `classify_stream_offer_lifecycle_explanations_for_retention`
- `plan_stream_offer_lifecycle_explanation_pruning`
- `apply_stream_offer_lifecycle_explanation_pruning_plan`
- `stream_offer_lifecycle_retention_decision_contains`
- `stream_offer_lifecycle_pruning_plan_contains`
- `stream_offer_lifecycle_pruning_apply_result_contains`

Scenarios `064` through `066` cover retention classification, read-only
pruning plans, and explicit pruning apply. The scenarios verify that retained
explanation records can be classified as kept or pruning candidates, that
retain filters beat prune filters, that pruning plans do not mutate retained
history, that no pruning occurs without explicit apply, and that explicit
apply reports pruned, retained, ignored, and missing keys deterministically.

Sprint 4 remains simulator-local and caller-driven. Classification and
pruning-plan actions are read-only. The apply action mutates only
`RegistryHub.stream_offer_lifecycle_explanation_history`; it does not mutate
held offers, stream offers, lifecycle plans, lifecycle apply results,
transition history, polling or admission history, delivery state, TrafficHub
state or routing, canonical identity, or compact snapshots.

Sprint 5 adds detailed snapshot/debug visibility for v1.5 lifecycle retention
and pruning action results:

- `stream_offer_lifecycle_retention_decisions`
- `stream_offer_lifecycle_pruning_plans`
- `stream_offer_lifecycle_pruning_apply_results`

The fields are copied JSON-safe detailed-snapshot summaries of existing action
results. Compact `world.snapshot()` output remains unchanged, and no retention
classification, pruning-plan, or pruning-apply semantics change.

Sprint 6: Release-candidate hardening and documentation audit coverage only.
It includes the v1.5 roadmap, draft release notes, retention docs, and
pruning docs in documentation readiness/link checks; confirms checked-in
scenario continuity from `001` through `066`; keeps
`docs/SCENARIO_INDEX.md` exactly generated from deterministic scenario
metadata; and updates README/release-checklist planning language without
claiming merge, tag, GitHub release, package publication, release assets, or
production behavior.

Sprint 6 does not add new feature behavior, new scenarios, retention
classification precedence changes, pruning plan/apply semantic changes,
compact snapshot changes, automatic cleanup workers, retry loops, durable
queues, live timers, live clocks, live polling, delivery behavior changes,
TrafficHub routing changes, networking, DNS lookup, external services, real
cryptography, production E2EE, production privacy/anonymity/firewall/DDoS
guarantees, or canonical identity rewrites.

## Scenario Coverage

The v1.5 planning branch adds scenarios `064` through `066`:

- `scenarios/064_stream_offer_lifecycle_retention_classification.yaml`
- `scenarios/065_stream_offer_lifecycle_pruning_plan.yaml`
- `scenarios/066_stream_offer_lifecycle_pruning_apply.yaml`

The checked-in scenario set is contiguous from `001` through `066`. v1.5
release prep reports package and CLI version `darwin-sim 1.5.0`.

## Current Limitations

- v1.5.0 release prep is complete on `v1.5/planning`.
- Sprint 1 through Sprint 5 planning work has been implemented.
- Focused helper and scenario tests have been added.
- v1.5 scenarios `064` through `066` have been added on the planning branch.
- No merge to `main`, tag, GitHub release, package publication, or release
  asset upload has been performed for v1.5.
- The package and CLI version report `darwin-sim 1.5.0` on this
  release-prep branch.

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
- version bumps beyond `1.5.0`.

## Release Readiness

Release-candidate documentation/readiness hardening has been added for the
v1.5.0 release-prep branch. Release prep set the package and CLI version to
`darwin-sim 1.5.0` and added the changelog release-prep entry. No merge to
`main`, tag, GitHub release, package publication, or release asset upload has
been performed for v1.5.

Final release-prep validation passed `python -m ruff check .`,
`python -m pytest` with 862 tests, `python scripts/run_all_scenarios.py` for
scenarios `001` through `066`, and `python -m darwin.cli.main --version`
reporting `darwin-sim 1.5.0`.
