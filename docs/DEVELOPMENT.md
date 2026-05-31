# DARWIN v0.2 Development

DARWIN v0.2 is the active simulator development branch. Development should keep
the repo self-checking with tests, Ruff, scenario validation, export sanity
checks, and all-scenario regression runs.

## Requirements

- Python 3.11 or 3.12
- `pip`
- No external services are required for simulator development

## Local Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
```

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

Install the package in editable mode with development and CLI dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev,cli]"
```

## Run Tests

```bash
python -m pytest
```

## Run Ruff

```bash
python -m ruff check .
```

## Run All Scenarios

List available scenarios:

```bash
python -m darwin.cli.main list-scenarios
```

List built-in scenario presets:

```bash
python -m darwin.cli.main list-presets
```

Generate the scenario index:

```bash
python -m darwin.cli.main scenario-index
```

Validate one scenario without executing it:

```bash
python -m darwin.cli.main validate-scenario scenarios/001_basic_registration.yaml
```

Describe a scenario without running it:

```bash
python -m darwin.cli.main describe-scenario scenarios/011_preset_lane_demo.yaml
```

Expand a preset-backed scenario:

```bash
python -m darwin.cli.main expand-scenario scenarios/011_preset_lane_demo.yaml
```

Run every checked-in YAML scenario:

```bash
python scripts/run_all_scenarios.py
```

Export Mermaid topology text:

```bash
python -m darwin.cli.main run scenarios/004_relocation_pause_resume.yaml --export-mermaid tmp_v02.mmd
```

Export timeline traces:

```bash
python -m darwin.cli.main run scenarios/004_relocation_pause_resume.yaml --export-timeline-md tmp_v02_timeline.md --export-timeline-json tmp_v02_timeline.json
```

The GitHub Actions workflow runs these same checks on push and pull request.

## Add a New Scenario

1. Add a YAML file under `scenarios/` with a stable numeric prefix.
2. Include `scenario_id`, `name`, `setup`, `steps`, and `assertions`.
3. Validate the file with `python -m darwin.cli.main validate-scenario <path>`.
4. Run `python scripts/run_all_scenarios.py`.
5. Add or adjust focused tests if the scenario covers new behavior.

## Add a New Simulator Behavior

1. Keep the behavior deterministic and driven by simulated time.
2. Add focused tests for the model or operation being changed.
3. Add a scenario only when the behavior is useful as an executable demo or
   regression case.
4. Keep CLI output stable enough for demos and regression checks.
5. Update README or docs when visible simulator behavior changes.

## Simulator Constraints

- No real networking, sockets, DNS integration, kernel routing, or packet
  capture.
- No production cryptography, key management, signatures, HMACs, CMACs,
  counters, replay protection, or security claims.
- Symbolic authentication and trust behavior only.
- Simulator-only behavior; no production runtime claims.
- Deterministic simulated time only; no async behavior or wall-clock scheduling.
