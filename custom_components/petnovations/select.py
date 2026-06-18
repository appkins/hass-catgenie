"""Select platform for the CatGenie operating mode."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.select import SelectEntity
from homeassistant.core import callback

from .entity import CatGenieEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .coordinator import CatGenieConfigEntry, CatGenieCoordinator

# The device exposes activation as two fields: `mode` (0 = cat, 1 = time) and a
# separate `manual` flag (1 = manual, overrides mode). The slugs are translated
# + iconized via strings.json / icons.json.
OPTION_CAT = "cat_activation"
OPTION_TIME = "time_activation"
OPTION_MANUAL = "manual"

_OPTIONS = [OPTION_CAT, OPTION_TIME, OPTION_MANUAL]
# mode value -> option slug (only when manual is off)
_MODE_TO_OPTION: dict[int, str] = {0: OPTION_CAT, 1: OPTION_TIME}


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: CatGenieConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the select platform."""
    coordinator = entry.runtime_data
    async_add_entities([CatGenieModeSelect(coordinator=coordinator)])


class CatGenieModeSelect(CatGenieEntity, SelectEntity):
    """Select entity for the device's activation mode."""

    _attr_translation_key = "mode"
    _unique_id_suffix = "mode"
    _attr_options = _OPTIONS

    def __init__(self, coordinator: CatGenieCoordinator) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._attr_current_option = self._option_from_config()

    def _option_from_config(self) -> str | None:
        """Derive the current option from the device configuration."""
        config = self.coordinator.data.configuration
        if config.manual:
            return OPTION_MANUAL
        return _MODE_TO_OPTION.get(config.mode)

    async def async_select_option(self, option: str) -> None:
        """Change the device activation mode."""
        config = self.coordinator.data.configuration
        if option == OPTION_CAT:
            await self.coordinator.client.async_set_mode(
                self.device_id, mode=0, manual=0
            )
        elif option == OPTION_TIME:
            # Time activation requires a schedule; keep the device's current one.
            await self.coordinator.client.async_set_mode(
                self.device_id, mode=1, manual=0, schedule=config.schedule
            )
        elif option == OPTION_MANUAL:
            await self.coordinator.client.async_set_mode(
                self.device_id, mode=config.mode, manual=1
            )

        # Optimistically reflect the change, then refresh from the device.
        self._attr_current_option = option
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_current_option = self._option_from_config()
        self.async_write_ha_state()
