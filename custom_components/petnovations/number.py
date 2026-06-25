"""Number platform for CatGenie configuration values."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
    RestoreNumber,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfTime
from homeassistant.core import callback

from .const import (
    CAT_DELAY_MAX,
    CAT_DELAY_MIN,
    CAT_DELAY_SCALE,
    CAT_DELAY_STEP,
    DEFAULT_RUN_TIME_MINUTES,
    RUN_TIME_MAX_MINUTES,
    RUN_TIME_MIN_MINUTES,
    RUN_TIME_STEP_MINUTES,
)
from .data import Configuration
from .entity import CatGenieEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .coordinator import CatGenieConfigEntry, CatGenieCoordinator

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class CatGenieNumberDescription(NumberEntityDescription):
    """Describes a CatGenie configuration number."""

    value_fn: Callable[[Configuration], float | None]
    config_key: str
    scale: float = 1.0


NUMBERS: tuple[CatGenieNumberDescription, ...] = (
    CatGenieNumberDescription(
        key="cat_delay",
        translation_key="cat_delay",
        config_key="catDelay",
        device_class=NumberDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        native_min_value=CAT_DELAY_MIN,
        native_max_value=CAT_DELAY_MAX,
        native_step=CAT_DELAY_STEP,
        scale=CAT_DELAY_SCALE,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda c: c.cat_delay,
    ),
    CatGenieNumberDescription(
        key="volume_level",
        translation_key="volume_level",
        config_key="volumeLevel",
        native_unit_of_measurement=PERCENTAGE,
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda c: c.volume_level,
    ),
    CatGenieNumberDescription(
        key="cat_sense",
        translation_key="cat_sense",
        config_key="catSense",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda c: c.cat_sense,
    ),
    CatGenieNumberDescription(
        key="pump_level",
        translation_key="pump_level",
        config_key="pumpPctT",
        native_unit_of_measurement=PERCENTAGE,
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda c: c.pump_pct_t,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: CatGenieConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the number platform."""
    coordinator = entry.runtime_data
    entities: list[NumberEntity] = [
        CatGenieNumber(coordinator=coordinator, description=description)
        for description in NUMBERS
    ]
    entities.append(CatGenieRunTimeNumber(coordinator=coordinator))
    async_add_entities(entities)


class CatGenieNumber(CatGenieEntity, NumberEntity):
    """A writable CatGenie configuration value."""

    entity_description: CatGenieNumberDescription

    def __init__(
        self,
        coordinator: CatGenieCoordinator,
        description: CatGenieNumberDescription,
    ) -> None:
        """Initialize the number entity."""
        self.entity_description = description
        self._unique_id_suffix = description.key
        super().__init__(coordinator)
        self._attr_native_value = self._current_value()

    def _current_value(self) -> float | None:
        """Read the current value (scaled to display units)."""
        raw = self.entity_description.value_fn(self.coordinator.data.configuration)
        if raw is None:
            return None
        return raw / self.entity_description.scale

    async def async_set_native_value(self, value: float) -> None:
        """Update the configuration value on the device."""
        scaled = int(round(value * self.entity_description.scale))
        await self.set_configuration(**{self.entity_description.config_key: scaled})
        self._attr_native_value = value
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = self._current_value()
        self.async_write_ha_state()


class CatGenieRunTimeNumber(CatGenieEntity, RestoreNumber):
    """Assumed clean-cycle length used to estimate remaining / finish time.

    The device doesn't expose its cycle length, so this is a local, persisted
    setpoint (not written to the device). It drives the "Time remaining" and
    "Cycle finishes at" sensors, the latter feeding the HomeKit valve's
    ``linked_valve_end_time`` countdown.
    """

    _attr_translation_key = "run_time"
    _unique_id_suffix = "run_time"
    _attr_device_class = NumberDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_native_min_value = RUN_TIME_MIN_MINUTES
    _attr_native_max_value = RUN_TIME_MAX_MINUTES
    _attr_native_step = RUN_TIME_STEP_MINUTES
    _attr_mode = NumberMode.BOX
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: CatGenieCoordinator) -> None:
        """Initialize the run-time number."""
        super().__init__(coordinator)
        self._attr_native_value = DEFAULT_RUN_TIME_MINUTES

    async def async_added_to_hass(self) -> None:
        """Restore the last set run time and apply it to the coordinator."""
        await super().async_added_to_hass()
        last = await self.async_get_last_number_data()
        if last is not None and last.native_value is not None:
            self._attr_native_value = last.native_value
        minutes = self._attr_native_value or DEFAULT_RUN_TIME_MINUTES
        self.coordinator.run_time_seconds = int(minutes * 60)

    async def async_set_native_value(self, value: float) -> None:
        """Update the assumed run time and refresh the dependent sensors."""
        self._attr_native_value = value
        self.coordinator.run_time_seconds = int(value * 60)
        self.async_write_ha_state()
        # Push the new estimate to the remaining/finish-time sensors immediately.
        self.coordinator.async_update_listeners()
