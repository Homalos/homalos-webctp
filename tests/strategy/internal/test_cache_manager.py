#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : test_cache_manager.py
@Date       : 2025/12/20
@Author     : Kiro AI Assistant
@Email      : -
@Software   : PyCharm
@Description: _CacheManager、_QuoteCache、_PositionCache 的单元测试
"""

import math
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import pytest
from hypothesis import given, strategies as st, settings
from src.strategy.internal.cache_manager import _CacheManager, _QuoteCache, _PositionCache
from src.strategy.internal.data_models import Quote, Position


class TestCacheManager:
    """_CacheManager 基类单元测试"""

    def test_initialization(self):
        """测试 _CacheManager 初始化"""
        cache = _CacheManager()
        
        assert cache._cache == {}
        assert cache._lock is not None

    def test_get_empty_cache(self):
        """测试从空缓存获取数据"""
        cache = _CacheManager()
        
        result = cache.get("nonexistent_key")
        assert result is None

    def test_update_and_get(self):
        """测试更新和获取数据"""
        cache = _CacheManager()
        
        cache.update("test_key", "test_value")
        result = cache.get("test_key")
        
        assert result == "test_value"

    def test_clear(self):
        """测试清空缓存"""
        cache = _CacheManager()
        
        cache.update("key1", "value1")
        cache.update("key2", "value2")
        
        cache.clear()
        
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_keys(self):
        """测试获取所有键"""
        cache = _CacheManager()
        
        cache.update("key1", "value1")
        cache.update("key2", "value2")
        cache.update("key3", "value3")
        
        keys = cache.keys()
        
        assert len(keys) == 3
        assert "key1" in keys
        assert "key2" in keys
        assert "key3" in keys

    def test_thread_safety(self):
        """测试线程安全性"""
        cache = _CacheManager()
        exceptions = []
        
        def worker(thread_id: int):
            try:
                for i in range(100):
                    key = f"key_{thread_id}_{i}"
                    cache.update(key, f"value_{thread_id}_{i}")
                    result = cache.get(key)
                    assert result == f"value_{thread_id}_{i}"
            except Exception as e:
                exceptions.append(e)
        
        threads = []
        for i in range(10):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        assert len(exceptions) == 0


class TestQuoteCache:
    """_QuoteCache 类单元测试"""

    def test_initialization(self):
        """测试 _QuoteCache 初始化"""
        cache = _QuoteCache()
        
        assert cache._cache == {}
        assert cache._lock is not None
        assert cache._quote_queues == {}

    def test_get_empty_cache_returns_none(self):
        """测试从空缓存获取行情返回 None"""
        cache = _QuoteCache()
        
        result = cache.get("rb2505")
        assert result is None

    def test_update_from_market_data(self, sample_market_data):
        """测试从市场数据更新缓存"""
        cache = _QuoteCache()
        instrument_id = "rb2505"
        
        cache.update_from_market_data(instrument_id, sample_market_data)
        
        quote = cache.get(instrument_id)
        assert quote is not None
        assert isinstance(quote, Quote)
        assert quote.InstrumentID == instrument_id
        assert quote.LastPrice == sample_market_data['LastPrice']
        assert quote.Volume == sample_market_data['Volume']

    def test_update_multiple_instruments(self, sample_market_data):
        """测试更新多个合约"""
        cache = _QuoteCache()
        
        instruments = ["rb2505", "rb2506", "rb2507"]
        
        for instrument_id in instruments:
            cache.update_from_market_data(instrument_id, sample_market_data)
        
        for instrument_id in instruments:
            quote = cache.get(instrument_id)
            assert quote is not None
            assert quote.InstrumentID == instrument_id

    def test_clear_cache(self, sample_market_data):
        """测试清空缓存"""
        cache = _QuoteCache()
        
        cache.update_from_market_data("rb2505", sample_market_data)
        cache.update_from_market_data("rb2506", sample_market_data)
        
        cache.clear()
        
        assert cache.get("rb2505") is None
        assert cache.get("rb2506") is None

    @settings(max_examples=100)
    @given(
        st.lists(
            st.tuples(
                st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Nd'))),
                st.dictionaries(
                    keys=st.sampled_from(['LastPrice', 'BidPrice1', 'AskPrice1', 'Volume', 'OpenInterest', 'UpdateTime']),
                    values=st.one_of(
                        st.floats(min_value=0.01, max_value=100000.0, allow_nan=False, allow_infinity=False),
                        st.integers(min_value=0, max_value=1000000),
                        st.text(min_size=0, max_size=20)
                    ),
                    min_size=1,
                    max_size=6
                )
            ),
            min_size=5,
            max_size=20
        )
    )
    def test_property_thread_safe_concurrent_access(self, operations):
        """
        **Feature: sync-strategy-api, Property 15: 线程安全数据访问**
        
        属性测试：对于任何并发访问行情缓存的操作，系统应该通过锁机制
        确保数据一致性，不会出现数据竞争或脏读。
        
        **Validates: Requirements 6.5**
        """
        cache = _QuoteCache()
        exceptions = []
        results = {}
        
        def write_operation(instrument_id: str, market_data: dict):
            try:
                cache.update_from_market_data(instrument_id, market_data)
                results[instrument_id] = market_data
            except Exception as e:
                exceptions.append(('write', instrument_id, e))
        
        def read_operation(instrument_id: str):
            try:
                quote = cache.get(instrument_id)
                assert quote is None or isinstance(quote, Quote)
                return quote
            except Exception as e:
                exceptions.append(('read', instrument_id, e))
                return None
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            
            for instrument_id, market_data in operations:
                future = executor.submit(write_operation, instrument_id, market_data)
                futures.append(future)
            
            for instrument_id, _ in operations:
                future = executor.submit(read_operation, instrument_id)
                futures.append(future)
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    exceptions.append(('future', None, e))
        
        assert len(exceptions) == 0, f"并发操作中出现异常: {exceptions}"
        
        for instrument_id, expected_data in results.items():
            quote = cache.get(instrument_id)
            assert quote is not None
            assert quote.InstrumentID == instrument_id


class TestPositionCache:
    """_PositionCache 类单元测试"""

    def test_initialization(self):
        """测试 _PositionCache 初始化"""
        cache = _PositionCache()
        
        assert cache._cache == {}
        assert cache._lock is not None

    def test_get_empty_cache_returns_empty_position(self):
        """测试从空缓存获取持仓返回空持仓对象"""
        cache = _PositionCache()
        
        position = cache.get("rb2505")
        assert position is not None
        assert isinstance(position, Position)
        assert position.pos_long == 0
        assert position.pos_short == 0

    def test_update_from_position_data(self, sample_position_data):
        """测试从持仓数据更新缓存"""
        cache = _PositionCache()
        instrument_id = "rb2505"
        
        cache.update_from_position_data(instrument_id, sample_position_data)
        
        position = cache.get(instrument_id)
        assert position is not None
        assert isinstance(position, Position)
        assert position.pos_long == sample_position_data['pos_long']
        assert position.pos_short == sample_position_data['pos_short']

    @settings(max_examples=100)
    @given(
        st.lists(
            st.tuples(
                st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Nd'))),
                st.dictionaries(
                    keys=st.sampled_from([
                        'pos_long', 'pos_long_today', 'pos_long_his', 'open_price_long',
                        'pos_short', 'pos_short_today', 'pos_short_his', 'open_price_short'
                    ]),
                    values=st.one_of(
                        st.integers(min_value=0, max_value=1000),
                        st.floats(min_value=0.01, max_value=100000.0, allow_nan=False, allow_infinity=False)
                    ),
                    min_size=1,
                    max_size=8
                )
            ),
            min_size=1,
            max_size=50
        )
    )
    def test_property_position_cache_auto_update(self, updates):
        """
        **Feature: sync-strategy-api, Property 7: 持仓缓存自动更新**
        
        属性测试：对于任何持仓数据更新回报，系统应该自动更新内部缓存，
        后续的 get_position() 调用应该返回更新后的数据。
        
        **Validates: Requirements 2.4**
        """
        cache = _PositionCache()
        last_update = {}
        
        for instrument_id, position_data in updates:
            cache.update_from_position_data(instrument_id, position_data)
            last_update[instrument_id] = position_data
            
            position = cache.get(instrument_id)
            assert position is not None
            
            if 'pos_long' in position_data:
                expected_value = position_data['pos_long']
                if isinstance(expected_value, int):
                    assert position.pos_long == expected_value
            
            if 'pos_short' in position_data:
                expected_value = position_data['pos_short']
                if isinstance(expected_value, int):
                    assert position.pos_short == expected_value

    def test_clear_cache(self, sample_position_data):
        """测试清空缓存"""
        cache = _PositionCache()
        
        cache.update_from_position_data("rb2505", sample_position_data)
        cache.update_from_position_data("rb2506", sample_position_data)
        
        cache.clear()
        
        # 清空后应该返回空持仓对象
        position = cache.get("rb2505")
        assert position.pos_long == 0
        assert position.pos_short == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
