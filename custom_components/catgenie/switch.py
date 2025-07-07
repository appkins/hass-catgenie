"""Support for CatGenie Cleaning switch."""

from typing import Any

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from propcache.api import cached_property

from .const import DOMAIN
from .entity import CatGenieEntity, DeviceOperation


async def async_setup_entry(
    hass: HomeAssistant,
    _: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SwitchBot Cloud entry."""
    coordinator = hass.data[DOMAIN]["coordinator"]
    async_add_entities(
        {
            CatGenieSwitch(
                coordinator=coordinator,
            ),
        },
    )


class CatGenieSwitch(CatGenieEntity, SwitchEntity):
    """Representation of a SwitchBot switch."""

    _attr_device_class = SwitchDeviceClass.SWITCH

    @cached_property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.data is not None
        )  # pyright: ignore[reportUnnecessaryComparison]

    @cached_property
    def unique_id(self) -> str:
        """Return the unique ID of the entity."""
        return f"{self.coordinator.data.manufacturer_id}_clean"

    @cached_property
    def name(self) -> str:
        """Return the name of the entity."""
        return "Clean"

    async def async_turn_on(self, **_: Any) -> None:
        """Turn the device on."""
        await self.device_operation(self._device_id, DeviceOperation.ON)
        self._attr_is_on = True

    async def async_turn_off(self, **_: Any) -> None:
        """Turn the device off."""
        await self.device_operation(self._device_id, DeviceOperation.OFF)
        self._attr_is_on = False
        self.async_write_ha_state()

    @cached_property
    def _device_id(self) -> str:
        """Return the device ID."""
        return self.coordinator.data.manufacturer_id

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if not self.coordinator.data:
            return
        if not self.coordinator.data.operation_status:
            self._attr_is_on = False
            self.async_write_ha_state()
            return
        self._attr_is_on = (
            self.coordinator.data.operation_status.state == DeviceOperation.ON.value
        )
        self.async_write_ha_state()
