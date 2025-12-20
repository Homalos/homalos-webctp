#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : conftest.py
@Date       : 2025/12/20
@Author     : Kiro AI Assistant
@Email      : -
@Software   : PyCharm
@Description: tests/strategy 包的共享 fixtures
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch


# ============================================================================
# 测试凭证
# ============================================================================

TEST_USER_ID = "test_user"
TEST_PASSWORD = "test_pass"


# ============================================================================
# Mock 客户端 Fixtures
# ============================================================================

@pytest.fixture
def mock_md_client():
    """创建 mock MdClient 实例"""
    mock_client = Mock()
    mock_client.start = AsyncMock()
    mock_client.stop = AsyncMock()
    mock_client.rsp_callback = None
    return mock_client


@pytest.fixture
def mock_td_client():
    """创建 mock TdClient 实例"""
    mock_client = Mock()
    mock_client.start = AsyncMock()
    mock_client.stop = AsyncMock()
    mock_client.rsp_callback = None
    return mock_client


@pytest.fixture
def mock_md_client_class(mock_md_client):
    """创建 mock MdClient 类"""
    with patch('src.services.md_client.MdClient') as mock_class:
        mock_class.return_value = mock_md_client
        yield mock_class


@pytest.fixture
def mock_td_client_class(mock_td_client):
    """创建 mock TdClient 类"""
    with patch('src.services.td_client.TdClient') as mock_class:
        mock_class.return_value = mock_td_client
        yield mock_class


# ============================================================================
# 测试数据 Fixtures
# ============================================================================

@pytest.fixture
def sample_quote_data():
    """创建示例行情数据"""
    return {
        'InstrumentID': 'rb2505',
        'LastPrice': 3500.0,
        'BidPrice1': 3499.0,
        'BidVolume1': 10,
        'AskPrice1': 3501.0,
        'AskVolume1': 5,
        'Volume': 1000,
        'OpenInterest': 5000.0,
        'UpdateTime': '09:30:00',
        'UpdateMillisec': 500
    }


@pytest.fixture
def sample_position_data():
    """创建示例持仓数据"""
    return {
        'pos_long': 10,
        'pos_long_today': 5,
        'pos_long_his': 5,
        'open_price_long': 3500.0,
        'pos_short': 8,
        'pos_short_today': 3,
        'pos_short_his': 5,
        'open_price_short': 3520.0
    }


@pytest.fixture
def sample_market_data():
    """创建示例市场数据字典（用于缓存更新）"""
    return {
        'LastPrice': 3500.0,
        'BidPrice1': 3499.0,
        'BidVolume1': 10,
        'AskPrice1': 3501.0,
        'AskVolume1': 5,
        'Volume': 1000,
        'OpenInterest': 5000.0,
        'UpdateTime': '09:30:00',
        'UpdateMillisec': 500
    }
