"""Custom types for integration_blueprint."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


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
    binary_elements: dict = field(default_factory=dict)

    @staticmethod
    def from_dict(obj: Any) -> Configuration:
        """Parse data from API."""
        return Configuration(
            child_lock=obj.get("childLock", 0),
            auto_lock=obj.get("autoLock", 0),
            volume_level=obj.get("volumeLevel", 0),
            mode=obj.get("mode", 0),
            manual=obj.get("manual", 0),
            cat_sense=obj.get("catSense", 0),
            timezone=obj.get("timezone", ""),
            dst_from=obj.get("dstFrom", ""),
            dst_to=obj.get("dstTo", ""),
            dnd_from=obj.get("dndFrom", ""),
            dnd_to=obj.get("dndTo", ""),
            schedule=obj.get("schedule", []),
            cat_delay=obj.get("catDelay", 0),
            extra_dry=obj.get("extraDry", False),
            binary_elements=obj.get("binaryElements", {}),
        )


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

    @staticmethod
    def from_dict(obj: Any) -> OperationStatus:
        """Parse data from API."""
        return OperationStatus(
            state=obj.get("state", 0),
            progress=obj.get("progress", 0),
            error=obj.get("error", ""),
            rtc=obj.get("rtc"),
            sens=obj.get("sens"),
            mode=obj.get("mode", 0),
            manual=obj.get("manual", 0),
            step_num=obj.get("stepNum", 0),
            relay_mode=obj.get("relayMode"),
        )


@dataclass
class UpdateGroup:
    """Information about the update group."""

    id: str = field(default_factory=str)
    name: str = field(default_factory=str)

    @staticmethod
    def from_dict(obj: Any) -> UpdateGroup:
        """Parse data from API."""
        return UpdateGroup(
            id=obj.get("id", ""),
            name=obj.get("name", ""),
        )


@dataclass
class DeviceData:
    """Comprehensive data representation for the device."""

    manufacturer_id: str = field(default_factory=str)
    name: str | None = None
    parent_id: str | None = None
    hw_revision: str | None = None
    fw_version: str = field(default_factory=str)
    type: int = field(default_factory=int)
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
    operation_status: OperationStatus = field(default_factory=OperationStatus)
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

    @staticmethod
    def from_dict(obj: Any) -> DeviceData:
        """Parse data from API."""
        return DeviceData(
            manufacturer_id=obj.get("manufacturerId", ""),
            name=obj.get("name"),
            parent_id=obj.get("parentId"),
            hw_revision=obj.get("hwRevision"),
            fw_version=obj.get("fwVersion", ""),
            type=obj.get("type", 0),
            status=obj.get("status", 0),
            reported_status=obj.get("reportedStatus", ""),
            creation_time=obj.get("creationTime", ""),
            last_updated_time=obj.get("lastUpdatedTime"),
            custom_properties=obj.get("customProperties", []),
            children_ids=obj.get("childrenIds", []),
            is_online_timestamp=obj.get("isOnlineTimestamp", 0),
            mb_last_fw_status=obj.get("mbLastFwStatus"),
            cp_last_fw_status=obj.get("cpLastFwStatus"),
            lg_last_fw_status=obj.get("lgLastFwStatus"),
            pump_type_enum=obj.get("pumpTypeEnum", ""),
            configuration=Configuration.from_dict(obj.get("configuration", {})),
            operation_status=OperationStatus.from_dict(obj.get("operationStatus", {})),
            mac_address=obj.get("macAddress", ""),
            last_clean=obj.get("lastClean"),
            total_sani_solution=obj.get("totalSaniSolution", 0),
            used_sani_solution=obj.get("usedSaniSolution", 0),
            remaining_sani_solution=obj.get("remainingSaniSolution", 0),
            tag_type=obj.get("tagType", 0),
            connection_mode=obj.get("connectionMode", ""),
            ble_connection_id=obj.get("bleConnectionId", ""),
            state=obj.get("state", 0),
            selected_lang=obj.get("selectedLang"),
            main_error_type=obj.get("mainErrorType"),
            active_errors=obj.get("activeErrors", []),
            update_group=UpdateGroup.from_dict(obj.get("updateGroup", {})),
            service_level=obj.get("serviceLevel", ""),
            activation_date_from_desired=obj.get("activationDateFromDesired"),
            in_blacklist=obj.get("inBlacklist"),
            country_code=obj.get("countryCode", 0),
            scale_id=obj.get("scaleId"),
            low_heater=obj.get("lowHeater", False),
            fan_shutter=obj.get("fanShutter", False),
            dome=obj.get("dome"),
            temp_out_ref_from_desired=obj.get("tempOutRefFromDesired"),
            online=obj.get("online", False),
        )
