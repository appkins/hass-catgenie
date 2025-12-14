import time

import requests

BASE_URL = "https://iot.petnovations.com"

HEADERS = {
    "User-Agent": "CatGenie/587 CFNetwork/3826.500.131 Darwin/24.5.0",
    "Content-Type": "application/json",
    "x-pm-en-ver": "1.0.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}


def get_x_render_t(endpoint: str) -> str:
    timestamp = str(int(time.time() * 1000))
    return f"{endpoint}/{timestamp}"


def request_login_code(phone_number: str):
    url = f"{BASE_URL}/ums/v1/users/generateLoginCode/v2"

    # TODO: Replace with actual AES encryption of phone number
    encrypted_str1 = "REPLACE_WITH_ENCRYPTED_PHONE_BASE64"  # Placeholder

    data = {"str1": encrypted_str1}

    headers = HEADERS.copy()
    headers["x-render-t"] = get_x_render_t("ums/v1/users/generateLoginCode/v2")
    headers["x-pm-en-dec"] = "PLACEHOLDER_SIGNATURE"  # Should be HMAC/AES signed header

    print("[*] Requesting login code...")
    resp = requests.post(url, json=data, headers=headers)
    print(f"[+] Status: {resp.status_code}")
    print(resp.text)


def login_with_code(encrypted_str1: str, code: str):
    url = f"{BASE_URL}/ums/v1/users/loginByPhoneNumber/v2"

    data = {"str1": encrypted_str1, "code": code}

    headers = HEADERS.copy()
    headers["x-render-t"] = get_x_render_t("ums/v1/users/loginByPhoneNumber/v2")
    headers["x-pm-en-dec"] = "PLACEHOLDER_SIGNATURE"  # Again, should be generated

    print("[*] Logging in with code...")
    resp = requests.post(url, json=data, headers=headers)
    print(f"[+] Status: {resp.status_code}")
    print(resp.json())


def refresh_access_token(refresh_token: str):
    url = f"{BASE_URL}/facade/v1/mobile-user/refreshToken/v2"

    data = {"refreshToken": refresh_token}

    headers = HEADERS.copy()
    headers["x-render-t"] = get_x_render_t("mobile-user/refreshToken/v2")
    headers["x-pm-en-dec"] = "PLACEHOLDER_SIGNATURE"  # Also signed

    print("[*] Refreshing token...")
    resp = requests.post(url, json=data, headers=headers)
    print(f"[+] Status: {resp.status_code}")
    print(resp.json())


# --- MAIN ENTRYPOINT ---
if __name__ == "__main__":
    phone = "+14435551234"  # REPLACE with your phone number

    # Step 1: Request code
    request_login_code(phone)

    # Step 2: After receiving SMS code, manually enter here:
    sms_code = input("Enter the verification code: ")

    # Step 3: REPLACE with encrypted str1 for that number (from app capture)
    encrypted_str1 = "REPLACE_WITH_BASE64_STR1"

    login_with_code(encrypted_str1, sms_code)

    # If successful, copy refreshToken from response and:
    # refresh_access_token("PASTE_YOUR_REFRESH_TOKEN_HERE")
