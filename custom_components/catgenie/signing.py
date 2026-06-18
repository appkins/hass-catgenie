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
import string
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


def _enc_dec_header(timestamp: int) -> str:
    """Build the AES-encrypted ``x-pm-en-dec`` header value."""
    # The app nudges the timestamp so that (timestamp // 100) is even.
    if (timestamp // 100) % 2 != 0:
        timestamp += 100

    alphabet = string.ascii_letters + string.digits
    random_part = "".join(random.choice(alphabet) for _ in range(7))  # noqa: S311
    pos = random.randint(0, len(random_part))  # noqa: S311
    random_part = f"{random_part[:pos]}Z{random_part[pos:]}"

    plaintext = f"{timestamp}-{random_part}".encode()

    padder = padding.PKCS7(128).padder()
    padded = padder.update(plaintext) + padder.finalize()

    cipher = Cipher(algorithms.AES(_AES_KEY_BYTES), modes.CBC(_AES_IV))
    encryptor = cipher.encryptor()
    encrypted = encryptor.update(padded) + encryptor.finalize()

    return base64.b64encode(encrypted).decode("utf-8")


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
