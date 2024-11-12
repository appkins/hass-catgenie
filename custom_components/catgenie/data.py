"""Custom types for integration_blueprint."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import CatGenieApiClient
    from .coordinator import CatGenieUpdateCoordinator


type CatGenieConfigEntry = ConfigEntry[CatGenieData]

@dataclass
class CatGenieDeviceStatus:
    """Switchbot device data."""

    state: int = field(default_factory=int)
    

@dataclass
class CatGenieDevice:
    """Switchbot devices data."""

    fwVersion: str = field(default_factory=str)
    mac: str = field(default_factory=str)
    name: str = field(default_factory=str)
    serial: str = field(default_factory=str)
    status: CatGenieDeviceStatus = field(default_factory=CatGenieDeviceStatus)


@dataclass
class CatGenieData:
    """Data for the Cat Genie integration."""

    client: CatGenieApiClient
    coordinator: CatGenieUpdateCoordinator
    integration: Integration
    devices: dict[str, CatGenieDevice] = field(default_factory=dict[str, CatGenieDevice])
