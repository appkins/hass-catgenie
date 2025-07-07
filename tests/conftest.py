"""Fixtures for CatGenie tests."""
import pytest

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.catgenie.const import DOMAIN


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations defined in the test dir."""
    yield


@pytest.fixture
def mock_config_entry():
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Test CatGenie",
        data={
            "name": "Test CatGenie",
            "token": "test_refresh_token",
        },
        unique_id="test_catgenie_unique_id",
    )
