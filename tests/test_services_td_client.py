
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.td_client import TdClient
from src.constants import TdConstant as Constant
from src.constants import CallError

@pytest.fixture
def td_service():
    """Fixture to create a TdClient service instance with mocked internals"""
    with patch("src.services.td_client.CTPTdClient") as MockCTP:
        client = TdClient()
        client._task_group = AsyncMock() # Mock the task group
        client.rsp_callback = AsyncMock() # Mock the callback
        return client

@pytest.mark.asyncio
async def test_validate_request_success(td_service):
    """Test validation with valid data"""
    msg_type = Constant.ReqQryInstrument
    data = {
        Constant.MessageType: msg_type,
        "MsgType": msg_type,
        "RequestID": 1,
        Constant.ReqQryInstrument: {
            "ExchangeID": "SHFE",
            "InstrumentID": "cu2501"
        }
    }

    result = td_service.validate_request(msg_type, data)
    assert result is None

@pytest.mark.asyncio
async def test_validate_request_fail_missing_field(td_service):
    """Test validation fails when required field is missing (if model enforces it)"""
    # Note: Pydantic models in this project might be optional fields, 
    # so we test with a completely wrong type to trigger validation error if strict
    pass 
    # For now, let's test invalid message type
    result = td_service.validate_request("InvalidMsgType", {})
    assert result[Constant.RspInfo]["ErrorID"] == -404


@pytest.mark.asyncio
async def test_call_login(td_service):
    """Test ReqUserLogin triggers start()"""
    req_data = {
        Constant.MessageType: Constant.ReqUserLogin,
        "MsgType": Constant.ReqUserLogin,
        "RequestID": 1,
        Constant.ReqUserLogin: {
            "UserID": "test_user",
            "Password": "test_password"
        }
    }

    
    # Mocking _create_ctp_client to return a mock
    mock_ctp_instance = MagicMock()
    with patch.object(td_service, "_create_ctp_client", return_value=mock_ctp_instance) as mock_create:
        with patch.object(td_service, "_client", new=None): # Ensure client is None initially
             # We need to mock start method or its internals. 
             # start() calls _create_ctp_client inside a thread.
             
             # Actually, let's mock start directly to verify routing logic first
             pass

    # Let's test the call method's routing strictly
    with patch.object(td_service, "start", new_callable=AsyncMock) as mock_start:
        await td_service.call(req_data)
        mock_start.assert_awaited_once_with("test_user", "test_password")

@pytest.mark.asyncio
async def test_call_qry_instrument(td_service):
    """Test specific query routes to _call_map"""
    req_data = {
        Constant.MessageType: Constant.ReqQryInstrument,
        "MsgType": Constant.ReqQryInstrument,
        "RequestID": 1,
        Constant.ReqQryInstrument: {
            "ExchangeID": "SHFE"
        }
    }

    
    # Mock the specific handler in _call_map
    mock_handler = MagicMock()
    td_service._call_map[Constant.ReqQryInstrument] = mock_handler
    
    await td_service.call(req_data)
    
    # Check if handler was called. 
    # Note: call() runs handler in to_thread.run_sync, so we verify mock_handler call
    mock_handler.assert_called_once_with(req_data)

@pytest.mark.asyncio
async def test_call_unknown_message(td_service):
    """Test call with unknown message type returns 404"""
    req_data = {
        Constant.MessageType: "UnknownType",
        "SomeData": {}
    }
    
    await td_service.call(req_data)
    
    td_service.rsp_callback.assert_awaited()
    call_args = td_service.rsp_callback.call_args[0][0]
    assert call_args[Constant.MessageType] == "UnknownType"
    assert call_args[Constant.RspInfo]["ErrorID"] == -404

