# DARWIN Traffic Hub and Routing Model v0.1

**Project name:** DARWIN  
**Document:** Traffic Hub and Routing Model  
**Version:** v0.1  
**Status:** Concept draft / simulator-oriented routing model  
**Related documents:**

- DARWIN Design Dossier v0.1
- DARWIN Identity, Trust, and Authentication Model v0.1
- DARWIN Packet, Checkpoint, and Lane Protocol v0.1
- DARWIN Registry Hub Data Model v0.1

---

## 1. Purpose

This document defines the first draft of DARWIN’s Traffic Hub and routing model.

The core question is:

```text
How does DARWIN move packets and logical lanes through the network once device identity and registry location are known?
```

A Traffic Hub is responsible for movement, not identity ownership.

It answers:

```text
What is the best current path from A to B?
Which next hop should receive this packet?
Is this lane active, paused, rerouting, or blocked?
Should traffic be forwarded, held, dropped, or redirected?
Is congestion or failure building in this part of the network?
Should a new physical or logical branch be recommended?
```

This document focuses on route behavior, traffic state, hub coordination, relocation support, and simulator-ready routing records.

---

## 2. Core Principle

DARWIN separates logical identity from traffic movement.

A Registry Hub says:

```text
This is who the device is, and this is its current registered attachment.
```

A Traffic Hub says:

```text
This is how traffic should currently reach that attachment.
```

Central rule:

```text
Traffic Hubs route toward verified attachment points, but they do not define device identity.
```

A Traffic Hub may cache identity-related hints, but it should not become the source of truth for passports, labels, or registry authority.

---

## 3. Registry Path vs Traffic Path

DARWIN distinguishes two path types.

### 3.1 Registry Path

A Registry Path describes scoped logical identity.

Example:

```text
global.family.david.home.my_pc
```

It answers:

```text
Where does this device live in the identity namespace?
```

---

### 3.2 Traffic Path

A Traffic Path describes current packet movement.

Example:

```text
hub_source_003 → hub_regional_002 → hub_office_007 → dev_A9F3
```

It answers:

```text
How do packets reach this device right now?
```

The two paths may align in simple networks, but they do not have to.

---

## 4. Traffic Hub Roles

A Traffic Hub may perform one or more roles.

```text
local_forwarder
edge_forwarder
regional_router
traffic_bridge
lane_manager
route_probe_agent
congestion_monitor
relocation_coordinator
hybrid_registry_traffic_hub
```

### 4.1 Local Forwarder

Moves packets between directly attached devices and local upstream hubs.

Example:

```text
home router forwarding between phone, printer, laptop, and upstream network
```

---

### 4.2 Edge Forwarder

Connects a local branch to a wider network.

Example:

```text
home router forwarding traffic to ISP edge hub
```

---

### 4.3 Regional Router

Routes between larger branches.

Example:

```text
regional traffic hub connecting several local hubs
```

---

### 4.4 Traffic Bridge

Creates a direct or semi-direct route between hot branches.

Example:

```text
frequent traffic between office and home branches triggers a dedicated bridge
```

---

### 4.5 Lane Manager

Maintains logical lane state.

This may include:

```text
lane open
lane pause
lane resume
sequence tracking
flow hold
relocation state
route update
```

---

### 4.6 Relocation Coordinator

Handles traffic behavior when a device enters `in_transit`.

This may include:

```text
pausing senders
holding lane metadata
requesting registry lookup
rerouting when new attachment is verified
closing lanes on timeout
```

---

## 5. Traffic Hub Record

A Traffic Hub should have a durable identity and routing scope.

Example:

```yaml
traffic_hub_record:
  hub_id: hub_regional_002
  hub_label: regional_002
  hub_roles:
    traffic: true
    registry: false
    hybrid: false
  traffic_scope: region.us_west.family_cluster
  parent_traffic_hub_id: hub_global_A
  peer_hubs:
    - hub_regional_003
    - hub_regional_004
  directly_connected_hubs:
    - hub_home_001
    - hub_office_007
  public_key: HUB_TRAFFIC_PUBLIC_KEY
  status: active
  capabilities:
    can_forward_packets: true
    can_manage_lanes: true
    can_issue_route_updates: true
    can_probe_routes: true
    can_coordinate_relocation: true
  created_at: 2026-05-26T12:00:00Z
```

A Traffic Hub may also be a Registry Hub, but those responsibilities should be stored separately.

---

## 6. Traffic Hub Data Model Overview

A Traffic Hub may maintain these record groups:

