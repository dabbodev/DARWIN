# DARWIN Design Dossier v0.1

**Project name:** DARWIN\
**Acronym:** Direct-Access Registration Window Interface Network\
**Document status:** Concept draft / thought-experiment preservation\
**Purpose:** Capture the core architecture, terminology, flows, and open design questions for a recursive identity-aware network registration and routing model.

---

## 1. Executive Summary

DARWIN is a proposed network architecture where devices do not rely solely on fragile address/location bindings. Instead, each device receives a durable identity, registers through scoped Registry Hubs, routes traffic through Traffic Hubs, and can move between branches of the network while preserving identity and potentially maintaining active logical connections.

The system is based on hierarchical dot-separated paths such as:

```text
globalrouter1.systemrouter1.homerouter1.my_pc
```

These paths behave like scoped identity chains. A device name only needs to be unique inside its local scope, while the full path disambiguates it globally.

DARWIN separates identity, registration, traffic movement, and authorization into related but distinct layers:

```text
Device Identity      = who the device is
Registry Path        = where the device is logically registered
Traffic Path         = how packets currently reach it
Agreement Passport   = proof that the device is authorized to exist in the network
Move Contract        = signed proof that the device changed attachment points
Checkpoint Packets   = lightweight state signals for liveness and relocation
Logical Lane         = persistent connection state between devices
```

The goal is a network model where names are persistent, movement is explicit, and routing can adapt without constantly breaking identity.

---

## 2. Core Premise

DARWIN uses recursive scoped registration.

Each device registers to the hub above it in the network tree. That hub may itself register upward, eventually forming a chain of logical identity:

```text
global.family.david.devices.my_pc
```

The same local name can exist in multiple scopes without conflict:

```text
global.family.david.home.printer
global.family.david.office.printer
global.company.lab.printer
```

This gives DARWIN the same broad structural pattern as filesystems, DNS, tag namespaces, and dot-separated configuration paths:

```text
root.branch.leaf
```

The path acts as:

- a location in a namespace
- a scoped identity
- a query handle
- a place where rules or permissions can attach
- a reference point for traversal

---

## 3. Design Goals

DARWIN is designed around these goals:

1. **Persistent device identity**\
   A device should remain the same actor even when it moves between hubs or networks.

2. **Scoped name reuse**\
   Names should only need to be unique within a local scope, not globally.

3. **Separation of logical identity and traffic routing**\
   The name of a device and the route used to reach it should not have to be the same thing.

4. **Recursive registration**\
   Hubs should hand up enough information to allow higher-level reconciliation without forcing every hub to know the entire network.

5. **Mobility-aware connections**\
   A moving device should be able to enter an explicit in-transit state rather than simply disappearing.

6. **Passport-based access control**\
   Devices without an approved identity certificate can be rejected, quarantined, or limited.

7. **Economical transport**\
   The network should move the minimum necessary identity and routing information needed to maintain continuity.

8. **Adaptive scaling**\
   The network should be able to detect pressure points and determine when new physical or logical branches are needed.

---

## 4. Major Entities

### 4.1 Device

A network participant with a durable identity.

A device has:

```text
device_id       = durable identifier, preferably cryptographic
device_label    = human-readable local name
passport        = first registration certificate
current_hub     = current Registry Hub or Traffic Hub attachment
state           = online, offline, in_transit, quarantined, etc.
```

Example:

```yaml
device:
  device_id: dev_A9F3
  device_label: my_pc
  current_registry_scope: global.family.david.devices
  current_state: online
```

---

### 4.2 Device ID

The durable identifier for a device.

The device ID should not depend on:

- current IP address
- current physical location
- current parent hub
- current display name

A device ID should ideally be tied to a cryptographic keypair so the device can prove it controls its identity.

---

### 4.3 Device Label

A human-friendly name such as:

```text
my_pc
printer
phone
livingroom_sensor
```

Labels are local to a scope. Two devices can have the same label if they exist under different parents.

If two devices with the same desired label appear under the same hub, the hub assigns a temporary conflict label:

```text
my_pc
my_pc_temp_B2C8
printer_temp_91AF
```

The underlying device identity remains stable even if the display label is temporarily changed.

---

### 4.4 Registry Hub

A Registry Hub manages identity, naming, device registration, and scoped namespace membership.

A Registry Hub answers:

```text
Who is this device?
What name does it have in this scope?
Where is this identity currently registered?
Is this device allowed here?
```

