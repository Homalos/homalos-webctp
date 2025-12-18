#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : test_sync_api_get_position.py
@Date       : 2025/12/16
@Author     : Kiro AI Assistant
@Email      : -
@Software   : PyCharm
@Description: get_position() 方法的属性测试
"""

import math
import asyncio
import threading
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import pytest
from hypothesis import given, strategies as st, settings
from src.strategy.sync_api import SyncStrategyApi, Position
# Test credentials
TEST_USER_ID = "test_user"
TEST_PASSWORD = "test_pass"


# 生成合约代码的策略
instrument_ids = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Nd')),
    min_size=4,
    max_size=8
)

# 生成持仓数据的策略
# 注意：确保至少有一个方向有持仓（多头或空头），避免生成全为 0 的持仓数据
# 因为全为 0 的持仓会被 get_position() 认为是缓存未命中，触发查询
@st.composite
def position_data_with_holdings(draw):
    """生成至少有一个方向有持仓的持仓数据"""
    # 随机选择是否有多头持仓
    has_long = draw(st.booleans())
    # 随机选择是否有空头持仓
    has_short = draw(st.booleans())
    
    # 确保至少有一个方向有持仓
    if not has_long and not has_short:
        has_long = True
    
    # 生成多头持仓数据
    if has_long:
        pos_long = draw(st.integers(min_value=1, max_value=1000))
        pos_long_today = draw(st.integers(min_value=0, max_value=pos_long))
        pos_long_his = pos_long - pos_long_today
        open_price_long = draw(st.floats(min_value=0.01, max_value=100000.0, allow_nan=False, allow_infinity=False))
    else:
        pos_long = 0
        pos_long_today = 0
        pos_long_his = 0
        open_price_long = float('nan')
    
    # 生成空头持仓数据
    if has_short:
        pos_short = draw(st.integers(min_value=1, max_value=1000))
        pos_short_today = draw(st.integers(min_value=0, max_value=pos_short))
        pos_short_his = pos_short - pos_short_today
        open_price_short = draw(st.floats(min_value=0.01, max_value=100000.0, allow_nan=False, allow_infinity=False))
    else:
        pos_short = 0
        pos_short_today = 0
        pos_short_his = 0
        open_price_short = float('nan')
    
    return {
        'pos_long': pos_long,
        'pos_long_today': pos_long_today,
        'pos_long_his': pos_long_his,
        'open_price_long': open_price_long,
        'pos_short': pos_short,
        'pos_short_today': pos_short_today,
        'pos_short_his': pos_short_his,
        'open_price_short': open_price_short,
    }

position_data_strategy = position_data_with_holdings()


class TestGetPositionProperty:
    """get_position() 方法的属性测试"""

    @settings(max_examples=100)
    @given(
        instrument_id=instrument_ids,
        position_data=position_data_strategy
    )
    def test_property_get_position_returns_valid_object(self, instrument_id, position_data):
        """
        **Feature: sync-strategy-api, Property 5: 持仓查询返回有效对象**
        
        属性测试：对于任何合约代码，调用 get_position(instrument_id) 应该返回 Position 对象，
        且对象包含多空持仓数量、今昨仓、开仓均价等关键字段。
        
        **Validates: Requirements 2.1, 2.5**
        
        测试策略：
        1. 生成随机合约代码和持仓数据
        2. Mock CTP 客户端和事件循环
        3. 模拟持仓查询响应
        4. 验证返回的 Position 对象包含所有必需字段
        5. 验证字段类型和值的正确性
        """
        # 创建 SyncStrategyApi 实例（不连接 CTP）
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # Mock 事件循环线程
        mock_event_loop_thread = Mock()
        mock_loop = Mock()
        mock_td_client = Mock()
        
        # 配置 mock 对象
        mock_event_loop_thread.loop = mock_loop
        mock_event_loop_thread.td_client = mock_td_client
        
        # 设置事件循环线程
        api._event_loop_thread = mock_event_loop_thread
        
        # 预先在缓存中设置持仓数据（模拟查询成功）
        api._position_cache.update(instrument_id, position_data)
        
        # 调用 get_position()
        position = api.get_position(instrument_id, timeout=5.0)
        
        # 验证：返回的应该是 Position 对象
        assert isinstance(position, Position), \
            f"get_position() 应该返回 Position 对象，实际返回: {type(position)}"
        
        # 验证：Position 对象包含所有必需字段
        # 1. 多头持仓字段
        assert hasattr(position, 'pos_long'), "Position 对象应该包含 pos_long 字段"
        assert hasattr(position, 'pos_long_today'), "Position 对象应该包含 pos_long_today 字段"
        assert hasattr(position, 'pos_long_his'), "Position 对象应该包含 pos_long_his 字段"
        assert hasattr(position, 'open_price_long'), "Position 对象应该包含 open_price_long 字段"
        
        # 2. 空头持仓字段
        assert hasattr(position, 'pos_short'), "Position 对象应该包含 pos_short 字段"
        assert hasattr(position, 'pos_short_today'), "Position 对象应该包含 pos_short_today 字段"
        assert hasattr(position, 'pos_short_his'), "Position 对象应该包含 pos_short_his 字段"
        assert hasattr(position, 'open_price_short'), "Position 对象应该包含 open_price_short 字段"
        
        # 验证：字段类型正确
        assert isinstance(position.pos_long, int), \
            f"pos_long 应该是 int 类型，实际: {type(position.pos_long)}"
        assert isinstance(position.pos_long_today, int), \
            f"pos_long_today 应该是 int 类型，实际: {type(position.pos_long_today)}"
        assert isinstance(position.pos_long_his, int), \
            f"pos_long_his 应该是 int 类型，实际: {type(position.pos_long_his)}"
        assert isinstance(position.open_price_long, float), \
            f"open_price_long 应该是 float 类型，实际: {type(position.open_price_long)}"
        
        assert isinstance(position.pos_short, int), \
            f"pos_short 应该是 int 类型，实际: {type(position.pos_short)}"
        assert isinstance(position.pos_short_today, int), \
            f"pos_short_today 应该是 int 类型，实际: {type(position.pos_short_today)}"
        assert isinstance(position.pos_short_his, int), \
            f"pos_short_his 应该是 int 类型，实际: {type(position.pos_short_his)}"
        assert isinstance(position.open_price_short, float), \
            f"open_price_short 应该是 float 类型，实际: {type(position.open_price_short)}"
        
        # 验证：字段值与预期一致
        assert position.pos_long == position_data['pos_long'], \
            f"pos_long 不一致: 期望 {position_data['pos_long']}, 实际 {position.pos_long}"
        assert position.pos_long_today == position_data['pos_long_today'], \
            f"pos_long_today 不一致: 期望 {position_data['pos_long_today']}, 实际 {position.pos_long_today}"
        assert position.pos_long_his == position_data['pos_long_his'], \
            f"pos_long_his 不一致: 期望 {position_data['pos_long_his']}, 实际 {position.pos_long_his}"
        
        # 对于浮点数价格字段，需要特殊处理 NaN 的比较
        expected_long_price = position_data['open_price_long']
        if math.isnan(expected_long_price):
            assert math.isnan(position.open_price_long), \
                f"open_price_long 应该是 NaN，实际: {position.open_price_long}"
        else:
            assert position.open_price_long == expected_long_price, \
                f"open_price_long 不一致: 期望 {expected_long_price}, 实际 {position.open_price_long}"
        
        assert position.pos_short == position_data['pos_short'], \
            f"pos_short 不一致: 期望 {position_data['pos_short']}, 实际 {position.pos_short}"
        assert position.pos_short_today == position_data['pos_short_today'], \
            f"pos_short_today 不一致: 期望 {position_data['pos_short_today']}, 实际 {position.pos_short_today}"
        assert position.pos_short_his == position_data['pos_short_his'], \
            f"pos_short_his 不一致: 期望 {position_data['pos_short_his']}, 实际 {position.pos_short_his}"
        
        # 对于浮点数价格字段，需要特殊处理 NaN 的比较
        expected_short_price = position_data['open_price_short']
        if math.isnan(expected_short_price):
            assert math.isnan(position.open_price_short), \
                f"open_price_short 应该是 NaN，实际: {position.open_price_short}"
        else:
            assert position.open_price_short == expected_short_price, \
                f"open_price_short 不一致: 期望 {expected_short_price}, 实际 {position.open_price_short}"
        
        # 验证：持仓数量应该是非负数
        assert position.pos_long >= 0, "pos_long 应该是非负数"
        assert position.pos_long_today >= 0, "pos_long_today 应该是非负数"
        assert position.pos_long_his >= 0, "pos_long_his 应该是非负数"
        assert position.pos_short >= 0, "pos_short 应该是非负数"
        assert position.pos_short_today >= 0, "pos_short_today 应该是非负数"
        assert position.pos_short_his >= 0, "pos_short_his 应该是非负数"
        
        # 验证：开仓均价的有效性（根据持仓情况）
        # 如果有多头持仓，开仓均价应该是有效的正数
        if position.pos_long > 0:
            assert not math.isnan(position.open_price_long), \
                "open_price_long 不应该是 NaN（在有多头持仓的情况下）"
            assert not math.isinf(position.open_price_long), \
                "open_price_long 不应该是 Inf"
            assert position.open_price_long > 0, \
                f"open_price_long 应该是正数，实际: {position.open_price_long}"
        
        # 如果有空头持仓，开仓均价应该是有效的正数
        if position.pos_short > 0:
            assert not math.isnan(position.open_price_short), \
                "open_price_short 不应该是 NaN（在有空头持仓的情况下）"
            assert not math.isinf(position.open_price_short), \
                "open_price_short 不应该是 Inf"
            assert position.open_price_short > 0, \
                f"open_price_short 应该是正数，实际: {position.open_price_short}"

    def test_get_position_returns_empty_position_for_nonexistent_instrument(self):
        """测试查询不存在的合约返回空持仓对象"""
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # Mock 事件循环线程
        mock_event_loop_thread = Mock()
        mock_loop = Mock()
        mock_td_client = Mock()
        
        mock_event_loop_thread.loop = mock_loop
        mock_event_loop_thread.td_client = mock_td_client
        
        api._event_loop_thread = mock_event_loop_thread
        
        # 查询不存在的合约（缓存中没有数据）
        # 由于没有真实的 CTP 连接，查询会超时并返回空持仓
        position = api.get_position("NONEXISTENT", timeout=0.1)
        
        # 验证：应该返回 Position 对象
        assert isinstance(position, Position)
        
        # 验证：应该是空持仓（所有字段为默认值）
        assert position.pos_long == 0
        assert position.pos_short == 0
        assert position.pos_long_today == 0
        assert position.pos_short_today == 0
        assert position.pos_long_his == 0
        assert position.pos_short_his == 0
        assert math.isnan(position.open_price_long)
        assert math.isnan(position.open_price_short)

    def test_get_position_returns_cached_position(self):
        """测试 get_position() 返回缓存的持仓数据"""
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        instrument_id = "rb2505"
        
        # 预先在缓存中设置持仓数据
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
        api._position_cache.update(instrument_id, position_data)
        
        # Mock 事件循环线程（但不应该被调用，因为缓存命中）
        mock_event_loop_thread = Mock()
        api._event_loop_thread = mock_event_loop_thread
        
        # 调用 get_position()
        position = api.get_position(instrument_id)
        
        # 验证：返回的是 Position 对象
        assert isinstance(position, Position)
        
        # 验证：数据与缓存一致
        assert position.pos_long == 10
        assert position.pos_long_today == 5
        assert position.pos_long_his == 5
        assert position.open_price_long == 3500.0
        assert position.pos_short == 0

    def test_get_position_with_zero_position(self):
        """测试持仓为零的情况"""
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        instrument_id = "rb2505"
        
        # 设置持仓为零的数据
        position_data = {
            'pos_long': 0,
            'pos_long_today': 0,
            'pos_long_his': 0,
            'open_price_long': float('nan'),
            'pos_short': 0,
            'pos_short_today': 0,
            'pos_short_his': 0,
            'open_price_short': float('nan')
        }
        api._position_cache.update(instrument_id, position_data)
        
        # Mock 事件循环线程
        mock_event_loop_thread = Mock()
        mock_loop = Mock()
        mock_td_client = Mock()
        
        mock_event_loop_thread.loop = mock_loop
        mock_event_loop_thread.td_client = mock_td_client
        
        api._event_loop_thread = mock_event_loop_thread
        
        # 调用 get_position()
        # 注意：由于持仓为零，会触发查询（因为缓存被认为是"未命中"）
        # 但查询会超时，返回空持仓
        position = api.get_position(instrument_id, timeout=0.1)
        
        # 验证：返回的是 Position 对象
        assert isinstance(position, Position)
        
        # 验证：所有持仓字段为零
        assert position.pos_long == 0
        assert position.pos_short == 0
        assert position.pos_long_today == 0
        assert position.pos_short_today == 0
        assert position.pos_long_his == 0
        assert position.pos_short_his == 0

    def test_get_position_with_only_long_position(self):
        """测试只有多头持仓的情况"""
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        instrument_id = "rb2505"
        
        # 设置只有多头持仓的数据
        position_data = {
            'pos_long': 20,
            'pos_long_today': 10,
            'pos_long_his': 10,
            'open_price_long': 3480.0,
            'pos_short': 0,
            'pos_short_today': 0,
            'pos_short_his': 0,
            'open_price_short': float('nan')
        }
        api._position_cache.update(instrument_id, position_data)
        
        # Mock 事件循环线程
        mock_event_loop_thread = Mock()
        api._event_loop_thread = mock_event_loop_thread
        
        # 调用 get_position()
        position = api.get_position(instrument_id)
        
        # 验证：多头持仓数据正确
        assert position.pos_long == 20
        assert position.pos_long_today == 10
        assert position.pos_long_his == 10
        assert position.open_price_long == 3480.0
        
        # 验证：空头持仓为零
        assert position.pos_short == 0
        assert position.pos_short_today == 0
        assert position.pos_short_his == 0
        assert math.isnan(position.open_price_short)

    def test_get_position_with_only_short_position(self):
        """测试只有空头持仓的情况"""
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        instrument_id = "rb2505"
        
        # 设置只有空头持仓的数据
        position_data = {
            'pos_long': 0,
            'pos_long_today': 0,
            'pos_long_his': 0,
            'open_price_long': float('nan'),
            'pos_short': 15,
            'pos_short_today': 8,
            'pos_short_his': 7,
            'open_price_short': 3520.0
        }
        api._position_cache.update(instrument_id, position_data)
        
        # Mock 事件循环线程
        mock_event_loop_thread = Mock()
        api._event_loop_thread = mock_event_loop_thread
        
        # 调用 get_position()
        position = api.get_position(instrument_id)
        
        # 验证：空头持仓数据正确
        assert position.pos_short == 15
        assert position.pos_short_today == 8
        assert position.pos_short_his == 7
        assert position.open_price_short == 3520.0
        
        # 验证：多头持仓为零
        assert position.pos_long == 0
        assert position.pos_long_today == 0
        assert position.pos_long_his == 0
        assert math.isnan(position.open_price_long)

    def test_get_position_with_both_long_and_short(self):
        """测试同时有多空持仓的情况"""
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        instrument_id = "rb2505"
        
        # 设置多空持仓数据
        position_data = {
            'pos_long': 10,
            'pos_long_today': 5,
            'pos_long_his': 5,
            'open_price_long': 3500.0,
            'pos_short': 8,
            'pos_short_today': 3,
            'pos_short_his': 5,
            'open_price_short': 3520.0
        }
        api._position_cache.update(instrument_id, position_data)
        
        # Mock 事件循环线程
        mock_event_loop_thread = Mock()
        api._event_loop_thread = mock_event_loop_thread
        
        # 调用 get_position()
        position = api.get_position(instrument_id)
        
        # 验证：多头持仓数据正确
        assert position.pos_long == 10
        assert position.pos_long_today == 5
        assert position.pos_long_his == 5
        assert position.open_price_long == 3500.0
        
        # 验证：空头持仓数据正确
        assert position.pos_short == 8
        assert position.pos_short_today == 3
        assert position.pos_short_his == 5
        assert position.open_price_short == 3520.0

    @settings(max_examples=100)
    @given(
        instrument_id=instrument_ids
    )
    def test_property_cache_miss_triggers_query(self, instrument_id):
        """
        **Feature: sync-strategy-api, Property 6: 持仓缓存未命中触发查询**
        
        属性测试：对于任何未缓存的合约，调用 get_position(instrument_id) 应该触发 CTP 查询，
        并在超时时间内返回持仓数据或返回空持仓对象。
        
        **Validates: Requirements 2.2, 2.3**
        
        测试策略：
        1. 生成随机合约代码
        2. 确保缓存中没有该合约的持仓数据（缓存未命中）
        3. Mock CTP 查询方法
        4. 调用 get_position()
        5. 验证触发了 CTP 查询
        6. 验证返回了持仓对象（可能是空持仓）
        """
        # 创建 SyncStrategyApi 实例
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # Mock 事件循环线程和相关组件
        mock_event_loop_thread = Mock()
        mock_loop = Mock()
        mock_td_client = Mock()
        
        # 配置 mock 对象
        mock_event_loop_thread.loop = mock_loop
        mock_event_loop_thread.td_client = mock_td_client
        
        # 设置事件循环线程
        api._event_loop_thread = mock_event_loop_thread
        
        # 确保缓存中没有该合约的持仓数据
        # 不调用 _position_cache.update()，保持缓存为空
        
        # Mock _query_position 方法来模拟查询行为
        query_called = threading.Event()
        original_query = api._query_position
        
        def mock_query_position(inst_id: str, timeout: float = 5.0):
            """Mock 查询方法：记录调用并模拟查询成功"""
            query_called.set()
            # 模拟查询成功，更新缓存（可能返回空持仓）
            # 这里模拟查询到空持仓的情况
            api._position_cache.update(inst_id, {
                'pos_long': 0,
                'pos_long_today': 0,
                'pos_long_his': 0,
                'open_price_long': float('nan'),
                'pos_short': 0,
                'pos_short_today': 0,
                'pos_short_his': 0,
                'open_price_short': float('nan')
            })
        
        # 替换 _query_position 方法
        api._query_position = mock_query_position
        
        # 调用 get_position()
        position = api.get_position(instrument_id, timeout=5.0)
        
        # 验证 1：应该触发了 CTP 查询
        assert query_called.is_set(), \
            f"缓存未命中时应该触发 CTP 查询，但没有调用 _query_position()"
        
        # 验证 2：应该返回 Position 对象
        assert isinstance(position, Position), \
            f"get_position() 应该返回 Position 对象，实际返回: {type(position)}"
        
        # 验证 3：返回的持仓对象应该包含所有必需字段
        assert hasattr(position, 'pos_long'), "Position 对象应该包含 pos_long 字段"
        assert hasattr(position, 'pos_short'), "Position 对象应该包含 pos_short 字段"
        assert hasattr(position, 'pos_long_today'), "Position 对象应该包含 pos_long_today 字段"
        assert hasattr(position, 'pos_short_today'), "Position 对象应该包含 pos_short_today 字段"
        assert hasattr(position, 'pos_long_his'), "Position 对象应该包含 pos_long_his 字段"
        assert hasattr(position, 'pos_short_his'), "Position 对象应该包含 pos_short_his 字段"
        assert hasattr(position, 'open_price_long'), "Position 对象应该包含 open_price_long 字段"
        assert hasattr(position, 'open_price_short'), "Position 对象应该包含 open_price_short 字段"
        
        # 验证 4：字段类型正确
        assert isinstance(position.pos_long, int), "pos_long 应该是 int 类型"
        assert isinstance(position.pos_short, int), "pos_short 应该是 int 类型"
        assert isinstance(position.open_price_long, float), "open_price_long 应该是 float 类型"
        assert isinstance(position.open_price_short, float), "open_price_short 应该是 float 类型"
        
        # 验证 5：持仓数量应该是非负数
        assert position.pos_long >= 0, "pos_long 应该是非负数"
        assert position.pos_short >= 0, "pos_short 应该是非负数"
        assert position.pos_long_today >= 0, "pos_long_today 应该是非负数"
        assert position.pos_short_today >= 0, "pos_short_today 应该是非负数"
        assert position.pos_long_his >= 0, "pos_long_his 应该是非负数"
        assert position.pos_short_his >= 0, "pos_short_his 应该是非负数"

    def test_cache_miss_triggers_query_with_timeout(self):
        """测试缓存未命中触发查询，查询超时返回空持仓"""
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        instrument_id = "rb2505"
        
        # Mock 事件循环线程
        mock_event_loop_thread = Mock()
        mock_loop = Mock()
        mock_td_client = Mock()
        
        mock_event_loop_thread.loop = mock_loop
        mock_event_loop_thread.td_client = mock_td_client
        
        api._event_loop_thread = mock_event_loop_thread
        
        # Mock _query_position 方法，模拟查询超时
        def mock_query_timeout(inst_id: str, timeout: float = 5.0):
            """Mock 查询方法：抛出 TimeoutError"""
            raise TimeoutError(f"查询超时")
        
        api._query_position = mock_query_timeout
        
        # 调用 get_position()，应该捕获超时异常并返回空持仓
        position = api.get_position(instrument_id, timeout=0.1)
        
        # 验证：应该返回空持仓对象（不抛出异常）
        assert isinstance(position, Position)
        assert position.pos_long == 0
        assert position.pos_short == 0
        assert math.isnan(position.open_price_long)
        assert math.isnan(position.open_price_short)

    def test_cache_miss_triggers_query_with_error(self):
        """测试缓存未命中触发查询，查询失败返回空持仓"""
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        instrument_id = "rb2505"
        
        # Mock 事件循环线程
        mock_event_loop_thread = Mock()
        mock_loop = Mock()
        mock_td_client = Mock()
        
        mock_event_loop_thread.loop = mock_loop
        mock_event_loop_thread.td_client = mock_td_client
        
        api._event_loop_thread = mock_event_loop_thread
        
        # Mock _query_position 方法，模拟查询失败
        def mock_query_error(inst_id: str, timeout: float = 5.0):
            """Mock 查询方法：抛出 RuntimeError"""
            raise RuntimeError("查询失败")
        
        api._query_position = mock_query_error
        
        # 调用 get_position()，应该捕获异常并返回空持仓
        position = api.get_position(instrument_id, timeout=0.1)
        
        # 验证：应该返回空持仓对象（不抛出异常）
        assert isinstance(position, Position)
        assert position.pos_long == 0
        assert position.pos_short == 0
        assert math.isnan(position.open_price_long)
        assert math.isnan(position.open_price_short)

    def test_cache_miss_triggers_query_success(self):
        """测试缓存未命中触发查询，查询成功返回持仓数据"""
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        instrument_id = "rb2505"
        
        # Mock 事件循环线程
        mock_event_loop_thread = Mock()
        mock_loop = Mock()
        mock_td_client = Mock()
        
        mock_event_loop_thread.loop = mock_loop
        mock_event_loop_thread.td_client = mock_td_client
        
        api._event_loop_thread = mock_event_loop_thread
        
        # Mock _query_position 方法，模拟查询成功
        def mock_query_success(inst_id: str, timeout: float = 5.0):
            """Mock 查询方法：模拟查询成功，更新缓存"""
            api._position_cache.update(inst_id, {
                'pos_long': 15,
                'pos_long_today': 10,
                'pos_long_his': 5,
                'open_price_long': 3500.0,
                'pos_short': 0,
                'pos_short_today': 0,
                'pos_short_his': 0,
                'open_price_short': float('nan')
            })
        
        api._query_position = mock_query_success
        
        # 调用 get_position()
        position = api.get_position(instrument_id, timeout=5.0)
        
        # 验证：应该返回查询到的持仓数据
        assert isinstance(position, Position)
        assert position.pos_long == 15
        assert position.pos_long_today == 10
        assert position.pos_long_his == 5
        assert position.open_price_long == 3500.0
        assert position.pos_short == 0

    def test_cache_hit_does_not_trigger_query(self):
        """测试缓存命中时不触发查询"""
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        instrument_id = "rb2505"
        
        # 预先在缓存中设置持仓数据
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
        api._position_cache.update(instrument_id, position_data)
        
        # Mock 事件循环线程
        mock_event_loop_thread = Mock()
        api._event_loop_thread = mock_event_loop_thread
        
        # Mock _query_position 方法，记录是否被调用
        query_called = threading.Event()
        
        def mock_query_should_not_call(inst_id: str, timeout: float = 5.0):
            """Mock 查询方法：不应该被调用"""
            query_called.set()
        
        api._query_position = mock_query_should_not_call
        
        # 调用 get_position()
        position = api.get_position(instrument_id, timeout=5.0)
        
        # 验证：不应该触发查询
        assert not query_called.is_set(), \
            "缓存命中时不应该触发 CTP 查询"
        
        # 验证：返回的是缓存中的数据
        assert position.pos_long == 10
        assert position.pos_long_today == 5
        assert position.pos_long_his == 5
        assert position.open_price_long == 3500.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
