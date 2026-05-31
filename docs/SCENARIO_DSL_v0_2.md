# DARWIN Scenario DSL v0.2

v0.2 adds optional built-in setup presets to reduce repeated YAML in simulator
scenarios. Presets expand to ordinary `setup` data before validation and before
the deterministic runner creates the world.

## Presets

Use presets with a top-level `use` list:

```yaml
scenario_id: 011_preset_lane_demo
name: Preset lane demo
use:
  - two_branch_network
steps:
  - action: open_lane
    source: dev_A9F3
    target: dev_B2C8
    traffic_hub: hub_1
    lane_id: lane_001
assertions:
  - type: lane_state
    traffic_hub: hub_1
    lane: lane_001
    expected: active
```

Available built-in presets:

| Preset | Purpose |
| --- | --- |
| `single_home_network` | One hybrid home hub with two common devices. |
| `two_branch_network` | Home and office registries, three traffic hubs, and home-to-office links. |
| `relocation_network` | Home and office registries with a relocation target traffic hub. |

List them from the CLI:

```powershell
python -m darwin.cli.main list-presets
```

## Expansion

Expansion is deterministic and uses plain setup data:

```powershell
python -m darwin.cli.main expand-scenario scenarios/011_preset_lane_demo.yaml
```

If PyYAML is installed, the command prints YAML. Otherwise it prints JSON.

## Merge Rules

Explicit scenario setup extends preset setup. For these list-based sections,
entries with the same key replace preset entries:

| Section | Merge key |
| --- | --- |
| `devices` | `device_id` |
| `registry_hubs` | `hub_id` |
| `traffic_hubs` | `hub_id` |
| `hybrid_hubs` | `hub_id` |
| `links` | `from`, `to` |

Example override:

```yaml
use:
  - two_branch_network
setup:
  devices:
    - device_id: dev_A9F3
      label: tablet
      registry_hub: registry_home
      traffic_hub: hub_1
```

`dev_A9F3` keeps the preset placement but uses the explicit device entry.

Unknown preset names fail validation at `use[n]`. Existing scenarios that do
not use presets remain valid and run through the same setup path as before.

## Library Metadata

Scenarios can include optional top-level metadata for discovery and generated
documentation:

```yaml
category: relocation
description: Pauses a lane during relocation and resumes it on the new route.
tags:
  - relocation
  - lane
demonstrates:
  - Lane pause and resume behavior during relocation.
expected_result: The lane returns to active state.
```

Supported categories are `registry`, `traffic`, `lane`, `relocation`,
`security`, `metrics`, `preset`, and `visualization`. Unknown categories warn
during validation instead of failing.

List scenario metadata from the CLI:

```powershell
python -m darwin.cli.main list-scenarios
```

Describe one scenario:

```powershell
python -m darwin.cli.main describe-scenario scenarios/004_relocation_pause_resume.yaml
```

Generate the Markdown index:

```powershell
python -m darwin.cli.main scenario-index
```
