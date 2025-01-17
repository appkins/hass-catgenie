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

        # suffix = ""
        # if self.device_class is not None:  # type: ignore reportUnnecessaryComparison
        #     suffix = f"_{self.device_class}"

        # self._attr_unique_id = (
        #     f"{DOMAIN}_{coordinator.data.mac_address}{suffix}"
        # )
        # if self._attr_unique_id is None:
        #     self._attr_unique_id = uuid4().hex
        #     self.async_write_ha_state()

        self._device_name = coordinator.data.name
        if not self._device_name:
            self._device_name = f"Litter Box {coordinator.data.manufacturer_id}"

    @property
    def device_name(self) -> str:
        """Return the device name."""
        return self._device_name

    @property
    def device_id(self) -> str:
        """Return the device ID."""
        return self.coordinator.data.manufacturer_id

    # @property
    # async def device(self) -> DeviceInfo:
        # """Return the device."""
        # return async_get(self.hass).async_get_device((DOMAIN, self.coordinator.data.mac_address))

    # @property
    # def info(self) -> DeviceInfo:
    #     """Return the device info."""
    #     return DeviceInfo(
    #         identifiers={
    #             (DOMAIN, self.coordinator.data.mac_address),
    #         },
    #         name=self._device_name,
    #         manufacturer="PetNovations Ltd.",
    #         model="VXHCATGENIE",
    #         model_id=self.coordinator.data.manufacturer_id,
    #         sw_version=self.coordinator.data.fw_version,
    #     )

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.coordinator.data.manufacturer_id),
            },
            # default_name="Litter Box",
            manufacturer="PetNovations Ltd.",
            model="VXHCATGENIE",
            model_id=self.coordinator.data.manufacturer_id,
            sw_version=self.coordinator.data.fw_version,
        )

    async def device_operation(self, device_id: str, op: DeviceOperation) -> Any:
        """Obtain the list of devices associated to a user."""
        return await self.coordinator.client.async_device_operation(device_id, op.value)
