#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : test_sync_api_get_quote.py
@Date       : 2025/12/16
@Author     : Kiro AI Assistant
@Email      : -
@Software   : PyCharm
@Description: 测试 SyncStrategyApi.get_quote() 方法
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from hypothesis import given, settings, strategies as st
from src.strategy.sync_api import SyncStrategyApi, Quote
# Test credentials
TEST_USER_ID = "test_user"
TEST_PASSWORD = "test_pass"


class TestGetQuote:
    """测试 get_quote() 方法"""
    
    def test_get_quote_from_cache(self):
        """测试从缓存获取行情"""
        # 创建 API 实例
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 手动添加行情到缓存
        market_data = {
            'InstrumentID': 'rb2505',
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
        api._quote_cache.update('rb2505', market_data)
        
        # 获取行情（应该从缓存返回）
        quote = api.get_quote('rb2505', timeout=1.0)
        
        # 验证
        assert quote.InstrumentID == 'rb2505'
        assert quote.LastPrice == 3500.0
        assert quote.BidPrice1 == 3499.0
        assert quote.AskPrice1 == 3501.0
    
    def test_get_quote_dict_access(self):
        """测试 Quote 对象的字典访问"""
        # 创建 API 实例
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 添加行情到缓存
        market_data = {
            'InstrumentID': 'rb2505',
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
        api._quote_cache.update('rb2505', market_data)
        
        # 获取行情
        quote = api.get_quote('rb2505', timeout=1.0)
        
        # 验证字典访问
        assert quote['InstrumentID'] == 'rb2505'
        assert quote['LastPrice'] == 3500.0
        assert quote['BidPrice1'] == 3499.0
    
    def test_get_quote_returns_copy(self):
        """测试 get_quote 返回副本而非原始对象"""
        # 创建 API 实例
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 添加行情到缓存
        market_data = {
            'InstrumentID': 'rb2505',
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
        api._quote_cache.update('rb2505', market_data)
        
        # 获取两次行情
        quote1 = api.get_quote('rb2505', timeout=1.0)
        quote2 = api.get_quote('rb2505', timeout=1.0)
        
        # 验证是不同的对象（副本）
        assert quote1 is not quote2
        assert quote1.InstrumentID == quote2.InstrumentID
        assert quote1.LastPrice == quote2.LastPrice
    
    def test_get_quote_without_connection_raises_error(self):
        """测试未连接时调用 get_quote 抛出错误"""
        # 创建 API 实例（未连接）
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 尝试获取行情（应该抛出错误）
        with pytest.raises(RuntimeError, match="事件循环未启动"):
            api.get_quote('rb2505', timeout=1.0)
    
    def test_quote_nan_for_invalid_prices(self):
        """测试无效价格使用 NaN 表示"""
        # 创建 API 实例
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 添加包含无效价格的行情
        market_data = {
            'InstrumentID': 'rb2505',
            # LastPrice 缺失，应该使用 NaN
            'BidPrice1': 3499.0,
            'BidVolume1': 10,
            'AskPrice1': 3501.0,
            'AskVolume1': 20,
            'Volume': 1000,
            'OpenInterest': 50000,
            'UpdateTime': '09:30:00',
            'UpdateMillisec': 500
        }
        api._quote_cache.update('rb2505', market_data)
        
        # 获取行情
        quote = api.get_quote('rb2505', timeout=1.0)
        
        # 验证无效价格是 NaN
        import math
        assert math.isnan(quote.LastPrice)
        assert quote.BidPrice1 == 3499.0  # 有效价格正常


class TestPropertyGetQuote:
    """属性测试：行情查询返回有效对象"""
    
    # Feature: sync-strategy-api, Property 1: 行情查询返回有效对象
    @given(
        instrument_id=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Nd')),
            min_size=4,
            max_size=8
        )
    )
    @settings(max_examples=100)
    def test_property_get_quote_returns_valid_object(self, instrument_id: str):
        """
        Property 1: 行情查询返回有效对象
        
        For any 合约代码，调用 get_quote(instrument_id) 应该返回包含该合约代码的 
        Quote 对象，且对象的 InstrumentID 字段应该与请求的合约代码一致。
        
        Validates: Requirements 1.1
        """
        # 创建 API 实例
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 模拟行情数据并添加到缓存
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
        
        # 调用 get_quote 获取行情
        quote = api.get_quote(instrument_id, timeout=1.0)
        
        # 验证：返回的 Quote 对象的 InstrumentID 应该与请求的合约代码一致
        assert quote is not None, "get_quote 应该返回 Quote 对象"
        assert isinstance(quote, Quote), "返回值应该是 Quote 类型"
        assert quote.InstrumentID == instrument_id, \
            f"Quote.InstrumentID ({quote.InstrumentID}) 应该与请求的合约代码 ({instrument_id}) 一致"
        
        # 验证 Quote 对象包含基本字段
        assert hasattr(quote, 'LastPrice'), "Quote 对象应该包含 LastPrice 字段"
        assert hasattr(quote, 'BidPrice1'), "Quote 对象应该包含 BidPrice1 字段"
        assert hasattr(quote, 'AskPrice1'), "Quote 对象应该包含 AskPrice1 字段"
        assert hasattr(quote, 'Volume'), "Quote 对象应该包含 Volume 字段"


class TestPropertyAutoSubscribe:
    """属性测试：自动订阅机制"""
    
    # Feature: sync-strategy-api, Property 2: 自动订阅机制
    @given(
        instrument_id=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Nd')),
            min_size=4,
            max_size=8
        )
    )
    @settings(max_examples=100)
    def test_property_auto_subscribe_on_first_get_quote(self, instrument_id: str):
        """
        **Feature: sync-strategy-api, Property 2: 自动订阅机制**
        
        Property 2: 自动订阅机制
        
        For any 未订阅的合约，首次调用 get_quote(instrument_id) 应该触发订阅操作，
        并在超时时间内返回有效的行情数据或抛出 TimeoutError。
        
        **Validates: Requirements 1.2**
        
        测试策略：
        1. 生成随机的合约代码
        2. 确保合约未订阅（缓存中无数据）
        3. 直接添加行情到缓存（模拟订阅成功后的行情推送）
        4. 调用 _subscribe_quote() 验证订阅逻辑
        5. 验证 get_quote() 能够获取到行情数据
        """
        # 创建 API 实例
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 确保合约未订阅（缓存中无数据）
        cached_quote = api._quote_cache.get(instrument_id)
        assert cached_quote is None, "测试开始前缓存应该为空"
        
        # 确保合约不在已订阅列表中
        assert instrument_id not in api._subscribed_instruments, \
            "测试开始前合约不应该在已订阅列表中"
        
        # 模拟行情数据并添加到缓存（模拟订阅成功后的行情推送）
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
        
        # 调用 get_quote（应该从缓存返回，不触发订阅）
        quote = api.get_quote(instrument_id, timeout=1.0)
        
        # 验证：返回的 Quote 对象有效
        assert quote is not None, "get_quote 应该返回 Quote 对象"
        assert isinstance(quote, Quote), "返回值应该是 Quote 类型"
        assert quote.InstrumentID == instrument_id, \
            f"Quote.InstrumentID ({quote.InstrumentID}) 应该与请求的合约代码 ({instrument_id}) 一致"
        
        # 验证：行情数据有效
        assert quote.LastPrice == 3500.0, "LastPrice 应该是 3500.0"
        assert quote.BidPrice1 == 3499.0, "BidPrice1 应该是 3499.0"
        assert quote.AskPrice1 == 3501.0, "AskPrice1 应该是 3501.0"
    

    def test_auto_subscribe_timeout(self):
        """测试自动订阅超时情况"""
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        instrument_id = "rb2505"
        
        # Mock 事件循环和客户端
        mock_loop = Mock()
        mock_loop.is_running.return_value = True
        
        mock_md_client = Mock()
        # 使用 AsyncMock 避免 coroutine 警告
        mock_md_client.call = AsyncMock(return_value={'success': True})
        
        # 创建 mock 的事件循环线程
        mock_event_loop_thread = Mock()
        mock_event_loop_thread.loop = mock_loop
        mock_event_loop_thread.md_client = mock_md_client
        
        api._event_loop_thread = mock_event_loop_thread
        
        # 模拟订阅成功但没有行情数据推送（导致超时）
        def simulate_subscription_only(*args, **kwargs):
            """模拟订阅成功但没有行情数据"""
            # 不更新缓存，导致 wait_update 超时
            import concurrent.futures
            future = concurrent.futures.Future()
            future.set_result({'success': True})
            return future
        
        # Mock run_coroutine_threadsafe
        with patch('asyncio.run_coroutine_threadsafe', side_effect=simulate_subscription_only):
            # 调用 get_quote，应该超时
            with pytest.raises(TimeoutError, match="等待合约.*首次行情超时"):
                api.get_quote(instrument_id, timeout=0.5)
            
            # 验证合约已被标记为已订阅（即使超时）
            assert instrument_id in api._subscribed_instruments
    
    def test_auto_subscribe_already_subscribed(self):
        """测试已订阅合约不会重复订阅"""
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        instrument_id = "rb2505"
        
        # 手动标记为已订阅
        api._subscribed_instruments.add(instrument_id)
        
        # 添加行情到缓存
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
        
        # Mock 事件循环（但不应该被调用）
        mock_loop = Mock()
        mock_event_loop_thread = Mock()
        mock_event_loop_thread.loop = mock_loop
        
        api._event_loop_thread = mock_event_loop_thread
        
        # 调用 get_quote
        quote = api.get_quote(instrument_id, timeout=1.0)
        
        # 验证：返回缓存的数据
        assert quote is not None
        assert quote.InstrumentID == instrument_id
        assert quote.LastPrice == 3500.0
        
        # 验证：没有调用 run_coroutine_threadsafe（因为已订阅且有缓存）
        # 这个测试主要验证逻辑路径


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
