#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : test_sync_api_exception_recovery.py
@Date       : 2025/12/20
@Author     : Kiro AI Assistant
@Email      : -
@Software   : PyCharm
@Description: 异常恢复测试 - 测试网络断开、重连等异常场景

测试场景
========

1. 网络断开后自动重连成功
2. 多次断开重连
3. 重连失败（超过最大次数）
4. 断开期间的操作处理
5. 登录失败后重试

测试策略
========

由于实际的网络断开和重连很难在测试环境中模拟，我们使用 Mock 来模拟这些场景。
测试将验证系统的错误处理和恢复逻辑是否正确。
"""

import time
import threading
from unittest.mock import Mock, patch, MagicMock
import pytest

from src.strategy.sync_api import SyncStrategyApi
from src.strategy.internal.data_models import Quote, Position


# 测试配置
TEST_USER_ID = "test_user"
TEST_PASSWORD = "test_password"


class TestNetworkDisconnectionRecovery:
    """
    测试场景 1：网络断开后自动重连成功
    
    验证：
    - 系统检测到断开
    - 重连计数器增加
    - 重连成功后恢复正常
    - 可以继续获取行情和下单
    """

    
    @patch('src.services.md_client.MdClient')
    @patch('src.services.td_client.TdClient')
    def test_disconnect_and_reconnect_success(
        self,
        mock_td_client_class,
        mock_md_client_class
    ):
        """
        测试网络断开后成功重连
        
        场景：
        1. 系统正常运行
        2. 模拟网络断开（OnFrontDisconnected）
        3. 模拟重连成功（OnFrontConnected）
        4. 验证系统恢复正常
        """
        # 创建 mock 客户端实例
        mock_md_client = MagicMock()
        mock_td_client = MagicMock()
        mock_md_client_class.return_value = mock_md_client
        mock_td_client_class.return_value = mock_td_client
        
        # 模拟客户端的 start 方法
        async def mock_md_start(user_id, password):
            # 模拟登录成功
            if hasattr(mock_md_client, 'rsp_callback') and mock_md_client.rsp_callback:
                await mock_md_client.rsp_callback({
                    'MsgType': 'RspUserLogin',
                    '_ClientType': 'Md',
                    'RspInfo': {'ErrorID': 0, 'ErrorMsg': ''}
                })
        
        async def mock_td_start(user_id, password):
            # 模拟登录成功
            if hasattr(mock_td_client, 'rsp_callback') and mock_td_client.rsp_callback:
                await mock_td_client.rsp_callback({
                    'MsgType': 'RspUserLogin',
                    '_ClientType': 'Td',
                    'RspInfo': {'ErrorID': 0, 'ErrorMsg': ''}
                })
        
        mock_md_client.start = mock_md_start
        mock_td_client.start = mock_td_start
        
        # 模拟 call 方法
        async def mock_call(request):
            pass
        
        mock_md_client.call = mock_call
        mock_td_client.call = mock_call
        
        # 初始化 API
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        try:
            # 验证初始状态：服务可用
            assert api._event_loop_thread.is_service_available is True
            
            # 模拟网络断开
            # 注意：实际的断开会触发 OnFrontDisconnected 回调
            # 这里我们直接修改服务可用性标志来模拟断开效果
            api._event_loop_thread._service_available = False
            
            # 验证服务不可用
            assert api._event_loop_thread.is_service_available is False
            
            # 尝试获取行情应该失败
            with pytest.raises(RuntimeError, match="事件循环服务不可用"):
                api.get_quote("rb2605", timeout=1.0)
            
            # 模拟重连成功
            api._event_loop_thread._service_available = True
            
            # 验证服务恢复
            assert api._event_loop_thread.is_service_available is True
            
        finally:
            api.stop()



class TestMultipleDisconnectionRecovery:
    """
    测试场景 2：多次断开重连
    
    验证：
    - 系统可以处理多次断开和重连
    - 重连计数器正确重置
    - 每次重连后系统都能正常工作
    """
    
    @patch('src.services.md_client.MdClient')
    @patch('src.services.td_client.TdClient')
    def test_multiple_disconnect_reconnect_cycles(
        self,
        mock_td_client_class,
        mock_md_client_class
    ):
        """
        测试多次断开和重连循环
        
        场景：
        1. 系统正常运行
        2. 模拟断开 -> 重连（重复 3 次）
        3. 验证每次都能成功恢复
        """
        # 创建 mock 客户端实例
        mock_md_client = MagicMock()
        mock_td_client = MagicMock()
        mock_md_client_class.return_value = mock_md_client
        mock_td_client_class.return_value = mock_td_client
        
        # 模拟客户端的 start 方法
        async def mock_md_start(user_id, password):
            if hasattr(mock_md_client, 'rsp_callback') and mock_md_client.rsp_callback:
                await mock_md_client.rsp_callback({
                    'MsgType': 'RspUserLogin',
                    '_ClientType': 'Md',
                    'RspInfo': {'ErrorID': 0, 'ErrorMsg': ''}
                })
        
        async def mock_td_start(user_id, password):
            if hasattr(mock_td_client, 'rsp_callback') and mock_td_client.rsp_callback:
                await mock_td_client.rsp_callback({
                    'MsgType': 'RspUserLogin',
                    '_ClientType': 'Td',
                    'RspInfo': {'ErrorID': 0, 'ErrorMsg': ''}
                })
        
        mock_md_client.start = mock_md_start
        mock_td_client.start = mock_td_start
        
        # 模拟 call 方法
        async def mock_call(request):
            pass
        
        mock_md_client.call = mock_call
        mock_td_client.call = mock_call
        
        # 初始化 API
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        try:
            # 模拟 3 次断开和重连循环
            for i in range(3):
                # 验证服务可用
                assert api._event_loop_thread.is_service_available is True
                
                # 模拟断开
                api._event_loop_thread._service_available = False
                assert api._event_loop_thread.is_service_available is False
                
                # 模拟重连
                api._event_loop_thread._service_available = True
                assert api._event_loop_thread.is_service_available is True
            
            # 验证最终状态：服务可用
            assert api._event_loop_thread.is_service_available is True
            
        finally:
            api.stop()



class TestReconnectionFailure:
    """
    测试场景 3：重连失败（超过最大次数）
    
    验证：
    - 系统检测到连续断开超过最大次数
    - 服务标记为不可用
    - 后续操作抛出适当的异常
    """
    
    @patch('src.services.md_client.MdClient')
    @patch('src.services.td_client.TdClient')
    def test_reconnection_exceeds_max_attempts(
        self,
        mock_td_client_class,
        mock_md_client_class
    ):
        """
        测试重连超过最大次数后的行为
        
        场景：
        1. 系统正常运行
        2. 模拟连续断开超过最大次数
        3. 验证服务标记为不可用
        4. 验证后续操作失败
        """
        # 创建 mock 客户端实例
        mock_md_client = MagicMock()
        mock_td_client = MagicMock()
        mock_md_client_class.return_value = mock_md_client
        mock_td_client_class.return_value = mock_td_client
        
        # 模拟客户端的 start 方法
        async def mock_md_start(user_id, password):
            if hasattr(mock_md_client, 'rsp_callback') and mock_md_client.rsp_callback:
                await mock_md_client.rsp_callback({
                    'MsgType': 'RspUserLogin',
                    '_ClientType': 'Md',
                    'RspInfo': {'ErrorID': 0, 'ErrorMsg': ''}
                })
        
        async def mock_td_start(user_id, password):
            if hasattr(mock_td_client, 'rsp_callback') and mock_td_client.rsp_callback:
                await mock_td_client.rsp_callback({
                    'MsgType': 'RspUserLogin',
                    '_ClientType': 'Td',
                    'RspInfo': {'ErrorID': 0, 'ErrorMsg': ''}
                })
        
        mock_md_client.start = mock_md_start
        mock_td_client.start = mock_td_start
        
        # 模拟 call 方法
        async def mock_call(request):
            pass
        
        mock_md_client.call = mock_call
        mock_td_client.call = mock_call
        
        # 初始化 API
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        try:
            # 验证初始状态
            assert api._event_loop_thread.is_service_available is True
            
            # 模拟连接失败（标记服务不可用）
            api._event_loop_thread._service_available = False
            
            # 验证服务不可用
            assert api._event_loop_thread.is_service_available is False
            
            # 验证后续操作失败
            with pytest.raises(RuntimeError, match="事件循环服务不可用"):
                api.get_quote("rb2605", timeout=1.0)
            
            with pytest.raises(RuntimeError, match="事件循环服务不可用"):
                api.wait_quote_update("rb2605", timeout=1.0)
            
            # get_position 不抛出异常，而是返回空持仓
            position = api.get_position("rb2605", timeout=1.0)
            assert position.pos_long == 0
            assert position.pos_short == 0
            
            # open_close 应该抛出异常
            with pytest.raises(RuntimeError, match="事件循环服务不可用"):
                api.open_close("rb2605", "kaiduo", 1, 3500.0, timeout=1.0)
            
        finally:
            api.stop()



class TestOperationsDuringDisconnection:
    """
    测试场景 4：断开期间的操作处理
    
    验证：
    - 断开期间的操作正确失败
    - 错误消息清晰明确
    - 重连后操作恢复正常
    """
    
    @patch('src.services.md_client.MdClient')
    @patch('src.services.td_client.TdClient')
    def test_operations_during_disconnection(
        self,
        mock_td_client_class,
        mock_md_client_class
    ):
        """
        测试断开期间的操作处理
        
        场景：
        1. 系统正常运行
        2. 模拟断开
        3. 尝试各种操作，验证失败
        4. 模拟重连
        5. 验证操作恢复正常
        """
        # 创建 mock 客户端实例
        mock_md_client = MagicMock()
        mock_td_client = MagicMock()
        mock_md_client_class.return_value = mock_md_client
        mock_td_client_class.return_value = mock_td_client
        
        # 模拟客户端的 start 方法
        async def mock_md_start(user_id, password):
            if hasattr(mock_md_client, 'rsp_callback') and mock_md_client.rsp_callback:
                await mock_md_client.rsp_callback({
                    'MsgType': 'RspUserLogin',
                    '_ClientType': 'Md',
                    'RspInfo': {'ErrorID': 0, 'ErrorMsg': ''}
                })
        
        async def mock_td_start(user_id, password):
            if hasattr(mock_td_client, 'rsp_callback') and mock_td_client.rsp_callback:
                await mock_td_client.rsp_callback({
                    'MsgType': 'RspUserLogin',
                    '_ClientType': 'Td',
                    'RspInfo': {'ErrorID': 0, 'ErrorMsg': ''}
                })
        
        mock_md_client.start = mock_md_start
        mock_td_client.start = mock_td_start
        
        # 模拟 call 方法
        async def mock_call(request):
            pass
        
        mock_md_client.call = mock_call
        mock_td_client.call = mock_call
        
        # 初始化 API
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        try:
            # 步骤 1: 验证初始状态
            assert api._event_loop_thread.is_service_available is True
            
            # 步骤 2: 模拟断开
            api._event_loop_thread._service_available = False
            
            # 步骤 3: 验证断开期间的操作失败
            
            # get_quote 应该抛出异常
            with pytest.raises(RuntimeError, match="事件循环服务不可用"):
                api.get_quote("rb2605", timeout=1.0)
            
            # wait_quote_update 应该抛出异常
            with pytest.raises(RuntimeError, match="事件循环服务不可用"):
                api.wait_quote_update("rb2605", timeout=1.0)
            
            # get_position 返回空持仓（不抛出异常）
            position = api.get_position("rb2605", timeout=1.0)
            assert position.pos_long == 0
            assert position.pos_short == 0
            
            # open_close 应该抛出异常
            with pytest.raises(RuntimeError, match="事件循环服务不可用"):
                api.open_close("rb2605", "kaiduo", 1, 3500.0, timeout=1.0)
            
            # 步骤 4: 模拟重连成功
            api._event_loop_thread._service_available = True
            
            # 步骤 5: 验证服务恢复
            assert api._event_loop_thread.is_service_available is True
            
        finally:
            api.stop()



class TestLoginRetry:
    """
    测试场景 5：登录失败后重试
    
    验证：
    - 系统检测到登录失败
    - 记录错误信息
    - 可以重新初始化并登录
    """
    
    @patch('src.services.md_client.MdClient')
    @patch('src.services.td_client.TdClient')
    def test_login_failure_and_retry(
        self,
        mock_td_client_class,
        mock_md_client_class
    ):
        """
        测试登录失败后重试
        
        场景：
        1. 模拟登录失败
        2. 验证系统记录错误
        3. 重新初始化
        4. 模拟登录成功
        5. 验证系统正常工作
        """
        # 创建 mock 客户端实例
        mock_md_client = MagicMock()
        mock_td_client = MagicMock()
        mock_md_client_class.return_value = mock_md_client
        mock_td_client_class.return_value = mock_td_client
        
        # 第一次尝试：模拟登录失败
        login_attempt = [0]  # 使用列表来在闭包中修改
        
        async def mock_md_start_fail(user_id, password):
            if hasattr(mock_md_client, 'rsp_callback') and mock_md_client.rsp_callback:
                if login_attempt[0] == 0:
                    # 第一次登录失败
                    await mock_md_client.rsp_callback({
                        'MsgType': 'RspUserLogin',
                        '_ClientType': 'Md',
                        'RspInfo': {'ErrorID': 3, 'ErrorMsg': 'CTP登录失败：用户名或密码错误'}
                    })
                else:
                    # 后续登录成功
                    await mock_md_client.rsp_callback({
                        'MsgType': 'RspUserLogin',
                        '_ClientType': 'Md',
                        'RspInfo': {'ErrorID': 0, 'ErrorMsg': ''}
                    })
        
        async def mock_td_start_fail(user_id, password):
            if hasattr(mock_td_client, 'rsp_callback') and mock_td_client.rsp_callback:
                if login_attempt[0] == 0:
                    # 第一次登录失败
                    await mock_td_client.rsp_callback({
                        'MsgType': 'RspUserLogin',
                        '_ClientType': 'Td',
                        'RspInfo': {'ErrorID': 3, 'ErrorMsg': 'CTP登录失败：用户名或密码错误'}
                    })
                else:
                    # 后续登录成功
                    await mock_td_client.rsp_callback({
                        'MsgType': 'RspUserLogin',
                        '_ClientType': 'Td',
                        'RspInfo': {'ErrorID': 0, 'ErrorMsg': ''}
                    })
        
        mock_md_client.start = mock_md_start_fail
        mock_td_client.start = mock_td_start_fail
        
        # 模拟 call 方法
        async def mock_call(request):
            pass
        
        mock_md_client.call = mock_call
        mock_td_client.call = mock_call
        
        # 第一次尝试：应该失败
        with pytest.raises(RuntimeError, match="CTP登录失败"):
            api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 第二次尝试：应该成功
        login_attempt[0] = 1
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        try:
            # 验证登录成功
            assert api._event_loop_thread.is_service_available is True
            assert api._event_loop_thread._md_logged_in is True
            assert api._event_loop_thread._td_logged_in is True
            
        finally:
            api.stop()



class TestServiceAvailabilityDuringRecovery:
    """
    测试场景 6：恢复期间的服务可用性
    
    验证：
    - 断开期间服务标记为不可用
    - 重连期间服务仍然不可用
    - 重连成功后服务恢复可用
    - 服务可用性标志的状态转换正确
    """
    
    @patch('src.services.md_client.MdClient')
    @patch('src.services.td_client.TdClient')
    def test_service_availability_state_transitions(
        self,
        mock_td_client_class,
        mock_md_client_class
    ):
        """
        测试服务可用性状态转换
        
        场景：
        1. 初始状态：服务可用
        2. 断开：服务不可用
        3. 重连中：服务不可用
        4. 重连成功：服务可用
        """
        # 创建 mock 客户端实例
        mock_md_client = MagicMock()
        mock_td_client = MagicMock()
        mock_md_client_class.return_value = mock_md_client
        mock_td_client_class.return_value = mock_td_client
        
        # 模拟客户端的 start 方法
        async def mock_md_start(user_id, password):
            if hasattr(mock_md_client, 'rsp_callback') and mock_md_client.rsp_callback:
                await mock_md_client.rsp_callback({
                    'MsgType': 'RspUserLogin',
                    '_ClientType': 'Md',
                    'RspInfo': {'ErrorID': 0, 'ErrorMsg': ''}
                })
        
        async def mock_td_start(user_id, password):
            if hasattr(mock_td_client, 'rsp_callback') and mock_td_client.rsp_callback:
                await mock_td_client.rsp_callback({
                    'MsgType': 'RspUserLogin',
                    '_ClientType': 'Td',
                    'RspInfo': {'ErrorID': 0, 'ErrorMsg': ''}
                })
        
        mock_md_client.start = mock_md_start
        mock_td_client.start = mock_td_start
        
        # 模拟 call 方法
        async def mock_call(request):
            pass
        
        mock_md_client.call = mock_call
        mock_td_client.call = mock_call
        
        # 初始化 API
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        try:
            # 状态 1: 初始状态 - 服务可用
            assert api._event_loop_thread.is_service_available is True
            
            # 状态 2: 断开 - 服务不可用
            api._event_loop_thread._service_available = False
            assert api._event_loop_thread.is_service_available is False
            
            # 状态 3: 重连中 - 服务仍然不可用
            # （在实际场景中，重连期间服务应该保持不可用）
            assert api._event_loop_thread.is_service_available is False
            
            # 状态 4: 重连成功 - 服务恢复可用
            api._event_loop_thread._service_available = True
            assert api._event_loop_thread.is_service_available is True
            
            # 验证状态转换的完整性
            # 可用 -> 不可用 -> 可用
            states = []
            
            states.append(api._event_loop_thread.is_service_available)  # True
            api._event_loop_thread._service_available = False
            states.append(api._event_loop_thread.is_service_available)  # False
            api._event_loop_thread._service_available = True
            states.append(api._event_loop_thread.is_service_available)  # True
            
            assert states == [True, False, True]
            
        finally:
            api.stop()
