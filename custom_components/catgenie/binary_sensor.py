"""Binary sensor platform for integration_blueprint."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN, LOGGER
from .entity import CatGenieEntity

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import CatGenieCoordinator


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
            CatGenieOccupancy(coordinator=coordinator),
        },
    )


class CatGenieBinarySensor(CatGenieEntity, BinarySensorEntity):
    """integration_blueprint binary_sensor class."""

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the entity."""
        return f"{self.coordinator.data.manufacturer_id}_{self.device_class}"

    @property
    def name(self) -> str:
        """Return the unique ID of the entity."""
        return self.device_class.title()

    def __init__(
        self,
        coordinator: CatGenieCoordinator,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        device_class = self._attr_device_class
        if device_class is None:
            # device_class = BinarySensorDeviceClass.POWER
            self._attr_device_class = BinarySensorDeviceClass.POWER
        # self.entity_description = BinarySensorEntityDescription(
        #     key=DOMAIN,
        #     name=f"Litter Box {device_class.name.title()}",
        #     device_class=device_class,
        # )

    def is_on(self) -> (bool | None):
        """Return true if the binary_sensor is on."""
        return self._attr_is_on

class CatGenieConnectivitySensor(
    CatGenieBinarySensor,
    BinarySensorEntity,
):
    """integration_blueprint binary_sensor class."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return "Connectivity"

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the entity."""
        return f"{self.coordinator.data.manufacturer_id}_connectivity"

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

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return "Running"

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the entity."""
        return f"{self.coordinator.data.manufacturer_id}_running"

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
    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return "Problem"

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the entity."""
        return f"{self.coordinator.data.manufacturer_id}_problem"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_is_on = self.coordinator.data.operation_status.error != ""
        self.async_write_ha_state()

class CatGenieOccupancy(
    CatGenieBinarySensor,
    BinarySensorEntity,
):
    """integration_blueprint binary_sensor class."""

    _attr_device_class = BinarySensorDeviceClass.OCCUPANCY
    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return "Occupancy"

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the entity."""
        return f"{self.coordinator.data.manufacturer_id}_occupancy"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator.data.operation_status.sens is None:
            self._attr_is_on = False
        str_sens = str(self.coordinator.data.operation_status.sens)
        if len(str_sens) > 0:
            self._attr_is_on = True
        self.async_write_ha_state()
