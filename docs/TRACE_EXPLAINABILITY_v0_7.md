# DARWIN v0.7 Trace Explainability Helpers

This document describes the v0.7 Sprint 3 deterministic trace explanation
helpers. The helpers convert existing registry history query results and
authority audit trace summaries into short, stable, JSON-safe explanation
dictionaries.

These helpers are simulator-only. They do not add external services, external
storage, production audit guarantees, compliance guarantees, real DNS,
registrar integration, public CA behavior, production identity proof, or
LLM-style prose generation.

## Purpose

Sprint 1 exposed read-only RegistryHub history query helpers. Sprint 2 exposed
read-only authority audit trace summaries. Sprint 3 adds a small explanation
layer over those structured outputs so tests, scenario assertions, and
documentation examples can display why an alias claim was approved, fell back,
conflicted, or failed.

The helpers live in `darwin.registry.trace_explain`:

- `explain_authority_trace(trace_entry)`
- `explain_authority_traces(trace_entries)`
- `explain_alias_history_entry(history_entry)`
- `explain_alias_conflict_entry(conflict_entry)`
- `explain_quarantine_event_entry(quarantine_entry)`

All helpers are read-only. They do not mutate RegistryHub state, alias records,
history records, authority records, security events, snapshots, scenarios, or
runtime behavior.

## Relationship to Sprint 1

`explain_alias_history_entry(...)`,
`explain_alias_conflict_entry(...)`, and
`explain_quarantine_event_entry(...)` accept Sprint 1 query result dataclasses
or their `to_dict()` output. They explain only fields already returned by:

- `query_alias_history(...)`
- `query_alias_conflicts(...)`
- `query_quarantine_events(...)`

The helpers do not invent missing history. For example, retained alias records
show the current retained alias status, such as `active` or `released`, but
they are not a broad append-only event stream.

## Relationship to Sprint 2

`explain_authority_trace(...)` accepts Sprint 2 authority audit dictionaries
from either retained RegistryHub grant provenance or in-memory authority path
summaries:

- `build_authority_audit_trace(...)`
- `summarize_authority_path(...)`

Retained RegistryHub grant traces can explain approved and fallback grants.
Failed outcomes such as conflict, simulator-local policy denial, and broken
authority paths can be explained when the caller still has the in-memory
`AliasAuthorityPath` summary.

## Example Output Shape

```json
{
  "category": "authority_trace",
  "outcome": "fallback",
  "summary": "Alias global.server fell back to global.us.server at registry_us_001.",
  "reason": "fallback_granted",
  "requested_alias": "global.server",
  "granted_alias": "global.us.server",
  "target_device": "dev_A9F3",
  "authority_ceiling": "global.us",
  "path_hubs": ["registry_us_001"]
}
```

Alias history explanations are similarly compact:

```json
{
  "category": "alias_history",
  "outcome": "claimed",
  "summary": "Alias global.family.david.home.server was claimed for dev_A9F3.",
  "reason": "alias_claimed",
  "alias": "global.family.david.home.server",
  "target_device": "dev_A9F3",
  "status": "active",
  "approved_by_registry_hub": "registry_home_001",
  "requested_alias": "global.family.david.home.server",
  "granted_alias": "global.family.david.home.server"
}
```

## Supported Outcomes

Authority trace explanations currently support:

- `approved`: the requested alias was approved at the terminal authority hub.
- `fallback`: the requested alias fell back to the granted alias at the
  terminal authority hub.
- `conflict`: the requested alias was denied because it was already taken.
- `policy_denied`: the requested alias was denied by simulator-local policy.
- `path_broken`: the authority path could not be evaluated.
- `partial`: the input did not contain enough known trace fields.

Registry history explanations currently support:

- `claimed`: retained alias history entry with `status == "active"`.
- `released`: retained alias history entry with `status == "released"`.
- `conflict`: retained alias conflict query entry.
- `observed`: retained quarantine event query entry.
- `partial`: alias history input without enough known fields.

## Scenario Assertions

Sprint 4 uses `explain_authority_trace(...)` inside
`authority_audit_trace_contains` when a scenario assertion supplies `outcome`
or `summary_contains`. This keeps scenario checks deterministic and derived
from structured helper output.

The assertion can explain retained approved/fallback grants from
`build_authority_audit_trace(...)`. Denied outcomes are explainable only when
the scenario runner still has the in-memory authority path from the current
action result.

## Limits

RegistryHub retains terminal grant provenance, not full failed authority-chain
paths. Failed outcomes are explained when the caller still has the in-memory
`AliasAuthorityPath` or a summary produced from it. The explainability helpers
do not pretend full persistent failed-path audit storage exists.

Deferred work:

- Broad append-only registry event storage.
- Full historical alias record versions.
- Production audit, compliance reporting, or external audit export.
- External service integration.
- Real DNS, registrar integration, public CA behavior, or production identity
  proof.

These helpers are deterministic adapters over existing simulator data, not a
production audit subsystem.
