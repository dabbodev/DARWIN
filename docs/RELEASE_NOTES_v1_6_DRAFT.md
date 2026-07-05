# DARWIN v1.6 Draft Release Notes

Status: planning draft only. v1.6 is unreleased, release prep has not started,
and no v1.6 implementation scope is locked in. The latest released version
remains `darwin-sim 1.5.0` on `main` with the annotated `v1.5.0` tag and
GitHub release:
https://github.com/dabbodev/DARWIN/releases/tag/v1.5.0. No package
publication was performed for v1.5.0, and no release assets were uploaded.

This placeholder is a planning seed only. It must not be treated as release
prep, a version bump, a changelog release entry, a package publication plan, a
GitHub release plan, or authorization to implement feature behavior.

This release line, if implemented later, should remain symbolic simulator
metadata flow only. It must not become real networking, a network service,
production DDoS protection, a firewall, a privacy or anonymity system, DNS, an
external service, real cryptography, production E2EE, a delivery enforcement
layer, a TrafficHub routing change, or a background cleanup system.

## Draft Release Theme

Retained audit compaction and replay summaries.

Potential v1.6 work may explore:

- Read-only audit compaction policy models for retained simulator histories.
- Deterministic compaction-plan helpers that summarize candidates without
  deleting or rewriting retained histories by default.
- Grouped replay-summary helpers for retained lifecycle, poll/admission,
  encrypted delivery, alias, or authority audit histories.
- Explicit opt-in compaction/apply helper only after read-only planning
  helpers stabilize.
- Scenario DSL coverage after helper and model slices land.
- Detailed snapshot visibility only after retained data/action results exist.
- Release-readiness documentation after scenario coverage.

## Compatibility Target

Any future v1.6 implementation should preserve these compatibility
expectations unless a later sprint explicitly and narrowly says otherwise:

- Existing mailbox delivery behavior remains unchanged.
- Existing encrypted delivery behavior remains unchanged.
- Existing TrafficHub routing behavior remains unchanged.
- Existing alias, identity, stream-offer polling/admission, lifecycle
  planning, lifecycle apply, retained-history, explanation, audit summary,
  snapshot, and scenario behavior remains unchanged outside explicitly scoped
  v1.6 planning/helper surfaces.
- Compact `world.snapshot()` output remains unchanged.
- The checked-in scenario set remains contiguous from `001` through `066`
  until future scenario coverage is intentionally added.
- The package and CLI version continue to report `darwin-sim 1.5.0` during
  planning.

## Draft Sprint Placeholder

No v1.6 sprint has been implemented by this placeholder.

Candidate sequencing, if accepted later, should start with read-only policy
models, then read-only compaction plans, then grouped replay summaries. Any
explicit apply helper should be considered only after read-only semantics are
stable and should remain caller-driven, simulator-local, and narrowly scoped.
Scenario coverage, detailed snapshot visibility, and release-readiness docs
should follow only after helper behavior exists.

## Scenario Coverage

No v1.6 scenarios are added by this planning placeholder.

The current released scenario set remains contiguous from `001` through
`066`, and v1.5.0 reports package and CLI version `darwin-sim 1.5.0`.

## Current Limitations

- v1.6 is unreleased planning only.
- No v1.6 helper, scenario, snapshot, release, or version behavior has been
  implemented by this placeholder.
- No package publication or release asset upload is planned by this document.
- The package and CLI version remain `darwin-sim 1.5.0`.

## Non-Goals

v1.6 planning does not add:

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
- version bumps beyond `1.5.0` during planning.

## Release Readiness

Release readiness has not started for v1.6. This placeholder only records
candidate planning themes and boundaries. Final release validation, changelog
updates, version bumps, merge, tag, GitHub release, release assets, and
package publication remain out of scope until explicitly requested later.