```text
Traffic Hub Record
Neighbor Table
Direct Attachment Table
Route Table
Route Cache
Lane Table
Flow Control Table
Relocation Table
Buffer Table
Route Probe Table
Congestion Metrics Table
Traffic Bridge Table
Policy Table
Security Event Log
Routing Decision Log
```

For the first simulator, the useful minimum is:

```text
Neighbor Table
Direct Attachment Table
Route Table
Lane Table
Relocation Table
Flow Control Table
Congestion Metrics Table
```

---

## 7. Neighbor Table

The Neighbor Table records directly reachable hubs or devices.

Example:

```yaml
neighbor_table:
  hub_home_001:
    neighbor_type: child_hub
    link_type: local_network
    reachable: true
    latency_ms: 2
    bandwidth_score: high
    congestion: low
    last_seen: 2026-05-26T12:06:00Z
    trust_status: verified_hub
  hub_regional_003:
    neighbor_type: peer_hub
    link_type: inter_branch
    reachable: true
    latency_ms: 18
    bandwidth_score: medium
    congestion: medium
    last_seen: 2026-05-26T12:06:00Z
    trust_status: verified_peer
```

Neighbor types:

```text
local_device
child_hub
parent_hub
peer_hub
traffic_bridge
registry_only_hub
unknown
```

The Neighbor Table supports next-hop decisions.

---

## 8. Direct Attachment Table

The Direct Attachment Table records devices currently attached directly to this Traffic Hub.

Example:

```yaml
direct_attachment_table:
  dev_A9F3:
    local_link_id: link_wifi_22
    current_state: online
    local_session_id: sess_8821
    checkpoint_tier: 2
    last_checkpoint: 2026-05-26T12:06:00Z
    link_quality: strong
    allowed_traffic: true
```

This table answers:

```text
Can I directly deliver traffic to this device?
Is the device currently reachable?
Is its link healthy?
Is traffic allowed by local policy?
```

---

## 9. Route Table

The Route Table maps target devices, hubs, or branches to next hops.

Example:

```yaml
route_table:
  dev_A9F3:
    target_type: device
    next_hop: hub_office_007
    route:
      - hub_regional_002
      - hub_office_007
    route_status: verified
    cost: 12
    latency_ms: 18
    congestion: low
    expires_at: 2026-05-26T12:11:00Z
  global.family.david.office:
    target_type: registry_scope
    next_hop: hub_office_007
    route_status: advisory
    cost: 10
```

Route targets may be:

```text
device_id
hub_id
registry_scope
traffic_scope
service_id
alias target
```

Route status values:

```text
verified
advisory
probing
stale
blocked
conflicted
unreachable
```

---

## 10. Route Cache

The Route Cache stores temporary routes or route hints.

Example:

```yaml
route_cache:
  dev_C391:
    next_hop: hub_office_007
    route_hint_source: registry_lookup
    confidence: medium
    cached_at: 2026-05-26T12:06:00Z
    expires_at: 2026-05-26T12:06:05Z
```

Caching rules:

```text
Direct attachments are freshest.
Verified route updates override cached hints.
Registry attachment hints can guide routing but do not prove reachability.
Route probe results should expire quickly.
In-transit routes should not be treated as stable.
```

---

## 11. Lane Table

The Lane Table tracks persistent logical connections.

Example:

```yaml
lane_table:
  lane_S991:
    source_device_id: dev_A9F3
    target_device_id: dev_B2C8
    lane_mode: reliable_ordered
    state: active
    current_route:
      - hub_home_001
      - hub_regional_002
      - hub_office_007
    next_hop: hub_regional_002
    last_sent_sequence: 1044
    last_acknowledged_sequence: 1043
    flow_state: normal
    relocation_state: none
    created_at: 2026-05-26T12:00:00Z
    last_activity: 2026-05-26T12:06:00Z
```

Lane states:

```text
opening
active
flow_hold
paused_relocation
awaiting_verification
rerouting
resumed
closing
terminated
reset
conflict_detected
quarantined
```

Lane modes:

```text
best_effort
reliable_unordered
reliable_ordered
realtime_loss_tolerant
critical_ordered
checkpoint_only
```

---

## 12. Flow Control Table

The Flow Control Table records active throttling, pausing, and hold decisions.

Example:

```yaml
flow_control_table:
  lane_S991:
    flow_state: flow_hold
    reason: recipient_in_transit
    hold_new_packets: true
    retain_unacked_window: true
    hold_started_at: 2026-05-26T12:06:00Z
    hold_until: 2026-05-26T12:06:03Z
    max_hold_extensions: 2
```

