"""Base class for CatGenie via API entities."""

from enum import Enum
from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CatGenieCoordinator


class DeviceOperation(Enum):
    """Device operation enum."""

    ON = 1
    OFF = 2
    RESUME = 3
    FULL_CLEAN = 4


class CatGenieEntity(CoordinatorEntity[CatGenieCoordinator]):
    """Representation of a CatGenie Cloud entity."""

    _switchbot_state: dict[str, Any] | None = None
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: CatGenieCoordinator,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.data.mac_address
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.data.mac_address)},
            name=coordinator.data.name,
            manufacturer="PetNovations Ltd.",
            model=coordinator.data.manufacturer_id,
            sw_version=coordinator.data.fw_version,
        )

    async def device_operation(self, device_id, op: DeviceOperation) -> Any:
        """Obtain the list of devices associated to a user."""
        return self.coordinator.client.async_device_operation(device_id, op)
