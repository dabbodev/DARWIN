# DARWIN v0.1 Architecture Overview

DARWIN v0.1 is a deterministic, in-memory behavioral simulator for Direct-Access Registration Window Interface Network concepts. It models durable device identities, scoped registration, symbolic traffic movement, checkpoint state, relocation pause/resume, symbolic trust failure handling, metrics, growth recommendations, and YAML/JSON scenario execution without implementing production networking, cryptography, DNS, async services, or kernel integration.

## Layer Map

### Registry Layer

The Registry layer owns scoped identity state. `RegistryHub` records local labels, durable device IDs, passports, current attachment hints, conflicts, checkpoint state, move history, quarantines, security events, and registry metrics.

### Traffic Layer

The Traffic layer owns symbolic packet movement. `TrafficHub` records neighboring hubs, direct device attachments, selected routes, packet forwarding results, route failures, and traffic metrics.

### Lane Layer

The Lane layer models identity-bound logical flows between source and target devices. A `LogicalLane` tracks lane state, current route, sequence counters, acknowledgments, and relocation pause/resume state.

### Checkpoint Layer

The Checkpoint layer records symbolic liveness and device state updates. Checkpoints are tiered, use simulated timestamps, and can be rejected for unknown devices, invalid symbolic auth tags, or unsupported states.

### Relocation Layer

The Relocation layer coordinates simulated movement between registry and traffic attachments. Registry operations mark devices `in_transit`, create symbolic move contracts, and update attachment state. Traffic operations pause active lanes, hold new sends, recalculate routes, and resume lanes after relocation.

### Symbolic Trust/Quarantine Layer

The symbolic trust layer models authentication outcomes without real cryptography. Passport, issuer, rolling-proof, and packet/checkpoint auth-tag fields are boolean simulator inputs. Failures can reject operations, log security events, or quarantine claimed device IDs.

### Metrics/Recommendation Layer

The metrics layer records registry lookups, conflicts, checkpoint updates, packet movement, route failures, lane operations, relocation pressure, symbolic auth failures, and cross-tree traffic. Recommendation helpers produce advisory growth records such as `create_traffic_bridge`.

### Scenario Runner Layer

The scenario runner loads YAML or JSON scenarios, validates their shape, builds a deterministic `World`, executes supported step actions, advances simulated time, evaluates assertions, returns event logs, and emits deterministic final snapshots.

## Key Data Flows

### Registration

A scenario or caller creates a `Device`, selects a `RegistryHub`, and calls `register_device`. The registry optionally evaluates symbolic auth/passport state, assigns the requested scoped label or a temporary conflict label, stores passport and local device records, updates attachment state, refreshes metrics, and mutates the device's current registry state.

### Lane Open/Send

A device must be directly attached to the starting `TrafficHub`. `open_lane` selects a symbolic route to the target device, creates an active `LogicalLane`, and records lane metrics. `send_lane_data` checks that the lane is active, creates a symbolic packet with the next sequence number, forwards it through the route graph, and advances sent/acknowledged sequence counters only after delivery.

### Checkpoint Update

`record_checkpoint` receives a symbolic checkpoint packet at a `RegistryHub`. The registry verifies that the device is known, the auth tag is symbolically valid, and the state is supported. It then records the checkpoint tier, last and expected next simulated times, optional device metadata, and current registry attachment state.

### Relocation Pause/Resume

`mark_in_transit` updates registry and device state for movement. `pause_lanes_for_relocation` marks active lanes involving the relocating device as `paused_relocation` and creates flow-control records. `move_device` creates a symbolic move contract, updates registry attachment, moves the traffic attachment, and registers the device in the new scope if needed. `resume_lanes_after_relocation` recalculates routes and restores affected lanes to active state when a route is available.

### Symbolic Trust Failure/Quarantine

Symbolic proof checks accept explicit simulator booleans. When `verify_rolling_proof` receives `proof_valid: false`, it creates or refreshes quarantine state, updates related registry checkpoint/attachment state when present, logs a high-severity security event, and returns a failed result. Invalid packet or checkpoint auth tags are rejected through their traffic or registry paths.

### Growth Recommendation

Traffic metrics can record repeated cross-tree packet pressure. `recommend_traffic_bridge` compares the counter to the active policy threshold and, when exceeded, stores a deterministic advisory `create_traffic_bridge` recommendation with affected hubs, branches, reason, confidence, and admin-approval status. v0.1 recommendations are advisory only and do not mutate topology.

## v0.1 Constraints

- Simulated networking only; packets move through in-memory hub objects.
- Symbolic authentication only; trust fields are simulator inputs.
- No production cryptography, signatures, HMACs, CMACs, key management, counters, or replay protection.
- No DNS integration or DNS replacement behavior.
- No kernel, driver, router, packet capture, or network stack integration.
- Deterministic simulated time; no async runtime or wall-clock scheduling.
