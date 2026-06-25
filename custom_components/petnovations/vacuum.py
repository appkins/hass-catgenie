"""CatGenie vacuum (litter box cleaner) entity."""

from __future__ import annotations

from typing import Any

from homeassistant.components.vacuum import (
    StateVacuumEntity,
    VacuumActivity,
    VacuumEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import CatGenieConfigEntry, CatGenieCoordinator
from .entity import CatGenieEntity, DeviceOperation

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CatGenieConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the CatGenie vacuum entity."""
    async_add_entities([CatGenieVacuum(entry.runtime_data)])


class CatGenieVacuum(CatGenieEntity, StateVacuumEntity):
    """The CatGenie self-cleaning litter box as a vacuum entity.

    Maps the device's ``operationStatus.state`` to HA vacuum activities:
      - state == 0, no errors  → IDLE    (ready)
      - state  > 0             → CLEANING (cycle in progress)
      - active errors present  → ERROR

    START sends operation 1 (normal start).
    STOP  sends operation 2 (abort/off).
    SEND_COMMAND "full_clean" runs an extended sanitizing cycle.
    Activation mode is managed by the separate Mode select entity.
    """

    _attr_name = None
    _attr_icon = "mdi:toilet"
    _unique_id_suffix = "vacuum"
    _attr_supported_features = (
        VacuumEntityFeature.START
        | VacuumEntityFeature.STOP
        | VacuumEntityFeature.PAUSE
        | VacuumEntityFeature.STATE
        | VacuumEntityFeature.SEND_COMMAND
    )

    def __init__(self, coordinator: CatGenieCoordinator) -> None:
        """Initialise the vacuum entity."""
        super().__init__(coordinator)
        self._paused = False

    @property
    def activity(self) -> VacuumActivity:
        """Return the current vacuum activity derived from device state."""
        data = self.coordinator.data
        if data.active_errors:
            return VacuumActivity.ERROR
        if data.operation_status.state > 0:
            return VacuumActivity.CLEANING
        if self._paused:
            return VacuumActivity.PAUSED
        return VacuumActivity.IDLE

    async def async_start(self) -> None:
        """Start a normal clean cycle."""
        self._paused = False
        await self.device_operation(self.device_id, DeviceOperation.ON)
        await self.coordinator.async_request_refresh()

    async def async_pause(self) -> None:
        """Pause the current clean cycle."""
        self._paused = True
        await self.device_operation(self.device_id, DeviceOperation.OFF)
        await self.coordinator.async_request_refresh()

    async def async_stop(self, **kwargs: Any) -> None:
        """Abort the current clean cycle."""
        self._paused = False
        await self.device_operation(self.device_id, DeviceOperation.OFF)
        await self.coordinator.async_request_refresh()

    async def async_send_command(
        self,
        command: str,
        params: dict[str, Any] | list[Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Execute a named command on the device."""
        if command == "full_clean":
            await self.device_operation(self.device_id, DeviceOperation.FULL_CLEAN)
            await self.coordinator.async_request_refresh()
