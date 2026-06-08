# DARWIN v0.7 Registry History Queries

Status: unreleased release-prep work on `v0.7/planning`. The current branch
version is `darwin-sim 0.7.0`.

This document describes the v0.7 Sprint 1 read-only RegistryHub history query
helpers. The helpers make simulator state that already exists easier to inspect
from tests, audit/explanation layers, and v0.7 scenario assertions.

The helpers are simulator-only. They do not add external storage, external
services, production audit guarantees, compliance guarantees, real DNS,
registrar integration, public CA behavior, or production identity proof.

## Purpose

RegistryHub already retains several useful history-like records:

- Alias records in `RegistryHub.aliases`, including released aliases that no
  longer resolve.
- Alias conflict records in `RegistryHub.conflicts`.
- Alias authority provenance stored on granted alias records.
- Security events in `RegistryHub.security_events`.
- Active quarantine records in `RegistryHub.quarantines`.

`darwin.registry.history_queries` exposes narrow query helpers over those
existing tables. The helpers are read-only and do not change alias claiming,
alias release, conflict recording, quarantine handling, TrafficHub routing, or
canonical identity.

## Query Helpers

### `query_alias_history(...)`

```python
query_alias_history(registry_hub, alias=None, device_id=None, status=None)
```

Returns `AliasHistoryQueryResult` records from retained alias records.

Supported filters:

- `alias`: exact alias string.
- `device_id`: matches target device or requesting device.
- `status`: exact alias record status, such as `active` or `released`.

Example:

```python
query_alias_history(hub, alias="global.family.david.home.server")
query_alias_history(hub, device_id="dev_A9F3", status="released")
```

### `query_alias_conflicts(...)`

```python
query_alias_conflicts(registry_hub, alias=None, device_id=None)
```

Returns `AliasConflictQueryResult` records for persisted
`alias_conflict` entries.

Supported filters:

- `alias`: exact conflicting alias string.
- `device_id`: matches the existing owner or requesting device.

Example:

```python
query_alias_conflicts(hub, alias="global.family.david.home.server")
query_alias_conflicts(hub, device_id="dev_B2C8")
```

### `query_authority_decisions(...)`

```python
query_authority_decisions(
    registry_hub,
    requested_alias=None,
    granted_alias=None,
    device_id=None,
    final_status=None,
)
```

Returns `AuthorityDecisionQueryResult` records derived from persisted alias
authority provenance on granted alias records.

Supported filters:

- `requested_alias`: original requested alias stored on the alias record.
- `granted_alias`: final granted alias stored on the alias record.
- `device_id`: target device for the granted alias.
- `final_status`: inferred stored grant outcome, currently `approved_here` or
  `fallback_granted`.

Example:

```python
query_authority_decisions(
    hub,
    requested_alias="global.server",
    final_status="fallback_granted",
)
```

Limit: the full ordered authority path is not persisted on RegistryHub after
failed authority-chain attempts. This helper does not fabricate failed
decisions or reconstruct paths that were never stored.

### `query_quarantine_events(...)`

```python
query_quarantine_events(registry_hub, device_id=None, reason=None)
```

Returns `QuarantineEventQueryResult` records from active quarantine records,
with matching security event metadata when an event is available.

Supported filters:

- `device_id`: exact quarantined claimed device ID.
- `reason`: exact quarantine reason.

Example:

```python
query_quarantine_events(hub, device_id="dev_A9F3")
query_quarantine_events(hub, reason="rolling_proof_failed")
```

## Ordering and Results

All helpers return lists. Empty matches return `[]`.

Ordering is deterministic:

- Alias history is sorted by alias string.
- Alias conflicts are sorted by conflict ID.
- Authority provenance is sorted by alias string.
- Quarantine results are sorted by timestamp when present, then device ID and
  quarantine key.

Each result is a small frozen dataclass with a `to_dict()` method for JSON-safe
inspection.

## Scenario Assertions

Sprint 4 wires these helpers into read-only scenario assertions:

- `alias_history_contains` uses `query_alias_history(...)`.
- `alias_conflict_history_contains` uses `query_alias_conflicts(...)`.
- `quarantine_history_contains` uses `query_quarantine_events(...)`.

See `docs/SCENARIO_DSL_v0_2.md` for assertion fields and count behavior.

## Limitations

The v0.7 Sprint 1 helpers intentionally query only data already represented by
the simulator.

Deferred categories:

- A broad append-only registry event store.
- Full ordered authority-chain paths for failed attempts.
- Historical versions of alias records before release or overwrite.
- Historical canonical identity/device registration revisions beyond the
  current local registry records.
- External audit log export, production audit retention, compliance reporting,
  or external service integration.

These helpers support the v0.7 audit trace and explainability layers, not a
production audit subsystem.
