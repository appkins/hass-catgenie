# CatGenie API Integration - Critical Blocker

## Current Status: 🔴 BLOCKED

**The integration is currently non-functional** because:

1. ✅ All API endpoints (v1 and v2) now require request signing
2. ❌ The `SIGNING_KEY` required for `x-pm-en-dec` header cannot be extracted from the app
3. ❌ Without valid `x-pm-en-dec` signatures, ALL API requests will fail with 401/403

## What Changed

PetNovations updated their API to require signed requests for security. Every request must include:

```
x-pm-en-dec: {base64_hmac_signature}  ← Requires SIGNING_KEY
x-render-t: {path}/{timestamp_ms}
x-pm-en-ver: 1.0.0
y-pm-sg-b: {sha256_of_body}
y-pm-sg-p: {sha256_of_path}
authorization: Bearer {access_token}
```

## Required Actions

### Option 1: Extract Signing Key (Recommended)

**Use Proxyman to intercept network traffic:**

```bash
# Install Proxyman
brew install --cask proxyman

# Steps:
# 1. Open Proxyman
# 2. Menu → Certificate → Install Certificate on this Mac
# 3. Enable SSL Proxying for iot.petnovations.com
# 4. Open CatGenie app
# 5. Trigger some actions (refresh, start cleaning, etc.)
# 6. Collect multiple request/signature pairs
# 7. Use the reverse engineering script below
```

**Then test captured data:**

```python
# Use /tmp/test_real_signature.py with captured values
# Fill in CAPTURED_TIMESTAMP, CAPTURED_BODY, CAPTURED_PATH, CAPTURED_SIGNATURE
# Run to find the signing key through pattern matching
python3 /tmp/test_real_signature.py
```

**If pattern matching fails, try brute-force approaches:**
- Compare multiple signatures from different requests
- Look for common patterns in the signing data
- Try XOR operations on signatures to find key material

### Option 2: Decompile the App Binary

```bash
# Install Hopper Disassembler (paid) or Ghidra (free)
brew install --cask ghidra

# Load the binary
open /Applications/CatGenie.app/Wrapper/CatGenie.app/CatGenie

# Search for:
# - String references to "x-pm-en-dec"
# - CryptoJS.HmacSHA256 calls
# - Key initialization code
```

### Option 3: Runtime Hooking with Frida

```bash
# Install Frida
brew install frida-tools
pip3 install frida

# Hook crypto operations
frida -U -n CatGenie -l hook_crypto.js

# Save this as hook_crypto.js:
```

```javascript
// Frida script to intercept crypto calls
if (ObjC.available) {
    // Hook HMAC operations
    var CryptoJS = ObjC.classes.NSObject;
    
    Interceptor.attach(Module.findExportByName(null, 'CCHmac'), {
        onEnter: function(args) {
            console.log('[*] CCHmac called');
            console.log('    Algorithm: ' + args[0]);
            console.log('    Key: ' + Memory.readUtf8String(args[1]));
            console.log('    Key length: ' + args[2]);
            console.log('    Data: ' + Memory.readUtf8String(args[3]));
        }
    });
}
```

### Option 4: Contact PetNovations

```
Email: support@petnovations.com
Subject: API Access for Home Assistant Integration

Request:
- Official API documentation
- API keys for third-party integrations
- OAuth or other supported authentication methods
```

### Option 5: Web Scraping Alternative

If the web interface doesn't require signing:
```python
# Use Selenium/Playwright to control the web app
# Extract data from the DOM instead of using the API
```

## Files to Update Once Key is Found

1. **custom_components/catgenie/phone.py**
   ```python
   # Line 17-18: Replace placeholders
   SIGNING_KEY = b"ACTUAL_KEY_HERE"
   ENCRYPTION_KEY = b"ACTUAL_KEY_HERE"
   ```

2. **custom_components/catgenie/api.py**
   ```python
   # Line 130: Add actual signature generation
   def _build_signed_headers(self, endpoint: str, body: str = "") -> dict[str, str]:
       # ... existing code ...
       
       # Add the actual HMAC signature
       import hmac
       import base64
       
       SIGNING_KEY = b"ACTUAL_KEY_HERE"
       data_to_sign = f"{timestamp}.{body_hash}.{path_hash}"
       signature = hmac.new(SIGNING_KEY, data_to_sign.encode(), hashlib.sha256).digest()
       headers["x-pm-en-dec"] = base64.b64encode(signature).decode()
       
       return headers
   ```

3. **All API calls need signing**
   ```python
   # Update _api_wrapper to add signed headers for ALL requests
   async def _api_wrapper(...):
       # Determine if we need to build full URL
       if not url.startswith('http'):
           endpoint = url.lstrip('/')
           url = f"https://iot.petnovations.com/{endpoint}"
           
           # Add signed headers
           signed_headers = self._build_signed_headers(endpoint, json.dumps(data) if data else "")
           if headers:
               signed_headers.update(headers)
           headers = signed_headers
   ```

## Next Steps

1. ✅ Document the problem (this file)
2. ⏳ Use Proxyman to capture real API requests
3. ⏳ Run reverse engineering script with captured data
4. ⏳ Update code with actual signing key
5. ⏳ Test integration with real device

## Resources

- `/tmp/test_real_signature.py` - Reverse engineering script
- `/tmp/advanced_key_search.py` - JS bundle analysis
- `data/Cat Genie 4.postman_collection.json` - API examples with signatures
- `/tmp/intercept_catgenie_api.md` - Network interception guide
