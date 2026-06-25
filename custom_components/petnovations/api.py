"""Sample API Client."""

from __future__ import annotations

import json
import socket
from datetime import UTC, datetime
from typing import Any

import aiohttp
import async_timeout

from .const import ENDPOINT_REFRESH, ENDPOINT_REFRESH_SIGN_PATH, HOST
from .data import GenerateLoginCodeRequest, LoginRequest, LoginResponse
from .signing import build_phone_token, generate_signature_headers

# Default headers sent with every request (mirrors the mobile app).
DEFAULT_HEADERS: dict[str, str] = {
    aiohttp.hdrs.HOST: HOST,
    # The Android app uses React Native's OkHttp default UA (it sets none itself).
    aiohttp.hdrs.USER_AGENT: "okhttp/4.9.2",
    aiohttp.hdrs.CONNECTION: "keep-alive",
    aiohttp.hdrs.ACCEPT: "application/json, text/plain, */*",
    aiohttp.hdrs.ACCEPT_ENCODING: "gzip, deflate, br",
    aiohttp.hdrs.ACCEPT_LANGUAGE: "en-US",
}


def async_create_session() -> aiohttp.ClientSession:
    """Create the API ClientSession.

    A dedicated session is used (rather than Home Assistant's shared one)
    because it must use aiohttp's ``ThreadedResolver``. HA's shared session uses
    the async (aiodns/pycares) resolver, and ``pycares`` >= 5 changed
    ``Channel.getaddrinfo()`` in a way that crashes ``aiodns`` 3.5.0 (the version
    HA pins). The threaded resolver sidesteps that and keeps DNS working
    regardless of the installed ``pycares`` version.

    The caller owns the session and must close it (e.g. via
    ``entry.async_on_unload(session.close)``).
    """
    connector = aiohttp.TCPConnector(resolver=aiohttp.ThreadedResolver())
    return aiohttp.ClientSession(
        base_url=f"https://{HOST}",
        connector=connector,
        headers=DEFAULT_HEADERS,
    )


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


