"""Policy placeholders for the simulator."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RegistryPolicy:
    conflict_strategy: str = "assign_temp_label"
    in_transit_hold_window_ms: int = 3000
    require_move_contract_for_scope_change: bool = True
    quarantine_on_failed_proof: bool = True
