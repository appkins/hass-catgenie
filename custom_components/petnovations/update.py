"""CatGenie firmware update entity."""

from __future__ import annotations

from homeassistant.components.update import (
    UpdateDeviceClass,
    UpdateEntity,
    UpdateEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import CatGenieConfigEntry, CatGenieCoordinator
from .entity import CatGenieEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CatGenieConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the firmware update entity."""
    async_add_entities([CatGenieFirmwareUpdate(entry.runtime_data)])


class CatGenieFirmwareUpdate(CatGenieEntity, UpdateEntity):
    """Firmware update entity for the CatGenie.

    The pending version is sourced from push-notification type 24 (FW_UPDATE),
    which the cloud delivers when new firmware is available.  Installing triggers
    ``PUT /device/update/{deviceId}/approve`` — the same call the mobile app makes
    when the user taps "Install now".
    """

    _attr_device_class = UpdateDeviceClass.FIRMWARE
    _attr_supported_features = UpdateEntityFeature.INSTALL
    _attr_title = "CatGenie Firmware"
    _unique_id_suffix = "firmware_update"

    def __init__(self, coordinator: CatGenieCoordinator) -> None:
        """Initialize the update entity."""
        super().__init__(coordinator)

    @property
    def installed_version(self) -> str | None:
        """Return the current firmware version reported by the device."""
        return self.coordinator.data.fw_version or None

    @property
    def latest_version(self) -> str | None:
        """Return the latest available firmware version.

        Returns the version from the pending FW_UPDATE notification, or the
        installed version when no update is pending (so the entity shows
        "up to date" rather than "unknown").
        """
        fw = self.coordinator.pending_firmware_update
        if fw and fw.version:
            return fw.version
        return self.installed_version

    async def async_install(
        self,
        version: str | None,
        backup: bool,  # noqa: FBT001
        **kwargs: object,
    ) -> None:
        """Approve the pending firmware update."""
        fw = self.coordinator.pending_firmware_update
        if fw is None:
            return

        await self.coordinator.client.async_approve_firmware_update(
            device_id=fw.device_id,
            version=fw.version,
            configuration_id=fw.configuration_id,
        )
        await self.coordinator.async_request_refresh()
