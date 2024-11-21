"""Binary sensor platform for integration_blueprint."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, LOGGER
from .coordinator import CatGenieCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

ENTITY_DESCRIPTIONS = (
    BinarySensorEntityDescription(
        key="catgenie",
        name="Litter Box Connectivity",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
    BinarySensorEntityDescription(
        key="catgenie",
        name="Litter Box Running",
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    BinarySensorEntityDescription(
        key="catgenie",
        name="Litter Box Problem",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # Unused function argument: `hass`
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary_sensor platform."""
    LOGGER.info(f"Setting up binary_sensor platform: {entry.entry_id}")
    coordinator = hass.data[DOMAIN]["coordinator"]

    async_add_entities(
        CatGenieBinarySensor(
            coordinator=coordinator,  # entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class CatGenieBinarySensor(
    CoordinatorEntity[CatGenieCoordinator],
    BinarySensorEntity,
):
    """integration_blueprint binary_sensor class."""

    def __init__(
        self,
        coordinator: CatGenieCoordinator,
        entity_description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary_sensor class."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.entity_description = entity_description
        self._attr_unique_id = f"{coordinator.data.mac_address}_{entity_description.key}_{entity_description.device_class}_sensor"
        self._attr_is_on = False

    @property
    def is_on(self) -> bool:
        """Return true if the binary_sensor is on."""
        match self.entity_description.entity_category:
            case BinarySensorDeviceClass.CONNECTIVITY:
                return self.coordinator.data.reported_status == "connected"
            case BinarySensorDeviceClass.PROBLEM:
                return self.coordinator.data.operation_status.error != ""
            case _:
                return self.coordinator.data.operation_status.state > 0

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        match self.entity_description.entity_category:
            case BinarySensorDeviceClass.CONNECTIVITY:
                self._attr_is_on = self.coordinator.data.reported_status == "connected"
            case BinarySensorDeviceClass.PROBLEM:
                self._attr_is_on = self.coordinator.data.operation_status.error != ""
            case _:
                self._attr_is_on = self.coordinator.data.operation_status.state > 0
        self.async_write_ha_state()

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        name = self.coordinator.data.name
        if not name:
            name = f"Litter Box {self.coordinator.data.manufacturer_id}"
        return DeviceInfo(
            identifiers={
                (DOMAIN, self.coordinator.data.mac_address),
            },
            name=self.coordinator.data.name,
            manufacturer="PetNovations Ltd.",
            model="VXHCATGENIE",
            model_id=self.coordinator.data.manufacturer_id,
            sw_version=self.coordinator.data.fw_version,
        )
