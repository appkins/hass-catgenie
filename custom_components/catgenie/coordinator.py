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
from .const import DOMAIN, LOGGER
from .data import DeviceData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

class UnknownError(Exception):
    """Raised when an unknown error occurs during update."""

    def __init__(self, *args: object) -> None:
        """Initialize the error."""
        super().__init__(f"Unknown error: {args}")

# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class CatGenieCoordinator(DataUpdateCoordinator[DeviceData]):
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
            update_interval=timedelta(seconds=20),
            always_update=True,
        )
        self.client = client

    async def _async_update_data(self) -> DeviceData:
        """Update data via library."""
        if not self.client.has_access_token():
            await self.client.async_refresh_token()
        try:
            result = await self.client.async_get_first_device()
            return DeviceData.from_dict(result)
        except CatGenieApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except CatGenieApiClientError as exception:
            raise UpdateFailed(exception) from exception
        except Exception as exception:
            raise UnknownError from exception
