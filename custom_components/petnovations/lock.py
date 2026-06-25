"""Lock platform for the CatGenie child lock."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.lock import LockEntity
from homeassistant.core import callback

from .entity import CatGenieEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .coordinator import CatGenieConfigEntry, CatGenieCoordinator

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: CatGenieConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the lock platform."""
    coordinator = entry.runtime_data
    async_add_entities([CatGenieChildLock(coordinator=coordinator)])


class CatGenieChildLock(CatGenieEntity, LockEntity):
    """Lock entity for the device's child lock (``childLock`` config field)."""

    _attr_translation_key = "child_lock"
    _unique_id_suffix = "child_lock"

    def __init__(self, coordinator: CatGenieCoordinator) -> None:
        """Initialize the lock entity."""
        super().__init__(coordinator)
        self._attr_is_locked = bool(coordinator.data.configuration.child_lock)

    async def async_lock(self, **_: Any) -> None:
        """Enable the child lock."""
        await self.coordinator.client.async_set_child_lock(
            self.device_id, enabled=True
        )
        self._attr_is_locked = True
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    async def async_unlock(self, **_: Any) -> None:
        """Disable the child lock."""
        await self.coordinator.client.async_set_child_lock(
            self.device_id, enabled=False
        )
        self._attr_is_locked = False
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_is_locked = bool(self.coordinator.data.configuration.child_lock)
        self.async_write_ha_state()