Registry Hubs maintain mappings like:

```text
device_id → canonical_identity_chain
device_id → current_attachment
device_label → local_device_id
```

Example:

```yaml
registry_hub:
  hub_id: hub_home_001
  scope: global.family.david.home
  children:
    my_pc: dev_A9F3
    printer: dev_B2C8
  upward_summary:
    dev_A9F3: global.family.david.home.my_pc
    dev_B2C8: global.family.david.home.printer
```

---

### 4.5 Traffic Hub

A Traffic Hub moves data. It does not necessarily own or define identity.

A Traffic Hub answers:

```text
How do packets reach this device right now?
What is the shortest viable route from A to B?
Should this lane be paused, rerouted, resumed, or terminated?
```

Traffic Hubs maintain routing information such as:

```text
device_id → current link
device_id → next hop
lane_id → current route
```

---

### 4.6 Hybrid Hub

Some hubs can act as both Registry Hubs and Traffic Hubs.

A home router might be a hybrid hub:

```text
Registry role: manages local names such as my_pc, printer, phone
Traffic role: forwards traffic between LAN devices and upstream networks
```

DARWIN allows Registry and Traffic functions to overlap without requiring them to always be the same thing.

---

### 4.7 Agreement Certificate / Passport

The first registration of a device creates an agreement certificate, also called a passport.

This certificate proves:

```text
This device exists.
This device owns this device_id.
This Registry Hub approved the device into a scope.
The device and Registry Hub both agreed to the registration.
```

Example:

```yaml
agreement_certificate:
  certificate_id: cert_123
  device_id: dev_A9F3
  canonical_label: my_pc
  registry_scope: global.family.david.devices
  issued_by: hub_david_devices_001
  issued_at: 2026-05-26T12:00:00Z
  device_public_key: DEVICE_PUBLIC_KEY
  registry_public_key: REGISTRY_PUBLIC_KEY
  permissions:
    can_move: true
    can_rename: with_registry_approval
    can_host_services: false
  signatures:
    device: DEVICE_SIGNATURE
    registry_hub: REGISTRY_SIGNATURE
```

The passport becomes the root identity document for future moves.

---

### 4.8 Move Contract

A Move Contract records a device changing registration or attachment points.

It references the original agreement certificate, like a passport stamp.

Example:

```yaml
move_contract:
  move_id: move_456
  certificate_id: cert_123
  device_id: dev_A9F3
  from_scope: global.family.david.home
  to_scope: global.family.david.office
  old_attachment: home_router.my_pc
  new_attachment: office_router.my_pc
  timestamp: 2026-05-26T12:05:00Z
  nonce: 918273
  signatures:
    device: DEVICE_SIGNATURE
    new_registry_hub: NEW_HUB_SIGNATURE
    old_registry_hub: OPTIONAL_OLD_HUB_SIGNATURE
```

A valid Move Contract prevents a malicious hub from simply claiming:

```text
This device is mine now.
```

The device must prove it controls the identity tied to the passport.

---

### 4.9 Parent Attestation

A Parent Attestation is a short-lived statement from a hub saying that a child device is currently attached to it.

Example:

```yaml
parent_attestation:
  attestation_id: attest_789
  child_device_id: dev_A9F3
  parent_hub_id: hub_home_001
  scope: global.family.david.home
  valid_from: 2026-05-26T12:00:00Z
  valid_until: 2026-05-26T12:10:00Z
  session_pubkey: SESSION_PUBLIC_KEY
  signature:
    parent_hub: PARENT_SIGNATURE
```

This helps prevent a device from secretly hiding behind another device and pretending to be a parent or authorized relay.

---

### 4.10 Logical Lane

A Logical Lane is a persistent connection relationship between devices, tied to identity rather than only to address.

A lane may survive movement if the device can re-register and prove continuity.

Example:

```yaml
lane:
  lane_id: lane_S991
  source_device: dev_A9F3
  target_device: dev_B2C8
  state: active
  current_route:
    - hub_home_001
    - hub_regional_003
    - hub_office_007
  last_confirmed_packet: 1042
```

Lane states might include:

```text
active
paused_relocation
awaiting_verification
rerouting
resumed
terminated
conflict_detected
```

---

## 5. Addressing and Namespaces

DARWIN uses dot-separated identity chains.

Example:

```text
global.family.david.home.my_pc
```

Each segment is meaningful only relative to the segment before it.

```text
my_pc
```

