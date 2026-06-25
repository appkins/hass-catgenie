"""Support for CatGenie Cleaning switch."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.components.switch import (
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import callback

from .data import Configuration
from .entity import CatGenieEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .coordinator import CatGenieConfigEntry, CatGenieCoordinator

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class CatGenieConfigSwitchDescription(SwitchEntityDescription):
    """Describes a CatGenie boolean configuration switch."""

    value_fn: Callable[[Configuration], bool]
    body_fn: Callable[[bool], dict[str, Any]]


CONFIG_SWITCHES: tuple[CatGenieConfigSwitchDescription, ...] = (
    CatGenieConfigSwitchDescription(
        key="auto_lock",
        translation_key="auto_lock",
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda c: bool(c.auto_lock),
        body_fn=lambda on: {"autoLock": 1 if on else 0},
    ),
    CatGenieConfigSwitchDescription(
        key="extra_dry",
        translation_key="extra_dry",
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda c: bool(c.extra_dry),
        body_fn=lambda on: {"extraDry": on},
    ),
    CatGenieConfigSwitchDescription(
        key="extra_wash",
        translation_key="extra_wash",
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda c: c.binary_elements.extra_wash,
        body_fn=lambda on: {"binaryElements": {"EXTRA_WASH": on}},
    ),
    CatGenieConfigSwitchDescription(
        key="extra_shake",
        translation_key="extra_shake",
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda c: c.binary_elements.extra_shake,
        body_fn=lambda on: {"binaryElements": {"EXTRA_SHAKE": on}},
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: CatGenieConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the CatGenie switch platform."""
    coordinator = entry.runtime_data
    async_add_entities(
        CatGenieConfigSwitch(coordinator=coordinator, description=description)
        for description in CONFIG_SWITCHES
    )


class CatGenieConfigSwitch(CatGenieEntity, SwitchEntity):
    """A boolean CatGenie configuration switch."""

    entity_description: CatGenieConfigSwitchDescription

    def __init__(
        self,
        coordinator: CatGenieCoordinator,
        description: CatGenieConfigSwitchDescription,
    ) -> None:
        """Initialize the config switch."""
        self.entity_description = description
        self._unique_id_suffix = description.key
        super().__init__(coordinator)
        self._attr_is_on = description.value_fn(coordinator.data.configuration)

    async def async_turn_on(self, **_: Any) -> None:
        """Enable the configuration option."""
        await self.set_configuration(**self.entity_description.body_fn(True))
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **_: Any) -> None:
        """Disable the configuration option."""
        await self.set_configuration(**self.entity_description.body_fn(False))
        self._attr_is_on = False
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_is_on = self.entity_description.value_fn(
            self.coordinator.data.configuration
        )
        self.async_write_ha_state()
