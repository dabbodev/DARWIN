# Retained Audit Compaction Policy v1.6

Status: v1.6 Sprint 1 helper included in the v1.6.0 release-prep branch. The
package version reports `darwin-sim 1.6.0`.

Sprint 6 release-candidate hardening and documentation audit confirms this
document is included in deterministic documentation readiness/link checks. It
does not change the helper's classification precedence or add compaction
behavior beyond explicit simulator helpers.

Sprint 5 adds detailed debug-snapshot visibility for scenario action results.
`World.detailed_snapshot()` exposes copied, deterministic decision summaries
at top-level `retained_audit_compaction_decisions`; compact
`world.snapshot()` remains unchanged.

Retained audit compaction policies and decisions are symbolic simulator-local
diagnostic metadata only. They describe how explicit retained audit records
would be classified for review under a caller-provided policy.

Sprint 1 classifies retained audit records but does not delete, compact,
mutate, rewrite, replace, schedule cleanup, or trigger delivery. The helper is
read-only and accepts explicit retained audit records plus an explicit policy.
It does not inspect or mutate `RegistryHub` histories by itself.

## Supported Record Families

Sprint 1 supports these retained stream-offer audit families:

- `stream_offer_lifecycle_explanation`
- `stream_offer_status_transition`

Unsupported retained-history families are ignored deterministically and
reported through ignored record keys. Rendezvous poll results, lane admission
decisions, encrypted delivery results, alias histories, authority histories,
quarantine histories, and conflict histories remain future work for broader
retained audit compaction classification.

## Policy Fields

`RetainedAuditCompactionPolicy` records:

- `policy_id`
- `hub_id`
- optional `history_types`
- optional `retain_reasons` and `compact_reasons`
- optional `retain_statuses` and `compact_statuses`
- optional `retain_sources` and `compact_sources`
- optional `max_records`
- optional JSON-safe `metadata`

`RetainedAuditCompactionDecision` records:

- `hub_id`
- `policy_id`
- `history_type`
- `retained_record_keys`
- `compaction_candidate_record_keys`
- `ignored_record_keys`
- grouped candidate counts by history type, reason, status, and source
- JSON-safe `metadata`

## Classification Rules

Classification is deterministic in the order records are provided.

- Unsupported records are ignored.
- Supported records from another hub are ignored.
- Supported records outside `policy.history_types` are ignored when that
  filter is set.
- Retain filters take precedence over compact filters when both match.
- Compact filters classify matching supported records as compaction candidates.
- Supported records that match neither retain nor compact filters are retained.
- When `max_records` is set, only the first retained records up to that cap
  remain retained; later otherwise-retained records become compaction
  candidates.

Record keys are stable sequence-style keys derived from explicit record order
and retained record fields. Lifecycle explanations use the existing v1.5
sequence key shape. Status transitions use a deterministic transition key with
the explicit sequence field when present.

## Non-Goals

Sprint 1 adds no background workers, retry loops, durable queues, live timers,
live clocks, live polling, network logs, compliance systems, firewall or DDoS
systems, privacy or anonymity guarantees, or production security
infrastructure.

Sprint 1 adds no delivery behavior, TrafficHub routing behavior, DNS,
networking, external service behavior, real cryptography, key generation,
private key storage, production E2EE, delivery enforcement, compact
`world.snapshot()` changes, scenario DSL actions, scenario DSL assertions, or
canonical identity rewrites.
