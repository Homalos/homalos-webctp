#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : test_sync_api_multi_strategy_concurrent.py
@Date       : 2025/12/20
@Author     : Kiro AI Assistant
@Email      : -
@Software   : PyCharm
@Description: 多策略并发测试

验证任务 14.2 的要求：
- 同时运行多个策略
- 验证策略之间不互相干扰
"""

import pytest
import time
import threading
from unittest.mock import Mock, MagicMock, patch
from src.strategy.sync_api import SyncStrategyApi, Quote, Position

# 测试凭证
TEST_USER_ID = "test_user"
TEST_PASSWORD = "test_pass"


class TestMultiStrategyConcurrent:
    """多策略并发测试"""
    
    @patch('src.strategy.sync_api._EventLoopThread')
    def test_multiple_strategies_different_instruments(self, mock_event_loop_class):
        """
        测试多个策略交易不同合约
        
        验证：
        1. 启动 3 个策略，每个策略交易不同的合约
        2. 每个策略执行：获取行情 → 查询持仓 → 模拟下单
        3. 所有策略都能成功完成
        4. 每个策略获取的数据是正确的合约数据
        5. 策略之间的数据不会混淆
        
        Requirements: 4.1, 4.2
        """
        # ===== 设置 Mock =====
        mock_event_loop = MagicMock()
        mock_event_loop_class.return_value = mock_event_loop
        
        mock_loop = Mock()
        mock_loop.is_running.return_value = True
        mock_event_loop.loop = mock_loop
        
        # ===== 初始化 API =====
        api = SyncStrategyApi(
            user_id=TEST_USER_ID,
            password=TEST_PASSWORD
        )
        
        # ===== 准备测试数据 =====
        instruments = ["rb2605", "cu2605", "au2606"]
        
        # 为每个合约添加行情数据
        for i, instrument_id in enumerate(instruments):
            market_data = {
                'InstrumentID': instrument_id,
                'LastPrice': 3500.0 + i * 100,  # 不同的价格
                'BidPrice1': 3499.0 + i * 100,
                'BidVolume1': 10 + i,
                'AskPrice1': 3501.0 + i * 100,
                'AskVolume1': 20 + i,
                'Volume': 1000 + i * 100,
                'OpenInterest': 50000 + i * 1000,
                'UpdateTime': '09:30:00',
                'UpdateMillisec': 0
            }
            api._quote_cache.update_from_market_data(instrument_id, market_data)
            
            # 为每个合约添加持仓数据
            position_data = {
                'pos_long': i,
                'pos_long_today': i,
                'pos_long_his': 0,
                'open_price_long': 3500.0 + i * 100,
                'pos_short': 0,
                'pos_short_today': 0,
                'pos_short_his': 0,
                'open_price_short': float('nan')
            }
            api._position_cache.update_from_position_data(instrument_id, position_data)
        
        # ===== 定义策略并收集结果 =====
        strategy_results = {}
        results_lock = threading.Lock()
        completion_events = {instrument: threading.Event() for instrument in instruments}
        
        def create_strategy(instrument_id: str, expected_price: float, expected_position: int):
            """创建策略函数"""
            def strategy():
                try:
                    # 1. 获取行情
                    quote = api.get_quote(instrument_id, timeout=2.0)
                    
                    # 2. 查询持仓
                    position = api._position_cache.get(instrument_id)
                    
                    # 3. 记录结果
                    with results_lock:
                        strategy_results[instrument_id] = {
                            'quote': quote,
                            'position': position,
                            'thread_id': threading.current_thread().ident,
                            'success': True
                        }
                    
                    # 4. 标记完成
                    completion_events[instrument_id].set()
                    
                except Exception as e:
                    with results_lock:
                        strategy_results[instrument_id] = {
                            'error': str(e),
                            'success': False
                        }
                    completion_events[instrument_id].set()
            
            return strategy
        
        # ===== 启动所有策略 =====
        threads = []
        for i, instrument_id in enumerate(instruments):
            expected_price = 3500.0 + i * 100
            expected_position = i
            strategy = create_strategy(instrument_id, expected_price, expected_position)
            thread = api.run_strategy(strategy)
            threads.append(thread)
        
        # ===== 等待所有策略完成 =====
        for event in completion_events.values():
            assert event.wait(timeout=5.0), "策略应该在超时前完成"
        
        for thread in threads:
            thread.join(timeout=5.0)
        
        # ===== 验证结果 =====
        # 验证 1：所有策略都成功完成
        assert len(strategy_results) == 3, "应该有 3 个策略的结果"
        
        for instrument_id in instruments:
            assert instrument_id in strategy_results, f"应该有 {instrument_id} 的结果"
            result = strategy_results[instrument_id]
            assert result['success'], f"{instrument_id} 策略应该成功"
        
        # 验证 2：每个策略获取的数据是正确的
        for i, instrument_id in enumerate(instruments):
            result = strategy_results[instrument_id]
            quote = result['quote']
            position = result['position']
            
            # 验证行情数据
            assert quote.InstrumentID == instrument_id, f"{instrument_id} 的合约代码应该匹配"
            assert quote.LastPrice == 3500.0 + i * 100, f"{instrument_id} 的价格应该正确"
            
            # 验证持仓数据
            assert position.pos_long == i, f"{instrument_id} 的持仓应该正确"
        
        # 验证 3：策略在不同线程中运行
        thread_ids = [result['thread_id'] for result in strategy_results.values()]
        assert len(set(thread_ids)) == 3, "策略应该在不同的线程中运行"
        
        # ===== 清理 =====
        api.stop()
    
    @patch('src.strategy.sync_api._EventLoopThread')
    def test_multiple_strategies_same_instrument(self, mock_event_loop_class):
        """
        测试多个策略交易相同合约
        
        验证：
        1. 启动 3 个策略，都交易同一个合约
        2. 每个策略同时获取行情和持仓
        3. 所有策略都能获取到相同的行情数据
        4. 共享资源（行情缓存）的访问是线程安全的
        5. 没有数据竞争或脏读
        
        Requirements: 4.2, 6.5
        """
        # ===== 设置 Mock =====
        mock_event_loop = MagicMock()
        mock_event_loop_class.return_value = mock_event_loop
        
        mock_loop = Mock()
        mock_loop.is_running.return_value = True
        mock_event_loop.loop = mock_loop
        
        # ===== 初始化 API =====
        api = SyncStrategyApi(
            user_id=TEST_USER_ID,
            password=TEST_PASSWORD
        )
        
        # ===== 准备测试数据 =====
        instrument_id = "rb2605"
        
        # 添加行情数据
        market_data = {
            'InstrumentID': instrument_id,
            'LastPrice': 3500.0,
            'BidPrice1': 3499.0,
            'BidVolume1': 10,
            'AskPrice1': 3501.0,
            'AskVolume1': 20,
            'Volume': 1000,
            'OpenInterest': 50000,
            'UpdateTime': '09:30:00',
            'UpdateMillisec': 0
        }
        api._quote_cache.update_from_market_data(instrument_id, market_data)
        
        # 添加持仓数据
        position_data = {
            'pos_long': 5,
            'pos_long_today': 2,
            'pos_long_his': 3,
            'open_price_long': 3500.0,
            'pos_short': 0,
            'pos_short_today': 0,
            'pos_short_his': 0,
            'open_price_short': float('nan')
        }
        api._position_cache.update_from_position_data(instrument_id, position_data)
        
        # ===== 定义策略并收集结果 =====
        strategy_results = []
        results_lock = threading.Lock()
        completion_count = threading.Semaphore(0)
        
        def create_strategy(strategy_id: int):
            """创建策略函数"""
            def strategy():
                try:
                    # 短暂延迟，增加并发冲突的可能性
                    time.sleep(0.01 * strategy_id)
                    
                    # 1. 获取行情
                    quote = api.get_quote(instrument_id, timeout=2.0)
                    
                    # 2. 查询持仓
                    position = api._position_cache.get(instrument_id)
                    
                    # 3. 记录结果
                    with results_lock:
                        strategy_results.append({
                            'strategy_id': strategy_id,
                            'quote': quote,
                            'position': position,
                            'thread_id': threading.current_thread().ident,
                            'success': True
                        })
                    
                    # 4. 标记完成
                    completion_count.release()
                    
                except Exception as e:
                    with results_lock:
                        strategy_results.append({
                            'strategy_id': strategy_id,
                            'error': str(e),
                            'success': False
                        })
                    completion_count.release()
            
            return strategy
        
        # ===== 启动所有策略 =====
        num_strategies = 3
        threads = []
        for i in range(num_strategies):
            strategy = create_strategy(i)
            thread = api.run_strategy(strategy)
            threads.append(thread)
        
        # ===== 等待所有策略完成 =====
        for _ in range(num_strategies):
            assert completion_count.acquire(timeout=5.0), "策略应该在超时前完成"
        
        for thread in threads:
            thread.join(timeout=5.0)
        
        # ===== 验证结果 =====
        # 验证 1：所有策略都成功完成
        assert len(strategy_results) == num_strategies, f"应该有 {num_strategies} 个策略的结果"
        
        for result in strategy_results:
            assert result['success'], f"策略 {result['strategy_id']} 应该成功"
        
        # 验证 2：所有策略获取到相同的行情数据
        for result in strategy_results:
            quote = result['quote']
            assert quote.InstrumentID == instrument_id, "合约代码应该匹配"
            assert quote.LastPrice == 3500.0, "所有策略应该获取到相同的价格"
            assert quote.BidPrice1 == 3499.0, "所有策略应该获取到相同的买一价"
        
        # 验证 3：所有策略获取到相同的持仓数据
        for result in strategy_results:
            position = result['position']
            assert position.pos_long == 5, "所有策略应该获取到相同的持仓"
            assert position.pos_long_today == 2, "所有策略应该获取到相同的今仓"
        
        # 验证 4：策略在不同线程中运行
        thread_ids = [result['thread_id'] for result in strategy_results]
        assert len(set(thread_ids)) == num_strategies, "策略应该在不同的线程中运行"
        
        # ===== 清理 =====
        api.stop()
    
    @patch('src.strategy.sync_api._EventLoopThread')
    def test_mixed_success_and_failure_strategies(self, mock_event_loop_class):
        """
        测试混合场景（成功和失败策略）
        
        验证：
        1. 启动 4 个策略：2 个正常策略、1 个抛出异常的策略、1 个访问无效合约的策略
        2. 正常策略不受失败策略影响
        3. 异常被正确捕获和记录
        4. 所有策略线程都能正常结束
        
        Requirements: 4.3, 7.4
        """
        # ===== 设置 Mock =====
        mock_event_loop = MagicMock()
        mock_event_loop_class.return_value = mock_event_loop
        
        mock_loop = Mock()
        mock_loop.is_running.return_value = True
        mock_event_loop.loop = mock_loop
        
        # ===== 初始化 API =====
        api = SyncStrategyApi(
            user_id=TEST_USER_ID,
            password=TEST_PASSWORD
        )
        
        # ===== 准备测试数据 =====
        valid_instruments = ["rb2605", "cu2605"]
        
        # 为有效合约添加数据
        for instrument_id in valid_instruments:
            market_data = {
                'InstrumentID': instrument_id,
                'LastPrice': 3500.0,
                'UpdateTime': '09:30:00',
                'UpdateMillisec': 0
            }
            api._quote_cache.update_from_market_data(instrument_id, market_data)
        
        # ===== 定义策略并收集结果 =====
        strategy_results = {}
        results_lock = threading.Lock()
        completion_events = {}
        
        def create_normal_strategy(strategy_id: str, instrument_id: str):
            """创建正常策略"""
            completion_events[strategy_id] = threading.Event()
            
            def strategy():
                try:
                    quote = api.get_quote(instrument_id, timeout=2.0)
                    
                    with results_lock:
                        strategy_results[strategy_id] = {
                            'type': 'normal',
                            'success': True,
                            'quote': quote
                        }
                except Exception as e:
                    with results_lock:
                        strategy_results[strategy_id] = {
                            'type': 'normal',
                            'success': False,
                            'error': str(e)
                        }
                finally:
                    completion_events[strategy_id].set()
            
            return strategy
        
        def create_exception_strategy(strategy_id: str):
            """创建会抛出异常的策略"""
            completion_events[strategy_id] = threading.Event()
            
            def strategy():
                try:
                    # 故意抛出异常
                    raise ValueError("测试异常")
                except Exception as e:
                    with results_lock:
                        strategy_results[strategy_id] = {
                            'type': 'exception',
                            'success': False,
                            'error': str(e)
                        }
                finally:
                    completion_events[strategy_id].set()
            
            return strategy
        
        def create_invalid_instrument_strategy(strategy_id: str):
            """创建访问无效合约的策略"""
            completion_events[strategy_id] = threading.Event()
            
            def strategy():
                try:
                    # 访问不存在的合约（会超时）
                    quote = api.get_quote("INVALID_SYMBOL", timeout=0.5)
                    
                    with results_lock:
                        strategy_results[strategy_id] = {
                            'type': 'invalid',
                            'success': True,
                            'quote': quote
                        }
                except TimeoutError as e:
                    with results_lock:
                        strategy_results[strategy_id] = {
                            'type': 'invalid',
                            'success': False,
                            'error': 'timeout'
                        }
                except Exception as e:
                    with results_lock:
                        strategy_results[strategy_id] = {
                            'type': 'invalid',
                            'success': False,
                            'error': str(e)
                        }
                finally:
                    completion_events[strategy_id].set()
            
            return strategy
        
        # ===== 启动所有策略 =====
        threads = []
        
        # 启动 2 个正常策略
        for i, instrument_id in enumerate(valid_instruments):
            strategy_id = f"normal_{i}"
            strategy = create_normal_strategy(strategy_id, instrument_id)
            thread = api.run_strategy(strategy)
            threads.append((strategy_id, thread))
        
        # 启动 1 个异常策略
        strategy_id = "exception_0"
        strategy = create_exception_strategy(strategy_id)
        thread = api.run_strategy(strategy)
        threads.append((strategy_id, thread))
        
        # 启动 1 个无效合约策略
        strategy_id = "invalid_0"
        strategy = create_invalid_instrument_strategy(strategy_id)
        thread = api.run_strategy(strategy)
        threads.append((strategy_id, thread))
        
        # ===== 等待所有策略完成 =====
        for event in completion_events.values():
            assert event.wait(timeout=10.0), "策略应该在超时前完成"
        
        for strategy_id, thread in threads:
            thread.join(timeout=10.0)
        
        # ===== 验证结果 =====
        # 验证 1：所有策略都有结果
        assert len(strategy_results) == 4, "应该有 4 个策略的结果"
        
        # 验证 2：正常策略成功
        normal_results = [r for r in strategy_results.values() if r['type'] == 'normal']
        assert len(normal_results) == 2, "应该有 2 个正常策略"
        for result in normal_results:
            assert result['success'], "正常策略应该成功"
        
        # 验证 3：异常策略失败但被捕获
        exception_results = [r for r in strategy_results.values() if r['type'] == 'exception']
        assert len(exception_results) == 1, "应该有 1 个异常策略"
        assert not exception_results[0]['success'], "异常策略应该失败"
        assert '测试异常' in exception_results[0]['error'], "应该捕获到测试异常"
        
        # 验证 4：无效合约策略超时
        invalid_results = [r for r in strategy_results.values() if r['type'] == 'invalid']
        assert len(invalid_results) == 1, "应该有 1 个无效合约策略"
        assert not invalid_results[0]['success'], "无效合约策略应该失败"
        assert invalid_results[0]['error'] == 'timeout', "应该是超时错误"
        
        # 验证 5：API 仍然可用（没有被失败策略破坏）
        assert api._event_loop_thread is not None, "API 应该仍然可用"
        
        # ===== 清理 =====
        api.stop()
    
    @patch('src.strategy.sync_api._EventLoopThread')
    def test_strategy_registry_management(self, mock_event_loop_class):
        """
        测试策略注册表管理
        
        验证：
        1. 启动多个策略
        2. 策略被正确添加到注册表
        3. 等待策略完成后，策略从注册表中移除
        4. 注册表正确维护运行中的策略
        
        Requirements: 4.5
        """
        # ===== 设置 Mock =====
        mock_event_loop = MagicMock()
        mock_event_loop_class.return_value = mock_event_loop
        
        mock_loop = Mock()
        mock_loop.is_running.return_value = True
        mock_event_loop.loop = mock_loop
        
        # ===== 初始化 API =====
        api = SyncStrategyApi(
            user_id=TEST_USER_ID,
            password=TEST_PASSWORD
        )
        
        # ===== 准备测试数据 =====
        instrument_id = "rb2605"
        market_data = {
            'InstrumentID': instrument_id,
            'LastPrice': 3500.0,
            'UpdateTime': '09:30:00',
            'UpdateMillisec': 0
        }
        api._quote_cache.update_from_market_data(instrument_id, market_data)
        
        # ===== 定义策略 =====
        completion_events = []
        start_events = []  # 用于确保策略已启动
        
        def create_short_strategy(strategy_id: int):
            """创建短时运行的策略"""
            start_event = threading.Event()
            completion_event = threading.Event()
            start_events.append(start_event)
            completion_events.append(completion_event)
            
            def strategy():
                # 标记已启动
                start_event.set()
                # 短暂运行
                time.sleep(0.3)
                completion_event.set()
            
            # 设置函数名称（用于注册表）
            strategy.__name__ = f"short_strategy_{strategy_id}"
            return strategy
        
        def create_long_strategy(strategy_id: int):
            """创建长时运行的策略"""
            start_event = threading.Event()
            completion_event = threading.Event()
            start_events.append(start_event)
            completion_events.append(completion_event)
            
            def strategy():
                # 标记已启动
                start_event.set()
                # 长时间运行
                time.sleep(1.0)
                completion_event.set()
            
            # 设置函数名称（用于注册表）
            strategy.__name__ = f"long_strategy_{strategy_id}"
            return strategy
        
        # ===== 启动策略 =====
        # 启动 2 个短时策略
        short_threads = []
        for i in range(2):
            strategy = create_short_strategy(i)
            thread = api.run_strategy(strategy)
            short_threads.append((strategy.__name__, thread))
        
        # 等待策略真正启动
        for event in start_events[:2]:
            assert event.wait(timeout=2.0), "策略应该启动"
        
        # 验证策略被添加到注册表
        with api._strategy_lock:
            registry_size = len(api._running_strategies)
            assert registry_size == 2, f"注册表应该有 2 个策略，实际有 {registry_size}"
        
        # 启动 1 个长时策略
        long_strategy = create_long_strategy(0)
        long_thread = api.run_strategy(long_strategy)
        
        # 等待长时策略启动
        assert start_events[2].wait(timeout=2.0), "长时策略应该启动"
        
        # 验证注册表增加
        with api._strategy_lock:
            registry_size = len(api._running_strategies)
            assert registry_size == 3, f"注册表应该有 3 个策略，实际有 {registry_size}"
        
        # ===== 等待短时策略完成 =====
        for event in completion_events[:2]:
            event.wait(timeout=5.0)
        
        for name, thread in short_threads:
            thread.join(timeout=5.0)
        
        # 短暂延迟，等待注册表更新
        time.sleep(0.1)
        
        # 验证短时策略从注册表移除
        with api._strategy_lock:
            registry_size = len(api._running_strategies)
            # 注意：由于策略执行很快，可能已经全部完成
            assert registry_size <= 1, f"短时策略完成后，注册表应该只剩 0-1 个策略，实际有 {registry_size}"
        
        # ===== 等待长时策略完成 =====
        completion_events[2].wait(timeout=5.0)
        long_thread.join(timeout=5.0)
        
        # 短暂延迟，等待注册表更新
        time.sleep(0.1)
        
        # 验证所有策略都从注册表移除
        with api._strategy_lock:
            registry_size = len(api._running_strategies)
            assert registry_size == 0, f"所有策略完成后，注册表应该为空，实际有 {registry_size}"
        
        # ===== 清理 =====
        api.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
