"""Test CatGenie entities."""
from unittest.mock import Mock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.catgenie.entity import CatGenieEntity, DeviceOperation
from custom_components.catgenie.data import DeviceData


@pytest.fixture
def mock_device_data():
    """Return mock device data."""
    return DeviceData(
        manufacturer_id="test_device_id",
        name="Test CatGenie",
        fw_version="1.0.0",
        reported_status="connected",
    )


@pytest.fixture
def mock_coordinator(mock_device_data):
    """Return mock coordinator."""
    coordinator = Mock()
    coordinator.data = mock_device_data
    return coordinator


async def test_catgenie_entity_initialization(hass: HomeAssistant, mock_coordinator):
    """Test CatGenie entity initialization."""
    entity = CatGenieEntity(mock_coordinator)

    assert entity.coordinator == mock_coordinator
    assert entity.device_name == "Test CatGenie"
    assert entity.device_id == "test_device_id"


async def test_catgenie_entity_device_info(hass: HomeAssistant, mock_coordinator):
    """Test CatGenie entity device info."""
    entity = CatGenieEntity(mock_coordinator)

    device_info = entity.device_info

    assert device_info["identifiers"] == {("catgenie", "test_device_id")}
    assert device_info["manufacturer"] == "PetNovations Ltd."
    assert device_info["model"] == "VXHCATGENIE"
    assert device_info["model_id"] == "test_device_id"
    assert device_info["sw_version"] == "1.0.0"


async def test_catgenie_entity_no_name_fallback(hass: HomeAssistant, mock_coordinator):
    """Test CatGenie entity fallback when no name provided."""
    mock_coordinator.data.name = None
    entity = CatGenieEntity(mock_coordinator)

    assert entity.device_name == "Litter Box test_device_id"


async def test_device_operation_enum():
    """Test DeviceOperation enum values."""
    assert DeviceOperation.ON.value == 1
    assert DeviceOperation.OFF.value == 2
    assert DeviceOperation.RESUME.value == 3
    assert DeviceOperation.FULL_CLEAN.value == 4


async def test_catgenie_entity_device_operation(hass: HomeAssistant, mock_coordinator):
    """Test device operation method."""
    entity = CatGenieEntity(mock_coordinator)

    # Mock the client's device operation method
    mock_coordinator.client.async_device_operation = Mock(return_value="success")

    result = await entity.device_operation("test_device_id", DeviceOperation.ON)

    mock_coordinator.client.async_device_operation.assert_called_once_with(
        "test_device_id", 1
    )
    assert result == "success"
