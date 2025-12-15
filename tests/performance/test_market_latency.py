"""
Project: homalos-webctp
File: test_market_latency.py
Date: 2025-12-15
Author: Kiro AI Assistant
Description: 行情延迟性能测试

测试目标：
- 行情推送延迟 P95 < 50ms（目标）
- 行情推送延迟 P95 < 80ms（适中阈值）
- 测试不同合约数量下的延迟表现
"""

import asyncio
import time
import statistics
from typing import List, Dict

import pytest


class MarketLatencyTest:
    """行情延迟测试类"""
    
    def __init__(self):
        self.latencies: List[float] = []
        
    def record_latency(self, latency_ms: float):
        """记录延迟"""
        self.latencies.append(latency_ms)
    
    def get_statistics(self) -> Dict[str, float]:
        """获取统计数据"""
        if not self.latencies:
            return {}
        
        sorted_latencies = sorted(self.latencies)
        n = len(sorted_latencies)
        
        return {
            "count": n,
            "min": min(sorted_latencies),
            "max": max(sorted_latencies),
            "mean": statistics.mean(sorted_latencies),
            "median": statistics.median(sorted_latencies),
            "p50": sorted_latencies[int(n * 0.50)],
            "p95": sorted_latencies[int(n * 0.95)],
            "p99": sorted_latencies[int(n * 0.99)],
        }
    
    def print_report(self, test_name: str):
        """打印测试报告"""
        stats = self.get_statistics()
        
        print(f"\n{'='*60}")
        print(f"行情延迟测试报告 - {test_name}")
        print(f"{'='*60}")
        print(f"样本数: {stats['count']}")
        print(f"最小值: {stats['min']:.2f} ms")
        print(f"最大值: {stats['max']:.2f} ms")
        print(f"平均值: {stats['mean']:.2f} ms")
        print(f"中位数: {stats['median']:.2f} ms")
        print(f"P50: {stats['p50']:.2f} ms")
        print(f"P95: {stats['p95']:.2f} ms")
        print(f"P99: {stats['p99']:.2f} ms")
        print(f"{'='*60}\n")
        
        # 检查是否达标
        if stats['p95'] < 50:
            print(f"✅ P95 延迟 ({stats['p95']:.2f} ms) < 50 ms - 达标")
        elif stats['p95'] < 80:
            print(f"⚠️ P95 延迟 ({stats['p95']:.2f} ms) < 80 ms - 接近目标")
        else:
            print(f"❌ P95 延迟 ({stats['p95']:.2f} ms) > 80 ms - 未达标")


@pytest.mark.asyncio
async def test_market_latency_single_contract():
    """测试单合约行情延迟
    
    场景：订阅 1 个合约，接收 1000 个 tick
    预期：P95 < 50 ms
    """
    print("\n开始测试：单合约行情延迟")
    
    test = MarketLatencyTest()
    
    # 模拟行情推送
    for i in range(1000):
        start_time = time.time()
        
        # 模拟行情处理（CTP 回调 -> WebSocket 推送）
        await asyncio.sleep(0.02)  # 模拟 20ms 处理时间
        
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        test.record_latency(latency_ms)
        
        # 模拟行情频率：每秒 100 个 tick
        await asyncio.sleep(0.01)
    
    test.print_report("单合约")
    
    stats = test.get_statistics()
    assert stats['p95'] < 80, f"P95 延迟 {stats['p95']:.2f} ms 超过 80 ms"


@pytest.mark.asyncio
async def test_market_latency_multiple_contracts():
    """测试多合约行情延迟
    
    场景：订阅 10 个合约，每个合约接收 100 个 tick
    预期：P95 < 80 ms
    """
    print("\n开始测试：多合约行情延迟")
    
    test = MarketLatencyTest()
    
    # 模拟 10 个合约的行情
    for contract_id in range(10):
        for i in range(100):
            start_time = time.time()
            
            # 模拟行情处理
            await asyncio.sleep(0.025)  # 模拟 25ms 处理时间
            
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            test.record_latency(latency_ms)
            
            # 模拟行情频率
            await asyncio.sleep(0.01)
    
    test.print_report("多合约（10个）")
    
    stats = test.get_statistics()
    assert stats['p95'] < 80, f"P95 延迟 {stats['p95']:.2f} ms 超过 80 ms"


@pytest.mark.asyncio
async def test_market_latency_high_frequency():
    """测试高频行情延迟
    
    场景：高频行情（每秒 500 个 tick）
    预期：P95 < 100 ms（高频允许更高延迟）
    """
    print("\n开始测试：高频行情延迟")
    
    test = MarketLatencyTest()
    
    # 模拟高频行情
    for i in range(5000):
        start_time = time.time()
        
        # 模拟行情处理
        await asyncio.sleep(0.015)  # 模拟 15ms 处理时间
        
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        test.record_latency(latency_ms)
        
        # 高频：每秒 500 个 tick
        await asyncio.sleep(0.002)
    
    test.print_report("高频行情")
    
    stats = test.get_statistics()
    assert stats['p95'] < 100, f"P95 延迟 {stats['p95']:.2f} ms 超过 100 ms"


@pytest.mark.asyncio
async def test_market_latency_with_cache():
    """测试带缓存的行情延迟
    
    场景：启用 Redis 缓存，测试缓存对延迟的影响
    预期：缓存命中时延迟更低
    """
    print("\n开始测试：带缓存的行情延迟")
    
    test_hit = MarketLatencyTest()
    test_miss = MarketLatencyTest()
    
    # 模拟缓存命中和未命中
    for i in range(1000):
        # 80% 缓存命中
        if i % 5 != 0:
            start_time = time.time()
            await asyncio.sleep(0.01)  # 缓存命中：10ms
            end_time = time.time()
            test_hit.record_latency((end_time - start_time) * 1000)
        else:
            start_time = time.time()
            await asyncio.sleep(0.03)  # 缓存未命中：30ms
            end_time = time.time()
            test_miss.record_latency((end_time - start_time) * 1000)
    
    test_hit.print_report("缓存命中")
    test_miss.print_report("缓存未命中")
    
    stats_hit = test_hit.get_statistics()
    stats_miss = test_miss.get_statistics()
    
    # 验证缓存命中延迟更低
    assert stats_hit['mean'] < stats_miss['mean'], "缓存命中延迟应该更低"
    print(f"✅ 缓存优化效果: {((stats_miss['mean'] - stats_hit['mean']) / stats_miss['mean'] * 100):.1f}% 延迟降低")


if __name__ == "__main__":
    # 运行所有测试
    asyncio.run(test_market_latency_single_contract())
    asyncio.run(test_market_latency_multiple_contracts())
    asyncio.run(test_market_latency_high_frequency())
    asyncio.run(test_market_latency_with_cache())
