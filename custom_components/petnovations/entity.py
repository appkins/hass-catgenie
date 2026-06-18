"""Base class for CatGenie via API entities."""

from __future__ import annotations

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

    _attr_has_entity_name = True
    _unique_id_suffix: str = ""

    def __init__(
        self,
        coordinator: CatGenieCoordinator,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)

        manufacturer_id = coordinator.data.manufacturer_id
        if self._unique_id_suffix:
            self._attr_unique_id = f"{manufacturer_id}_{self._unique_id_suffix}"

        self._device_name = coordinator.data.name or f"Litter Box {manufacturer_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, manufacturer_id),
            },
            name=self._device_name,
            manufacturer="PetNovations Ltd.",
            model="VXHCATGENIE",
            model_id=manufacturer_id,
            sw_version=coordinator.data.fw_version,
        )

    @property
    def device_name(self) -> str:
        """Return the device name."""
        return self._device_name

    @property
    def device_id(self) -> str:
        """Return the device ID."""
        return self.coordinator.data.manufacturer_id

    async def device_operation(
        self,
        device_id: str,
        op: DeviceOperation,
    ) -> Any:
        """Send an operation command to the device."""
        return await self.coordinator.client.async_device_operation(
            device_id,
            op.value,
        )

    async def set_configuration(self, **fields: Any) -> None:
        """Write configuration field(s) and refresh from the device."""
        await self.coordinator.client.async_set_configuration(
            self.device_id, **fields
        )
        await self.coordinator.async_request_refresh()