Flow states:

```text
normal
slow_down
flow_hold
paused_relocation
blocked
terminated
```

This table prevents senders from blindly filling buffers during relocation.

---

## 13. Relocation Table

The Relocation Table tracks devices and lanes currently affected by movement.

Example:

```yaml
relocation_table:
  dev_A9F3:
    relocation_state: in_transit
    previous_attachment: hub_home_001
    expected_new_attachment: unknown
    affected_lanes:
      - lane_S991
      - lane_S992
    last_confirmed_packet_by_lane:
      lane_S991: 1042
      lane_S992: 88
    hold_window_ms: 3000
    started_at: 2026-05-26T12:06:00Z
    verification_status: pending
```

Relocation states:

```text
none
in_transit
awaiting_new_attachment
awaiting_registry_verification
route_update_pending
rerouting
resumed
failed
conflict_detected
```

---

## 14. Buffer Table

The Buffer Table stores traffic retained during congestion or relocation.

DARWIN should avoid unbounded buffering.

Example:

```yaml
buffer_table:
  lane_S991:
    buffer_policy: retain_unacked_only
    max_packets: 32
    max_bytes: 1048576
    buffered_sequences:
      - 1043
      - 1044
    current_bytes: 20480
    overflow_action: sender_pause
```

Buffer policies:

```text
none
minimal_hold
retain_unacked_only
bounded_buffer
application_defined
critical_preserve
```

Important rule:

```text
During relocation, prefer pausing senders over growing buffers.
```

---

## 15. Route Probe Table

The Route Probe Table stores active or recent route tests.

Example:

```yaml
route_probe_table:
  probe_001:
    target_device_id: dev_A9F3
    target_attachment_hint: hub_office_007
    probe_status: completed
    reachable: true
    latency_ms: 18
    congestion: low
    auth_path_validity: verified
    started_at: 2026-05-26T12:06:01Z
    completed_at: 2026-05-26T12:06:01.018Z
```

Probe results can inform:

```text
route selection
failover
relocation resume
branch growth recommendations
congestion avoidance
```

---

## 16. Congestion Metrics Table

Traffic Hubs should measure pressure.

Example:

```yaml
congestion_metrics:
  hub_id: hub_regional_002
  sample_window_ms: 60000
  packets_forwarded: 120000
  packets_dropped: 180
  average_latency_ms: 22
  p95_latency_ms: 64
  active_lanes: 2400
  paused_lanes: 14
  relocation_events: 9
  cross_tree_traffic_ratio: 0.37
  congestion_state: medium
```

Metrics may include:

```text
packet rate
lane count
route latency
route failures
packet drops
buffer pressure
relocation frequency
cross-tree traffic
probe failure rate
checkpoint volume
flow hold rate
```

---

## 17. Traffic Bridge Table

Traffic Bridges are added when two branches exchange enough traffic to justify a more direct path.

Example:

```yaml
traffic_bridge_table:
  bridge_home_office_001:
    from_hub: hub_home_001
    to_hub: hub_office_007
    bridge_type: direct_logical_bridge
    status: active
    reason: sustained_cross_branch_traffic
    created_at: 2026-05-26T12:30:00Z
    metrics:
      average_latency_before_ms: 64
      average_latency_after_ms: 18
      traffic_reduction_on_parent: 0.42
```

Bridge types:

```text
direct_physical_bridge
direct_logical_bridge
cached_route_bridge
relay_bridge
temporary_event_bridge
critical_standby_bridge
```

---

## 18. Routing Policy Table

Traffic Hubs should route according to policy.

Example:

```yaml
routing_policy:
  hub_id: hub_regional_002
  default_route_metric: weighted_cost
  weights:
    latency: 0.35
    congestion: 0.25
    trust: 0.20
    hop_count: 0.10
    stability: 0.10
  relocation:
    pause_before_buffer: true
    default_hold_window_ms: 3000
    max_hold_extensions: 2
  security:
    reject_unauthenticated_route_updates: true
    require_verified_attachment_for_lane_resume: true
  priority:
    allow_device_claimed_critical_priority: false
```

Policies should be scoped and adjustable.

---

## 19. Route Selection

Route selection chooses the best next hop or path.

Inputs:

```text
target device_id
target attachment hint
available neighbors
route cache
route probes
congestion metrics
lane mode
priority
trust status
policy
```

Basic route selection flow:

