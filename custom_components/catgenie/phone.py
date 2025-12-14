"""Phone-based authentication for CatGenie API.

This module implements the authentication mechanism used by the CatGenie mobile app.
The authentication uses custom headers for request signing:
- x-render-t: Endpoint path with timestamp
- x-pm-en-dec: Base64-encoded HMAC signature
- x-pm-en-ver: Encryption version (1.0.0)
- y-pm-sg-b: Body signature
- y-pm-sg-p: Path signature
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import time
from typing import Any

import requests

BASE_URL = "https://iot.petnovations.com"

# Standard headers used by the mobile app
STANDARD_HEADERS = {
    "User-Agent": "CatGenie/587 CFNetwork/3826.500.131 Darwin/24.5.0",
    "Content-Type": "application/json",
    "x-pm-en-ver": "1.0.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

# TODO: These keys need to be extracted from the mobile app binary
# For now, these are placeholders
SIGNING_KEY = b"REPLACE_WITH_ACTUAL_KEY"  # HMAC signing key
ENCRYPTION_KEY = b"REPLACE_WITH_ACTUAL_KEY"  # AES encryption key


def get_x_render_t(endpoint: str) -> str:
    """Generate x-render-t header value.

    Format: {endpoint_path}/{timestamp_ms}
    Example: mobile-user/refreshToken/v2/1751877063109
    """
    timestamp = str(int(time.time() * 1000))
    return f"{endpoint}/{timestamp}"


def generate_signature(endpoint: str, body: str = "") -> str:
    """Generate x-pm-en-dec signature.

    This appears to be an HMAC-SHA256 signature of the request.
    The exact algorithm needs to be extracted from the mobile app.
    """
    # Placeholder implementation
    # Real implementation would be: HMAC(signing_key, endpoint + timestamp + body)
    message = f"{endpoint}{int(time.time() * 1000)}{body}"
    signature = hmac.new(SIGNING_KEY, message.encode(), hashlib.sha256).digest()
    return base64.b64encode(signature).decode()


def generate_body_signature(body: str) -> str:
    """Generate y-pm-sg-b signature for request body."""
    return hashlib.sha256(body.encode()).hexdigest()


def generate_path_signature(path: str) -> str:
    """Generate y-pm-sg-p signature for request path."""
    return hashlib.sha256(path.encode()).hexdigest()


def encrypt_phone_number(phone: str) -> str:
    """Encrypt phone number using AES.

    The mobile app encrypts the phone number before sending.
    This needs to be extracted from the mobile app.
    """
    # Placeholder - needs actual AES-CBC or AES-GCM implementation
    # Real implementation would use Crypto.Cipher.AES
    return base64.b64encode(phone.encode()).decode()


def build_headers(endpoint: str, body: str = "") -> dict[str, str]:
    """Build complete headers for API request."""
    headers = STANDARD_HEADERS.copy()
    headers["x-render-t"] = get_x_render_t(endpoint)
    headers["x-pm-en-dec"] = generate_signature(endpoint, body)

    if body:
        headers["y-pm-sg-b"] = generate_body_signature(body)

    full_path = f"/{endpoint}"
    headers["y-pm-sg-p"] = generate_path_signature(full_path)

    return headers


def request_login_code(phone_number: str) -> dict[str, Any]:
    """Request SMS verification code for phone number.

    Args:
        phone_number: Phone number in international format (e.g., +14435551234)

    Returns:
        API response as dictionary
    """
    endpoint = "ums/v1/users/generateLoginCode/v2"
    url = f"{BASE_URL}/{endpoint}"

    encrypted_phone = encrypt_phone_number(phone_number)
    data = {"str1": encrypted_phone}
    body = str(data)

    headers = build_headers(endpoint, body)

    print("[*] Requesting login code...")
    resp = requests.post(url, json=data, headers=headers, timeout=30)
    print(f"[+] Status: {resp.status_code}")

    if resp.status_code == 200:
        result = resp.json()
        print("[+] Login code sent successfully")
        return result
    else:
        print(f"[-] Error: {resp.text}")
        resp.raise_for_status()
        return {}


def login_with_code(encrypted_phone: str, code: str) -> dict[str, Any]:
    """Login using phone number and verification code.

    Args:
        encrypted_phone: Base64-encoded encrypted phone number
        code: SMS verification code

    Returns:
        API response containing access and refresh tokens
    """
    endpoint = "ums/v1/users/loginByPhoneNumber/v2"
    url = f"{BASE_URL}/{endpoint}"

    data = {"str1": encrypted_phone, "code": code}
    body = str(data)

    headers = build_headers(endpoint, body)

    print("[*] Logging in with code...")
    resp = requests.post(url, json=data, headers=headers, timeout=30)
    print(f"[+] Status: {resp.status_code}")

    if resp.status_code == 200:
        result = resp.json()
        print("[+] Login successful")
        print(f"[+] Access token expires: {result.get('expiration')}")
        return result
    else:
        print(f"[-] Error: {resp.text}")
        resp.raise_for_status()
        return {}


def refresh_access_token(refresh_token: str) -> dict[str, Any]:
    """Refresh access token using refresh token.

    Args:
        refresh_token: JWT refresh token

    Returns:
        API response with new access token
    """
    endpoint = "facade/v1/mobile-user/refreshToken/v2"
    url = f"{BASE_URL}/{endpoint}"

    data = {"refreshToken": refresh_token}
    body = str(data)

    headers = build_headers(endpoint, body)

    print("[*] Refreshing token...")
    resp = requests.post(url, json=data, headers=headers, timeout=30)
    print(f"[+] Status: {resp.status_code}")

    if resp.status_code == 200:
        result = resp.json()
        print("[+] Token refreshed successfully")
        print(f"[+] New expiration: {result.get('expiration')}")
        return result
    else:
        print(f"[-] Error: {resp.text}")
        resp.raise_for_status()
        return {}


# --- MAIN ENTRYPOINT ---
if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("CatGenie Phone Authentication")
    print("=" * 60)
    print()
    print("⚠️  WARNING: This requires reverse-engineering the mobile app")
    print("   to extract the encryption and signing keys.")
    print()

    # Check if user wants to proceed
    proceed = input("Do you want to continue? (yes/no): ")
    if proceed.lower() != "yes":
        sys.exit(0)

    phone = input("Enter phone number (e.g., +14435551234): ")

    try:
        # Step 1: Request code
        request_login_code(phone)

        # Step 2: Get SMS code from user
        sms_code = input("\nEnter the verification code from SMS: ")

        # Step 3: Login with code
        encrypted_phone = encrypt_phone_number(phone)
        result = login_with_code(encrypted_phone, sms_code)

        if "refreshToken" in result:
            print("\n" + "=" * 60)
            print("Authentication successful!")
            print("=" * 60)
            print(f"\nRefresh Token: {result['refreshToken']}")
            print(f"\nSave this token to use with the integration.")
            print("\nYou can test token refresh with:")
            print(f"  python {__file__} --refresh <your_token>")
    except Exception as e:
        print(f"\n[-] Error: {e}")
        sys.exit(1)
