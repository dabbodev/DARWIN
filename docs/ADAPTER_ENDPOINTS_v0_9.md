# DARWIN Adapter Endpoint Records v0.9

Status: released in v0.9.0 on `main`; current package and CLI version is
`darwin-sim 0.9.0`.

DARWIN v0.9 Sprint 5 adds simulator-local adapter endpoint and hub topology
advertisement records. These records describe adapter-shaped availability that
future mailbox delivery planning can reference, but they remain inert
RegistryHub bookkeeping only.

Adapter endpoint records are not live listeners, socket bindings, DNS records,
service discovery protocols, deployment automation, or production
infrastructure.

## Adapter Endpoint Records

`AdapterEndpoint` describes a subject's simulator-local adapter-shaped
availability. A subject can be a mailbox, RegistryHub, TrafficHub, device, or
future resource.

Endpoint summaries are JSON-safe and include:

- `endpoint_id`
- `subject_id`
- `subject_kind`
- `adapter_kind`
- `status`
- `lane_signatures`
- `scope`
- `host_hint`
- `port_hint`
- `path_hint`
- `metadata`

Supported adapter kinds are compact descriptors:

- `in_memory`
- `loopback_placeholder`
- `websocket_placeholder`
- `domain_hint`
- `ipv4_placeholder`
- `ipv6_placeholder`

Supported endpoint statuses are:

- `available`
- `stale`
- `in_transit`
- `disabled`
- `unknown`

These values are simulator data. A `websocket_placeholder` endpoint does not
start a WebSocket client or server. A `domain_hint` does not resolve a domain.
An IPv4 or IPv6 placeholder does not bind or connect to an address.

## Hub Topology Advertisements

`HubTopologyAdvertisement` represents future "this hub can be reached through
this adapter-shaped endpoint" metadata. It supports planning for top-level hub,
local hub, and deployment-shaped demos without implementing hub-to-hub
networking.

Topology advertisement summaries are JSON-safe and include:

- `advertisement_id`
- `hub_id`
- `hub_kind`
- `scope`
- `parent_hub_id`
- `endpoint_id`
- `adapter_kind`
- `host_hint`
- `visibility_tier`
- `status`
- `metadata`

Visibility remains discovery metadata only. It does not authorize mailbox lane
use, delivery, registration with a parent hub, or real network access.

## RegistryHub Storage and Helpers

`RegistryHub` now has two empty dictionaries by default:

- `adapter_endpoints`: maps `endpoint_id` to `AdapterEndpoint`.
- `hub_topology_advertisements`: maps `advertisement_id` to
  `HubTopologyAdvertisement`.

Endpoint helpers:

- `register_adapter_endpoint(registry_hub, endpoint)`
- `get_adapter_endpoint(registry_hub, endpoint_id)`
- `list_adapter_endpoints(...)`

Topology helpers:

- `register_hub_topology_advertisement(registry_hub, advertisement)`
- `get_hub_topology_advertisement(registry_hub, advertisement_id)`
- `list_hub_topology_advertisements(...)`

Registering the same endpoint ID or advertisement ID replaces the previous
record deterministically. Listing is sorted by the stored ID and filters are
additive.

## Domain, Host, Port, and Path Hints

`host_hint`, `port_hint`, and `path_hint` are descriptive only.

They can help future demos show deployment-shaped topology, such as a
top-level combined registration/logic hub advertised with a normal-looking
domain for human convenience while local Registry Hubs register upstream in the
simulator. Sprint 5 models this only as endpoint and topology metadata.

DARWIN does not perform DNS lookup, registrar lookup, certificate validation,
socket binding, socket connection, HTTP requests, WebSocket negotiation, or
external service calls when these hints are created, registered, listed, or
summarized.

## Examples

Future top-level hub advertisement with a domain hint:

```python
from darwin.models import HubTopologyAdvertisement

advertisement = HubTopologyAdvertisement(
    advertisement_id="topology_global_demo",
    hub_id="hub_global_demo",
    hub_kind="registry_hub",
    scope="global",
    parent_hub_id=None,
    endpoint_id="endpoint_global_demo",
    adapter_kind="domain_hint",
    host_hint="darwin-demo.example.test",
    visibility_tier=0,
    status="available",
    metadata={"simulator_local": True, "hint_only": True},
)
```

Local hub advertisement under that future top-level hub:

```python
from darwin.models import HubTopologyAdvertisement

advertisement = HubTopologyAdvertisement(
    advertisement_id="topology_local_chat",
    hub_id="hub_chat_001",
    hub_kind="registry_hub",
    scope="global.chat",
    parent_hub_id="hub_global_demo",
    endpoint_id="endpoint_chat_local",
    adapter_kind="loopback_placeholder",
    host_hint="local-chat-hub",
    visibility_tier=1,
    status="available",
    metadata={"simulator_local": True},
)
```

Both examples construct records only. They do not register with an upstream
service, open transport, or deliver messages.

## Relationship to Mailboxes and Lanes

Mailbox registration remains separate from endpoint registration. An
`AdapterEndpoint` can reference `basic_messaging:v1`, but that does not create
a mailbox, bind a mailbox capability, authorize lane use, select an adapter,
or deliver a message.

Lane registries remain scoped catalogs of lane definitions. Endpoint records
may reference lane signatures, but Sprint 5 does not require the lane to be
registered and does not change lane registry behavior.

Future message delivery may use endpoint status and topology advertisements to
explain adapter availability or stale endpoints. Sprint 6 adds toy,
RegistryHub-local in-memory delivery results and inbox append behavior,
documented in `docs/MESSAGE_DELIVERY_v0_9.md`. Endpoint records still do not
open transports, contact hosts, authorize lane use by themselves, or create
durable queues. Sprint 7 adds scenario DSL actions and assertions that can
register inert endpoints and assert delivery outcomes; see
`docs/SCENARIO_DSL_v0_2.md` and scenarios `044` through `046`.

## Non-Goals

Adapter endpoint records do not add:

- real networking;
- sockets;
- DNS lookup;
- DNS replacement behavior;
- registrar behavior;
- public CA behavior;
- production identity proof;
- production chat system behavior;
- production encryption or E2EE;
- external services;
- production message delivery;
- message queues;
- TrafficHub routing changes;
- live scenario transports.

Endpoint and topology records remain deterministic, simulator-local
RegistryHub bookkeeping until future work explicitly scopes additional
behavior.