can exist under many parents:

```text
global.family.david.home.my_pc
global.family.david.office.my_pc
global.company.lab.my_pc
```

The full chain disambiguates the identity path.

---

## 6. Logical Path vs Traffic Path

DARWIN differentiates between a **Registry Path** and a **Traffic Path**.

A Registry Path describes logical identity:

```text
global.family.david.devices.my_pc
```

A Traffic Path describes how data currently reaches the device:

```text
fiber_node7.isp_edge2.home_router.my_pc
```

These paths may be the same in simple cases, but they do not have to be.

This distinction allows:

- stable names for moving devices
- shortest-path routing independent of human names
- logical grouping separate from physical topology
- hybrid operation where some hubs handle both roles

---

## 7. Registration Flow

Initial registration might work like this:

```text
1. Device connects to a Registry Hub.
2. Device proposes a device_label.
3. Hub checks local namespace for conflicts.
4. Hub verifies or generates a device_id.
5. Device and Hub exchange public keys.
6. Hub creates an Agreement Certificate.
7. Device signs the certificate.
8. Hub signs the certificate.
9. Hub registers the device locally.
10. Hub hands summary information upward.
```

Example upward summary:

```yaml
upward_registration_summary:
  device_id: dev_A9F3
  identity_chain: global.family.david.home.my_pc
  certificate_id: cert_123
  current_attachment: hub_home_001
  state: online
```

---

## 8. Hand-Up Registry Propagation

Registry Hubs should hand access lists and summaries upward one or more levels.

The purpose is to make it possible for higher-level hubs to recognize known device IDs if they move.

A local hub may know direct children:

```text
home hub knows: my_pc, printer, phone
```

A parent hub may know summaries:

```text
family hub knows: dev_A9F3 belongs somewhere under david.home
```

A higher hub may know sparse anchors:

```text
global hub knows: dev_A9F3 belongs under global.family.david.*
```

This avoids requiring every hub to know the entire network.

---

## 9. Device Movement and Light Relocation

DARWIN treats movement as a first-class protocol event.

When a device disconnects from one hub and appears elsewhere, the network should not immediately treat the device as dead.

Instead, the old hub can mark the device as:

```text
in_transit
```

Then traffic can be paused until the device re-registers.

Basic relocation flow:

```text
1. Device disconnects from Hub A.
2. Hub A marks device state as in_transit.
3. Hub A signals active senders to pause traffic.
4. Active lanes enter paused_relocation.
5. Device connects to Hub B.
6. Device presents passport.
7. Hub B verifies passport and device signature.
8. Hub B asks up the registry chain about prior identity history.
9. Registry chain confirms known device_id and previous path.
10. Hub B creates or validates a Move Contract.
11. Traffic Hubs reroute logical lanes.
12. Sender receives resume signal.
13. Traffic continues through the new route.
```

This makes packet forwarding supplemental to identity-aware relocation.

---

## 10. Sender Pause and Buffer Control

When a recipient is in transit, the transient hub should not buffer unbounded traffic.

Instead, the old hub or lane manager can signal the sender:

```text
recipient_in_transit
pause_transmission
```

This prevents buffer growth while preserving the session.

A simple state transition:

```text
active → paused_relocation → awaiting_verification → rerouting → resumed
```

Example lane update:

```yaml
lane_state_update:
  lane_id: lane_S991
  recipient: dev_A9F3
  state: paused_relocation
  last_confirmed_packet: 1042
  sender_action: pause_new_packets
  hold_window_ms: 3000
```

After the recipient reappears:

```yaml
lane_resume:
  lane_id: lane_S991
  recipient: dev_A9F3
  new_attachment: hub_office_007
  resume_from_packet: 1043
  state: resumed
```

---

## 11. Checkpoint Packets

Checkpoint packets are lightweight signals that allow hubs to track device and lane state.

They may indicate:

```text
online
offline
idle
timed_out
disconnected
in_transit
awaiting_verification
quarantined
revoked
```

Example checkpoint packet:

```yaml
checkpoint:
  checkpoint_id: cp_001
  device_id: dev_A9F3
  session_epoch: 8821
  current_hub: hub_office_007
  lane_count: 3
  state: online
  timestamp: 2026-05-26T12:06:00Z
  auth_tag: AUTH_TAG
```

Checkpoint packets help the network maintain a living topology map rather than a purely static routing table.

---

## 12. Tiered Checkpoint Granularity

