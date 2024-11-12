"""Binary sensor platform for integration_blueprint."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
# from .data import CatGenieDeviceStatusData
from .const import DOMAIN

from .coordinator import CatGenieUpdateCoordinator

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
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary_sensor platform."""
    # client = hass.data[DOMAIN][entry.entry_id]
    # coordinator = CatGenieUpdateCoordinator(hass, client)
    print(entry.entry_id)
    coordinator = hass.data[DOMAIN]["coordinator"]
    
    async_add_entities(
        CatGenieBinarySensor(
            coordinator=coordinator, # entry.runtime_data.coordinator,
            entity_description=entity_description,
        ) for entity_description in ENTITY_DESCRIPTIONS
    )


class CatGenieBinarySensor(CoordinatorEntity[CatGenieUpdateCoordinator], BinarySensorEntity):
    """integration_blueprint binary_sensor class."""

    def __init__(
        self,
        coordinator: CatGenieUpdateCoordinator,
        entity_description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary_sensor class."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.entity_description = entity_description
        self._attr_unique_id = f"{coordinator.device.get('macAddress')}_{entity_description.key}_{entity_description.device_class}_sensor"
        self._attr_is_on = False

    @property
    def is_on(self) -> bool:
        """Return true if the binary_sensor is on."""
        if self.entity_description.entity_category == BinarySensorDeviceClass.CONNECTIVITY:
            status = self.coordinator.device.get("reportedStatus", "")
            return status == "connected"
        elif self.entity_description.entity_category == BinarySensorDeviceClass.PROBLEM:
            err = self.coordinator.data.get("error", "")
            return err != ""
        else:
            state = self.coordinator.data.get("state", 0)
            return state > 0
        # if self._attr_is_on is None:
        #     return False
        # return self._attr_is_on
    
    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.entity_description.entity_category == BinarySensorDeviceClass.CONNECTIVITY:
            status = self.coordinator.device.get("reportedStatus", "")
            self._attr_is_on = status == "connected"
        elif self.entity_description.entity_category == BinarySensorDeviceClass.PROBLEM:
            err = self.coordinator.data.get("error", "")
            self._attr_is_on = err != ""
        else:
            state = self.coordinator.data.get("state", 0)
            self._attr_is_on = state > 0
        self.async_write_ha_state()
        
    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                (DOMAIN, self.coordinator.device.get("macAddress"))
            },
            name=self.coordinator.device.get("name"),
            manufacturer="PetNovations Ltd.",
            model="VXHCATGENIE",
            model_id=self.coordinator.device.get("manufacturerId"),
            sw_version=self.coordinator.device.get("fwVersion"),
        )
