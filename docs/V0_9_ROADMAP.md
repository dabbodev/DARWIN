# DARWIN v0.9 Roadmap: Mailbox / Chat Adapter Foundations

DARWIN v0.9 planning starts from the released v0.8.0 simulator on `main`.
The planning branch is `v0.9/planning`. It is now unreleased release-prep work
for `darwin-sim 0.9.0`; v0.9.0 has not been merged, tagged, published as a
GitHub release, or published as a package.

Recommended theme: DARWIN Mailbox / Chat Adapter Foundations.

v0.9 should remain simulator-first. It should not become a production chat
system, secure messaging product, DNS replacement, registrar system, public
CA, real networking replacement, or production identity/compliance layer.

## Core Concept

Add typed, simulator-local lane intent foundations before mailbox delivery.
DARWIN should not model open ports. It should model lane signatures that
describe what a lane is for, plus authorized lane intent advertisements that
control who can discover those intents.

The release should then build toward DARWIN-addressed mailbox/chat adapter
models where lane discovery, mailbox registration, adapter binding, and
delivery explainability remain separate simulator concepts. Transport stays
local, in-memory, or adapter-mode only.

Discovery and authorization stay separate:

- visibility means "can this requester see that the lane exists?"
- authorization means "can this requester actually use the lane?"

v0.9 should preserve existing RegistryHub authority concepts without changing
canonical identity truth, TrafficHub routing, real DNS, external services, or
production cryptography.

## Release Boundaries

In scope:

- Simulator-local lane signature and lane intent advertisement models.
- Lane visibility tiers for discovery control.
- Pure lane intent discovery helpers.
- Scoped RegistryHub lane definition catalogs and fallback policy models.
- Simulator-local mailbox identity and resource models after lane intent
  foundations.
- DARWIN mailbox address strings, such as `darwin://global.chat.neo/inbox`.
- RegistryHub-backed mailbox registration and alias resolution helpers.
- Simulator-local adapter endpoint records.
- Toy in-memory message envelopes and delivery results.
- Scenario coverage for delivery success and explainable failure.
- Documentation that keeps adapter and transport behavior explicitly
  simulator-only.

Out of scope:

- Real networking, sockets, or external services.
- Production chat, secure messaging, or public mailbox service behavior.
- DNS replacement, registrar integration, or public CA behavior.
- Production identity proof, audit/compliance behavior, or production
  cryptography.
- TrafficHub routing changes.
- Canonical identity rewrites.
- Version bump beyond `0.9.0`.

## Sprint 1: Lane Signature and Lane Intent Discovery Models

Goal: define the smallest simulator-local lane intent vocabulary.

Candidate work:

- Add `LaneSignature` for compact typed lane intent, such as
  `basic_messaging:v1`.
- Add `LaneIntentAdvertisement` for simulator identities, devices, mailboxes,
  or future resources that can advertise a lane intent.
- Add a 0-5 `LaneVisibilityTier` model for discovery visibility.
- Add a simulator-local `LaneTrustContext` and pure discovery helpers.
- Keep lane signatures as service-intent descriptors, not ports, sockets,
  DNS records, endpoint URLs, or cryptographic signatures.
- Keep visibility and use authorization separate.
- Do not implement mailbox registration, adapter binding, message delivery,
  scenario DSL actions, or scenario assertions yet.

Acceptance targets:

- `basic_messaging:v1` formats and parses deterministically.
- Malformed lane signatures are rejected.
- Lane signature and lane intent advertisement summaries are JSON-safe.
- Visibility tiers `0` through `5` have deterministic discovery behavior.
- Discovery visibility does not imply lane-use authorization.
- Filtering discoverable advertisements preserves deterministic ordering.
- Docs clearly state that lane signatures are not network ports, socket
  bindings, DNS records, production service discovery, or cryptographic
  signatures.

## Sprint 2: Mailbox Identity and Address Models

Status: implemented on the v0.9 planning branch.

Goal: define the smallest simulator-local mailbox shape after lane intent
foundations exist.

Candidate work:

- Add simulator-local mailbox identity/resource models.
- Define a DARWIN mailbox address shape, such as
  `darwin://global.chat.neo/inbox`.
- Keep addresses as simulator strings, not real URLs or DNS records.
- Bind mailbox records to stable simulator identity fields without changing
  canonical device identity.
- Reference supported lane signatures without registering or delivering mail.
- Do not implement message delivery yet.

Acceptance targets:

- Mailbox addresses parse or validate deterministically as simulator strings.
- Mailbox records can be created in tests without opening sockets or using
  external services.
- Docs clearly state that mailbox addresses are not real URLs or DNS.