Different devices need different checkpoint behavior.

A battery sensor should not checkpoint like a gaming PC or autonomous vehicle.

### Tier 0: Passive / Ultra-Low-Power IoT

For sleepy sensors and low-power devices.

```yaml
checkpoint_mode:
  tier: 0
  type: sparse
  interval: 30m
  state_only: true
```

Suitable for:

```text
temperature sensors
humidity sensors
leak detectors
simple smart buttons
```

---

### Tier 1: Normal Smart Devices

For everyday smart home devices.

```yaml
checkpoint_mode:
  tier: 1
  type: periodic
  interval: 30s
  route_awareness: local
```

Suitable for:

```text
smart TVs
thermostats
speakers
cameras
appliances
```

---

### Tier 2: Mobile Interactive Devices

For devices that roam and maintain active sessions.

```yaml
checkpoint_mode:
  tier: 2
  type: active
  interval: 1s-5s
  transit_support: true
```

Suitable for:

```text
phones
laptops
tablets
vehicles
wearables
```

---

### Tier 3: Real-Time / Critical Systems

For systems requiring low interruption tolerance.

```yaml
checkpoint_mode:
  tier: 3
  type: continuous
  predictive_rerouting: true
  standby_route: true
```

Suitable for:

```text
industrial controls
medical systems
autonomous systems
live media infrastructure
critical operations
```

---

## 13. Security and Firewall Behavior

DARWIN passports can function as a first-level firewall mechanism.

Before a device receives meaningful access, a hub can ask:

```text
Does this device have a valid passport?
Was the passport issued by a trusted Registry Hub?
Is the passport revoked?
Is this device allowed in this scope?
Can the device prove it controls the private key tied to the passport?
```

Possible access outcomes:

```text
valid passport       → register and route
unknown issuer       → limited sandbox
no passport          → guest/quarantine
bad signature        → reject
revoked passport     → block
conflicting identity → investigate/quarantine
```

Example policy:

```yaml
passport_policy:
  allowed_scopes:
    - global.family.home.*
    - global.family.office.guest
  denied_scopes:
    - global.family.office.secure_lab.*
  capabilities:
    can_register_name: true
    can_request_routes: true
    can_host_services: false
```

---

## 14. Anti-Impersonation and Actor Continuity

DARWIN must prevent one device from hiding behind another and pretending to be a parent, hub, or authorized actor.

The security model should distinguish:

```text
Passport              = who the device is
Move Contract         = where the device moved
Parent Attestation    = who currently vouches for the device
Session Proof         = whether packets still belong to the same actor
```

A practical approach:

```text
1. Heavy validation at session creation.
2. Session key derivation.
3. Cheap rolling authentication tags on packets.
4. Periodic challenge-response checks.
5. Escalated verification during movement or suspicious behavior.
```

Example per-packet continuity tag:

```text
auth_tag = HMAC(session_key, packet_header + sequence_number + payload_hash)
```

This avoids requiring every packet to carry a full passport while still maintaining actor continuity.

---

## 15. Distributed Agreement and Identity History

Registry Hubs can ask around to trace and query device history.

Questions a hub may ask:

```text
Who last knew this device_id?
What labels has this device used?
What registry paths has this device occupied?
Was the most recent move signed?
Is there an active conflict?
Has this passport been revoked?
```

This creates a federated identity ledger without requiring every event to reach global consensus.

Agreement should be scoped to the relevant conflict.

For example:

```text
local move within home network → local agreement only
move between sibling hubs       → parent agreement
move between registry trees     → nearest common ancestor or witness hubs
identity conflict               → broader agreement escalation
```

The goal is not universal voting on every event. The goal is enough agreement to prevent identity amnesia, hijacking, and conflict.

---

## 16. Scaling and Branch Growth

DARWIN scales by adding branches, not by forcing one global trunk to carry all load.

There may be multiple high-level registry trees:

```text
Global Root A        Global Root B        Global Root C
     │                    │                    │
  regions              regions              regions
     │                    │                    │
 local hubs           local hubs           local hubs
     │                    │                    │
 devices              devices              devices
```

Roots can coordinate through sparse bridges:

```text
Root A ↔ Root B ↔ Root C
```

The network can monitor pressure to decide whether to create new logical or physical branches.

---

## 17. Physical vs Logical Scaling

DARWIN distinguishes between traffic pressure and registry pressure.

Physical pressure indicators:

```text
high route congestion
high latency
high packet loss
frequent traffic across distant branches
bandwidth saturation
```

Logical pressure indicators:

```text
too many devices in one registry scope
high lookup miss rate
frequent upward queries
high namespace collision rate
high move-contract churn
registry table growth
```

Possible responses:

```text
Traffic pressure  → add physical/traffic branch
Registry pressure → add logical/registry branch
Both              → promote or add a hybrid hub
```

Example policy sketch:

```yaml
branch_growth_policy:
  if_cross_tree_traffic_sustained: create_traffic_bridge
  if_registry_load_high: split_registry_scope
  if_mobile_churn_high: create_roaming_witness_hub
  if_name_conflicts_high: create_subscope_or_alias_policy
```

This creates growth-aware routing and registration.

---

## 18. DNS and URL Compatibility

DARWIN can support TLD-style registries and familiar domains.

Instead of resolving a domain directly to an IP address:

```text
example.com → 93.184.216.34
```

A domain could resolve to a DARWIN identity path:

```text
example.com → darwin://global.registry.us.hostingcluster7.webnode3.example_service
```

This allows:

```text
human domain
→ TLD-style registry
→ DARWIN identity chain
→ current attachment
→ traffic route
```

Potential consequences:

```text
Domain ownership does not require fixed server location.
Hosting migrations become signed move contracts.
CDNs can act as Traffic Hubs.
Registrars can act as Registry Hubs.
DNS-like names become aliases over DARWIN passports.
```

---

## 19. Example: New Device Registration

```text
Device: my_pc
Desired scope: global.family.david.home
Hub: home_router
```

Flow:

```text
1. my_pc connects to home_router.
2. my_pc presents or generates keypair.
3. home_router checks whether my_pc label is free.
4. home_router assigns device_id dev_A9F3.
5. home_router creates agreement certificate cert_123.
6. my_pc signs cert_123.
7. home_router signs cert_123.
8. home_router registers:
   dev_A9F3 → global.family.david.home.my_pc
9. home_router hands summary upward.
```

Result:

```yaml
registered_device:
  device_id: dev_A9F3
  identity_chain: global.family.david.home.my_pc
  passport: cert_123
  current_hub: home_router
  state: online
```

---

## 20. Example: Name Conflict

Two devices request the same label in one scope.

Existing device:

```text
global.family.david.home.my_pc → dev_A9F3
```

New device requests:

```text
my_pc → dev_B2C8
```

Hub assigns temporary alias:

```text
global.family.david.home.my_pc_temp_B2C8 → dev_B2C8
```

The device can still be registered, quarantined, or placed in pending status while the human or policy layer resolves the conflict.

---

## 21. Example: Device Relocation

A phone moves from home Wi-Fi to office Wi-Fi during an active session.

```text
1. phone disconnects from home_router.
2. home_router marks phone as in_transit.
3. home_router signals sender to pause transmission.
4. phone connects to office_router.
5. phone presents passport cert_123.
6. office_router verifies device signature.
7. office_router asks registry chain about dev_A9F3.
8. registry confirms known identity.
9. office_router creates move contract move_456.
10. traffic route is updated.
11. sender resumes from last confirmed packet.
```

Result:

```text
The phone kept its identity while changing attachment points.
The lane paused instead of failing immediately.
Traffic resumed after verified relocation.
```

---

## 22. Conceptual Layer Stack

One possible layer model:

```text
Application Layer
  human domains, services, apps

Logical Lane Layer
  session continuity, pause/resume, ordering

Traffic Layer
  routing, next hop, congestion, forwarding

Registry Layer
  identity chains, scope, device lookup

Agreement Layer
  passports, move contracts, attestations

Cryptographic Layer
  keys, signatures, auth tags, revocation

Physical/Link Layer
  actual radio, cable, interface, carrier
```

DARWIN mainly lives between naming, identity, authorization, and routing.

---

## 23. Preliminary Data Objects

### Device Record

```yaml
device_record:
  device_id: dev_A9F3
  current_label: my_pc
  canonical_identity_chain: global.family.david.home.my_pc
  passport_id: cert_123
  current_attachment: hub_home_001
  current_state: online
  last_checkpoint: 2026-05-26T12:06:00Z
```

### Registry Summary

```yaml
registry_summary:
  hub_id: hub_family_001
  scope: global.family.david
  known_devices:
    - device_id: dev_A9F3
      identity_chain: global.family.david.home.my_pc
      current_state: online
    - device_id: dev_B2C8
      identity_chain: global.family.david.home.printer
      current_state: idle
```

