"""Custom types for integration_blueprint."""

from __future__ import annotations

from dataclasses import dataclass, field

# from homeassistant.config_entries import ConfigEntry
# from homeassistant.loader import Integration

# from .api import CatGenieApiClient
# from .coordinator import CatGenieUpdateCoordinator

@dataclass
class CatGenieDeviceStatusData:
    """Switchbot device data."""
    state: int = field(default_factory=int)
    progress: int = field(default_factory=int)
    error: str = field(default_factory=str)
    rtc: str | None = None
    sens: str | None = None
    mode: int = field(default_factory=int)
    manual: int = field(default_factory=int)
    stepNum: int = field(default_factory=int)
    relayMode: int | None = None


# @dataclass
# class CatGenieDevice:
#     """Switchbot devices data."""
# 
#     fwVersion: str = field(default_factory=str)
#     mac: str = field(default_factory=str)
#     name: str = field(default_factory=str)
#     serial: str = field(default_factory=str)
#     status: CatGenieDeviceStatus = field(default_factory=CatGenieDeviceStatus)


# @dataclass
# class CatGenieData:
#     """Data for the Cat Genie integration."""
# 
#     client: CatGenieApiClient
#     # coordinator: CatGenieUpdateCoordinator
#     # integration: Integration
#     devices: dict[str, CatGenieDevice] = field(default_factory=dict[str, CatGenieDevice])
