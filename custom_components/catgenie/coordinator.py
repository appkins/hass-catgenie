"""DataUpdateCoordinator for integration_blueprint."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .data import CatGenieDeviceStatusData

from .api import (
    CatGenieApiClientAuthenticationError,
    CatGenieApiClientError,
    CatGenieApiClient,
)
from .const import DOMAIN, LOGGER

# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class CatGenieUpdateCoordinator(DataUpdateCoordinator[CatGenieDeviceStatusData]):
    """Class to manage fetching data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: CatGenieApiClient,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=1),
        )
        
        self.client = client
        self.devices = {}

    async def _async_setup(self):
        """Set up the coordinator

        This is the place to set up your coordinator,
        or to load data, that only needs to be loaded once.

        This method will be called automatically during
        coordinator.async_config_entry_first_refresh.
        """
        if self.client._access_token is None:
            await self.client.async_get_access_token()
        devices = await self.client.async_get_devices()
        self.device = devices.values()[0]

    async def _async_update_data(self) -> CatGenieDeviceStatusData:
        """Update data via library."""
        
        device_id = self.device["manufacturerId"]
        self.device_id = device_id
        
        try:
            return await self.client.async_get_device_status(device_id)
        except CatGenieApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except CatGenieApiClientError as exception:
            raise UpdateFailed(exception) from exception
            # status = await self.client.async_get_device_status(device_id)
            # return CatGenieDeviceStatusData(
            #     state=status["state"],
            #     progress=status["progress"],
            #     error=status["error"],
            #     rtc=status["rtc"],
            #     sens=status["sens"],
            #     mode=status["mode"],
            #     manual=status["manual"],
            #     stepNum=status["stepNum"],
            #     relayMode=status["relayMode"],
            # )
        
        # devices: dict[str, CatGenieDevice] = {}

        # device_statuses = {}

        # for device_id, device in self.devices.items():
        #     try:
        #         device_status = await self.client.async_get_device_status(device_id)
                
        #         devices[device_id] = CatGenieDevice(device.fwVersion, device.mac, device.name, device.serial, device_status)
        #         # device_statuses[device_id] = device_status
        #     except CatGenieApiClientAuthenticationError as exception:
        #         raise ConfigEntryAuthFailed(exception) from exception
        #     except CatGenieApiClientError as exception:
        #         raise UpdateFailed(exception) from exception
            
        # return CatGenieData(
        #     client=self.client,
        #     devices=devices,
        # )

        # try:
        #     # Note: asyncio.TimeoutError and aiohttp.ClientError are already
        #     # handled by the data update coordinator.
        #     async with async_timeout.timeout(10):
        #         listening_idx = set(self.async_contexts())
        #         return await self.client._async_get_device_status(listening_idx)
        # except CatGenieApiClientAuthenticationError as exception:
        #     raise ConfigEntryAuthFailed(exception) from exception
        # except CatGenieApiClientError as exception:
        #     raise UpdateFailed(exception) from exception

        # devices = await self.client.async_get_devices_list()
