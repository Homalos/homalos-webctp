#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : test_td_client_cache_integration.py
@Date       : 2025/12/15
@Author     : Kiro Agent
@Software   : PyCharm
@Description: TdClient 缓存集成测试
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from hypothesis import given, strategies as st, settings
import fakeredis.aioredis
from src.services.td_client import TdClient
from src.services.cache_manager import CacheManager
from src.constants import TdConstant as Constant


@pytest.fixture
def mock_cache_manager():
    """创建模拟的 CacheManager"""
    cache = MagicMock(spec=CacheManager)
    cache.is_available.return_value = True
    cache.hset = AsyncMock(return_value=True)
    cache.set = AsyncMock(return_value=True)
    cache.zadd = AsyncMock(return_value=1)
    return cache


@pytest.fixture
async def real_cache_manager():
    """创建真实的 CacheManager 用于属性测试"""
    
    # 使用 fakeredis 创建真实的 Redis 实例
    fake_redis = fakeredis.aioredis.FakeRedis()
    
    cache = CacheManager()
    cache._redis = fake_redis
    cache._available = True
    
    yield cache
    
    # 清理
    await fake_redis.flushall()
    await fake_redis.aclose()


@pytest.fixture
def td_client_with_cache(mock_cache_manager):
    """创建带缓存的 TdClient 实例"""
    with patch("src.services.td_client.CTPTdClient"):
        client = TdClient()
        client.set_cache_manager(mock_cache_manager)
        client._user_id = "test_user"
        return client


@pytest.fixture
async def td_client_with_real_cache(real_cache_manager):
    """创建带真实缓存的 TdClient 实例用于属性测试"""
    with patch("src.services.td_client.CTPTdClient"):
        client = TdClient()
        client.set_cache_manager(real_cache_manager)
        client._user_id = "test_user"
        yield client


# ============================================================================
# Hypothesis 策略定义
# ============================================================================

