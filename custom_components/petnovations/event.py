"""Event platform surfacing the CatGenie notification feed.

HA can't register for real push (it has no FCM token to send to the app's
``notification/v1/mobile/attach`` endpoint), so the coordinator polls the
``notification/v1/push/user`` feed and this entity replays new items as HA
events. Each event also lands on the event bus for automations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.event import EventEntity
from homeassistant.core import callback

from .entity import CatGenieEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .coordinator import CatGenieConfigEntry, CatGenieCoordinator
    from .data import Notification

PARALLEL_UPDATES = 0

# Declared event types. Any feed item whose type isn't recognised is reported as
# the catch-all ``notification`` so HA never rejects an unexpected value.
EVENT_OTHER = "notification"
EVENT_TYPES: list[str] = [
    "cat_detected",
    "cycle_started",
    "cycle_complete",
    "cycle_aborted",
    "cartridge_low",
    "cartridge_empty",
    "maintenance",
    "error",
    "fw_update",
    EVENT_OTHER,
]

# Map raw feed ``type`` substrings to a declared event type.
_TYPE_ALIASES: dict[str, str] = {
    "cat": "cat_detected",
    "visit": "cat_detected",
    "start": "cycle_started",
    "begin": "cycle_started",
    "complete": "cycle_complete",
    "finish": "cycle_complete",
    "done": "cycle_complete",
    "flush": "cycle_complete",
    "abort": "cycle_aborted",
    "cancel": "cycle_aborted",
    "stop": "cycle_aborted",
    "low": "cartridge_low",
    "empty": "cartridge_empty",
    "cartridge": "cartridge_low",
    "solution": "cartridge_low",
    "maintenance": "maintenance",
    "service": "maintenance",
    "error": "error",
    "fault": "error",
    "fw": "fw_update",
    "firmware": "fw_update",
    "update": "fw_update",
}


def _map_event_type(raw_type: str) -> str:
    """Map a raw notification type onto a declared event type."""
    lowered = raw_type.lower()
    for needle, event_type in _TYPE_ALIASES.items():
        if needle in lowered:
            return event_type
    return EVENT_OTHER


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: CatGenieConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the event platform."""
    coordinator = entry.runtime_data
    async_add_entities([CatGenieNotificationEvent(coordinator=coordinator)])


class CatGenieNotificationEvent(CatGenieEntity, EventEntity):
    """Replays new CatGenie notification-feed items as HA events."""

    _attr_translation_key = "notification"
    _unique_id_suffix = "notification"
    _attr_event_types = EVENT_TYPES

    def __init__(self, coordinator: CatGenieCoordinator) -> None:
        """Initialize the event entity."""
        super().__init__(coordinator)
        # Seed with the ids already present so startup doesn't replay history.
        self._seen_ids: set[str] = {n.id for n in coordinator.notifications}

    @callback
    def _handle_coordinator_update(self) -> None:
        """Fire an event for each newly seen notification."""
        new_items: list[Notification] = [
            n for n in self.coordinator.notifications if n.id not in self._seen_ids
        ]
        # Replay oldest-first so the most recent ends up as the entity state.
        for item in sorted(new_items, key=lambda n: n.timestamp):
            self._seen_ids.add(item.id)
            self._trigger_event(
                _map_event_type(item.type),
                {
                    "id": item.id,
                    "raw_type": item.type,
                    "message": item.message,
                    "timestamp": item.timestamp,
                    "device_id": item.device_id,
                },
            )
        if new_items:
            self.async_write_ha_state()
