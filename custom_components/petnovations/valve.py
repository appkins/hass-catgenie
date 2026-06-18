"""Valve platform exposing the CatGenie cleaning cycle.

Modelled as a valve so HomeKit (via the HA HomeKit bridge) maps it to a valve
accessory: open = run a clean cycle, closed = idle, and the valve position
mirrors the device's reported cycle ``progress``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.valve import (
    ValveDeviceClass,
    ValveEntity,
    ValveEntityFeature,
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
    """Set up the valve platform."""
    coordinator = entry.runtime_data
    async_add_entities([CatGenieCleanValve(coordinator=coordinator)])


class CatGenieCleanValve(CatGenieEntity, ValveEntity):
    """Valve entity representing the CatGenie clean cycle."""

    _attr_translation_key = "clean_cycle"
    _unique_id_suffix = "clean_valve"
    _attr_device_class = ValveDeviceClass.WATER
    _attr_reports_position = True
    _attr_supported_features = ValveEntityFeature.OPEN | ValveEntityFeature.CLOSE

    @property
    def _operation(self) -> Any:
        """Return the device's operation status."""
        return self.coordinator.data.operation_status

    @property
    def current_valve_position(self) -> int:
        """Return the cycle progress (0-100) while running, else 0.

        Position 0 reads as closed; while a cycle is active we report at least 1
        so the valve shows open even before the device reports any progress.
        """
        if self._operation.state == 0:
            return 0
        return max(1, min(100, self._operation.progress))

    async def async_open_valve(self, **_: Any) -> None:
        """Start a clean cycle."""
        await self.device_operation(self.device_id, DeviceOperation.ON)
        await self.coordinator.async_request_refresh()

    async def async_close_valve(self, **_: Any) -> None:
        """Stop the running clean cycle."""
        await self.device_operation(self.device_id, DeviceOperation.OFF)
        await self.coordinator.async_request_refresh()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
