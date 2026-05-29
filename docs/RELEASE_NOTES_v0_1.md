# DARWIN Simulator v0.1.0 Release Notes

DARWIN simulator v0.1.0 is the first behavioral release of the Direct-Access Registration Window Interface Network model. It is a deterministic, simulator-first Python prototype for exploring identity-aware registration, scoped names, symbolic traffic routing, logical lanes, checkpoints, relocation, symbolic trust behavior, metrics, growth recommendations, and YAML scenario execution.

## What It Supports

- Scoped Registry Hub registration and same-scope label conflict handling.
- Durable device IDs, local labels, passports, attachment records, and registry summaries.
- Traffic Hub route selection, direct attachments, and symbolic packet delivery.
- Logical lane open/send behavior with sequence and acknowledgment state.
- Checkpoint recording, checkpoint tiers, and timeout state helpers.
- Relocation flow with `in_transit`, lane pause, symbolic move contracts, attachment updates, reroute, and lane resume.
- Symbolic rolling-proof failure, quarantine, and invalid packet/checkpoint auth-tag rejection.
- Metrics and advisory growth recommendations, including `create_traffic_bridge`.
- YAML/JSON scenario validation, execution, event logs, assertions, and deterministic final snapshots.
- CLI commands for listing, validating, and running scenarios.

## What It Intentionally Does Not Support

- Real networking, sockets, packet capture, DNS integration, kernel routing, or network stack integration.
- Production cryptography, signatures, HMACs, CMACs, key management, counters, replay protection, or security claims.
- Real authentication or authorization decisions.
- Async behavior, distributed hub processes, web UI, persistence, package publishing, or automatic releases.
- Automatic topology mutation from recommendations.

## Run The Demo

Install development and CLI dependencies:

```bash
python -m pip install -e ".[dev,cli]"
```

List scenarios:

```bash
python -m darwin.cli.main list-scenarios
```

Run the recommended demo scenarios:

```bash
python -m darwin.cli.main run scenarios/001_basic_registration.yaml
python -m darwin.cli.main run scenarios/004_relocation_pause_resume.yaml --dump-snapshot
python -m darwin.cli.main run scenarios/006_mac_spoof_symbolic_failure.yaml
python -m darwin.cli.main run scenarios/007_congestion_bridge_recommendation.yaml
```

The same commands are available through `darwin-sim` when the console script is on your PATH.

## Verify The Release Locally

```bash
python -m pytest
python -m ruff check .
python scripts/run_all_scenarios.py
python -m darwin.cli.main list-scenarios
python -m darwin.cli.main validate-scenario scenarios/001_basic_registration.yaml
```

Expected result: tests pass, Ruff reports no issues, all checked-in scenarios pass, scenario listing prints the six v0.1 YAML files, and the basic registration scenario validates as `VALID`.

## Known Limitations

- Simulator time is deterministic and integer-based; there is no wall-clock scheduling.
- Scenario validation is intentionally lightweight in v0.1.
- Route costs are simple and symbolic.
- Recommendations are advisory records only.
- Symbolic auth fields are booleans used to exercise state transitions.
- Snapshots and event logs are stable enough for demos and tests, but not yet a formal export format.
