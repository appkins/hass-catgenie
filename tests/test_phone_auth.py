"""Test phone authentication mechanism."""

from __future__ import annotations

import base64
import hashlib
import json
from unittest.mock import Mock, patch

import pytest

# Import the phone auth module
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components"))

from catgenie.phone import (
    build_headers,
    encrypt_phone_number,
    generate_body_signature,
    generate_path_signature,
    generate_signature,
    get_x_render_t,
    login_with_code,
    refresh_access_token,
    request_login_code,
)


class TestHeaderGeneration:
    """Test header generation functions."""

    def test_get_x_render_t_format(self):
        """Test x-render-t header format."""
        endpoint = "mobile-user/refreshToken/v2"
        result = get_x_render_t(endpoint)

        assert "/" in result
        parts = result.split("/")
        # Should be: mobile-user/refreshToken/v2/timestamp
        assert len(parts) == 4
        assert parts[0] == "mobile-user"
        assert parts[1] == "refreshToken"
        assert parts[2] == "v2"
        # Last part should be a timestamp (13 digits for milliseconds)
        assert parts[3].isdigit()
        assert len(parts[3]) == 13

    def test_generate_body_signature(self):
        """Test body signature generation."""
        body = '{"refreshToken": "test_token"}'
        signature = generate_body_signature(body)

        # Should be a SHA256 hex digest
        assert len(signature) == 64
        assert all(c in "0123456789abcdef" for c in signature)

        # Should be deterministic
        signature2 = generate_body_signature(body)
        assert signature == signature2

    def test_generate_path_signature(self):
        """Test path signature generation."""
        path = "/facade/v1/mobile-user/refreshToken/v2"
        signature = generate_path_signature(path)

        # Should be a SHA256 hex digest
        assert len(signature) == 64
        assert all(c in "0123456789abcdef" for c in signature)

    def test_generate_signature_returns_base64(self):
        """Test that signature is base64 encoded."""
        endpoint = "mobile-user/refreshToken/v2"
        body = '{"test": "data"}'

        signature = generate_signature(endpoint, body)

        # Should be valid base64
        try:
            decoded = base64.b64decode(signature)
            assert len(decoded) > 0
        except Exception as e:
            pytest.fail(f"Signature is not valid base64: {e}")

    def test_build_headers_contains_required_fields(self):
        """Test that build_headers includes all required fields."""
        endpoint = "mobile-user/refreshToken/v2"
        body = '{"test": "data"}'

        headers = build_headers(endpoint, body)

        # Check required headers
        assert "User-Agent" in headers
        assert "Content-Type" in headers
        assert "x-pm-en-ver" in headers
        assert "x-render-t" in headers
        assert "x-pm-en-dec" in headers
        assert "y-pm-sg-b" in headers
        assert "y-pm-sg-p" in headers

        # Check values
        assert headers["x-pm-en-ver"] == "1.0.0"
        assert headers["Content-Type"] == "application/json"
        assert "CatGenie" in headers["User-Agent"]


class TestEncryption:
    """Test encryption functions."""

    def test_encrypt_phone_number_returns_base64(self):
        """Test phone number encryption returns base64."""
        phone = "+14435551234"
        encrypted = encrypt_phone_number(phone)

        # Should be valid base64
        try:
            decoded = base64.b64decode(encrypted)
            assert len(decoded) > 0
        except Exception as e:
            pytest.fail(f"Encrypted phone is not valid base64: {e}")


class TestAPIRequests:
    """Test API request functions."""

    @patch("catgenie.phone.requests.post")
    def test_request_login_code_success(self, mock_post):
        """Test successful login code request."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_post.return_value = mock_response

        result = request_login_code("+14435551234")

        # Verify request was made
        assert mock_post.called
        call_args = mock_post.call_args

        # Check URL
        assert "iot.petnovations.com" in call_args[1]["url"]
        assert "generateLoginCode/v2" in call_args[1]["url"]

        # Check headers
        headers = call_args[1]["headers"]
        assert "x-render-t" in headers
        assert "x-pm-en-dec" in headers

        # Check result
        assert result == {"success": True}

    @patch("catgenie.phone.requests.post")
    def test_login_with_code_success(self, mock_post):
        """Test successful login with code."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "token": "access_token",
            "refreshToken": "refresh_token",
            "expiration": "1751878863518",
        }
        mock_post.return_value = mock_response

        result = login_with_code("encrypted_phone", "123456")

        # Verify request was made
        assert mock_post.called
        call_args = mock_post.call_args

        # Check URL
        assert "loginByPhoneNumber/v2" in call_args[1]["url"]

        # Check data
        data = call_args[1]["json"]
        assert data["str1"] == "encrypted_phone"
        assert data["code"] == "123456"

        # Check result
        assert "refreshToken" in result
        assert result["refreshToken"] == "refresh_token"

    @patch("catgenie.phone.requests.post")
    def test_refresh_access_token_success(self, mock_post):
        """Test successful token refresh."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "token": "new_access_token",
            "refreshToken": "same_refresh_token",
            "expiration": "1751878863518",
        }
        mock_post.return_value = mock_response

        result = refresh_access_token("test_refresh_token")

        # Verify request was made
        assert mock_post.called
        call_args = mock_post.call_args

        # Check URL
        assert "refreshToken/v2" in call_args[1]["url"]

        # Check data
        data = call_args[1]["json"]
        assert data["refreshToken"] == "test_refresh_token"

        # Check headers include signing
        headers = call_args[1]["headers"]
        assert "x-render-t" in headers
        assert "y-pm-sg-b" in headers
        assert "y-pm-sg-p" in headers

        # Check result
        assert "token" in result
        assert result["token"] == "new_access_token"

    @patch("catgenie.phone.requests.post")
    def test_request_handles_error(self, mock_post):
        """Test error handling in requests."""
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.raise_for_status.side_effect = Exception("Unauthorized")
        mock_post.return_value = mock_response

        with pytest.raises(Exception):
            request_login_code("+14435551234")


class TestSignatureValidation:
    """Test signature validation with known values."""

    def test_body_signature_matches_expected(self):
        """Test body signature against known hash."""
        # Known input and output
        body = '{"refreshToken":"test"}'
        expected_hash = hashlib.sha256(body.encode()).hexdigest()

        result = generate_body_signature(body)
        assert result == expected_hash

    def test_path_signature_matches_expected(self):
        """Test path signature against known hash."""
        # Known input and output
        path = "/facade/v1/mobile-user/refreshToken/v2"
        expected_hash = hashlib.sha256(path.encode()).hexdigest()

        result = generate_path_signature(path)
        assert result == expected_hash


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
