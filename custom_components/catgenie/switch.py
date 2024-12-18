"""Support for CatGenie Cleaning switch."""

from typing import Any

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

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
    _attr_name = None

    async def async_turn_on(self, **_: Any) -> None:
        """Turn the device on."""
        await self.send_api_command(DeviceOperation.ON)
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **_: Any) -> None:
        """Turn the device off."""
        await self.device_operation(DeviceOperation.OFF)
        self._attr_is_on = False
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if not self.coordinator.data:
            return
        self._attr_is_on = (
            self.coordinator.data.operation_status.state == DeviceOperation.ON
        )
        self.async_write_ha_state()
