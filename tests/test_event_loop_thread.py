#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : test_event_loop_thread.py
@Date       : 2025/12/16
@Author     : Kiro AI Assistant
@Email      : -
@Software   : PyCharm
@Description: _EventLoopThread 类的单元测试
"""

import pytest
import time
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.strategy.sync_api import _EventLoopThread


class TestEventLoopThread:
    """_EventLoopThread 类的单元测试"""
    
    def test_initialization(self):
        """测试 _EventLoopThread 初始化"""
        thread = _EventLoopThread()
        
        assert thread._loop is None
        assert thread._thread is None
        assert thread._md_client is None
        assert thread._td_client is None
        assert thread._running is False
        assert thread._ready_event is not None
    
    @patch('src.services.md_client.MdClient')
    @patch('src.services.td_client.TdClient')
    def test_start_creates_thread(self, mock_td_client, mock_md_client):
        """测试 start() 方法创建线程并初始化客户端"""
        # 创建 mock 客户端实例
        mock_md_instance = Mock()
        mock_md_instance.start = AsyncMock()
        mock_md_client.return_value = mock_md_instance
        
        mock_td_instance = Mock()
        mock_td_instance.start = AsyncMock()
        mock_td_client.return_value = mock_td_instance
        
        thread = _EventLoopThread()
        
        # 启动线程
        thread.start("test_user", "test_password")
        
        # 验证线程已创建并启动
        assert thread._running is True
        assert thread._thread is not None
        assert thread._thread.is_alive()
        
        # 等待初始化完成（最多 5 秒）
        time.sleep(1.0)  # 给线程时间初始化
        
        # 验证 MdClient 和 TdClient 已创建
        assert mock_md_client.called, "MdClient 应该被创建"
        assert mock_td_client.called, "TdClient 应该被创建"
        
        # 验证客户端的 start 方法被调用
        assert mock_md_instance.start.called, "MdClient.start() 应该被调用"
        assert mock_td_instance.start.called, "TdClient.start() 应该被调用"
        
        # 验证客户端实例已设置
        assert thread._md_client is not None, "MdClient 实例应该被设置"
        assert thread._td_client is not None, "TdClient 实例应该被设置"
        
        # 清理
        thread.stop(timeout=2.0)
    
    def test_start_twice_raises_error(self):
        """测试重复调用 start() 抛出异常"""
        thread = _EventLoopThread()
        
        with patch('src.services.md_client.MdClient'), \
             patch('src.services.td_client.TdClient'):
            thread.start("test_user", "test_password")
            
            # 尝试再次启动应该抛出异常
            with pytest.raises(RuntimeError, match="事件循环线程已经在运行"):
                thread.start("test_user", "test_password")
            
            # 清理
            thread.stop(timeout=2.0)
    
    @patch('src.services.md_client.MdClient')
    @patch('src.services.td_client.TdClient')
    def test_stop_stops_thread(self, mock_td_client, mock_md_client):
        """测试 stop() 方法停止线程"""
        # 创建 mock 客户端实例
        mock_md_instance = Mock()
        mock_md_instance.start = AsyncMock()
        mock_md_instance.stop = AsyncMock()
        mock_md_client.return_value = mock_md_instance
        
        mock_td_instance = Mock()
        mock_td_instance.start = AsyncMock()
        mock_td_instance.stop = AsyncMock()
        mock_td_client.return_value = mock_td_instance
        
        thread = _EventLoopThread()
        thread.start("test_user", "test_password")
        
        # 等待线程启动
        time.sleep(0.5)
        
        # 停止线程
        thread.stop(timeout=2.0)
        
        # 验证线程已停止
        assert thread._running is False
        if thread._thread:
            # 给线程一点时间完全停止
            time.sleep(0.5)
            assert not thread._thread.is_alive()
    
    def test_stop_when_not_running(self):
        """测试在未运行时调用 stop() 不会出错"""
        thread = _EventLoopThread()
        
        # 应该不会抛出异常
        thread.stop(timeout=1.0)
        
        assert thread._running is False
    
    @patch('src.services.md_client.MdClient')
    @patch('src.services.td_client.TdClient')
    def test_wait_ready_with_init_error(self, mock_td_client, mock_md_client):
        """测试 wait_ready() 在初始化失败时抛出异常"""
        # 创建会抛出异常的 mock，导致初始化失败
        async def failing_start(*args):
            raise Exception("模拟初始化失败")
        
        mock_md_instance = Mock()
        mock_md_instance.start = AsyncMock(side_effect=failing_start)
        mock_md_client.return_value = mock_md_instance
        
        mock_td_instance = Mock()
        mock_td_instance.start = AsyncMock()
        mock_td_client.return_value = mock_td_instance
        
        thread = _EventLoopThread()
        thread.start("test_user", "test_password")
        
        # 等待就绪应该抛出 RuntimeError（因为初始化失败）
        with pytest.raises(RuntimeError, match="CTP 客户端初始化失败"):
            thread.wait_ready(timeout=2.0)
        
        # 清理
        thread.stop(timeout=2.0)
    
    @patch('src.services.md_client.MdClient')
    @patch('src.services.td_client.TdClient')
    def test_set_callbacks(self, mock_td_client, mock_md_client):
        """测试设置回调函数"""
        # 创建 mock 客户端实例
        mock_md_instance = Mock()
        mock_md_instance.start = AsyncMock()
        mock_md_client.return_value = mock_md_instance
        
        mock_td_instance = Mock()
        mock_td_instance.start = AsyncMock()
        mock_td_client.return_value = mock_td_instance
        
        thread = _EventLoopThread()
        thread.start("test_user", "test_password")
        
        # 等待初始化
        time.sleep(0.5)
        
        # 设置回调函数
        md_callback = Mock()
        td_callback = Mock()
        
        thread.set_md_callback(md_callback)
        thread.set_td_callback(td_callback)
        
        # 验证回调已设置
        assert thread._md_client.rsp_callback == md_callback
        assert thread._td_client.rsp_callback == td_callback
        
        # 清理
        thread.stop(timeout=2.0)
    
    @patch('src.services.md_client.MdClient')
    @patch('src.services.td_client.TdClient')
    def test_properties(self, mock_td_client, mock_md_client):
        """测试属性访问"""
        # 创建 mock 客户端实例
        mock_md_instance = Mock()
        mock_md_instance.start = AsyncMock()
        mock_md_client.return_value = mock_md_instance
        
        mock_td_instance = Mock()
        mock_td_instance.start = AsyncMock()
        mock_td_client.return_value = mock_td_instance
        
        thread = _EventLoopThread()
        
        # 启动前属性应该为 None
        assert thread.loop is None
        assert thread.md_client is None
        assert thread.td_client is None
        
        thread.start("test_user", "test_password")
        
        # 等待初始化
        time.sleep(0.5)
        
        # 启动后属性应该有值
        assert thread.loop is not None
        assert thread.md_client is not None
        assert thread.td_client is not None
        
        # 清理
        thread.stop(timeout=2.0)
    
    @patch('src.services.md_client.MdClient')
    @patch('src.services.td_client.TdClient')
    def test_wait_ready_timeout_on_init(self, mock_td_client, mock_md_client):
        """测试 wait_ready() 在初始化阶段超时"""
        # 创建永远不会完成的 mock，模拟初始化挂起
        async def hanging_start(*args):
            await asyncio.sleep(100)  # 模拟长时间挂起
        
        mock_md_instance = Mock()
        mock_md_instance.start = AsyncMock(side_effect=hanging_start)
        mock_md_client.return_value = mock_md_instance
        
        mock_td_instance = Mock()
        mock_td_instance.start = AsyncMock(side_effect=hanging_start)
        mock_td_client.return_value = mock_td_instance
        
        thread = _EventLoopThread()
        thread.start("test_user", "test_password")
        
        # 等待就绪应该超时（设置很短的超时时间）
        with pytest.raises(TimeoutError, match="等待 CTP 客户端初始化超时"):
            thread.wait_ready(timeout=1.0)
        
        # 清理
        thread.stop(timeout=2.0)
    
    @patch('src.services.md_client.MdClient')
    @patch('src.services.td_client.TdClient')
    def test_wait_ready_timeout_on_login(self, mock_td_client, mock_md_client):
        """测试 wait_ready() 在登录阶段超时"""
        # 创建 mock 客户端实例，start 方法正常完成但不触发登录回调
        mock_md_instance = Mock()
        mock_md_instance.start = AsyncMock()  # 正常完成
        mock_md_client.return_value = mock_md_instance
        
        mock_td_instance = Mock()
        mock_td_instance.start = AsyncMock()  # 正常完成
        mock_td_client.return_value = mock_td_instance
        
        thread = _EventLoopThread()
        thread.start("test_user", "test_password")
        
        # 等待就绪应该在登录阶段超时（因为没有登录回调）
        with pytest.raises(TimeoutError, match="等待 CTP 登录完成超时"):
            thread.wait_ready(timeout=2.0)
        
        # 清理
        thread.stop(timeout=2.0)
    
    @patch('src.services.md_client.MdClient')
    @patch('src.services.td_client.TdClient')
    def test_wait_ready_with_login_error(self, mock_td_client, mock_md_client):
        """测试 wait_ready() 在登录失败时抛出异常"""
        # 创建 mock 客户端实例
        mock_md_instance = Mock()
        mock_md_instance.start = AsyncMock()
        mock_md_client.return_value = mock_md_instance
        
        mock_td_instance = Mock()
        mock_td_instance.start = AsyncMock()
        mock_td_client.return_value = mock_td_instance
        
        thread = _EventLoopThread()
        thread.start("test_user", "test_password")
        
        # 等待初始化完成
        time.sleep(0.5)
        
        # 模拟登录失败响应
        login_error_response = {
            'msg_type': 'OnRspUserLogin_Md',
            'RspInfo': {
                'ErrorID': 3,
                'ErrorMsg': '用户名或密码错误'
            }
        }
        
        # 触发登录失败回调
        thread._on_login_response(login_error_response)
        
        # 等待就绪应该抛出 RuntimeError（因为登录失败）
        with pytest.raises(RuntimeError, match="CTP 登录失败"):
            thread.wait_ready(timeout=2.0)
        
        # 清理
        thread.stop(timeout=2.0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
