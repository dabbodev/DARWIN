"""Public registry helpers for DARWIN v0.1."""

from darwin.registry.alias_authority import (
    can_continue_alias_upward,
    claim_alias_through_authority_chain,
    evaluate_alias_authority_chain,
    evaluate_alias_authority_step,
    fallback_alias_for_scope,
    is_alias_within_scope,
)
from darwin.registry.aliases import (
    alias_exists,
    claim_alias,
    claim_bundle_alias,
    claim_progressive_alias,
    create_alias_bundle,
    highest_authorized_alias,
    release_alias,
    resolve_alias,
    resolve_bundle_alias,
    suggest_alias_fallbacks,
)
from darwin.registry.authority_audit import (
    build_authority_audit_trace,
    summarize_authority_decision,
    summarize_authority_path,
)
from darwin.registry.checkpoints import (
    detect_checkpoint_timeouts,
    get_checkpoint_state,
    record_checkpoint,
)
from darwin.registry.history_queries import (
    AliasConflictQueryResult,
    AliasHistoryQueryResult,
    AuthorityDecisionQueryResult,
    QuarantineEventQueryResult,
    query_alias_conflicts,
    query_alias_history,
    query_authority_decisions,
    query_quarantine_events,
)
from darwin.registry.operations import (
    assign_temp_label,
    register_device,
    resolve_device_id,
    resolve_label,
)
from darwin.registry.trace_explain import (
    explain_alias_conflict_entry,
    explain_alias_history_entry,
    explain_authority_trace,
    explain_authority_traces,
    explain_quarantine_event_entry,
)

__all__ = [
    "alias_exists",
    "AliasConflictQueryResult",
    "AliasHistoryQueryResult",
    "AuthorityDecisionQueryResult",
    "build_authority_audit_trace",
    "assign_temp_label",
    "claim_alias",
    "claim_alias_through_authority_chain",
    "claim_bundle_alias",
    "claim_progressive_alias",
    "can_continue_alias_upward",
    "create_alias_bundle",
    "detect_checkpoint_timeouts",
    "evaluate_alias_authority_chain",
    "evaluate_alias_authority_step",
    "explain_alias_conflict_entry",
    "explain_alias_history_entry",
    "explain_authority_trace",
    "explain_authority_traces",
    "explain_quarantine_event_entry",
    "fallback_alias_for_scope",
    "get_checkpoint_state",
    "is_alias_within_scope",
    "QuarantineEventQueryResult",
    "query_alias_conflicts",
    "query_alias_history",
    "query_authority_decisions",
    "query_quarantine_events",
    "record_checkpoint",
    "register_device",
    "release_alias",
    "resolve_device_id",
    "resolve_alias",
    "resolve_bundle_alias",
    "resolve_label",
    "highest_authorized_alias",
    "suggest_alias_fallbacks",
    "summarize_authority_decision",
    "summarize_authority_path",
]
