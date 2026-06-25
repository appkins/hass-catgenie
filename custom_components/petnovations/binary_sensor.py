"""Binary sensor platform for CatGenie."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import EntityCategory
from homeassistant.core import callback

from .const import LOGGER
from .entity import CatGenieEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .coordinator import CatGenieConfigEntry

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: CatGenieConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the binary_sensor platform."""
    LOGGER.debug("Setting up binary_sensor platform: %s", entry.entry_id)
    coordinator = entry.runtime_data

    async_add_entities(
        [
            CatGenieProblemSensor(coordinator=coordinator),
            CatGenieConnectivitySensor(coordinator=coordinator),
            CatGenieOccupancy(coordinator=coordinator),
        ],
    )


class CatGenieBinarySensor(CatGenieEntity, BinarySensorEntity):
    """Base CatGenie binary_sensor class."""

    _attr_device_class = BinarySensorDeviceClass.POWER


class CatGenieConnectivitySensor(CatGenieBinarySensor):
    """CatGenie connectivity binary_sensor."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_translation_key = "connectivity"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _unique_id_suffix = "connectivity"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_is_on = self.coordinator.data.reported_status == "connected"
        self.async_write_ha_state()



class CatGenieProblemSensor(CatGenieBinarySensor):
    """CatGenie problem binary_sensor."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_translation_key = "problem"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _unique_id_suffix = "problem"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_is_on = self.coordinator.data.operation_status.error != ""
        self.async_write_ha_state()


class CatGenieOccupancy(CatGenieBinarySensor):
    """CatGenie occupancy binary_sensor."""

    _attr_device_class = BinarySensorDeviceClass.OCCUPANCY
    _attr_translation_key = "occupancy"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _unique_id_suffix = "occupancy"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        sens = self.coordinator.data.operation_status.sens
        self._attr_is_on = bool(sens)
        self.async_write_ha_state()
