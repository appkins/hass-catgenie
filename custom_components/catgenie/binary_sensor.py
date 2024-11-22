"""Binary sensor platform for integration_blueprint."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant, callback

from custom_components.catgenie.entity import CatGenieEntity

from .const import DOMAIN, LOGGER

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.helpers.entity_platform import AddEntitiesCallback


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
            CatGenieProblemSensor(coordinator=coordinator),
            CatGenieConnectivitySensor(coordinator=coordinator),
            CatGenieRunningSensor(coordinator=coordinator),
        },
    )


class CatGenieBinarySensor(CatGenieEntity, BinarySensorEntity):
    """integration_blueprint binary_sensor class."""

    @property
    def is_on(self) -> bool:
        """Return true if the binary_sensor is on."""
        return self._attr_is_on

    @property
    def entity_description(self) -> BinarySensorEntityDescription:
        """Return the class of this binary_sensor."""
        device_class = self._attr_device_class
        if device_class is None:
            device_class = BinarySensorDeviceClass.POWER
        return BinarySensorEntityDescription(
            key=DOMAIN,
            name=f"Litter Box {device_class.name.title()}",
            device_class=device_class,
        )


class CatGenieConnectivitySensor(
    CatGenieBinarySensor,
    BinarySensorEntity,
):
    """integration_blueprint binary_sensor class."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_is_on = self.coordinator.data.reported_status == "connected"
        self.async_write_ha_state()


class CatGenieRunningSensor(
    CatGenieBinarySensor,
    BinarySensorEntity,
):
    """integration_blueprint binary_sensor class."""

    _attr_device_class = BinarySensorDeviceClass.RUNNING

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_is_on = self.coordinator.data.operation_status.state > 0
        self.async_write_ha_state()


class CatGenieProblemSensor(
    CatGenieBinarySensor,
    BinarySensorEntity,
):
    """integration_blueprint binary_sensor class."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_is_on = self.coordinator.data.operation_status.error != ""
        self.async_write_ha_state()