# 持仓数据策略
position_strategy = st.fixed_dictionaries({
    "InstrumentID": st.text(min_size=1, max_size=31, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    "Position": st.integers(min_value=0, max_value=1000000),
    "Direction": st.sampled_from(["0", "1", "2", "3"]),  # 买、卖、净、空
    "YdPosition": st.integers(min_value=0, max_value=1000000),
    "TodayPosition": st.integers(min_value=0, max_value=1000000),
    "PositionCost": st.floats(min_value=0, max_value=1000000000, allow_nan=False, allow_infinity=False),
})

# 资金数据策略
account_strategy = st.fixed_dictionaries({
    "Balance": st.floats(min_value=0, max_value=1000000000, allow_nan=False, allow_infinity=False),
    "Available": st.floats(min_value=0, max_value=1000000000, allow_nan=False, allow_infinity=False),
    "WithdrawQuota": st.floats(min_value=0, max_value=1000000000, allow_nan=False, allow_infinity=False),
    "Credit": st.floats(min_value=0, max_value=1000000000, allow_nan=False, allow_infinity=False),
    "Mortgage": st.floats(min_value=0, max_value=1000000000, allow_nan=False, allow_infinity=False),
})

# 订单数据策略
order_strategy = st.fixed_dictionaries({
    "OrderRef": st.text(min_size=1, max_size=13, alphabet=st.characters(whitelist_categories=('Nd',))),
    "OrderSysID": st.text(min_size=1, max_size=21, alphabet=st.characters(whitelist_categories=('Nd',))),
    "InstrumentID": st.text(min_size=1, max_size=31, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    "Direction": st.sampled_from(["0", "1"]),  # 买、卖
    "OrderStatus": st.sampled_from(["0", "1", "2", "3", "4", "5"]),
    "VolumeTotalOriginal": st.integers(min_value=1, max_value=1000),
    "VolumeTraded": st.integers(min_value=0, max_value=1000),
})


@pytest.mark.asyncio
async def test_cache_position_data(td_client_with_cache, mock_cache_manager):
    """测试持仓数据缓存"""
    position_data = {
        Constant.MessageType: Constant.OnRspQryInvestorPosition,
        Constant.InvestorPosition: {
            "InstrumentID": "cu2501",
            "Position": 10,
            "Direction": "0"
        }
    }

    await td_client_with_cache._cache_position_data(position_data)

    # 验证 hset 被调用
    mock_cache_manager.hset.assert_awaited_once()
    call_args = mock_cache_manager.hset.call_args
    assert "account:position:test_user" in call_args[0][0]
    assert "cu2501" == call_args[0][1]


@pytest.mark.asyncio
async def test_cache_account_data(td_client_with_cache, mock_cache_manager):
    """测试资金数据缓存"""
    account_data = {
        Constant.MessageType: Constant.OnRspQryTradingAccount,
        Constant.TradingAccount: {
            "Balance": 100000.0,
            "Available": 50000.0
        }
    }

    await td_client_with_cache._cache_account_data(account_data)

    # 验证 set 被调用
    mock_cache_manager.set.assert_awaited_once()
    call_args = mock_cache_manager.set.call_args
    assert "account:funds:test_user" in call_args[0][0]


@pytest.mark.asyncio
async def test_cache_order_data(td_client_with_cache, mock_cache_manager):
    """测试订单数据缓存"""
    order_data = {
        Constant.MessageType: Constant.OnRtnOrder,
        Constant.Order: {
            "OrderRef": "000001",
            "OrderSysID": "12345",
            "InstrumentID": "cu2501"
        }
    }

    await td_client_with_cache._cache_order_data(order_data)

    # 验证 zadd 被调用
    mock_cache_manager.zadd.assert_awaited_once()
    call_args = mock_cache_manager.zadd.call_args
    assert "account:orders:test_user" in call_args[0][0]


@pytest.mark.asyncio
async def test_cache_degradation_when_unavailable(td_client_with_cache, mock_cache_manager):
    """测试 Redis 不可用时的降级处理"""
    # 模拟 Redis 不可用
    mock_cache_manager.is_available.return_value = False

    position_data = {
        Constant.MessageType: Constant.OnRspQryInvestorPosition,
        Constant.InvestorPosition: {
            "InstrumentID": "cu2501",
            "Position": 10
        }
    }

    # 应该不抛出异常
    await td_client_with_cache._cache_position_data(position_data)

    # 验证 hset 没有被调用
    mock_cache_manager.hset.assert_not_awaited()


@pytest.mark.asyncio
async def test_on_rsp_or_rtn_with_position_data(td_client_with_cache):
    """测试 on_rsp_or_rtn 方法处理持仓数据"""
    position_data = {
        Constant.MessageType: Constant.OnRspQryInvestorPosition,
        Constant.InvestorPosition: {
            "InstrumentID": "cu2501",
            "Position": 10
        }
    }

    # Mock 父类方法
    with patch.object(TdClient.__bases__[0], 'on_rsp_or_rtn') as mock_super:
        td_client_with_cache.on_rsp_or_rtn(position_data)

        # 验证父类方法被调用（消息正常推送）
        mock_super.assert_called_once_with(position_data)


@pytest.mark.asyncio
async def test_cache_without_user_id(mock_cache_manager):
    """测试没有设置 user_id 时的处理"""
    with patch("src.services.td_client.CTPTdClient"):
        client = TdClient()
        client.set_cache_manager(mock_cache_manager)
        # 不设置 user_id

        position_data = {
            Constant.MessageType: Constant.OnRspQryInvestorPosition,
            Constant.InvestorPosition: {
                "InstrumentID": "cu2501",
                "Position": 10
            }
        }

        # 应该不抛出异常
        await client._cache_position_data(position_data)

        # 验证 hset 没有被调用
        mock_cache_manager.hset.assert_not_awaited()


@pytest.mark.asyncio
async def test_query_position_cached_single_instrument(td_client_with_cache, mock_cache_manager):
    """测试查询单个合约的持仓缓存"""
    from src.utils.serialization import get_msgpack_serializer
    
    serializer = get_msgpack_serializer()
    position_data = {
        "InstrumentID": "cu2501",
        "Position": 10,
        "Direction": "0"
    }
    serialized_data = serializer.serialize(position_data)
    
    # 模拟 Redis 返回数据
    mock_cache_manager.hget = AsyncMock(return_value=serialized_data)
    
    result = await td_client_with_cache.query_position_cached("cu2501")
    
    # 验证结果
    assert result is not None
    assert result["InstrumentID"] == "cu2501"
    assert result["Position"] == 10
    
    # 验证 hget 被调用
    mock_cache_manager.hget.assert_awaited_once()
    call_args = mock_cache_manager.hget.call_args
    assert "account:position:test_user" in call_args[0][0]
    assert "cu2501" == call_args[0][1]


@pytest.mark.asyncio
async def test_query_position_cached_all_instruments(td_client_with_cache, mock_cache_manager):
    """测试查询所有合约的持仓缓存"""
    from src.utils.serialization import get_msgpack_serializer
    
    serializer = get_msgpack_serializer()
    position_data_1 = {"InstrumentID": "cu2501", "Position": 10}
    position_data_2 = {"InstrumentID": "au2506", "Position": 5}
    
    # 模拟 Redis 返回所有持仓数据
    mock_cache_manager.hgetall = AsyncMock(return_value={
        b"cu2501": serializer.serialize(position_data_1),
        b"au2506": serializer.serialize(position_data_2)
    })
    
    result = await td_client_with_cache.query_position_cached()
    
    # 验证结果
    assert result is not None
    assert len(result) == 2
    assert "cu2501" in result
    assert "au2506" in result
    assert result["cu2501"]["Position"] == 10
    assert result["au2506"]["Position"] == 5
    
    # 验证 hgetall 被调用
    mock_cache_manager.hgetall.assert_awaited_once()


@pytest.mark.asyncio
async def test_query_position_cached_not_found(td_client_with_cache, mock_cache_manager):
    """测试查询不存在的持仓缓存"""
    # 模拟 Redis 返回 None
    mock_cache_manager.hget = AsyncMock(return_value=None)
    
    result = await td_client_with_cache.query_position_cached("cu2501")
    
    # 验证结果为 None
    assert result is None


@pytest.mark.asyncio
async def test_query_account_cached(td_client_with_cache, mock_cache_manager):
    """测试查询资金账户缓存"""
    from src.utils.serialization import get_msgpack_serializer
    
    serializer = get_msgpack_serializer()
    account_data = {
        "Balance": 100000.0,
        "Available": 50000.0
    }
    serialized_data = serializer.serialize(account_data)
    
    # 模拟 Redis 返回数据
    mock_cache_manager.get = AsyncMock(return_value=serialized_data)
    
    result = await td_client_with_cache.query_account_cached()
    
    # 验证结果
    assert result is not None
    assert result["Balance"] == 100000.0
    assert result["Available"] == 50000.0
    
    # 验证 get 被调用
    mock_cache_manager.get.assert_awaited_once()
    call_args = mock_cache_manager.get.call_args
    assert "account:funds:test_user" in call_args[0][0]


@pytest.mark.asyncio
async def test_query_account_cached_not_found(td_client_with_cache, mock_cache_manager):
    """测试查询不存在的资金账户缓存"""
    # 模拟 Redis 返回 None
    mock_cache_manager.get = AsyncMock(return_value=None)
    
    result = await td_client_with_cache.query_account_cached()
    
    # 验证结果为 None
    assert result is None


@pytest.mark.asyncio
async def test_query_orders_cached(td_client_with_cache, mock_cache_manager):
    """测试查询订单缓存"""
    from src.utils.serialization import get_msgpack_serializer
    
    serializer = get_msgpack_serializer()
    order_data_1 = {"OrderRef": "000001", "InstrumentID": "cu2501"}
    order_data_2 = {"OrderRef": "000002", "InstrumentID": "au2506"}
    
    serialized_1 = serializer.serialize(order_data_1)
    serialized_2 = serializer.serialize(order_data_2)
    
    # 模拟 Redis 返回订单数据（Sorted Set 格式）
    member_1 = f"000001:{serialized_1.hex()}".encode('utf-8')
    member_2 = f"000002:{serialized_2.hex()}".encode('utf-8')
    
    mock_cache_manager.zrange = AsyncMock(return_value=[member_1, member_2])
    
    result = await td_client_with_cache.query_orders_cached()
    
    # 验证结果（应该是倒序）
    assert len(result) == 2
    assert result[0]["OrderRef"] == "000002"  # 最新的在前
    assert result[1]["OrderRef"] == "000001"
    
    # 验证 zrange 被调用
    mock_cache_manager.zrange.assert_awaited_once()


@pytest.mark.asyncio
async def test_query_orders_cached_empty(td_client_with_cache, mock_cache_manager):
    """测试查询空的订单缓存"""
    # 模拟 Redis 返回空列表
    mock_cache_manager.zrange = AsyncMock(return_value=[])
    
    result = await td_client_with_cache.query_orders_cached()
    
    # 验证结果为空列表
    assert result == []


@pytest.mark.asyncio
async def test_refresh_cache(td_client_with_cache, mock_cache_manager):
    """测试刷新缓存"""
    # 模拟 Redis 删除操作成功
    mock_cache_manager.delete = AsyncMock(return_value=True)
    
    result = await td_client_with_cache.refresh_cache()
    
    # 验证结果
    assert result["position_cleared"] is True
    assert result["account_cleared"] is True
    assert result["orders_cleared"] is True
    
    # 验证 delete 被调用 3 次
    assert mock_cache_manager.delete.await_count == 3


@pytest.mark.asyncio
async def test_refresh_cache_redis_unavailable(td_client_with_cache, mock_cache_manager):
    """测试 Redis 不可用时刷新缓存"""
    # 模拟 Redis 不可用
    mock_cache_manager.is_available.return_value = False
    
    result = await td_client_with_cache.refresh_cache()
    
    # 验证结果全部为 False
    assert result["position_cleared"] is False
    assert result["account_cleared"] is False
    assert result["orders_cleared"] is False


@pytest.mark.asyncio
async def test_query_cached_methods_without_user_id(mock_cache_manager):
    """测试没有设置 user_id 时查询缓存方法的处理"""
    with patch("src.services.td_client.CTPTdClient"):
        client = TdClient()
        client.set_cache_manager(mock_cache_manager)
        # 不设置 user_id
        
        # 测试查询持仓
        result = await client.query_position_cached("cu2501")
        assert result is None
        
        # 测试查询资金
        result = await client.query_account_cached()
        assert result is None
        
        # 测试查询订单
        result = await client.query_orders_cached()
        assert result == []
        
        # 测试刷新缓存
        result = await client.refresh_cache()
        assert result["position_cleared"] is False
        assert result["account_cleared"] is False
        assert result["orders_cleared"] is False



# ============================================================================
# 属性测试（Property-Based Testing）
# ============================================================================


@settings(max_examples=100)
@given(position_data=position_strategy)
@pytest.mark.asyncio
async def test_property_position_cache_consistency(position_data):
    """
    **Feature: performance-optimization-phase1, Property 1: 缓存一致性**
    
    属性测试：对于任何持仓数据更新，当数据写入 Redis 缓存后，从缓存读取应该返回相同的数据
    
    验证需求：4.1, 4.4
    """
    # 创建真实的 Redis 实例
    fake_redis = fakeredis.aioredis.FakeRedis()
    cache = CacheManager()
    cache._redis = fake_redis
    cache._available = True
    
    # 创建 TdClient 实例
    with patch("src.services.td_client.CTPTdClient"):
        client = TdClient()
        client.set_cache_manager(cache)
        client._user_id = "test_user"
        
        # 构造完整的持仓消息
        position_message = {
            Constant.MessageType: Constant.OnRspQryInvestorPosition,
            Constant.InvestorPosition: position_data
        }
        
        # 写入缓存
        await client._cache_position_data(position_message)
        
        # 从缓存读取
        instrument_id = position_data["InstrumentID"]
        cached_data = await client.query_position_cached(instrument_id)
        
        # 验证一致性
        assert cached_data is not None, f"缓存数据不应为空: instrument_id={instrument_id}"
        
        # 验证关键字段
        assert cached_data["InstrumentID"] == position_data["InstrumentID"], \
            f"InstrumentID 不一致: 原始={position_data['InstrumentID']}, 缓存={cached_data['InstrumentID']}"
        assert cached_data["Position"] == position_data["Position"], \
            f"Position 不一致: 原始={position_data['Position']}, 缓存={cached_data['Position']}"
        assert cached_data["Direction"] == position_data["Direction"], \
            f"Direction 不一致: 原始={position_data['Direction']}, 缓存={cached_data['Direction']}"
        
        # 验证所有字段
        for key, value in position_data.items():
            assert key in cached_data, f"缓存中缺少字段: {key}"
            assert cached_data[key] == value, \
                f"字段 {key} 不一致: 原始={value}, 缓存={cached_data[key]}"
    
    # 清理
    await fake_redis.flushall()
    await fake_redis.aclose()



@settings(max_examples=100)
@given(account_data=account_strategy)
@pytest.mark.asyncio
async def test_property_account_cache_consistency(account_data):
    """
    **Feature: performance-optimization-phase1, Property 1: 缓存一致性**
    
    属性测试：对于任何资金数据更新，当数据写入 Redis 缓存后，从缓存读取应该返回相同的数据
    
    验证需求：4.2, 4.4
    """
    # 创建真实的 Redis 实例
    fake_redis = fakeredis.aioredis.FakeRedis()
    cache = CacheManager()
    cache._redis = fake_redis
    cache._available = True
    
    # 创建 TdClient 实例
    with patch("src.services.td_client.CTPTdClient"):
        client = TdClient()
        client.set_cache_manager(cache)
        client._user_id = "test_user"
        
        # 构造完整的资金消息
        account_message = {
            Constant.MessageType: Constant.OnRspQryTradingAccount,
            Constant.TradingAccount: account_data
        }
        
        # 写入缓存
        await client._cache_account_data(account_message)
        
        # 从缓存读取
        cached_data = await client.query_account_cached()
        
        # 验证一致性
        assert cached_data is not None, "缓存数据不应为空"
        
        # 验证关键字段
        assert cached_data["Balance"] == account_data["Balance"], \
            f"Balance 不一致: 原始={account_data['Balance']}, 缓存={cached_data['Balance']}"
        assert cached_data["Available"] == account_data["Available"], \
            f"Available 不一致: 原始={account_data['Available']}, 缓存={cached_data['Available']}"
        
        # 验证所有字段
        for key, value in account_data.items():
            assert key in cached_data, f"缓存中缺少字段: {key}"
            # 对于浮点数，使用近似比较
            if isinstance(value, float):
                assert abs(cached_data[key] - value) < 1e-6, \
                    f"字段 {key} 不一致: 原始={value}, 缓存={cached_data[key]}"
            else:
                assert cached_data[key] == value, \
                    f"字段 {key} 不一致: 原始={value}, 缓存={cached_data[key]}"
    
    # 清理
    await fake_redis.flushall()
    await fake_redis.aclose()



@settings(max_examples=100)
@given(order_data=order_strategy)
@pytest.mark.asyncio
async def test_property_order_cache_consistency(order_data):
    """
    **Feature: performance-optimization-phase1, Property 1: 缓存一致性**
    
    属性测试：对于任何订单数据更新，当数据写入 Redis 缓存后，从缓存读取应该返回相同的数据
    
    验证需求：4.3, 4.4
    """
    # 创建真实的 Redis 实例
    fake_redis = fakeredis.aioredis.FakeRedis()
    cache = CacheManager()
    cache._redis = fake_redis
    cache._available = True
    
    # 创建 TdClient 实例
    with patch("src.services.td_client.CTPTdClient"):
        client = TdClient()
        client.set_cache_manager(cache)
        client._user_id = "test_user"
        
        # 构造完整的订单消息
        order_message = {
            Constant.MessageType: Constant.OnRtnOrder,
            Constant.Order: order_data
        }
        
        # 写入缓存
        await client._cache_order_data(order_message)
        
        # 从缓存读取（获取最新的订单）
        cached_orders = await client.query_orders_cached()
        
        # 验证一致性
        assert len(cached_orders) > 0, "缓存中应该有订单数据"
        
        # 获取最新的订单（第一个）
        cached_data = cached_orders[0]
        
        # 验证关键字段
        assert cached_data["OrderRef"] == order_data["OrderRef"], \
            f"OrderRef 不一致: 原始={order_data['OrderRef']}, 缓存={cached_data['OrderRef']}"
        assert cached_data["InstrumentID"] == order_data["InstrumentID"], \
            f"InstrumentID 不一致: 原始={order_data['InstrumentID']}, 缓存={cached_data['InstrumentID']}"
        assert cached_data["Direction"] == order_data["Direction"], \
            f"Direction 不一致: 原始={order_data['Direction']}, 缓存={cached_data['Direction']}"
        
        # 验证所有字段
        for key, value in order_data.items():
            assert key in cached_data, f"缓存中缺少字段: {key}"
            assert cached_data[key] == value, \
                f"字段 {key} 不一致: 原始={value}, 缓存={cached_data[key]}"
    
    # 清理
    await fake_redis.flushall()
    await fake_redis.aclose()
