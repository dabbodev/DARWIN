# DARWIN Scoped Lane Registries v0.9

Status: released in v0.9.0 on `main`; current package and CLI version is
`darwin-sim 0.9.0`.

DARWIN v0.9 Sprint 3 adds simulator-local scoped lane registries on
`RegistryHub`. A lane registry is a catalog of lane definitions that a hub can
publish for its own scope. It is not an external service, production protocol
registry, DNS system, registrar, public CA, or network discovery system.

Scoped lane registries keep the v0.9 direction centered on lane signatures
rather than numeric ports. They describe which lane shapes exist in a simulator
scope and how future delivery planning should treat common failure cases.

## Core Terms

A lane signature is the compact typed lane identifier, such as:

```text
basic_messaging:v1
```

A lane definition is a scoped catalog record for a lane signature. It can carry
a description, payload kind, schema reference, protocol reference, compatible
adapter kinds, visibility tier, authority scope, lifecycle status, fallback
policy, and JSON-safe simulator metadata.

A lane intent advertisement says that a subject, such as a future mailbox or
device resource, can expose a lane intent. Advertisements are about a subject's
intent, not the hub's scoped catalog.

A mailbox capability says that a mailbox record may support a lane signature.
Sprint 4 adds RegistryHub-local mailbox registration helpers that bind mailbox
capabilities to lane definitions already registered in this catalog. See
`docs/MAILBOX_REGISTRY_v0_9.md`.

## RegistryHub Catalogs

`RegistryHub` now has an empty `lane_registry` dictionary by default. The
registry key is the deterministic compact lane signature string.

The helper `register_lane_definition(registry_hub, lane_definition)` stores or
replaces a definition by that signature. This is simulator-local catalog
mutation only. It does not register a mailbox, bind a lane, authorize use,
open an adapter endpoint, deliver messages, or change `TrafficHub` routing.

Read helpers include:

- `get_lane_definition(registry_hub, lane_signature)`
- `list_lane_definitions(registry_hub, visibility_tier=None, status=None)`
- `list_discoverable_lane_definitions(registry_hub, trust_context)`

Listing is deterministic by lane signature.

## Lane Definition Fields

`LaneDefinition` summaries are JSON-safe and include:

- `lane_signature`
- `scope`
- `description`
- `payload_kind`
- `schema_ref`
- `protocol_ref`
- `visibility_tier`
- `authority_scope`
- `adapter_kinds`
- `status`
- `fallback_policy`
- `metadata`

The initial status vocabulary is compact: `draft`, `active`, `deprecated`, and
`disabled`.

## Basic Messaging Example

The helper `make_basic_messaging_lane_definition(scope, authority_scope=None)`
builds a deterministic definition for `basic_messaging:v1`.

Its default payload kind is `symbolic_message_envelope`, its adapter kind is
`mailbox_adapter`, and its lane-use policy remains
`authorization_required`. Public discoverability does not authorize actual
message delivery.

Example summary shape:

```json
{
  "lane_signature": "basic_messaging:v1",
  "scope": "global.chat",
  "description": "Simulator-local symbolic mailbox messaging lane.",
  "payload_kind": "symbolic_message_envelope",
  "schema_ref": "darwin://schemas/basic_messaging/v1",
  "protocol_ref": "darwin://protocols/basic_messaging/v1",
  "visibility_tier": 0,
  "authority_scope": "global.chat",
  "adapter_kinds": ["mailbox_adapter"],
  "status": "active"
}
```

## Delivery Fallback Policy

`LaneDeliveryFallbackPolicy` records conservative fallback actions for future
delivery planning. It is inert data in Sprint 3.

The default `basic_messaging:v1` policy is:

- unknown recipient: `bounce`
- stale device: `queue_with_expiry`
- in-transit device: `hold_until_relocation_resolves`
- quarantined identity: `reject`
- missing lane capability: `reject`
- adapter unavailable: `queue_with_retry`

Allowed actions are `reject`, `bounce`, `queue`, `queue_with_expiry`,
`hold_until_relocation_resolves`, `queue_with_retry`, and
`manual_resolution_required`.

These values describe how later simulator delivery work may explain outcomes.
They do not implement delivery, queues, retries, mailbox lookup, or adapter
availability checks yet.

## Visibility Versus Authorization

Lane definition visibility answers only this question: can a requester discover
that a lane definition exists in this scoped catalog?

The visibility tiers mirror lane intent discovery:

- tier `0`, public: anyone can discover the definition.
- tier `1`, local scope: requester scope must match the definition scope.
- tier `2`, authenticated: requester must have authenticated simulator state.
- tier `3`, scoped trust: requester must trust the definition scope.
- tier `4`, delegated trust: requester must have a delegated trust path.
- tier `5`, explicit private: requester must have explicit permission for the
  lane signature or scoped lane signature.

Authorization remains separate. A discoverable lane definition does not mean a
requester can use that lane, send to a mailbox, bind an adapter, or deliver a
message.

## Relationship to Future Work

Scoped lane registries give later v0.9 sprints a local catalog to reference.
Sprint 4 uses that catalog for strict mailbox capability binding. Sprint 5
adds inert adapter endpoint records and hub topology advertisements,
documented in `docs/ADAPTER_ENDPOINTS_v0_9.md`. Sprint 6 adds toy,
RegistryHub-local in-memory message delivery over registered mailbox, lane, and
endpoint records, documented in `docs/MESSAGE_DELIVERY_v0_9.md`. Sprint 7
adds scenario DSL coverage for registering lane definitions and asserting
delivery outcomes; see `docs/SCENARIO_DSL_v0_2.md` and scenarios `044`
through `046`.

Those later behaviors should continue to preserve canonical identity truth,
existing alias authority behavior, retained authority outcomes, audit traces,
snapshot behavior, and `TrafficHub` routing unless a future sprint explicitly
scopes a change.

## Non-Goals

Scoped lane registries do not add:

- real networking;
- socket binding;
- HTTP or WebSocket clients or servers;
- DNS replacement behavior;
- registrar behavior;
- public CA behavior;
- production identity proof;
- production chat system behavior;
- production message delivery;
- mailbox registration by themselves;
- mailbox lane binding by themselves;
- production encryption or E2EE;
- external services;
- production protocol registry behavior.

The lane registry remains deterministic, simulator-local catalog data until
future work explicitly scopes additional behavior.
