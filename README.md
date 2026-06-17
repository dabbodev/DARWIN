# DARWIN Simulator

**DARWIN** stands for **Direct-Access Registration Window Interface Network**.

DARWIN is an experimental identity-aware network model where devices carry durable identities, register through scoped namespaces, route through Traffic Hubs, and can move between network branches without losing their logical identity.

This repository is a **simulator-first prototype**, not a real network stack. The v0.1 goal is to model DARWIN behavior clearly enough to test registration, movement, routing, checkpointing, lane pause/resume, conflicts, symbolic trust decisions, metrics, and advisory growth recommendations before attempting real sockets, production cryptography, kernel networking, DNS integration, or hardware identity.

## Current Status

This project is currently released at **simulator v0.8.0** on `main`. The
annotated `v0.8.0` tag and GitHub release have been published. No package
publication was performed. The v0.8 release extends simulator-only retained
authority outcome history while keeping canonical identity, TrafficHub routing,
and v0.7 registry history, audit, and trace explainability behavior unchanged.

The v0.1 simulator answers questions like:

- Can a device register under a scoped Registry Hub?
- Can two devices reuse the same local label in different scopes?
- Can a hub detect a same-scope label conflict and assign a temporary label?
- Can a device move from one hub to another while preserving identity?
- Can active logical lanes pause while a device is `in_transit`?
- Can lanes resume after a verified symbolic move?
- Can symbolic authentication failures quarantine a spoofed actor?
- Can repeated traffic pressure produce an advisory bridge recommendation?

The simulator makes those behaviors visible through deterministic logs, snapshots, YAML scenario files, and tests.

## v0.2 Development Branch

The v0.2 release remains simulator-only. It does not add real networking,
production cryptography, DNS integration, an async runtime, or a web UI.

Useful v0.2 docs:

- `docs/SCENARIO_DSL_v0_2.md`
- `docs/SCENARIO_INDEX.md`
- `docs/VISUALIZATION_v0_2.md`
- `docs/TRACE_EXPORT_v0_2.md`
- `docs/RELEASE_NOTES_v0_2.md`

## v0.3 Auth Bridge

The v0.3 auth bridge remains simulator-only. It adds opt-in
`hmac_sha256_experimental` scenarios for deterministic HMAC-style checks, but
does not add production cryptography, key exchange, secure storage, public-key
signatures, certificate chains, or real networking.

- `docs/AUTH_BRIDGE_v0_3.md`
- `docs/V0_3_ROADMAP.md`
- `docs/RELEASE_NOTES_v0_3.md`

## v0.4 Move-Contract Auth

The v0.4 move-contract auth release keeps symbolic move validation as the
default while allowing opt-in `hmac_sha256_experimental` move proofs that reuse
v0.3 local session lifecycle concepts. This is deterministic simulator behavior
only, not production cryptography.

- `docs/V0_4_ROADMAP.md`
- `docs/MOVE_CONTRACT_AUTH_v0_4.md`
- `docs/RELEASE_NOTES_v0_4.md`

## v0.5 Alias Registry

v0.5 implements simulator-only Registry Hub aliases, short handles,
progressive alias fallback, and delegated alias bundles or zones. DNS-style
alias bundles are simulator records only; v0.5 does not add real DNS, public
domain registration, production identity proof, public CA behavior, real
networking, external registry integration, TrafficHub routing changes, or
canonical identity replacement.

- `docs/V0_5_ROADMAP.md`
- `docs/ALIAS_REGISTRY_v0_5.md`
- `docs/RELEASE_NOTES_v0_5.md`

## v0.6 Alias Authority Chain

v0.6 implements simulator-only parent-scope authority negotiation for alias
claims. Aliases are authorized shortcuts and do not replace canonical identity
chains. The released simulator version is `darwin-sim 0.6.0`. The `v0.6.0`
tag and GitHub release exist; no package publication was performed. v0.6 does
not add real DNS, integrate registrars, model public CA behavior, change
TrafficHub routing, or rewrite canonical identity chains.

- `docs/V0_6_ROADMAP.md`
- `docs/ALIAS_AUTHORITY_CHAIN_v0_6.md`
- `docs/RELEASE_NOTES_v0_6_DRAFT.md`

