"""Base class for CatGenie via API entities."""

from enum import Enum
from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from propcache.api import cached_property

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
    _attr_suffix: str | None = None
    _attr_state: str | None = None
    coordinator: CatGenieCoordinator

    def __init__(
        self,
        coordinator: CatGenieCoordinator,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)

        self.coordinator = coordinator

        self._device_name = coordinator.data.name
        if not self._device_name:
            self._device_name = f"Litter Box {coordinator.data.manufacturer_id}"

    @cached_property
    def available(self) -> bool:
        """Return True if entity is available."""
        return super().available

    @cached_property
    def device_name(self) -> str:
        """Return the device name."""
        return (
            self._device_name or f"Litter Box {self.coordinator.data.manufacturer_id}"
        )

    @cached_property
    def device_id(self) -> str:
        """Return the device ID."""
        return self.coordinator.data.manufacturer_id

    @cached_property
    def device_info(self) -> DeviceInfo:  # type: ignore reportImplicitStringConcatenation
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.coordinator.data.manufacturer_id),
            },
            manufacturer="PetNovations Ltd.",
            model="VXHCATGENIE",
            model_id=self.coordinator.data.manufacturer_id,
            sw_version=self.coordinator.data.fw_version,
        )

    async def device_operation(self, device_id: str, op: DeviceOperation) -> Any:
        """Obtain the list of devices associated to a user."""
        return await self.coordinator.client.async_device_operation(device_id, op.value)
