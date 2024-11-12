"""Sample API Client."""

from __future__ import annotations

import socket
from typing import Any

import aiohttp
import async_timeout


class CatGenieApiClientError(Exception):
    """Exception to indicate a general API error."""


class CatGenieApiClientCommunicationError(
    CatGenieApiClientError,
):
    """Exception to indicate a communication error."""


class CatGenieApiClientAuthenticationError(
    CatGenieApiClientError,
):
    """Exception to indicate an authentication error."""


def _verify_response_or_raise(response: aiohttp.ClientResponse) -> None:
    """Verify that the response is valid."""
    if response.status in (401, 403):
        msg = "Invalid credentials"
        raise CatGenieApiClientAuthenticationError(
            msg,
        )
    response.raise_for_status()


class CatGenieApiClient:
    """Sample API Client."""

    def __init__(
        self,
        refresh_token: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Sample API Client."""
        self._base_url = f"https://iot.petnovations.com"
        self._refresh_token = refresh_token
        self._access_token = None
        self._session = session
        # self.device_list = {}

    async def async_get_data(self) -> Any:
        """Get data from the API."""
        return await self._api_wrapper(
            method="get",
            url="/device/device",
        )
    
    async def async_get_devices(self) -> dict:
        """Obtain the list of devices associated to a user."""
        resp = await self._api_wrapper("GET", url="/device/device")

        return {dev["manufacturerId"]: dev for dev in resp["thingList"]}
        # _LOGGER.debug("DEV_LIST: %s", self.device_list)

        # return self.device_list
    
    async def async_get_device_status(self, id) -> Any:
        """Obtain the list of devices associated to a user."""
        return await self._api_wrapper(
            method="GET",
            url=f"/device/management/{id}/operation/status"
        )
    
    async def async_get_access_token(self) -> Any:
        """Obtain a valid access token."""

        full_url = self._base_url + "/facade/v1/mobile-user/refreshToken"

        try:
            async with async_timeout.timeout(10):
                response = await self._session.request(
                    method="GET",
                    url=full_url,
                    headers={
                        "host": "iot.petnovations.com",
                        "content-type": "application/json",
                        "connection": "keep-alive",
                        "accept": "application/json, text/plain, */*",
                        "user-agent": "CatGenie/493 CFNetwork/1562 Darwin/24.0.0",
                        "content-length": "464",
                        "accept-language": "en-US,en;q=0.9",
                        "accept-encoding": "gzip, deflate, br",
                    },
                    json={
                        "refreshToken": self._refresh_token,
                    },
                )
                _verify_response_or_raise(response)
                if not response.ok:
                    return "Request failed, status " + str(response.status)
                
                r_json =  await response.json()
                if not r_json["success"]:
                    return f"Error {r_json['code']}: {r_json['msg']}"
                
                self._access_token = r_json["result"]["token"]
                return self._access_token
        except:
            return "Request failed, status ConnectionError"

    async def async_set_title(self, value: str) -> Any:
        """Get data from the API."""
        return await self._api_wrapper(
            method="patch",
            url="https://jsonplaceholder.typicode.com/posts/1",
            data={"title": value},
            headers={"Content-type": "application/json; charset=UTF-8"},
        )

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        data: dict | None = None,
        headers: dict | None = None,
    ) -> Any:
        """Get information from the API."""
        default_headers = {
            "authorization": f"Bearer {self._access_token}",
            "user-agent": "CatGenie/493 CFNetwork/1559 Darwin/24.0.0",
            "connection": "keep-alive",
            "accept": "application/json, text/plain, */*",  
            "host": "iot.petnovations.com",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9",
        }

        full_url = self._base_url + url

        try:
            async with async_timeout.timeout(10):
                response = await self._session.request(
                    method=method,
                    url=full_url,
                    headers=dict(default_headers, **headers),
                    json=data,
                )
                _verify_response_or_raise(response)
                return await response.json()

        except TimeoutError as exception:
            msg = f"Timeout error fetching information - {exception}"
            raise CatGenieApiClientCommunicationError(
                msg,
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error fetching information - {exception}"
            raise CatGenieApiClientCommunicationError(
                msg,
            ) from exception
        except Exception as exception:  # pylint: disable=broad-except
            msg = f"Something really wrong happened! - {exception}"
            raise CatGenieApiClientError(
                msg,
            ) from exception