## v0.7 History, Audit, and Trace Explainability

v0.7 released work focuses on registry history,
authority audit trails, and scenario trace explainability while preserving the
v0.6 authority-chain behavior. Sprint 1 adds read-only RegistryHub history query
helpers, Sprint 2 adds read-only authority audit trace summary helpers, Sprint
3 adds deterministic trace explanation helpers, Sprint 4 adds read-only
scenario assertions and v0.7 scenarios, and Sprint 5
hardens assertion validation, diagnostics, docs, scenario index checks, and
release-note material without changing simulator runtime behavior.

- `docs/V0_7_ROADMAP.md`
- `docs/REGISTRY_HISTORY_QUERIES_v0_7.md`
- `docs/AUTHORITY_AUDIT_TRACES_v0_7.md`
- `docs/TRACE_EXPLAINABILITY_v0_7.md`
- `docs/RELEASE_NOTES_v0_7_DRAFT.md`

v0.7 scenarios:

- `scenarios/037_registry_history_alias_claim.yaml`
- `scenarios/038_registry_history_alias_conflict.yaml`
- `scenarios/039_authority_audit_trace_success.yaml`
- `scenarios/040_authority_audit_trace_fallback.yaml`
- `scenarios/041_trace_explainability_denials.yaml`

v0.5 alias scenarios:

- `scenarios/026_alias_claim_success.yaml`
- `scenarios/027_alias_claim_conflict.yaml`
- `scenarios/028_alias_release_blocks_resolution.yaml`
- `scenarios/029_progressive_alias_fallback.yaml`
- `scenarios/030_alias_bundle_delegation.yaml`
- `scenarios/031_dns_style_alias_bundle.yaml`

v0.6 authority-chain scenarios:

- `scenarios/032_alias_authority_chain_success.yaml`
- `scenarios/033_alias_authority_chain_fallback.yaml`
- `scenarios/034_alias_authority_chain_name_taken.yaml`
- `scenarios/035_alias_authority_chain_policy_denied.yaml`
- `scenarios/036_alias_authority_chain_broken_parent.yaml`

The v0.7 released scenario set is `001` through `041`, and the v0.7 version
reported `darwin-sim 0.7.0`.

v0.7 remains simulator-only. RegistryHub retains terminal grant provenance,
not full persistent failed authority-chain paths, and scenario `041` relies on
scenario-run in-memory denial explainability data. v0.7 does not add
production audit/compliance guarantees, persistent failed-path audit storage,
a broad event store, real DNS, registrar integration, public CA behavior,
production identity proof, external services, TrafficHub routing changes, or
canonical identity rewrites.

## v0.8 Retained Authority Outcomes

v0.8 released work adds retained authority outcome history. Sprint 1 adds
simulator-local authority outcome retention on the requesting `RegistryHub`,
keeping compact records for
successful, fallback, conflict/name-taken, policy-denied, broken-path, and
other terminal authority-chain attempts. Sprint 2 adds read-only query helpers
for those retained outcomes.
Sprint 3 adds read-only scenario assertions for retained authority outcomes
and Sprint 4 exposes those retained summaries in detailed snapshots and
existing JSON snapshot/result exports. Sprint 5 hardens tests and docs for
retained records, queries, assertions, snapshot/export visibility, scenario
listing coverage, and draft release-note material while preserving v0.7 alias,
audit, explanation, TrafficHub routing, and canonical identity behavior.
The v0.8.0 release is on `main` with annotated tag `v0.8.0` and a published
GitHub release. No package publication was performed.

- `docs/V0_8_ROADMAP.md`
- `docs/AUTHORITY_OUTCOME_RETENTION_v0_8.md`
- `docs/AUTHORITY_OUTCOME_QUERIES_v0_8.md`
- `docs/RELEASE_NOTES_v0_8_DRAFT.md`

v0.8 scenarios:

- `scenarios/042_authority_outcome_history_success.yaml`
- `scenarios/043_authority_outcome_history_denials.yaml`