```text
1. Check whether target is directly attached.
2. Check verified Route Table entry.
3. Check fresh Route Cache entry.
4. Ask Registry Hub for current attachment if needed.
5. Probe candidate routes if needed.
6. Score candidate routes.
7. Select next hop.
8. Store route decision.
9. Forward packet or open lane.
```

Example route decision:

```yaml
route_decision:
  target_device_id: dev_A9F3
  selected_next_hop: hub_office_007
  selected_route:
    - hub_regional_002
    - hub_office_007
  score: 0.91
  reason:
    - verified_attachment
    - low_latency
    - low_congestion
    - trusted_hub_path
```

---

## 20. Route Cost Model

A route may be scored using multiple factors.

Example factors:

```text
latency
hop_count
congestion
packet_loss
trust_status
route_stability
lane_mode_fit
power_cost
policy_preference
```

Example cost sketch:

```text
route_cost =
  latency_weight * normalized_latency +
  congestion_weight * normalized_congestion +
  hop_weight * hop_count +
  trust_penalty +
  instability_penalty
```

For critical lanes, trust and stability may matter more than low latency.

For real-time lanes, latency and packet loss may dominate.

---

## 21. Routing Modes

Different lanes may request different routing modes.

```text
shortest_path
lowest_latency
lowest_congestion
highest_trust
most_stable
power_saving
realtime
critical_redundant
```

Example:

```yaml
lane_routing_preference:
  lane_id: lane_S991
  mode: reliable_ordered
  routing_preference: most_stable
  avoid_untrusted_hubs: true
  allow_reroute_during_lane: true
```

---

## 22. Forwarding Data Packets

Basic forwarding flow:

```text
1. Receive packet.
2. Validate packet class and header.
3. Check auth tag or trusted upstream validation.
4. Check lane state if packet belongs to a lane.
5. Check target state.
6. Select next hop.
7. Forward packet, buffer it, hold it, drop it, or return error.
8. Update metrics and logs.
```

Example forwarding result:

```yaml
forwarding_result:
  packet_id: pkt_1043
  lane_id: lane_S991
  action: forwarded
  next_hop: hub_office_007
  route_status: verified
```

If target is in transit:

```yaml
forwarding_result:
  packet_id: pkt_1043
  lane_id: lane_S991
  action: held_or_rejected
  reason: target_in_transit
  sender_signal: flow_hold
```

---

## 23. Opening a Routed Lane

Traffic Hubs help establish logical lanes.

Flow:

```text
1. Source requests lane to target device_id.
2. Source Traffic Hub asks Registry Hub for current target attachment.
3. Traffic Hub selects route.
4. Traffic Hub sends lane_open along selected route.
5. Target side validates lane request.
6. lane_open_ack returns.
7. Intermediate hubs store lane forwarding state if required.
8. Lane enters active state.
```

Example lane route state:

```yaml
lane_route_state:
  lane_id: lane_S991
  source_device_id: dev_A9F3
  target_device_id: dev_B2C8
  route:
    - hub_home_001
    - hub_regional_002
    - hub_office_007
  forward_state_by_hub:
    hub_home_001: next_hop_hub_regional_002
    hub_regional_002: next_hop_hub_office_007
    hub_office_007: deliver_local
```

---

## 24. Relocation-Aware Routing

When a device moves, Traffic Hubs should pause and reroute rather than blindly fail.

Relocation-aware routing flow:

```text
1. Old hub detects device disconnect or movement intent.
2. Old hub marks target as in_transit.
3. Old hub signals affected Traffic Hubs and senders.
4. Lane enters paused_relocation.
5. New hub verifies device registration and move contract.
6. Registry Hub confirms new attachment.
7. Traffic Hubs receive route_update or relocation_resume.
8. Lane route is replaced or patched.
9. Sender resumes from correct sequence.
```

Example route patch:

```yaml
route_patch:
  lane_id: lane_S991
  old_segment:
    - hub_regional_002
    - hub_home_001
  new_segment:
    - hub_regional_002
    - hub_office_007
  effective_after_sequence: 1042
  reason: verified_relocation
```

---

## 25. Sender Pause Behavior

Traffic Hubs may signal senders to stop sending new packets.

Example:

```yaml
sender_pause_signal:
  packet_class: CONTROL
  packet_type: flow_hold
  lane_id: lane_S991
  target_device_id: dev_A9F3
  reason: recipient_in_transit
  hold_new_packets: true
  retain_unacked_window: true
  hold_until_ms: 3000
```

Sender behavior:

