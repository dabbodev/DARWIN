# Stream Offer Lifecycle Explanation Pruning Plans v1.5

v1.5 Sprint 2 adds read-only pruning plan metadata for stream-offer lifecycle
explanations. A pruning plan identifies deterministic candidate keys from a
retention decision, but it does not delete, prune, mutate, schedule cleanup, or
trigger delivery.

Pruning plans are symbolic simulator-local diagnostic and planning metadata
only. They are not production retention enforcement, durable audit trails,
network logs, security evidence, privacy guarantees, anonymity guarantees, or
compliance records.

## Model

Sprint 2 adds:

```text
StreamOfferLifecycleExplanationPruningPlan
```

It contains:

- `hub_id`
- `policy_id`
- deterministic `candidate_explanation_keys`
- deterministic `retained_explanation_keys`
- deterministic `ignored_explanation_keys`
- `candidate_count`
- `retained_count`
- `ignored_count`
- grouped `by_decision_category` counts
- grouped candidate counts by category, reason, and source
- optional JSON-safe `metadata`

Lifecycle explanations still do not have durable explanation IDs. Pruning plans
reuse the deterministic sequence-style explanation keys produced by the Sprint
1 retention classifier:

```text
lifecycle_explanation:<index>:<hub_id>:<offer_id>:<category>:<reason>:<status>:<source>:<checked_at>
```

These keys identify records in the returned decision and plan only. They are
not database IDs, public record IDs, production log IDs, or security audit IDs.

## Helpers

Sprint 2 adds:

- `plan_stream_offer_lifecycle_explanation_pruning(...)`
- `summarize_stream_offer_lifecycle_explanation_pruning_plan(...)`
- `summarize_stream_offer_lifecycle_explanation_pruning_by_reason(...)`
- `summarize_stream_offer_lifecycle_explanation_pruning_by_category(...)`

The planning helper can accept an explicit
`StreamOfferLifecycleExplanationRetentionDecision`, or it can accept explicit
`StreamOfferLifecycleExplanation` records plus a
`StreamOfferLifecycleExplanationRetentionPolicy` and run the Sprint 1
classifier internally.

The helper does not read or mutate a `RegistryHub` by itself. Callers that want
to plan against retained history can pass a tuple or copied list of
`registry_hub.stream_offer_lifecycle_explanation_history`.

Summary helpers return copied JSON-safe metadata. Mutating a returned summary
does not mutate the plan, retention decision, policy, lifecycle explanation
records, retained history, held offers, lifecycle plans, apply results,
transition history, TrafficHub state, or compact snapshots.

## Planning Rules

Pruning plans preserve Sprint 1 retention classification semantics:

- hub mismatches remain `ignored`;
- retain filters beat prune filters;
- otherwise matching prune filters classify `prune_candidate`;
- otherwise matching-hub records remain `kept`;
- `max_records` is applied after filter precedence in deterministic input
  order.

The pruning plan maps Sprint 1 decision buckets into plan terminology:

- `prune_candidate_explanation_keys` become `candidate_explanation_keys`;
- `kept_explanation_keys` become `retained_explanation_keys`;
- `ignored_explanation_keys` remain `ignored_explanation_keys`.

Grouped pruning summaries count candidate records only. If the helper receives
only an explicit decision and no explanation records, key lists and counts are
still deterministic, and grouped candidate counts are empty.

## Read-Only Boundaries

Sprint 2 identifies pruning candidates but does not delete, prune, mutate,
schedule cleanup, or trigger delivery.

Pruning plans do not:

- mutate retained explanation history;
- mutate held offers;
- mutate lifecycle plans;
- mutate lifecycle apply results;
- mutate retained transition history;
- apply lifecycle plans;
- delete offers;
- delete explanation records;
- rewrite explanation records;
- run automatic cleanup workers;
- run retry loops;
- create durable queues;
- use live timers, live clocks, live polling, sockets, HTTP, or WebSockets;
- add network logs;
- add firewall or DDoS systems;
- add privacy or anonymity guarantees;
- add production security infrastructure;
- change delivery behavior;
- change TrafficHub routing;
- perform DNS lookups;
- integrate with registrars, public CAs, or external services;
- add real cryptography, production E2EE, key generation, or private key
  storage;
- rewrite canonical identities;
- change compact `world.snapshot()` output;
- add scenario DSL actions or assertions.

Future prune/apply behavior, if ever added, must be explicit caller-driven work
in a later sprint. Sprint 2 is planning metadata only.
