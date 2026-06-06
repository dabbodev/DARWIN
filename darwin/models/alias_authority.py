"""Alias authority-chain data models for DARWIN v0.6."""

from __future__ import annotations

from dataclasses import dataclass, field

from darwin.models.alias import AliasRecord

ALIAS_AUTHORITY_DECISIONS = (
    "approved_here",
    "continue_upward",
    "fallback_available",
    "name_taken",
    "insufficient_authority",
    "policy_denied",
    "device_blocked",
    "authority_path_broken",
)


@dataclass(slots=True)
class AliasAuthorityDecision:
    """One hub-local decision recorded during alias authority evaluation."""

    hub_id: str
    scope_path: str
    decision: str
    reason: str | None = None
    alias: str | None = None
    fallback_alias: str | None = None
    authority_ceiling: str | None = None
    can_continue_upward: bool = False

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return {
            "hub_id": self.hub_id,
            "scope_path": self.scope_path,
            "decision": self.decision,
            "reason": self.reason,
            "alias": self.alias,
            "fallback_alias": self.fallback_alias,
            "authority_ceiling": self.authority_ceiling,
            "can_continue_upward": self.can_continue_upward,
        }


@dataclass(slots=True)
class AliasAuthorityPathSummary:
    """Compact scenario-friendly view of an alias authority path."""

    requested_alias: str
    granted_alias: str | None
    final_status: str
    authority_ceiling: str | None
    decision_count: int
    path_hubs: list[str]

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return {
            "requested_alias": self.requested_alias,
            "granted_alias": self.granted_alias,
            "final_status": self.final_status,
            "authority_ceiling": self.authority_ceiling,
            "decision_count": self.decision_count,
            "path_hubs": list(self.path_hubs),
        }


@dataclass(slots=True)
class AliasAuthorityPath:
    """Ordered authority-chain record for an alias claim attempt."""

    requested_alias: str
    target_device_id: str
    requesting_hub_id: str
    decisions: list[AliasAuthorityDecision] = field(default_factory=list)
    final_status: str = "pending"
    granted_alias: str | None = None
    authority_ceiling: str | None = None

    def add_decision(self, decision: AliasAuthorityDecision) -> None:
        """Append one decision while preserving path order."""
        self.decisions.append(decision)

    def latest_decision(self) -> AliasAuthorityDecision | None:
        """Return the most recently appended decision, if any."""
        if not self.decisions:
            return None
        return self.decisions[-1]

    def to_summary(self) -> AliasAuthorityPathSummary:
        """Return a compact summary of the recorded authority path."""
        return AliasAuthorityPathSummary(
            requested_alias=self.requested_alias,
            granted_alias=self.granted_alias,
            final_status=self.final_status,
            authority_ceiling=self.authority_ceiling,
            decision_count=len(self.decisions),
            path_hubs=[decision.hub_id for decision in self.decisions],
        )

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-safe representation."""
        return {
            "requested_alias": self.requested_alias,
            "target_device_id": self.target_device_id,
            "requesting_hub_id": self.requesting_hub_id,
            "decisions": [decision.to_dict() for decision in self.decisions],
            "final_status": self.final_status,
            "granted_alias": self.granted_alias,
            "authority_ceiling": self.authority_ceiling,
        }


@dataclass(slots=True)
class AliasAuthorityClaimResult:
    """Outcome of claiming an alias through an evaluated authority chain."""

    success: bool
    status: str
    reason: str | None
    requested_alias: str
    granted_alias: str | None
    alias_record: AliasRecord | None
    authority_path: AliasAuthorityPath
    authority_ceiling: str | None