```text
stop sending new packets
retain unacknowledged sequence state
wait for resume, route update, failure, or timeout
avoid increasing intermediate buffers
```

---

## 26. Resume Behavior

When a device reappears and movement is verified, Traffic Hubs resume affected lanes.

Example:

```yaml
resume_decision:
  lane_id: lane_S991
  target_device_id: dev_A9F3
  new_attachment: hub_office_007
  verified_by_registry: true
  route_probe_success: true
  resume_from_sequence: 1043
  action: resume_lane
```

Resume policy depends on lane mode:

```text
best_effort              → resume with newest packet
reliable_unordered       → resend missing packets if useful
reliable_ordered         → resume from first unacknowledged sequence
realtime_loss_tolerant   → skip stale packets
critical_ordered         → verify complete sequence continuity
```

---

## 27. Rerouting Without Device Movement

Traffic Hubs may reroute lanes even if devices do not move.

Triggers:

```text
congestion
link failure
better route discovered
traffic bridge created
policy change
trust degradation
maintenance event
```

Flow:

```text
1. Detect route pressure or failure.
2. Probe alternatives.
3. Select replacement route.
4. Issue route_update.
5. Continue lane with minimal interruption.
```

Example:

```yaml
route_update:
  lane_id: lane_S991
  reason: congestion_avoidance
  old_route:
    - hub_A
    - hub_B
    - hub_C
  new_route:
    - hub_A
    - hub_D
    - hub_C
  effective_after_sequence: 2200
```

---

## 28. Route Update Trust

Route updates can be dangerous if forged.

A malicious route update could redirect traffic.

Traffic Hubs should require:

```text
trusted hub signature
valid hub authority
route update bound to lane_id and sequence window
registry confirmation for target attachment changes
policy check before accepting route change
```

Example rejection:

```yaml
route_update_result:
  lane_id: lane_S991
  accepted: false
  reason: untrusted_route_update_issuer
  action: ignore_and_log
```

---

## 29. Traffic and Registry Cooperation

Traffic Hubs and Registry Hubs cooperate but should not collapse into one conceptual layer.

Traffic Hub asks Registry Hub:

```text
Where is this device currently registered?
Is this device in transit?
Is the new attachment verified?
Is this passport or move contract valid?
```

Registry Hub asks Traffic Hub:

```text
Can this attachment actually be reached?
Is the route healthy?
Are lanes paused for this device?
Is traffic pressure building between these branches?
```

Shared boundary:

```text
Registry knows identity and attachment truth.
Traffic knows path and movement truth.
```

---

## 30. Route Probing

Route probes test reachability and quality.

Example probe request:

```yaml
route_probe:
  probe_id: probe_001
  source_hub: hub_regional_002
  target_device_id: dev_A9F3
  target_attachment_hint: hub_office_007
  requested_metrics:
    - reachability
    - latency
    - congestion
    - trust_path_validity
```

Example probe response:

```yaml
route_probe_response:
  probe_id: probe_001
  reachable: true
  latency_ms: 18
  congestion: low
  trust_path_validity: verified
  recommended_next_hop: hub_office_007
```

Probe types:

```text
reachability_probe
latency_probe
congestion_probe
trust_path_probe
relocation_probe
standby_route_probe
```

---

## 31. Congestion Handling

When congestion is detected, Traffic Hubs may respond by:

```text
slowing senders
rerouting lanes
lowering priority of bulk traffic
creating flow_hold states
requesting Traffic Bridge creation
reporting pressure to parent hubs
recommending branch growth
```

Example congestion decision:

```yaml
congestion_decision:
  hub_id: hub_regional_002
  congestion_state: high
  affected_routes:
    - hub_home_001_to_hub_office_007
  actions:
    - slow_bulk_lanes
    - probe_alternative_routes
    - recommend_traffic_bridge
```

---

## 32. Traffic Bridge Creation

A Traffic Bridge may be recommended when repeated traffic crosses the same expensive boundary.

Signals:

```text
sustained high cross-tree traffic
frequent route probes between same branches
high latency through parent hubs
repeated relocation between same branches
persistent congestion on shared trunk
critical lanes requiring standby paths
```

Bridge creation flow:

```text
1. Traffic Hubs collect metrics.
2. Hubs identify recurring pressure between branches.
3. Candidate bridge is proposed.
4. Policy checks authority and cost.
5. Route probes validate benefit.
6. Bridge is created or simulated.
7. Route tables are updated.
8. Metrics compare before and after behavior.
```

