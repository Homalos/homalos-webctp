#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : test_backward_compatibility.py
@Date       : 2025/12/20
@Author     : Kiro AI Assistant
@Email      : -
@Software   : PyCharm
@Description: SyncStrategyApi 向后兼容性测试
"""

import inspect
import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.strategy.sync_api import SyncStrategyApi, Quote, Position

# 测试凭证
TEST_USER_ID = "test_user"
TEST_PASSWORD = "test_pass"


class TestAPISignatures:
    """测试 API 方法签名未变化"""

    def test_sync_strategy_api_init_signature(self):
        """测试 SyncStrategyApi.__init__ 方法签名"""
        sig = inspect.signature(SyncStrategyApi.__init__)
        params = list(sig.parameters.keys())
        
        # 验证参数列表
        assert 'self' in params
        assert 'user_id' in params
        assert 'password' in params
        
        # 验证参数顺序
        assert params.index('user_id') < params.index('password')

    def test_get_quote_signature(self):
        """测试 get_quote 方法签名"""
        sig = inspect.signature(SyncStrategyApi.get_quote)
        params = list(sig.parameters.keys())
        
        assert 'self' in params
        assert 'instrument_id' in params

    def test_wait_quote_update_signature(self):
        """测试 wait_quote_update 方法签名"""
        sig = inspect.signature(SyncStrategyApi.wait_quote_update)
        params = list(sig.parameters.keys())
        
        assert 'self' in params
        assert 'instrument_id' in params
        assert 'timeout' in params

    def test_get_position_signature(self):
        """测试 get_position 方法签名"""
        sig = inspect.signature(SyncStrategyApi.get_position)
        params = list(sig.parameters.keys())
        
        assert 'self' in params
        assert 'instrument_id' in params

    def test_open_close_signature(self):
        """测试 open_close 方法签名"""
        sig = inspect.signature(SyncStrategyApi.open_close)
        params = list(sig.parameters.keys())
        
        assert 'self' in params
        assert 'instrument_id' in params
        assert 'action' in params
        assert 'volume' in params
        assert 'price' in params

    def test_run_strategy_signature(self):
        """测试 run_strategy 方法签名"""
        sig = inspect.signature(SyncStrategyApi.run_strategy)
        params = list(sig.parameters.keys())
        
        assert 'self' in params
        assert 'strategy_func' in params

    def test_stop_signature(self):
        """测试 stop 方法签名"""
        sig = inspect.signature(SyncStrategyApi.stop)
        params = list(sig.parameters.keys())
        
        assert 'self' in params


class TestDataClassesCompatibility:
    """测试数据类的向后兼容性"""

    def test_quote_fields(self):
        """测试 Quote 数据类的字段"""
        quote = Quote()
        
        # 验证所有必需字段存在
        assert hasattr(quote, 'InstrumentID')
        assert hasattr(quote, 'LastPrice')
        assert hasattr(quote, 'BidPrice1')
        assert hasattr(quote, 'BidVolume1')
        assert hasattr(quote, 'AskPrice1')
        assert hasattr(quote, 'AskVolume1')
        assert hasattr(quote, 'Volume')
        assert hasattr(quote, 'OpenInterest')
        assert hasattr(quote, 'UpdateTime')
        assert hasattr(quote, 'UpdateMillisec')
        assert hasattr(quote, 'ctp_datetime')

    def test_quote_dict_access(self):
        """测试 Quote 的字典访问方式"""
        quote = Quote(InstrumentID="rb2505", LastPrice=3500.0)
        
        # 验证字典访问方式仍然有效
        assert quote["InstrumentID"] == "rb2505"
        assert quote["LastPrice"] == 3500.0

    def test_position_fields(self):
        """测试 Position 数据类的字段"""
        position = Position()
        
        # 验证所有必需字段存在
        assert hasattr(position, 'pos_long')
        assert hasattr(position, 'pos_long_today')
        assert hasattr(position, 'pos_long_his')
        assert hasattr(position, 'open_price_long')
        assert hasattr(position, 'pos_short')
        assert hasattr(position, 'pos_short_today')
        assert hasattr(position, 'pos_short_his')
        assert hasattr(position, 'open_price_short')


class TestAPIBehavior:
    """测试 API 行为与重构前一致"""

    @patch('src.services.md_client.MdClient')
    @patch('src.services.td_client.TdClient')
    def test_initialization_behavior(self, mock_td_client_class, mock_md_client_class):
        """测试初始化行为"""
        mock_md_instance = Mock()
        mock_md_instance.start = AsyncMock()
        mock_md_client_class.return_value = mock_md_instance
        
        mock_td_instance = Mock()
        mock_td_instance.start = AsyncMock()
        mock_td_client_class.return_value = mock_td_instance
        
        # 应该能够正常初始化
        api = SyncStrategyApi(TEST_USER_ID, TEST_PASSWORD)
        
        # 验证内部状态
        assert api._event_loop_thread is not None
        assert api._quote_cache is not None
        assert api._position_cache is not None
        
        api.stop()

    @patch('src.services.md_client.MdClient')
    @patch('src.services.td_client.TdClient')
    def test_get_quote_returns_none_for_nonexistent(self, mock_td_client_class, mock_md_client_class):
        """测试 get_quote 对不存在的合约返回 None"""
        mock_md_instance = Mock()
        mock_md_instance.start = AsyncMock()
        mock_md_client_class.return_value = mock_md_instance
        
        mock_td_instance = Mock()
        mock_td_instance.start = AsyncMock()
        mock_td_client_class.return_value = mock_td_instance
        
        api = SyncStrategyApi(TEST_USER_ID, TEST_PASSWORD)
        
        # 对于不存在的合约，应该返回 None
        quote = api.get_quote("NONEXISTENT")
        assert quote is None
        
        api.stop()

    @patch('src.services.md_client.MdClient')
    @patch('src.services.td_client.TdClient')
    def test_get_position_returns_empty_for_nonexistent(self, mock_td_client_class, mock_md_client_class):
        """测试 get_position 对不存在的合约返回空持仓"""
        mock_md_instance = Mock()
        mock_md_instance.start = AsyncMock()
        mock_md_client_class.return_value = mock_md_instance
        
        mock_td_instance = Mock()
        mock_td_instance.start = AsyncMock()
        mock_td_client_class.return_value = mock_td_instance
        
        api = SyncStrategyApi(TEST_USER_ID, TEST_PASSWORD)
        
        # 对于不存在的合约，应该返回空持仓对象
        position = api.get_position("NONEXISTENT")
        assert position is not None
        assert position.pos_long == 0
        assert position.pos_short == 0
        
        api.stop()

    @patch('src.services.md_client.MdClient')
    @patch('src.services.td_client.TdClient')
    def test_stop_can_be_called_multiple_times(self, mock_td_client_class, mock_md_client_class):
        """测试 stop 方法可以多次调用"""
        mock_md_instance = Mock()
        mock_md_instance.start = AsyncMock()
        mock_md_client_class.return_value = mock_md_instance
        
        mock_td_instance = Mock()
        mock_td_instance.start = AsyncMock()
        mock_td_client_class.return_value = mock_td_instance
        
        api = SyncStrategyApi(TEST_USER_ID, TEST_PASSWORD)
        
        # 应该能够多次调用 stop 而不抛出异常
        api.stop()
        api.stop()
        api.stop()


class TestPublicAPIExports:
    """测试公共 API 导出"""

    def test_sync_strategy_api_exported(self):
        """测试 SyncStrategyApi 被导出"""
        from src.strategy.sync_api import SyncStrategyApi as ImportedAPI
        assert ImportedAPI is not None

    def test_quote_exported(self):
        """测试 Quote 被导出"""
        from src.strategy.sync_api import Quote as ImportedQuote
        assert ImportedQuote is not None

    def test_position_exported(self):
        """测试 Position 被导出"""
        from src.strategy.sync_api import Position as ImportedPosition
        assert ImportedPosition is not None

    def test_strategy_plugin_exported(self):
        """测试 StrategyPlugin 被导出"""
        from src.strategy.sync_api import StrategyPlugin as ImportedPlugin
        assert ImportedPlugin is not None


class TestExampleCodeCompatibility:
    """测试现有示例代码的兼容性"""

    @patch('src.services.md_client.MdClient')
    @patch('src.services.td_client.TdClient')
    def test_basic_usage_pattern(self, mock_td_client_class, mock_md_client_class):
        """测试基本使用模式"""
        mock_md_instance = Mock()
        mock_md_instance.start = AsyncMock()
        mock_md_client_class.return_value = mock_md_instance
        
        mock_td_instance = Mock()
        mock_td_instance.start = AsyncMock()
        mock_td_client_class.return_value = mock_td_instance
        
        # 模拟典型的使用模式
        api = SyncStrategyApi(TEST_USER_ID, TEST_PASSWORD)
        
        # 获取行情
        quote = api.get_quote("rb2505")
        
        # 获取持仓
        position = api.get_position("rb2505")
        
        # 停止
        api.stop()
        
        # 验证：不应该抛出任何异常

    @patch('src.services.md_client.MdClient')
    @patch('src.services.td_client.TdClient')
    def test_strategy_function_pattern(self, mock_td_client_class, mock_md_client_class):
        """测试策略函数模式"""
        mock_md_instance = Mock()
        mock_md_instance.start = AsyncMock()
        mock_md_client_class.return_value = mock_md_instance
        
        mock_td_instance = Mock()
        mock_td_instance.start = AsyncMock()
        mock_td_client_class.return_value = mock_td_instance
        
        api = SyncStrategyApi(TEST_USER_ID, TEST_PASSWORD)
        
        # 定义策略函数
        def my_strategy(api):
            quote = api.get_quote("rb2505")
            position = api.get_position("rb2505")
            # 策略逻辑...
            api.stop()
        
        # 应该能够传递策略函数
        # 注意：这里不实际运行，只验证接口兼容性
        assert callable(my_strategy)
        
        api.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