v0.8 remains simulator-only and does not add production audit/compliance
guarantees, DNS, registrar integration, public CA behavior, production identity
proof, external services, scenario actions, TrafficHub routing changes, or
canonical identity rewrites. Retained authority outcome history is
simulator-local introspection on the requesting `RegistryHub`; detailed
snapshots and JSON result exports expose compact retained summaries, while
compact `world.snapshot()` remains unchanged.

On the v0.9 planning branch, scenarios `044` through `046` add
simulator-local mailbox message delivery coverage for successful in-memory
delivery, deterministic failure behavior, and lane fallback policy outcomes.
The checked-in scenario set is currently `001` through `046`, and the current
branch version remains `darwin-sim 0.8.0`.

## What v0.1 Supports

- Scoped Registry Hub registration and label conflict handling.
- Registry hand-up summaries.
- Traffic Hub route selection and symbolic packet delivery.
- Logical lane open/send behavior with sequence state.
- Checkpoint recording and timeout state.
- Relocation flow with `in_transit`, lane pause, move, reroute, and resume.
- Symbolic trust failures, quarantine, and auth-tag rejection behavior.
- Metrics and advisory growth recommendations.
- Deterministic YAML/JSON scenario parsing, validation, execution, event logs, and snapshots.

Scenarios use simulated time only. Runs are deterministic for the same input file.

## What v0.1 Intentionally Does Not Support

- Real networking, sockets, DNS integration, kernel routing, or packet capture.
- Real cryptography, key management, signatures, HMACs, CMACs, counters, or replay protection.
- Real authentication or authorization decisions.
- Async behavior, distributed processes, web UI, or automatic topology mutation.
- Production-grade performance, persistence, or security claims.

Authentication and cryptography fields in v0.1 are symbolic flags used to exercise simulator behavior. Networking is simulated in memory.

## Core Concepts

### Device Identity

A DARWIN device has a durable `device_id`.

The `device_id` should not depend on the current IP address, MAC address, local attachment point, or display label. In later phases, this identity may be tied to a cryptographic keypair. In v0.1, identity can be represented symbolically.

```text
Device Identity = who the device is
Attachment      = where the device is currently connected
Label           = local human-readable name
```

### Scoped Labels and Registry Paths

Device labels are scoped. A label only needs to be unique inside its local Registry Hub scope.

```text
global.family.david.home.printer
global.family.david.office.printer
global.company.lab.printer
```

Those can all be valid because each `printer` label belongs to a different scope.

### Registry Hubs

A **Registry Hub** manages identity, labels, passports, summaries, attachment state, checkpoint state, move history, conflicts, revocation, and authority inside a scope.

Registry Hubs answer questions like:

```text
Who is this device?
What label does it have here?
Is its passport valid?
Where is it currently attached?
Has it moved recently?
Should I ask a parent or witness hub?
```

### Traffic Hubs

A **Traffic Hub** moves packets and manages routes, lanes, forwarding, congestion, route probes, relocation handoffs, flow control, and traffic bridge recommendations.

Traffic Hubs answer questions like:

```text
How do packets reach this device right now?
Is this lane active, paused, rerouting, or blocked?
Should traffic be forwarded, held, dropped, or redirected?
Is congestion building?
Should a traffic bridge be recommended?
```

### Hybrid Hubs

A **Hybrid Hub** performs both Registry Hub and Traffic Hub roles.

For v0.1, prefer composition over complicated inheritance:

```text
HybridHub
  registry: RegistryHub
  traffic: TrafficHub
```

### Passports

A DARWIN passport is the root identity record for a device.

It represents the first approved registration of a device into a scope. In production, it would likely involve public-key signatures and issuer trust. In v0.1, it should be symbolic.

```yaml
PassportRecord:
  passport_id: cert_123
  device_id: dev_A9F3
  issued_by: hub_home_001
  issued_scope: global.family.david.home
  valid: true
  revoked: false
```

### Move Contracts

A **Move Contract** records that a device moved between scopes or attachment points. It references the passport and prevents a new hub from simply claiming a device without proof.

For v0.1, move validity can be represented with a simple symbolic flag.

```yaml
MoveContract:
  move_id: move_001
  passport_id: cert_123
  device_id: dev_A9F3
  from_scope: global.family.david.home
  to_scope: global.family.david.office
  old_attachment: hub_home_001
  new_attachment: hub_office_007
  valid: true
```

