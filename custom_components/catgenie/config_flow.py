"""Adds config flow for CatGenie."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from aiohttp import hdrs
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME, CONF_TOKEN
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import (
    CatGenieApiClient,
    CatGenieApiClientAuthenticationError,
    CatGenieApiClientCommunicationError,
    CatGenieApiClientError,
)
from .const import CONF_SECRET, DOMAIN, HOST, LOGGER


class CatGenieHandler(ConfigFlow, domain=DOMAIN):
    """Config flow for CatGenie."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
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
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NAME,
                        default=(user_input or {}).get(CONF_NAME, vol.UNDEFINED),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                    vol.Required(CONF_TOKEN): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD,
                        ),
                    ),
                    vol.Required(CONF_SECRET): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD,
                        ),
                    ),
                },
            ),
            errors=_errors,
        )

    async def _test_credentials(self, refresh_token: str, secret: str) -> None:
        """Validate credentials."""
        client = CatGenieApiClient(
            refresh_token=refresh_token,
            secret=secret,
            session=async_create_clientsession(
                self.hass,
                base_url=f"https://{HOST}",
                headers={hdrs.HOST: HOST},
            ),
        )
        await client.async_get_devices()
