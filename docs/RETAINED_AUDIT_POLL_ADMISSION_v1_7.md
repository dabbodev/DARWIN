# Retained Audit Poll and Admission Expansion v1.7

Status: included in the v1.7.0 source-release snapshot as
`darwin-sim 1.7.0` behavior.

This specification extends the v1.6 retained-audit classifier, replay summary,
and explicit apply helper. It does not introduce a new storage model or an
automatic compaction process.

## Supported Histories and Ownership

The supported history-type order is:

1. `stream_offer_lifecycle_explanation`
2. `stream_offer_status_transition`
3. `rendezvous_poll_result`
4. `lane_admission_decision`

A rendezvous poll result belongs to the RegistryHub named by
`parent_hub_id`. A lane-admission decision belongs to the RegistryHub named by
`hub_id`. A missing owner or an owner different from the requested policy hub
is ignored deterministically. The original record is never rewritten.

## Deterministic Record Keys

Keys retain the existing index-prefixed convention and use explicit `none`
tokens for absent optional values:

```text
rendezvous_poll:{index}:{parent_hub_id}:{polling_hub_id}:{request_id}:{target_scope}:{visibility}:{status}:{reason}:{comma-joined-matched-offer-ids-or-none}

lane_admission:{index}:{hub-id-or-none}:{decision_id}:{policy-id-or-none}:{offer-id-or-none}:{request-id-or-none}:{status}:{reason}
```

Poll `matched_offer_ids` retain their recorded order inside the key. Existing
v1.6 lifecycle explanation and status-transition key shapes are unchanged.

## Classification

`classify_retained_audit_records_for_compaction(...)` applies the established
v1.6 rules in input order:

1. Ignore unsupported records, foreign/missing owners, and records excluded by
   an explicit history-type filter.
2. Apply retain filters before compact filters when both match.
3. Retain supported records that match neither filter.
4. When `max_records` is present, retain only the first otherwise-retained
   records up to the cap and classify later ones as candidates.

Classification is read-only. A mixed poll/admission record set can produce a
mixed decision for inspection, but that decision is not eligible for apply.

## Replay Summaries

`RetainedAuditReplaySummary` adds an optional trailing `by_request_id` mapping.
Its `to_summary()` representation copies and emits the mapping in sorted key
order, consistent with the other grouped counts.

- Poll results contribute request ID, status, reason, and metadata `source`.
- Admission decisions contribute request ID, status, reason, metadata
  `source`, and their optional `offer_id`.
- Poll `matched_offer_ids` do not contribute to `by_offer_id`.
- Target scopes are not grouped.
- Decision-category filtering remains read-only and reuses v1.6 record keys;
  it does not reclassify records.

## Explicit Apply

`apply_retained_audit_compaction_decision(...)` accepts the existing explicit
RegistryHub and decision inputs. An effective apply must select exactly one
supported history type. For v1.7 that selected history may be
`rendezvous_poll_result_history` or `lane_admission_decision_history`.

- Only current records whose generated keys are compaction candidates are
  removed.
- Remaining records preserve their original order.
- Candidate keys no longer present are reported as missing.
- Retained and ignored keys are reported only when currently present.
- Poll apply sets `polling_history_mutated` only when poll history changes.
- Admission apply sets `admission_history_mutated` only when admission history
  changes.
- A mixed or unsupported decision returns the existing deterministic
  unsupported/no-mutation result.

Apply never mutates the other retained history, held offers, delivery state,
TrafficHub routing, or canonical identity.

## Scenario and Snapshot Contract

The existing retained-audit DSL actions accept the two new history labels.
Replay-summary assertions can check request-ID counts. Scenarios `070` through
`072` cover mixed read-only classification, replay grouping and filtering,
and separate poll/admission apply isolation.

`World.detailed_snapshot()` reuses the existing top-level retained-audit
decision, replay-summary, and apply-result fields. Returned data is copied and
JSON-safe. Compact `world.snapshot()` remains unchanged.

## Non-Goals

This extension provides no automatic compaction, background workers, retries,
durable queues, live timers, live clocks, live polling, delivery enforcement,
networking, DNS, external services, real cryptography, production E2EE,
production compliance, or production data-retention guarantees. It does not
change delivery behavior, TrafficHub routing, compact snapshots, or canonical
identity.
