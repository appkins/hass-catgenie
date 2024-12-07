"""Base class for CatGenie via API entities."""

from enum import Enum
import uuid
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
    _attr_suffix: str | None = None
    coordinator: CatGenieCoordinator

    def __init__(
        self,
        coordinator: CatGenieCoordinator,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)

        self.coordinator = coordinator

        suffix = ""
        if self.device_class is not None:  # type: ignore reportUnnecessaryComparison
            suffix = f"_{self.device_class}"

        self._attr_unique_id = (
            f"{DOMAIN}_{coordinator.data.mac_address}{suffix}"
        )

        self._device_name = coordinator.data.name
        if not self._device_name:
            self._device_name = f"Litter Box {coordinator.data.manufacturer_id}"

    @property
    def suffix(self) -> str:
        """Return the suffix of the entity."""
        if self._attr_suffix is None:
            device_class = self.device_class()
            if device_class is not None:
                return device_class
            return uuid.uuid4().hex
        return self._attr_suffix

    @property
    def device_name(self) -> str:
        """Return the device name."""
        return self._device_name

    def name(self) -> str:
        """Return the name of the switch."""
        if self._attr_name is None:
            name_parts = (self._device_name.title(), self.suffix.title())
            self._attr_name = " ".join(name_parts)
        return self._attr_name

    # def unique_id(self) -> str:
    #     """Return the unique ID of the switch."""
    #     if self._attr_unique_id is None:
    #         id_parts: tuple[str] = (DOMAIN, self.coordinator.data.mac_address, self.suffix) # type: ignore reportCallIssue
    #         self._attr_unique_id = "_".join(id_parts)
    #     return self._attr_unique_id

    # def get_unique_id(self, suffix: str) -> str:
    #     """Return the unique ID of the entity."""
    #     return f"{DOMAIN}_{self.coordinator.data.mac_address}_{suffix}"

    @property
    def device_id(self) -> str:
        """Return the device ID."""
        return self.coordinator.data.manufacturer_id

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                (DOMAIN, self.coordinator.data.mac_address),
            },
            name=self._device_name,
            manufacturer="PetNovations Ltd.",
            model="VXHCATGENIE",
            model_id=self.coordinator.data.manufacturer_id,
            sw_version=self.coordinator.data.fw_version,
        )

    async def device_operation(self, device_id: str, op: DeviceOperation) -> Any:
        """Obtain the list of devices associated to a user."""
        return await self.coordinator.client.async_device_operation(device_id, op.value)
