"""Adds config flow for CatGenie."""

from __future__ import annotations

import re
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME, CONF_TOKEN
from homeassistant.helpers import selector

from .api import (
    CatGenieApiClient,
    CatGenieApiClientAuthenticationError,
    CatGenieApiClientCommunicationError,
    CatGenieApiClientError,
    async_create_session,
)
from .const import CONF_SECRET, DEFAULT_SECRET, DOMAIN, LOGGER
from .data import LoginResponse

CONF_COUNTRY_CODE = "country_code"
CONF_PHONE = "phone"
CONF_CODE = "code"


class CatGenieHandler(ConfigFlow, domain=DOMAIN):
    """Config flow for CatGenie."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._phone: str | None = None

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,  # noqa: ARG002
    ) -> ConfigFlowResult:
        """Let the user choose how to authenticate."""
        return self.async_show_menu(
            step_id="user",
            menu_options=["phone", "manual"],
        )

    async def async_step_phone(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Collect the phone number and send an SMS login code."""
        _errors: dict[str, str] = {}
        if user_input is not None:
            country_code = user_input[CONF_COUNTRY_CODE].strip()
            if not country_code.startswith("+"):
                country_code = f"+{country_code}"
            national = re.sub(r"\D", "", user_input[CONF_PHONE])
            phone = f"{country_code}{national}"
            try:
                await self._async_send_code(country_code, national, phone)
            except CatGenieApiClientCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except CatGenieApiClientError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                self._phone = phone
                return await self.async_step_code()

        return self.async_show_form(
            step_id="phone",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_COUNTRY_CODE, default="+1"
                    ): selector.TextSelector(),
                    vol.Required(CONF_PHONE): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEL,
                        ),
                    ),
                },
            ),
            errors=_errors,
        )

    async def async_step_code(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Complete login with the SMS code and store the refresh token."""
        _errors: dict[str, str] = {}
        if user_input is not None and self._phone is not None:
            try:
                login = await self._async_login(self._phone, user_input[CONF_CODE])
            except CatGenieApiClientAuthenticationError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "invalid_code"
            except CatGenieApiClientCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except CatGenieApiClientError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(login.account_id)
                self._abort_if_unique_id_configured()
                name = (
                    " ".join(
                        part for part in (login.first_name, login.last_name) if part
                    )
                    or "CatGenie"
                )
                return self.async_create_entry(
                    title=name,
                    data={
                        CONF_NAME: name,
                        CONF_TOKEN: login.refresh_token,
                        CONF_SECRET: DEFAULT_SECRET,
                    },
                )

        return self.async_show_form(
            step_id="code",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CODE): selector.TextSelector(),
                },
            ),
            errors=_errors,
        )

    async def async_step_manual(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Manually enter a refresh token and signing secret."""
        _errors: dict[str, str] = {}
        if user_input is not None:
            try:
                await self._test_credentials(
                    refresh_token=user_input[CONF_TOKEN],
                    secret=user_input[CONF_SECRET],
                )
            except CatGenieApiClientAuthenticationError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"
            except CatGenieApiClientCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except CatGenieApiClientError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="manual",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NAME,
                        default=(user_input or {}).get(CONF_NAME, vol.UNDEFINED),
                    ): selector.TextSelector(),
                    vol.Required(CONF_TOKEN): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD,
                        ),
                    ),
                    vol.Required(
                        CONF_SECRET, default=DEFAULT_SECRET
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD,
                        ),
                    ),
                },
            ),
            errors=_errors,
        )

    async def _async_send_code(
        self,
        country_code: str,
        national: str,
        phone: str,
    ) -> None:
        """Request an SMS login code (mirrors the app's pre-flight + request)."""
        session = async_create_session()
        client = CatGenieApiClient(
            refresh_token="",
            secret=DEFAULT_SECRET,
            session=session,
        )
        try:
            # The app hits config/v1/url with the phone before requesting a code.
            await client.async_get_config_url(country_code, national)
            await client.async_generate_login_code(phone)
        finally:
            await session.close()

    async def _async_login(self, phone: str, code: str) -> LoginResponse:
        """Exchange the SMS code for tokens."""
        session = async_create_session()
        client = CatGenieApiClient(
            refresh_token="",
            secret=DEFAULT_SECRET,
            session=session,
        )
        try:
            return await client.async_login_by_phone(phone, code)
        finally:
            await session.close()

    async def _test_credentials(self, refresh_token: str, secret: str) -> None:
        """Validate manually-entered credentials."""
        session = async_create_session()
        client = CatGenieApiClient(
            refresh_token=refresh_token,
            secret=secret,
            session=session,
        )
        try:
            await client.async_get_devices()
        finally:
            await session.close()
