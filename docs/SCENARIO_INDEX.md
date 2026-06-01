# DARWIN Scenario Index

Scenarios are deterministic, support presets through `use`, and are simulator-only.

| Scenario | Category | Description | Tags |
| --- | --- | --- | --- |
| `001_basic_registration` - Basic registration | registry | Registers one device, resolves its label, and confirms the registry event. | `registration`, `label`, `checkpoint` |
| `002_name_conflict` - Name conflict | registry | Registers two devices with the same label and records the deterministic conflict handling. | `registration`, `label-conflict`, `conflict` |
| `003_lane_open_and_send` - Lane open and send | lane | Opens a logical lane across traffic hubs and sends one payload. | `lane`, `traffic`, `sequence` |
| `004_relocation_pause_resume` - Relocation pause and resume | relocation | Pauses a lane during relocation, moves the target device, and resumes traffic on the new route. | `relocation`, `lane`, `flow-control` |
| `005_relocation_timeout` - Relocation timeout keeps lane held | relocation | Expires a relocation hold and verifies that traffic remains paused after timeout. | `relocation`, `timeout`, `flow-control` |
| `006_mac_spoof_symbolic_failure` - Symbolic spoof failure | security | Rejects an invalid symbolic rolling proof and quarantines the device. | `symbolic-trust`, `spoofing`, `quarantine` |
| `007_congestion_bridge_recommendation` - Congestion bridge recommendation | metrics | Records sustained cross-tree traffic and proposes a traffic bridge recommendation. | `metrics`, `recommendation`, `cross-tree-traffic` |
| `008_invalid_move_contract` - Invalid move contract keeps relocation paused | relocation | Rejects an invalid move contract and keeps relocation flow control active. | `relocation`, `move-contract`, `validation` |
| `009_duplicate_device_claim` - Duplicate device claim during relocation | security | Simulates a duplicate device claim while relocation is paused. | `relocation`, `duplicate-device`, `conflict` |
| `010_unreachable_relocation_resume` - Unreachable relocation resume keeps flow control | relocation | Attempts to resume relocation traffic when the moved target has no reachable route. | `relocation`, `routing`, `flow-control` |
| `011_preset_lane_demo` - Preset lane demo | preset | Uses a built-in two-branch setup preset to open a lane with minimal YAML. | `preset`, `lane`, `two-branch-network` |
| `012_hmac_checkpoint_success` - HMAC checkpoint success | security | Records a test-only HMAC-authenticated checkpoint. | `hmac`, `checkpoint`, `simulator-only` |
| `013_hmac_packet_auth_failure` - HMAC packet auth failure | security | Rejects a lane packet with a tampered test-only HMAC tag. | `hmac`, `packet-auth`, `simulator-only` |
