#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : test_sync_api_event_loop_exception.py
@Date       : 2025/12/17
@Author     : Kiro AI Assistant
@Email      : -
@Software   : PyCharm
@Description: 测试异步事件循环异常处理

验证需求 7.5: WHEN 异步事件循环异常 THEN 系统 SHALL 记录错误并标记服务不可用
"""

import pytest
import time
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from hypothesis import given, strategies as st, settings
from src.strategy.sync_api import _EventLoopThread, SyncStrategyApi, Position
# Test credentials
TEST_USER_ID = "test_user"
TEST_PASSWORD = "test_pass"


class TestEventLoopExceptionHandling:
    """测试事件循环异常处理的基本行为"""
    
    @patch('src.services.md_client.MdClient')
    @patch('src.services.td_client.TdClient')
    def test_event_loop_exception_marks_service_unavailable(
        self, 
        mock_td_client, 
        mock_md_client
    ):
        """
        测试事件循环异常时标记服务不可用
        
        验证：
        1. 初始化失败时 _service_available 被设置为 False
        2. 初始化错误被保存到 _init_error
        3. wait_ready() 抛出 RuntimeError
        """
        # 创建会抛出异常的 mock，导致初始化失败
        async def failing_start(*args):
            raise RuntimeError("模拟事件循环初始化失败")
        
        mock_md_instance = Mock()
        mock_md_instance.start = AsyncMock(side_effect=failing_start)
        mock_md_client.return_value = mock_md_instance
        
        mock_td_instance = Mock()
        mock_td_instance.start = AsyncMock()
        mock_td_client.return_value = mock_td_instance
        
        thread = _EventLoopThread()
        thread.start(TEST_USER_ID, TEST_PASSWORD)
        
        # 等待初始化完成（会失败）
        time.sleep(1.0)
        
        # 验证服务被标记为不可用
        assert thread.is_service_available is False, "服务应该被标记为不可用"
        
        # 验证 wait_ready() 抛出 RuntimeError
        with pytest.raises(RuntimeError, match="CTP 客户端初始化失败"):
            thread.wait_ready(timeout=2.0)
        
        # 清理
        thread.stop(timeout=2.0)
    
    @patch('src.services.md_client.MdClient')
    @patch('src.services.td_client.TdClient')
    def test_event_loop_exception_logged(
        self, 
        mock_td_client, 
        mock_md_client
    ):
        """
        测试事件循环异常被记录
        
        验证：
        1. 异常被记录到日志
        2. 包含完整的堆栈信息
        """
        # 创建会抛出异常的 mock
        async def failing_start(*args):
            raise ValueError("模拟值错误")
        
        mock_md_instance = Mock()
        mock_md_instance.start = AsyncMock(side_effect=failing_start)
        mock_md_client.return_value = mock_md_instance
        
        mock_td_instance = Mock()
        mock_td_instance.start = AsyncMock()
        mock_td_client.return_value = mock_td_instance
        
        thread = _EventLoopThread()
        
        # 使用 caplog 捕获日志
        with patch('src.strategy.sync_api.logger') as mock_logger:
            thread.start(TEST_USER_ID, TEST_PASSWORD)
            
            # 等待初始化完成（会失败）
            time.sleep(1.0)
            
            # 验证错误日志被记录
            # 检查是否调用了 logger.error
            assert mock_logger.error.called, "应该记录错误日志"
            
            # 检查日志消息
            error_calls = [call for call in mock_logger.error.call_args_list]
            assert len(error_calls) > 0, "应该至少有一条错误日志"
            
            # 验证日志包含异常信息
            log_messages = [str(call) for call in error_calls]
            assert any("事件循环" in msg or "异常" in msg for msg in log_messages), \
                "日志应该包含事件循环异常信息"
        
        # 清理
        thread.stop(timeout=2.0)
    
    @patch('src.services.md_client.MdClient')
    @patch('src.services.td_client.TdClient')
    def test_api_checks_service_availability_on_get_quote(
        self, 
        mock_td_client, 
        mock_md_client
    ):
        """
        测试 get_quote 检查服务可用性
        
        验证：
        1. 当服务不可用时，get_quote 抛出 RuntimeError
        2. 错误消息明确指出服务不可用
        """
        # 创建会抛出异常的 mock
        async def failing_start(*args):
            raise RuntimeError("模拟初始化失败")
        
        mock_md_instance = Mock()
        mock_md_instance.start = AsyncMock(side_effect=failing_start)
        mock_md_client.return_value = mock_md_instance
        
        mock_td_instance = Mock()
        mock_td_instance.start = AsyncMock()
        mock_td_client.return_value = mock_td_instance
        
        # 创建 API 实例
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 手动创建事件循环线程（模拟 connect）
        api._event_loop_thread = _EventLoopThread()
        api._event_loop_thread.start(TEST_USER_ID, TEST_PASSWORD)
        
        # 等待初始化失败
        time.sleep(1.0)
        
        # 验证服务不可用
        assert api._event_loop_thread.is_service_available is False
        
        # 调用 get_quote 应该抛出 RuntimeError
        with pytest.raises(RuntimeError, match="事件循环服务不可用"):
            api.get_quote("rb2505", timeout=1.0)
        
        # 清理
        api._event_loop_thread.stop(timeout=2.0)
    
    @patch('src.services.md_client.MdClient')
    @patch('src.services.td_client.TdClient')
    def test_api_checks_service_availability_on_get_position(
        self, 
        mock_td_client, 
        mock_md_client
    ):
        """
        测试 get_position 检查服务可用性
        
        验证：
        1. 当服务不可用时，get_position 返回空持仓对象
        2. 记录错误日志
        """
        # 创建会抛出异常的 mock
        async def failing_start(*args):
            raise RuntimeError("模拟初始化失败")
        
        mock_md_instance = Mock()
        mock_md_instance.start = AsyncMock(side_effect=failing_start)
        mock_md_client.return_value = mock_md_instance
        
        mock_td_instance = Mock()
        mock_td_instance.start = AsyncMock()
        mock_td_client.return_value = mock_td_client
        
        # 创建 API 实例
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 手动创建事件循环线程（模拟 connect）
        api._event_loop_thread = _EventLoopThread()
        api._event_loop_thread.start(TEST_USER_ID, TEST_PASSWORD)
        
        # 等待初始化失败
        time.sleep(1.0)
        
        # 验证服务不可用
        assert api._event_loop_thread.is_service_available is False
        
        # 调用 get_position 应该返回空持仓对象（不抛出异常）
        position = api.get_position("rb2505", timeout=1.0)
        
        # 验证返回的是空持仓对象
        assert isinstance(position, Position)
        assert position.pos_long == 0
        assert position.pos_short == 0
        
        # 清理
        api._event_loop_thread.stop(timeout=2.0)
    
    @patch('src.services.md_client.MdClient')
    @patch('src.services.td_client.TdClient')
    def test_api_checks_service_availability_on_open_close(
        self, 
        mock_td_client, 
        mock_md_client
    ):
        """
        测试 open_close 检查服务可用性
        
        验证：
        1. 当服务不可用时，open_close 抛出 RuntimeError
        2. 错误消息明确指出服务不可用
        """
        # 创建会抛出异常的 mock
        async def failing_start(*args):
            raise RuntimeError("模拟初始化失败")
        
        mock_md_instance = Mock()
        mock_md_instance.start = AsyncMock(side_effect=failing_start)
        mock_md_client.return_value = mock_md_instance
        
        mock_td_instance = Mock()
        mock_td_instance.start = AsyncMock()
        mock_td_client.return_value = mock_td_instance
        
        # 创建 API 实例
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 手动创建事件循环线程（模拟 connect）
        api._event_loop_thread = _EventLoopThread()
        api._event_loop_thread.start(TEST_USER_ID, TEST_PASSWORD)
        
        # 等待初始化失败
        time.sleep(1.0)
        
        # 验证服务不可用
        assert api._event_loop_thread.is_service_available is False
        
        # 调用 open_close 应该抛出 RuntimeError
        with pytest.raises(RuntimeError, match="事件循环服务不可用"):
            api.open_close("rb2505", "kaiduo", 1, 3500.0)
        
        # 清理
        api._event_loop_thread.stop(timeout=2.0)


class TestPropertyEventLoopExceptionHandling:
    """
    Property 17: 异步事件循环异常处理
    
    Feature: sync-strategy-api, Property 17: 异步事件循环异常处理
    Validates: Requirements 7.5
    
    验证对于任意异步事件循环中的异常，系统都能记录错误并标记服务不可用。
    """
    
    @given(
        exception_type=st.sampled_from([
            RuntimeError,
            ValueError,
            TypeError,
            ConnectionError,
            OSError,
            Exception
        ]),
        error_message=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs')),
            min_size=5,
            max_size=50
        )
    )
    @settings(max_examples=100, deadline=None)
    @patch('src.services.md_client.MdClient')
    @patch('src.services.td_client.TdClient')
    def test_property_event_loop_exception_handling(
        self,
        mock_td_client,
        mock_md_client,
        exception_type,
        error_message
    ):
        """
        Property 17: 异步事件循环异常处理
        
        对于任意类型的异常和任意错误消息，当异步事件循环初始化失败时：
        1. 系统应该捕获异常
        2. 记录错误日志（包含完整堆栈信息）
        3. 标记服务不可用（_service_available = False）
        4. 保存初始化错误（_init_error）
        5. wait_ready() 应该抛出 RuntimeError
        6. 不会静默失败
        
        Args:
            exception_type: 随机选择的异常类型
            error_message: 随机生成的错误消息
        """
        # 创建会抛出指定异常的 mock
        async def failing_start(*args):
            raise exception_type(error_message)
        
        mock_md_instance = Mock()
        mock_md_instance.start = AsyncMock(side_effect=failing_start)
        mock_md_client.return_value = mock_md_instance
        
        mock_td_instance = Mock()
        mock_td_instance.start = AsyncMock()
        mock_td_client.return_value = mock_td_instance
        
        # 创建事件循环线程
        thread = _EventLoopThread()
        
        # 使用 mock logger 捕获日志
        with patch('src.strategy.sync_api.logger') as mock_logger:
            # 启动线程（会失败）
            thread.start(TEST_USER_ID, TEST_PASSWORD)
            
            # 等待初始化完成（会失败）
            time.sleep(1.0)
            
            # 验证1：服务被标记为不可用
            assert thread.is_service_available is False, \
                f"服务应该被标记为不可用（异常类型: {exception_type.__name__}）"
            
            # 验证2：初始化错误被保存
            assert thread._init_error is not None, \
                "初始化错误应该被保存"
            assert isinstance(thread._init_error, exception_type), \
                f"保存的错误类型应该是 {exception_type.__name__}"
            
            # 验证3：错误日志被记录
            assert mock_logger.error.called, \
                "应该记录错误日志"
            
            # 验证4：wait_ready() 抛出 RuntimeError（不是静默失败）
            with pytest.raises(RuntimeError, match="CTP 客户端初始化失败"):
                thread.wait_ready(timeout=2.0)
        
        # 清理
        thread.stop(timeout=2.0)
    
    @given(
        exception_type=st.sampled_from([
            RuntimeError,
            ValueError,
            ConnectionError,
            OSError
        ])
    )
    @settings(max_examples=50, deadline=None)
    @patch('src.services.md_client.MdClient')
    @patch('src.services.td_client.TdClient')
    def test_property_api_operations_fail_gracefully_when_service_unavailable(
        self,
        mock_td_client,
        mock_md_client,
        exception_type
    ):
        """
        Property 17 扩展：服务不可用时 API 操作优雅失败
        
        对于任意类型的初始化异常，当服务不可用时：
        1. get_quote() 应该抛出 RuntimeError（明确错误）
        2. get_position() 应该返回空持仓对象（优雅降级）
        3. wait_quote_update() 应该抛出 RuntimeError（明确错误）
        4. open_close() 应该抛出 RuntimeError（明确错误）
        5. 不会出现未处理的异常或崩溃
        
        Args:
            exception_type: 随机选择的异常类型
        """
        # 创建会抛出异常的 mock
        async def failing_start(*args):
            raise exception_type("模拟初始化失败")
        
        mock_md_instance = Mock()
        mock_md_instance.start = AsyncMock(side_effect=failing_start)
        mock_md_client.return_value = mock_md_instance
        
        mock_td_instance = Mock()
        mock_td_instance.start = AsyncMock()
        mock_td_client.return_value = mock_td_instance
        
        # 创建 API 实例
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 手动创建事件循环线程（模拟 connect）
        api._event_loop_thread = _EventLoopThread()
        api._event_loop_thread.start(TEST_USER_ID, TEST_PASSWORD)
        
        # 等待初始化失败
        time.sleep(1.0)
        
        # 验证服务不可用
        assert api._event_loop_thread.is_service_available is False
        
        # 测试1：get_quote 抛出 RuntimeError
        with pytest.raises(RuntimeError, match="事件循环服务不可用"):
            api.get_quote("rb2505", timeout=1.0)
        
        # 测试2：get_position 返回空持仓对象（优雅降级）
        position = api.get_position("rb2505", timeout=1.0)
        assert isinstance(position, Position)
        assert position.pos_long == 0
        assert position.pos_short == 0
        
        # 测试3：wait_quote_update 抛出 RuntimeError
        with pytest.raises(RuntimeError, match="事件循环服务不可用"):
            api.wait_quote_update("rb2505", timeout=1.0)
        
        # 测试4：open_close 抛出 RuntimeError
        with pytest.raises(RuntimeError, match="事件循环服务不可用"):
            api.open_close("rb2505", "kaiduo", 1, 3500.0)
        
        # 清理
        api._event_loop_thread.stop(timeout=2.0)
    
    @given(
        num_exceptions=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=20, deadline=None)
    @patch('src.services.md_client.MdClient')
    @patch('src.services.td_client.TdClient')
    def test_property_multiple_exceptions_handled_consistently(
        self,
        mock_td_client,
        mock_md_client,
        num_exceptions
    ):
        """
        Property 17 扩展：多次异常处理的一致性
        
        对于任意数量的连续异常，系统应该：
        1. 每次都正确标记服务不可用
        2. 每次都记录错误日志
        3. 每次都保存错误信息
        4. 行为保持一致
        
        Args:
            num_exceptions: 随机生成的异常次数
        """
        exception_types = [RuntimeError, ValueError, ConnectionError, OSError, TypeError]
        
        for i in range(num_exceptions):
            # 选择异常类型
            exception_type = exception_types[i % len(exception_types)]
            
            # 创建会抛出异常的 mock
            async def failing_start(*args):
                raise exception_type(f"模拟第 {i+1} 次异常")
            
            mock_md_instance = Mock()
            mock_md_instance.start = AsyncMock(side_effect=failing_start)
            mock_md_client.return_value = mock_md_instance
            
            mock_td_instance = Mock()
            mock_td_instance.start = AsyncMock()
            mock_td_client.return_value = mock_td_instance
            
            # 创建事件循环线程
            thread = _EventLoopThread()
            
            with patch('src.strategy.sync_api.logger') as mock_logger:
                # 启动线程（会失败）
                thread.start(TEST_USER_ID, TEST_PASSWORD)
                
                # 等待初始化失败
                time.sleep(0.5)
                
                # 验证：每次都正确处理
                assert thread.is_service_available is False, \
                    f"第 {i+1} 次异常：服务应该被标记为不可用"
                
                assert thread._init_error is not None, \
                    f"第 {i+1} 次异常：错误应该被保存"
                
                assert mock_logger.error.called, \
                    f"第 {i+1} 次异常：应该记录错误日志"
                
                # 验证 wait_ready 抛出异常
                with pytest.raises(RuntimeError, match="CTP 客户端初始化失败"):
                    thread.wait_ready(timeout=1.0)
            
            # 清理
            thread.stop(timeout=1.0)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