Example bridge recommendation:

```yaml
traffic_bridge_recommendation:
  from_branch: global.family.david.home
  to_branch: global.family.david.office
  reason: sustained_cross_branch_traffic
  sample_window_ms: 3600000
  average_latency_ms: 72
  projected_latency_ms: 22
  parent_trunk_load_reduction: 0.38
  recommendation: create_direct_logical_bridge
```

---

## 33. Physical vs Logical Traffic Branches

Traffic scaling may involve physical or logical changes.

### 33.1 Physical Branch

A physical branch changes actual connectivity.

Examples:

```text
new router
new relay node
new dedicated link
new access point
new edge hub
```

Use when:

```text
bandwidth is saturated
latency is physical/topological
packet loss is link-related
many devices need closer access
```

---

### 33.2 Logical Branch

A logical branch changes route organization without necessarily adding physical hardware.

Examples:

```text
new route grouping
new virtual traffic bridge
new lane coordinator
new cache layer
new traffic policy scope
```

Use when:

```text
routing decisions are too centralized
lane state is too concentrated
relocation events are clustered
traffic policy needs more granularity
```

---

## 34. Standby Routes

Some lane modes may require standby routes.

Example:

```yaml
standby_route_record:
  lane_id: lane_critical_001
  primary_route:
    - hub_A
    - hub_B
    - hub_C
  standby_route:
    - hub_A
    - hub_D
    - hub_C
  standby_status: warm
  last_probe: 2026-05-26T12:06:00Z
```

Standby route modes:

```text
none
cold
warm
hot
parallel
```

Use cases:

```text
critical ordered lanes
industrial controls
medical systems
live media infrastructure
autonomous systems
```

---

## 35. Lane Migration Between Traffic Hubs

A lane manager role may move from one Traffic Hub to another.

Reasons:

```text
relocation
congestion
hub failure
better route locality
branch growth
policy change
```

Flow:

```text
1. Current lane manager proposes transfer.
2. New lane manager accepts or rejects.
3. Lane state snapshot is transferred.
4. Sequence state is verified.
5. Route update is issued.
6. Old manager retires its lane authority.
```

Example:

```yaml
lane_manager_transfer:
  lane_id: lane_S991
  old_manager: hub_regional_002
  new_manager: hub_office_007
  transfer_reason: target_relocated_near_new_manager
  sequence_state:
    last_acknowledged: 1042
    resume_from: 1043
  status: pending_acceptance
```

Open question:

```text
Should the lane manager be a Traffic Hub, the sender hub, the receiver hub, or a dedicated lane coordinator?
```

---

## 36. Hub Failure Handling

Traffic Hubs may fail or disappear.

Failure signals:

```text
missed hub checkpoint
route probe failure
neighbor unreachable
sudden packet loss
lane ack timeout
registry reports hub unavailable
```

Response options:

```text
route around hub
pause affected lanes
query registry for alternate attachment
promote standby route
transfer lane management
emit route_unavailable error
recommend branch repair
```

Example failure response:

```yaml
hub_failure_response:
  failed_hub: hub_regional_002
  affected_lanes:
    - lane_S991
    - lane_S992
  action:
    - probe_alternate_routes
    - activate_standby_routes
    - notify_registry
```

---

## 37. Security-Aware Routing

Routing should consider trust, not only speed.

Security-aware route inputs:

```text
hub trust level
route update signature validity
known compromised hubs
policy-denied regions
lane security mode
passport and move status
attachment verification freshness
```

Example:

```yaml
security_route_filter:
  lane_id: lane_secure_001
  avoid_hubs:
    - hub_untrusted_009
  require_verified_route_updates: true
  require_trusted_attachment: true
  minimum_hub_trust_level: federated_peer
```

For some lanes, a slower trusted route should beat a faster untrusted route.

---

## 38. Traffic Priority

Traffic Hubs may schedule packets by priority.

Priority levels:

```text
critical
control
high
normal
low
bulk
```

Suggested order:

```text
critical security and quarantine signals
movement and relocation signals
authentication signals
lane control packets
checkpoint packets
data packets
bulk traffic
```

Important rule:

```text
A device should not be allowed to self-declare critical priority unless its passport, local policy, or lane mode permits it.
```

---

## 39. Traffic Hub Metrics for Scaling

Traffic Hubs should collect metrics that help the network grow intelligently.

Metrics:

```text
active lanes
lane opens per minute
packets forwarded
packets dropped
average latency
p95 latency
buffer pressure
flow hold count
relocation count
route probe failure rate
cross-tree traffic ratio
traffic bridge benefit estimate
hot target devices
hot source branches
```

