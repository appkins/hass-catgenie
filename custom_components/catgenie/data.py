"""Custom types for integration_blueprint."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from dataclasses_json import LetterCase, dataclass_json


@dataclass_json(letter_case=LetterCase.CAMEL)  # type: ignore reportUnknownMemberType
@dataclass
class Configuration:
    """Configuration settings for the device."""

    child_lock: int = field(default_factory=int)
    auto_lock: int = field(default_factory=int)
    volume_level: int = field(default_factory=int)
    mode: int = field(default_factory=int)
    manual: int = field(default_factory=int)
    cat_sense: int = field(default_factory=int)
    timezone: str = field(default_factory=str)
    dst_from: str = field(default_factory=str)
    dst_to: str = field(default_factory=str)
    dnd_from: str = field(default_factory=str)
    dnd_to: str = field(default_factory=str)
    schedule: list[Any] = field(default_factory=list)
    cat_delay: int = field(default_factory=int)
    extra_dry: bool = field(default_factory=bool)
    binary_elements: dict[str, bool] = field(default_factory=dict[str, bool])


@dataclass_json(letter_case=LetterCase.CAMEL)  # type: ignore reportUnknownMemberType
@dataclass
class OperationStatus:
    """Operation status of the device."""

    state: int = field(default_factory=int)
    progress: int = field(default_factory=int)
    error: str = field(default_factory=str)
    rtc: str | None = None
    sens: str | None = None
    mode: int = field(default_factory=int)
    manual: int = field(default_factory=int)
    step_num: int = field(default_factory=int)
    relay_mode: int | None = None


@dataclass_json(letter_case=LetterCase.CAMEL)  # type: ignore reportUnknownMemberType
@dataclass
class UpdateGroup:
    """Information about the update group."""

    group_id: str = field(default_factory=str)
    name: str = field(default_factory=str)


@dataclass_json(letter_case=LetterCase.CAMEL)  # type: ignore reportUnknownMemberType
@dataclass
class DeviceData:
    """Comprehensive data representation for the device."""

    manufacturer_id: str = field(default_factory=str)
    name: str | None = None
    parent_id: str | None = None
    hw_revision: str | None = None
    fw_version: str = field(default_factory=str)
    device_type: int = field(default_factory=int)
    status: int = field(default_factory=int)
    reported_status: str = field(default_factory=str)
    creation_time: str = field(default_factory=str)
    last_updated_time: str | None = None
    custom_properties: list[Any] = field(default_factory=list)
    children_ids: list[Any] = field(default_factory=list)
    is_online_timestamp: int = field(default_factory=int)
    mb_last_fw_status: str | None = None
    cp_last_fw_status: str | None = None
    lg_last_fw_status: str | None = None
    pump_type_enum: str = field(default_factory=str)
    configuration: Configuration = field(default_factory=Configuration)
    operation_status: OperationStatus | None = None
    mac_address: str = field(default_factory=str)
    last_clean: str | None = None
    total_sani_solution: int = field(default_factory=int)
    used_sani_solution: int = field(default_factory=int)
    remaining_sani_solution: int = field(default_factory=int)
    tag_type: int = field(default_factory=int)
    connection_mode: str = field(default_factory=str)
    ble_connection_id: str = field(default_factory=str)
    state: int = field(default_factory=int)
    selected_lang: str | None = None
    main_error_type: str | None = None
    active_errors: list[Any] = field(default_factory=list)
    update_group: UpdateGroup = field(default_factory=UpdateGroup)
    service_level: str = field(default_factory=str)
    activation_date_from_desired: str | None = None
    in_blacklist: bool | None = None
    country_code: int = field(default_factory=int)
    scale_id: str | None = None
    low_heater: bool = field(default_factory=bool)
    fan_shutter: bool = field(default_factory=bool)
    dome: str | None = None
    temp_out_ref_from_desired: str | None = None
    online: bool = field(default_factory=bool)


@dataclass_json(letter_case=LetterCase.CAMEL)  # type: ignore reportUnknownMemberType
@dataclass
class DevicesResponse:
    """Response from the devices endpoint."""

    thing_list: list[DeviceData] = field(default_factory=list[DeviceData])
