import sys
import pytest
from unittest.mock import MagicMock

# Mock the CTP C++ extension modules BEFORE they are imported by application code
# This avoids ImportError when the DLLs are missing or incompatible in the test environment
mock_thosttraderapi = MagicMock()
mock_thostmduserapi = MagicMock()
sys.modules["src.ctp._thosttraderapi"] = MagicMock()
sys.modules["src.ctp._thostmduserapi"] = MagicMock()

# Also mock the Python wrappers if they import the underscore modules at top level
sys.modules["src.ctp.thosttraderapi"] = mock_thosttraderapi
sys.modules["src.ctp.thostmduserapi"] = mock_thostmduserapi

@pytest.fixture
def anyio_backend():
    return 'asyncio'

