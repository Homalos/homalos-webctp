#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : test_sync_api_init.py
@Date       : 2025/12/17
@Author     : Kiro AI Assistant
@Email      : -
@Software   : PyCharm
@Description: 测试 SyncStrategyApi.__init__() 方法

验证任务 11.1 的要求：
- 初始化所有内部数据结构
- 创建 QuoteCache 和 PositionCache
- 启动后台事件循环线程
- 等待 CTP 连接就绪
"""

import pytest
from unittest.mock import patch, MagicMock
from src.strategy.sync_api import SyncStrategyApi


class TestSyncApiInit:
    """测试 SyncStrategyApi.__init__() 方法"""
    
    def test_init_requires_user_credentials(self):
        """
        测试 __init__ 方法需要用户凭证
        
        验证：
        1. user_id 参数是必需的
        2. password 参数是必需的
        3. 缺少参数时抛出 TypeError
        
        Requirements: 5.1, 5.2, 5.3
        """
        # 测试缺少所有参数
        with pytest.raises(TypeError, match="missing 2 required positional arguments"):
            SyncStrategyApi()
        
        # 测试只提供 user_id
        with pytest.raises(TypeError, match="missing 1 required positional argument"):
            SyncStrategyApi(user_id="test_user")
        
        # 测试只提供 password
        with pytest.raises(TypeError, match="missing 1 required positional argument"):
            SyncStrategyApi(password="test_password")
    
    @patch('src.strategy.sync_api._EventLoopThread')
    def test_init_creates_internal_data_structures(self, mock_event_loop):
        """
        测试 __init__ 方法创建内部数据结构
        
        验证：
        1. QuoteCache 被创建
        2. PositionCache 被创建
        3. 订阅状态跟踪被初始化
        4. 持仓查询状态跟踪被初始化
        5. 策略管理被初始化
        
        Requirements: 5.1
        """
        # Mock 事件循环线程
        mock_instance = MagicMock()
        mock_event_loop.return_value = mock_instance
        
        # 初始化 API
        api = SyncStrategyApi(user_id="test_user", password="test_password")
        
        # 验证内部数据结构被创建
        assert api._quote_cache is not None, "QuoteCache 应该被创建"
        assert api._position_cache is not None, "PositionCache 应该被创建"
        assert api._subscribed_instruments is not None, "订阅状态跟踪应该被初始化"
        assert api._subscription_lock is not None, "订阅锁应该被创建"
        assert api._position_query_events is not None, "持仓查询事件应该被初始化"
        assert api._position_query_lock is not None, "持仓查询锁应该被创建"
        assert api._running_strategies is not None, "策略注册表应该被初始化"
        assert api._strategy_lock is not None, "策略锁应该被创建"
    
    @patch('src.strategy.sync_api._EventLoopThread')
    def test_init_starts_event_loop_thread(self, mock_event_loop):
        """
        测试 __init__ 方法启动事件循环线程
        
        验证：
        1. _EventLoopThread 被创建
        2. start() 方法被调用，传入用户凭证
        3. wait_ready() 方法被调用
        
        Requirements: 5.1, 5.2, 5.3
        """
        # Mock 事件循环线程
        mock_instance = MagicMock()
        mock_event_loop.return_value = mock_instance
        
        # 初始化 API
        api = SyncStrategyApi(
            user_id="test_user",
            password="test_password",
            config_path="test_config.yaml"
        )
        
        # 验证 _EventLoopThread 被创建
        mock_event_loop.assert_called_once()
        
        # 验证 start() 被调用，传入用户凭证和配置路径
        mock_instance.start.assert_called_once_with(
            "test_user",
            "test_password",
            "test_config.yaml"
        )
        
        # 验证 wait_ready() 被调用
        mock_instance.wait_ready.assert_called_once()
    
    @patch('src.strategy.sync_api._EventLoopThread')
    def test_init_sets_callbacks(self, mock_event_loop):
        """
        测试 __init__ 方法设置回调函数
        
        验证：
        1. 行情回调被设置
        2. 交易回调被设置
        
        Requirements: 5.2
        """
        # Mock 事件循环线程
        mock_instance = MagicMock()
        mock_event_loop.return_value = mock_instance
        
        # 初始化 API
        api = SyncStrategyApi(user_id="test_user", password="test_password")
        
        # 验证回调被设置
        mock_instance.set_md_callback.assert_called_once()
        mock_instance.set_td_callback.assert_called_once()
        
        # 验证回调函数是正确的方法
        md_callback = mock_instance.set_md_callback.call_args[0][0]
        td_callback = mock_instance.set_td_callback.call_args[0][0]
        
        assert md_callback == api._on_market_data, "行情回调应该是 _on_market_data"
        assert td_callback == api._on_trade_data, "交易回调应该是 _on_trade_data"
    
    @patch('src.strategy.sync_api._EventLoopThread')
    def test_init_uses_custom_timeout(self, mock_event_loop):
        """
        测试 __init__ 方法使用自定义超时时间
        
        验证：
        1. 传入的 timeout 参数被使用
        2. wait_ready() 使用正确的超时值
        
        Requirements: 5.4
        """
        # Mock 事件循环线程
        mock_instance = MagicMock()
        mock_event_loop.return_value = mock_instance
        
        # 初始化 API，传入自定义超时
        api = SyncStrategyApi(
            user_id="test_user",
            password="test_password",
            timeout=60.0
        )
        
        # 验证 wait_ready() 使用自定义超时
        mock_instance.wait_ready.assert_called_once_with(timeout=60.0)
    
    @patch('src.strategy.sync_api._EventLoopThread')
    def test_init_uses_config_timeout_when_not_specified(self, mock_event_loop):
        """
        测试 __init__ 方法在未指定超时时使用配置值
        
        验证：
        1. 未传入 timeout 参数时使用配置的默认值
        2. wait_ready() 使用配置的超时值
        
        Requirements: 5.4, 10.4
        """
        # Mock 事件循环线程
        mock_instance = MagicMock()
        mock_event_loop.return_value = mock_instance
        
        # 初始化 API，不传入 timeout
        api = SyncStrategyApi(user_id="test_user", password="test_password")
        
        # 验证 wait_ready() 被调用（使用配置的默认超时）
        mock_instance.wait_ready.assert_called_once()
        
        # 获取实际使用的超时值
        actual_timeout = mock_instance.wait_ready.call_args[1]['timeout']
        
        # 验证使用的是配置的超时值
        assert actual_timeout == api._config.connect_timeout, \
            "应该使用配置的 connect_timeout"
    
    @patch('src.strategy.sync_api._EventLoopThread')
    def test_init_handles_connection_timeout(self, mock_event_loop):
        """
        测试 __init__ 方法处理连接超时
        
        验证：
        1. wait_ready() 超时时抛出 TimeoutError
        2. 异常被正确传播
        
        Requirements: 5.5
        """
        # Mock 事件循环线程，wait_ready() 抛出 TimeoutError
        mock_instance = MagicMock()
        mock_instance.wait_ready.side_effect = TimeoutError("连接超时")
        mock_event_loop.return_value = mock_instance
        
        # 验证初始化时抛出 TimeoutError
        with pytest.raises(TimeoutError, match="连接超时"):
            SyncStrategyApi(user_id="test_user", password="test_password")
    
    @patch('src.strategy.sync_api._EventLoopThread')
    def test_init_handles_connection_failure(self, mock_event_loop):
        """
        测试 __init__ 方法处理连接失败
        
        验证：
        1. wait_ready() 失败时抛出 RuntimeError
        2. 异常被正确传播
        
        Requirements: 5.5
        """
        # Mock 事件循环线程，wait_ready() 抛出 RuntimeError
        mock_instance = MagicMock()
        mock_instance.wait_ready.side_effect = RuntimeError("连接失败")
        mock_event_loop.return_value = mock_instance
        
        # 验证初始化时抛出 RuntimeError
        with pytest.raises(RuntimeError, match="连接失败"):
            SyncStrategyApi(user_id="test_user", password="test_password")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
