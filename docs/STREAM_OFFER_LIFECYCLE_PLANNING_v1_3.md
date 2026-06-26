# DARWIN v1.3 Stream Offer Lifecycle Planning and Apply

Sprint 2 adds deterministic, read-only planning helpers for retained
stream-offer expiration and cleanup candidates. Sprint 3 adds an explicit
opt-in apply helper for caller-provided lifecycle plans. The helpers are
symbolic simulator-local metadata and mutation only. They exist to make
explicit lifecycle planning and application inspectable in tests and docs
without changing runtime delivery behavior.

This feature does not add delivery behavior, TrafficHub routing, DNS,
networking, external services, real cryptography, or production security
behavior.

## Purpose

Held stream offers remain stored on:

```text
RegistryHub.held_stream_offers
```

Lifecycle planning returns immutable `StreamOfferLifecyclePlan` records. Plans
are not retained on the hub by default and do not mutate held offers,
transition history, message inboxes, delivery results, or TrafficHub state.

Each plan contains:

- `hub_id`
- `checked_at`
- `expired_offer_ids`
- `cleanup_candidate_offer_ids`
- `active_offer_ids`
- `ignored_offer_ids`
- JSON-safe `metadata`

Explicit apply calls return immutable `StreamOfferLifecycleApplyResult`
records containing:

- `hub_id`
- `plan_checked_at`
- `applied_offer_ids`
- `skipped_offer_ids`
- `missing_offer_ids`
- `recorded_transition_count`
- JSON-safe `metadata`

`checked_at` is an explicit simulator order supplied by the caller. The
helpers do not read wall-clock time, run timers, poll in the background, or
start cleanup services.

## Helpers

Sprint 2 adds:

- `query_expired_held_stream_offers(registry_hub, checked_at=...)`
- `plan_stream_offer_expiration(registry_hub, checked_at=..., metadata=None)`
- `summarize_stream_offer_lifecycle_plan(plan)`

Sprint 3 adds:

- `apply_stream_offer_lifecycle_plan(registry_hub, plan, ...)`
- `summarize_stream_offer_lifecycle_apply_result(result)`

`query_expired_held_stream_offers(...)` returns active held offers that are
expired at the explicit `checked_at` simulator order. It uses existing
stream-offer active and expiration predicates and preserves retained offer
append order.

`plan_stream_offer_expiration(...)` classifies retained held offers into a
read-only plan:

- active offers expired by `checked_at` are listed in `expired_offer_ids`;
- active offers not expired by `checked_at` are listed in `active_offer_ids`;
- terminal offers, including already-expired offers, are cleanup candidates
  but are not treated as fresh expiration targets;
- active expired offers are also cleanup candidates for later explicit
  caller-driven cleanup planning.

`summarize_stream_offer_lifecycle_plan(...)` returns copied JSON-safe plan
metadata. Mutating a summary does not mutate the plan or the hub.

`apply_stream_offer_lifecycle_plan(...)` is the only Sprint 3 mutation helper.
It requires an explicit caller-provided `StreamOfferLifecyclePlan`. It checks
the plan `hub_id` against the target `RegistryHub`, iterates only
`plan.expired_offer_ids`, reports missing offer IDs in plan order, skips
terminal or no-longer-expired offers, and marks eligible non-terminal expired
offers as `expired`.

Apply never deletes held offers and never runs automatically. It does not read
wall-clock time or live clocks; eligibility is rechecked against the explicit
`plan.checked_at` simulator order.

By default, apply records retained lifecycle transitions through the existing
status update helper with reason `expired`. Callers can pass
`record_transition=False` to update statuses without appending transition
history. In both modes, only eligible planned offers are mutated.

`summarize_stream_offer_lifecycle_apply_result(...)` returns copied JSON-safe
apply result metadata. Mutating a summary does not mutate the result or hub.

## Read-Only Default

Lifecycle planning is read-only by default:

- it does not remove retained stream offers;
- it does not update stream-offer statuses;
- it does not record status transitions;
- it does not create delivery results;
- it does not change message inboxes;
- it does not mutate TrafficHub routes;
- it does not change compact `world.snapshot()` output.

Lifecycle application is explicit and simulator-local:

- it only runs when `apply_stream_offer_lifecycle_plan(...)` is called;
- it only considers offer IDs listed in the provided plan;
- it leaves terminal offers unchanged;
- it reports missing offer IDs instead of creating offers;
- it does not remove retained held offers;
- it does not change compact `world.snapshot()` output.

No automatic cleanup worker, cleanup daemon, retry loop, durable queue, live
timer, live polling service, socket, HTTP/WebSocket behavior, DNS lookup,
registrar integration, public CA behavior, external service, real
cryptography, key generation, private key storage, delivery enforcement,
TrafficHub routing change, or canonical identity rewrite is added.

## Snapshot Visibility

Lifecycle plans and apply results are returned to callers and are not stored on
`RegistryHub` by default. Detailed snapshots expose copied action-result
summaries at top level for scenario/debug inspection:

```text
stream_offer_lifecycle_plans
stream_offer_lifecycle_apply_results
```

Detailed snapshots also continue to show retained stream offers and Sprint 1
transition history under each `RegistryHub`. Compact `world.snapshot()` output
remains unchanged.

## Non-Goals

Sprint 2 and Sprint 3 do not add:

- real networking;
- sockets;
- HTTP or WebSocket behavior;
- DNS lookup;
- registrar integration;
- public CA behavior;
- external services;
- cleanup workers or cleanup daemons;
- retry loops;
- background jobs;
- durable queues;
- clocks, timers, or live polling;
- network logs;
- production DDoS guarantees;
- production firewall guarantees;
- production privacy or anonymity guarantees;
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
- scenario DSL changes;
- package publication;
- version bumps beyond `1.3.0`.
