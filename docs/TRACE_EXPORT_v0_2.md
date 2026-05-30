# DARWIN v0.2 Timeline Trace Export

DARWIN can export deterministic scenario timelines for simulator observability.
Timeline export adapts the existing in-memory event log; it does not mutate world
state, add networking behavior, render images, or introduce external dependencies.

## CLI Usage

```powershell
python -m darwin.cli.main run scenarios/003_lane_open_and_send.yaml `
  --export-timeline-json trace.json `
  --export-timeline-md trace.md
```

Optional trace filters can be combined with either timeline export:

- `--trace-event-type EVENT_TYPE`
- `--trace-device DEVICE_ID`
- `--trace-lane LANE_ID`
- `--trace-hub HUB_ID`

Existing exports still work and can be used in the same run:

```powershell
python -m darwin.cli.main run scenarios/004_relocation_pause_resume.yaml `
  --export-snapshot snapshot.json `
  --export-events events.json `
  --export-result result.json `
  --export-mermaid topology.mmd `
  --export-timeline-json trace.json `
  --export-timeline-md trace.md `
  --trace-lane lane_001
```

## Python Usage

```python
from darwin.sim.runner import run_scenario
from darwin.sim.timeline import scenario_result_to_timeline, timeline_to_markdown

result = run_scenario("scenarios/003_lane_open_and_send.yaml")
timeline = scenario_result_to_timeline(result)
markdown = timeline_to_markdown(timeline, title=f"Timeline: {result.scenario_id}")
```

## Timeline Shape

Each record includes stable core fields:

- `time`
- `event_type`
- `actor`
- `target`
- `device_id`
- `hub_id`
- `lane_id`
- `status`
- `message`
- `data`

Fields such as `device_id`, `lane_id`, and `hub_id` are optional because not all
events are tied to the same simulator entity. The `message` field preserves the
readable log text, while `data` carries structured details such as routes,
sequence counters, relocation lanes, conflict identifiers, and reasons.

JSON exports are UTF-8, sorted-key, JSON-safe values only. Markdown exports use a
concise timeline table and include failed assertions when a scenario runs but
does not pass its assertions.
