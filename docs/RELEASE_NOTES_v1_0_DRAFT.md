# DARWIN v1.0.0 Draft Release Notes

Status: unreleased release-prep draft on `v1.0/planning`. The current package
and CLI version on this branch is `darwin-sim 1.0.0`. Do not treat v1.0.0 as
released until it is merged, tagged, and published as a GitHub release. No
package publication has been performed.

DARWIN v1.0 is scoped as symbolic encrypted mailbox model foundations. It
adds model, registry, policy, scenario, audit, and documentation coverage for
simulator-only encrypted mailbox concepts without implementing real
cryptography or changing v0.9 message delivery behavior.

## Release-Prep Highlights

- Symbolic encryption identity records for mailbox, device, and future
  resource subjects.
- Symbolic key bundle references that store public reference labels only and
  never store private key material.
- Mailbox encryption bindings that connect a mailbox to a symbolic encryption
  identity and key bundle reference.
- Symbolic encrypted envelope metadata and message wrappers that distinguish
  plaintext test messages from symbolic encrypted-envelope references.
- Mailbox encryption policy helpers for lane-specific symbolic requirements,
  plaintext fallback decisions, unsupported profiles, missing setup, inactive
  identities, unusable key bundles, and not-ready envelopes.
- RegistryHub-local encryption registries for encryption identities, key
  bundle references, mailbox encryption bindings, and mailbox encryption
  policies.
- Registered symbolic policy evaluation through
  `evaluate_registered_mailbox_encryption_policy(...)` without wiring policy
  decisions into message delivery.
- Retained symbolic encryption policy decision history on
  `RegistryHub.encryption_policy_decision_history`.
- Read-only retained policy decision query helper
  `query_encryption_policy_decisions(...)` with additive filters that preserve
  append order.
- Scenario DSL actions for symbolic encryption setup and registered policy
  evaluation:
  - `register_encryption_identity`
  - `register_key_bundle_reference`
  - `register_mailbox_encryption_binding`
  - `register_mailbox_encryption_policy`
  - `evaluate_mailbox_encryption_policy`
- Scenario assertions for symbolic encryption registry records and policy
  decisions:
  - `encryption_identity_registered`
  - `key_bundle_registered`
  - `mailbox_encryption_binding_registered`
  - `mailbox_encryption_policy_registered`
  - `encryption_policy_decision_contains`
- v1.0 release-prep scenarios `047` through `049` for symbolic encryption
  registry setup, successful required policy evaluation, and deterministic
  policy failure outcomes.
- Detailed snapshot visibility for RegistryHub encryption registries and
  retained encryption policy decision history. Compact `world.snapshot()`
  remains unchanged.
- Scenario index regression and release-candidate hardening for scenarios
  `001` through `049`.
- Tests and documentation hardening for JSON-safe summaries, deterministic
  predicates, missing cross-reference diagnostics, non-mutating policy
  evaluation, scenario validation, scenario index continuity, and simulator-only
  scope.

## Scenario Coverage

The current checked-in release-prep scenario set is `001` through `049`.

- `047_symbolic_encryption_registry.yaml`
- `048_symbolic_encryption_policy_required.yaml`
- `049_symbolic_encryption_policy_failures.yaml`

Scenarios `047` through `049` are v1.0 release-prep scenarios. They are
simulator-only and do not deliver messages, mutate inboxes, enforce encrypted
delivery, open sockets, perform DNS lookup, or import cryptographic libraries.

## Compatibility Notes

- v0.9 released scenarios `001` through `046` remain valid.
- v1.0 release-prep scenarios `047` through `049` run on `v1.0/planning`.
- The package and CLI version now report `darwin-sim 1.0.0` on this branch.
- TrafficHub routing and canonical identity behavior are unchanged.
- Existing plaintext mailbox delivery semantics are unchanged.
- v1.0.0 has not been merged, tagged, published as a GitHub release, or
  published as a package.

## Explicit Non-Goals

v1.0 release-prep symbolic encryption work does not add:

- real cryptography;
- key generation;
- private key storage;
- secret material;
- encryption or decryption;
- production E2EE;
- secure messenger behavior;
- crypto library integration;
- Signal, MLS, HPKE, or Noise implementation;
- delivery enforcement;
- production identity proof;
- networking;
- sockets;
- HTTP or WebSocket behavior;
- DNS lookup;
- external services;
- registrar integration;
- public CA behavior;
- durable queues or retry workers;
- TrafficHub routing changes;
- canonical identity rewrites;
- package publication.

## Release Readiness

This branch is prepared for v1.0.0 release review with the simulator version
bumped to `darwin-sim 1.0.0`, release-facing docs updated, and scenarios
`001` through `049` expected to pass. Merge, tag creation, GitHub release
publication, and package publication remain intentionally deferred.
