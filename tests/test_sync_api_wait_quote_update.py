#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : test_sync_api_wait_quote_update.py
@Date       : 2025/12/16
@Author     : Kiro AI Assistant
@Email      : -
@Software   : PyCharm
@Description: 测试 SyncStrategyApi.wait_quote_update() 方法
"""

import pytest
import threading
import time
from hypothesis import given, settings, strategies as st, HealthCheck
from src.strategy.sync_api import SyncStrategyApi, Quote
# Test credentials
TEST_USER_ID = "test_user"
TEST_PASSWORD = "test_pass"


class TestWaitQuoteUpdate:
    """测试 wait_quote_update() 方法"""
    
    def test_wait_quote_update_basic(self):
        """测试基本的等待行情更新功能"""
        # 创建 API 实例
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        instrument_id = "rb2505"
        
        # 手动标记为已订阅（避免触发实际订阅）
        api._subscribed_instruments.add(instrument_id)
        
        # 在另一个线程中延迟推送行情
        def push_quote():
            time.sleep(0.5)  # 延迟 0.5 秒
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
                'UpdateMillisec': 500
            }
            api._quote_cache.update(instrument_id, market_data)
        
        # 启动推送线程
        push_thread = threading.Thread(target=push_quote)
        push_thread.start()
        
        # 等待行情更新（应该在 0.5 秒后返回）
        start_time = time.time()
        quote = api.wait_quote_update(instrument_id, timeout=2.0)
        elapsed_time = time.time() - start_time
        
        # 验证
        assert quote is not None
        assert quote.InstrumentID == instrument_id
        assert quote.LastPrice == 3500.0
        assert 0.4 < elapsed_time < 1.0, f"应该在约 0.5 秒后返回，实际: {elapsed_time}"
        
        # 等待推送线程结束
        push_thread.join()
    
    def test_wait_quote_update_timeout(self):
        """测试等待超时情况"""
        # 创建 API 实例
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        instrument_id = "rb2505"
        
        # 手动标记为已订阅
        api._subscribed_instruments.add(instrument_id)
        
        # 不推送行情，应该超时
        with pytest.raises(TimeoutError, match="等待合约.*行情更新超时"):
            api.wait_quote_update(instrument_id, timeout=0.5)
    
    def test_wait_quote_update_auto_subscribe(self):
        """测试自动订阅功能"""
        # 创建 API 实例
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        instrument_id = "rb2505"
        
        # 确保未订阅
        assert instrument_id not in api._subscribed_instruments
        
        # Mock 事件循环和客户端
        from unittest.mock import Mock, AsyncMock, patch
        import asyncio
        
        mock_loop = Mock()
        mock_loop.is_running.return_value = True
        
        mock_md_client = Mock()
        mock_md_client.call = AsyncMock(return_value={'success': True})
        
        mock_event_loop_thread = Mock()
        mock_event_loop_thread.loop = mock_loop
        mock_event_loop_thread.md_client = mock_md_client
        
        api._event_loop_thread = mock_event_loop_thread
        
        # 模拟订阅成功并推送行情
        def simulate_subscription_and_push(*args, **kwargs):
            """模拟订阅成功并推送行情"""
            import concurrent.futures
            
            # 在另一个线程中推送行情
            def push_quote():
                time.sleep(0.3)
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
                    'UpdateMillisec': 500
                }
                api._quote_cache.update(instrument_id, market_data)
            
            push_thread = threading.Thread(target=push_quote)
            push_thread.start()
            
            future = concurrent.futures.Future()
            future.set_result({'success': True})
            return future
        
        # Mock run_coroutine_threadsafe
        with patch('asyncio.run_coroutine_threadsafe', side_effect=simulate_subscription_and_push):
            # 调用 wait_quote_update，应该自动订阅并等待行情
            quote = api.wait_quote_update(instrument_id, timeout=2.0)
            
            # 验证
            assert quote is not None
            assert quote.InstrumentID == instrument_id
            assert quote.LastPrice == 3500.0
            
            # 验证合约已被标记为已订阅
            assert instrument_id in api._subscribed_instruments
    
    def test_wait_quote_update_multiple_waiters(self):
        """测试多个线程同时等待同一合约的行情更新"""
        # 创建 API 实例
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        instrument_id = "rb2505"
        
        # 手动标记为已订阅
        api._subscribed_instruments.add(instrument_id)
        
        # 用于存储各线程收到的行情
        quotes = []
        errors = []
        
        def wait_for_quote():
            try:
                quote = api.wait_quote_update(instrument_id, timeout=2.0)
                quotes.append(quote)
            except Exception as e:
                errors.append(e)
        
        # 启动多个等待线程
        wait_threads = []
        for _ in range(3):
            thread = threading.Thread(target=wait_for_quote)
            thread.start()
            wait_threads.append(thread)
        
        # 等待所有线程启动
        time.sleep(0.2)
        
        # 推送一次行情
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
            'UpdateMillisec': 500
        }
        api._quote_cache.update(instrument_id, market_data)
        
        # 等待所有线程完成
        for thread in wait_threads:
            thread.join(timeout=3.0)
        
        # 验证：修复后，所有等待线程都应该收到通知
        assert len(quotes) == 3, f"所有 3 个等待线程都应该收到行情通知，实际收到: {len(quotes)}"
        assert len(errors) == 0, f"不应该有线程超时，实际超时: {len(errors)}"
        
        # 验证收到的行情数据正确
        for quote in quotes:
            assert quote.InstrumentID == instrument_id
            assert quote.LastPrice == 3500.0
    
    def test_wait_quote_update_returns_copy(self):
        """测试 wait_quote_update 返回副本而非原始对象"""
        # 创建 API 实例
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        instrument_id = "rb2505"
        
        # 手动标记为已订阅
        api._subscribed_instruments.add(instrument_id)
        
        # 在另一个线程中推送行情
        def push_quote():
            time.sleep(0.3)
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
                'UpdateMillisec': 500
            }
            api._quote_cache.update(instrument_id, market_data)
        
        push_thread = threading.Thread(target=push_quote)
        push_thread.start()
        
        # 等待行情更新
        quote1 = api.wait_quote_update(instrument_id, timeout=2.0)
        
        push_thread.join()
        
        # 再次推送行情
        push_thread2 = threading.Thread(target=push_quote)
        push_thread2.start()
        
        quote2 = api.wait_quote_update(instrument_id, timeout=2.0)
        
        push_thread2.join()
        
        # 验证是不同的对象（副本）
        assert quote1 is not quote2
        assert quote1.InstrumentID == quote2.InstrumentID
        assert quote1.LastPrice == quote2.LastPrice


class TestPropertyWaitQuoteUpdate:
    """属性测试：行情更新阻塞等待"""
    
    # Feature: sync-strategy-api, Property 3: 行情更新阻塞等待
    @given(
        instrument_id=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Nd')),
            min_size=4,
            max_size=8
        ),
        initial_price=st.floats(min_value=1000.0, max_value=10000.0, allow_nan=False),
        updated_price=st.floats(min_value=1000.0, max_value=10000.0, allow_nan=False)
    )
    @settings(max_examples=100, deadline=5000)
    def test_property_wait_quote_update_timestamp_advances(
        self, 
        instrument_id: str, 
        initial_price: float,
        updated_price: float
    ):
        """
        **Feature: sync-strategy-api, Property 3: 行情更新阻塞等待**
        
        Property 3: 行情更新阻塞等待
        
        For any 已订阅的合约，调用 wait_quote_update(instrument_id) 应该阻塞当前线程，
        直到该合约有新行情推送，且返回的行情时间戳应该晚于调用前的行情时间戳。
        
        **Validates: Requirements 1.3**
        
        测试策略：
        1. 生成随机的合约代码和行情价格
        2. 推送初始行情（时间戳 T1）
        3. 在后台线程中延迟推送新行情（时间戳 T2 > T1）
        4. 调用 wait_quote_update() 并验证：
           - 方法阻塞直到新行情到达
           - 返回的行情时间戳晚于初始时间戳
           - 返回的行情价格是更新后的价格
        """
        # 创建 API 实例
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 手动标记为已订阅
        api._subscribed_instruments.add(instrument_id)
        
        # 推送初始行情（时间戳 T1）
        initial_time = "09:30:00"
        initial_millisec = 100
        initial_market_data = {
            'InstrumentID': instrument_id,
            'LastPrice': initial_price,
            'BidPrice1': initial_price - 1.0,
            'BidVolume1': 10,
            'AskPrice1': initial_price + 1.0,
            'AskVolume1': 20,
            'Volume': 1000,
            'OpenInterest': 50000,
            'UpdateTime': initial_time,
            'UpdateMillisec': initial_millisec
        }
        api._quote_cache.update(instrument_id, initial_market_data)
        
        # 获取初始行情（用于后续比较）
        initial_quote = api._quote_cache.get(instrument_id)
        assert initial_quote is not None, "初始行情应该存在于缓存中"
        
        # 在后台线程中延迟推送新行情（时间戳 T2 > T1）
        def push_updated_quote():
            time.sleep(0.3)  # 延迟 0.3 秒
            
            # 新行情的时间戳晚于初始时间戳
            updated_time = "09:30:01"  # 时间增加 1 秒
            updated_millisec = 200  # 毫秒也增加
            
            updated_market_data = {
                'InstrumentID': instrument_id,
                'LastPrice': updated_price,
                'BidPrice1': updated_price - 1.0,
                'BidVolume1': 15,
                'AskPrice1': updated_price + 1.0,
                'AskVolume1': 25,
                'Volume': 1100,
                'OpenInterest': 51000,
                'UpdateTime': updated_time,
                'UpdateMillisec': updated_millisec
            }
            api._quote_cache.update(instrument_id, updated_market_data)
        
        # 启动推送线程
        push_thread = threading.Thread(target=push_updated_quote)
        push_thread.start()
        
        # 记录开始等待的时间
        start_time = time.time()
        
        # 调用 wait_quote_update()（应该阻塞直到新行情到达）
        updated_quote = api.wait_quote_update(instrument_id, timeout=2.0)
        
        # 记录返回的时间
        elapsed_time = time.time() - start_time
        
        # 等待推送线程结束
        push_thread.join()
        
        # 验证 1：方法确实阻塞了（至少等待了 0.2 秒）
        assert elapsed_time >= 0.2, \
            f"wait_quote_update 应该阻塞至少 0.2 秒，实际: {elapsed_time:.3f} 秒"
        
        # 验证 2：返回的行情不为空
        assert updated_quote is not None, "wait_quote_update 应该返回 Quote 对象"
        
        # 验证 3：返回的行情合约代码正确
        assert updated_quote.InstrumentID == instrument_id, \
            f"返回的合约代码 ({updated_quote.InstrumentID}) 应该与请求的 ({instrument_id}) 一致"
        
        # 验证 4：返回的行情时间戳晚于初始时间戳
        # 比较时间字符串和毫秒
        initial_timestamp = (initial_quote.UpdateTime, initial_quote.UpdateMillisec)
        updated_timestamp = (updated_quote.UpdateTime, updated_quote.UpdateMillisec)
        
        assert updated_timestamp > initial_timestamp, \
            f"更新后的时间戳 {updated_timestamp} 应该晚于初始时间戳 {initial_timestamp}"
        
        # 验证 5：返回的行情价格是更新后的价格
        assert updated_quote.LastPrice == updated_price, \
            f"返回的价格 ({updated_quote.LastPrice}) 应该是更新后的价格 ({updated_price})"
        
        # 验证 6：返回的是新行情数据（不是初始行情）
        assert updated_quote.UpdateTime == "09:30:01", \
            "返回的行情时间应该是更新后的时间"
        assert updated_quote.UpdateMillisec == 200, \
            "返回的行情毫秒应该是更新后的毫秒"


class TestPropertyQuoteNotificationBroadcast:
    """属性测试：行情通知广播"""
    
    def test_broadcast_basic(self):
        """基本的广播测试 - 验证当前实现的限制"""
        # 创建 API 实例
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        instrument_id = "rb2505"
        
        # 手动标记为已订阅
        api._subscribed_instruments.add(instrument_id)
        
        # 用于存储各线程收到的行情
        quotes = []
        errors = []
        quotes_lock = threading.Lock()
        errors_lock = threading.Lock()
        
        def wait_for_quote():
            """等待行情更新的线程函数"""
            try:
                # 等待行情更新（较短的超时）
                quote = api.wait_quote_update(instrument_id, timeout=2.0)
                
                # 线程安全地添加到结果列表
                with quotes_lock:
                    quotes.append(quote)
                    
            except Exception as e:
                # 线程安全地添加到错误列表
                with errors_lock:
                    errors.append(e)
        
        # 启动3个等待线程
        num_waiters = 3
        wait_threads = []
        for i in range(num_waiters):
            thread = threading.Thread(target=wait_for_quote, name=f"Waiter-{i}")
            thread.start()
            wait_threads.append(thread)
        
        # 给线程一点时间进入等待状态
        time.sleep(0.3)
        
        # 推送一次行情更新
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
            'UpdateMillisec': 500
        }
        api._quote_cache.update(instrument_id, market_data)
        
        # 等待所有线程完成
        for thread in wait_threads:
            thread.join(timeout=3.0)
        
        # 验证：所有等待线程都应该收到通知
        # 这是 Property 4 的核心验证
        # 注意：当前实现只有一个线程能收到通知，所以这个断言会失败
        assert len(quotes) == num_waiters, \
            f"所有 {num_waiters} 个等待线程都应该收到行情通知，但只有 {len(quotes)} 个收到"
        
        # 验证：没有线程超时
        assert len(errors) == 0, \
            f"不应该有线程超时，但有 {len(errors)} 个线程超时"
    
    def test_quote_cache_broadcast_mechanism(self):
        """直接测试 QuoteCache 的广播机制"""
        from src.strategy.sync_api import _QuoteCache
        
        cache = _QuoteCache()
        instrument_id = "rb2505"
        
        # 用于存储各线程收到的行情
        quotes = []
        quotes_lock = threading.Lock()
        
        def wait_for_quote():
            """等待行情更新的线程函数"""
            try:
                quote = cache.wait_update(instrument_id, timeout=2.0)
                with quotes_lock:
                    quotes.append(quote)
            except TimeoutError:
                pass  # 忽略超时
        
        # 启动3个等待线程
        num_waiters = 3
        wait_threads = []
        for i in range(num_waiters):
            thread = threading.Thread(target=wait_for_quote, name=f"Waiter-{i}")
            thread.start()
            wait_threads.append(thread)
        
        # 给线程一点时间进入等待状态
        time.sleep(0.2)
        
        # 推送一次行情更新
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
            'UpdateMillisec': 500
        }
        cache.update(instrument_id, market_data)
        
        # 等待所有线程完成
        for thread in wait_threads:
            thread.join(timeout=3.0)
        
        # 验证：修复后，所有线程都应该收到通知
        assert len(quotes) == num_waiters, \
            f"所有 {num_waiters} 个线程都应该收到通知，实际收到: {len(quotes)}"
    
    # Feature: sync-strategy-api, Property 4: 行情通知广播
    @given(
        num_waiters=st.integers(min_value=2, max_value=3),
        price=st.floats(min_value=1000.0, max_value=10000.0, allow_nan=False)
    )
    @settings(max_examples=5, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])  # 只运行5个示例
    def test_property_all_waiters_receive_quote_update(
        self,
        num_waiters: int,
        price: float
    ):
        """
        **Feature: sync-strategy-api, Property 4: 行情通知广播**
        
        Property 4: 行情通知广播
        
        For any 合约的行情更新，所有等待该合约行情的策略线程都应该收到通知
        并获取到最新的行情数据。
        
        **Validates: Requirements 1.4**
        
        测试策略：
        1. 生成随机的等待线程数量和行情价格
        2. 创建多个线程，所有线程同时等待同一合约的行情更新
        3. 推送一次行情更新
        4. 验证所有线程都收到通知并获取到相同的行情数据
        """
        # 使用固定的合约代码以避免生成问题
        instrument_id = "rb2505"
        
        # 创建 API 实例
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 手动标记为已订阅
        api._subscribed_instruments.add(instrument_id)
        
        # 用于存储各线程收到的行情
        quotes = []
        errors = []
        quotes_lock = threading.Lock()
        errors_lock = threading.Lock()
        
        def wait_for_quote():
            """等待行情更新的线程函数"""
            try:
                # 等待行情更新（较短的超时）
                quote = api.wait_quote_update(instrument_id, timeout=1.5)
                
                # 线程安全地添加到结果列表
                with quotes_lock:
                    quotes.append(quote)
                    
            except Exception as e:
                # 线程安全地添加到错误列表
                with errors_lock:
                    errors.append(e)
        
        # 启动多个等待线程
        wait_threads = []
        for i in range(num_waiters):
            thread = threading.Thread(target=wait_for_quote, name=f"Waiter-{i}", daemon=True)
            thread.start()
            wait_threads.append(thread)
        
        # 给线程一点时间进入等待状态
        time.sleep(0.15)
        
        # 推送一次行情更新
        market_data = {
            'InstrumentID': instrument_id,
            'LastPrice': price,
            'BidPrice1': price - 1.0,
            'BidVolume1': 10,
            'AskPrice1': price + 1.0,
            'AskVolume1': 20,
            'Volume': 1000,
            'OpenInterest': 50000,
            'UpdateTime': '09:30:00',
            'UpdateMillisec': 500
        }
        api._quote_cache.update(instrument_id, market_data)
        
        # 等待所有线程完成
        for thread in wait_threads:
            thread.join(timeout=2.0)
        
        # 验证：所有等待线程都应该收到通知
        # 这是 Property 4 的核心验证
        assert len(quotes) == num_waiters, \
            f"所有 {num_waiters} 个等待线程都应该收到行情通知，但只有 {len(quotes)} 个收到"
        
        # 验证：没有线程超时
        assert len(errors) == 0, \
            f"不应该有线程超时，但有 {len(errors)} 个线程超时"
        
        # 验证：所有线程收到的行情数据一致
        for i, quote in enumerate(quotes):
            assert quote is not None, f"线程 {i} 收到的行情不应该为 None"
            assert quote.InstrumentID == instrument_id, \
                f"线程 {i} 收到的合约代码 ({quote.InstrumentID}) 应该与请求的 ({instrument_id}) 一致"
            assert quote.LastPrice == price, \
                f"线程 {i} 收到的价格 ({quote.LastPrice}) 应该与推送的价格 ({price}) 一致"
        
        # 验证：所有线程收到的是不同的对象（副本）
        if len(quotes) > 1:
            for i in range(len(quotes) - 1):
                for j in range(i + 1, len(quotes)):
                    # 对象应该不同（不同的内存地址）
                    assert quotes[i] is not quotes[j], \
                        f"线程 {i} 和线程 {j} 应该收到不同的 Quote 对象（副本）"
                    # 但内容应该相同
                    assert quotes[i].InstrumentID == quotes[j].InstrumentID
                    assert quotes[i].LastPrice == quotes[j].LastPrice


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
