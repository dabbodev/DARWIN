# Authority Outcome Retention v0.8

DARWIN v0.8 Sprint 1 adds minimal persistent simulator-local records for
authority-chain outcomes. The goal is to keep enough compact provenance on a
`RegistryHub` to inspect what happened after an authority-chain claim attempt,
including failed paths that v0.7 could only explain from the in-memory
`AliasAuthorityPath` attached to the scenario action result.

This is simulator bookkeeping only. It is not production audit or compliance
infrastructure, and it does not add external services, DNS, registrar
integration, public CA behavior, or production identity proof.

## Retention Location

Authority outcome records are retained on the starting/requesting
`RegistryHub` in:

```python
RegistryHub.authority_outcome_history
```

The requesting hub is the simulator actor that initiated the authority-chain
claim and needs to explain the outcome. Existing v0.7 terminal grant
provenance remains on granted `AliasRecord` objects at the approving authority
hub. Sprint 1 does not duplicate outcome records across every hub in the
authority path.

If the starting hub is missing, there is no local `RegistryHub` available to
retain the outcome.

## Retained Outcomes

Sprint 1 retains one compact `AliasAuthorityOutcomeRecord` for each
`claim_alias_through_authority_chain(...)` attempt when the requesting hub
exists.

Retained outcomes include:

- successful authority approval
- fallback grant
- name-taken conflict
- simulator-local policy denial
- broken parent or path-broken result
- other authority-chain terminal failures, such as blocked devices or
  insufficient authority

Retention preserves deterministic append order and does not change alias
records, conflict records, alias resolution, canonical identity, TrafficHub
routing, or the returned `AliasAuthorityPath`.

## Summary Shape

Each retained record is compact and JSON-safe through `to_summary()` or
`to_dict()`:

```json
{
  "record_id": "authority_outcome:registry_home_001:0001",
  "requested_alias": "global.server",
  "granted_alias": null,
  "target_device": "dev_A9F3",
  "requesting_hub": "registry_home_001",
  "authority_ceiling": "global.family.david",
  "final_status": "policy_denied",
  "status": "rejected",
  "reason": "pass_up_denied_by_policy",
  "decision_count": 2,
  "path_hubs": [
    "registry_home_001",
    "registry_family_001"
  ],
  "decisions": [
    {
      "hub_id": "registry_home_001",
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
      "decision": "policy_denied",
      "reason": "pass_up_denied_by_policy",
      "alias": "global.server",
      "fallback_alias": null,
      "authority_ceiling": "global.family.david",
      "can_continue_upward": false
    }
  ],
  "fallback_used": false,
  "conflict_detected": false,
  "policy_denied": true,
  "path_broken": false
}
```

`record_id` values are deterministic per requesting hub and append order:
`authority_outcome:<hub_id>:0001`, `authority_outcome:<hub_id>:0002`, and so on.

## Relationship to v0.7 Helpers

v0.7 history queries and authority audit traces continue to behave as before:

- `query_authority_decisions(...)` reads terminal grant provenance from
  retained `AliasRecord` data.
- `query_authority_outcomes(...)` reads retained
  `AliasAuthorityOutcomeRecord` summaries from
  `RegistryHub.authority_outcome_history`, including failed paths.
- `build_authority_audit_trace(...)` summarizes retained successful and
  fallback grants from alias records.
- `summarize_authority_path(...)` summarizes an in-memory
  `AliasAuthorityPath`, including failures.
- `explain_authority_trace(...)` can still explain v0.7 trace summaries and
  in-memory path summaries.

Sprint 2 adds read-only query helpers for `authority_outcome_history`. Scenario
assertions are added in Sprint 3 through the read-only
`authority_outcome_history_contains` assertion, which queries retained records
without changing retention or authority-chain behavior.

Sprint 4 exposes retained authority outcome records in detailed world
snapshots under each requesting `RegistryHub`:

```text
registry_hubs.<hub_id>.authority_outcome_history
```

The snapshot entries use the retained record's JSON-safe summary shape and
preserve retained append order. Compact `world.snapshot()` output continues to
list only entity IDs and does not include retained authority outcomes.
Existing scenario JSON snapshot and result exports write the final detailed
snapshot, so they include the same simulator-local retained summaries without
new export flags or external services.

## Retained Record vs. AliasAuthorityPath

`AliasAuthorityPath` remains the ordered in-memory path attached to a claim
result. It is still the richest immediate explanation object for an action
result.

`AliasAuthorityOutcomeRecord` is a compact retained summary copied from the
known path and final claim result. It is stored on the requesting hub so failed
authority outcomes are not lost as soon as callers stop holding the in-memory
result.

The retained record does not replace or mutate the original path.

## Limitations

- Simulator-local only.
- No production audit or compliance guarantee.
- No external storage or services.
- No real DNS behavior.
- No registrar integration.
- No public CA behavior.
- No production identity proof.
- No TrafficHub routing changes.
- No canonical identity rewrite.
- No scenario DSL actions are added by retention, query helpers, or retained
  outcome assertions.
- Query helpers are read-only and simulator-local.
- Detailed snapshot and JSON export visibility is read-only simulator-local
  introspection, not production audit/compliance infrastructure.
