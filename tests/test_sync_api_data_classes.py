#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : test_sync_api_data_classes.py
@Date       : 2025/12/16
@Author     : Kiro AI Assistant
@Email      : -
@Software   : PyCharm
@Description: Quote 和 Position 数据类的单元测试
"""

import math
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import pytest
from hypothesis import given, strategies as st, settings
from src.strategy.sync_api import Quote, Position, _QuoteCache, _PositionCache


class TestQuote:
    """Quote 数据类单元测试"""

    @settings(max_examples=100)
    @given(
        st.fixed_dictionaries({
            'InstrumentID': st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Nd'))),
            'LastPrice': st.floats(min_value=0.01, max_value=100000.0, allow_nan=False, allow_infinity=False),
            'BidPrice1': st.floats(min_value=0.01, max_value=100000.0, allow_nan=False, allow_infinity=False),
            'BidVolume1': st.integers(min_value=0, max_value=1000000),
            'AskPrice1': st.floats(min_value=0.01, max_value=100000.0, allow_nan=False, allow_infinity=False),
            'AskVolume1': st.integers(min_value=0, max_value=1000000),
            'Volume': st.integers(min_value=0, max_value=10000000),
            'OpenInterest': st.floats(min_value=0.0, max_value=10000000.0, allow_nan=False, allow_infinity=False),
            'UpdateTime': st.text(min_size=0, max_size=20),
            'UpdateMillisec': st.integers(min_value=0, max_value=999)
        })
    )
    def test_property_dual_access_equivalence(self, quote_data):
        """
        **Feature: sync-strategy-api, Property 14: 数据对象双重访问**
        
        属性测试：对于任何 Quote 对象，应该同时支持属性访问（quote.LastPrice）
        和字典访问（quote["LastPrice"]），且两种方式返回相同的值。
        
        **Validates: Requirements 6.1, 6.2**
        
        测试策略：
        1. 生成随机的 Quote 对象数据
        2. 创建 Quote 对象
        3. 验证所有字段的属性访问和字典访问返回相同值
        4. 验证对于所有字段，两种访问方式的结果完全一致
        """
        # 创建 Quote 对象
        quote = Quote(
            InstrumentID=quote_data['InstrumentID'],
            LastPrice=quote_data['LastPrice'],
            BidPrice1=quote_data['BidPrice1'],
            BidVolume1=quote_data['BidVolume1'],
            AskPrice1=quote_data['AskPrice1'],
            AskVolume1=quote_data['AskVolume1'],
            Volume=quote_data['Volume'],
            OpenInterest=quote_data['OpenInterest'],
            UpdateTime=quote_data['UpdateTime'],
            UpdateMillisec=quote_data['UpdateMillisec']
        )
        
        # 验证所有字段的属性访问和字典访问返回相同值
        fields_to_test = [
            'InstrumentID', 'LastPrice', 'BidPrice1', 'BidVolume1',
            'AskPrice1', 'AskVolume1', 'Volume', 'OpenInterest',
            'UpdateTime', 'UpdateMillisec'
        ]
        
        for field_name in fields_to_test:
            # 获取属性访问的值
            attr_value = getattr(quote, field_name)
            
            # 获取字典访问的值
            dict_value = quote[field_name]
            
            # 验证两种访问方式返回相同的值
            assert attr_value == dict_value, \
                f"字段 {field_name} 的属性访问和字典访问返回不同的值: " \
                f"属性访问={attr_value}, 字典访问={dict_value}"
            
            # 验证值与原始数据一致
            assert attr_value == quote_data[field_name], \
                f"字段 {field_name} 的值与原始数据不一致: " \
                f"实际值={attr_value}, 期望值={quote_data[field_name]}"

    def test_quote_attribute_access(self):
        """测试 Quote 的属性访问方式"""
        quote = Quote(
            InstrumentID="rb2505",
            LastPrice=3500.0,
            BidPrice1=3499.0,
            BidVolume1=10,
            AskPrice1=3501.0,
            AskVolume1=5,
            Volume=1000,
            OpenInterest=5000.0,
            UpdateTime="09:30:00",
            UpdateMillisec=500
        )
        
        assert quote.InstrumentID == "rb2505"
        assert quote.LastPrice == 3500.0
        assert quote.BidPrice1 == 3499.0
        assert quote.BidVolume1 == 10
        assert quote.AskPrice1 == 3501.0
        assert quote.AskVolume1 == 5
        assert quote.Volume == 1000
        assert quote.OpenInterest == 5000.0
        assert quote.UpdateTime == "09:30:00"
        assert quote.UpdateMillisec == 500

    def test_quote_dict_access(self):
        """测试 Quote 的字典访问方式"""
        quote = Quote(
            InstrumentID="rb2505",
            LastPrice=3500.0,
            BidPrice1=3499.0,
            BidVolume1=10,
            AskPrice1=3501.0,
            AskVolume1=5
        )
        
        assert quote["InstrumentID"] == "rb2505"
        assert quote["LastPrice"] == 3500.0
        assert quote["BidPrice1"] == 3499.0
        assert quote["BidVolume1"] == 10
        assert quote["AskPrice1"] == 3501.0
        assert quote["AskVolume1"] == 5

    def test_quote_attribute_and_dict_access_equivalence(self):
        """测试 Quote 的属性访问和字典访问返回相同值"""
        quote = Quote(
            InstrumentID="rb2505",
            LastPrice=3500.0,
            BidPrice1=3499.0,
            BidVolume1=10,
            AskPrice1=3501.0,
            AskVolume1=5,
            Volume=1000,
            OpenInterest=5000.0,
            UpdateTime="09:30:00"
        )
        
        # 验证所有字段的属性访问和字典访问返回相同值
        assert quote.InstrumentID == quote["InstrumentID"]
        assert quote.LastPrice == quote["LastPrice"]
        assert quote.BidPrice1 == quote["BidPrice1"]
        assert quote.BidVolume1 == quote["BidVolume1"]
        assert quote.AskPrice1 == quote["AskPrice1"]
        assert quote.AskVolume1 == quote["AskVolume1"]
        assert quote.Volume == quote["Volume"]
        assert quote.OpenInterest == quote["OpenInterest"]
        assert quote.UpdateTime == quote["UpdateTime"]

    def test_quote_invalid_price_nan(self):
        """测试 Quote 的无效价格使用 NaN 表示"""
        # 测试默认值
        quote = Quote(InstrumentID="rb2505")
        
        assert math.isnan(quote.LastPrice)
        assert math.isnan(quote.BidPrice1)
        assert math.isnan(quote.AskPrice1)
        
        # 测试显式设置 NaN
        quote_with_nan = Quote(
            InstrumentID="rb2505",
            LastPrice=float('nan'),
            BidPrice1=float('nan'),
            AskPrice1=float('nan')
        )
        
        assert math.isnan(quote_with_nan.LastPrice)
        assert math.isnan(quote_with_nan.BidPrice1)
        assert math.isnan(quote_with_nan.AskPrice1)

    def test_quote_dict_access_invalid_key(self):
        """测试 Quote 字典访问不存在的键时抛出异常"""
        quote = Quote(InstrumentID="rb2505", LastPrice=3500.0)
        
        with pytest.raises(AttributeError):
            _ = quote["NonExistentField"]

    def test_quote_default_values(self):
        """测试 Quote 的默认值初始化"""
        quote = Quote()
        
        assert quote.InstrumentID == ""
        assert math.isnan(quote.LastPrice)
        assert math.isnan(quote.BidPrice1)
        assert quote.BidVolume1 == 0
        assert math.isnan(quote.AskPrice1)
        assert quote.AskVolume1 == 0
        assert quote.Volume == 0
        assert quote.OpenInterest == 0
        assert quote.UpdateTime == ""
        assert quote.UpdateMillisec == 0
        assert quote.ctp_datetime is None


class TestPosition:
    """Position 数据类单元测试"""

    def test_position_field_initialization(self):
        """测试 Position 的字段初始化"""
        position = Position(
            pos_long=10,
            pos_long_today=5,
            pos_long_his=5,
            open_price_long=3500.0,
            pos_short=8,
            pos_short_today=3,
            pos_short_his=5,
            open_price_short=3520.0
        )
        
        assert position.pos_long == 10
        assert position.pos_long_today == 5
        assert position.pos_long_his == 5
        assert position.open_price_long == 3500.0
        assert position.pos_short == 8
        assert position.pos_short_today == 3
        assert position.pos_short_his == 5
        assert position.open_price_short == 3520.0

    def test_position_default_values(self):
        """测试 Position 的默认值"""
        position = Position()
        
        assert position.pos_long == 0
        assert position.pos_long_today == 0
        assert position.pos_long_his == 0
        assert math.isnan(position.open_price_long)
        assert position.pos_short == 0
        assert position.pos_short_today == 0
        assert position.pos_short_his == 0
        assert math.isnan(position.open_price_short)

    def test_position_custom_values(self):
        """测试 Position 的自定义值初始化"""
        position = Position(
            pos_long=20,
            pos_long_today=10,
            pos_long_his=10,
            open_price_long=3480.0
        )
        
        # 验证设置的值
        assert position.pos_long == 20
        assert position.pos_long_today == 10
        assert position.pos_long_his == 10
        assert position.open_price_long == 3480.0
        
        # 验证未设置的值使用默认值
        assert position.pos_short == 0
        assert position.pos_short_today == 0
        assert position.pos_short_his == 0
        assert math.isnan(position.open_price_short)

    def test_position_invalid_price_nan(self):
        """测试 Position 的开仓均价使用 NaN 表示无效价格"""
        # 测试默认值
        position = Position()
        assert math.isnan(position.open_price_long)
        assert math.isnan(position.open_price_short)
        
        # 测试显式设置 NaN
        position_with_nan = Position(
            pos_long=10,
            open_price_long=float('nan'),
            pos_short=5,
            open_price_short=float('nan')
        )
        assert math.isnan(position_with_nan.open_price_long)
        assert math.isnan(position_with_nan.open_price_short)
        
        # 测试部分有效价格
        position_partial = Position(
            pos_long=10,
            open_price_long=3500.0,
            pos_short=5
            # open_price_short 使用默认 NaN
        )
        assert position_partial.open_price_long == 3500.0
        assert math.isnan(position_partial.open_price_short)


class TestQuoteCacheThreadSafety:
    """QuoteCache 线程安全属性测试"""

    @settings(max_examples=100)
    @given(
        st.lists(
            st.tuples(
                st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Nd'))),  # 合约代码
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
        
        属性测试：对于任何并发访问行情或持仓缓存的操作，系统应该通过锁机制
        确保数据一致性，不会出现数据竞争或脏读。
        
        **Validates: Requirements 6.5**
        
        测试策略：
        1. 生成随机的合约代码和行情数据
        2. 使用多线程并发执行读写操作
        3. 验证所有操作都能正常完成，没有异常
        4. 验证最终数据的一致性
        """
        cache = _QuoteCache()
        exceptions = []
        results = {}
        
        def write_operation(instrument_id: str, market_data: dict):
            """写操作：更新行情缓存"""
            try:
                cache.update(instrument_id, market_data)
                # 记录最后一次写入的数据
                results[instrument_id] = market_data
            except Exception as e:
                exceptions.append(('write', instrument_id, e))
        
        def read_operation(instrument_id: str):
            """读操作：获取行情快照"""
            try:
                quote = cache.get(instrument_id)
                # 验证返回的是 Quote 对象或 None
                assert quote is None or isinstance(quote, Quote), \
                    f"get() 应该返回 Quote 对象或 None，实际返回: {type(quote)}"
                return quote
            except Exception as e:
                exceptions.append(('read', instrument_id, e))
                return None
        
        # 使用线程池执行并发操作
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            
            # 提交写操作
            for instrument_id, market_data in operations:
                future = executor.submit(write_operation, instrument_id, market_data)
                futures.append(future)
            
            # 提交读操作（与写操作交错）
            for instrument_id, _ in operations:
                future = executor.submit(read_operation, instrument_id)
                futures.append(future)
            
            # 等待所有操作完成
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    exceptions.append(('future', None, e))
        
        # 验证：不应该有任何异常
        assert len(exceptions) == 0, \
            f"并发操作中出现异常: {exceptions}"
        
        # 验证：最终数据一致性
        # 对于每个合约，验证缓存中的数据与最后一次写入的数据一致
        for instrument_id, expected_data in results.items():
            quote = cache.get(instrument_id)
            assert quote is not None, \
                f"合约 {instrument_id} 应该在缓存中"
            
            # 验证合约代码
            assert quote.InstrumentID == instrument_id, \
                f"合约代码不一致: 期望 {instrument_id}, 实际 {quote.InstrumentID}"
            
            # 验证数据字段（如果存在于 expected_data 中）
            if 'LastPrice' in expected_data:
                expected_price = expected_data['LastPrice']
                if isinstance(expected_price, (int, float)):
                    assert quote.LastPrice == expected_price, \
                        f"LastPrice 不一致: 期望 {expected_price}, 实际 {quote.LastPrice}"
            
            if 'Volume' in expected_data:
                expected_volume = expected_data['Volume']
                if isinstance(expected_volume, int):
                    assert quote.Volume == expected_volume, \
                        f"Volume 不一致: 期望 {expected_volume}, 实际 {quote.Volume}"

    def test_concurrent_same_instrument_updates(self):
        """测试同一合约的并发更新"""
        cache = _QuoteCache()
        instrument_id = "rb2505"
        num_threads = 20
        updates_per_thread = 10
        
        def update_worker(thread_id: int):
            """工作线程：多次更新同一合约"""
            for i in range(updates_per_thread):
                market_data = {
                    'LastPrice': 3500.0 + thread_id + i * 0.1,
                    'Volume': thread_id * 1000 + i,
                    'UpdateTime': f"09:30:{thread_id:02d}"
                }
                cache.update(instrument_id, market_data)
        
        # 启动多个线程并发更新
        threads = []
        for thread_id in range(num_threads):
            thread = threading.Thread(target=update_worker, args=(thread_id,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证：缓存中应该有该合约的数据
        quote = cache.get(instrument_id)
        assert quote is not None, "并发更新后缓存中应该有数据"
        assert quote.InstrumentID == instrument_id
        
        # 验证：数据应该是有效的（来自某次更新）
        assert not math.isnan(quote.LastPrice), "LastPrice 应该是有效值"
        assert quote.Volume >= 0, "Volume 应该是非负数"

    def test_concurrent_read_write_mix(self):
        """测试读写混合的并发操作"""
        cache = _QuoteCache()
        instruments = [f"rb250{i}" for i in range(5)]
        num_operations = 100
        read_count = 0
        write_count = 0
        lock = threading.Lock()
        
        def mixed_worker():
            """工作线程：随机执行读或写操作"""
            nonlocal read_count, write_count
            import random
            
            for _ in range(num_operations):
                instrument_id = random.choice(instruments)
                
                if random.random() < 0.5:
                    # 写操作
                    market_data = {
                        'LastPrice': random.uniform(3000.0, 4000.0),
                        'Volume': random.randint(0, 10000),
                        'UpdateTime': '09:30:00'
                    }
                    cache.update(instrument_id, market_data)
                    with lock:
                        write_count += 1
                else:
                    # 读操作
                    quote = cache.get(instrument_id)
                    # 验证返回值类型
                    assert quote is None or isinstance(quote, Quote)
                    with lock:
                        read_count += 1
        
        # 启动多个线程
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=mixed_worker)
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证：所有操作都已完成
        assert read_count + write_count == 10 * num_operations
        
        # 验证：缓存中应该有数据
        for instrument_id in instruments:
            quote = cache.get(instrument_id)
            # 可能有数据，也可能没有（取决于随机操作序列）
            if quote is not None:
                assert isinstance(quote, Quote)
                assert quote.InstrumentID == instrument_id


class TestPositionCacheAutoUpdate:
    """PositionCache 自动更新属性测试"""

    @settings(max_examples=100)
    @given(
        st.lists(
            st.tuples(
                st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Nd'))),  # 合约代码
                st.dictionaries(
                    keys=st.sampled_from([
                        'pos_long', 'pos_long_today', 'pos_long_his', 'open_price_long',
                        'pos_short', 'pos_short_today', 'pos_short_his', 'open_price_short'
                    ]),
                    values=st.one_of(
                        st.integers(min_value=0, max_value=1000),  # 持仓数量
                        st.floats(min_value=0.01, max_value=100000.0, allow_nan=False, allow_infinity=False)  # 价格
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
        
        测试策略：
        1. 生成随机的持仓数据更新序列
        2. 依次执行每个更新操作
        3. 验证每次更新后，get() 返回的数据与最新更新一致
        4. 验证缓存能够正确处理多次更新同一合约的情况
        """
        cache = _PositionCache()
        last_update = {}  # 记录每个合约的最后一次更新
        
        # 执行所有更新操作
        for instrument_id, position_data in updates:
            # 更新缓存
            cache.update(instrument_id, position_data)
            
            # 记录最后一次更新
            last_update[instrument_id] = position_data
            
            # 立即验证：get() 应该返回刚更新的数据
            position = cache.get(instrument_id)
            assert position is not None, \
                f"更新后应该能获取到合约 {instrument_id} 的持仓数据"
            
            # 验证数据字段（如果在更新数据中存在）
            if 'pos_long' in position_data:
                expected_value = position_data['pos_long']
                if isinstance(expected_value, int):
                    assert position.pos_long == expected_value, \
                        f"pos_long 不一致: 期望 {expected_value}, 实际 {position.pos_long}"
            
            if 'pos_long_today' in position_data:
                expected_value = position_data['pos_long_today']
                if isinstance(expected_value, int):
                    assert position.pos_long_today == expected_value, \
                        f"pos_long_today 不一致: 期望 {expected_value}, 实际 {position.pos_long_today}"
            
            if 'pos_short' in position_data:
                expected_value = position_data['pos_short']
                if isinstance(expected_value, int):
                    assert position.pos_short == expected_value, \
                        f"pos_short 不一致: 期望 {expected_value}, 实际 {position.pos_short}"
            
            if 'open_price_long' in position_data:
                expected_value = position_data['open_price_long']
                if isinstance(expected_value, (int, float)):
                    assert position.open_price_long == expected_value, \
                        f"open_price_long 不一致: 期望 {expected_value}, 实际 {position.open_price_long}"
            
            if 'open_price_short' in position_data:
                expected_value = position_data['open_price_short']
                if isinstance(expected_value, (int, float)):
                    assert position.open_price_short == expected_value, \
                        f"open_price_short 不一致: 期望 {expected_value}, 实际 {position.open_price_short}"
        
        # 最终验证：所有合约的缓存数据应该与最后一次更新一致
        for instrument_id, expected_data in last_update.items():
            position = cache.get(instrument_id)
            assert position is not None, \
                f"合约 {instrument_id} 应该在缓存中"
            
            # 验证所有字段
            for field_name in ['pos_long', 'pos_long_today', 'pos_long_his', 
                              'pos_short', 'pos_short_today', 'pos_short_his']:
                if field_name in expected_data:
                    expected_value = expected_data[field_name]
                    if isinstance(expected_value, int):
                        actual_value = getattr(position, field_name)
                        assert actual_value == expected_value, \
                            f"{field_name} 不一致: 期望 {expected_value}, 实际 {actual_value}"
            
            for field_name in ['open_price_long', 'open_price_short']:
                if field_name in expected_data:
                    expected_value = expected_data[field_name]
                    if isinstance(expected_value, (int, float)):
                        actual_value = getattr(position, field_name)
                        assert actual_value == expected_value, \
                            f"{field_name} 不一致: 期望 {expected_value}, 实际 {actual_value}"

    def test_position_cache_single_update(self):
        """测试单次持仓更新"""
        cache = _PositionCache()
        instrument_id = "rb2505"
        
        # 初始状态：缓存为空，返回空持仓对象
        position = cache.get(instrument_id)
        assert position.pos_long == 0
        assert position.pos_short == 0
        
        # 更新持仓数据
        position_data = {
            'pos_long': 10,
            'pos_long_today': 5,
            'pos_long_his': 5,
            'open_price_long': 3500.0,
            'pos_short': 0,
            'pos_short_today': 0,
            'pos_short_his': 0,
            'open_price_short': float('nan')
        }
        cache.update(instrument_id, position_data)
        
        # 验证：get() 应该返回更新后的数据
        position = cache.get(instrument_id)
        assert position.pos_long == 10
        assert position.pos_long_today == 5
        assert position.pos_long_his == 5
        assert position.open_price_long == 3500.0
        assert position.pos_short == 0

    def test_position_cache_multiple_updates(self):
        """测试多次更新同一合约"""
        cache = _PositionCache()
        instrument_id = "rb2505"
        
        # 第一次更新
        cache.update(instrument_id, {
            'pos_long': 10,
            'pos_long_today': 10,
            'open_price_long': 3500.0
        })
        
        position = cache.get(instrument_id)
        assert position.pos_long == 10
        assert position.pos_long_today == 10
        assert position.open_price_long == 3500.0
        
        # 第二次更新（增加持仓）
        cache.update(instrument_id, {
            'pos_long': 20,
            'pos_long_today': 15,
            'pos_long_his': 5,
            'open_price_long': 3480.0
        })
        
        position = cache.get(instrument_id)
        assert position.pos_long == 20
        assert position.pos_long_today == 15
        assert position.pos_long_his == 5
        assert position.open_price_long == 3480.0
        
        # 第三次更新（平仓部分）
        cache.update(instrument_id, {
            'pos_long': 15,
            'pos_long_today': 10,
            'pos_long_his': 5,
            'open_price_long': 3480.0
        })
        
        position = cache.get(instrument_id)
        assert position.pos_long == 15
        assert position.pos_long_today == 10
        assert position.pos_long_his == 5

    def test_position_cache_concurrent_updates(self):
        """测试并发更新持仓缓存"""
        cache = _PositionCache()
        instruments = [f"rb250{i}" for i in range(5)]
        num_updates_per_instrument = 20
        
        def update_worker(instrument_id: str, thread_id: int):
            """工作线程：多次更新持仓"""
            for i in range(num_updates_per_instrument):
                position_data = {
                    'pos_long': thread_id * 10 + i,
                    'pos_long_today': thread_id * 5 + i,
                    'open_price_long': 3500.0 + thread_id + i * 0.1,
                    'pos_short': thread_id * 2,
                    'open_price_short': 3520.0 + thread_id
                }
                cache.update(instrument_id, position_data)
        
        # 启动多个线程并发更新不同合约
        threads = []
        for idx, instrument_id in enumerate(instruments):
            thread = threading.Thread(target=update_worker, args=(instrument_id, idx))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证：所有合约都应该有数据
        for instrument_id in instruments:
            position = cache.get(instrument_id)
            assert position is not None
            # 验证数据有效性（应该来自某次更新）
            assert position.pos_long >= 0
            assert position.pos_short >= 0
            assert not math.isnan(position.open_price_long)

    def test_position_cache_partial_update(self):
        """测试部分字段更新"""
        cache = _PositionCache()
        instrument_id = "rb2505"
        
        # 第一次更新：只更新多头持仓
        cache.update(instrument_id, {
            'pos_long': 10,
            'pos_long_today': 10,
            'open_price_long': 3500.0
        })
        
        position = cache.get(instrument_id)
        assert position.pos_long == 10
        assert position.pos_short == 0  # 未更新的字段应该是默认值
        
        # 第二次更新：只更新空头持仓
        cache.update(instrument_id, {
            'pos_short': 5,
            'pos_short_today': 5,
            'open_price_short': 3520.0
        })
        
        position = cache.get(instrument_id)
        # 注意：这次更新会覆盖整个 Position 对象
        # 所以之前的多头持仓数据会丢失（变回默认值）
        assert position.pos_long == 0  # 被重置为默认值
        assert position.pos_short == 5
        assert position.pos_short_today == 5
        assert position.open_price_short == 3520.0

    def test_position_cache_empty_update(self):
        """测试空数据更新"""
        cache = _PositionCache()
        instrument_id = "rb2505"
        
        # 更新空数据
        cache.update(instrument_id, {})
        
        # 验证：应该创建一个默认的 Position 对象
        position = cache.get(instrument_id)
        assert position.pos_long == 0
        assert position.pos_short == 0
        assert math.isnan(position.open_price_long)
        assert math.isnan(position.open_price_short)

    def test_position_cache_get_nonexistent(self):
        """测试获取不存在的合约持仓"""
        cache = _PositionCache()
        
        # 获取不存在的合约
        position = cache.get("NONEXISTENT")
        
        # 验证：应该返回空持仓对象
        assert position is not None
        assert position.pos_long == 0
        assert position.pos_short == 0
        assert math.isnan(position.open_price_long)
        assert math.isnan(position.open_price_short)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
