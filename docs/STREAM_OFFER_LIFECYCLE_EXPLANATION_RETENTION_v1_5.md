# DARWIN v1.5 Stream Offer Lifecycle Explanation Retention

Sprint 1 adds read-only retention policy and classification metadata for
stream-offer lifecycle explanations. Retention policies and decisions are
symbolic simulator-local diagnostic metadata only. They make caller-provided
`StreamOfferLifecycleExplanation` records easier to classify for inspection
without changing retained explanation history, lifecycle planning, lifecycle
apply, delivery, routing, identity, networking, or cryptography behavior.

This feature does not add delivery behavior, TrafficHub routing, DNS,
networking, external services, real cryptography, or production security
behavior.

## Purpose

The retention policy model is:

```text
StreamOfferLifecycleExplanationRetentionPolicy
```

It contains:

- `policy_id`
- `hub_id`
- optional `retain_categories`
- optional `retain_reasons`
- optional `prune_categories`
- optional `prune_reasons`
- optional `retain_sources`
- optional `prune_sources`
- optional `max_records`
- optional JSON-safe `metadata`

The retention decision model is:

```text
StreamOfferLifecycleExplanationRetentionDecision
```

It contains:

- `hub_id`
- `policy_id`
- deterministic `kept_explanation_keys`
- deterministic `prune_candidate_explanation_keys`
- deterministic `ignored_explanation_keys`
- grouped `by_decision_category` counts
- optional JSON-safe `metadata`

Lifecycle explanations do not currently have durable explanation IDs. Sprint 1
therefore uses deterministic sequence-style keys derived from the explicit
input order and explanation fields:

```text
lifecycle_explanation:<index>:<hub_id>:<offer_id>:<category>:<reason>:<status>:<source>:<checked_at>
```

These keys are diagnostic identifiers for the returned decision only. They are
not durable database IDs, public record IDs, security audit IDs, or production
log identifiers.

## Helpers

Sprint 1 adds:

- `make_stream_offer_lifecycle_explanation_retention_policy(...)`
- `classify_stream_offer_lifecycle_explanations_for_retention(...)`
- `summarize_stream_offer_lifecycle_explanation_retention_decision(...)`

The classifier accepts explicit explanation records and an explicit retention
policy. It does not read or mutate a `RegistryHub` by itself. Callers that want
to classify retained history can pass a copy or tuple of
`registry_hub.stream_offer_lifecycle_explanation_history`.

`summarize_stream_offer_lifecycle_explanation_retention_decision(...)` returns
a copied JSON-safe summary. Mutating the summary does not mutate the decision,
the policy, explanation records, retained history, held offers, lifecycle
plans, apply results, transition history, or TrafficHub state.

## Detailed Snapshot Visibility

Sprint 5 exposes retention decision action results in detailed simulator
snapshots under the top-level
`stream_offer_lifecycle_retention_decisions` field. Entries use the existing
copied JSON-safe retention decision summary shape.

Compact `world.snapshot()` output remains unchanged and does not include
retention decision action results.

## Classification Rules

Classification is deterministic and input-order preserving.

Records whose `hub_id` does not match the policy `hub_id` are classified as
`ignored`.

For matching-hub records, retain filters are evaluated before prune filters:

- matching any retain category, reason, or source classifies the record as
  `kept`;
- otherwise, matching any prune category, reason, or source classifies the
  record as `prune_candidate`;
- otherwise, the record is `kept`.

If a retain filter and a prune filter both match, retain wins. This precedence
is recorded in decision metadata as:

```text
retain_filters_before_prune_filters
```

If `max_records` is set, it is applied after retain/prune filter precedence.
Only the first `max_records` otherwise kept matching-hub records remain
`kept`; later otherwise kept matching-hub records become
`prune_candidate` entries. Explicit prune candidates and ignored records do not
count against `max_records`.

## Read-Only Boundaries

Sprint 1 classifies lifecycle explanation records but does not delete, prune,
mutate, schedule cleanup, or trigger delivery.

Retention classification does not:

- mutate retained explanation history;
- mutate held offers;
- mutate lifecycle plans;
- mutate lifecycle apply results;
- mutate retained transition history;
- apply lifecycle plans;
- delete offers;
- delete explanation records;
- run cleanup;
- schedule retries;
- trigger delivery;
- create delivery results;
- change message inboxes;
- change TrafficHub routing;
- change compact `world.snapshot()` output.

The helpers do not read wall-clock time, use live clocks, start timers, poll in
the background, or require scenario context.

## Non-Goals

Sprint 1 does not add:

- background workers;
- automatic cleanup workers or cleanup daemons;
- retry loops;
- durable queues;
- live timers;
- live clocks;
- live polling;
- sockets;
- HTTP or WebSocket behavior;
- network logs;
- DNS lookup;
- registrar integration;
- public CA behavior;
- external services;
- firewall or DDoS systems;
- production privacy or anonymity guarantees;
- production security infrastructure;
- real cryptography;
- key generation;
- private key storage;
- encryption or decryption;
- production E2EE;
- delivery enforcement;
- mailbox delivery behavior changes;
- encrypted delivery behavior changes;
- TrafficHub routing changes;
- canonical identity rewrites;
- scenario DSL actions or assertions;
- compact snapshot changes;
- prune/apply mutation behavior;
- package publication;
- release assets;
- merge, tag, GitHub release, or version bump beyond `1.4.0`.
