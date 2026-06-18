"""Platform for sensor integration."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfTime
from homeassistant.core import callback
from homeassistant.util import dt as dt_util

from .const import CLEAN_CYCLE_SECONDS, LOGGER
from .entity import CatGenieEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .coordinator import CatGenieConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: CatGenieConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    LOGGER.debug("Setting up sensor platform: %s", entry.entry_id)
    coordinator = entry.runtime_data

    async_add_entities(
        [
            CatGenieSaniSolutionSensor(coordinator=coordinator),
            CatGenieProgressSensor(coordinator=coordinator),
            CatGenieTimeRemainingSensor(coordinator=coordinator),
            CatGenieFinishesAtSensor(coordinator=coordinator),
        ],
    )


class CatGenieSaniSolutionSensor(CatGenieEntity, SensorEntity):
    """Representation of a CatGenie Cloud sensor entity."""

    _attr_name = "Solution"
    _unique_id_suffix = "sani_solution"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if not self.coordinator.data:
            return
        self._attr_native_value = self.coordinator.data.remaining_sani_solution
        self.async_write_ha_state()


class CatGenieProgressSensor(CatGenieEntity, SensorEntity):
    """Progress (%) of the current clean cycle."""

    _attr_translation_key = "progress"
    _unique_id_suffix = "progress"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if not self.coordinator.data:
            return
        status = self.coordinator.data.operation_status
        self._attr_native_value = status.progress if status.state > 0 else 0
        self.async_write_ha_state()


def _remaining_seconds(state: int, progress: int) -> int:
    """Estimate seconds left in the cycle from the reported progress."""
    if state == 0:
        return 0
    clamped = max(0, min(100, progress))
    return round(CLEAN_CYCLE_SECONDS * (100 - clamped) / 100)


class CatGenieTimeRemainingSensor(CatGenieEntity, SensorEntity):
    """Estimated time remaining in the current clean cycle.

    Derived from the device's reported ``progress`` against an approximate full
    cycle duration (``CLEAN_CYCLE_SECONDS``), so it tracks the valve nicely for
    HomeKit while staying an estimate.
    """

    _attr_translation_key = "time_remaining"
    _unique_id_suffix = "time_remaining"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if not self.coordinator.data:
            return
        status = self.coordinator.data.operation_status
        self._attr_native_value = _remaining_seconds(status.state, status.progress)
        self.async_write_ha_state()


class CatGenieFinishesAtSensor(CatGenieEntity, SensorEntity):
    """Estimated wall-clock time the current clean cycle will finish.

    This is the entity to wire to the HomeKit valve's ``linked_valve_end_time``:
    HomeKit derives the valve's RemainingDuration as ``finish - now``, giving a
    live countdown driven by the device's ``progress``. Reports ``None`` (no
    countdown) while the device is idle.
    """

    _attr_translation_key = "finishes_at"
    _unique_id_suffix = "finishes_at"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if not self.coordinator.data:
            return
        status = self.coordinator.data.operation_status
        if status.state == 0:
            self._attr_native_value = None
        else:
            remaining = _remaining_seconds(status.state, status.progress)
            self._attr_native_value = dt_util.utcnow() + timedelta(seconds=remaining)
        self.async_write_ha_state()
