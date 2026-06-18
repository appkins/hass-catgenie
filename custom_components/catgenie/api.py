"""Sample API Client."""

from __future__ import annotations

import socket
from datetime import UTC, datetime
from typing import Any

import aiohttp
import async_timeout

from .signing import generate_signature_headers


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
        secret: str,
    ) -> None:
        """Sample API Client."""
        self._refresh_token = refresh_token
        self._secret = secret
        self._access_token = None
        self._session = session
        self._token_expiration = datetime.now(UTC)

    async def async_get_first_device(self) -> Any:
        """Get data from the API."""
        resp = await self.async_get_devices()
        return resp[0]

    async def async_get_devices(self) -> list[dict[str, Any]]:
        """Obtain the list of devices associated to a user."""
        resp = await self._api_wrapper(
            aiohttp.hdrs.METH_GET,
            url="/device/device/v2",
            params={"useFleetIndexAndGetRealConnectivity": "true"},
        )
        return resp["thingList"]

    async def async_get_device_status(self, device_id: str) -> Any:
        """Obtain the list of devices associated to a user."""
        return await self._api_wrapper(
            method=aiohttp.hdrs.METH_GET,
            url=f"/device/management/{device_id}/operation/status",
        )

    async def async_device_operation(self, device_id: str, state: int = 1) -> Any:
        """Obtain the list of devices associated to a user."""
        return await self._api_wrapper(
            method=aiohttp.hdrs.METH_POST,
            url=f"/device/management/{device_id}/operation",
            data={"state": state},
        )

    def _is_token_expired(self) -> bool:
        """Check if the token is expired."""
        if self._access_token is None:
            return True
        return self._token_expiration <= datetime.now(UTC)

    def has_access_token(self) -> bool:
        """Check if the token is expired."""
        return self._access_token is not None

    @property
    def headers(self) -> dict[str, str]:
        """Return the access token."""
        if self._access_token is not None:
            return {aiohttp.hdrs.AUTHORIZATION: f"Bearer {self._access_token}"}
        return {}

    def _signature_headers(
        self,
        method: str,
        path: str,
        data: dict[Any, Any] | None = None,
        params: dict[Any, Any] | None = None,
    ) -> dict[str, str]:
        """Build the per-request signature headers."""
        return generate_signature_headers(
            secret=self._secret,
            path=path,
            method=method,
            body=data,
            params=params,
        )

    async def async_refresh_token(self) -> None:
        """Obtain a valid access token."""
        if self._access_token is not None:
            self._access_token = None

        path = "/facade/v1/mobile-user/refreshToken"
        body = {"refreshToken": self._refresh_token}

        try:
            async with async_timeout.timeout(10):
                response = await self._session.post(
                    url=path,
                    json=body,
                    headers={
                        **self.headers,
                        **self._signature_headers(
                            aiohttp.hdrs.METH_POST,
                            path,
                            data=body,
                        ),
                    },
                )
                _verify_response_or_raise(response)

                data = await response.json()

                expiration = data["expiration"]
                access_token = data["token"]

                self._access_token = access_token

                self._token_expiration = datetime.fromtimestamp(
                    float(int(expiration) / 1000),
                    UTC,
                )
        except Exception as exception:  # pylint: disable=broad-except
            msg = f"Error refreshing token - {exception}"
            raise CatGenieApiClientError(
                msg,
            ) from exception

    async def _api_wrapper_inner(
        self,
        method: str,
        url: str,
        data: dict[Any,Any] | None = None,
        params: dict[Any,Any] | None = None,
        headers: dict[str,str] | None = None,
    ) -> Any:
        """Get information from the API."""
        real_headers = self.headers
        real_headers.update(
            self._signature_headers(method, url, data=data, params=params),
        )
        if headers is not None:
            real_headers.update(headers)

        async with async_timeout.timeout(10):
            response = await self._session.request(
                method=method,
                url=url,
                headers=real_headers,
                json=data,
                params=params,
            )
            _verify_response_or_raise(response)
            return await response.json()

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        data: dict[Any,Any] | None = None,
        params: dict[Any,Any] | None = None,
        headers: dict[str,str] | None = None,
    ) -> Any:
        """Get information from the API."""
        if self._is_token_expired():
            await self.async_refresh_token()

        try:
            return await self._api_wrapper_inner(
                method=method,
                url=url,
                data=data,
                params=params,
                headers=headers,
            )
        except CatGenieApiClientAuthenticationError:
            try:
                await self.async_refresh_token()
                return await self._api_wrapper_inner(
                    method=method,
                    url=url,
                    data=data,
                    params=params,
                    headers=headers,
                )
            except Exception as exception:  # pylint: disable=broad-except
                msg = f"Something really wrong happened! - {exception}"
                raise CatGenieApiClientError(
                    msg,
                ) from exception
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
