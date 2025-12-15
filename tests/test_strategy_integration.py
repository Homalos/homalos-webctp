#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : test_strategy_integration.py
@Date       : 2025/12/15
@Author     : Kiro Agent
@Software   : PyCharm
@Description: StrategyManager 集成测试 - 测试多策略并行、行情分发、错误隔离和资源限制
"""

import pytest
import pytest_asyncio
import asyncio
from unittest.mock import patch
import fakeredis.aioredis

from src.services.strategy_manager import (
    StrategyManager,
    StrategyConfig,
    StrategyStatus,
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
        max_strategies=10
    )
    yield manager
    
    # 清理：停止所有运行中的策略
    for strategy_id in list(manager._strategies.keys()):
        if manager._strategies[strategy_id].status == StrategyStatus.RUNNING:
            await manager.stop_strategy(strategy_id)


@pytest.fixture
def serializer():
    """创建 msgpack 序列化器"""
    return get_msgpack_serializer()


# ============================================================================
# TestMultiStrategyParallel - 多策略并行运行测试
# ============================================================================


class TestMultiStrategyParallel:
    """测试多策略并行运行"""

    @pytest.mark.asyncio
    async def test_multiple_strategies_run_concurrently(self, strategy_manager):
        """测试多个策略可以并行运行"""
        # 记录每个策略的调用次数
        call_counts = {f"strategy_{i}": [] for i in range(3)}
        
        # 创建3个策略
        for i in range(3):
            strategy_id = f"strategy_{i}"
            
            async def strategy_func(market_data: dict, sid=strategy_id):
                call_counts[sid].append(market_data)
                await asyncio.sleep(0.1)  # 模拟处理时间
            
            config = StrategyConfig(
                strategy_id=strategy_id,
                name=f"策略{i}",
                subscribed_instruments=["rb2505"],
            )
            
            await strategy_manager.register_strategy(strategy_id, strategy_func, config)
            await strategy_manager.start_strategy(strategy_id)
        
        # 等待所有策略启动
        await asyncio.sleep(0.3)
        
        # 验证所有策略都在运行
        for i in range(3):
            strategy_id = f"strategy_{i}"
            status = strategy_manager.get_strategy_status(strategy_id)
            assert status.status == StrategyStatus.RUNNING
        
        # 广播行情数据
        market_data = {
            "InstrumentID": "rb2505",
            "LastPrice": 3500.0,
        }
        await strategy_manager.broadcast_market_data(market_data)
        
        # 等待所有策略处理完成
        await asyncio.sleep(0.5)
        
        # 验证所有策略都收到了数据
        for i in range(3):
            strategy_id = f"strategy_{i}"
            assert len(call_counts[strategy_id]) > 0, f"策略 {strategy_id} 应该收到行情数据"


    @pytest.mark.asyncio
    async def test_strategies_do_not_block_each_other(self, strategy_manager):
        """测试策略之间不会相互阻塞"""
        # 记录策略执行时间
        execution_times = {}
        
        async def fast_strategy(market_data: dict):
            start = asyncio.get_event_loop().time()
            await asyncio.sleep(0.05)  # 快速策略
            execution_times["fast"] = asyncio.get_event_loop().time() - start
        
        async def slow_strategy(market_data: dict):
            start = asyncio.get_event_loop().time()
            await asyncio.sleep(0.3)  # 慢速策略
            execution_times["slow"] = asyncio.get_event_loop().time() - start
        
        # 注册并启动策略
        fast_config = StrategyConfig(
            strategy_id="fast_strategy",
            name="快速策略",
            subscribed_instruments=["rb2505"],
        )
        slow_config = StrategyConfig(
            strategy_id="slow_strategy",
            name="慢速策略",
            subscribed_instruments=["rb2505"],
        )
        
        await strategy_manager.register_strategy("fast_strategy", fast_strategy, fast_config)
        await strategy_manager.register_strategy("slow_strategy", slow_strategy, slow_config)
        
        await strategy_manager.start_strategy("fast_strategy")
        await strategy_manager.start_strategy("slow_strategy")
        
        # 等待策略启动
        await asyncio.sleep(0.2)
        
        # 广播行情
        market_data = {"InstrumentID": "rb2505", "LastPrice": 3500.0}
        await strategy_manager.broadcast_market_data(market_data)
        
        # 等待处理完成
        await asyncio.sleep(0.5)
        
        # 验证快速策略没有被慢速策略阻塞
        assert "fast" in execution_times
        assert execution_times["fast"] < 0.15, "快速策略不应该被慢速策略阻塞"


# ============================================================================
# TestMarketDataDistribution - 行情分发测试
# ============================================================================


class TestMarketDataDistribution:
    """测试行情数据分发到多策略"""

    @pytest.mark.asyncio
    async def test_market_data_distributed_to_all_subscribers(self, strategy_manager):
        """测试行情数据分发到所有订阅策略"""
        received_data = {f"strategy_{i}": [] for i in range(3)}
        
        # 创建3个订阅相同合约的策略
        for i in range(3):
            strategy_id = f"strategy_{i}"
            
            async def strategy_func(market_data: dict, sid=strategy_id):
                received_data[sid].append(market_data)
            
            config = StrategyConfig(
                strategy_id=strategy_id,
                name=f"策略{i}",
                subscribed_instruments=["rb2505"],
            )
            
            await strategy_manager.register_strategy(strategy_id, strategy_func, config)
            await strategy_manager.start_strategy(strategy_id)
        
        # 等待策略启动
        await asyncio.sleep(0.3)
        
        # 广播行情数据
        market_data = {
            "InstrumentID": "rb2505",
            "LastPrice": 3500.0,
            "Volume": 1000,
        }
        await strategy_manager.broadcast_market_data(market_data)
        
        # 等待分发完成
        await asyncio.sleep(0.3)
        
        # 验证所有策略都收到了相同的数据
        for i in range(3):
            strategy_id = f"strategy_{i}"
            assert len(received_data[strategy_id]) > 0, f"策略 {strategy_id} 应该收到数据"
            assert received_data[strategy_id][0]["InstrumentID"] == "rb2505"
            assert received_data[strategy_id][0]["LastPrice"] == 3500.0


    @pytest.mark.asyncio
    async def test_strategies_receive_only_subscribed_instruments(self, strategy_manager):
        """测试策略只接收订阅的合约行情"""
        received_data = {
            "rb_strategy": [],
            "au_strategy": [],
        }
        
        # 创建订阅不同合约的策略
        async def rb_strategy(market_data: dict):
            received_data["rb_strategy"].append(market_data)
        
        async def au_strategy(market_data: dict):
            received_data["au_strategy"].append(market_data)
        
        rb_config = StrategyConfig(
            strategy_id="rb_strategy",
            name="螺纹钢策略",
            subscribed_instruments=["rb2505"],
        )
        au_config = StrategyConfig(
            strategy_id="au_strategy",
            name="黄金策略",
            subscribed_instruments=["au2506"],
        )
        
        await strategy_manager.register_strategy("rb_strategy", rb_strategy, rb_config)
        await strategy_manager.register_strategy("au_strategy", au_strategy, au_config)
        
        await strategy_manager.start_strategy("rb_strategy")
        await strategy_manager.start_strategy("au_strategy")
        
        # 等待策略启动
        await asyncio.sleep(0.3)
        
        # 广播螺纹钢行情
        rb_data = {"InstrumentID": "rb2505", "LastPrice": 3500.0}
        await strategy_manager.broadcast_market_data(rb_data)
        
        # 广播黄金行情
        au_data = {"InstrumentID": "au2506", "LastPrice": 450.0}
        await strategy_manager.broadcast_market_data(au_data)
        
        # 等待分发完成
        await asyncio.sleep(0.3)
        
        # 验证策略只收到订阅的合约
        assert len(received_data["rb_strategy"]) > 0
        assert all(d["InstrumentID"] == "rb2505" for d in received_data["rb_strategy"])
        
        assert len(received_data["au_strategy"]) > 0
        assert all(d["InstrumentID"] == "au2506" for d in received_data["au_strategy"])

    @pytest.mark.asyncio
    async def test_multiple_market_data_broadcasts(self, strategy_manager):
        """测试多次行情广播"""
        received_count = {"strategy": 0}
        
        async def counting_strategy(market_data: dict):
            received_count["strategy"] += 1
        
        config = StrategyConfig(
            strategy_id="counting_strategy",
            name="计数策略",
            subscribed_instruments=["rb2505"],
        )
        
        await strategy_manager.register_strategy("counting_strategy", counting_strategy, config)
        await strategy_manager.start_strategy("counting_strategy")
        
        # 等待策略启动
        await asyncio.sleep(0.3)
        
        # 广播多次行情
        for i in range(5):
            market_data = {
                "InstrumentID": "rb2505",
                "LastPrice": 3500.0 + i,
            }
            await strategy_manager.broadcast_market_data(market_data)
            await asyncio.sleep(0.05)
        
        # 等待处理完成
        await asyncio.sleep(0.3)
        
        # 验证策略收到了所有行情
        assert received_count["strategy"] >= 5, "策略应该收到所有广播的行情"


# ============================================================================
# TestStrategyCrashIsolation - 策略崩溃隔离测试
# ============================================================================


class TestStrategyCrashIsolation:
    """测试策略崩溃隔离"""

    @pytest.mark.asyncio
    async def test_failing_strategy_does_not_affect_others(self, strategy_manager):
        """测试失败策略不影响其他策略"""
        call_counts = {
            "failing_strategy": [],
            "normal_strategy_1": [],
            "normal_strategy_2": [],
        }
        
        async def failing_strategy(market_data: dict):
            call_counts["failing_strategy"].append(market_data)
            raise ValueError("策略故意失败")
        
        async def normal_strategy_1(market_data: dict):
            call_counts["normal_strategy_1"].append(market_data)
        
        async def normal_strategy_2(market_data: dict):
            call_counts["normal_strategy_2"].append(market_data)
        
        # 注册策略
        configs = [
            ("failing_strategy", failing_strategy, 100),
            ("normal_strategy_1", normal_strategy_1, 10),
            ("normal_strategy_2", normal_strategy_2, 10),
        ]
        
        for strategy_id, func, threshold in configs:
            config = StrategyConfig(
                strategy_id=strategy_id,
                name=strategy_id,
                subscribed_instruments=["rb2505"],
                error_threshold=threshold,
            )
            await strategy_manager.register_strategy(strategy_id, func, config)
            await strategy_manager.start_strategy(strategy_id)
        
        # 等待策略启动
        await asyncio.sleep(0.3)
        
        # 广播行情数据
        market_data = {"InstrumentID": "rb2505", "LastPrice": 3500.0}
        await strategy_manager.broadcast_market_data(market_data)
        
        # 等待处理
        await asyncio.sleep(0.5)
        
        # 验证正常策略收到数据
        assert len(call_counts["normal_strategy_1"]) > 0, "正常策略1应该收到数据"
        assert len(call_counts["normal_strategy_2"]) > 0, "正常策略2应该收到数据"
        
        # 验证失败策略记录了错误
        failing_info = strategy_manager.get_strategy_status("failing_strategy")
        assert failing_info.error_count > 0, "失败策略应该记录错误"
        assert failing_info.last_error is not None


    @pytest.mark.asyncio
    async def test_strategy_error_does_not_stop_manager(self, strategy_manager):
        """测试策略错误不会停止管理器"""
        async def crashing_strategy(market_data: dict):
            raise RuntimeError("严重错误")
        
        async def stable_strategy(market_data: dict):
            pass
        
        crash_config = StrategyConfig(
            strategy_id="crashing_strategy",
            name="崩溃策略",
            subscribed_instruments=["rb2505"],
            error_threshold=100,
        )
        stable_config = StrategyConfig(
            strategy_id="stable_strategy",
            name="稳定策略",
            subscribed_instruments=["rb2505"],
        )
        
        await strategy_manager.register_strategy("crashing_strategy", crashing_strategy, crash_config)
        await strategy_manager.register_strategy("stable_strategy", stable_strategy, stable_config)
        
        await strategy_manager.start_strategy("crashing_strategy")
        await strategy_manager.start_strategy("stable_strategy")
        
        # 等待策略启动
        await asyncio.sleep(0.3)
        
        # 广播行情
        market_data = {"InstrumentID": "rb2505", "LastPrice": 3500.0}
        await strategy_manager.broadcast_market_data(market_data)
        
        # 等待处理
        await asyncio.sleep(0.5)
        
        # 验证管理器仍然可以列出策略
        strategies = strategy_manager.list_strategies()
        assert len(strategies) == 2
        
        # 验证可以注册新策略
        async def new_strategy(market_data: dict):
            pass
        
        new_config = StrategyConfig(
            strategy_id="new_strategy",
            name="新策略",
            subscribed_instruments=["rb2505"],
        )
        result = await strategy_manager.register_strategy("new_strategy", new_strategy, new_config)
        assert result is True

    @pytest.mark.asyncio
    async def test_multiple_strategies_with_mixed_failures(self, strategy_manager):
        """测试多个策略混合失败场景"""
        results = {
            "success_1": [],
            "fail_1": [],
            "success_2": [],
            "fail_2": [],
            "success_3": [],
        }
        
        async def success_strategy_1(market_data: dict):
            results["success_1"].append("success")
        
        async def fail_strategy_1(market_data: dict):
            results["fail_1"].append("fail")
            raise Exception("策略 fail_1 失败")
        
        async def success_strategy_2(market_data: dict):
            results["success_2"].append("success")
        
        async def fail_strategy_2(market_data: dict):
            results["fail_2"].append("fail")
            raise Exception("策略 fail_2 失败")
        
        async def success_strategy_3(market_data: dict):
            results["success_3"].append("success")
        
        # 注册5个策略，其中2个会失败
        strategies = [
            ("success_1", success_strategy_1, False),
            ("fail_1", fail_strategy_1, True),
            ("success_2", success_strategy_2, False),
            ("fail_2", fail_strategy_2, True),
            ("success_3", success_strategy_3, False),
        ]
        
        for strategy_id, func, _ in strategies:
            config = StrategyConfig(
                strategy_id=strategy_id,
                name=strategy_id,
                subscribed_instruments=["rb2505"],
                error_threshold=100,
            )
            await strategy_manager.register_strategy(strategy_id, func, config)
            await strategy_manager.start_strategy(strategy_id)
        
        # 等待策略启动
        await asyncio.sleep(0.3)
        
        # 广播行情
        market_data = {"InstrumentID": "rb2505", "LastPrice": 3500.0}
        await strategy_manager.broadcast_market_data(market_data)
        
        # 等待处理
        await asyncio.sleep(0.5)
        
        # 验证成功策略都收到数据
        assert len(results["success_1"]) > 0
        assert len(results["success_2"]) > 0
        assert len(results["success_3"]) > 0
        
        # 验证失败策略记录了错误
        for strategy_id in ["fail_1", "fail_2"]:
            info = strategy_manager.get_strategy_status(strategy_id)
            assert info.error_count > 0


# ============================================================================
# TestResourceLimits - 资源限制测试
# ============================================================================


class TestResourceLimits:
    """测试资源限制"""

    @pytest.mark.asyncio
    async def test_max_strategies_limit(self, cache_manager_with_fake_redis):
        """测试最大策略数量限制"""
        # 创建限制为5个策略的管理器
        manager = StrategyManager(
            cache_manager=cache_manager_with_fake_redis,
            max_strategies=5
        )
        
        async def dummy_strategy(market_data: dict):
            pass
        
        # 注册5个策略（达到限制）
        for i in range(5):
            config = StrategyConfig(
                strategy_id=f"strategy_{i}",
                name=f"策略{i}",
                subscribed_instruments=["rb2505"],
            )
            result = await manager.register_strategy(f"strategy_{i}", dummy_strategy, config)
            assert result is True, f"策略 {i} 应该注册成功"
        
        # 尝试注册第6个策略（应该失败）
        config = StrategyConfig(
            strategy_id="strategy_6",
            name="策略6",
            subscribed_instruments=["rb2505"],
        )
        result = await manager.register_strategy("strategy_6", dummy_strategy, config)
        assert result is False, "超过限制的策略注册应该失败"
        
        # 验证只有5个策略
        strategies = manager.list_strategies()
        assert len(strategies) == 5
        
        # 清理
        for i in range(5):
            await manager.unregister_strategy(f"strategy_{i}")


    @pytest.mark.asyncio
    async def test_unregister_frees_slot(self, cache_manager_with_fake_redis):
        """测试注销策略释放槽位"""
        manager = StrategyManager(
            cache_manager=cache_manager_with_fake_redis,
            max_strategies=3
        )
        
        async def dummy_strategy(market_data: dict):
            pass
        
        # 注册3个策略（达到限制）
        for i in range(3):
            config = StrategyConfig(
                strategy_id=f"strategy_{i}",
                name=f"策略{i}",
                subscribed_instruments=["rb2505"],
            )
            await manager.register_strategy(f"strategy_{i}", dummy_strategy, config)
        
        # 注销一个策略
        await manager.unregister_strategy("strategy_1")
        
        # 现在应该可以注册新策略
        config = StrategyConfig(
            strategy_id="new_strategy",
            name="新策略",
            subscribed_instruments=["rb2505"],
        )
        result = await manager.register_strategy("new_strategy", dummy_strategy, config)
        assert result is True, "注销后应该可以注册新策略"
        
        # 清理
        await manager.unregister_strategy("strategy_0")
        await manager.unregister_strategy("strategy_2")
        await manager.unregister_strategy("new_strategy")

    @pytest.mark.asyncio
    async def test_strategy_without_subscriptions(self, strategy_manager):
        """测试没有订阅合约的策略"""
        call_count = {"strategy": 0}
        
        async def no_sub_strategy(market_data: dict):
            call_count["strategy"] += 1
        
        # 创建没有订阅合约的策略
        config = StrategyConfig(
            strategy_id="no_sub_strategy",
            name="无订阅策略",
            subscribed_instruments=[],  # 空订阅列表
        )
        
        result = await strategy_manager.register_strategy("no_sub_strategy", no_sub_strategy, config)
        assert result is True
        
        result = await strategy_manager.start_strategy("no_sub_strategy")
        assert result is True
        
        # 等待策略启动
        await asyncio.sleep(0.3)
        
        # 广播行情
        market_data = {"InstrumentID": "rb2505", "LastPrice": 3500.0}
        await strategy_manager.broadcast_market_data(market_data)
        
        # 等待处理
        await asyncio.sleep(0.3)
        
        # 验证策略没有收到数据（因为没有订阅）
        assert call_count["strategy"] == 0, "没有订阅的策略不应该收到数据"


# ============================================================================
# TestStrategyDynamicControl - 策略动态控制测试
# ============================================================================


class TestStrategyDynamicControl:
    """测试策略动态启停"""

    @pytest.mark.asyncio
    async def test_start_stop_strategy_during_operation(self, strategy_manager):
        """测试运行期间启停策略"""
        received_data = {
            "strategy_1": [],
            "strategy_2": [],
        }
        
        async def strategy_1(market_data: dict):
            received_data["strategy_1"].append(market_data)
        
        async def strategy_2(market_data: dict):
            received_data["strategy_2"].append(market_data)
        
        # 注册两个策略
        for i in [1, 2]:
            config = StrategyConfig(
                strategy_id=f"strategy_{i}",
                name=f"策略{i}",
                subscribed_instruments=["rb2505"],
            )
            func = strategy_1 if i == 1 else strategy_2
            await strategy_manager.register_strategy(f"strategy_{i}", func, config)
        
        # 只启动策略1
        await strategy_manager.start_strategy("strategy_1")
        await asyncio.sleep(0.3)
        
        # 广播第一次行情
        market_data_1 = {"InstrumentID": "rb2505", "LastPrice": 3500.0}
        await strategy_manager.broadcast_market_data(market_data_1)
        await asyncio.sleep(0.3)
        
        # 验证只有策略1收到数据
        assert len(received_data["strategy_1"]) > 0
        assert len(received_data["strategy_2"]) == 0
        
        # 启动策略2
        await strategy_manager.start_strategy("strategy_2")
        await asyncio.sleep(0.3)
        
        # 广播第二次行情
        market_data_2 = {"InstrumentID": "rb2505", "LastPrice": 3600.0}
        await strategy_manager.broadcast_market_data(market_data_2)
        await asyncio.sleep(0.3)
        
        # 验证两个策略都收到第二次数据
        assert len(received_data["strategy_1"]) >= 2
        assert len(received_data["strategy_2"]) > 0
        
        # 停止策略1
        await strategy_manager.stop_strategy("strategy_1")
        await asyncio.sleep(0.2)
        
        # 清空计数
        count_before = len(received_data["strategy_1"])
        
        # 广播第三次行情
        market_data_3 = {"InstrumentID": "rb2505", "LastPrice": 3700.0}
        await strategy_manager.broadcast_market_data(market_data_3)
        await asyncio.sleep(0.3)
        
        # 验证策略1没有收到新数据，策略2收到了
        assert len(received_data["strategy_1"]) == count_before, "停止的策略不应该收到新数据"
        assert len(received_data["strategy_2"]) >= 2


    @pytest.mark.asyncio
    async def test_restart_stopped_strategy(self, strategy_manager):
        """测试重启已停止的策略"""
        call_count = {"strategy": 0}
        
        async def counting_strategy(market_data: dict):
            call_count["strategy"] += 1
        
        config = StrategyConfig(
            strategy_id="restart_strategy",
            name="重启策略",
            subscribed_instruments=["rb2505"],
        )
        
        # 注册并启动策略
        await strategy_manager.register_strategy("restart_strategy", counting_strategy, config)
        await strategy_manager.start_strategy("restart_strategy")
        await asyncio.sleep(0.3)
        
        # 广播行情
        market_data = {"InstrumentID": "rb2505", "LastPrice": 3500.0}
        await strategy_manager.broadcast_market_data(market_data)
        await asyncio.sleep(0.3)
        
        first_count = call_count["strategy"]
        assert first_count > 0
        
        # 停止策略
        await strategy_manager.stop_strategy("restart_strategy")
        await asyncio.sleep(0.2)
        
        # 重新启动策略
        result = await strategy_manager.start_strategy("restart_strategy")
        assert result is True, "应该可以重启已停止的策略"
        await asyncio.sleep(0.3)
        
        # 广播新行情
        await strategy_manager.broadcast_market_data(market_data)
        await asyncio.sleep(0.3)
        
        # 验证策略重启后继续接收数据
        assert call_count["strategy"] > first_count, "重启后的策略应该继续接收数据"


# ============================================================================
# TestComplexScenarios - 复杂场景测试
# ============================================================================


class TestComplexScenarios:
    """测试复杂场景"""

    @pytest.mark.asyncio
    async def test_high_frequency_broadcasts(self, strategy_manager):
        """测试高频行情广播"""
        received_count = {"strategy": 0}
        
        async def high_freq_strategy(market_data: dict):
            received_count["strategy"] += 1
        
        config = StrategyConfig(
            strategy_id="high_freq_strategy",
            name="高频策略",
            subscribed_instruments=["rb2505"],
        )
        
        await strategy_manager.register_strategy("high_freq_strategy", high_freq_strategy, config)
        await strategy_manager.start_strategy("high_freq_strategy")
        await asyncio.sleep(0.3)
        
        # 快速广播100次行情
        for i in range(100):
            market_data = {
                "InstrumentID": "rb2505",
                "LastPrice": 3500.0 + i * 0.1,
            }
            await strategy_manager.broadcast_market_data(market_data)
        
        # 等待处理完成
        await asyncio.sleep(1.0)
        
        # 验证策略收到了大部分行情（允许一些丢失）
        assert received_count["strategy"] >= 90, f"高频场景下应该收到大部分行情，实际收到: {received_count['strategy']}"

    @pytest.mark.asyncio
    async def test_strategy_with_multiple_instruments(self, strategy_manager):
        """测试订阅多个合约的策略"""
        received_instruments = {"strategy": set()}
        
        async def multi_instrument_strategy(market_data: dict):
            instrument_id = market_data.get("InstrumentID")
            if instrument_id:
                received_instruments["strategy"].add(instrument_id)
        
        config = StrategyConfig(
            strategy_id="multi_instrument_strategy",
            name="多合约策略",
            subscribed_instruments=["rb2505", "au2506", "cu2501"],
        )
        
        await strategy_manager.register_strategy("multi_instrument_strategy", multi_instrument_strategy, config)
        await strategy_manager.start_strategy("multi_instrument_strategy")
        await asyncio.sleep(0.3)
        
        # 广播不同合约的行情
        instruments = ["rb2505", "au2506", "cu2501"]
        for instrument in instruments:
            market_data = {
                "InstrumentID": instrument,
                "LastPrice": 3500.0,
            }
            await strategy_manager.broadcast_market_data(market_data)
            await asyncio.sleep(0.1)
        
        # 等待处理完成
        await asyncio.sleep(0.5)
        
        # 验证策略收到了所有订阅的合约
        assert len(received_instruments["strategy"]) == 3
        assert "rb2505" in received_instruments["strategy"]
        assert "au2506" in received_instruments["strategy"]
        assert "cu2501" in received_instruments["strategy"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
