"""Test the CatGenie config flow."""
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries, data_entry_flow, setup
from homeassistant.const import CONF_NAME, CONF_TOKEN

from custom_components.catgenie.const import DOMAIN
from custom_components.catgenie.api import (
    CatGenieApiClientAuthenticationError,
    CatGenieApiClientCommunicationError,
    CatGenieApiClientError,
)


async def test_form(hass):
    """Test we get the form."""
    await setup.async_setup_component(hass, "persistent_notification", {})
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {}


async def test_form_successful_flow(hass):
    """Test successful config flow."""
    await setup.async_setup_component(hass, "persistent_notification", {})

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {}

    with patch(
        "custom_components.catgenie.async_setup_entry", return_value=True
    ) as mock_setup_entry, patch(
        "custom_components.catgenie.api.CatGenieApiClient.async_get_devices",
        return_value=AsyncMock(),
    ) as mock_get_devices:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_NAME: "Test CatGenie",
                CONF_TOKEN: "test_refresh_token",
            },
        )

    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Test CatGenie"
    assert result2["data"] == {
        CONF_NAME: "Test CatGenie",
        CONF_TOKEN: "test_refresh_token",
    }
    assert len(mock_setup_entry.mock_calls) == 1
    assert len(mock_get_devices.mock_calls) == 1


async def test_form_authentication_error(hass):
    """Test we handle authentication error."""
    await setup.async_setup_component(hass, "persistent_notification", {})

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.catgenie.api.CatGenieApiClient.async_get_devices",
        side_effect=CatGenieApiClientAuthenticationError("Invalid token"),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_NAME: "Test CatGenie",
                CONF_TOKEN: "invalid_token",
            },
        )

    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["errors"] == {"base": "auth"}


async def test_form_communication_error(hass):
    """Test we handle communication error."""
    await setup.async_setup_component(hass, "persistent_notification", {})

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.catgenie.api.CatGenieApiClient.async_get_devices",
        side_effect=CatGenieApiClientCommunicationError("Connection failed"),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_NAME: "Test CatGenie",
                CONF_TOKEN: "test_token",
            },
        )

    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["errors"] == {"base": "connection"}


async def test_form_unknown_error(hass):
    """Test we handle unknown error."""
    await setup.async_setup_component(hass, "persistent_notification", {})

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.catgenie.api.CatGenieApiClient.async_get_devices",
        side_effect=CatGenieApiClientError("Unknown error"),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_NAME: "Test CatGenie",
                CONF_TOKEN: "test_token",
            },
        )

    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["errors"] == {"base": "unknown"}


async def test_form_exception_error(hass):
    """Test we handle general exception."""
    await setup.async_setup_component(hass, "persistent_notification", {})

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.catgenie.api.CatGenieApiClient.async_get_devices",
        side_effect=Exception("Unexpected error"),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_NAME: "Test CatGenie",
                CONF_TOKEN: "test_token",
            },
        )

    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["errors"] == {"base": "unknown"}


async def test_form_user_input_preserved_on_error(hass):
    """Test user input is preserved when validation fails."""
    await setup.async_setup_component(hass, "persistent_notification", {})

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.catgenie.api.CatGenieApiClient.async_get_devices",
        side_effect=CatGenieApiClientAuthenticationError("Invalid token"),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_NAME: "Test CatGenie",
                CONF_TOKEN: "invalid_token",
            },
        )

    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["errors"] == {"base": "auth"}
    # Check that the name field is pre-filled with the previous input
    name_field = result2["data_schema"].schema[CONF_NAME]
    assert name_field.default == "Test CatGenie"
