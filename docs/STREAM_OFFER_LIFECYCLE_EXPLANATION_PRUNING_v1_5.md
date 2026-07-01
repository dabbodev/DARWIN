# Stream Offer Lifecycle Explanation Pruning Plans v1.5

v1.5 Sprint 2 adds read-only pruning plan metadata for stream-offer lifecycle
explanations. A pruning plan identifies deterministic candidate keys from a
retention decision, but it does not delete, prune, mutate, schedule cleanup, or
trigger delivery.

v1.5 Sprint 3 adds an explicit opt-in apply helper. The apply helper is a
simulator-local mutation of retained explanation-history metadata only. It
removes currently retained records whose deterministic keys match pruning-plan
candidate keys, reports retained, ignored, pruned, and missing keys, and
preserves the order of all remaining retained explanation-history records.

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

Sprint 3 adds:

```text
StreamOfferLifecycleExplanationPruningApplyResult
```

It contains:

- `hub_id`
- `policy_id`
- deterministic `pruned_explanation_keys`
- deterministic `retained_explanation_keys`
- deterministic `ignored_explanation_keys`
- deterministic `missing_explanation_keys`
- `pruned_count`
- `retained_count`
- `ignored_count`
- `missing_count`
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

Sprint 3 adds:

- `apply_stream_offer_lifecycle_explanation_pruning_plan(...)`
- `summarize_stream_offer_lifecycle_explanation_pruning_apply_result(...)`

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

The apply helper requires an explicit `RegistryHub` and explicit
`StreamOfferLifecycleExplanationPruningPlan`. It only mutates
`registry_hub.stream_offer_lifecycle_explanation_history`. It does not require
scenario context, does not use live clocks, and does not run unless a caller
invokes it directly.

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

## Explicit Apply Rules

`apply_stream_offer_lifecycle_explanation_pruning_plan(...)` compares the plan's
candidate keys with the current retained explanation-history keys. Candidate
records that still exist in retained history are removed. Candidate keys that no
longer exist are reported as missing. Plan retained and ignored keys that still
exist are reported and preserved.

The helper preserves the relative order of every remaining explanation-history
record. It does not rewrite explanation records, create replacement records, or
recalculate plan decisions.

## Read-Only Boundaries

Sprint 2 identifies pruning candidates but does not delete, prune, mutate,
schedule cleanup, or trigger delivery. Sprint 3's apply helper is the only
mutation added here, and it is limited to explicit caller-driven edits to
retained lifecycle explanation history.

Pruning plans and pruning apply do not:

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

The Sprint 3 apply helper is not automatic cleanup, a worker, a retry loop, a
durable queue, a live timer, a delivery trigger, production retention
infrastructure, production privacy infrastructure, anonymity infrastructure,
firewall behavior, or DDoS protection. It provides no production privacy,
anonymity, firewall, or DDoS guarantees.