## Sprint 3: Scoped Lane Registry Definitions

Status: implemented on the v0.9 planning branch.

Goal: add scoped lane definition records and RegistryHub-local lane registry
catalog helpers before mailbox registration or delivery exists.

Candidate work:

- Add `LaneDefinition` records for lane signatures available in a simulator
  scope.
- Add `LaneDeliveryFallbackPolicy` data for future delivery planning outcomes.
- Add compact lane registry status values for local catalog lifecycle.
- Add an empty default `RegistryHub.lane_registry` catalog.
- Add helpers to register, retrieve, list, filter, and discover lane
  definitions.
- Add a deterministic `basic_messaging:v1` lane definition constructor.
- Keep visibility and use authorization separate.
- Do not implement mailbox registration, lane binding, adapter endpoints,
  message delivery, real networking, or scenario DSL changes yet.

Acceptance targets:

- `RegistryHub` construction remains backward compatible with an empty lane
  registry.
- Lane definitions and fallback policies return JSON-safe summaries.
- Registering a lane definition stores or replaces it deterministically by
  lane signature.
- Listing definitions is deterministic and supports visibility/status filters.
- Discovery uses the same tier `0` through `5` visibility semantics as lane
  intent advertisements.
- Discovery does not imply lane-use authorization.
- Docs clearly state that scoped lane registries are simulator-local catalogs,
  not DNS, service discovery, production protocol registries, registrars,
  public CAs, external services, or networking.

## Sprint 4: Mailbox Registration and Lane Binding

Status: implemented on the v0.9 planning branch for direct RegistryHub
mailbox registration and capability-to-lane-definition binding. Alias-to-mailbox
integration remains deferred.

Goal: register mailbox identities through existing RegistryHub concepts.

Candidate work:

- Register mailboxes against `RegistryHub`.
- Bind registered mailboxes to advertised lane signatures.
- Bind mailbox identity to device/canonical identity where appropriate.
- Preserve canonical identity truth.
- Keep aliases as authorized shortcuts without changing alias behavior in this
  sprint.
- Reuse existing alias conflict and authority language only when future
  alias-to-mailbox integration is explicitly scoped.

Acceptance targets:

- A mailbox can be registered under a RegistryHub scope.
- Registered mailboxes can be looked up by mailbox ID or raw DARWIN mailbox
  address.
- Mailbox listings are deterministic and can filter by scope, canonical device
  identity, or mailbox capability.
- Binding a mailbox capability requires the referenced lane definition to be
  registered first.
- Enabled mailbox capabilities can report lane support; disabled capabilities
  do not count as supported.
- Duplicate mailbox ID, duplicate address, and duplicate capability behavior
  remains deterministic and simulator-local.
- Canonical identity truth, alias behavior, TrafficHub routing, scenarios, and
  existing lane registry behavior remain unchanged.

## Sprint 5: Local Adapter Endpoint Records

Status: implemented on the v0.9 planning branch for simulator-local adapter
endpoint records and hub topology advertisements. Endpoint records remain
inert metadata and do not perform networking or delivery.

Goal: model how a mailbox might expose local adapter availability without
opening real transport.

Candidate work:

- Add simulator-local adapter endpoint models, such as `in_memory`,
  `loopback_placeholder`, or `websocket_placeholder`.
- Add hub topology advertisement records for future top-level hub and local
  hub planning metadata.
- Do not open real sockets.
- Do not resolve domains or host hints.
- Do not add external services.
- Model endpoint availability and stale endpoint behavior.
- Keep adapter records separate from TrafficHub routing.

Acceptance targets:

- Tests can mark an endpoint available, unavailable, or stale.
- Hub topology advertisements can describe future domain-shaped or local hub
  metadata without registering upstream or contacting external services.
- Future delivery planning can later explain unavailable or stale endpoint
  failures.
- Placeholder endpoint types remain inert data, not live transports.

## Sprint 6: In-Memory Message Delivery over `basic_messaging:v1`

Status: implemented on the v0.9 planning branch for toy, RegistryHub-local
message envelopes, retained delivery results, and in-memory inbox append
helpers. Sprint 7 adds scenario DSL support for this helper path.

Goal: add a toy delivery path that proves address resolution and adapter
selection without production transport.

Candidate work:

- Add toy message envelopes and in-memory mailbox delivery.
- Deliver by resolving a DARWIN mailbox address through RegistryHub.
- Keep payloads symbolic/plaintext for now.
- Return structured delivery outcomes.
- Do not add production encryption.

Acceptance targets:

- A message envelope can be delivered to an in-memory mailbox.
- Unresolved mailbox and unavailable adapter outcomes are explicit.
- Payloads are test fixtures only and are not described as secure messaging.
- Delivery results retain deterministic audit paths and can be filtered by
  message ID, recipient address, mailbox ID, status, reason, and lane
  signature.
- The helper remains simulator-local and does not perform networking, DNS
  lookup, TrafficHub routing, canonical identity mutation, background retries,
  durable queues, or production encryption.

## Sprint 7: Scenario DSL Message Delivery Coverage

Status: implemented on the v0.9 planning branch for simulator-local scenario
actions, assertions, and scenarios `044` through `046`. Release prep remains
deferred.

Goal: make delivery decisions explainable in scenario output without changing
the release version or crossing simulator-only boundaries.

Implemented work:

- Expose delivery result records in scenario output through scenario actions
  and detailed snapshots.
- Add scenario actions for lane definition registration, mailbox registration,
  mailbox capability binding, inert adapter endpoint registration, and toy
  message delivery.
- Add scenario assertions for registered mailboxes, mailbox lane support,
  retained delivery results, and in-memory inbox contents.
- Add scenarios for successful delivery, deterministic failure behavior, and
  fallback policy behavior.
- Keep simulator-only framing clear.
- Avoid production audit/compliance claims.
- Regression tests for mailbox registration, adapter records, delivery, and
  delivery explainability.
- Documentation polish and scenario index checks.

Acceptance targets:

- Ruff, pytest, scenario runner, and CLI version checks pass.
- Scenario assertions can validate delivery success and failure reasons.
- Delivery explainability shows address, registry resolution, adapter status,
  and terminal outcome.
- Scenario index coverage remains contiguous and discoverable.
- Scenario documentation distinguishes local adapter simulation from real
  networking.
- Release-facing docs state that v0.9 remains simulator-only.

Still deferred after release prep:

- Merge, tag, GitHub release, and package publication.

## Sprint 8: Hardening and Draft Release Notes

Status: implemented on the v0.9 planning branch. This is a hardening sprint,
not a feature sprint.

Goal: polish the mailbox/chat adapter foundations without changing runtime
semantics.

Candidate work:

- Audit v0.9 scenario action and assertion behavior for deterministic,
  JSON-safe results and read-only assertion semantics.
- Confirm mailbox delivery scenario actions use the existing simulator-local
  helper path and do not perform networking, DNS lookup, socket operations,
  external service calls, durable queueing, retry work, TrafficHub routing, or
  production chat behavior.
- Confirm detailed snapshots expose v0.9 RegistryHub state compactly while
  compact `world.snapshot()` output remains stable.
- Confirm scenarios `044` through `046` remain clear v0.9 draft scenarios and
  the scenario set remains contiguous from `001` through `046`.
- Add draft v0.9 release notes without marking v0.9 as released.
- Keep all non-goals explicit: no production chat, no production encryption or
  E2EE, no real networking, no DNS, no registrar integration, no public CA
  behavior, no production identity proof, no external services, no durable
  queues, no TrafficHub routing changes, no canonical identity rewrite, and no
  package publication.

## Release Prep

Status: completed release-prep work on `v0.9/planning` for
`darwin-sim 0.9.0`.

Release prep finalizes release-facing docs, keeps the checked-in scenario set
at `001` through `046`, and validates Ruff, pytest, the scenario runner,
scenario index output, and CLI version reporting. This release-prep step does
not add features, scenarios, scenario actions, scenario assertions, runtime
behavior, networking, production chat behavior, encryption, durable queueing,
TrafficHub routing changes, or canonical identity changes.

Merge, tag, GitHub release creation, and package publication remain deferred.

## Future Encryption Planning

v1.0 may model end-to-end encrypted mailbox delivery, but DARWIN should not
invent production cryptography.

Future work should evaluate established protocol patterns such as
Signal-style asynchronous messaging, MLS for groups, HPKE-style envelopes, or
Noise-style handshakes. v0.9 should not implement production encryption.

## Recommended First Implementation Sprint

Start with Sprint 1: lane signature and lane intent discovery models. It is
the smallest slice that creates a shared vocabulary for later mailbox address,
registration, adapter, and delivery work without changing simulator behavior
outside the new lane-intent surface.

## Intentionally Deferred Work

- Real networking and socket transport.
- Production chat service behavior.
- Production encryption or secure messaging guarantees.
- DNS replacement, registrar integration, or public CA behavior.
- Production identity proof.
- Production audit or compliance behavior.
- TrafficHub routing changes.
- Canonical identity rewrites.
- Package publication, tagging, or release creation during planning.
