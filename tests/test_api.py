"""Test the CatGenie API client."""
import pytest
from aioresponses import aioresponses
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.catgenie.api import (
    CatGenieApiClient,
    CatGenieApiClientAuthenticationError,
    CatGenieApiClientCommunicationError,
    CatGenieApiClientError,
)


async def test_api_client_authentication_error(hass):
    """Test API client raises authentication error for 401."""
    session = async_get_clientsession(hass)
    client = CatGenieApiClient(refresh_token="invalid_token", session=session)

    with aioresponses() as mock_resp:
        mock_resp.post(
            "https://iot.petnovations.com/facade/v1/mobile-user/refreshToken",
            status=401,
            payload={"error": "Unauthorized"}
        )

        with pytest.raises(CatGenieApiClientAuthenticationError):
            await client.async_refresh_token()


async def test_api_client_communication_error(hass):
    """Test API client raises communication error for network issues."""
    session = async_get_clientsession(hass)
    client = CatGenieApiClient(refresh_token="test_token", session=session)

    with aioresponses() as mock_resp:
        mock_resp.post(
            "https://iot.petnovations.com/facade/v1/mobile-user/refreshToken",
            exception=ConnectionError("Network error")
        )

        with pytest.raises(CatGenieApiClientCommunicationError):
            await client.async_refresh_token()


async def test_api_client_unknown_error(hass):
    """Test API client raises generic error for other HTTP status codes."""
    session = async_get_clientsession(hass)
    client = CatGenieApiClient(refresh_token="test_token", session=session)

    with aioresponses() as mock_resp:
        mock_resp.post(
            "https://iot.petnovations.com/facade/v1/mobile-user/refreshToken",
            status=500,
            payload={"error": "Internal Server Error"}
        )

        with pytest.raises(CatGenieApiClientError):
            await client.async_refresh_token()


async def test_api_client_successful_token_refresh(hass):
    """Test API client successfully refreshes token."""
    session = async_get_clientsession(hass)
    client = CatGenieApiClient(refresh_token="valid_token", session=session)

    with aioresponses() as mock_resp:
        mock_resp.post(
            "https://iot.petnovations.com/facade/v1/mobile-user/refreshToken",
            status=200,
            payload={"access_token": "new_access_token", "expires_in": 3600}
        )

        await client.async_refresh_token()
        assert client.has_access_token()


async def test_api_client_get_devices_success(hass):
    """Test API client successfully gets devices."""
    session = async_get_clientsession(hass)
    client = CatGenieApiClient(refresh_token="valid_token", session=session)

    # Mock token refresh
    with aioresponses() as mock_resp:
        mock_resp.post(
            "https://iot.petnovations.com/facade/v1/mobile-user/refreshToken",
            status=200,
            payload={"access_token": "access_token", "expires_in": 3600}
        )

        mock_resp.get(
            "https://iot.petnovations.com/facade/v1/things",
            status=200,
            payload={
                "thingList": [
                    {
                        "manufacturerId": "test_device_id",
                        "name": "Test CatGenie",
                        "fwVersion": "1.0.0",
                        "reportedStatus": "connected"
                    }
                ]
            }
        )

        devices = await client.async_get_devices()
        assert len(devices.thing_list) == 1
        assert devices.thing_list[0].manufacturer_id == "test_device_id"
