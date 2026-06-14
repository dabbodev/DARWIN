# DARWIN Mailbox Addressing v0.9

DARWIN v0.9 adds compact, simulator-local mailbox identity and address models
for future mailbox and chat adapter demos. These models describe addressable
mailbox records in the simulator only. They do not register mailboxes, bind
lanes, open adapters, deliver messages, contact external services, or define a
production networking protocol.

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
capabilities still do not register mailboxes, bind lanes, authorize lane use,
create lane intent advertisements, or attach adapter endpoints. Those remain
future slices.

## Relationship to Future RegistryHub Registration

Future v0.9 work may add RegistryHub-backed mailbox registration. That future
registration should bind mailbox records to existing simulator identity and
authority concepts while preserving canonical identity truth.

Sprint 2 intentionally stops at data models and pure address helpers. It does
not add RegistryHub storage, registration helpers, mailbox lookup, mailbox
conflict handling, or lane binding.

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
- mailbox registration;
- lane binding;
- adapter endpoint records;
- production encryption or E2EE;
- external services.

Mailbox addresses remain deterministic simulator-local strings until future
work explicitly scopes additional behavior.
