"""Simple test runner for CatGenie component without Home Assistant pytest plugin."""

import sys
import asyncio
from pathlib import Path

# Add the custom_components directory to the path
sys.path.insert(0, str(Path(__file__).parent / "custom_components"))

async def test_imports():
    """Test that all modules can be imported without errors."""
    print("Testing imports...")

    try:
        # Test basic imports
        from catgenie import const
        print("✅ const.py imported successfully")

        from catgenie import data
        print("✅ data.py imported successfully")

        # Test config flow import (this should work without HA)
        from catgenie import config_flow
        print("✅ config_flow.py imported successfully")

        print("\n✅ All basic imports successful!")
        return True

    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

async def test_data_classes():
    """Test that data classes work correctly."""
    print("\nTesting data classes...")

    try:
        from catgenie.data import DeviceData, OperationStatus, Configuration

        # Test creating instances
        config = Configuration()
        operation_status = OperationStatus()
        device = DeviceData()

        print("✅ Data classes instantiated successfully")

        # Test with some data
        operation_status.state = 1
        operation_status.error = "test error"
        device.operation_status = operation_status

        print("✅ Data classes work with test data")
        return True

    except Exception as e:
        print(f"❌ Data class error: {e}")
        return False

def test_config_flow_class():
    """Test config flow class structure."""
    print("\nTesting config flow structure...")

    try:
        from catgenie.config_flow import CatGenieHandler

        # Check if the class has the required methods
        required_methods = ['async_step_user', '_test_credentials']
        for method in required_methods:
            if hasattr(CatGenieHandler, method):
                print(f"✅ {method} method exists")
            else:
                print(f"❌ {method} method missing")
                return False

        print("✅ Config flow structure is correct")
        return True

    except Exception as e:
        print(f"❌ Config flow error: {e}")
        return False

async def main():
    """Run all tests."""
    print("🧪 Running CatGenie Component Tests\n")

    tests = [
        test_imports(),
        test_data_classes(),
    ]

    results = await asyncio.gather(*tests, return_exceptions=True)

    # Run sync test
    sync_result = test_config_flow_class()

    # Count successes
    successes = sum(1 for result in results if result is True) + (1 if sync_result else 0)
    total = len(results) + 1

    print(f"\n📊 Test Results: {successes}/{total} tests passed")

    if successes == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
