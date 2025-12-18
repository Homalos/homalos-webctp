#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : test_sync_api_run_strategy.py
@Date       : 2025/12/16
@Author     : Kiro AI Assistant
@Email      : -
@Software   : PyCharm
@Description: 测试 SyncStrategyApi.run_strategy() 方法 - Property 11 & 12
"""

import pytest
import time
import threading
from hypothesis import given, settings, strategies as st
from src.strategy.sync_api import SyncStrategyApi
# Test credentials
TEST_USER_ID = "test_user"
TEST_PASSWORD = "test_pass"


class TestRunStrategy:
    """测试 run_strategy() 方法的基本功能"""
    
    def test_run_strategy_returns_thread(self):
        """测试 run_strategy 返回线程对象"""
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 定义简单的策略函数
        def simple_strategy():
            time.sleep(0.1)
        
        # 运行策略
        thread = api.run_strategy(simple_strategy)
        
        # 验证返回的是线程对象
        assert isinstance(thread, threading.Thread), "run_strategy 应该返回 threading.Thread 对象"
        assert thread.is_alive(), "策略线程应该处于运行状态"
        
        # 等待线程结束
        thread.join(timeout=1.0)
        assert not thread.is_alive(), "策略线程应该已经结束"
    
    def test_run_strategy_with_arguments(self):
        """测试 run_strategy 传递参数"""
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 用于验证参数传递的共享变量
        result = {'value': None}
        
        def strategy_with_args(x, y, z=0):
            result['value'] = x + y + z
        
        # 运行策略并传递参数
        thread = api.run_strategy(strategy_with_args, 10, 20, z=5)
        
        # 等待策略执行完成
        thread.join(timeout=1.0)
        
        # 验证参数正确传递
        assert result['value'] == 35, "策略函数应该正确接收参数"
    
    def test_run_strategy_adds_to_registry(self):
        """测试策略被添加到注册表"""
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        def test_strategy():
            time.sleep(0.2)
        
        # 运行策略
        thread = api.run_strategy(test_strategy)
        
        # 验证策略在注册表中
        strategies = api.get_running_strategies()
        assert 'test_strategy' in strategies, "策略应该在注册表中"
        assert strategies['test_strategy'] is thread, "注册表中的线程对象应该与返回的一致"
        
        # 等待策略结束
        thread.join(timeout=1.0)
        
        # 策略结束后应该从注册表移除
        strategies = api.get_running_strategies()
        assert 'test_strategy' not in strategies, "策略结束后应该从注册表移除"
    
    def test_run_strategy_exception_handling(self):
        """测试策略异常被捕获"""
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        def failing_strategy():
            raise ValueError("测试异常")
        
        # 运行会抛出异常的策略
        thread = api.run_strategy(failing_strategy)
        
        # 等待策略执行完成
        thread.join(timeout=1.0)
        
        # 验证线程已结束（异常被捕获，不会导致程序崩溃）
        assert not thread.is_alive(), "即使策略抛出异常，线程也应该正常结束"
        
        # 验证策略已从注册表移除
        strategies = api.get_running_strategies()
        assert 'failing_strategy' not in strategies, "异常策略应该从注册表移除"
    
    def test_run_strategy_thread_name(self):
        """测试策略线程名称"""
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        def my_custom_strategy():
            time.sleep(0.1)
        
        # 运行策略
        thread = api.run_strategy(my_custom_strategy)
        
        # 验证线程名称包含策略函数名
        assert 'my_custom_strategy' in thread.name, \
            f"线程名称应该包含策略函数名，实际名称: {thread.name}"
        
        # 清理
        thread.join(timeout=1.0)


class TestPropertyStrategyThreadIndependence:
    """属性测试：策略线程独立运行"""
    
    # Feature: sync-strategy-api, Property 11: 策略线程独立运行
    @given(
        num_strategies=st.integers(min_value=2, max_value=5),
        sleep_time=st.floats(min_value=0.05, max_value=0.2)
    )
    @settings(max_examples=100, deadline=5000)
    def test_property_multiple_strategies_run_independently(
        self, 
        num_strategies: int, 
        sleep_time: float
    ):
        """
        **Feature: sync-strategy-api, Property 11: 策略线程独立运行**
        
        Property 11: 策略线程独立运行
        
        For any 策略函数，调用 run_strategy(strategy_func, *args, **kwargs) 
        应该在独立线程中启动该策略，且返回有效的线程对象。
        多个策略应该能够并发运行互不干扰。
        
        **Validates: Requirements 4.1, 4.2, 4.4**
        
        测试策略：
        1. 生成随机数量的策略（2-5个）
        2. 每个策略在独立线程中运行
        3. 验证所有策略的线程 ID 不同
        4. 验证所有策略都能正常执行完成
        5. 验证策略之间互不干扰
        """
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 用于记录策略执行情况的共享数据结构
        execution_records = {}
        lock = threading.Lock()
        
        def create_strategy(strategy_id: int):
            """创建一个策略函数"""
            def strategy():
                # 记录线程 ID
                thread_id = threading.current_thread().ident
                
                # 模拟策略执行
                time.sleep(sleep_time)
                
                # 记录执行结果
                with lock:
                    execution_records[strategy_id] = {
                        'thread_id': thread_id,
                        'completed': True,
                        'thread_name': threading.current_thread().name
                    }
            
            # 设置函数名称（用于注册表）
            strategy.__name__ = f'strategy_{strategy_id}'
            return strategy
        
        # 启动多个策略
        threads = []
        for i in range(num_strategies):
            strategy_func = create_strategy(i)
            thread = api.run_strategy(strategy_func)
            threads.append(thread)
        
        # 验证1：所有返回的对象都是线程
        for thread in threads:
            assert isinstance(thread, threading.Thread), \
                "run_strategy 应该返回 threading.Thread 对象"
        
        # 验证2：所有线程都在运行
        for thread in threads:
            assert thread.is_alive(), "策略线程应该处于运行状态"
        
        # 验证3：所有线程的 ID 不同（独立线程）
        thread_ids = [thread.ident for thread in threads]
        assert len(thread_ids) == len(set(thread_ids)), \
            "每个策略应该在独立的线程中运行（线程 ID 应该不同）"
        
        # 验证4：所有策略都在注册表中
        strategies = api.get_running_strategies()
        for i in range(num_strategies):
            strategy_name = f'strategy_{i}'
            assert strategy_name in strategies, \
                f"策略 {strategy_name} 应该在注册表中"
        
        # 等待所有策略执行完成
        for thread in threads:
            thread.join(timeout=sleep_time * 2 + 1.0)
        
        # 验证5：所有策略都执行完成
        assert len(execution_records) == num_strategies, \
            f"应该有 {num_strategies} 个策略执行完成，实际: {len(execution_records)}"
        
        # 验证6：所有策略都标记为完成
        for i in range(num_strategies):
            assert i in execution_records, f"策略 {i} 应该有执行记录"
            assert execution_records[i]['completed'], f"策略 {i} 应该标记为完成"
        
        # 验证7：策略在不同的线程中执行
        recorded_thread_ids = [record['thread_id'] for record in execution_records.values()]
        assert len(recorded_thread_ids) == len(set(recorded_thread_ids)), \
            "每个策略应该在不同的线程中执行"
        
        # 验证8：所有线程都已结束
        for thread in threads:
            assert not thread.is_alive(), "策略执行完成后线程应该结束"
        
        # 验证9：策略已从注册表移除
        strategies = api.get_running_strategies()
        for i in range(num_strategies):
            strategy_name = f'strategy_{i}'
            assert strategy_name not in strategies, \
                f"策略 {strategy_name} 执行完成后应该从注册表移除"
    
    @given(
        num_strategies=st.integers(min_value=2, max_value=4)
    )
    @settings(max_examples=50, deadline=5000)
    def test_property_strategy_isolation(self, num_strategies: int):
        """
        **Feature: sync-strategy-api, Property 11: 策略线程独立运行（隔离性测试）**
        
        验证策略之间的隔离性：一个策略的异常不应该影响其他策略。
        
        **Validates: Requirements 4.2, 4.3**
        """
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 用于记录策略执行情况
        execution_status = {}
        lock = threading.Lock()
        
        def create_normal_strategy(strategy_id: int):
            """创建正常的策略"""
            def strategy():
                time.sleep(0.1)
                with lock:
                    execution_status[strategy_id] = 'completed'
            strategy.__name__ = f'normal_strategy_{strategy_id}'
            return strategy
        
        def create_failing_strategy(strategy_id: int):
            """创建会抛出异常的策略"""
            def strategy():
                time.sleep(0.05)
                with lock:
                    execution_status[strategy_id] = 'started'
                raise RuntimeError(f"策略 {strategy_id} 故意抛出异常")
            strategy.__name__ = f'failing_strategy_{strategy_id}'
            return strategy
        
        # 启动多个策略，其中一个会失败
        threads = []
        
        # 第一个策略会失败
        failing_strategy = create_failing_strategy(0)
        thread = api.run_strategy(failing_strategy)
        threads.append(thread)
        
        # 其他策略正常运行
        for i in range(1, num_strategies):
            normal_strategy = create_normal_strategy(i)
            thread = api.run_strategy(normal_strategy)
            threads.append(thread)
        
        # 等待所有策略执行完成
        for thread in threads:
            thread.join(timeout=1.0)
        
        # 验证：失败的策略被记录
        assert 0 in execution_status, "失败的策略应该有执行记录"
        assert execution_status[0] == 'started', "失败的策略应该标记为已启动"
        
        # 验证：其他策略正常完成（不受失败策略影响）
        for i in range(1, num_strategies):
            assert i in execution_status, f"策略 {i} 应该有执行记录"
            assert execution_status[i] == 'completed', \
                f"策略 {i} 应该正常完成（不受失败策略影响）"
        
        # 验证：所有线程都已结束
        for thread in threads:
            assert not thread.is_alive(), "所有线程都应该结束"
    
    def test_property_strategy_with_shared_api(self):
        """
        **Feature: sync-strategy-api, Property 11: 策略线程独立运行（共享 API 测试）**
        
        验证多个策略可以共享同一个 SyncStrategyApi 实例。
        
        **Validates: Requirements 4.1, 4.4**
        """
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 用于记录策略访问 API 的情况
        api_access_records = []
        lock = threading.Lock()
        
        def create_api_using_strategy(strategy_id: int):
            """创建使用 API 的策略"""
            def strategy():
                # 模拟访问 API（这里只是记录，不实际调用）
                time.sleep(0.05)
                with lock:
                    api_access_records.append({
                        'strategy_id': strategy_id,
                        'thread_id': threading.current_thread().ident,
                        'api_instance': id(api)
                    })
            strategy.__name__ = f'api_strategy_{strategy_id}'
            return strategy
        
        # 启动多个策略
        num_strategies = 3
        threads = []
        for i in range(num_strategies):
            strategy = create_api_using_strategy(i)
            thread = api.run_strategy(strategy)
            threads.append(thread)
        
        # 等待所有策略完成
        for thread in threads:
            thread.join(timeout=1.0)
        
        # 验证：所有策略都访问了 API
        assert len(api_access_records) == num_strategies, \
            f"应该有 {num_strategies} 个策略访问了 API"
        
        # 验证：所有策略使用的是同一个 API 实例
        api_instances = [record['api_instance'] for record in api_access_records]
        assert len(set(api_instances)) == 1, \
            "所有策略应该使用同一个 API 实例"
        
        # 验证：策略在不同的线程中运行
        thread_ids = [record['thread_id'] for record in api_access_records]
        assert len(thread_ids) == len(set(thread_ids)), \
            "每个策略应该在不同的线程中运行"


class TestPropertyStrategyExceptionIsolation:
    """属性测试：策略异常隔离"""
    
    # Feature: sync-strategy-api, Property 12: 策略异常隔离
    @given(
        num_normal_strategies=st.integers(min_value=2, max_value=4),
        num_failing_strategies=st.integers(min_value=1, max_value=3),
        exception_type=st.sampled_from([
            ValueError,
            RuntimeError,
            TypeError,
            KeyError,
            IndexError,
            ZeroDivisionError
        ])
    )
    @settings(max_examples=100, deadline=5000)
    def test_property_exception_isolation(
        self,
        num_normal_strategies: int,
        num_failing_strategies: int,
        exception_type: type
    ):
        """
        **Feature: sync-strategy-api, Property 12: 策略异常隔离**
        
        Property 12: 策略异常隔离
        
        For any 抛出异常的策略函数，系统应该捕获异常并记录日志，
        而不影响其他正在运行的策略。
        
        **Validates: Requirements 4.3, 7.4**
        
        测试策略：
        1. 生成随机数量的正常策略和失败策略
        2. 失败策略抛出随机类型的异常
        3. 验证失败策略的异常被捕获，不会导致程序崩溃
        4. 验证正常策略不受失败策略影响，继续正常运行
        5. 验证所有策略线程都能正常结束
        6. 验证失败策略从注册表中正确移除
        """
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 用于记录策略执行情况
        execution_records = {}
        lock = threading.Lock()
        
        def create_normal_strategy(strategy_id: int):
            """创建正常的策略函数"""
            def strategy():
                # 模拟策略执行
                time.sleep(0.1)
                
                # 记录执行结果
                with lock:
                    execution_records[f'normal_{strategy_id}'] = {
                        'type': 'normal',
                        'completed': True,
                        'thread_id': threading.current_thread().ident
                    }
            
            strategy.__name__ = f'normal_strategy_{strategy_id}'
            return strategy
        
        def create_failing_strategy(strategy_id: int, exc_type: type):
            """创建会抛出异常的策略函数"""
            def strategy():
                # 先记录启动
                with lock:
                    execution_records[f'failing_{strategy_id}'] = {
                        'type': 'failing',
                        'started': True,
                        'thread_id': threading.current_thread().ident
                    }
                
                # 模拟一些执行
                time.sleep(0.05)
                
                # 抛出异常
                raise exc_type(f"策略 {strategy_id} 故意抛出的异常")
            
            strategy.__name__ = f'failing_strategy_{strategy_id}'
            return strategy
        
        # 启动所有策略（混合正常和失败的）
        all_threads = []
        
        # 启动失败策略
        for i in range(num_failing_strategies):
            failing_strategy = create_failing_strategy(i, exception_type)
            thread = api.run_strategy(failing_strategy)
            all_threads.append(('failing', i, thread))
        
        # 启动正常策略
        for i in range(num_normal_strategies):
            normal_strategy = create_normal_strategy(i)
            thread = api.run_strategy(normal_strategy)
            all_threads.append(('normal', i, thread))
        
        # 验证1：所有线程都已启动
        for strategy_type, strategy_id, thread in all_threads:
            assert isinstance(thread, threading.Thread), \
                f"{strategy_type}_{strategy_id} 应该返回线程对象"
            assert thread.is_alive(), \
                f"{strategy_type}_{strategy_id} 的线程应该处于运行状态"
        
        # 验证2：所有策略都在注册表中
        strategies = api.get_running_strategies()
        expected_count = num_normal_strategies + num_failing_strategies
        assert len(strategies) == expected_count, \
            f"注册表中应该有 {expected_count} 个策略，实际: {len(strategies)}"
        
        # 等待所有策略执行完成
        for strategy_type, strategy_id, thread in all_threads:
            thread.join(timeout=2.0)
        
        # 验证3：所有线程都已结束（包括抛出异常的线程）
        for strategy_type, strategy_id, thread in all_threads:
            assert not thread.is_alive(), \
                f"{strategy_type}_{strategy_id} 的线程应该已经结束"
        
        # 验证4：失败策略有启动记录
        for i in range(num_failing_strategies):
            key = f'failing_{i}'
            assert key in execution_records, \
                f"失败策略 {i} 应该有执行记录"
            assert execution_records[key]['started'], \
                f"失败策略 {i} 应该标记为已启动"
        
        # 验证5：正常策略都完成了（不受失败策略影响）
        for i in range(num_normal_strategies):
            key = f'normal_{i}'
            assert key in execution_records, \
                f"正常策略 {i} 应该有执行记录"
            assert execution_records[key]['completed'], \
                f"正常策略 {i} 应该标记为完成（不受失败策略影响）"
        
        # 验证6：所有策略都从注册表中移除
        strategies = api.get_running_strategies()
        assert len(strategies) == 0, \
            f"所有策略执行完成后，注册表应该为空，实际: {len(strategies)}"
        
        # 验证7：程序没有崩溃（能执行到这里就说明异常被正确隔离）
        # 这个验证是隐式的，如果异常没有被隔离，测试会在上面的步骤中失败
    
    @given(
        num_strategies=st.integers(min_value=3, max_value=5)
    )
    @settings(max_examples=50, deadline=5000)
    def test_property_multiple_exceptions_isolation(
        self,
        num_strategies: int
    ):
        """
        **Feature: sync-strategy-api, Property 12: 策略异常隔离（多异常测试）**
        
        验证多个策略同时抛出不同类型的异常时，系统能够正确隔离。
        
        **Validates: Requirements 4.3, 7.4**
        """
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 定义多种异常类型
        exception_types = [
            ValueError,
            RuntimeError,
            TypeError,
            KeyError,
            ZeroDivisionError
        ]
        
        # 用于记录策略执行情况
        execution_status = {}
        lock = threading.Lock()
        
        def create_strategy_with_exception(strategy_id: int, exc_type: type):
            """创建会抛出特定异常的策略"""
            def strategy():
                with lock:
                    execution_status[strategy_id] = {
                        'started': True,
                        'exception_type': exc_type.__name__
                    }
                
                time.sleep(0.05)
                raise exc_type(f"策略 {strategy_id} 抛出 {exc_type.__name__}")
            
            strategy.__name__ = f'exception_strategy_{strategy_id}'
            return strategy
        
        # 启动多个策略，每个抛出不同类型的异常
        threads = []
        for i in range(num_strategies):
            exc_type = exception_types[i % len(exception_types)]
            strategy = create_strategy_with_exception(i, exc_type)
            thread = api.run_strategy(strategy)
            threads.append((i, thread))
        
        # 等待所有策略执行完成
        for strategy_id, thread in threads:
            thread.join(timeout=1.0)
        
        # 验证1：所有策略都启动了
        assert len(execution_status) == num_strategies, \
            f"应该有 {num_strategies} 个策略启动，实际: {len(execution_status)}"
        
        # 验证2：所有线程都已结束
        for strategy_id, thread in threads:
            assert not thread.is_alive(), \
                f"策略 {strategy_id} 的线程应该已经结束"
        
        # 验证3：所有策略都从注册表中移除
        strategies = api.get_running_strategies()
        assert len(strategies) == 0, \
            "所有策略执行完成后，注册表应该为空"
        
        # 验证4：程序没有崩溃（能执行到这里就说明所有异常都被正确隔离）
    
    def test_property_exception_does_not_propagate(self):
        """
        **Feature: sync-strategy-api, Property 12: 策略异常隔离（异常不传播测试）**
        
        验证策略中的异常不会传播到主线程或其他策略。
        
        **Validates: Requirements 4.3, 7.4**
        """
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 标记主线程是否收到异常
        main_thread_exception = {'occurred': False}
        
        def failing_strategy():
            """会抛出异常的策略"""
            time.sleep(0.05)
            raise RuntimeError("这个异常应该被隔离")
        
        def normal_strategy():
            """正常的策略"""
            time.sleep(0.1)
        
        # 启动失败策略
        failing_thread = api.run_strategy(failing_strategy)
        
        # 启动正常策略
        normal_thread = api.run_strategy(normal_strategy)
        
        # 在主线程中等待（如果异常传播，这里会抛出异常）
        try:
            failing_thread.join(timeout=1.0)
            normal_thread.join(timeout=1.0)
        except Exception as e:
            # 如果捕获到异常，说明异常传播了（这是不应该发生的）
            main_thread_exception['occurred'] = True
            main_thread_exception['exception'] = e
        
        # 验证：主线程没有收到异常
        assert not main_thread_exception['occurred'], \
            f"策略异常不应该传播到主线程，但收到了: {main_thread_exception.get('exception')}"
        
        # 验证：两个线程都已结束
        assert not failing_thread.is_alive(), "失败策略的线程应该已经结束"
        assert not normal_thread.is_alive(), "正常策略的线程应该已经结束"
        
        # 验证：注册表为空
        strategies = api.get_running_strategies()
        assert len(strategies) == 0, "所有策略执行完成后，注册表应该为空"


class TestPropertyStrategyRegistryMaintenance:
    """属性测试：策略注册表维护"""
    
    # Feature: sync-strategy-api, Property 13: 策略注册表维护
    @given(
        num_strategies=st.integers(min_value=1, max_value=5),
        sleep_time=st.floats(min_value=0.05, max_value=0.3)
    )
    @settings(max_examples=100, deadline=5000)
    def test_property_registry_maintenance(
        self,
        num_strategies: int,
        sleep_time: float
    ):
        """
        **Feature: sync-strategy-api, Property 13: 策略注册表维护**
        
        Property 13: 策略注册表维护
        
        For any 运行中的策略，系统应该在内部注册表中维护该策略的信息，
        包括线程对象和运行状态。
        
        **Validates: Requirements 4.5**
        
        测试策略：
        1. 生成随机数量的策略（1-5个）
        2. 启动所有策略
        3. 验证所有策略都在注册表中
        4. 验证注册表中的线程对象与返回的一致
        5. 验证注册表中的线程都处于运行状态
        6. 等待策略完成
        7. 验证策略完成后从注册表中移除
        8. 验证注册表最终为空
        """
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 用于记录策略执行情况
        execution_records = {}
        lock = threading.Lock()
        
        def create_strategy(strategy_id: int):
            """创建一个策略函数"""
            def strategy():
                # 记录执行开始
                with lock:
                    execution_records[strategy_id] = {
                        'started': True,
                        'thread_id': threading.current_thread().ident
                    }
                
                # 模拟策略执行
                time.sleep(sleep_time)
                
                # 记录执行完成
                with lock:
                    execution_records[strategy_id]['completed'] = True
            
            # 设置函数名称（用于注册表）
            strategy.__name__ = f'test_strategy_{strategy_id}'
            return strategy
        
        # 启动所有策略
        threads = []
        strategy_names = []
        
        for i in range(num_strategies):
            strategy_func = create_strategy(i)
            strategy_name = strategy_func.__name__
            strategy_names.append(strategy_name)
            
            thread = api.run_strategy(strategy_func)
            threads.append((strategy_name, thread))
        
        # 验证1：所有策略都在注册表中
        strategies = api.get_running_strategies()
        assert len(strategies) == num_strategies, \
            f"注册表中应该有 {num_strategies} 个策略，实际: {len(strategies)}"
        
        for strategy_name in strategy_names:
            assert strategy_name in strategies, \
                f"策略 {strategy_name} 应该在注册表中"
        
        # 验证2：注册表中的线程对象与返回的一致
        for strategy_name, thread in threads:
            registry_thread = strategies.get(strategy_name)
            assert registry_thread is thread, \
                f"注册表中的线程对象应该与 run_strategy 返回的一致（策略: {strategy_name}）"
        
        # 验证3：注册表中的线程都处于运行状态
        for strategy_name, thread in threads:
            assert thread.is_alive(), \
                f"策略 {strategy_name} 的线程应该处于运行状态"
        
        # 验证4：可以多次获取注册表（不影响内部状态）
        strategies_copy1 = api.get_running_strategies()
        strategies_copy2 = api.get_running_strategies()
        
        assert len(strategies_copy1) == len(strategies_copy2), \
            "多次获取注册表应该返回相同数量的策略"
        
        # 验证5：返回的是副本，修改不影响内部注册表
        strategies_copy1.clear()
        strategies_after_clear = api.get_running_strategies()
        assert len(strategies_after_clear) == num_strategies, \
            "修改返回的注册表副本不应该影响内部注册表"
        
        # 等待所有策略执行完成
        for strategy_name, thread in threads:
            thread.join(timeout=sleep_time * 2 + 1.0)
        
        # 验证6：所有策略都执行完成
        assert len(execution_records) == num_strategies, \
            f"应该有 {num_strategies} 个策略执行完成"
        
        for i in range(num_strategies):
            assert i in execution_records, f"策略 {i} 应该有执行记录"
            assert execution_records[i].get('started'), f"策略 {i} 应该标记为已启动"
            assert execution_records[i].get('completed'), f"策略 {i} 应该标记为已完成"
        
        # 验证7：所有线程都已结束
        for strategy_name, thread in threads:
            assert not thread.is_alive(), \
                f"策略 {strategy_name} 的线程应该已经结束"
        
        # 验证8：策略完成后从注册表中移除
        # 给一点时间让 finally 块执行完成
        time.sleep(0.1)
        
        final_strategies = api.get_running_strategies()
        assert len(final_strategies) == 0, \
            f"所有策略执行完成后，注册表应该为空，实际: {len(final_strategies)}"
        
        for strategy_name in strategy_names:
            assert strategy_name not in final_strategies, \
                f"策略 {strategy_name} 执行完成后应该从注册表移除"
    
    @given(
        num_normal_strategies=st.integers(min_value=1, max_value=3),
        num_failing_strategies=st.integers(min_value=1, max_value=2)
    )
    @settings(max_examples=50, deadline=5000)
    def test_property_registry_cleanup_on_exception(
        self,
        num_normal_strategies: int,
        num_failing_strategies: int
    ):
        """
        **Feature: sync-strategy-api, Property 13: 策略注册表维护（异常清理测试）**
        
        验证策略抛出异常后，注册表能够正确清理。
        
        **Validates: Requirements 4.5**
        """
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 用于记录策略执行情况
        execution_status = {}
        lock = threading.Lock()
        
        def create_normal_strategy(strategy_id: int):
            """创建正常的策略"""
            def strategy():
                with lock:
                    execution_status[f'normal_{strategy_id}'] = 'running'
                time.sleep(0.1)
                with lock:
                    execution_status[f'normal_{strategy_id}'] = 'completed'
            strategy.__name__ = f'normal_strategy_{strategy_id}'
            return strategy
        
        def create_failing_strategy(strategy_id: int):
            """创建会抛出异常的策略"""
            def strategy():
                with lock:
                    execution_status[f'failing_{strategy_id}'] = 'running'
                time.sleep(0.05)
                raise RuntimeError(f"策略 {strategy_id} 故意抛出异常")
            strategy.__name__ = f'failing_strategy_{strategy_id}'
            return strategy
        
        # 启动所有策略
        all_threads = []
        all_strategy_names = []
        
        # 启动失败策略
        for i in range(num_failing_strategies):
            strategy = create_failing_strategy(i)
            strategy_name = strategy.__name__
            all_strategy_names.append(strategy_name)
            thread = api.run_strategy(strategy)
            all_threads.append((strategy_name, thread))
        
        # 启动正常策略
        for i in range(num_normal_strategies):
            strategy = create_normal_strategy(i)
            strategy_name = strategy.__name__
            all_strategy_names.append(strategy_name)
            thread = api.run_strategy(strategy)
            all_threads.append((strategy_name, thread))
        
        # 验证1：所有策略都在注册表中
        total_strategies = num_normal_strategies + num_failing_strategies
        strategies = api.get_running_strategies()
        assert len(strategies) == total_strategies, \
            f"注册表中应该有 {total_strategies} 个策略"
        
        # 验证2：所有策略名称都在注册表中
        for strategy_name in all_strategy_names:
            assert strategy_name in strategies, \
                f"策略 {strategy_name} 应该在注册表中"
        
        # 等待所有策略执行完成
        for strategy_name, thread in all_threads:
            thread.join(timeout=1.0)
        
        # 验证3：所有线程都已结束（包括抛出异常的）
        for strategy_name, thread in all_threads:
            assert not thread.is_alive(), \
                f"策略 {strategy_name} 的线程应该已经结束"
        
        # 验证4：注册表已清空（包括异常策略）
        # 给一点时间让 finally 块执行完成
        time.sleep(0.1)
        
        final_strategies = api.get_running_strategies()
        assert len(final_strategies) == 0, \
            f"所有策略执行完成后（包括异常策略），注册表应该为空，实际: {len(final_strategies)}"
        
        # 验证5：所有策略都从注册表中移除
        for strategy_name in all_strategy_names:
            assert strategy_name not in final_strategies, \
                f"策略 {strategy_name} 应该从注册表中移除"
    
    @given(
        num_strategies=st.integers(min_value=2, max_value=4)
    )
    @settings(max_examples=50, deadline=5000)
    def test_property_registry_thread_consistency(
        self,
        num_strategies: int
    ):
        """
        **Feature: sync-strategy-api, Property 13: 策略注册表维护（线程一致性测试）**
        
        验证注册表中维护的线程对象与实际运行的线程一致。
        
        **Validates: Requirements 4.5**
        """
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 用于记录线程信息
        thread_info = {}
        lock = threading.Lock()
        
        def create_strategy(strategy_id: int):
            """创建策略函数"""
            def strategy():
                # 记录当前线程信息
                current_thread = threading.current_thread()
                with lock:
                    thread_info[strategy_id] = {
                        'thread_id': current_thread.ident,
                        'thread_name': current_thread.name,
                        'is_alive': current_thread.is_alive()
                    }
                
                # 模拟策略执行
                time.sleep(0.2)
            
            strategy.__name__ = f'consistency_strategy_{strategy_id}'
            return strategy
        
        # 启动所有策略
        returned_threads = {}
        
        for i in range(num_strategies):
            strategy = create_strategy(i)
            strategy_name = strategy.__name__
            thread = api.run_strategy(strategy)
            returned_threads[strategy_name] = thread
        
        # 验证1：注册表中的线程对象与返回的线程对象完全一致（同一个对象）
        registry = api.get_running_strategies()
        
        for strategy_name, returned_thread in returned_threads.items():
            registry_thread = registry.get(strategy_name)
            
            assert registry_thread is not None, \
                f"策略 {strategy_name} 应该在注册表中"
            
            assert registry_thread is returned_thread, \
                f"注册表中的线程对象应该与返回的线程对象是同一个对象（策略: {strategy_name}）"
            
            # 验证线程 ID 一致
            assert registry_thread.ident == returned_thread.ident, \
                f"注册表中的线程 ID 应该与返回的线程 ID 一致（策略: {strategy_name}）"
            
            # 验证线程名称一致
            assert registry_thread.name == returned_thread.name, \
                f"注册表中的线程名称应该与返回的线程名称一致（策略: {strategy_name}）"
            
            # 验证线程状态一致
            assert registry_thread.is_alive() == returned_thread.is_alive(), \
                f"注册表中的线程状态应该与返回的线程状态一致（策略: {strategy_name}）"
        
        # 等待所有策略完成
        for thread in returned_threads.values():
            thread.join(timeout=1.0)
        
        # 验证2：策略执行期间记录的线程信息与返回的线程一致
        for i in range(num_strategies):
            strategy_name = f'consistency_strategy_{i}'
            returned_thread = returned_threads[strategy_name]
            recorded_info = thread_info.get(i)
            
            assert recorded_info is not None, \
                f"策略 {i} 应该有线程信息记录"
            
            assert recorded_info['thread_id'] == returned_thread.ident, \
                f"策略执行期间的线程 ID 应该与返回的线程 ID 一致"
            
            assert strategy_name in recorded_info['thread_name'], \
                f"策略执行期间的线程名称应该包含策略名称"
        
        # 验证3：注册表已清空
        time.sleep(0.1)
        final_registry = api.get_running_strategies()
        assert len(final_registry) == 0, \
            "所有策略执行完成后，注册表应该为空"
    
    def test_property_registry_concurrent_access(self):
        """
        **Feature: sync-strategy-api, Property 13: 策略注册表维护（并发访问测试）**
        
        验证多个线程同时访问注册表时的线程安全性。
        
        **Validates: Requirements 4.5**
        """
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 用于记录并发访问结果
        access_results = []
        lock = threading.Lock()
        
        def strategy_that_checks_registry(strategy_id: int):
            """策略函数，会多次检查注册表"""
            def strategy():
                for _ in range(5):
                    # 获取注册表
                    registry = api.get_running_strategies()
                    
                    # 记录结果
                    with lock:
                        access_results.append({
                            'strategy_id': strategy_id,
                            'registry_size': len(registry),
                            'thread_id': threading.current_thread().ident
                        })
                    
                    time.sleep(0.05)
            
            strategy.__name__ = f'checking_strategy_{strategy_id}'
            return strategy
        
        # 启动多个策略，每个策略都会访问注册表
        num_strategies = 3
        threads = []
        
        for i in range(num_strategies):
            strategy = strategy_that_checks_registry(i)
            thread = api.run_strategy(strategy)
            threads.append(thread)
        
        # 等待所有策略完成
        for thread in threads:
            thread.join(timeout=2.0)
        
        # 验证1：所有并发访问都成功完成
        expected_accesses = num_strategies * 5
        assert len(access_results) == expected_accesses, \
            f"应该有 {expected_accesses} 次注册表访问，实际: {len(access_results)}"
        
        # 验证2：每次访问时注册表大小都在合理范围内（0 到 num_strategies）
        for result in access_results:
            registry_size = result['registry_size']
            assert 0 <= registry_size <= num_strategies, \
                f"注册表大小应该在 0 到 {num_strategies} 之间，实际: {registry_size}"
        
        # 验证3：注册表最终为空
        time.sleep(0.1)
        final_registry = api.get_running_strategies()
        assert len(final_registry) == 0, \
            "所有策略执行完成后，注册表应该为空"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
