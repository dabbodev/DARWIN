# DARWIN v1.3 Roadmap Draft: Rendezvous Lifecycle and Retained Stream-Offer Status Transitions

Status: planning draft only. v1.3 is unreleased. DARWIN v1.2.0 remains the
latest released version on `main` as `darwin-sim 1.2.0`. The annotated
`v1.2.0` tag and GitHub release exist:
https://github.com/dabbodev/DARWIN/releases/tag/v1.2.0. No package
publication was performed.

Recommended candidate theme: Rendezvous lifecycle and retained stream-offer
status transitions.

This roadmap is a seed for future planning. It does not lock implementation
scope, commit to a release date, or authorize feature work. Any later v1.3
sprint should remain simulator-first and symbolic unless explicitly scoped
otherwise.

v1.3 should not become production networking, a real DDoS protection system,
a firewall product, a privacy or anonymity system, DNS, registrar
infrastructure, external service discovery, a secure messaging protocol, or a
real cryptography project.

## Core Concept

Explore a small, simulator-local lifecycle layer for stream offers retained by
rendezvous and RegistryHub-local state.

v1.2 introduced stream offer records, held offer queues, private polling
descent helpers, symbolic lane admission policy, retained poll/admission
histories, scenarios, and detailed snapshot visibility. A possible v1.3 line
could focus on making retained stream-offer lifecycle movement easier to
inspect without changing delivery behavior, TrafficHub routing, canonical
identity, networking, or cryptography.

The primary planning question is:

```text
Can a retained stream offer move through explicit symbolic lifecycle states in
a deterministic, inspectable way without becoming delivery enforcement,
networking, durable queueing, or production security behavior?
```

## Planning Boundaries

Candidate in scope:

- Simulator-local stream-offer lifecycle status helpers.
- Symbolic expiration and cleanup helpers over retained offers.
- Retained stream-offer status transition history.
- Read-only query and summarize helpers for lifecycle audit metadata.
- Scenario DSL coverage only after helper behavior is stable.
- Documentation and release-readiness checks after scenario coverage exists.

Out of scope:

- Real networking, sockets, HTTP, WebSocket, DNS, or service discovery.
- Live polling loops, background workers, durable queues, retry services, or
  scheduler behavior.
- Production DDoS protection, firewall guarantees, abuse mitigation claims, or
  delivery guarantees.
- Privacy, anonymity, metadata-hiding, or traffic-analysis guarantees.
- Registrar integration, public CA behavior, or production identity proof.
- Real cryptography, key generation, private key storage, production E2EE, or
  secure messaging.
- TrafficHub routing changes.
- Canonical identity rewrites.
- Version bump beyond `1.2.0` during planning.
- Package publication.

## Candidate Concepts

Stream-offer lifecycle status:

- A simulator-local label describing where a retained offer sits in its
  explicit lifecycle.
- Possible future labels might describe held, discoverable, admitted,
  denied, expired, cleaned up, superseded, or withdrawn states.
- The exact vocabulary should be chosen during implementation planning, not
  locked by this roadmap draft.

Symbolic expiration:

- An explicit helper-level operation that marks or selects retained stream
  offers based on simulated time or scenario-provided metadata.
- It should not be a wall-clock timer, background worker, retry loop, durable
  queue, or live service.

Cleanup helper:

- A deterministic simulator helper that removes, marks, or summarizes retained
  offers according to explicit caller-provided criteria.
- It should not imply production retention policy, compliance deletion,
  guaranteed delivery cleanup, or external storage behavior.

Status transition history:

- Compact retained audit metadata for explicit stream-offer status changes.
- It should remain RegistryHub-local simulator state, not a production log or
  compliance audit trail.

Lifecycle audit query:

- Read-only filters and summaries over retained lifecycle metadata.
- Queries should preserve deterministic append order and expose only
  JSON-safe simulator summaries.

## Candidate Sprint 1: Lifecycle Status Planning and Pure Predicates

Status: draft candidate, not started.

Goal: define the smallest useful lifecycle vocabulary and pure predicates for
retained stream-offer state.

Possible work:

- Review existing `StreamOfferStatus` behavior and v1.2 retained offer helper
  boundaries.
- Identify the minimum lifecycle labels needed for later expiration, cleanup,
  and audit slices.
- Add pure status predicates only if they are needed by a later accepted
  implementation sprint.
- Keep construction, queueing, polling, admission, delivery, and routing
  behavior unchanged unless a later sprint explicitly scopes a helper change.

Acceptance targets for any future implementation:

- Existing v1.2 stream offer, poll, admission, history, snapshot, and scenario
  behavior remains unchanged unless explicitly documented.
