"""Exercise the token-refresh endpoint with full wire-level logging.

Reads the refresh token from out/credentials.txt (or supply one on the CLI)
and calls the integration's async_refresh_token() with an aiohttp TraceConfig
that prints every detail before the bytes leave the socket and again when the
response arrives.

Usage:
    python test_refresh.py                          # reads out/credentials.txt
    python test_refresh.py <refresh_token>          # explicit token
    python test_refresh.py <refresh_token> <secret> # explicit token + secret
"""

from __future__ import annotations

import asyncio
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "custom_components"))

import aiohttp  # noqa: E402

from petnovations.api import CatGenieApiClient  # noqa: E402
from petnovations.const import DEFAULT_SECRET  # noqa: E402

_CREDENTIALS = Path(__file__).parent / "out" / "credentials.txt"


def _load_credentials() -> tuple[str, str]:
    """Pull refresh token and secret out of out/credentials.txt."""
    text = _CREDENTIALS.read_text()
    token_m = re.search(r"token \([^)]+\):\s*(\S+)", text)
    secret_m = re.search(r"secret \([^)]+\):\s*(\S+)", text)
    if not token_m:
        raise SystemExit(f"Could not parse refresh token from {_CREDENTIALS}")
    token = token_m.group(1)
    secret = secret_m.group(1) if secret_m else DEFAULT_SECRET
    return token, secret


# ---------------------------------------------------------------------------
# aiohttp trace hooks — fired in the session's event loop, before/after I/O
# ---------------------------------------------------------------------------

async def _on_request_start(
    _session: aiohttp.ClientSession,
    _ctx: aiohttp.TraceRequestStartParams,
    params: aiohttp.TraceRequestStartParams,
) -> None:
    print(f"\n>>> REQUEST  {params.method} {params.url}")
    for k, v in params.headers.items():
        print(f"    {k}: {v}")


async def _on_request_chunk_sent(
    _session: aiohttp.ClientSession,
    _ctx: aiohttp.TraceRequestChunkSentParams,
    params: aiohttp.TraceRequestChunkSentParams,
) -> None:
    if params.chunk:
        print(f"    body: {params.chunk.decode(errors='replace')}")


async def _on_response_chunk_received(
    _session: aiohttp.ClientSession,
    _ctx: aiohttp.TraceResponseChunkReceivedParams,
    params: aiohttp.TraceResponseChunkReceivedParams,
) -> None:
    if params.chunk:
        print(f"<<< body chunk: {params.chunk.decode(errors='replace')}")


async def _on_request_end(
    _session: aiohttp.ClientSession,
    _ctx: aiohttp.TraceRequestEndParams,
    params: aiohttp.TraceRequestEndParams,
) -> None:
    print(f"<<< RESPONSE {params.response.status} {params.response.reason}")
    for k, v in params.response.headers.items():
        print(f"    {k}: {v}")


async def _on_request_exception(
    _session: aiohttp.ClientSession,
    _ctx: aiohttp.TraceRequestExceptionParams,
    params: aiohttp.TraceRequestExceptionParams,
) -> None:
    print(f"<<< EXCEPTION {type(params.exception).__name__}: {params.exception}")


def _build_trace_config() -> aiohttp.TraceConfig:
    tc = aiohttp.TraceConfig()
    tc.on_request_start.append(_on_request_start)
    tc.on_request_chunk_sent.append(_on_request_chunk_sent)
    tc.on_response_chunk_received.append(_on_response_chunk_received)
    tc.on_request_end.append(_on_request_end)
    tc.on_request_exception.append(_on_request_exception)
    return tc


async def main(refresh_token: str, secret: str) -> None:
    print(f"[refresh] token (first 40 chars): {refresh_token[:40]}…")
    print(f"[refresh] secret (first 20 chars): {secret[:20]}…")

    tc = _build_trace_config()
    connector = aiohttp.TCPConnector(resolver=aiohttp.ThreadedResolver())
    from petnovations.api import DEFAULT_HEADERS
    from petnovations.const import HOST

    async with aiohttp.ClientSession(
        base_url=f"https://{HOST}",
        connector=connector,
        headers=DEFAULT_HEADERS,
        trace_configs=[tc],
    ) as session:
        client = CatGenieApiClient(
            refresh_token=refresh_token,
            secret=secret,
            session=session,
        )
        try:
            await client.async_refresh_token()
            print("\n[refresh] SUCCESS")
            print(f"[refresh] access token (first 40): {client._access_token[:40]}…")  # noqa: SLF001
            print(f"[refresh] expires: {client._token_expiration}")  # noqa: SLF001
        except Exception as exc:  # noqa: BLE001
            print(f"\n[refresh] FAILED: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        tok = sys.argv[1]
        sec = sys.argv[2] if len(sys.argv) >= 3 else DEFAULT_SECRET
    else:
        tok, sec = _load_credentials()

    asyncio.run(main(tok, sec))