### Local Rolling Proof

Passports are for heavier cross-network or cross-scope identity checks.

Local rolling proof is for same-network continuity. It helps prevent a device from gaining access by spoofing a MAC address, local address, label, or stale attachment hint.

In v0.1, this is symbolic:

```yaml
auth_state:
  passport_valid: true
  issuer_trusted: true
  rolling_proof_valid: true
  packet_auth_tag_valid: true
```

Future phases may replace these fields with real challenge-response, HMAC, CMAC, signatures, counters, epochs, and replay protection.

### Checkpoints

Checkpoint packets report liveness and state.

Common device states include:

```text
unknown
claiming_identity
passport_verified
locally_authenticated
online
idle
active
disconnected
in_transit
awaiting_verification
timed_out
offline
quarantined
revoked
rejected
```

Checkpoint tiers allow different devices to report at different rates:

```text
Tier 0 = sparse / passive IoT
Tier 1 = normal smart device
Tier 2 = mobile interactive device
Tier 3 = critical / real-time device
```

### Logical Lanes

A **Logical Lane** is a persistent connection relationship between authenticated device identities.

A lane is not just a route. It tracks source identity, target identity, lane mode, sequence state, acknowledgments, route state, flow state, and relocation state.

Example states:

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
conflict_detected
quarantined
```

During relocation, DARWIN should pause senders and avoid unbounded buffering.

```text
active -> paused_relocation -> awaiting_verification -> rerouting -> resumed -> active
```

## Simulator Design

The simulator is a deterministic, in-memory Python model.

It should use:

- Python 3.11+
- `dataclasses` for models
- `pytest` for tests
- YAML or JSON scenario files
- `argparse` for the CLI
- optional `networkx` for graph routing experiments later

The simulator models DARWIN as objects interacting through explicit events.

Example event types:

```text
DeviceConnects
DeviceRegisters
DeviceSendsCheckpoint
DeviceOpensLane
PacketSent
PacketForwarded
PacketAcknowledged
DeviceDisconnects
DeviceMarkedInTransit
SenderFlowHeld
DeviceReconnects
MoveVerified
RouteUpdated
LaneResumed
ConflictDetected
DeviceQuarantined
GrowthRecommended
```

The simulator uses simulated time rather than wall-clock time so tests remain deterministic.

## Repository Structure

```text
DARWIN/
  README.md
  pyproject.toml
  docs/
    ARCHITECTURE_v0_1.md
    DARWIN_Design_Dossier_v0_1.md
    DARWIN_Identity_Trust_Authentication_v0_1.md
    DARWIN_Packet_Checkpoint_Lane_Protocol_v0_1.md
    DARWIN_Registry_Hub_Data_Model_v0_1.md
    DARWIN_Traffic_Hub_Routing_Model_v0_1.md
    DARWIN_Simulator_Build_Plan_v0_1.md
    DEMO_GUIDE_v0_1.md
    DEVELOPMENT.md
    RELEASE_NOTES_v0_1.md
    RELEASE_NOTES_v0_2.md
    RELEASE_NOTES_v0_3.md
    RELEASE_NOTES_v0_4.md
    RELEASE_NOTES_v0_5.md
    SCENARIO_DSL_v0_2.md
    SCENARIO_INDEX.md
    TRACE_EXPORT_v0_2.md
    V0_2_ROADMAP.md
    V0_3_ROADMAP.md
    V0_4_ROADMAP.md
    V0_5_ROADMAP.md
    VISUALIZATION_v0_2.md
    AUTH_BRIDGE_v0_3.md
    ALIAS_REGISTRY_v0_5.md
    MOVE_CONTRACT_AUTH_v0_4.md
  darwin/
    __init__.py
    ids.py
    models/
      __init__.py
      device.py
      hub.py
      passport.py
      packet.py
      lane.py
      route.py
      checkpoint.py
      events.py
      policies.py
    sim/
      __init__.py
      assertions.py
      event_log.py
      export.py
      library.py
      presets.py
      runner.py
      scenarios.py
      timeline.py
      validation.py
      visualize.py
      world.py
    registry/
      __init__.py
      operations.py
      summaries.py
      conflicts.py
    traffic/
      __init__.py
      routing.py
      lanes.py
      relocation.py
      metrics.py
    auth/
      __init__.py
      hmac_bridge.py
      move_contract.py
      modes.py
      symbolic.py
      trust.py
    cli/
      __init__.py
      main.py
  scenarios/
    001_basic_registration.yaml
    002_name_conflict.yaml
    003_lane_open_and_send.yaml
    004_relocation_pause_resume.yaml
    005_relocation_timeout.yaml
    006_mac_spoof_symbolic_failure.yaml
    007_congestion_bridge_recommendation.yaml
    008_invalid_move_contract.yaml
    009_duplicate_device_claim.yaml
    010_unreachable_relocation_resume.yaml
    011_preset_lane_demo.yaml
    012_hmac_checkpoint_success.yaml
    013_hmac_packet_auth_failure.yaml
    014_hmac_checkpoint_tamper_failure.yaml
    015_hmac_missing_secret_failure.yaml
    016_hmac_rolling_proof_failure.yaml
    017_hmac_session_rotation.yaml
    018_hmac_session_expiration.yaml
    019_hmac_revoked_session_failure.yaml
    020_hmac_quarantine_blocks_checkpoint.yaml
    021_hmac_move_contract_success.yaml
    022_hmac_move_contract_tamper_failure.yaml
    023_hmac_move_contract_expired_session.yaml
    024_hmac_move_contract_revoked_device.yaml
    025_symbolic_move_contract_still_works.yaml
  tests/
    test_auth_symbolic.py
    test_checkpoints.py
    test_growth_recommendations.py
    test_logical_lanes.py
    test_metrics.py
    test_quarantine.py
    test_registry_operations.py
    test_registry_summaries.py
    test_release_readiness.py
    test_relocation_edge_cases.py
    test_relocation.py
    test_route_costs.py
    test_scenario_export.py
    test_scenario_library.py
    test_scenario_presets.py
    test_scenario_route_costs.py
    test_scenario_runner.py
    test_scenario_suite.py
    test_scenario_validation.py
    test_smoke.py
    test_symbolic_trust.py
    test_timeline_export.py
    test_mermaid_export.py
    test_traffic_routing.py
    test_v01_polish.py