### Lane Record

```yaml
lane_record:
  lane_id: lane_S991
  source_device: dev_A9F3
  target_device: dev_B2C8
  state: active
  last_confirmed_packet: 1042
  current_route:
    - hub_home_001
    - hub_family_001
    - hub_office_007
```

---

## 24. Design Principles

1. **Identity is stable. Attachment is temporary.**

2. **Names are scoped. Device IDs are durable.**

3. **Registry paths and traffic paths may diverge.**

4. **Movement should be signed, not guessed.**

5. **Agreement should escalate only as far as needed.**

6. **Checkpointing should match device class and power budget.**

7. **Routing should respond to pressure and topology, not just static hierarchy.**

8. **Security should begin at registration, not after traffic is already flowing.**

9. **Local hubs should know local truth; higher hubs should know summaries.**

10. **The system should pause intelligently rather than fail blindly.**

---

## 25. Open Questions

### Identity and Cryptography

- How is `device_id` generated?
- Is `device_id` a public key hash, random UUID, hardware-bound identifier, or something else?
- How are lost or compromised passports revoked?
- Can a device rotate keys without losing identity?
- How are ownership transfers handled?

### Registry Architecture

- How many levels upward should a hub hand summaries?
- What information should be handed upward?
- How are privacy and visibility handled?
- Can two registry trees disagree about a device?
- How is nearest-common-ancestor discovery performed?

### Movement and Lanes

- How long should a hub keep a device in `in_transit`?
- How much data should be buffered during relocation?
- Who owns lane state: sender, receiver, traffic hub, or registry hub?
- What happens if a device reconnects from two places at once?
- How does the system distinguish sleep from disconnect from hostile disappearance?

### Security

- What is the minimal safe handshake?
- What packet authentication scheme is cheap enough for normal traffic?
- How often should parent attestations renew?
- How are malicious hubs detected?
- How are quarantined devices allowed to recover?

### Scaling

- What metrics determine when a new Registry Hub should be created?
- What metrics determine when a new Traffic Hub should be created?
- Can branch creation be automatic, advisory, or admin-controlled?
- How do high-level registry trees coordinate without flooding each other?

### DNS Compatibility

- What does a DARWIN URL look like?
- Can existing DNS records point to DARWIN paths?
- Would DARWIN need a new URI scheme such as `darwin://`?
- How would TLD-style registries map ownership to passports?

### IoT and Low-Power Devices

- How sparse can checkpoints be before registry confidence decays?
- Can a parent hub checkpoint on behalf of sleepy child devices?
- How does the system prevent a parent from lying about a sleeping device?
- What is the minimum viable passport for ultra-cheap devices?

---

## 26. Possible Build Path

This is not implementation yet, but a reasonable future path would be:

### Phase 1: Local Simulation

Build a small simulator with:

```text
Registry Hub objects
Traffic Hub objects
Device objects
Agreement Certificates
Move Contracts
Checkpoint states
```

No real networking required. Use in-memory objects or JSON files.

### Phase 2: Localhost Prototype

Run hubs as local processes communicating over HTTP, WebSocket, or TCP.

Demonstrate:

```text
device registration
name conflict handling
move contract creation
in_transit pause/resume
checkpoint updates
```

### Phase 3: LAN Prototype

Run the prototype across multiple machines on a local network.

Test:

```text
actual device movement
hub discovery
traffic rerouting
passport verification
quarantine mode
```

### Phase 4: Application Overlay

Create DARWIN as an overlay network rather than replacing existing IP networking.

Existing IP handles physical delivery. DARWIN handles identity, registry, movement, and session continuity above it.

### Phase 5: DNS/URL Bridge

Map familiar domains or local names to DARWIN identity paths.

---

## 27. One-Sentence Description

DARWIN is an identity-aware network registration system where devices carry signed passports, register through scoped namespace trees, move using signed contracts, and preserve logical connectivity through checkpointed, reroutable lanes.

---

## 28. Working Metaphor

DARWIN treats devices like travelers in a transportation network:

```text
Passport          = original identity certificate
Border stamp      = move contract
Station           = hub
Route             = traffic path
Name/address      = scoped registry path
Transit notice    = in_transit checkpoint
Ticket/lane       = active connection
```

The device does not become a new person every time it changes stations. It presents its passport, receives a new stamp, and the transport network updates the route.

