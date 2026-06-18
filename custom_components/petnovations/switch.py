"""Support for CatGenie Cleaning switch."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
)
from homeassistant.core import callback

from .entity import CatGenieEntity, DeviceOperation

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .coordinator import CatGenieConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: CatGenieConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the CatGenie switch platform."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            CatGenieSwitch(
                coordinator=coordinator,
            ),
        ],
    )


class CatGenieSwitch(CatGenieEntity, SwitchEntity):
    """Representation of a CatGenie cleaning switch."""

    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_name = "Clean"
    _unique_id_suffix = "clean"

    async def async_turn_on(self, **_: Any) -> None:
        """Turn the device on."""
        await self.device_operation(self._device_id, DeviceOperation.ON)
        self._attr_is_on = True

    async def async_turn_off(self, **_: Any) -> None:
        """Turn the device off."""
        await self.device_operation(self._device_id, DeviceOperation.OFF)
        self._attr_is_on = False
        self.async_write_ha_state()

    @property
    def _device_id(self) -> str:
        """Return the device ID."""
        return self.coordinator.data.manufacturer_id

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if not self.coordinator.data:
            return
        self._attr_is_on = (
            self.coordinator.data.operation_status.state == DeviceOperation.ON.value
        )
        self.async_write_ha_state()
