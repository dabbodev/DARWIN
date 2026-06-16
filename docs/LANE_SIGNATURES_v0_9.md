# DARWIN Lane Signatures v0.9

DARWIN v0.9 introduces simulator-local lane signatures and lane intent
advertisements as the foundation for later mailbox and chat adapter demos.

A lane signature describes what a logical lane is for. A lane intent
advertisement says that a simulator identity, mailbox, device, or future
resource can receive or use that lane shape. Discovery is controlled by a
visibility tier, and lane use remains a separate authorization question.

Lane signatures are service-intent descriptors. They are not network ports,
socket bindings, DNS records, endpoint URLs, or cryptographic signatures.

Sprint 3 builds on these signatures with scoped RegistryHub lane definition
catalogs. See `docs/LANE_REGISTRY_v0_9.md` for the simulator-local catalog
records that describe available lane signatures in a scope.

Sprint 4 adds RegistryHub-local mailbox registration and capability binding
helpers. See `docs/MAILBOX_REGISTRY_v0_9.md`.

## Why Not Numeric Ports

DARWIN should model typed, authorized lane intent rather than open ports.
Numeric ports imply live network listeners and transport binding. v0.9 keeps
the model simulator-first by describing intent:

```text
basic_messaging:v1
```

That signature means a DARWIN-addressed mailbox can receive simple symbolic
message envelopes in a future simulator slice. It does not open a socket, bind
a port, publish a DNS record, or create a production messaging service.

## Lane Signature Fields

`LaneSignature` is a compact simulator-local model with these summary fields:

- `lane_id`: stable symbolic lane identifier, such as `basic_messaging`.
- `version`: lane intent version, such as `v1`.
- `signature`: compact `lane_id:version` string.
- `direction`: intended flow direction, such as `receive`.
- `payload_kind`: symbolic payload class, such as
  `symbolic_message_envelope`.
- `recipient_kind`: target kind, such as `mailbox`.
- `required_capability`: capability a future use authorization check may
  require, such as `basic_messaging`.
- `auth_policy`: lane-use policy hint, such as `authorization_required`.
- `adapter_kind`: simulator adapter family, such as `mailbox_adapter`.

Helpers:

- `format_lane_signature(lane_id, version)` returns `lane_id:version`.
- `parse_lane_signature(raw)` parses a compact signature string.
- `is_lane_signature(raw)` returns a boolean validation result.

## Lane Intent Advertisement Fields

`LaneIntentAdvertisement` describes that a simulator subject is advertising a
lane intent:

- `advertisement_id`: stable simulator-local advertisement ID.
- `subject_id`: device ID, mailbox ID, or future resource ID.
- `subject_kind`: subject type, such as `device`, `mailbox`, or `resource`.
- `lane_signature`: the advertised `LaneSignature`.
- `visibility_tier`: discovery tier from `0` through `5`.
- `scope`: simulator scope for local or trusted discovery checks.
- `authorized_observers`: explicit discovery allowlist for private or
  restricted advertisements.
- `metadata`: optional JSON-safe simulator metadata.

Advertisements do not register mailboxes, bind adapters, deliver messages, or
authorize use of a lane. They only describe discoverable lane intent.

## Visibility Tiers

Visibility controls who can discover that a lane intent exists. It does not
authorize sending, receiving, mailbox access, adapter use, or message delivery.

| Tier | Label | Discovery meaning |
| --- | --- | --- |
| `0` | `public` | Anyone can discover that the lane intent exists. |
| `1` | `local_scope` | Visible to requesters in the same simulator scope. |
| `2` | `authenticated` | Visible to requesters with authenticated simulator state. |
| `3` | `scoped_trusted` | Visible to requesters trusted for the advertised scope. |
| `4` | `delegated_trusted` | Visible through an approved delegated trust path. |
| `5` | `explicit_private` | Visible only to explicitly authorized observers. |

The helper `can_discover_lane_intent(advertisement, trust_context)` evaluates
only this discovery question. `filter_discoverable_lane_intents(...)` applies
the same check while preserving deterministic input ordering.

## Visibility Versus Authorization

Discovery and authorization are intentionally separate:

- Visibility means: can this requester see that the lane intent exists?
- Authorization means: can this requester actually use the lane?

For example, a tier `0` `basic_messaging:v1` advertisement may be publicly
discoverable while its signature still declares `auth_policy:
authorization_required`. A future mailbox delivery slice must still check lane
use authorization before any simulated delivery.

## Future Mailbox and Chat Adapter Work

Lane signatures give later v0.9 sprints a vocabulary for mailbox and chat
adapter models:

- mailbox address models can refer to `basic_messaging:v1`;
- mailbox registration can bind a mailbox capability to a registered lane
  definition;
- local adapter endpoint records can describe inert availability for that
  lane;
- scoped lane registries publish local lane definitions and fallback policy
  data before any delivery exists;
- in-memory delivery can later require both discovery and authorization before
  symbolic delivery.

This document does not define those later behaviors.

## Non-Goals

v0.9 lane signatures do not add:

- real networking;
- socket binding;
- HTTP or WebSocket clients or servers;
- DNS replacement behavior;
- registrar behavior;
- public CA behavior;
- production identity proof;
- production chat system behavior;
- message delivery;
- mailbox registration;
- production encryption or E2EE;
- external services.

Lane signatures remain deterministic, simulator-local data until future work
explicitly scopes additional behavior.
