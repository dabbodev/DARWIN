# Retained Audit Compaction Apply v1.6

Status: released in v1.6.0 on `main`. The package version reports
`darwin-sim 1.6.0`.

Sprint 6 release-candidate hardening and documentation audit confirms this
document is included in deterministic documentation readiness/link checks. It
does not change compaction-apply semantics or add behavior beyond the explicit
caller-driven simulator helper.

Sprint 5 adds detailed debug-snapshot visibility for scenario action results.
`World.detailed_snapshot()` exposes copied, deterministic apply-result
summaries at top-level `retained_audit_compaction_apply_results`; compact
`world.snapshot()` remains unchanged.

Retained audit compaction apply is an explicit caller-driven mutation helper
for selected retained audit-history metadata. It accepts an explicit
`RegistryHub` and an explicit `RetainedAuditCompactionDecision`, then removes
only currently matching `compaction_candidate` records from the decision's
selected retained history.

The helper is not automatic cleanup, not a worker, not a retry loop, not a
durable queue, not a live timer, not a delivery trigger, and not production
data-retention infrastructure.

## Supported Record Families

Sprint 3 applies decisions only for these retained stream-offer audit
families:

- `stream_offer_lifecycle_explanation`
- `stream_offer_status_transition`

Unsupported retained-history families, including mixed decisions, are handled
deterministically as no-op apply results. They do not mutate retained
histories.

## Apply Result Model

`RetainedAuditCompactionApplyResult` records:

- `hub_id`
- `policy_id`
- `history_type`
- `compacted_record_keys`
- `retained_record_keys`
- `ignored_record_keys`
- `missing_record_keys`
- `unsupported_record_keys`
- deterministic counts for each key group
- optional JSON-safe `metadata`

Record keys use the same deterministic sequence-style key shapes as the
Sprint 1 compaction classification and Sprint 2 replay summary helpers.

## Helper

Sprint 3 adds:

- `apply_retained_audit_compaction_decision(...)`
- `summarize_retained_audit_compaction_apply_result(...)`

`apply_retained_audit_compaction_decision(...)` mutates only the selected
retained history named by `decision.history_type`. It removes only records
whose current deterministic keys match `decision.compaction_candidate_record_keys`.
Remaining retained records preserve their original order.

Candidate keys that are not currently present in the selected retained history
are reported as `missing_record_keys`. Retained and ignored keys are reported
only when they are currently present in the selected retained history.

## Mutation Boundaries

Compaction apply does not mutate:

- held offers;
- stream offers;
- lifecycle plans;
- lifecycle apply results;
- polling histories;
- admission histories;
- encrypted delivery histories;
- alias histories;
- authority histories;
- delivery state;
- TrafficHub state or routing;
- unrelated retained histories;
- compact `world.snapshot()` output;
- canonical identity state.

The helper does not run automatically, does not require scenario context, and
does not use live clocks.

## Non-Goals

Sprint 3 provides no production privacy, anonymity, compliance, firewall, or
DDoS guarantees.

Sprint 3 adds no automatic cleanup workers, background services, retry loops,
durable queues, live timers, live clocks, live polling, sockets, HTTP or
WebSocket behavior, DNS lookup, registrar integration, public CA behavior,
external services, real cryptography, key generation, private key storage,
production E2EE, delivery enforcement, delivery behavior changes, TrafficHub
routing changes, scenario DSL actions, scenario DSL assertions, compact
snapshot changes, canonical identity rewrites, package publication, release
assets, or version bump beyond `1.6.0`.
