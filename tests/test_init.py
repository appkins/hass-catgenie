"""Test the CatGenie integration setup."""
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_TOKEN

from custom_components.catgenie import async_setup_entry, async_unload_entry
from custom_components.catgenie.const import DOMAIN


async def test_setup_entry_success(hass: HomeAssistant, mock_config_entry):
    """Test setup of config entry."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.catgenie.CatGenieCoordinator.async_config_entry_first_refresh",
        return_value=None,
    ) as mock_refresh, patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
        return_value=True,
    ) as mock_forward_setups:
        result = await async_setup_entry(hass, mock_config_entry)

    assert result is True
    assert len(mock_refresh.mock_calls) == 1
    assert len(mock_forward_setups.mock_calls) == 1
    assert DOMAIN in hass.data
    assert "coordinator" in hass.data[DOMAIN]


async def test_setup_entry_coordinator_refresh_failure(hass: HomeAssistant, mock_config_entry):
    """Test setup entry fails when coordinator refresh fails."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.catgenie.CatGenieCoordinator.async_config_entry_first_refresh",
        side_effect=Exception("Refresh failed"),
    ):
        with pytest.raises(Exception, match="Refresh failed"):
            await async_setup_entry(hass, mock_config_entry)


async def test_unload_entry(hass: HomeAssistant, mock_config_entry):
    """Test unloading a config entry."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_unload_platforms",
        return_value=True,
    ) as mock_unload:
        result = await async_unload_entry(hass, mock_config_entry)

    assert result is True
    assert len(mock_unload.mock_calls) == 1


async def test_reload_entry(hass: HomeAssistant, mock_config_entry):
    """Test reloading a config entry."""
    from custom_components.catgenie import async_reload_entry

    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.catgenie.async_unload_entry",
        return_value=True,
    ) as mock_unload, patch(
        "custom_components.catgenie.async_setup_entry",
        return_value=True,
    ) as mock_setup:
        await async_reload_entry(hass, mock_config_entry)

    assert len(mock_unload.mock_calls) == 1
    assert len(mock_setup.mock_calls) == 1
