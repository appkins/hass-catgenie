"""Request signing for the CatGenie (petnovations) IoT API.

The mobile API requires every request to be signed with a set of custom
headers. The algorithm was reverse engineered from the React Native app and is
documented in ``docs/SIGNATURE_ALGORITHM.md``.

Each request must carry:

* ``x-pm-en-dec`` - AES-CBC encrypted timestamp (Base64)
* ``x-pm-en-ver`` - encryption version (``1.0.0``)
* ``x-render-t``  - ``<path>/<timestamp>``
* ``y-pm-sg-b``   - HMAC-SHA256 of the serialized body + ``x-render-t``
* ``y-pm-sg-p``   - HMAC-SHA256 of the serialized params + ``x-render-t``
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import random
import re
import time
from typing import Any

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from .const import AES_KEY, DERIVATION_PARAMS, EN_VER

_AES_KEY_BYTES = AES_KEY.encode("utf-8")
_AES_IV = b"\x00" * 16


def derive_hmac_key(secret: str, environment: str = "production") -> str:
    """Derive the 32-character HMAC key from the account secret.

    Algorithm: ``prefix + secret[index:index + 28] + suffix``.
    """
    params = DERIVATION_PARAMS.get(environment, DERIVATION_PARAMS["production"])
    index_str, prefix, suffix = params.split("-")
    index = int(index_str)
    return prefix + secret[index : index + 28] + suffix


def serialize_data(data: dict[str, Any] | None) -> str:
    """Serialize request data for signing.

    Keys are sorted in reverse alphabetical order, their values concatenated
    (skipping ``None`` and ``imageContent``), then spaces are stripped and the
    result is lower-cased.
    """
    if not data:
        return ""

    result = ""
    for key in sorted(data.keys(), reverse=True):
        value = data.get(key)
        if value is not None and key != "imageContent":
            result += str(value)

    return result.replace(" ", "").lower()


def _hmac_sha256(key: str, message: str) -> str:
    """Return the lowercase hex HMAC-SHA256 of ``message`` under ``key``."""
    return hmac.new(
        key.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


_APP_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXTZabcdefghiklmnopqrstuvwxyz"


def _random_suffix(length: int) -> str:
    """Return a random string from the app's 61-char alphabet."""
    return "".join(random.choice(_APP_ALPHABET) for _ in range(length))  # noqa: S311


def _app_suffix(length: int, insert: str) -> str:
    """Return ``length`` random chars with ``insert`` injected at a random position.

    Mirrors the app's ``T(I(length), insert)`` function — produces a suffix of
    ``length + 1`` total characters with exactly one uppercase injection character.
    Used for ``str1`` (inserts 'X') and ``x-pm-en-dec`` (inserts 'Z').
    """
    base = _random_suffix(length)
    pos = random.randint(0, length)  # noqa: S311
    return base[:pos] + insert.upper() + base[pos:]


def aes_encrypt(plaintext: str) -> str:
    """AES-CBC encrypt (static key, zero IV, PKCS7) and base64-encode."""
    padder = padding.PKCS7(128).padder()
    padded = padder.update(plaintext.encode("utf-8")) + padder.finalize()
    cipher = Cipher(algorithms.AES(_AES_KEY_BYTES), modes.CBC(_AES_IV))
    encryptor = cipher.encryptor()
    return base64.b64encode(encryptor.update(padded) + encryptor.finalize()).decode(
        "utf-8"
    )


def build_phone_token(phone: str) -> str:
    """Build the login ``str1`` field.

    Mirrors the app's ``pE(phone)`` function: AES-CBC encrypt of
    ``"{phone}-{T(I(7),'x')}"`` — 7 chars from the app alphabet with one
    uppercase 'X' injected at a random position (8-char suffix total).
    Confirmed against live captures: every observed suffix contains exactly
    one 'X'.  Used by both ``generateLoginCode/v2`` and ``loginByPhoneNumber/v2``.
    """
    return aes_encrypt(f"{phone}-{_app_suffix(7, 'x')}")


def _enc_dec_header(timestamp: int) -> str:
    """Build the AES-encrypted ``x-pm-en-dec`` header value.

    Encrypts ``"{timestamp}-{random}"`` where ``random`` is 7 alphanumeric chars
    with a ``Z`` inserted at a random position.
    """
    # The app nudges the timestamp so that (timestamp // 100) is even.
    if (timestamp // 100) % 2 != 0:
        timestamp += 100

    return aes_encrypt(f"{timestamp}-{_app_suffix(7, 'z')}")


def deobfuscate_secret(header: str) -> str:
    """Extract the signing secret from the x-access-control-allow-headers value.

    The server encodes the rotated secret with three sequential transforms
    reverse-engineered from the React Native bundle (f3 → r4 → w):

    f3: A→9, "e,"→r, ","→2, "-"→F
    r4: " A"→dc, " "→5, "en"→w, [aogT]→""
    w:  remove every 3rd character (positions where (n+1) % 3 == 0)
    """
    # f3
    s = header.replace("A", "9").replace("e,", "r").replace(",", "2").replace("-", "F")
    # r4
    s = s.replace(" A", "dc").replace(" ", "5").replace("en", "w")
    s = re.sub(r"[aogT]", "", s)
    # w: drop every 3rd character
    return "".join(c for i, c in enumerate(s) if (i + 1) % 3 != 0)


def generate_signature_headers(
    secret: str,
    path: str,
    method: str = "GET",
    body: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    environment: str = "production",
) -> dict[str, str]:
    """Generate all signature headers required for a CatGenie API request."""
    timestamp = int(time.time() * 1000)
    hmac_key = derive_hmac_key(secret, environment)

    render_t = f"{path.lstrip('/')}/{timestamp}"

    body_part = ""
    if method.upper() in ("POST", "PUT", "PATCH"):
        body_part = serialize_data(body)

    params_part = serialize_data(params)

    return {
        "x-pm-en-dec": _enc_dec_header(timestamp),
        "x-pm-en-ver": EN_VER,
        "x-render-t": render_t,
        "y-pm-sg-b": _hmac_sha256(hmac_key, body_part + render_t),
        "y-pm-sg-p": _hmac_sha256(hmac_key, params_part + render_t),
    }
