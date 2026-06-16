# DARWIN Mailbox Addressing v0.9

DARWIN v0.9 adds compact, simulator-local mailbox identity and address models
for future mailbox and chat adapter demos. These models describe addressable
mailbox records in the simulator only. They do not register mailboxes, bind
lanes, open adapters, deliver messages, contact external services, or define a
production networking protocol.

Sprint 4 adds RegistryHub-local mailbox registration and lane binding helpers
around these models. See `docs/MAILBOX_REGISTRY_v0_9.md`.

## Address Shape

A DARWIN mailbox address uses this compact simulator string form:

```text
darwin://global.chat.neo/inbox
```

The parser treats that example as:

- `scheme`: `darwin`
- `scope`: `global.chat`
- `mailbox`: `neo`
- `resource`: `inbox`

The split is deterministic: after the required `darwin://` prefix, the final
dot before the `/` separates the simulator scope from the local mailbox name.
The resource is a single non-empty segment after the `/`.

Mailbox addresses are not real URLs, DNS names, socket endpoints, public
identifiers, or transport routes. The simulator does not perform DNS lookup,
network resolution, registrar lookup, certificate validation, or public
identity proof when parsing them.

## Models

`DarwinMailboxAddress` stores the parsed address fields and returns a
JSON-safe summary with:

- `raw`
- `scheme`
- `scope`
- `mailbox`
- `resource`

`MailboxCapability` stores a simulator-local capability reference for a future
mailbox lane binding. Its `lane_signature` may reference Sprint 1 signatures
such as:

```text
basic_messaging:v1
```

This reference is descriptive only. It does not advertise, authorize, bind, or
resolve lane use.

`MailboxIdentity` stores a compact mailbox record with:

- `mailbox_id`
- `canonical_device_id`
- `local_name`
- `scope`
- `address`
- `capabilities`
- `metadata`

The `canonical_device_id` field links a mailbox record to stable simulator
identity without rewriting canonical device identity or changing RegistryHub
identity truth.

## Helpers

The mailbox helpers are pure and deterministic:

- `format_mailbox_address(scope, mailbox, resource="inbox")`
- `parse_mailbox_address(raw)`
- `is_mailbox_address(raw)`

They validate conservative address syntax and do not perform lookup,
registration, lane binding, authorization, or delivery.

## Relationship to Lane Signatures

Mailbox capabilities can reference lane signatures introduced in Sprint 1,
especially `basic_messaging:v1`. This gives later v0.9 work a stable way to
say a mailbox may support symbolic basic messaging in the simulator.

Sprint 3 adds scoped RegistryHub lane definition catalogs for signatures such
as `basic_messaging:v1`, documented in `docs/LANE_REGISTRY_v0_9.md`. Mailbox
capabilities can be bound to registered lane definitions by Sprint 4 mailbox
registry helpers, documented in `docs/MAILBOX_REGISTRY_v0_9.md`. They still do
not authorize lane use, create lane intent advertisements, attach adapter
endpoints, or deliver messages.

## Relationship to RegistryHub Registration

Sprint 4 adds RegistryHub-backed mailbox registration storage, direct mailbox
lookup, raw-address lookup, and strict capability binding to registered lane
definitions. Registration binds mailbox records to existing simulator identity
fields while preserving canonical identity truth.

Address parsing remains pure. Parsing a DARWIN mailbox address still does not
perform lookup, registration, authorization, alias resolution, or delivery.

## Relationship to Aliases

Existing aliases remain authorized shortcuts to durable simulator identity.
Future mailbox work may allow aliases to point toward or help resolve mailbox
records, but aliases should not replace canonical identity, bypass authority,
or become DNS records.

Sprint 2 does not change alias behavior, alias authority chains, retained
outcomes, audit traces, snapshots, or TrafficHub routing.

## Non-Goals

v0.9 mailbox addressing does not add:

- real networking;
- socket binding;
- HTTP or WebSocket clients or servers;
- DNS replacement behavior;
- registrar behavior;
- public CA behavior;
- production identity proof;
- production chat system behavior;
- message delivery;
- adapter endpoint records;
- production encryption or E2EE;
- external services.

Mailbox addresses remain deterministic simulator-local strings until future
work explicitly scopes additional behavior.