async def _decode_json(response: aiohttp.ClientResponse) -> Any:
    """Decode a response body as JSON.

    Centralised so every call site handles the API's quirks identically: some
    endpoints serve JSON with a ``text/plain`` content type (so the built-in
    ``response.json()`` content-type check is bypassed) and others return an
    empty ``200`` body (e.g. configuration writes). A non-JSON body is returned
    verbatim.
    """
    body = await response.text()
    if not body:
        return None
    try:
        return json.loads(body)
    except ValueError:
        return body


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
            params={"useFleetIndexAndGetRealConnectivity": "false"},
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

    async def async_set_mode(
        self,
        device_id: str,
        *,
        mode: int,
        manual: int,
        schedule: list[str] | None = None,
    ) -> Any:
        """Set the device activation mode.

        ``mode``: 0 = cat activation, 1 = time activation.
        ``manual``: 1 enables manual mode (takes precedence over ``mode``).
        ``schedule``: required when ``mode`` is 1 (time activation),
        e.g. ``["08:31:00"]``.
        """
        body: dict[str, Any] = {"mode": mode, "manual": manual}
        if schedule is not None:
            body["schedule"] = schedule
        return await self._api_wrapper(
            method=aiohttp.hdrs.METH_PUT,
            url=f"/device/management/{device_id}/configuration",
            data=body,
        )

    async def async_set_child_lock(self, device_id: str, *, enabled: bool) -> Any:
        """Enable or disable the child lock.

        Sent as the ``childLock`` configuration field (1 = locked, 0 = open).
        """
        return await self.async_set_configuration(
            device_id, childLock=1 if enabled else 0
        )

    async def async_set_configuration(self, device_id: str, **fields: Any) -> Any:
        """Update arbitrary device configuration fields.

        ``fields`` are the camelCase API keys of the ``configuration`` object
        (e.g. ``catDelay``, ``volumeLevel``, ``extraDry``,
        ``binaryElements={"EXTRA_WASH": True}``). The device accepts partial
        updates, so only the supplied keys are changed.
        """
        return await self._api_wrapper(
            method=aiohttp.hdrs.METH_PUT,
            url=f"/device/management/{device_id}/configuration",
            data=fields,
        )

    async def async_get_notifications(self) -> list[dict[str, Any]]:
        """Return the user's push-notification feed (cat visits, cycles, etc.).

        This is the pollable counterpart to the app's ``notification/v1/mobile/
        attach`` registration: HA has no FCM token to register for real push, so
        we read the same events the cloud would have pushed.
        """
        resp = await self._api_wrapper(
            method=aiohttp.hdrs.METH_GET,
            url="/notification/v1/push/user",
        )
        if isinstance(resp, dict):
            for key in ("notifications", "pushList", "pushes", "content"):
                value = resp.get(key)
                if isinstance(value, list):
                    return value
            return []
        if isinstance(resp, list):
            return resp
        return []

    async def async_get_pet_statistics(
        self,
        start_time: datetime | None = None,
    ) -> dict[str, Any]:
        """Get pet usage statistics (visits, cleaning cycles, pets).

        ``start_time`` is sent as an ISO-8601 UTC string with millisecond
        precision (e.g. ``2026-05-19T00:00:00.000Z``), matching the app.
        """
        params: dict[str, Any] = {}
        if start_time is not None:
            stamp = start_time.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")
            params["startTime"] = f"{stamp[:-3]}Z"
        return await self._api_wrapper(
            method=aiohttp.hdrs.METH_GET,
            url="/device/history/account/pet/statistics",
            params=params or None,
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

    def _enc_only_headers(
        self,
        method: str,
        path: str,
        data: dict[Any, Any] | None = None,
        params: dict[Any, Any] | None = None,
    ) -> dict[str, str]:
        """Signature headers without the HMAC pair (for the no-auth endpoints)."""
        sig = self._signature_headers(method, path, data=data, params=params)
        return {k: v for k, v in sig.items() if not k.startswith("y-pm-sg")}

    async def async_get_config_url(
        self,
        country_code: str,
        phone: str,
    ) -> dict[str, Any]:
        """Region/URL bootstrap the app calls before requesting a login code.

        ``country_code`` is the dialing code (e.g. ``+1``) and ``phone`` the
        national number. aiohttp encodes the ``+`` as ``%2B`` automatically.
        """
        path = "/config/v1/url"
        params = {"countryCode": country_code, "phone": phone}
        headers = self._enc_only_headers(aiohttp.hdrs.METH_GET, path, params=params)
        try:
            async with async_timeout.timeout(10):
                response = await self._session.get(
                    url=path,
                    params=params,
                    headers=headers,
                )
                response.raise_for_status()
                return await _decode_json(response)
        except TimeoutError as exception:
            msg = f"Timeout fetching config url - {exception}"
            raise CatGenieApiClientCommunicationError(msg) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error fetching config url - {exception}"
            raise CatGenieApiClientCommunicationError(msg) from exception

    async def async_generate_login_code(self, phone: str) -> None:
        """Request an SMS login code for an E.164 phone number (e.g. +1555…).

        Unauthenticated; signed with the encryption header only (the app does
        not send an HMAC signature for this call).
        """
        path = "/ums/v1/users/generateLoginCode/v2"
        body = GenerateLoginCodeRequest(str1=build_phone_token(phone)).to_body()
        headers = self._enc_only_headers(aiohttp.hdrs.METH_POST, path, data=body)
        try:
            async with async_timeout.timeout(10):
                response = await self._session.post(
                    url=path,
                    json=body,
                    headers=headers,
                )
                response.raise_for_status()
        except TimeoutError as exception:
            msg = f"Timeout requesting login code - {exception}"
            raise CatGenieApiClientCommunicationError(msg) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error requesting login code - {exception}"
            raise CatGenieApiClientCommunicationError(msg) from exception

    async def async_login_by_phone(self, phone: str, code: str) -> LoginResponse:
        """Complete phone login with the SMS code; returns tokens + profile."""
        path = "/ums/v1/users/loginByPhoneNumber/v2"
        body = LoginRequest(str1=build_phone_token(phone), code=code).to_body()
        headers = self._signature_headers(aiohttp.hdrs.METH_POST, path, data=body)
        try:
            async with async_timeout.timeout(10):
                response = await self._session.post(
                    url=path,
                    json=body,
                    headers=headers,
                )
                if response.status in (400, 401, 403):
                    msg = "Invalid or expired login code"
                    raise CatGenieApiClientAuthenticationError(msg)
                response.raise_for_status()
                data = await _decode_json(response)
                return LoginResponse.from_dict(data)
        except CatGenieApiClientAuthenticationError:
            raise
        except TimeoutError as exception:
            msg = f"Timeout during login - {exception}"
            raise CatGenieApiClientCommunicationError(msg) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error during login - {exception}"
            raise CatGenieApiClientCommunicationError(msg) from exception

    async def async_refresh_token(self) -> None:
        """Obtain a valid access token."""
        if self._access_token is not None:
            self._access_token = None

        body = {"refreshToken": self._refresh_token}

        try:
            async with async_timeout.timeout(10):
                response = await self._session.post(
                    url=ENDPOINT_REFRESH,
                    json=body,
                    headers={
                        **self.headers,
                        # The facade service signs relative to its /facade/v1/
                        # base, so x-render-t omits that prefix.
                        **self._signature_headers(
                            aiohttp.hdrs.METH_POST,
                            ENDPOINT_REFRESH_SIGN_PATH,
                            data=body,
                        ),
                    },
                )
                _verify_response_or_raise(response)

                data = await _decode_json(response)

                expiration = data["expiration"]
                access_token = data["token"]

                self._access_token = access_token

                self._token_expiration = datetime.fromtimestamp(
                    float(int(expiration) / 1000),
                    UTC,
                )
        except CatGenieApiClientAuthenticationError:
            raise
        except Exception as exception:  # pylint: disable=broad-except
            msg = f"Error refreshing token - {exception}"
            raise CatGenieApiClientError(
                msg,
            ) from exception

    async def _api_wrapper_inner(
        self,
        method: str,
        url: str,
        data: dict[Any, Any] | None = None,
        params: dict[Any, Any] | None = None,
        headers: dict[str, str] | None = None,
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
            return await _decode_json(response)

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        data: dict[Any, Any] | None = None,
        params: dict[Any, Any] | None = None,
        headers: dict[str, str] | None = None,
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
            except CatGenieApiClientAuthenticationError:
                raise
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
