# DARWIN v0.1 Demo Guide

DARWIN v0.1 is a deterministic, simulator-first prototype. It uses in-memory
state, simulated time, symbolic authentication, and symbolic packet movement.
It does not use real networking, real cryptography, external services, DNS, or
kernel/network-stack integration.

## Setup

Install the package with development and CLI dependencies:

```bash
pip install -e ".[dev,cli]"
```

Run the full regression suite:

```bash
python -m pytest
```

Run Ruff:

```bash
python -m ruff check .
```

## Scenario Commands

List available scenarios:

```bash
python -m darwin.cli.main list-scenarios
```

Validate a scenario without running it:

```bash
python -m darwin.cli.main validate-scenario scenarios/001_basic_registration.yaml
```

Run basic registration:

```bash
python -m darwin.cli.main run scenarios/001_basic_registration.yaml
```

Run relocation pause/resume:

```bash
python -m darwin.cli.main run scenarios/004_relocation_pause_resume.yaml
```

Run symbolic spoof failure:

```bash
python -m darwin.cli.main run scenarios/006_mac_spoof_symbolic_failure.yaml
```

Run growth recommendation:

```bash
python -m darwin.cli.main run scenarios/007_congestion_bridge_recommendation.yaml
```

Run a scenario with the final deterministic snapshot:

```bash
python -m darwin.cli.main run scenarios/004_relocation_pause_resume.yaml --dump-snapshot
```

Run every checked-in YAML scenario with a compact pass/fail summary:

```bash
python scripts/run_all_scenarios.py
```

## Demo Flow

1. Start with `001_basic_registration.yaml` to show a device registering under
   a scoped Registry Hub and resolving its local label.
2. Use `004_relocation_pause_resume.yaml` to show an active logical lane pause
   while the target device is in transit, then resume after the move.
3. Use `006_mac_spoof_symbolic_failure.yaml` to show symbolic rolling-proof
   failure and quarantine behavior.
4. Use `007_congestion_bridge_recommendation.yaml` to show repeated cross-tree
   traffic producing an advisory `create_traffic_bridge` recommendation.

The `--dump-snapshot` flag is useful when explaining final simulator state:
devices, hubs, lanes, registry records, quarantines, and recommendations are
rendered as deterministic JSON.
