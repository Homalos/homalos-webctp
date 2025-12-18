import sys
import pytest
from unittest.mock import MagicMock
from src.utils.config import GlobalConfig, AlertsConfig

# Mock the CTP C++ extension modules BEFORE they are imported by application code
# This avoids ImportError when the DLLs are missing or incompatible in the test environment
mock_thosttraderapi = MagicMock()
mock_thostmduserapi = MagicMock()
sys.modules["src.ctp._thosttraderapi"] = MagicMock()
sys.modules["src.ctp._thostmduserapi"] = MagicMock()

# Also mock the Python wrappers if they import the underscore modules at top level
sys.modules["src.ctp.thosttraderapi"] = mock_thosttraderapi
sys.modules["src.ctp.thostmduserapi"] = mock_thostmduserapi

# Initialize GlobalConfig with default values for testing
GlobalConfig.HeartbeatInterval = 30.0
GlobalConfig.HeartbeatTimeout = 60.0
GlobalConfig.Alerts = AlertsConfig()

# Test credentials for SyncStrategyApi
TEST_USER_ID = "test_user"
TEST_PASSWORD = "test_pass"

@pytest.fixture
def anyio_backend():
    return 'asyncio'

