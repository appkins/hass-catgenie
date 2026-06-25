"""Button platform for CatGenie run controls."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import callback

from .data import OperationStatus
from .entity import CatGenieEntity, DeviceOperation

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .coordinator import CatGenieConfigEntry, CatGenieCoordinator

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class CatGenieButtonDescription(ButtonEntityDescription):
    """Describes a CatGenie run-control button."""

    operation: DeviceOperation
    available_fn: Callable[[OperationStatus], bool]


BUTTONS: tuple[CatGenieButtonDescription, ...] = (
    CatGenieButtonDescription(
        key="resume",
        translation_key="resume",
        operation=DeviceOperation.RESUME,
        available_fn=lambda status: status.state > 0,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: CatGenieConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the button platform."""
    coordinator = entry.runtime_data
    async_add_entities(
        CatGenieButton(coordinator=coordinator, description=description)
        for description in BUTTONS
    )


class CatGenieButton(CatGenieEntity, ButtonEntity):
    """A CatGenie run-control button."""

    entity_description: CatGenieButtonDescription

    def __init__(
        self,
        coordinator: CatGenieCoordinator,
        description: CatGenieButtonDescription,
    ) -> None:
        """Initialize the button entity."""
        self.entity_description = description
        self._unique_id_suffix = description.key
        super().__init__(coordinator)

    @property
    def available(self) -> bool:
        """Return whether the action is valid for the current run state."""
        if not super().available:
            return False
        return self.entity_description.available_fn(
            self.coordinator.data.operation_status
        )

    async def async_press(self) -> None:
        """Send the run-control command to the device."""
        await self.device_operation(self.device_id, self.entity_description.operation)
        await self.coordinator.async_request_refresh()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
