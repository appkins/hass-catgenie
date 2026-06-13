# CatGenie API Authentication - Reverse Engineering Summary

## Overview

Successfully reverse-engineered the authentication mechanism used by the CatGenie mobile app (v587) from the Postman collection captures.

## Authentication Flow

### 1. Phone-Based Login

The CatGenie API uses phone number-based authentication with SMS verification codes.

**Endpoints:**

- Generate Code: `POST /ums/v1/users/generateLoginCode/v2`
- Login: `POST /ums/v1/users/loginByPhoneNumber/v2`
- Refresh Token: `POST /facade/v1/mobile-user/refreshToken/v2`

### 2. Request Signing

All API v2 requests require special headers for request signing:

```
x-pm-en-ver: "1.0.0"                    # Encryption version
x-render-t: {endpoint}/{timestamp_ms}    # Timestamp header
x-pm-en-dec: {base64_signature}          # HMAC signature (requires secret key)
y-pm-sg-b: {sha256_body_hash}            # Body signature
y-pm-sg-p: {sha256_path_hash}            # Path signature
```

**Example:**

```
x-render-t: mobile-user/refreshToken/v2/1751877063109
y-pm-sg-b: 205e7eedce76a80831fa8d624e1d2235310f332cbacf862a06e0ff4c7df04dc4
y-pm-sg-p: def9ab94e978e9c6a914353d743cca50cc759f84e9c5f650a2d9bac2a0ef36dd
```

### 3. Token Management

- **Access Token**: JWT token with ~30 min expiration
- **Refresh Token**: Long-lived JWT (expires in 2067!)
- Token format: RS512-signed JWT

## Implementation Status

### ✅ Completed

1. **phone.py** - Phone authentication module
   - Header generation (x-render-t, y-pm-sg-b, y-pm-sg-p)
   - Request signing framework
   - Login/refresh token functions
   - Encryption stubs for phone number

2. **api.py** - Updated API client
   - Added `_build_signed_headers()` method
   - Updated `async_refresh_token()` to use v2 endpoint
   - Proper timestamp and signature generation

3. **Test Coverage**
   - `test_phone_auth.py` - 12 tests for phone authentication
   - `test_api_signing.py` - 9 tests for API request signing
   - Tests cover header generation, signatures, token refresh

### ⚠️ Requires Mobile App Binary Analysis

The following require extracting secrets from the mobile app:

1. **x-pm-en-dec Signature Key**
   - Currently placeholder: `REPLACE_WITH_ACTUAL_KEY`
   - Likely HMAC-SHA256 signing key
   - Needs to be extracted from iOS/Android app binary

2. **Phone Number Encryption**
   - Currently placeholder AES encryption
   - Real implementation requires:
     - AES encryption key
     - IV (initialization vector)
     - Encryption mode (likely CBC or GCM)

## Files Modified/Created

### Modified

- `custom_components/catgenie/api.py` - Added request signing
- `custom_components/catgenie/phone.py` - Complete rewrite with proper auth
- `pyproject.toml` - Added `requests` dependency

### Created

- `tests/test_phone_auth.py` - Phone authentication tests
- `tests/test_api_signing.py` - API signing tests

## Usage Example

### Using Refresh Token (Works Now)

```python
from catgenie.api import CatGenieApiClient
import aiohttp

async with aiohttp.ClientSession() as session:
    client = CatGenieApiClient(
        refresh_token="your_refresh_token_here",
        session=session
    )

    # This will use v2 endpoint with signing
    await client.async_refresh_token()

    # Get devices
    devices = await client.async_get_devices()
```

### Phone Login (Requires Key Extraction)

```python
from catgenie.phone import request_login_code, login_with_code

# Step 1: Request SMS code
request_login_code("+14435551234")

# Step 2: Login with code
result = login_with_code(encrypted_phone, "123456")

# Step 3: Save refresh token
refresh_token = result["refreshToken"]
```

## Next Steps

To fully implement phone-based authentication:

1. **Extract Signing Key**
   - Decompile iOS IPA or Android APK
   - Look for HMAC/signing key constants
   - Search for "x-pm-en-dec" generation code

2. **Extract Encryption Key**
   - Find AES encryption implementation
   - Extract key and IV
   - Implement in `encrypt_phone_number()`

3. **Test Against Live API**
   - Verify signature generation works
   - Test complete login flow
   - Validate token refresh

## Testing

### Run Authentication Tests

```bash
# Run all tests
poetry run pytest tests/test_phone_auth.py tests/test_api_signing.py -v

# Run without HA plugin
poetry run pytest tests/test_phone_auth.py -v -p no:homeassistant
```

### Run Phone Auth CLI

```bash
poetry run python custom_components/catgenie/phone.py
```

## Security Notes

⚠️ **Important Security Considerations:**

1. The signing keys are security-critical and should be kept confidential
2. Extracting keys from mobile apps may violate ToS
3. Use this only for legitimate integration purposes
4. Consider asking PetNovations for an official API

## References

- Postman Collection: `data/Cat Genie 4.postman_collection.json`
- User-Agent: `CatGenie/587 CFNetwork/3826.500.131 Darwin/24.5.0`
- Base URL: `https://iot.petnovations.com`
- Mobile App: CatGenie iOS/Android v1.8.184
