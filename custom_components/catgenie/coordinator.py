"""DataUpdateCoordinator for integration_blueprint."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any

import async_timeout
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    CatGenieApiClientAuthenticationError,
    CatGenieApiClientError,
)
from .const import DOMAIN, LOGGER

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import CatGenieConfigEntry

type Status = dict[str, Any] | None

# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class CatGenieUpdateCoordinator(DataUpdateCoordinator[Status]):
    """Class to manage fetching data from the API."""

    config_entry: CatGenieConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=1),
        )

    async def _async_setup(self):
        """Set up the coordinator

        This is the place to set up your coordinator,
        or to load data, that only needs to be loaded once.

        This method will be called automatically during
        coordinator.async_config_entry_first_refresh.
        """
        if self.config_entry.runtime_data.client._access_token is None:
            await self.config_entry.runtime_data.client.async_get_access_token()
        self._devices = await self.config_entry.runtime_data.client.async_get_devices()

    async def _async_update_data(self) -> Any:
        """Update data via library."""

        device_statuses = {}

        for device_id in self._devices.keys():
            try:
                device_status = await self.config_entry.runtime_data.client.async_get_device_status(device_id)
                device_statuses[device_id] = device_status
            except CatGenieApiClientAuthenticationError as exception:
                raise ConfigEntryAuthFailed(exception) from exception
            except CatGenieApiClientError as exception:
                raise UpdateFailed(exception) from exception
            
        return device_statuses

        # try:
        #     # Note: asyncio.TimeoutError and aiohttp.ClientError are already
        #     # handled by the data update coordinator.
        #     async with async_timeout.timeout(10):
        #         listening_idx = set(self.async_contexts())
        #         return await self.config_entry.runtime_data.client._async_get_device_status(listening_idx)
        # except CatGenieApiClientAuthenticationError as exception:
        #     raise ConfigEntryAuthFailed(exception) from exception
        # except CatGenieApiClientError as exception:
        #     raise UpdateFailed(exception) from exception

        # devices = await self.config_entry.runtime_data.client.async_get_devices_list()
