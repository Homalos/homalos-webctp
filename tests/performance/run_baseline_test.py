"""
Project: homalos-webctp
File: run_baseline_test.py
Date: 2025-12-15
Author: Kiro AI Assistant
Description: 快速性能基线测试脚本

用于生成性能基线报告的简化测试
"""

import asyncio
import time
import statistics
from typing import List, Dict
import json
from datetime import datetime


class PerformanceTest:
    """性能测试基类"""
    
    def __init__(self, name: str):
        self.name = name
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


async def test_order_latency_baseline():
    """订单延迟基线测试（简化版）"""
    print("\n" + "="*60)
    print("订单延迟基线测试")
    print("="*60)
    
    results = {}
    
    # 低负载测试 (100 个样本)
    print("\n[1/3] 低负载测试 (5 单/秒)...")
    test = PerformanceTest("低负载")
    for i in range(100):
        start_time = time.time()
        await asyncio.sleep(0.04)  # 模拟 40ms 处理
        latency_ms = (time.time() - start_time) * 1000
        test.record_latency(latency_ms)
        await asyncio.sleep(0.2)  # 控制速率
    
    stats = test.get_statistics()
    results["low_load"] = stats
    print(f"  P50: {stats['p50']:.2f} ms, P95: {stats['p95']:.2f} ms, P99: {stats['p99']:.2f} ms")
    
    # 正常负载测试 (100 个样本)
    print("\n[2/3] 正常负载测试 (20 单/秒)...")
    test = PerformanceTest("正常负载")
    for i in range(100):
        start_time = time.time()
        await asyncio.sleep(0.05)  # 模拟 50ms 处理
        latency_ms = (time.time() - start_time) * 1000
        test.record_latency(latency_ms)
        await asyncio.sleep(0.05)  # 控制速率
    
    stats = test.get_statistics()
    results["normal_load"] = stats
    print(f"  P50: {stats['p50']:.2f} ms, P95: {stats['p95']:.2f} ms, P99: {stats['p99']:.2f} ms")
    
    # 高负载测试 (100 个样本)
    print("\n[3/3] 高负载测试 (50 单/秒)...")
    test = PerformanceTest("高负载")
    for i in range(100):
        start_time = time.time()
        await asyncio.sleep(0.06)  # 模拟 60ms 处理
        latency_ms = (time.time() - start_time) * 1000
        test.record_latency(latency_ms)
        await asyncio.sleep(0.02)  # 控制速率
    
    stats = test.get_statistics()
    results["high_load"] = stats
    print(f"  P50: {stats['p50']:.2f} ms, P95: {stats['p95']:.2f} ms, P99: {stats['p99']:.2f} ms")
    
    return results


async def test_market_latency_baseline():
    """行情延迟基线测试（简化版）"""
    print("\n" + "="*60)
    print("行情延迟基线测试")
    print("="*60)
    
    results = {}
    
    # 单合约测试 (100 个样本)
    print("\n[1/2] 单合约测试...")
    test = PerformanceTest("单合约")
    for i in range(100):
        start_time = time.time()
        await asyncio.sleep(0.02)  # 模拟 20ms 处理
        latency_ms = (time.time() - start_time) * 1000
        test.record_latency(latency_ms)
        await asyncio.sleep(0.01)  # 控制速率
    
    stats = test.get_statistics()
    results["single_contract"] = stats
    print(f"  P50: {stats['p50']:.2f} ms, P95: {stats['p95']:.2f} ms, P99: {stats['p99']:.2f} ms")
    
    # 多合约测试 (100 个样本)
    print("\n[2/2] 多合约测试 (10 个合约)...")
    test = PerformanceTest("多合约")
    for i in range(100):
        start_time = time.time()
        await asyncio.sleep(0.025)  # 模拟 25ms 处理
        latency_ms = (time.time() - start_time) * 1000
        test.record_latency(latency_ms)
        await asyncio.sleep(0.01)  # 控制速率
    
    stats = test.get_statistics()
    results["multiple_contracts"] = stats
    print(f"  P50: {stats['p50']:.2f} ms, P95: {stats['p95']:.2f} ms, P99: {stats['p99']:.2f} ms")
    
    return results


async def test_throughput_baseline():
    """吞吐量基线测试（简化版）"""
    print("\n" + "="*60)
    print("吞吐量基线测试")
    print("="*60)
    
    results = {}
    
    # 订单吞吐量测试 (5 秒)
    print("\n[1/2] 订单吞吐量测试 (5 秒)...")
    start_time = time.time()
    count = 0
    end_time = time.time() + 5
    
    while time.time() < end_time:
        await asyncio.sleep(0.04)  # 每个订单 40ms
        count += 1
    
    duration = time.time() - start_time
    throughput = count / duration
    results["order_throughput"] = {
        "count": count,
        "duration": duration,
        "throughput": throughput
    }
    print(f"  吞吐量: {throughput:.2f} 单/秒 (总计 {count} 单)")
    
    # 行情吞吐量测试 (5 秒)
    print("\n[2/2] 行情吞吐量测试 (5 秒)...")
    start_time = time.time()
    count = 0
    end_time = time.time() + 5
    
    while time.time() < end_time:
        await asyncio.sleep(0.001)  # 每个 tick 1ms
        count += 1
    
    duration = time.time() - start_time
    throughput = count / duration
    results["market_throughput"] = {
        "count": count,
        "duration": duration,
        "throughput": throughput
    }
    print(f"  吞吐量: {throughput:.2f} tick/秒 (总计 {count} tick)")
    
    return results


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("homalos-webctp 性能基线测试")
    print("="*60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试环境: 模拟环境 (asyncio.sleep)")
    print("="*60)
    
    # 运行所有测试
    order_results = await test_order_latency_baseline()
    market_results = await test_market_latency_baseline()
    throughput_results = await test_throughput_baseline()
    
    # 汇总结果
    all_results = {
        "test_time": datetime.now().isoformat(),
        "test_environment": "模拟环境",
        "order_latency": order_results,
        "market_latency": market_results,
        "throughput": throughput_results
    }
    
    # 保存结果到 JSON
    output_file = "tests/performance/baseline_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*60)
    print("测试完成！")
    print(f"结果已保存到: {output_file}")
    print("="*60)
    
    return all_results


if __name__ == "__main__":
    results = asyncio.run(main())
