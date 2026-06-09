# DARWIN v0.7 Authority Audit Trace Summaries

Status: released on `main`. The current version is `darwin-sim 0.7.0`.

This document describes the v0.7 Sprint 2 read-only authority audit trace
summary helpers. The helpers expose compact, JSON-safe views of authority-chain
claim decisions and retained alias grant provenance already represented by the
simulator.

These helpers are simulator-only. They do not add external services, external
storage, production audit guarantees, compliance guarantees, real DNS,
registrar integration, public CA behavior, or production identity proof.

## Purpose

v0.6 introduced in-memory authority-chain paths for alias claims. v0.7 Sprint 1
then added read-only RegistryHub history query helpers over retained records.
Sprint 2 builds on those pieces by adding structured audit summaries that are
easy to inspect in tests and future explanation layers.

The helpers live in `darwin.registry.authority_audit`:

- `summarize_authority_decision(decision)`
- `summarize_authority_path(authority_path)`
- `build_authority_audit_trace(registry_hub, ...)`

All helpers are read-only. They do not mutate RegistryHub state, alias records,
authority records, security events, snapshots, or scenario results.

## Relationship to Sprint 1

`build_authority_audit_trace(...)` uses the Sprint 1
`query_authority_decisions(...)` helper. It therefore summarizes only authority
grant provenance currently retained on alias records.

`summarize_authority_path(...)` works with the in-memory
`AliasAuthorityPath` object returned by v0.6 authority-chain evaluation and
claim helpers. It can summarize success, fallback, conflict, policy denial,
blocked-device, insufficient-authority, and broken-parent paths while the
caller still has that result object.

## Example Output Shape

Retained RegistryHub audit traces are compact dictionaries:

```json
[
  {
    "requested_alias": "global.server",
    "granted_alias": "global.us.server",
    "target_device": "dev_A9F3",
    "final_status": "fallback_granted",
    "status": "active",
    "reason": "insufficient_authority",
    "authority_ceiling": "global.us",
    "decision_count": 1,
    "path_hubs": ["registry_us_001"],
    "decisions": [
      {
        "hub_id": "registry_us_001",
        "scope_path": "global.us",
        "status": "fallback_granted",
        "reason": "insufficient_authority",
        "alias": "global.server",
        "fallback_alias": "global.us.server",
        "authority_ceiling": "global.us"
      }
    ],
    "fallback_used": true,
    "conflict_detected": false,
    "policy_denied": false,
    "path_broken": false,
    "summary": "fallback granted at registry_us_001"
  }
]
```

In-memory path summaries include the full decision list when the caller has an
`AliasAuthorityPath`:

```json
{
  "requested_alias": "global.server",
  "granted_alias": null,
  "target_device": "dev_A9F3",
  "final_status": "policy_denied",
  "status": "policy_denied",
  "reason": "pass_up_denied_by_policy",
  "authority_ceiling": "global.family.david",
  "decision_count": 2,
  "path_hubs": ["registry_home_001", "registry_family_001"],
  "fallback_used": false,
  "conflict_detected": false,
  "policy_denied": true,
  "path_broken": false,
  "summary": "denied by simulator-local policy"
}
```

## Available Data

Currently available from retained RegistryHub data:

- Requested alias, granted alias, target device, final grant status, alias
  status, fallback reason, authority ceiling, and approving hub for retained
  alias records.
- Deterministic ordering from the Sprint 1 history query helper.
- Empty lists when no retained matching grant exists.

Currently available from in-memory authority paths:

- Ordered authority decisions.
- Decision count.
- Path hub IDs.
- Final status.
- Terminal reason.
- Flags for fallback, conflict, policy denial, and broken paths.

## Scenario Assertions

Sprint 4 wires retained authority grant traces into
`authority_audit_trace_contains`. The assertion uses
`build_authority_audit_trace(...)` for retained RegistryHub provenance and can
apply deterministic explanation checks through the Sprint 3 explainability
helpers.

During a scenario run, failed authority outcomes can also be checked from the
in-memory `AliasAuthorityPath` still attached to the action result. Assertion
actuals identify that source as `in_memory_authority_path`; this is
scenario-run-only data, not persistent failed-path audit storage.

See `docs/SCENARIO_DSL_v0_2.md` for assertion fields and count behavior.

## Limitations

RegistryHub does not currently persist full failed authority-chain paths after
the helper returns. As a result, `build_authority_audit_trace(...)` does not
fabricate failed `name_taken`, `policy_denied`, `device_blocked`, or
`authority_path_broken` entries from RegistryHub state.

The retained RegistryHub trace includes one terminal retained decision summary
for a grant. It does not reconstruct intermediate parent hops for a previously
completed successful chain unless that full `AliasAuthorityPath` is still
available to the caller.

Deferred work:

- Broad append-only event storage.
- Production audit or compliance reporting.
- External audit log export or service integration.

These helpers are an inspection layer over simulator data, not a production
audit subsystem.
