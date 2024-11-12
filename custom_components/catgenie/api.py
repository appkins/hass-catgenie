"""Sample API Client."""

from __future__ import annotations

import json
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
        self._host = "iot.petnovations.com"
        self._base_url = f"https://{self._host}"
        session._base_url = self._base_url
        session.headers.update({
            "host": self._host,
            "user-agent": "CatGenie/493 CFNetwork/1559 Darwin/24.0.0",
            "connection": "keep-alive",
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9",
        })
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
        
    async def async_get_first_device(self) -> Any:
        """Get data from the API."""
        resp = await self._api_wrapper("GET", url="/device/device")
        return resp["thingList"][0]
    
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
        
    async def async_device_operation(self, id, state: int = 1) -> Any:
        """Obtain the list of devices associated to a user."""
        data = {"state": state}
        data_str = json.dumps(data)
        data_len = len(data_str)
        return await self._api_wrapper(
            method="POST",
            url=f"/device/management/{id}/operation",
            data={"state": state},
            headers={"content-type": "application/json", "content-length": data_len},
        )
    
    async def async_get_access_token(self) -> Any:
        """Obtain a valid access token."""

        full_url = self._base_url + "/facade/v1/mobile-user/refreshToken"

        try:
            async with async_timeout.timeout(10):
                response = await self._session.request(
                    method="POST",
                    url=full_url,
                    headers={
                        "host": self._host,
                        # "content-type": "application/json",
                        "connection": "keep-alive",
                        "accept": "application/json, text/plain, */*",
                        "user-agent": "CatGenie/493 CFNetwork/1562 Darwin/24.0.0",
                        # "content-length": "464",
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
                # if not r_json["success"]:
                #     return f"Error {r_json['code']}: {r_json['msg']}"
                
                # self._access_token = r_json["result"]["token"]
                self._access_token = r_json["token"]
                return self._access_token
        except aiohttp.ClientError as exception:
            return f"Request failed, status ConnectionError: {exception}"

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        data: dict | None = None,
        headers: dict | None = None,
    ) -> Any:
        """Get information from the API."""
        
        access_token = self._access_token
        
        if access_token is None:
            access_token = await self.async_get_access_token()
        
        default_headers = {
            "authorization": f"Bearer {access_token}",
            "user-agent": "CatGenie/493 CFNetwork/1559 Darwin/24.0.0",
            "connection": "keep-alive",
            "accept": "application/json, text/plain, */*",  
            "host": self._host,
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9",
        }
        
        if headers is None:
            headers = {}

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
