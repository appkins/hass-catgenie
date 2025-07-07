"""Event related entities for CatGenie integration."""

from homeassistant.components.event import (
    EventEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LOGGER
from .entity import CatGenieEntity


async def async_setup_entry(
    hass: HomeAssistant,  # Unused function argument: `hass`
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the event platform."""
    LOGGER.info(f"Setting up event platform: {entry.entry_id}")
    coordinator = hass.data[DOMAIN]["coordinator"]

    async_add_entities(
        {
            CatGenieErrorEvent(coordinator=coordinator),
        },
    )


class CatGenieErrorEvent(CatGenieEntity, EventEntity):
    """Representation of a CatGenie Cloud sensor entity."""

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the entity."""
        return f"{self.coordinator.data.manufacturer_id}_operation_error"

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return "Operation Error"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if not self.coordinator.data:
            return
        if not self.coordinator.data.operation_status:
            return
        if not self.coordinator.data.operation_status.error:
            return
        self._attr_state = self.coordinator.data.operation_status.error
        self.async_write_ha_state()
