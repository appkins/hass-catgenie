"""DataUpdateCoordinator for integration_blueprint."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    CatGenieApiClient,
    CatGenieApiClientAuthenticationError,
    CatGenieApiClientError,
)
from .const import CLEAN_CYCLE_SECONDS, CONF_SECRET, DOMAIN, LOGGER
from .data import DeviceData, FirmwareUpdate, Notification

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

type CatGenieConfigEntry = ConfigEntry[CatGenieCoordinator]


class UnknownError(Exception):
    """Raised when an unknown error occurs during update."""

    def __init__(self, *args: object) -> None:
        """Initialize the error."""
        super().__init__(f"Unknown error: {args}")


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class CatGenieCoordinator(DataUpdateCoordinator[DeviceData]):
    """Class to manage fetching data from the API."""

    config_entry: CatGenieConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: CatGenieConfigEntry,
        client: CatGenieApiClient,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass=hass,
            logger=LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
            always_update=True,
        )
        self.client = client
        self.notifications: list[Notification] = []
        self.pending_firmware_update: FirmwareUpdate | None = None
        # Assumed full-cycle length used to estimate remaining/finish time from
        # the device's progress %. Adjustable via the "Run time" number entity.
        self.run_time_seconds: int = CLEAN_CYCLE_SECONDS

    async def _async_update_data(self) -> DeviceData:
        """Update data via library."""
        try:
            if not self.client.has_access_token():
                await self.client.async_refresh_token()
            result = await self.client.async_get_first_device()
            await self._async_update_notifications()
            data = DeviceData.from_dict(result)
        except CatGenieApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except CatGenieApiClientError as exception:
            raise UpdateFailed(exception) from exception
        except Exception as exception:
            raise UnknownError from exception

        new_secret = self.client.consume_secret_update()
        if new_secret:
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={**self.config_entry.data, CONF_SECRET: new_secret},
            )

        return data

    async def _async_update_notifications(self) -> None:
        """Refresh the push-notification feed (best effort, non-fatal)."""
        try:
            raw = await self.client.async_get_notifications()
        except CatGenieApiClientError as exception:
            LOGGER.debug("Could not fetch notifications: %s", exception)
            return
        self.notifications = [Notification.from_dict(item) for item in raw]
        self.pending_firmware_update = next(
            (n.firmware_update for n in self.notifications if n.firmware_update),
            None,
        )
