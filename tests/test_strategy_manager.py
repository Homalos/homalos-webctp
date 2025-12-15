#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : test_strategy_manager.py
@Date       : 2025/12/15 00:00
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: StrategyManager 单元测试和属性测试
"""

import pytest
import pytest_asyncio
import asyncio
from unittest.mock import patch
from hypothesis import given, strategies as st, settings
import fakeredis.aioredis

from src.services.strategy_manager import (
    StrategyManager,
    StrategyConfig,
    StrategyStatus,
    StrategyInfo,
)
from src.services.cache_manager import CacheManager
from src.utils.config import CacheConfig
from src.utils.serialization import get_msgpack_serializer


# ============================================================================
# Fixtures
# ============================================================================


@pytest_asyncio.fixture
async def fake_redis_server():
    """创建 fakeredis 服务器实例"""
    server = fakeredis.FakeServer()
    yield server
    # 清理
    server.connected = False


@pytest_asyncio.fixture
async def cache_manager_with_fake_redis(fake_redis_server):
    """创建使用 fakeredis 的 CacheManager 实例"""
    cache_config = CacheConfig(
        enabled=True,
        host="localhost",
        port=6379,
        db=0,
        max_connections=10,
        socket_timeout=5.0,
    )
    
    cache_manager = CacheManager()
    
    # 使用 fakeredis 替换真实的 Redis 连接
    with patch('src.services.cache_manager.Redis') as mock_redis_class:
        fake_redis = fakeredis.aioredis.FakeRedis(server=fake_redis_server, decode_responses=False)
        mock_redis_class.return_value = fake_redis
        
        await cache_manager.initialize(cache_config)
        
        # 手动设置 redis 实例为 fakeredis
        cache_manager._redis = fake_redis
        
        yield cache_manager
        
        # 清理
        await cache_manager.close()


@pytest_asyncio.fixture
async def strategy_manager(cache_manager_with_fake_redis):
    """创建 StrategyManager 实例"""
    manager = StrategyManager(
        cache_manager=cache_manager_with_fake_redis,
        max_strategies=5
    )
    yield manager
    
    # 清理：停止所有运行中的策略
    for strategy_id in list(manager._strategies.keys()):
        if manager._strategies[strategy_id].status == StrategyStatus.RUNNING:
            await manager.stop_strategy(strategy_id)


@pytest.fixture
def sample_strategy_config():
    """创建示例策略配置"""
    return StrategyConfig(
        strategy_id="test_strategy_1",
        name="测试策略1",
        enabled=True,
        subscribed_instruments=["rb2505", "au2506"],
        error_threshold=3,
    )


@pytest.fixture
def serializer():
    """创建 msgpack 序列化器"""
    return get_msgpack_serializer()


# ============================================================================
# TestStrategyManagerRegistration - 策略注册和注销测试
# ============================================================================


class TestStrategyManagerRegistration:
    """StrategyManager 策略注册和注销测试"""

    @pytest.mark.asyncio
    async def test_register_strategy_success(self, strategy_manager, sample_strategy_config):
        """测试成功注册策略"""
        async def test_strategy(market_data: dict):
            pass
        
        result = await strategy_manager.register_strategy(
            "test_strategy_1",
            test_strategy,
            sample_strategy_config
        )
        
        assert result is True
        assert "test_strategy_1" in strategy_manager._strategies
        assert strategy_manager._strategies["test_strategy_1"].status == StrategyStatus.REGISTERED

    @pytest.mark.asyncio
    async def test_register_duplicate_strategy(self, strategy_manager, sample_strategy_config):
        """测试重复注册失败"""
        async def test_strategy(market_data: dict):
            pass
        
        # 第一次注册
        await strategy_manager.register_strategy(
            "test_strategy_1",
            test_strategy,
            sample_strategy_config
        )
        
        # 第二次注册相同ID应该失败
        result = await strategy_manager.register_strategy(
            "test_strategy_1",
            test_strategy,
            sample_strategy_config
        )
        
        assert result is False

    @pytest.mark.asyncio
    async def test_register_exceeds_max_strategies(self, strategy_manager):
        """测试达到最大策略数量限制"""
        async def test_strategy(market_data: dict):
            pass
        
        # 注册最大数量的策略（5个）
        for i in range(5):
            config = StrategyConfig(
                strategy_id=f"strategy_{i}",
                name=f"策略{i}",
                subscribed_instruments=["rb2505"],
            )
            result = await strategy_manager.register_strategy(
                f"strategy_{i}",
                test_strategy,
                config
            )
            assert result is True
        
        # 尝试注册第6个策略应该失败
        config = StrategyConfig(
            strategy_id="strategy_6",
            name="策略6",
            subscribed_instruments=["rb2505"],
        )
        result = await strategy_manager.register_strategy(
            "strategy_6",
            test_strategy,
            config
        )
        
        assert result is False

    @pytest.mark.asyncio
    async def test_register_non_async_function(self, strategy_manager, sample_strategy_config):
        """测试注册非异步函数失败"""
        def sync_strategy(market_data: dict):
            pass
        
        result = await strategy_manager.register_strategy(
            "test_strategy_1",
            sync_strategy,
            sample_strategy_config
        )
        
        assert result is False

    @pytest.mark.asyncio
    async def test_unregister_strategy_success(self, strategy_manager, sample_strategy_config):
        """测试成功注销策略"""
        async def test_strategy(market_data: dict):
            pass
        
        # 先注册
        await strategy_manager.register_strategy(
            "test_strategy_1",
            test_strategy,
            sample_strategy_config
        )
        
        # 注销
        result = await strategy_manager.unregister_strategy("test_strategy_1")
        
        assert result is True
        assert "test_strategy_1" not in strategy_manager._strategies

    @pytest.mark.asyncio
    async def test_unregister_nonexistent_strategy(self, strategy_manager):
        """测试注销不存在的策略"""
        result = await strategy_manager.unregister_strategy("nonexistent_strategy")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_unregister_running_strategy(self, strategy_manager, sample_strategy_config):
        """测试注销运行中的策略"""
        async def test_strategy(market_data: dict):
            await asyncio.sleep(0.1)
        
        # 注册并启动策略
        await strategy_manager.register_strategy(
            "test_strategy_1",
            test_strategy,
            sample_strategy_config
        )
        await strategy_manager.start_strategy("test_strategy_1")
        
        # 等待策略启动
        await asyncio.sleep(0.1)
        
        # 注销运行中的策略应该先停止再注销
        result = await strategy_manager.unregister_strategy("test_strategy_1")
        
        assert result is True
        assert "test_strategy_1" not in strategy_manager._strategies


# ============================================================================
# TestStrategyManagerLifecycle - 策略启动和停止测试
# ============================================================================


class TestStrategyManagerLifecycle:
    """StrategyManager 策略生命周期测试"""

    @pytest.mark.asyncio
    async def test_start_strategy_success(self, strategy_manager, sample_strategy_config):
        """测试成功启动策略"""
        async def test_strategy(market_data: dict):
            await asyncio.sleep(0.1)
        
        # 注册策略
        await strategy_manager.register_strategy(
            "test_strategy_1",
            test_strategy,
            sample_strategy_config
        )
        
        # 启动策略
        result = await strategy_manager.start_strategy("test_strategy_1")
        
        assert result is True
        assert strategy_manager._strategies["test_strategy_1"].status == StrategyStatus.RUNNING
        assert strategy_manager._strategies["test_strategy_1"].start_time is not None

    @pytest.mark.asyncio
    async def test_start_nonexistent_strategy(self, strategy_manager):
        """测试启动不存在的策略失败"""
        result = await strategy_manager.start_strategy("nonexistent_strategy")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_start_already_running_strategy(self, strategy_manager, sample_strategy_config):
        """测试启动已运行的策略失败"""
        async def test_strategy(market_data: dict):
            await asyncio.sleep(0.1)
        
        # 注册并启动策略
        await strategy_manager.register_strategy(
            "test_strategy_1",
            test_strategy,
            sample_strategy_config
        )
        await strategy_manager.start_strategy("test_strategy_1")
        
        # 尝试再次启动应该失败
        result = await strategy_manager.start_strategy("test_strategy_1")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_start_disabled_strategy(self, strategy_manager):
        """测试启动未启用的策略失败"""
        async def test_strategy(market_data: dict):
            pass
        
        config = StrategyConfig(
            strategy_id="test_strategy_1",
            name="测试策略1",
            enabled=False,  # 未启用
            subscribed_instruments=["rb2505"],
        )
        
        await strategy_manager.register_strategy(
            "test_strategy_1",
            test_strategy,
            config
        )
        
        result = await strategy_manager.start_strategy("test_strategy_1")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_stop_strategy_success(self, strategy_manager, sample_strategy_config):
        """测试成功停止策略"""
        async def test_strategy(market_data: dict):
            await asyncio.sleep(10)  # 长时间运行
        
        # 注册并启动策略
        await strategy_manager.register_strategy(
            "test_strategy_1",
            test_strategy,
            sample_strategy_config
        )
        await strategy_manager.start_strategy("test_strategy_1")
        
        # 等待策略启动
        await asyncio.sleep(0.1)
        
        # 停止策略
        result = await strategy_manager.stop_strategy("test_strategy_1")
        
        assert result is True
        assert strategy_manager._strategies["test_strategy_1"].status == StrategyStatus.STOPPED
        assert strategy_manager._strategies["test_strategy_1"].stop_time is not None

    @pytest.mark.asyncio
    async def test_stop_nonexistent_strategy(self, strategy_manager):
        """测试停止不存在的策略失败"""
        result = await strategy_manager.stop_strategy("nonexistent_strategy")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_stop_not_running_strategy(self, strategy_manager, sample_strategy_config):
        """测试停止未运行的策略失败"""
        async def test_strategy(market_data: dict):
            pass
        
        # 只注册，不启动
        await strategy_manager.register_strategy(
            "test_strategy_1",
            test_strategy,
            sample_strategy_config
        )
        
        result = await strategy_manager.stop_strategy("test_strategy_1")
        
        assert result is False


# ============================================================================
# TestStrategyManagerBroadcast - 行情广播测试
# ============================================================================


class TestStrategyManagerBroadcast:
    """StrategyManager 行情广播测试"""

    @pytest.mark.asyncio
    async def test_broadcast_market_data_success(self, strategy_manager, serializer):
        """测试成功广播行情数据"""
        market_data = {
            "InstrumentID": "rb2505",
            "LastPrice": 3500.0,
            "Volume": 1000,
        }
        
        # 广播行情数据（不抛出异常即为成功）
        await strategy_manager.broadcast_market_data(market_data)

    @pytest.mark.asyncio
    async def test_broadcast_without_redis(self, sample_strategy_config):
        """测试 Redis 不可用时的广播"""
        # 创建没有 Redis 的 StrategyManager
        manager = StrategyManager(cache_manager=None, max_strategies=5)
        
        market_data = {
            "InstrumentID": "rb2505",
            "LastPrice": 3500.0,
        }
        
        # 应该不抛出异常
        await manager.broadcast_market_data(market_data)

    @pytest.mark.asyncio
    async def test_broadcast_missing_instrument_id(self, strategy_manager):
        """测试缺少 InstrumentID 的行情数据"""
        market_data = {
            "LastPrice": 3500.0,
            # 缺少 InstrumentID
        }
        
        # 应该不抛出异常，只记录警告
        await strategy_manager.broadcast_market_data(market_data)

    @pytest.mark.asyncio
    async def test_strategy_receives_broadcast(self, strategy_manager, serializer):
        """测试策略接收广播的行情数据"""
        received_data = []
        
        async def test_strategy(market_data: dict):
            received_data.append(market_data)
        
        config = StrategyConfig(
            strategy_id="test_strategy_1",
            name="测试策略1",
            subscribed_instruments=["rb2505"],
        )
        
        # 注册并启动策略
        await strategy_manager.register_strategy(
            "test_strategy_1",
            test_strategy,
            config
        )
        await strategy_manager.start_strategy("test_strategy_1")
        
        # 等待策略启动和订阅
        await asyncio.sleep(0.2)
        
        # 广播行情数据
        market_data = {
            "InstrumentID": "rb2505",
            "LastPrice": 3500.0,
        }
        await strategy_manager.broadcast_market_data(market_data)
        
        # 等待策略接收数据
        await asyncio.sleep(0.2)
        
        # 验证策略收到数据
        assert len(received_data) > 0
        assert received_data[0]["InstrumentID"] == "rb2505"


# ============================================================================
# TestStrategyManagerIsolation - 策略异常隔离测试
# ============================================================================


class TestStrategyManagerIsolation:
    """StrategyManager 策略异常隔离测试"""

    @pytest.mark.asyncio
    async def test_strategy_exception_isolation(self, strategy_manager):
        """测试单个策略异常不影响其他策略"""
        strategy1_calls = []
        strategy2_calls = []
        
        async def failing_strategy(market_data: dict):
            strategy1_calls.append(market_data)
            raise ValueError("策略1故意抛出异常")
        
        async def normal_strategy(market_data: dict):
            strategy2_calls.append(market_data)
        
        # 注册两个策略
        config1 = StrategyConfig(
            strategy_id="failing_strategy",
            name="失败策略",
            subscribed_instruments=["rb2505"],
            error_threshold=10,  # 设置较高的阈值避免自动停止
        )
        config2 = StrategyConfig(
            strategy_id="normal_strategy",
            name="正常策略",
            subscribed_instruments=["rb2505"],
        )
        
        await strategy_manager.register_strategy("failing_strategy", failing_strategy, config1)
        await strategy_manager.register_strategy("normal_strategy", normal_strategy, config2)
        
        # 启动两个策略
        await strategy_manager.start_strategy("failing_strategy")
        await strategy_manager.start_strategy("normal_strategy")
        
        # 等待策略启动
        await asyncio.sleep(0.2)
        
        # 广播行情数据
        market_data = {
            "InstrumentID": "rb2505",
            "LastPrice": 3500.0,
        }
        await strategy_manager.broadcast_market_data(market_data)
        
        # 等待处理
        await asyncio.sleep(0.3)
        
        # 验证：失败策略应该记录错误，但正常策略应该继续运行
        failing_info = strategy_manager.get_strategy_status("failing_strategy")
        normal_info = strategy_manager.get_strategy_status("normal_strategy")
        
        # 正常策略应该收到数据
        assert len(strategy2_calls) > 0
        
        # 失败策略应该记录错误
        assert failing_info.error_count > 0

    @pytest.mark.asyncio
    async def test_strategy_error_count(self, strategy_manager):
        """测试策略错误计数"""
        call_count = [0]
        
        async def failing_strategy(market_data: dict):
            call_count[0] += 1
            raise ValueError("策略异常")
        
        config = StrategyConfig(
            strategy_id="test_strategy",
            name="测试策略",
            subscribed_instruments=["rb2505"],
            error_threshold=5,
        )
        
        await strategy_manager.register_strategy("test_strategy", failing_strategy, config)
        await strategy_manager.start_strategy("test_strategy")
        
        # 等待策略启动
        await asyncio.sleep(0.2)
        
        # 广播多次行情数据
        for i in range(3):
            market_data = {
                "InstrumentID": "rb2505",
                "LastPrice": 3500.0 + i,
            }
            await strategy_manager.broadcast_market_data(market_data)
            await asyncio.sleep(0.1)
        
        # 等待处理
        await asyncio.sleep(0.3)
        
        # 验证错误计数
        info = strategy_manager.get_strategy_status("test_strategy")
        assert info.error_count > 0
        assert info.last_error is not None

    @pytest.mark.asyncio
    async def test_strategy_auto_stop_on_threshold(self, strategy_manager):
        """测试达到错误阈值后自动停止"""
        error_count = [0]
        
        async def failing_strategy(market_data: dict):
            error_count[0] += 1
            raise ValueError("策略异常")
        
        config = StrategyConfig(
            strategy_id="test_strategy",
            name="测试策略",
            subscribed_instruments=["rb2505"],
            error_threshold=2,  # 低阈值
        )
        
        await strategy_manager.register_strategy("test_strategy", failing_strategy, config)
        await strategy_manager.start_strategy("test_strategy")
        
        # 等待策略启动
        await asyncio.sleep(0.2)
        
        # 广播行情数据触发第一次错误
        market_data = {
            "InstrumentID": "rb2505",
            "LastPrice": 3500.0,
        }
        await strategy_manager.broadcast_market_data(market_data)
        
        # 等待第一次错误处理
        await asyncio.sleep(0.5)
        
        # 验证第一次错误被记录
        info = strategy_manager.get_strategy_status("test_strategy")
        assert info.error_count >= 1
        
        # 等待策略重启（5秒）并再次触发错误
        await asyncio.sleep(5.5)
        
        # 广播第二次行情数据触发第二次错误
        await strategy_manager.broadcast_market_data(market_data)
        
        # 等待第二次错误处理和自动停止
        await asyncio.sleep(1.0)
        
        # 验证策略达到错误阈值后停止
        info = strategy_manager.get_strategy_status("test_strategy")
        # 策略应该处于 ERROR 状态或错误计数达到阈值
        assert info.error_count >= config.error_threshold or info.status == StrategyStatus.ERROR


# ============================================================================
# TestStrategyManagerQuery - 策略查询测试
# ============================================================================


class TestStrategyManagerQuery:
    """StrategyManager 策略查询测试"""

    @pytest.mark.asyncio
    async def test_get_strategy_status(self, strategy_manager, sample_strategy_config):
        """测试获取策略状态"""
        async def test_strategy(market_data: dict):
            pass
        
        await strategy_manager.register_strategy(
            "test_strategy_1",
            test_strategy,
            sample_strategy_config
        )
        
        status = strategy_manager.get_strategy_status("test_strategy_1")
        
        assert status is not None
        assert status.strategy_id == "test_strategy_1"
        assert status.status == StrategyStatus.REGISTERED

    @pytest.mark.asyncio
    async def test_get_nonexistent_strategy_status(self, strategy_manager):
        """测试获取不存在的策略状态"""
        status = strategy_manager.get_strategy_status("nonexistent")
        
        assert status is None

    @pytest.mark.asyncio
    async def test_list_strategies(self, strategy_manager):
        """测试列出所有策略"""
        async def test_strategy(market_data: dict):
            pass
        
        # 注册多个策略
        for i in range(3):
            config = StrategyConfig(
                strategy_id=f"strategy_{i}",
                name=f"策略{i}",
                subscribed_instruments=["rb2505"],
            )
            await strategy_manager.register_strategy(
                f"strategy_{i}",
                test_strategy,
                config
            )
        
        strategies = strategy_manager.list_strategies()
        
        assert len(strategies) == 3
        assert all(isinstance(s, StrategyInfo) for s in strategies)

    @pytest.mark.asyncio
    async def test_list_strategies_empty(self, strategy_manager):
        """测试列出空策略列表"""
        strategies = strategy_manager.list_strategies()
        
        assert len(strategies) == 0
        assert isinstance(strategies, list)


# ============================================================================
# 属性测试（Property-Based Testing）
# ============================================================================


@settings(max_examples=50, deadline=5000)
@given(
    st.lists(
        st.tuples(
            st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),  # strategy_id
            st.booleans(),  # will_fail
        ),
        min_size=2,
        max_size=5,
        unique_by=lambda x: x[0],  # 确保 strategy_id 唯一
    )
)
@pytest.mark.asyncio
async def test_property_strategy_isolation(strategies_config):
    """
    **Feature: performance-optimization-phase1, Property 4: 策略隔离性**
    
    属性测试：对于任何策略崩溃或异常，其他策略应该继续正常运行不受影响
    
    验证需求：6.4
    """
    # 创建 fakeredis 实例
    fake_server = fakeredis.FakeServer()
    fake_redis = fakeredis.aioredis.FakeRedis(server=fake_server, decode_responses=False)
    
    cache_manager = CacheManager()
    cache_manager._redis = fake_redis
    cache_manager._available = True
    cache_manager._config = CacheConfig(enabled=True)
    
    strategy_manager = StrategyManager(
        cache_manager=cache_manager,
        max_strategies=10
    )
    
    # 记录每个策略的调用次数
    call_counts = {strategy_id: [] for strategy_id, _ in strategies_config}
    
    try:
        # 为每个策略创建函数
        for strategy_id, will_fail in strategies_config:
            if will_fail:
                # 失败策略
                async def failing_strategy(market_data: dict, sid=strategy_id):
                    call_counts[sid].append(market_data)
                    raise ValueError(f"策略 {sid} 故意失败")
                
                strategy_func = failing_strategy
            else:
                # 正常策略
                async def normal_strategy(market_data: dict, sid=strategy_id):
                    call_counts[sid].append(market_data)
                
                strategy_func = normal_strategy
            
            # 注册策略
            config = StrategyConfig(
                strategy_id=strategy_id,
                name=f"策略_{strategy_id}",
                subscribed_instruments=["rb2505"],
                error_threshold=100,  # 高阈值避免自动停止
            )
            
            result = await strategy_manager.register_strategy(
                strategy_id,
                strategy_func,
                config
            )
            
            if not result:
                # 注册失败，跳过此策略
                continue
            
            # 启动策略
            await strategy_manager.start_strategy(strategy_id)
        
        # 等待所有策略启动
        await asyncio.sleep(0.3)
        
        # 广播行情数据
        market_data = {
            "InstrumentID": "rb2505",
            "LastPrice": 3500.0,
        }
        await strategy_manager.broadcast_market_data(market_data)
        
        # 等待处理
        await asyncio.sleep(0.5)
        
        # 验证：所有正常策略都应该收到数据
        normal_strategies = [sid for sid, will_fail in strategies_config if not will_fail]
        failing_strategies = [sid for sid, will_fail in strategies_config if will_fail]
        
        # 至少有一个正常策略和一个失败策略才进行验证
        if len(normal_strategies) > 0 and len(failing_strategies) > 0:
            # 验证正常策略收到数据
            for strategy_id in normal_strategies:
                if strategy_id in call_counts:
                    # 正常策略应该成功处理数据
                    assert len(call_counts[strategy_id]) > 0, \
                        f"正常策略 {strategy_id} 应该收到行情数据，但实际没有收到"
            
            # 验证失败策略记录了错误
            for strategy_id in failing_strategies:
                if strategy_id in strategy_manager._strategies:
                    info = strategy_manager.get_strategy_status(strategy_id)
                    # 失败策略应该有错误记录
                    assert info.error_count > 0, \
                        f"失败策略 {strategy_id} 应该记录错误，但错误计数为 0"
        
    finally:
        # 清理：停止所有策略
        for strategy_id, _ in strategies_config:
            if strategy_id in strategy_manager._strategies:
                if strategy_manager._strategies[strategy_id].status == StrategyStatus.RUNNING:
                    await strategy_manager.stop_strategy(strategy_id)
        
        await cache_manager.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