- No real networking, DNS lookup, external services, delivery enforcement,
  TrafficHub routing changes, canonical identity rewrites, real cryptography,
  or version bump is added.

## Candidate Sprint 2: Symbolic Expiration and Cleanup Helpers

Status: draft candidate, not started.

Goal: explore explicit helper calls for symbolic stream-offer expiration and
cleanup.

Possible work:

- Add deterministic helper behavior for selecting retained stream offers that
  are expired under simulated-time or scenario metadata.
- Add an explicit cleanup operation if it proves useful after expiration
  semantics are clear.
- Preserve append-order summaries and JSON-safe output.
- Keep all behavior caller-driven and in-memory.

Acceptance targets for any future implementation:

- Expiration and cleanup are explicit simulator helper calls, not live timers,
  background workers, durable queues, or retry services.
- Helpers do not deliver messages, enforce production policy, mutate
  TrafficHub routes, perform DNS lookup, or contact external services.

## Candidate Sprint 3: Retained Status Transition History

Status: draft candidate, not started.

Goal: record compact, deterministic lifecycle transition metadata for
retained stream offers when explicit helper calls change status.

Possible work:

- Add a compact transition record shape if existing status summaries are not
  enough.
- Retain transition history on the relevant RegistryHub-local simulator state.
- Include previous status, next status, reason, offer ID, hub ID, simulated
  time or scenario timestamp when available, and JSON-safe metadata only if
  those fields are necessary.
- Preserve read-only defaults where helper behavior is meant to inspect rather
  than mutate state.

Acceptance targets for any future implementation:

- Transition history remains simulator audit metadata only.
- Retention does not become a production audit log, compliance store, delivery
  queue, or security guarantee.

## Candidate Sprint 4: Lifecycle Query and Summary Helpers

Status: draft candidate, not started.

Goal: make retained lifecycle audit metadata easy to inspect without changing
runtime behavior.

Possible work:

- Add read-only filters over retained transition history.
- Add compact summaries suitable for detailed snapshots or scenario
  assertions.
- Preserve deterministic ordering and stable JSON-safe output.
- Keep query helpers additive and non-mutating.

Acceptance targets for any future implementation:

- Queries are read-only and deterministic.
- Existing compact `world.snapshot()` behavior remains unchanged unless a
  later sprint explicitly scopes a compatible visibility update.

## Candidate Sprint 5: Scenario DSL Coverage

Status: draft candidate, not started.

Goal: expose stable lifecycle helpers through scenario YAML only after helper
behavior and summaries are covered by focused tests.

Possible work:

- Add scenario actions for explicit expiration, cleanup, or transition
  recording only if those helpers land.
- Add read-only assertions for retained lifecycle transition summaries.
- Add contiguous scenarios after `057` only when the behavior is stable.
- Update `docs/SCENARIO_INDEX.md` through the existing deterministic metadata
  path.

Acceptance targets for any future implementation:

- Existing scenarios `001` through `057` continue to pass unchanged.
- New scenarios remain symbolic and make no networking, delivery, DNS,
  cryptography, TrafficHub, or canonical identity claims.

## Candidate Sprint 6: Release-Readiness Docs and Hardening

Status: draft candidate, not started.

Goal: if v1.3 implementation slices are accepted and completed, harden tests,
scenario coverage, release notes, and documentation.

Possible work:

- Confirm Ruff, pytest, all-scenario, and CLI version checks.
- Update release notes from placeholder to implementation summary.
- Check README, changelog, checklist, scenario index, and docs for consistency.
- Keep the version bump deferred to explicit release prep.

Acceptance targets for any future implementation:

- Documentation clearly states v1.3 remains simulator-first and symbolic.
- Docs avoid production networking, DNS, registrar, public CA, external
  service, real cryptography, production E2EE, privacy, anonymity, firewall,
  DDoS, delivery, TrafficHub routing, and canonical identity claims.

## Recommended First Planning Step

Start by auditing v1.2 stream offer statuses and retained histories before
adding any feature code. The safest next decision is whether v1.3 needs a new
transition record shape or can reuse existing retained stream-offer and
admission/poll summaries.

## Intentionally Deferred Work

- Real networking, sockets, HTTP/WebSocket behavior, DNS lookup, and external
  services.
- Live polling, durable queues, retry workers, background cleanup services, or
  wall-clock schedulers.
- Production DDoS protection, firewall guarantees, abuse mitigation, or
  delivery guarantees.
- Privacy, anonymity, metadata-hiding, or traffic-analysis guarantees.
- Registrar integration, public CA behavior, and production identity proof.
- Real cryptography, key generation, private key storage, production E2EE, and
  secure messaging protocols.
- TrafficHub routing changes.
- Canonical identity rewrites.
- Package publication or version bump beyond `1.2.0` during planning.
