"""Exercise the integration's real login flow against the live API.

Runs the same two pre-account calls the app makes:
  1. GET  /config/v1/url   (region bootstrap, enc-only headers)
  2. POST /ums/v1/users/generateLoginCode/v2   (triggers the SMS)

Usage:  python test_login.py +1 4435691504
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "custom_components"))

import aiohttp  # noqa: E402

from petnovations.api import (  # noqa: E402
    CatGenieApiClient,
    async_create_session,
)
from petnovations.const import DEFAULT_SECRET  # noqa: E402
from petnovations.signing import build_phone_token, generate_signature_headers  # noqa: E402


async def main(country_code: str, national: str) -> None:
    phone = f"{country_code}{national}"
    print(f"[test] phone={phone}  country={country_code}  national={national}")

    # Show exactly what we will send (mirrors the app's generateLoginCode).
    path = "/ums/v1/users/generateLoginCode/v2"
    body = {"str1": build_phone_token(phone)}
    sig = generate_signature_headers(
        secret=DEFAULT_SECRET, path=path.lstrip("/"), method="POST", body=body
    )
    enc_only = {k: v for k, v in sig.items() if not k.startswith("y-pm-sg")}
    print("[test] generateLoginCode headers (enc-only):")
    for k, v in enc_only.items():
        print(f"         {k}: {v}")
    print(f"[test] body: {body}")

    session = async_create_session()
    client = CatGenieApiClient(refresh_token="", secret=DEFAULT_SECRET, session=session)
    try:
        print("\n[test] 1) GET /config/v1/url ...")
        try:
            cfg = await client.async_get_config_url(country_code, national)
            print(f"[test]    -> OK: {cfg}")
        except Exception as exc:  # noqa: BLE001
            print(f"[test]    -> FAILED: {type(exc).__name__}: {exc}")

        print("\n[test] 2) POST generateLoginCode/v2 ...")
        try:
            await client.async_generate_login_code(phone)
            print("[test]    -> OK (HTTP 2xx) — server accepted; SMS should send")
        except aiohttp.ClientResponseError as exc:
            print(f"[test]    -> HTTP ERROR {exc.status}: {exc.message}")
        except Exception as exc:  # noqa: BLE001
            print(f"[test]    -> FAILED: {type(exc).__name__}: {exc}")
    finally:
        await session.close()


if __name__ == "__main__":
    cc = sys.argv[1] if len(sys.argv) > 1 else "+1"
    nat = sys.argv[2] if len(sys.argv) > 2 else "4435691504"
    asyncio.run(main(cc, nat))
