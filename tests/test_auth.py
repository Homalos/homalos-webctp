
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.apps.td_app import td_websocket
from src.apps.md_app import md_websocket
from src.utils.config import GlobalConfig
from fastapi import WebSocket

# Helper to create a mock WebSocket
def create_mock_websocket():
    ws = AsyncMock(spec=WebSocket)
    return ws

@pytest.fixture
def mock_td_connection():
    with patch("src.apps.td_app.TdConnection") as MockConn:
        instance = MockConn.return_value
        instance.run = AsyncMock(return_value=None)
        yield MockConn

@pytest.fixture
def mock_md_connection():
    with patch("src.apps.md_app.MdConnection") as MockConn:
        instance = MockConn.return_value
        instance.run = AsyncMock(return_value=None)
        yield MockConn

@pytest.mark.asyncio
async def test_td_auth_success(mock_td_connection):
    GlobalConfig.Token = "secret"
    ws = create_mock_websocket()
    
    await td_websocket(ws, token="secret")
    
    # Should run connection
    mock_td_connection.return_value.run.assert_awaited()
    # Should NOT close with 1008
    # It might close implicitly when function ends, but we check verification passed
    # If 1008 was called, it would return before run()
    
    # Check if close(code=1008) was NOT called
    for call in ws.close.call_args_list:
        assert call.kwargs.get('code') != 1008

@pytest.mark.asyncio
async def test_td_auth_failure(mock_td_connection):
    GlobalConfig.Token = "secret"
    ws = create_mock_websocket()
    
    await td_websocket(ws, token="wrong")
    
    # Should close with 1008
    ws.close.assert_awaited_with(code=1008)
    # Should NOT run connection
    mock_td_connection.return_value.run.assert_not_awaited()

@pytest.mark.asyncio
async def test_td_no_auth_needed(mock_td_connection):
    GlobalConfig.Token = ""
    ws = create_mock_websocket()
    
    await td_websocket(ws, token=None)
    
    # Should run connection
    mock_td_connection.return_value.run.assert_awaited()

@pytest.mark.asyncio
async def test_md_auth_failure(mock_md_connection):
    GlobalConfig.Token = "secret"
    ws = create_mock_websocket()
    
    await md_websocket(ws, token="wrong")
    
    ws.close.assert_awaited_with(code=1008)
    mock_md_connection.return_value.run.assert_not_awaited()

