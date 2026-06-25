"""Diagnostics support for CatGenie."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from .coordinator import CatGenieConfigEntry

TO_REDACT = {
    "token",
    "secret",
    "refresh_token",
    "access_token",
    "macAddress",
    "bleConnectionId",
    "mac_address",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: CatGenieConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    return {
        "entry": async_redact_data(dict(entry.data), TO_REDACT),
        "device": async_redact_data(
            {k: v for k, v in vars(coordinator.data).items() if not k.startswith("_")},
            TO_REDACT,
        ),
        "pending_firmware_update": (
            vars(coordinator.pending_firmware_update)
            if coordinator.pending_firmware_update
            else None
        ),
    }
