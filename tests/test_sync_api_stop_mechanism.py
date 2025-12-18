#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : test_sync_api_stop_mechanism.py
@Date       : 2025/12/17
@Author     : Kiro AI Assistant
@Email      : -
@Software   : PyCharm
@Description: 测试 SyncStrategyApi.stop() 方法的单元测试
              测试事件循环停止、线程池关闭、资源释放和停止超时处理
              Requirements: 9.1, 9.3, 9.4, 9.5
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from src.strategy.sync_api import SyncStrategyApi
# Test credentials
TEST_USER_ID = "test_user"
TEST_PASSWORD = "test_pass"


class TestStopMechanism:
    """测试 SyncStrategyApi 的停止机制"""
    
    def test_stop_with_no_strategies(self):
        """
        测试没有运行策略时调用 stop()
        
        验证：
        - stop() 方法应该正常返回
        - 事件循环的 stop() 方法被调用
        - 策略注册表为空
        - 不应该抛出异常
        
        Requirements: 9.1, 9.3
        """
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # Mock 事件循环线程
        mock_event_loop = Mock()
        mock_event_loop.loop = Mock()
        mock_event_loop.is_service_available = True
        mock_event_loop.stop = Mock()
        api._event_loop_thread = mock_event_loop
        
        # 调用 stop()（没有运行中的策略）
        api.stop(timeout=1.0)
        
        # 验证事件循环的 stop() 被调用
        mock_event_loop.stop.assert_called_once_with(timeout=1.0)
        
        # 验证策略注册表为空
        assert len(api.get_running_strategies()) == 0, \
            "stop() 后策略注册表应该为空"
    
    def test_stop_waits_for_strategies(self):
        """
        测试 stop() 等待策略线程完成
        
        验证：
        - 启动多个短时间运行的策略
        - 调用 stop() 应该等待所有策略完成
        - 所有策略线程都已停止
        - 事件循环的 stop() 被调用
        
        Requirements: 9.1, 9.2, 9.3
        """
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # Mock 事件循环线程
        mock_event_loop = Mock()
        mock_event_loop.loop = Mock()
        mock_event_loop.is_service_available = True
        mock_event_loop.stop = Mock()
        api._event_loop_thread = mock_event_loop
        
        # 记录策略执行状态
        strategy_completed = []
        lock = threading.Lock()
        
        # 定义多个不同名称的测试策略函数
        def test_strategy_1(duration: float):
            """测试策略函数 1"""
            time.sleep(duration)
            with lock:
                strategy_completed.append(1)
        
        def test_strategy_2(duration: float):
            """测试策略函数 2"""
            time.sleep(duration)
            with lock:
                strategy_completed.append(2)
        
        def test_strategy_3(duration: float):
            """测试策略函数 3"""
            time.sleep(duration)
            with lock:
                strategy_completed.append(3)
        
        # 启动多个策略
        strategy_duration = 0.5  # 增加策略运行时间
        strategy_funcs = [test_strategy_1, test_strategy_2, test_strategy_3]
        strategy_threads = []
        
        for func in strategy_funcs:
            thread = api.run_strategy(func, duration=strategy_duration)
            strategy_threads.append(thread)
        
        # 等待策略启动（但不要等太久，确保策略还在运行）
        time.sleep(0.05)
        
        # 验证策略已启动
        num_strategies = len(strategy_funcs)
        assert len(api.get_running_strategies()) == num_strategies, \
            f"应该有 {num_strategies} 个策略在运行"
        
        # 调用 stop()（此时策略应该还在运行）
        start_time = time.time()
        api.stop(timeout=2.0)
        stop_duration = time.time() - start_time
        
        # 验证所有策略都已完成
        with lock:
            assert len(strategy_completed) == num_strategies, \
                f"应该有 {num_strategies} 个策略完成"
        
        # 验证所有策略线程都已停止
        for thread in strategy_threads:
            assert not thread.is_alive(), \
                f"策略线程 {thread.name} 应该已停止"
        
        # 验证 stop() 等待了策略完成
        # 由于我们在策略启动后 0.05 秒调用 stop()，
        # stop() 应该等待剩余的时间（约 0.45 秒）
        expected_wait_time = strategy_duration - 0.05
        assert stop_duration >= expected_wait_time * 0.7, \
            f"stop() 应该等待策略完成，实际等待 {stop_duration:.3f}s，期望至少 {expected_wait_time * 0.7:.3f}s"
        
        # 验证事件循环的 stop() 被调用
        mock_event_loop.stop.assert_called_once()
        
        # 验证策略注册表已清空
        assert len(api.get_running_strategies()) == 0, \
            "stop() 后策略注册表应该为空"
    
    def test_stop_timeout_with_long_running_strategy(self):
        """
        测试长时间运行策略的超时处理
        
        验证：
        - 启动一个长时间运行的策略
        - 调用 stop() 并设置较短的超时
        - stop() 应该在超时后返回
        - 应该记录警告日志
        
        Requirements: 9.2, 9.5
        """
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # Mock 事件循环线程
        mock_event_loop = Mock()
        mock_event_loop.loop = Mock()
        mock_event_loop.is_service_available = True
        mock_event_loop.stop = Mock()
        api._event_loop_thread = mock_event_loop
        
        # 定义一个长时间运行的策略
        def long_running_strategy():
            time.sleep(5.0)  # 运行 5 秒
        
        # 启动策略
        thread = api.run_strategy(long_running_strategy)
        
        # 等待策略启动
        time.sleep(0.1)
        
        # 验证策略正在运行
        assert thread.is_alive(), "策略线程应该正在运行"
        
        # 调用 stop()，设置较短的超时时间
        start_time = time.time()
        api.stop(timeout=0.5)
        stop_duration = time.time() - start_time
        
        # 验证 stop() 在超时后返回
        assert 0.4 <= stop_duration <= 1.5, \
            f"stop() 应该在超时后返回，实际等待 {stop_duration:.3f}s"
        
        # 验证事件循环的 stop() 被调用
        mock_event_loop.stop.assert_called_once()
        
        # 清理：等待策略线程结束（避免影响其他测试）
        thread.join(timeout=5.0)
    
    def test_stop_cleans_up_resources(self):
        """
        测试资源清理
        
        验证：
        - 启动策略
        - 调用 stop()
        - 策略注册表被清空
        - 事件循环被停止
        
        Requirements: 9.3, 9.4
        """
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # Mock 事件循环线程
        mock_event_loop = Mock()
        mock_event_loop.loop = Mock()
        mock_event_loop.is_service_available = True
        mock_event_loop.stop = Mock()
        api._event_loop_thread = mock_event_loop
        
        # 定义快速完成的策略
        def quick_strategy():
            time.sleep(0.1)
        
        # 启动策略
        thread = api.run_strategy(quick_strategy)
        
        # 等待策略启动
        time.sleep(0.05)
        
        # 验证策略在注册表中
        assert len(api.get_running_strategies()) == 1, \
            "应该有 1 个策略在运行"
        
        # 调用 stop()
        api.stop(timeout=2.0)
        
        # 验证策略注册表已清空
        assert len(api.get_running_strategies()) == 0, \
            "stop() 后策略注册表应该为空"
        
        # 验证事件循环的 stop() 被调用
        mock_event_loop.stop.assert_called_once_with(timeout=2.0)
        
        # 验证策略线程已停止
        assert not thread.is_alive(), \
            "策略线程应该已停止"
    
    def test_stop_handles_event_loop_stop_error(self):
        """
        测试事件循环停止失败的处理
        
        验证：
        - Mock 事件循环的 stop() 方法抛出异常
        - 调用 stop()
        - 异常被捕获并记录
        - stop() 方法正常返回
        
        Requirements: 9.3, 9.4
        """
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # Mock 事件循环线程，stop() 方法抛出异常
        mock_event_loop = Mock()
        mock_event_loop.loop = Mock()
        mock_event_loop.is_service_available = True
        mock_event_loop.stop = Mock(side_effect=Exception("模拟停止失败"))
        api._event_loop_thread = mock_event_loop
        
        # 调用 stop() 应该不抛出异常（异常被内部捕获）
        api.stop(timeout=1.0)
        
        # 验证事件循环的 stop() 被调用
        mock_event_loop.stop.assert_called_once_with(timeout=1.0)
    
    def test_stop_multiple_times(self):
        """
        测试多次调用 stop()
        
        验证：
        - 第一次调用 stop()
        - 再次调用 stop()
        - 不会出错
        
        Requirements: 9.1, 9.3
        """
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # Mock 事件循环线程
        mock_event_loop = Mock()
        mock_event_loop.loop = Mock()
        mock_event_loop.is_service_available = True
        mock_event_loop.stop = Mock()
        api._event_loop_thread = mock_event_loop
        
        # 第一次调用 stop()
        api.stop(timeout=1.0)
        
        # 验证事件循环的 stop() 被调用
        assert mock_event_loop.stop.call_count == 1
        
        # 再次调用 stop()（应该不会出错）
        api.stop(timeout=1.0)
        
        # 验证事件循环的 stop() 被再次调用
        assert mock_event_loop.stop.call_count == 2
    
    def test_stop_with_already_completed_strategies(self):
        """
        测试策略已完成时调用 stop()
        
        验证：
        - 启动快速完成的策略
        - 等待策略完成
        - 调用 stop()
        - stop() 应该几乎立即返回
        
        Requirements: 9.2, 9.3
        """
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # Mock 事件循环线程
        mock_event_loop = Mock()
        mock_event_loop.loop = Mock()
        mock_event_loop.is_service_available = True
        mock_event_loop.stop = Mock()
        api._event_loop_thread = mock_event_loop
        
        # 定义快速完成的策略
        def quick_strategy():
            time.sleep(0.05)
        
        # 启动策略
        thread = api.run_strategy(quick_strategy)
        
        # 等待策略完成
        thread.join(timeout=1.0)
        assert not thread.is_alive(), "策略应该已完成"
        
        # 调用 stop()
        start_time = time.time()
        api.stop(timeout=2.0)
        stop_duration = time.time() - start_time
        
        # 验证 stop() 几乎立即返回（因为策略已完成）
        assert stop_duration < 0.5, \
            f"stop() 应该快速返回，实际等待 {stop_duration:.3f}s"
        
        # 验证事件循环的 stop() 被调用
        mock_event_loop.stop.assert_called_once()
    
    def test_stop_with_no_event_loop(self):
        """
        测试事件循环未初始化时调用 stop()
        
        验证：
        - 事件循环未初始化
        - 调用 stop()
        - 不应该抛出异常
        
        Requirements: 9.1, 9.3
        """
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 不设置事件循环线程（保持为 None）
        assert api._event_loop_thread is None
        
        # 调用 stop() 应该不抛出异常
        api.stop(timeout=1.0)
        
        # 验证策略注册表为空
        assert len(api.get_running_strategies()) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
