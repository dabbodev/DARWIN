# Authority Outcome Queries v0.8

DARWIN v0.8 Sprint 2 adds read-only query helpers for authority-chain outcome
records retained by Sprint 1. The purpose is to inspect compact retained
provenance after a claim attempt has completed, including outcomes that do not
leave a granted alias record behind.

This is simulator bookkeeping only. It is not production audit or compliance
infrastructure, and it does not add external services, DNS, registrar
integration, public CA behavior, production identity proof, or a broad event
store.

## Relationship to Sprint 1 Retention

Sprint 1 introduced `AliasAuthorityOutcomeRecord` entries retained in:

```python
RegistryHub.authority_outcome_history
```

Sprint 2 adds a read-only helper:

```python
query_authority_outcomes(
    registry_hub,
    *,
    requested_alias=None,
    granted_alias=None,
    device_id=None,
    requesting_hub=None,
    final_status=None,
    status=None,
    reason=None,
    authority_ceiling=None,
    fallback_used=None,
    conflict_detected=None,
    policy_denied=None,
    path_broken=None,
)
```

The helper reads retained records from the supplied `RegistryHub`, applies only
the filters that are provided, and returns deterministic results in retained
append order. It does not mutate the hub, retained records, aliases, conflicts,
events, or scenario results.

## Supported Filters

- `requested_alias`: original alias requested by the claim.
- `granted_alias`: alias that was actually granted, when any.
- `device_id`: target device retained as `target_device`.
- `requesting_hub`: hub that initiated the authority-chain claim.
- `final_status`: terminal authority-chain status, such as `approved_here`,
  `fallback_granted`, `name_taken`, `policy_denied`, or
  `authority_path_broken`.
- `status`: returned claim status, such as `claimed`, `fallback_granted`,
  `conflict`, `rejected`, or `authority_path_broken`.
- `reason`: retained terminal reason.
- `authority_ceiling`: last authority scope reached for the outcome.
- `fallback_used`: boolean fallback outcome marker.
- `conflict_detected`: boolean conflict marker.
- `policy_denied`: boolean simulator-local policy denial marker.
- `path_broken`: boolean broken authority path marker.

Filters are additive. If no retained outcomes match all supplied filters, the
helper returns an empty list.

## Example Usage

```python
from darwin.registry.history_queries import query_authority_outcomes

fallbacks = query_authority_outcomes(
    registry_hub,
    device_id="dev_A9F3",
    fallback_used=True,
)

for outcome in fallbacks:
    print(outcome.to_dict())
```

## Example Output

Query results are compact dataclasses with deterministic JSON-safe
`to_dict()` output:

```json
{
  "record_id": "authority_outcome:registry_child_001:0002",
  "requested_alias": "global.server",
  "granted_alias": "global.family.david.server",
  "target_device": "dev_A9F3",
  "requesting_hub": "registry_child_001",
  "authority_ceiling": "global.family.david",
  "final_status": "fallback_granted",
  "status": "fallback_granted",
  "reason": "insufficient_authority",
  "decision_count": 2,
  "path_hubs": [
    "registry_child_001",
    "registry_family_001"
  ],
  "decisions": [
    {
      "hub_id": "registry_child_001",
      "scope_path": "global.family.david.home",
      "decision": "continue_upward",
      "reason": "insufficient_authority",
      "alias": "global.server",
      "fallback_alias": null,
      "authority_ceiling": "global.family.david.home",
      "can_continue_upward": true
    },
    {
      "hub_id": "registry_family_001",
      "scope_path": "global.family.david",
      "decision": "fallback_available",
      "reason": "insufficient_authority",
      "alias": "global.server",
      "fallback_alias": "global.family.david.server",
      "authority_ceiling": "global.family.david",
      "can_continue_upward": false
    }
  ],
  "fallback_used": true,
  "conflict_detected": false,
  "policy_denied": false,
  "path_broken": false
}
```

## Retention Location

Authority outcome records are retained only on the starting/requesting
`RegistryHub`. They are not duplicated across every hub in the authority path.

Successful and fallback grants may also leave v0.7 terminal provenance on
granted `AliasRecord` objects at the approving authority hub. Failed outcomes
such as conflicts, simulator-local policy denials, and broken paths are
queryable through `authority_outcome_history` on the requesting hub.

## Retained Records vs. AliasAuthorityPath

`AliasAuthorityPath` remains the in-memory ordered path attached to an
individual authority-chain claim result. It is the richest immediate object for
explaining that one action result.

`AliasAuthorityOutcomeRecord` is a compact retained summary copied from the
path and final claim result. It exists so callers can query outcomes later from
the requesting `RegistryHub` without still holding the original in-memory
result.

The query helper reads the retained summaries. It does not recreate an
`AliasAuthorityPath` and does not mutate the original path or retained record.

## Relationship to v0.7 Helpers

The v0.7 query, audit, and explanation helpers remain unchanged:

- `query_alias_history(...)` reads retained alias records.
- `query_alias_conflicts(...)` reads retained alias conflict records.
- `query_authority_decisions(...)` reads terminal grant provenance from
  retained alias records.
- `query_quarantine_events(...)` reads retained quarantine records.
- `build_authority_audit_trace(...)` continues to summarize retained
  successful and fallback grants from alias records.
- `summarize_authority_path(...)` and `explain_authority_trace(...)` continue
  to work with in-memory path summaries and audit trace summaries.

`query_authority_outcomes(...)` is the v0.8 helper for retained authority
outcome summaries, including failed authority paths.

## Relationship to Scenario Assertions

Sprint 3 adds the read-only scenario assertion
`authority_outcome_history_contains`. It calls
`query_authority_outcomes(...)`, applies the same filter fields, and validates
retained records on the requesting `RegistryHub`. The assertion does not add
scenario actions, mutate retained records, or change authority-chain runtime
behavior.

## Limitations

- Simulator-local only.
- No production audit or compliance guarantee.
- No external storage or services.
- No broad event store.
- No real DNS behavior.
- No registrar integration.
- No public CA behavior.
- No production identity proof.
- No TrafficHub routing changes.
- No canonical identity rewrite.
- No scenario DSL actions.
- No snapshot or export expansion yet.
