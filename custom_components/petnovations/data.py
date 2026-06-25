"""Custom types for integration_blueprint."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Activation:
    """Sani-solution / cartridge activation state."""

    date: str | None = None
    state: int = field(default_factory=int)
    count: int = field(default_factory=int)

    @staticmethod
    def from_dict(obj: Any) -> Activation:
        """Parse data from API."""
        return Activation(
            date=obj.get("date"),
            state=obj.get("state", 0),
            count=obj.get("count", 0),
        )


@dataclass
class Language:
    """Device language settings (desired/actual)."""

    desired: str = field(default_factory=str)
    actual: str = field(default_factory=str)

    @staticmethod
    def from_dict(obj: Any) -> Language:
        """Parse data from API."""
        return Language(
            desired=obj.get("des", ""),
            actual=obj.get("act", ""),
        )


@dataclass
class Heater:
    """Heater configuration."""

    model: int | None = None
    temp_out_ref: int = field(default_factory=int)

    @staticmethod
    def from_dict(obj: Any) -> Heater:
        """Parse data from API."""
        return Heater(
            model=obj.get("model"),
            temp_out_ref=obj.get("tempOutRef", 0),
        )


@dataclass
class BinaryElements:
    """Optional binary wash/shake toggles."""

    extra_wash: bool = field(default_factory=bool)
    extra_shake: bool = field(default_factory=bool)

    @staticmethod
    def from_dict(obj: Any) -> BinaryElements:
        """Parse data from API."""
        return BinaryElements(
            extra_wash=obj.get("EXTRA_WASH", False),
            extra_shake=obj.get("EXTRA_SHAKE", False),
        )


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
    pump_pct_t: int = field(default_factory=int)
    extra_dry: bool = field(default_factory=bool)
    activation: Activation = field(default_factory=Activation)
    language: Language = field(default_factory=Language)
    heater: Heater = field(default_factory=Heater)
    binary_elements: BinaryElements = field(default_factory=BinaryElements)

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
            pump_pct_t=obj.get("pumpPctT", 0),
            extra_dry=obj.get("extraDry", False),
            activation=Activation.from_dict(obj.get("activation", {})),
            language=Language.from_dict(obj.get("lng", {})),
            heater=Heater.from_dict(obj.get("heater", {})),
            binary_elements=BinaryElements.from_dict(obj.get("binaryElements", {})),
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

    group_id: str = field(default_factory=str)
    name: str = field(default_factory=str)

    @staticmethod
    def from_dict(obj: Any) -> UpdateGroup:
        """Parse data from API."""
        return UpdateGroup(
            group_id=obj.get("id", ""),
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
    connection_modified_time: str | None = None
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
            device_type=obj.get("type", 0),
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
            connection_modified_time=obj.get("connectionModifiedTime"),
            online=obj.get("online", False),
        )


@dataclass
class VisitFields:
    """Per-visit detail fields."""

    rtc_start: str = field(default_factory=str)
    serial_number: str = field(default_factory=str)
    duration_seconds: int = field(default_factory=int)
    device_id: str = field(default_factory=str)

    @staticmethod
    def from_dict(obj: Any) -> VisitFields:
        """Parse data from API."""
        return VisitFields(
            rtc_start=obj.get("rtcStart", ""),
            serial_number=obj.get("serialNumber", ""),
            duration_seconds=obj.get("durationSeconds", 0),
            device_id=obj.get("deviceId", ""),
        )


@dataclass
class VisitResponse:
    """A single cat-visit history record."""

    timestamp: int = field(default_factory=int)
    event_type: str = field(default_factory=str)
    machine_ts: str = field(default_factory=str)
    fields: VisitFields = field(default_factory=VisitFields)

    @staticmethod
    def from_dict(obj: Any) -> VisitResponse:
        """Parse data from API."""
        return VisitResponse(
            timestamp=obj.get("timestamp", 0),
            event_type=obj.get("type", ""),
            machine_ts=obj.get("machineTS", ""),
            fields=VisitFields.from_dict(obj.get("fields", {})),
        )


@dataclass
class FlushFields:
    """Per-cycle (flush/end-of-cycle) detail fields."""

    rtc_end: str = field(default_factory=str)
    serial_number: str = field(default_factory=str)
    aborted: int = field(default_factory=int)

    @staticmethod
    def from_dict(obj: Any) -> FlushFields:
        """Parse data from API."""
        return FlushFields(
            rtc_end=obj.get("rtcEnd", ""),
            serial_number=obj.get("serialNumber", ""),
            aborted=obj.get("aborted", 0),
        )


@dataclass
class FlushResponse:
    """A single cleaning-cycle history record."""

    timestamp: int = field(default_factory=int)
    event_type: str = field(default_factory=str)
    machine_ts: str = field(default_factory=str)
    fields: FlushFields = field(default_factory=FlushFields)

    @staticmethod
    def from_dict(obj: Any) -> FlushResponse:
        """Parse data from API."""
        return FlushResponse(
            timestamp=obj.get("timestamp", 0),
            event_type=obj.get("type", ""),
            machine_ts=obj.get("machineTS", ""),
            fields=FlushFields.from_dict(obj.get("fields", {})),
        )


@dataclass
class PetResponse:
    """A pet registered on the account."""

    id: str = field(default_factory=str)
    user_id: str = field(default_factory=str)
    name: str = field(default_factory=str)
    device_id: str | None = None
    pet_type: str | None = None
    hair_type: str | None = None
    birthday: str | None = None
    gender: str | None = None
    weight: float | None = None
    image_url: str | None = None
    last_visit_time: str | None = None

    @staticmethod
    def from_dict(obj: Any) -> PetResponse:
        """Parse data from API."""
        return PetResponse(
            id=obj.get("id", ""),
            user_id=obj.get("userId", ""),
            name=obj.get("name", ""),
            device_id=obj.get("deviceId"),
            pet_type=obj.get("petType"),
            hair_type=obj.get("hairType"),
            birthday=obj.get("birthday"),
            gender=obj.get("gender"),
            weight=obj.get("weight"),
            image_url=obj.get("imageUrl"),
            last_visit_time=obj.get("lastVisitTime"),
        )


@dataclass
class PetStatistics:
    """Response for ``device/history/account/pet/statistics``."""

    visit_responses: list[VisitResponse] = field(default_factory=list[VisitResponse])
    flush_responses: list[FlushResponse] = field(default_factory=list[FlushResponse])
    pet_responses: list[PetResponse] = field(default_factory=list[PetResponse])

    @staticmethod
    def from_dict(obj: Any) -> PetStatistics:
        """Parse data from API."""
        return PetStatistics(
            visit_responses=[
                VisitResponse.from_dict(item)
                for item in obj.get("visitResponses", [])
            ],
            flush_responses=[
                FlushResponse.from_dict(item)
                for item in obj.get("flushResponses", [])
            ],
            pet_responses=[
                PetResponse.from_dict(item)
                for item in obj.get("petResponses", [])
            ],
        )


NOTIFICATION_TYPE_FW_UPDATE = 24


@dataclass
class FirmwareUpdate:
    """Pending firmware update sourced from a type-24 push notification."""

    device_id: str = field(default_factory=str)
    parent_device_id: str = field(default_factory=str)
    version: str = field(default_factory=str)
    configuration_id: str | None = None

    @staticmethod
    def from_notification_data(data: dict[str, Any]) -> FirmwareUpdate:
        """Parse the inner ``data`` JSON of a FW_UPDATE (type 24) notification."""
        return FirmwareUpdate(
            device_id=data.get("deviceId", ""),
            parent_device_id=data.get("parentDeviceId", ""),
            version=data.get("version", ""),
            configuration_id=data.get("configurationId"),
        )


@dataclass
class Notification:
    """A single push-notification feed item.

    The cloud feed isn't strongly typed across firmware versions, so parsing is
    deliberately tolerant: the id/type/message are pulled from whichever of the
    known aliases is present, and the untouched payload is kept in ``raw``.
    """

    id: str = field(default_factory=str)
    type: str = field(default_factory=str)
    message: str = field(default_factory=str)
    timestamp: int = field(default_factory=int)
    device_id: str | None = None
    firmware_update: FirmwareUpdate | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def from_dict(obj: dict[str, Any]) -> Notification:
        """Parse data from API."""

        def first(*keys: str) -> Any:
            for key in keys:
                value = obj.get(key)
                if value not in (None, ""):
                    return value
            return None

        timestamp = first("timestamp", "createdAt", "creationTime", "time") or 0

        # The server embeds the notification type inside a JSON-encoded "data"
        # string rather than at the top level (e.g. FW_UPDATE notifications have
        # no top-level "type" key).  Parse it first so the type is available.
        embedded: dict[str, Any] = {}
        raw_data_field = obj.get("data")
        if isinstance(raw_data_field, str):
            try:
                parsed = json.loads(raw_data_field)
                if isinstance(parsed, dict):
                    embedded = parsed
            except (json.JSONDecodeError, ValueError):
                pass
        elif isinstance(raw_data_field, dict):
            embedded = raw_data_field

        def first_also_embedded(*keys: str) -> Any:
            for key in keys:
                for src in (obj, embedded):
                    value = src.get(key)
                    if value not in (None, ""):
                        return value
            return None

        raw_type = first_also_embedded("type", "notificationType", "category", "event") or ""

        firmware_update: FirmwareUpdate | None = None
        if str(raw_type) == str(NOTIFICATION_TYPE_FW_UPDATE):
            firmware_update = FirmwareUpdate.from_notification_data(embedded)

        return Notification(
            id=str(
                first("id", "notificationId", "pushId", "_id", "uuid") or timestamp
            ),
            type=str(raw_type),
            message=str(first_also_embedded("message", "body", "text", "description", "title") or ""),
            timestamp=int(timestamp) if str(timestamp).isdigit() else 0,
            device_id=first_also_embedded("deviceId", "manufacturerId", "thingId"),
            firmware_update=firmware_update,
            raw=obj,
        )


@dataclass
class ConfigUrlResponse:
    """Response for ``config/v1/url`` (unauthenticated base-URL probe)."""

    url: str = field(default_factory=str)
    env: str = field(default_factory=str)

    @staticmethod
    def from_dict(obj: Any) -> ConfigUrlResponse:
        """Parse data from API."""
        return ConfigUrlResponse(
            url=obj.get("url", ""),
            env=obj.get("env", ""),
        )


@dataclass
class GenerateLoginCodeRequest:
    """Body for ``ums/v1/users/generateLoginCode/v2`` (triggers the SMS code).

    ``str1`` is the AES-encrypted ``"{E.164 phone}-{random}"`` token; build it
    with ``signing.build_phone_token(phone)``.
    """

    str1: str

    def to_body(self) -> dict[str, str]:
        """Serialize to the request body."""
        return {"str1": self.str1}


@dataclass
class LoginRequest:
    """Body for ``ums/v1/users/loginByPhoneNumber/v2``.

    ``str1`` is the AES-encrypted phone token (see ``signing.build_phone_token``)
    and ``code`` is the SMS one-time code the user received.
    """

    str1: str
    code: str

    def to_body(self) -> dict[str, str]:
        """Serialize to the request body."""
        return {"str1": self.str1, "code": self.code}


@dataclass
class LoginResponse:
    """Response for ``ums/v1/users/loginByPhoneNumber/v2``."""

    user_id: str = field(default_factory=str)
    tenant_id: str = field(default_factory=str)
    account_id: str = field(default_factory=str)
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    access_token: str = field(default_factory=str)
    refresh_token: str = field(default_factory=str)
    phone: str | None = None
    email_verified: bool = field(default_factory=bool)
    phone_verified: bool = field(default_factory=bool)
    password_reset_required: bool = field(default_factory=bool)
    mfa_request_token: str | None = None
    group_names: list[str] = field(default_factory=list[str])
    country_codes: list[Any] | None = None
    mfa_required: bool = field(default_factory=bool)

    @staticmethod
    def from_dict(obj: Any) -> LoginResponse:
        """Parse data from API."""
        return LoginResponse(
            user_id=obj.get("userId", ""),
            tenant_id=obj.get("tenantId", ""),
            account_id=obj.get("accountId", ""),
            email=obj.get("email"),
            first_name=obj.get("firstName"),
            last_name=obj.get("lastName"),
            access_token=obj.get("accessToken", ""),
            refresh_token=obj.get("refreshToken", ""),
            phone=obj.get("phone"),
            email_verified=obj.get("emailVerified", False),
            phone_verified=obj.get("phoneVerified", False),
            password_reset_required=obj.get("passwordResetRequired", False),
            mfa_request_token=obj.get("mfaRequestToken"),
            group_names=obj.get("groupNames", []),
            country_codes=obj.get("countryCodes"),
            mfa_required=obj.get("mfaRequired", False),
        )
