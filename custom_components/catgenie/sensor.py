"""Platform for sensor integration."""


from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
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
    """Set up the binary_sensor platform."""
    LOGGER.info(f"Setting up binary_sensor platform: {entry.entry_id}")
    coordinator = hass.data[DOMAIN]["coordinator"]

    async_add_entities(
        {
            CatGenieSaniSolutionSensor(coordinator=coordinator),
            CatGeniePresenceSensor(coordinator=coordinator),
        },
    )


class CatGenieSaniSolutionSensor(CatGenieEntity, SensorEntity):
    """Representation of a CatGenie Cloud sensor entity."""

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if not self.coordinator.data:
            return
        self._attr_native_value = self.coordinator.data.remaining_sani_solution
        self.async_write_ha_state()

class CatGeniePresenceSensor(CatGenieEntity, SensorEntity):
    """integration_blueprint binary_sensor class."""

    _attr_device_class = SensorDeviceClass.ENUM # type: ignore

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_state = self.coordinator.data.operation_status.sens
        self.async_write_ha_state()
