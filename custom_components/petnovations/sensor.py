"""Platform for sensor integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import callback

from .const import LOGGER
from .entity import CatGenieEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .coordinator import CatGenieConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: CatGenieConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    LOGGER.debug("Setting up sensor platform: %s", entry.entry_id)
    coordinator = entry.runtime_data

    async_add_entities(
        [
            CatGenieSaniSolutionSensor(coordinator=coordinator),
        ],
    )


class CatGenieSaniSolutionSensor(CatGenieEntity, SensorEntity):
    """Representation of a CatGenie Cloud sensor entity."""

    _attr_name = "Solution"
    _unique_id_suffix = "sani_solution"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if not self.coordinator.data:
            return
        self._attr_native_value = self.coordinator.data.remaining_sani_solution
        self.async_write_ha_state()
