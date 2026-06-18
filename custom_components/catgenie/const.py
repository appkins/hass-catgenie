"""Constants for integration_blueprint."""

from logging import Logger, getLogger
from typing import Final

LOGGER: Logger = getLogger(__package__)

DOMAIN: Final[str] = "catgenie"
ATTRIBUTION: Final[str] = "Data provided by PetNovations Ltd."

HOST: Final[str] = "iot.petnovations.com"
ENDPOINT_REFRESH: Final[str] = "/facade/v1/mobile-user/refreshToken"

# Config entry keys
CONF_SECRET: Final[str] = "secret"

# Request signing (see signing.py and docs/SIGNATURE_ALGORITHM.md).
# Derivation parameters by environment: "index-prefix-suffix".
DERIVATION_PARAMS: Final[dict[str, str]] = {
    "dev": "0-1b-Mg",
    "staging": "28-wq-0C",
    "production": "56-Yt-x3",
}
# Static AES-CBC key used to encrypt the x-pm-en-dec timestamp header.
AES_KEY: Final[str] = "P-3Rp6d81Kw9a3Z-CyvWH0WXRieyITk6"
# Value sent in the x-pm-en-ver header.
EN_VER: Final[str] = "1.0.0"
