# DARWIN Development

DARWIN v0.1 is a deterministic simulator. Development should keep the repo
self-checking with tests, Ruff, scenario validation, and all-scenario
regression runs.

## Requirements

- Python 3.11 or 3.12
- `pip`
- No external services are required for v0.1 development

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

Validate one scenario without executing it:

```bash
python -m darwin.cli.main validate-scenario scenarios/001_basic_registration.yaml
```

Run every checked-in YAML scenario:

```bash
python scripts/run_all_scenarios.py
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
5. Update README or docs when the visible v0.1 behavior changes.

## v0.1 Constraints

- No real networking, sockets, DNS integration, kernel routing, or packet
  capture.
- No production cryptography, key management, signatures, HMACs, CMACs,
  counters, replay protection, or security claims.
- Symbolic authentication and trust behavior only.
- Simulated time only; no async behavior or wall-clock scheduling.
