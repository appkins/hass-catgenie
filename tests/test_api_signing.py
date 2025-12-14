"""Test API client authentication and request signing."""

from __future__ import annotations

import hashlib
import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

import aiohttp
import pytest
from aioresponses import aioresponses

# Import the API client
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components"))

from catgenie.api import CatGenieApiClient


@pytest.fixture
def mock_session():
    """Create a mock aiohttp session."""
    session = Mock(spec=aiohttp.ClientSession)
    return session


@pytest.fixture
def api_client(mock_session):
    """Create an API client with mock session."""
    return CatGenieApiClient(
        refresh_token="test_refresh_token",
        session=mock_session,
    )


class TestRequestSigning:
    """Test request signing mechanism."""

    def test_build_signed_headers_contains_required_fields(self, api_client):
        """Test that signed headers include all required fields."""
        endpoint = "facade/v1/mobile-user/refreshToken/v2"
        body = '{"refreshToken":"test"}'

        headers = api_client._build_signed_headers(endpoint, body)

        # Check required headers
        assert "x-pm-en-ver" in headers
        assert "x-render-t" in headers
        assert "y-pm-sg-b" in headers
        assert "y-pm-sg-p" in headers

        # Check version
        assert headers["x-pm-en-ver"] == "1.0.0"

    def test_x_render_t_format(self, api_client):
        """Test x-render-t header format."""
        endpoint = "facade/v1/mobile-user/refreshToken/v2"
        headers = api_client._build_signed_headers(endpoint)

        x_render_t = headers["x-render-t"]

        # Should be: endpoint/timestamp
        assert x_render_t.startswith(endpoint)
        assert "/" in x_render_t

        # Extract timestamp
        parts = x_render_t.split("/")
        timestamp = parts[-1]

        # Should be a 13-digit number (milliseconds)
        assert timestamp.isdigit()
        assert len(timestamp) == 13

    def test_body_signature_is_sha256(self, api_client):
        """Test that body signature is SHA256 hash."""
        endpoint = "test/endpoint"
        body = '{"test":"data"}'

        headers = api_client._build_signed_headers(endpoint, body)

        expected_hash = hashlib.sha256(body.encode()).hexdigest()
        assert headers["y-pm-sg-b"] == expected_hash

    def test_path_signature_is_sha256(self, api_client):
        """Test that path signature is SHA256 hash."""
        endpoint = "facade/v1/mobile-user/refreshToken/v2"

        headers = api_client._build_signed_headers(endpoint)

        path = f"/{endpoint}"
        expected_hash = hashlib.sha256(path.encode()).hexdigest()
        assert headers["y-pm-sg-p"] == expected_hash

    def test_headers_include_authorization_when_token_present(self, api_client):
        """Test that Authorization header is included when access token exists."""
        # Set an access token
        api_client._access_token = "test_access_token"

        endpoint = "test/endpoint"
        headers = api_client._build_signed_headers(endpoint)

        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test_access_token"

    def test_timestamp_changes_between_calls(self, api_client):
        """Test that timestamp in x-render-t changes between calls."""
        endpoint = "test/endpoint"

        headers1 = api_client._build_signed_headers(endpoint)
        time.sleep(0.01)  # Small delay
        headers2 = api_client._build_signed_headers(endpoint)

        # Timestamps should be different
        assert headers1["x-render-t"] != headers2["x-render-t"]


class TestTokenRefresh:
    """Test token refresh with v2 endpoint."""

    @pytest.mark.asyncio
    async def test_refresh_token_uses_v2_endpoint(self, api_client):
        """Test that refresh token uses v2 endpoint with signing."""
        with aioresponses() as m:
            # Mock the v2 endpoint
            m.post(
                "https://iot.petnovations.com/facade/v1/mobile-user/refreshToken/v2",
                payload={
                    "token": "new_access_token",
                    "refreshToken": "test_refresh_token",
                    "expiration": "1751878863518",
                },
            )

            await api_client.async_refresh_token()

            # Check that token was updated
            assert api_client._access_token == "new_access_token"
            assert api_client.has_access_token()

    @pytest.mark.asyncio
    async def test_refresh_token_updates_expiration(self, api_client):
        """Test that token expiration is updated correctly."""
        expiration_ms = 1751878863518

        with aioresponses() as m:
            m.post(
                "https://iot.petnovations.com/facade/v1/mobile-user/refreshToken/v2",
                payload={
                    "token": "new_access_token",
                    "refreshToken": "test_refresh_token",
                    "expiration": str(expiration_ms),
                },
            )

            await api_client.async_refresh_token()

            # Check expiration was set correctly
            expected_time = datetime.fromtimestamp(
                expiration_ms / 1000,
                timezone.utc,
            )
            assert api_client._token_expiration == expected_time

    @pytest.mark.asyncio
    async def test_refresh_token_sends_signed_headers(self, api_client):
        """Test that refresh token sends properly signed headers."""
        with aioresponses() as m:
            m.post(
                "https://iot.petnovations.com/facade/v1/mobile-user/refreshToken/v2",
                payload={
                    "token": "new_access_token",
                    "refreshToken": "test_refresh_token",
                    "expiration": "1751878863518",
                },
            )

            await api_client.async_refresh_token()

            # Get the request that was made
            requests = m.requests
            assert len(requests) == 1

            request = requests[("POST", "https://iot.petnovations.com/facade/v1/mobile-user/refreshToken/v2")][0]
            headers = request.kwargs.get("headers", {})

            # Check signing headers are present
            assert "x-pm-en-ver" in headers
            assert "x-render-t" in headers
            assert "y-pm-sg-p" in headers


class TestAPIIntegration:
    """Test full API integration with signing."""

    @pytest.mark.asyncio
    async def test_api_wrapper_refreshes_token_when_expired(self, api_client):
        """Test that API wrapper refreshes token when expired."""
        # Set token as expired
        api_client._token_expiration = datetime.now(timezone.utc)

        with aioresponses() as m:
            # Mock refresh endpoint
            m.post(
                "https://iot.petnovations.com/facade/v1/mobile-user/refreshToken/v2",
                payload={
                    "token": "new_access_token",
                    "refreshToken": "test_refresh_token",
                    "expiration": str(int(time.time() * 1000) + 3600000),
                },
            )

            # Mock devices endpoint
            m.get(
                "https://iot.petnovations.com/device/device?useFleetIndexAndGetRealConnectivity=true",
                payload={"thingList": []},
            )

            # This should trigger a token refresh
            await api_client.async_get_devices()

            # Verify token was refreshed
            assert api_client._access_token == "new_access_token"


class TestErrorHandling:
    """Test error handling in authentication."""

    @pytest.mark.asyncio
    async def test_refresh_token_raises_on_auth_error(self, api_client):
        """Test that auth errors are raised properly."""
        with aioresponses() as m:
            m.post(
                "https://iot.petnovations.com/facade/v1/mobile-user/refreshToken/v2",
                status=401,
            )

            with pytest.raises(Exception):
                await api_client.async_refresh_token()

    @pytest.mark.asyncio
    async def test_api_handles_timeout(self, api_client):
        """Test that API handles timeouts gracefully."""
        with aioresponses() as m:
            m.post(
                "https://iot.petnovations.com/facade/v1/mobile-user/refreshToken/v2",
                exception=TimeoutError("Request timed out"),
            )

            with pytest.raises(Exception):
                await api_client.async_refresh_token()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