```

## Quick Start

```bash
git clone <repo-url>
cd DARWIN
python -m venv .venv
```

Activate the environment:

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

Install in editable mode with test, lint, and scenario YAML support:

```bash
pip install -e ".[dev,cli]"
```

Run tests:

```bash
python -m pytest
```

Run Ruff:

```bash
python -m ruff check .
```

The CI workflow runs the same local validation commands: Ruff, pytest,
scenario listing/validation, and the all-scenario regression script.

List scenarios:

```bash
python -m darwin.cli.main list-scenarios
```

Validate a scenario without executing it:

```bash
python -m darwin.cli.main validate-scenario scenarios/001_basic_registration.yaml
```

Run a scenario:

```bash
python -m darwin.cli.main run scenarios/001_basic_registration.yaml
```

Run a relocation scenario with a final snapshot:

```bash
python -m darwin.cli.main run scenarios/004_relocation_pause_resume.yaml --dump-snapshot
```

If the package script is on your PATH, the same commands are available as:

```bash
darwin-sim list-scenarios
darwin-sim validate-scenario scenarios/001_basic_registration.yaml
darwin-sim run scenarios/001_basic_registration.yaml
```

## First Development Milestones

### Milestone 1: Basic Object World

Goal: create the smallest working simulation world.

Deliverables:

```text
World exists
Devices can be created
Hubs can be created
Hubs can connect
Devices can attach to hubs
One trivial scenario runs
```

Success check:

```text
A device object and hub object can be created, attached, logged, and printed.
```

### Milestone 2: Registry Works

Goal: implement scoped registration.

Deliverables:

```text
RegistryHub
Device
PassportRecord
LocalDeviceRecord
Label Index
Device ID Index
Attachment Index
register_device()
resolve_label()
resolve_device_id()
assign_temp_label()
```

Success check:

```text
dev_A9F3 registers as global.family.david.home.my_pc.
dev_B2C8 requests my_pc in the same scope and receives my_pc_temp_B2C8.
```

### Milestone 3: Traffic Works

Goal: move symbolic packets through a route graph.

Deliverables:

```text
TrafficHub
Neighbor Table
Direct Attachment Table
Route Table
select_route()
forward_packet()
basic route cost
packet forwarding logs
```

Success check:

```text
A packet moves from Device A through Hub 1, Hub 2, and Hub 3 to Device B.
```

### Milestone 4: Logical Lanes Work

Goal: model persistent identity-bound connections.

Deliverables:

```text
LogicalLane
lane_open
lane_open_ack
lane states
sequence numbers
acknowledgments
basic data packet forwarding
```

Success check:

```text
Device A opens lane_001 to Device B, sends packet 1, and receives ack 1.
```

### Milestone 5: Checkpoints Work

Goal: track liveness and state.

Deliverables:

```text
CheckpointPacket
checkpoint tiers
record_checkpoint()
missed checkpoint detection
online, idle, active, timed_out, offline states
```

Success check:

```text
A Tier 2 mobile device updates frequently.
A Tier 0 sensor remains valid with sparse checkpoints.
```

### Milestone 6: Relocation Works

Goal: pause and resume lanes during movement.

Deliverables:

```text
mark_in_transit()
flow_hold
pause_lane_for_relocation()
MoveContract symbolic record
update_attachment()
relocation_resume
resume_lane_after_relocation()
resume sequence behavior
```

Success check:

```text
Device B moves from Hub 3 to Hub 4.
Sender pauses while B is in_transit.
Lane resumes from the correct sequence after B registers at Hub 4.
```

### Milestone 7: Symbolic Security Failures Work

Goal: model trust failure outcomes before real cryptography.

Deliverables:

```text
passport_valid flag
issuer_trusted flag
rolling_proof_valid flag
auth_tag_valid flag
quarantine state
security event log
MAC spoof symbolic scenario
```

Success check:

```text
A spoofed actor claiming dev_A9F3 fails rolling proof and is quarantined.
```

### Milestone 8: Metrics and Growth Recommendations Work

Goal: detect routing pressure and recommend growth.

Deliverables:

```text
lookup counts
route counts
cross-tree traffic count
lane pause count
relocation count
congestion score
traffic bridge recommendation
registry split recommendation
```

Success check:

```text
Repeated traffic between home and office branches produces a create_traffic_bridge recommendation.
```

## Documentation

The following design documents should live in `docs/` and remain the source of truth until superseded:

1. `docs/ARCHITECTURE_v0_1.md`
2. `docs/DARWIN_Design_Dossier_v0_1.md`
3. `docs/DARWIN_Identity_Trust_Authentication_v0_1.md`
4. `docs/DARWIN_Packet_Checkpoint_Lane_Protocol_v0_1.md`
5. `docs/DARWIN_Registry_Hub_Data_Model_v0_1.md`
6. `docs/DARWIN_Traffic_Hub_Routing_Model_v0_1.md`
7. `docs/DARWIN_Simulator_Build_Plan_v0_1.md`

For a concise command-by-command demo path, see `docs/DEMO_GUIDE_v0_1.md`.

For development setup, local validation commands, and v0.1 contribution
constraints, see `docs/DEVELOPMENT.md`.

For v0.1 release notes, see `docs/RELEASE_NOTES_v0_1.md`.

For v0.2 development docs, see:

- `docs/V0_2_ROADMAP.md`
- `docs/SCENARIO_DSL_v0_2.md`
- `docs/SCENARIO_INDEX.md`
- `docs/VISUALIZATION_v0_2.md`
- `docs/TRACE_EXPORT_v0_2.md`
- `docs/RELEASE_NOTES_v0_2.md`

For the v0.3 auth bridge, see:

- `docs/AUTH_BRIDGE_v0_3.md`
- `docs/V0_3_ROADMAP.md`
- `docs/RELEASE_NOTES_v0_3.md`

For v0.4 move-contract auth, see:

- `docs/V0_4_ROADMAP.md`
- `docs/MOVE_CONTRACT_AUTH_v0_4.md`
- `docs/RELEASE_NOTES_v0_4.md`

For v0.5 alias registry behavior, see:

- `docs/V0_5_ROADMAP.md`
- `docs/ALIAS_REGISTRY_v0_5.md`
- `docs/RELEASE_NOTES_v0_5.md`

For v0.6 alias authority chain behavior, see:

- `docs/V0_6_ROADMAP.md`
- `docs/ALIAS_AUTHORITY_CHAIN_v0_6.md`
- `docs/RELEASE_NOTES_v0_6_DRAFT.md`

For v0.7 history, audit, and trace explainability behavior, see:

- `docs/V0_7_ROADMAP.md`
- `docs/REGISTRY_HISTORY_QUERIES_v0_7.md`
- `docs/AUTHORITY_AUDIT_TRACES_v0_7.md`
- `docs/TRACE_EXPLAINABILITY_v0_7.md`

For v0.8 retained authority outcome behavior, see:

- `docs/V0_8_ROADMAP.md`
- `docs/AUTHORITY_OUTCOME_RETENTION_v0_8.md`
- `docs/AUTHORITY_OUTCOME_QUERIES_v0_8.md`
- `docs/RELEASE_NOTES_v0_8_DRAFT.md`

For v0.9 mailbox/chat adapter planning, see:

- `docs/V0_9_ROADMAP.md`
- `docs/LANE_SIGNATURES_v0_9.md`
- `docs/LANE_REGISTRY_v0_9.md`
- `docs/MAILBOX_ADDRESSING_v0_9.md`
- `docs/MAILBOX_REGISTRY_v0_9.md`
- `docs/ADAPTER_ENDPOINTS_v0_9.md`
- `docs/MESSAGE_DELIVERY_v0_9.md`

## What v0.1 Is Not

DARWIN simulator v0.1 is not:

- a replacement for TCP/IP
- a VPN
- a real router
- a real authentication system
- a production security library
- a DNS replacement
- a kernel module
- a packet capture tool
- a cryptography experiment
- a deployable network product

The v0.1 simulator is a behavioral model. It should prove whether the state machines, tables, events, and flows make sense.

## Future Phases

### Future Phase: Real Cryptography

Replace symbolic fields with standard, reviewed mechanisms:

```text
public-key signatures for passports and move contracts
HMAC or CMAC-style local session proofs
counter, nonce, timestamp, and epoch replay protection
auth tags for packet and checkpoint validation
revocation checks
key rotation behavior
```

Avoid custom cryptography. The simulator can model crypto concepts first, but production phases should use well-reviewed standard constructions.

### Future Phase: Localhost Prototype

Run hubs as local processes communicating over HTTP, WebSocket, or TCP.

Demonstrate:

```text
device registration
name conflict handling
move contract creation
in_transit pause/resume
checkpoint updates
route updates
```

### Future Phase: LAN Overlay Prototype

Use existing IP networking for physical delivery while DARWIN handles identity, registry behavior, movement, checkpoints, and logical lanes above it.

### Future Phase: DNS / URL Compatibility

Explore aliases such as:

```text
example.com -> darwin://global.registry.us.hostingcluster7.webnode3.example_service
```

This would remain a future compatibility experiment. v0.5 DNS-style alias
bundles are simulator-local naming records only, not real DNS integration or a
public DNS replacement.

## Design Rules

Keep these rules close while building:

```text
Identity is stable. Attachment is temporary.
Device labels are scoped. Device IDs are durable.
Registry paths and traffic paths may diverge.
Registry Hubs manage identity and authority.
Traffic Hubs manage movement and lane behavior.
Passports are for cross-network identity.
Local rolling proof is for same-network continuity.
Move Contracts record verified relocation.
Checkpoints report liveness and state.
Logical Lanes belong to authenticated device identities.
Pause senders during relocation instead of growing unbounded buffers.
Model behavior first. Add real cryptography and real networking later.
```

## License

MIT. See `LICENSE`.

## Project Note

DARWIN is a thought experiment and prototype architecture. It should be developed with careful skepticism, observable simulations, and small testable milestones. The goal is not to claim a finished system. The goal is to build a clean playground where the model can prove, break, and refine itself.