Example:

```yaml
traffic_scaling_metrics:
  hub_id: hub_regional_002
  sample_window_ms: 60000
  active_lanes: 2400
  packets_forwarded: 120000
  average_latency_ms: 22
  p95_latency_ms: 64
  relocation_count: 9
  flow_hold_count: 14
  cross_tree_traffic_ratio: 0.37
  bridge_recommendation: consider_home_office_bridge
```

---

## 40. Growth Recommendations

A Traffic Hub may recommend changes.

Recommendation types:

```text
create_traffic_bridge
promote_edge_hub
add_physical_branch
add_logical_branch
split_lane_management
increase_checkpoint_frequency
reduce_checkpoint_frequency
adjust_route_policy
create_standby_route
```

Example:

```yaml
growth_recommendation:
  recommendation_id: rec_001
  recommendation_type: create_traffic_bridge
  affected_branches:
    - global.family.david.home
    - global.family.david.office
  reason: sustained_cross_tree_traffic
  confidence: high
  expected_benefit:
    latency_reduction: 0.62
    trunk_load_reduction: 0.38
  requires_admin_approval: true
```

---

## 41. Traffic Hub Operations

Core Traffic Hub operations:

```text
forward_packet
open_lane
close_lane
pause_lane
resume_lane
reroute_lane
select_route
probe_route
update_route_table
mark_target_in_transit
apply_flow_hold
release_flow_hold
buffer_packet
flush_buffer
record_congestion
recommend_bridge
handle_hub_failure
verify_route_update
```

Each operation should return:

```text
success
failure
pending
rerouted
paused
blocked
quarantined
```

---

## 42. Operation: Forward Packet

Purpose:

```text
Move a packet toward its target according to lane state and route policy.
```

Flow:

```text
1. Receive packet.
2. Validate header and packet class.
3. Check lane state if lane_id is present.
4. Check target state if known.
5. Validate or trust auth status according to policy.
6. Select next hop.
7. Forward, hold, buffer, drop, or error.
8. Record metrics.
```

Example result:

```yaml
forward_packet_result:
  packet_id: pkt_1043
  action: forwarded
  next_hop: hub_office_007
  route_status: verified
```

---

## 43. Operation: Select Route

Purpose:

```text
Choose a route or next hop for a target.
```

Flow:

```text
1. Check direct attachment.
2. Check verified route table.
3. Check route cache.
4. Ask registry for attachment if needed.
5. Probe candidate routes if needed.
6. Score candidates.
7. Return route decision.
```

Example result:

```yaml
select_route_result:
  target_device_id: dev_A9F3
  selected_next_hop: hub_office_007
  selected_route:
    - hub_regional_002
    - hub_office_007
  route_status: verified
  score: 0.91
```

---

## 44. Operation: Pause Lane for Relocation

Purpose:

```text
Pause traffic when a target device is in transit.
```

Flow:

```text
1. Receive in_transit notice.
2. Find affected lanes.
3. Update Lane Table to paused_relocation.
4. Update Flow Control Table.
5. Apply Buffer Policy.
6. Signal senders with flow_hold.
7. Wait for relocation_resume, relocation_failed, or timeout.
```

Example result:

```yaml
pause_lane_result:
  lane_id: lane_S991
  state: paused_relocation
  reason: recipient_in_transit
  hold_window_ms: 3000
  sender_signal: flow_hold
```

---

## 45. Operation: Resume Lane After Relocation

Purpose:

```text
Resume a paused lane after the target reappears and movement is verified.
```

Flow:

```text
1. Receive relocation_resume or verified route update.
2. Confirm registry verification.
3. Probe new route if needed.
4. Update Route Table and Lane Table.
5. Set resume sequence.
6. Release flow hold.
7. Notify sender.
```

Example result:

```yaml
resume_lane_result:
  lane_id: lane_S991
  state: active
  new_route:
    - hub_source_003
    - hub_regional_002
    - hub_office_007
  resume_from_sequence: 1043
```

---

## 46. Operation: Recommend Traffic Bridge

Purpose:

```text
Suggest a new bridge when traffic patterns show repeated expensive crossing.
```

Flow:

```text
1. Aggregate traffic metrics.
2. Detect hot branch pair.
3. Estimate benefit.
4. Check policy and authority.
5. Produce recommendation.
6. Optionally simulate proposed bridge.
```

Example result:

```yaml
recommend_traffic_bridge_result:
  recommendation_type: create_traffic_bridge
  from_hub: hub_home_001
  to_hub: hub_office_007
  confidence: high
  expected_latency_reduction: 0.62
  requires_admin_approval: true
```

---

## 47. Minimal Simulator Data Model

For the first simulator, a Traffic Hub can be simple.

Minimum object:

```yaml
TrafficHub:
  hub_id: string
  neighbors: map[hub_id, NeighborRecord]
  direct_attachments: map[device_id, AttachmentRecord]
  routes: map[target_id, RouteRecord]
  lanes: map[lane_id, LaneRecord]
  flow_controls: map[lane_id, FlowControlRecord]
  relocations: map[device_id, RelocationRecord]
  metrics: TrafficMetrics
```

Minimum operations:

```text
connect_neighbor()
attach_device()
detach_device()
select_route()
forward_packet()
open_lane()
pause_lane()
resume_lane()
mark_in_transit()
update_route()
record_metric()
```

---

## 48. Minimal Simulator Scenarios

### 48.1 Direct Local Delivery

```text
Device A and Device B attach to same Traffic Hub.
A opens lane to B.
Packets deliver directly.
```

Expected result:

```text
route has one hub
lane enters active
packets delivered
```

---

### 48.2 Routed Delivery Across Hubs

```text
Device A attaches to Hub 1.
Device B attaches to Hub 3.
Hub 1 routes through Hub 2 to Hub 3.
```

Expected result:

```text
route selected
packets forwarded through intermediate hub
acks return
```

---

### 48.3 Recipient Relocation

```text
Device B moves from Hub 3 to Hub 4.
Old hub marks B in_transit.
Lane pauses.
New route is verified.
Lane resumes.
```

Expected result:

```text
flow_hold emitted
route patched
resume sequence preserved
```

---

### 48.4 Congestion Reroute

```text
Hub 2 becomes congested.
Alternative route through Hub 5 exists.
Lane reroutes.
```

Expected result:

```text
route_update emitted
lane remains active or briefly rerouting
metrics improve
```

---

### 48.5 Traffic Bridge Recommendation

```text
Home branch and office branch exchange high sustained traffic.
Parent hub becomes overloaded.
System recommends direct bridge.
```

Expected result:

```text
growth_recommendation created
estimated benefit recorded
```

---

### 48.6 Untrusted Route Update

```text
Unknown hub sends route_update for an active lane.
Traffic Hub rejects it.
```

Expected result:

```text
route_update ignored
security event logged
lane remains on trusted route
```

---

## 49. Open Questions

### Routing Authority

- Who is allowed to issue route updates?
- Can multiple Traffic Hubs manage the same lane?
- Should route decisions be local, negotiated, or centrally coordinated?
- Can a device request a preferred route?

### Lane Management

- Who owns authoritative lane state?
- Can lane management migrate during relocation?
- How much lane state should intermediate hubs store?
- Should stateless forwarding be supported for some lane modes?

### Route Metrics

- What is the default route cost formula?
- How should trust be weighted against latency?
- How are route probes authenticated?
- How often should route metrics be refreshed?

### Relocation

- Should old hubs or new hubs coordinate resume?
- How does the system handle simultaneous old and new attachment claims?
- What is the default relocation hold window?
- Can predictive routing prepare for movement before disconnect?

### Traffic Bridges

- Who approves bridge creation?
- Can bridges be temporary?
- Can bridges be automatically removed when traffic drops?
- How are bridge trust and security handled?

### Scaling

- When does traffic pressure justify a physical branch?
- When does it justify a logical branch?
- How do Traffic Hub recommendations coordinate with Registry Hub recommendations?
- Can branch growth be simulated before being deployed?

### Security

- Which routing messages require signatures?
- How are malicious Traffic Hubs detected?
- Can a Traffic Hub route packets without knowing device identity?
- How much metadata should Traffic Hubs be allowed to inspect?

---

## 50. Working Summary

A DARWIN Traffic Hub is the motion layer of the network. It does not create identity, but it uses verified identity and attachment information to move packets, manage lanes, respond to relocation, avoid congestion, and recommend growth.

The central traffic rule is:

```text
Route toward verified attachment, preserve lane continuity when possible, and pause before flooding uncertainty.
```

In the travel metaphor:

```text
The Traffic Hub is the transit dispatcher. It does not decide who the traveler is, but it decides which train, road, bridge, detour, or holding pattern gets them and their messages to the next verified station.
```

