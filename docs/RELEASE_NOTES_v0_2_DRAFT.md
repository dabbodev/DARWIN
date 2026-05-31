# DARWIN Simulator v0.2.0 Draft Release Notes

DARWIN simulator v0.2.0 is the active development release for the
Direct-Access Registration Window Interface Network model. It builds on v0.1 by
making scenarios easier to validate, reuse, inspect, and export while keeping
the simulator deterministic, in-memory, and simulator-only.

## What v0.2 Adds Over v0.1

- Structured scenario validation with field locations and suggestions.
- Polished JSON exports for snapshots, event logs, and scenario run results.
- Route-cost routing and routing policy support for deterministic symbolic routing.
- Mermaid text export for topology and logical lane inspection.
- Additional relocation edge-case scenarios and regression coverage.
- Timeline trace export in JSON and Markdown formats.
- Built-in scenario setup presets.
- Scenario metadata, generated scenario index output, and scenario description CLI support.

## How To Run

Install development and CLI dependencies:

```bash
python -m pip install -e ".[dev,cli]"
```

Run tests:

```bash
python -m pytest
```

Run Ruff:

```bash
python -m ruff check .
```

Run all checked-in scenarios:

```bash
python scripts/run_all_scenarios.py
```

Generate the scenario index:

```bash
python -m darwin.cli.main scenario-index
```

Describe a scenario:

```bash
python -m darwin.cli.main describe-scenario scenarios/011_preset_lane_demo.yaml
```

Expand a preset-backed scenario:

```bash
python -m darwin.cli.main expand-scenario scenarios/011_preset_lane_demo.yaml
```

Export Mermaid topology text:

```bash
python -m darwin.cli.main run scenarios/004_relocation_pause_resume.yaml --export-mermaid tmp_v02.mmd
```

Export timeline traces:

```bash
python -m darwin.cli.main run scenarios/004_relocation_pause_resume.yaml --export-timeline-md tmp_v02.md --export-timeline-json tmp_v02.json
```

The export flags can be combined in one run:

```bash
python -m darwin.cli.main run scenarios/004_relocation_pause_resume.yaml --export-mermaid tmp_v02.mmd --export-timeline-md tmp_v02.md --export-timeline-json tmp_v02.json
```

## Compatibility Notes

- v0.1 scenarios still validate and pass.
- Scenario runs remain deterministic for the same input file.
- DARWIN v0.2 is still a simulator-only prototype.
- Authentication behavior remains symbolic unless explicitly stated otherwise.
- There is no real networking, socket transport, packet capture, DNS integration, kernel integration, or distributed hub runtime.
- There is no production cryptography, key management, replay protection, or security guarantee.

## Known Limitations

- Mermaid export is plain text; the simulator does not render images or provide a web UI.
- Timeline export adapts the existing event log and is intended for observability, not distributed tracing.
- Route costs are symbolic simulator inputs, not measured network latency or throughput.
- Scenario presets are convenience expansions, not a separate runtime configuration layer.
- Recommendations remain advisory records only and do not mutate topology automatically.
- The optional HMAC-style auth bridge remains a candidate, not a completed production security feature.

## Suggested Upgrade Notes

- Existing v0.1 scenario files can continue to run without presets.
- Add optional scenario metadata when a scenario should appear clearly in generated indexes.
- Use presets for repeated setup only when they make the scenario easier to read.
- Prefer JSON exports for automated inspection and Markdown or Mermaid exports for review notes.
- Keep documentation and demos clear that v0.2 remains a behavioral simulator rather than deployable network infrastructure.
