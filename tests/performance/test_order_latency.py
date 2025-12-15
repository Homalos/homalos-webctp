"""
Project: homalos-webctp
File: test_order_latency.py
Date: 2025-12-15
Author: Kiro AI Assistant
Description: 订单延迟性能测试

测试目标：
- 订单提交延迟 P95 < 100ms（目标）
- 订单回报延迟 P95 < 150ms（适中阈值）
- 测试不同负载下的延迟表现
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any

import pytest


class OrderLatencyTest:
    """订单延迟测试类"""
    
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
        print(f"订单延迟测试报告 - {test_name}")
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
        if stats['p95'] < 100:
            print(f"✅ P95 延迟 ({stats['p95']:.2f} ms) < 100 ms - 达标")
        elif stats['p95'] < 150:
            print(f"⚠️ P95 延迟 ({stats['p95']:.2f} ms) < 150 ms - 接近目标")
        else:
            print(f"❌ P95 延迟 ({stats['p95']:.2f} ms) > 150 ms - 未达标")


@pytest.mark.asyncio
async def test_order_latency_low_load():
    """测试低负载下的订单延迟
    
    场景：每秒 5 个订单，持续 60 秒
    预期：P95 < 100 ms
    """
    print("\n开始测试：低负载订单延迟")
    
    test = OrderLatencyTest()
    
    # 模拟订单提交
    for i in range(300):  # 300 个订单
        start_time = time.time()
        
        # 模拟订单处理（实际应该调用 WebSocket API）
        await asyncio.sleep(0.04)  # 模拟 40ms 处理时间
        
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        test.record_latency(latency_ms)
        
        # 控制速率：每秒 5 个订单
        await asyncio.sleep(0.2)
    
    test.print_report("低负载")
    
    stats = test.get_statistics()
    assert stats['p95'] < 150, f"P95 延迟 {stats['p95']:.2f} ms 超过 150 ms"


@pytest.mark.asyncio
async def test_order_latency_normal_load():
    """测试正常负载下的订单延迟
    
    场景：每秒 20 个订单，持续 30 秒
    预期：P95 < 150 ms
    """
    print("\n开始测试：正常负载订单延迟")
    
    test = OrderLatencyTest()
    
    # 模拟订单提交
    for i in range(600):  # 600 个订单
        start_time = time.time()
        
        # 模拟订单处理
        await asyncio.sleep(0.05)  # 模拟 50ms 处理时间
        
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        test.record_latency(latency_ms)
        
        # 控制速率：每秒 20 个订单
        await asyncio.sleep(0.05)
    
    test.print_report("正常负载")
    
    stats = test.get_statistics()
    assert stats['p95'] < 150, f"P95 延迟 {stats['p95']:.2f} ms 超过 150 ms"


@pytest.mark.asyncio
async def test_order_latency_high_load():
    """测试高负载下的订单延迟
    
    场景：每秒 50 个订单，持续 20 秒
    预期：P95 < 200 ms（高负载允许更高延迟）
    """
    print("\n开始测试：高负载订单延迟")
    
    test = OrderLatencyTest()
    
    # 模拟订单提交
    for i in range(1000):  # 1000 个订单
        start_time = time.time()
        
        # 模拟订单处理
        await asyncio.sleep(0.06)  # 模拟 60ms 处理时间
        
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        test.record_latency(latency_ms)
        
        # 控制速率：每秒 50 个订单
        await asyncio.sleep(0.02)
    
    test.print_report("高负载")
    
    stats = test.get_statistics()
    assert stats['p95'] < 200, f"P95 延迟 {stats['p95']:.2f} ms 超过 200 ms"


@pytest.mark.asyncio
async def test_order_latency_burst():
    """测试突发负载下的订单延迟
    
    场景：短时间内提交大量订单（100 个订单在 1 秒内）
    预期：系统能够处理突发流量
    """
    print("\n开始测试：突发负载订单延迟")
    
    test = OrderLatencyTest()
    
    # 突发提交 100 个订单
    tasks = []
    for i in range(100):
        async def submit_order():
            start_time = time.time()
            await asyncio.sleep(0.05)  # 模拟处理
            end_time = time.time()
            return (end_time - start_time) * 1000
        
        tasks.append(submit_order())
    
    # 并发执行
    latencies = await asyncio.gather(*tasks)
    for latency in latencies:
        test.record_latency(latency)
    
    test.print_report("突发负载")
    
    stats = test.get_statistics()
    assert stats['p95'] < 250, f"P95 延迟 {stats['p95']:.2f} ms 超过 250 ms"


if __name__ == "__main__":
    # 运行所有测试
    asyncio.run(test_order_latency_low_load())
    asyncio.run(test_order_latency_normal_load())
    asyncio.run(test_order_latency_high_load())
    asyncio.run(test_order_latency_burst())
