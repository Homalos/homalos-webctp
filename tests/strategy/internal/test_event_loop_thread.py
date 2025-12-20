#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : test_event_loop_thread.py
@Date       : 2025/12/20
@Author     : Kiro AI Assistant
@Email      : -
@Software   : PyCharm
@Description: _EventLoopThread 类的单元测试
"""

import pytest
import time
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.strategy.internal.event_loop_thread import _EventLoopThread

# 测试凭证
TEST_USER_ID = "test_user"
TEST_PASSWORD = "test_pass"


class TestEventLoopThread:
    """_EventLoopThread 类的单元测试"""
    
    def test_initialization(self):
        """测试 _EventLoopThread 初始化"""
        thread = _EventLoopThread()
        
        assert thread._anyio_token is None
        assert thread._thread is None
        assert thread._md_client is None
        assert thread._td_client is None
        assert thread._running is False
        assert thread._ready_event is not None
    
    @patch('src.services.md_client.MdClient')
    @patch('src.services.td_client.TdClient')
    def test_start_creates_thread(self, mock_td_client_class, mock_md_client_class, 
                                 mock_md_client, mock_td_client):
        """测试 start() 方法创建线程并初始化客户端"""
        mock_md_client_class.return_value = mock_md_client
        mock_td_client_class.return_value = mock_td_client
        
        thread = _EventLoopThread()
        thread.start(TEST_USER_ID, TEST_PASSWORD)
        
        assert thread._running is True
        assert thread._thread is not None
        assert thread._thread.is_alive()
        
        time.sleep(1.0)
        
        assert mock_md_client_class.called
        assert mock_td_client_class.called
        assert mock_md_client.start.called
        assert mock_td_client.start.called
        assert thread._md_client is not None
        assert thread._td_client is not None
        
        thread.stop(timeout=2.0)
    
    def test_start_twice_raises_error(self, mock_md_client_class, mock_td_client_class):
        """测试重复调用 start() 抛出异常"""
        thread = _EventLoopThread()
        thread.start(TEST_USER_ID, TEST_PASSWORD)
        
        with pytest.raises(RuntimeError, match="事件循环线程已经在运行"):
            thread.start(TEST_USER_ID, TEST_PASSWORD)
        
        thread.stop(timeout=2.0)
    
    @patch('src.services.md_client.MdClient')
    @patch('src.services.td_client.TdClient')
    def test_stop_stops_thread(self, mock_td_client_class, mock_md_client_class,
                              mock_md_client, mock_td_client):
        """测试 stop() 方法停止线程"""
        mock_md_client_class.return_value = mock_md_client
        mock_td_client_class.return_value = mock_td_client
        
        thread = _EventLoopThread()
        thread.start(TEST_USER_ID, TEST_PASSWORD)
        
        time.sleep(0.5)
        
        thread.stop(timeout=2.0)
        
        assert thread._running is False
        if thread._thread:
            time.sleep(0.5)
            assert not thread._thread.is_alive()
    
    def test_stop_when_not_running(self):
        """测试在未运行时调用 stop() 不会出错"""
        thread = _EventLoopThread()
        thread.stop(timeout=1.0)
        
        assert thread._running is False
    
    @patch('src.services.md_client.MdClient')
    @patch('src.services.td_client.TdClient')
    def test_wait_ready_with_init_error(self, mock_td_client_class, mock_md_client_class):
        """测试 wait_ready() 在初始化失败时抛出异常"""
        async def failing_start(*args):
            raise Exception("模拟初始化失败")
        
        mock_md_instance = Mock()
        mock_md_instance.start = AsyncMock(side_effect=failing_start)
        mock_md_client_class.return_value = mock_md_instance
        
        mock_td_instance = Mock()
        mock_td_instance.start = AsyncMock()
        mock_td_client_class.return_value = mock_td_instance
        
        thread = _EventLoopThread()
        thread.start(TEST_USER_ID, TEST_PASSWORD)
        
        with pytest.raises(RuntimeError, match="CTP 客户端初始化失败"):
            thread.wait_ready(timeout=2.0)
        
        thread.stop(timeout=2.0)
    
    @patch('src.services.md_client.MdClient')
    @patch('src.services.td_client.TdClient')
    def test_set_callbacks(self, mock_td_client_class, mock_md_client_class,
                          mock_md_client, mock_td_client):
        """测试设置回调函数"""
        mock_md_client_class.return_value = mock_md_client
        mock_td_client_class.return_value = mock_td_client
        
        thread = _EventLoopThread()
        thread.start(TEST_USER_ID, TEST_PASSWORD)
        
        time.sleep(0.5)
        
        md_callback = Mock()
        td_callback = Mock()
        
        thread.set_md_callback(md_callback)
        thread.set_td_callback(td_callback)
        
        assert thread._md_client.rsp_callback == md_callback
        assert thread._td_client.rsp_callback == td_callback
        
        thread.stop(timeout=2.0)
    
    @patch('src.services.md_client.MdClient')
    @patch('src.services.td_client.TdClient')
    def test_properties(self, mock_td_client_class, mock_md_client_class,
                       mock_md_client, mock_td_client):
        """测试属性访问"""
        mock_md_client_class.return_value = mock_md_client
        mock_td_client_class.return_value = mock_td_client
        
        thread = _EventLoopThread()
        
        assert thread.md_client is None
        assert thread.td_client is None
        
        thread.start(TEST_USER_ID, TEST_PASSWORD)
        
        time.sleep(0.5)
        
        assert thread.md_client is not None
        assert thread.td_client is not None
        
        thread.stop(timeout=2.0)
    
    @patch('src.services.md_client.MdClient')
    @patch('src.services.td_client.TdClient')
    def test_wait_ready_timeout_on_init(self, mock_td_client_class, mock_md_client_class):
        """测试 wait_ready() 在初始化阶段超时"""
        async def hanging_start(*args):
            await asyncio.sleep(100)
        
        mock_md_instance = Mock()
        mock_md_instance.start = AsyncMock(side_effect=hanging_start)
        mock_md_client_class.return_value = mock_md_instance
        
        mock_td_instance = Mock()
        mock_td_instance.start = AsyncMock(side_effect=hanging_start)
        mock_td_client_class.return_value = mock_td_instance
        
        thread = _EventLoopThread()
        thread.start(TEST_USER_ID, TEST_PASSWORD)
        
        with pytest.raises(TimeoutError, match="等待 CTP 客户端初始化超时"):
            thread.wait_ready(timeout=1.0)
        
        thread.stop(timeout=2.0)
    
    @patch('src.services.md_client.MdClient')
    @patch('src.services.td_client.TdClient')
    def test_wait_ready_timeout_on_login(self, mock_td_client_class, mock_md_client_class,
                                        mock_md_client, mock_td_client):
        """测试 wait_ready() 在登录阶段超时"""
        mock_md_client_class.return_value = mock_md_client
        mock_td_client_class.return_value = mock_td_client
        
        thread = _EventLoopThread()
        thread.start(TEST_USER_ID, TEST_PASSWORD)
        
        with pytest.raises(TimeoutError, match="等待 CTP 登录完成超时"):
            thread.wait_ready(timeout=2.0)
        
        thread.stop(timeout=2.0)
    
    @patch('src.services.md_client.MdClient')
    @patch('src.services.td_client.TdClient')
    def test_wait_ready_with_login_error(self, mock_td_client_class, mock_md_client_class,
                                        mock_md_client, mock_td_client):
        """测试 wait_ready() 在登录失败时抛出异常"""
        mock_md_client_class.return_value = mock_md_client
        mock_td_client_class.return_value = mock_td_client
        
        thread = _EventLoopThread()
        thread.start(TEST_USER_ID, TEST_PASSWORD)
        
        time.sleep(0.5)
        
        login_error_response = {
            'msg_type': 'OnRspUserLogin_Md',
            'RspInfo': {
                'ErrorID': 3,
                'ErrorMsg': '用户名或密码错误'
            }
        }
        
        thread._on_login_response(login_error_response)
        
        with pytest.raises(RuntimeError, match="CTP 登录失败"):
            thread.wait_ready(timeout=2.0)
        
        thread.stop(timeout=2.0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
