"""Device model for the first DARWIN simulator skeleton."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Device:
    """A simulated network participant with durable identity and local label."""

    device_id: str
    label: str
    passport_id: str | None = None
    current_registry_hub: str | None = None
    current_traffic_hub: str | None = None
    state: str = "unknown"
    checkpoint_tier: int = 1

    def attach(self, hub_id: str) -> None:
        """Attach this device to a hub in simulator state."""
        self.current_registry_hub = hub_id
        self.current_traffic_hub = hub_id
        self.state = "online"

    def mark_in_transit(self) -> None:
        """Mark this device as relocating rather than simply offline."""
        self.state = "in_transit"
