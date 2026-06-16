# DARWIN Mailbox Registry v0.9

DARWIN v0.9 Sprint 4 adds simulator-local mailbox registration and lane
binding helpers on `RegistryHub`. These helpers connect `MailboxIdentity`
records to a hub-local mailbox catalog and bind mailbox capabilities to lane
definitions already present in the hub's scoped lane registry.

Mailbox registration remains registry bookkeeping only. It is not account
creation, DNS, service discovery, registrar integration, production identity
proof, networking, adapter availability, or message delivery.

## RegistryHub Mailbox Storage

`RegistryHub` now has two empty dictionaries by default:

- `mailboxes`: maps `mailbox_id` to `MailboxIdentity`.
- `mailbox_address_index`: maps a raw DARWIN mailbox address string to
  `mailbox_id`.

The helper `register_mailbox(registry_hub, mailbox_identity)` stores or
replaces a mailbox by `mailbox_id`. If the same mailbox ID is registered with a
new address, the old address index entry is removed. If two mailbox IDs use the
same raw address, the address index resolves to the latest registered mailbox.
Both behaviors are deterministic and simulator-local.

Read helpers include:

- `get_mailbox(registry_hub, mailbox_id)`
- `resolve_mailbox_address(registry_hub, mailbox_address)`
- `list_mailboxes(registry_hub, scope=None, canonical_device_id=None,
  capability=None)`

Listing is deterministic by `mailbox_id`. The optional `capability` filter can
match a mailbox capability ID or lane signature string.

## Mailbox Identity Relationships

`MailboxIdentity` is still the mailbox record. It carries:

- `mailbox_id`: stable simulator-local mailbox record ID.
- `canonical_device_id`: the canonical simulator device identity that owns or
  backs the mailbox.
- `local_name` and `scope`: the fields used by the compact DARWIN mailbox
  address.
- `address`: a `DarwinMailboxAddress` such as
  `darwin://global.chat.neo/inbox`.
- `capabilities`: `MailboxCapability` records describing supported lane
  signatures.

The registry helpers do not rewrite canonical device identity, create aliases,
resolve aliases, or change RegistryHub authority truth.

## Lane Binding

Mailbox capabilities reference lane signatures such as:

```text
basic_messaging:v1
```

The helper `bind_mailbox_capability(registry_hub, mailbox_id, capability)`
requires the capability's lane signature to already exist in
`registry_hub.lane_registry`. This keeps lane definitions and mailbox support
separate: the hub first catalogs a lane definition, then a mailbox may bind a
capability for that registered lane.

Additional helpers:

- `mailbox_supports_lane(registry_hub, mailbox_id, lane_signature)` returns
  `True` only when the mailbox has an enabled capability for the lane.
- `list_mailbox_capabilities(registry_hub, mailbox_id)` returns capabilities in
  deterministic capability ID order.
- `make_basic_messaging_mailbox(...)` builds a mailbox identity with a
  `basic_messaging:v1` capability, but does not register it.

Duplicate capability binding is deterministic: binding a capability with the
same `capability_id` replaces the previous capability on that mailbox.

## Basic Messaging Example

```python
from darwin.models import RegistryHub, make_basic_messaging_lane_definition
from darwin.registry import (
    bind_mailbox_capability,
    make_basic_messaging_mailbox,
    register_lane_definition,
    register_mailbox,
)

hub = RegistryHub(hub_id="hub_chat_001", scope_path="global.chat")

register_lane_definition(
    hub,
    make_basic_messaging_lane_definition("global.chat"),
)

mailbox = make_basic_messaging_mailbox(
    mailbox_id="mailbox_neo",
    canonical_device_id="dev_A9F3",
    local_name="neo",
    scope="global.chat",
)
register_mailbox(hub, mailbox)

bind_mailbox_capability(
    hub,
    "mailbox_neo",
    mailbox.capabilities[0],
)
```

This example registers catalog and mailbox records only. It does not open an
adapter, authorize delivery, or send a message.

## Related Concepts

A lane definition is a scoped RegistryHub catalog record for a lane signature.
It says a lane shape exists in the simulator scope.

A mailbox capability is a mailbox-local support record for a lane signature.
It says the mailbox may support that lane once later authorization and delivery
layers exist.

A lane intent advertisement is a discoverable statement that a subject exposes
lane intent. It is separate from the hub's lane catalog and from mailbox
capability binding.

A future adapter endpoint may describe inert local adapter availability. Sprint
4 does not add adapter endpoint records.

Future delivery authorization may decide whether a requester can use a mailbox
lane. Sprint 4 lane support does not imply delivery authorization.

## Non-Goals

Mailbox registry helpers do not add:

- real networking;
- sockets;
- HTTP or WebSocket clients or servers;
- DNS replacement behavior;
- registrar behavior;
- public CA behavior;
- production identity proof;
- production chat system behavior;
- production encryption or E2EE;
- external services;
- adapter endpoint records;
- message delivery.

Mailbox registration and lane binding remain deterministic, simulator-local
RegistryHub bookkeeping until future work explicitly scopes additional
behavior.
