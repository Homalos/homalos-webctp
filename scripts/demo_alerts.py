#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : demo_alerts.py
@Date       : 2025/12/15 00:00
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: 演示性能告警功能
"""

import asyncio
from src.utils.metrics import MetricsCollector
from src.utils.config import MetricsConfig


async def demo_alerts():
    """演示性能告警功能"""
    
    print("=" * 60)
    print("性能告警功能演示")
    print("=" * 60)
    
    # 创建配置（使用较低的阈值以便演示）
    config = MetricsConfig(
        enabled=True,
        report_interval=5,  # 5 秒报告一次（演示用）
        sample_rate=1.0,
        latency_warning_threshold_ms=50.0,  # 50ms 阈值
        cache_hit_rate_warning_threshold=60.0,  # 60% 阈值
        cpu_warning_threshold=70.0,  # 70% 阈值
        memory_warning_threshold=70.0,  # 70% 阈值
    )
    
    # 创建指标收集器
    collector = MetricsCollector(config=config)
    
    print("\n配置的告警阈值:")
    print(f"  - 延迟告警阈值: {config.latency_warning_threshold_ms} ms")
    print(f"  - Redis 命中率告警阈值: {config.cache_hit_rate_warning_threshold}%")
    print(f"  - CPU 使用率告警阈值: {config.cpu_warning_threshold}%")
    print(f"  - 内存使用率告警阈值: {config.memory_warning_threshold}%")
    
    # 场景 1: 正常情况（不触发告警）
    print("\n" + "=" * 60)
    print("场景 1: 正常情况（不触发告警）")
    print("=" * 60)
    
    for _ in range(10):
        collector.record_latency("order_latency", 30.0)  # 低于 50ms 阈值
    
    collector.record_counter("cache_hit", 70)  # 70% 命中率
    collector.record_counter("cache_miss", 30)
    
    print("\n记录的指标:")
    print("  - 订单延迟: 30ms (低于阈值)")
    print("  - Redis 命中率: 70% (高于阈值)")
    print("\n生成报告...")
    await collector._report()
    print("✅ 未触发告警（正常情况）")
    
    # 场景 2: 延迟超过阈值
    print("\n" + "=" * 60)
    print("场景 2: 延迟超过阈值")
    print("=" * 60)
    
    # 清空之前的数据
    collector._latencies.clear()
    collector._counters.clear()
    
    for _ in range(10):
        collector.record_latency("order_latency", 80.0)  # 超过 50ms 阈值
    
    print("\n记录的指标:")
    print("  - 订单延迟: 80ms (超过 50ms 阈值)")
    print("\n生成报告...")
    await collector._report()
    print("⚠️ 应该触发延迟告警")
    
    # 场景 3: Redis 命中率过低
    print("\n" + "=" * 60)
    print("场景 3: Redis 命中率过低")
    print("=" * 60)
    
    # 清空之前的数据
    collector._latencies.clear()
    collector._counters.clear()
    
    collector.record_counter("cache_hit", 40)  # 40% 命中率
    collector.record_counter("cache_miss", 60)
    
    print("\n记录的指标:")
    print("  - Redis 命中率: 40% (低于 60% 阈值)")
    print("\n生成报告...")
    await collector._report()
    print("⚠️ 应该触发 Redis 命中率告警")
    
    # 场景 4: 多个告警同时触发
    print("\n" + "=" * 60)
    print("场景 4: 多个告警同时触发")
    print("=" * 60)
    
    # 清空之前的数据
    collector._latencies.clear()
    collector._counters.clear()
    
    # 记录超过阈值的延迟
    for _ in range(10):
        collector.record_latency("order_latency", 100.0)  # 超过 50ms 阈值
        collector.record_latency("market_latency", 90.0)  # 超过 50ms 阈值
    
    # 记录低命中率
    collector.record_counter("cache_hit", 30)  # 30% 命中率
    collector.record_counter("cache_miss", 70)
    
    print("\n记录的指标:")
    print("  - 订单延迟: 100ms (超过 50ms 阈值)")
    print("  - 行情延迟: 90ms (超过 50ms 阈值)")
    print("  - Redis 命中率: 30% (低于 60% 阈值)")
    print("\n生成报告...")
    await collector._report()
    print("⚠️ 应该触发多个告警")
    
    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)
    print("\n提示:")
    print("  - 告警会记录在日志文件中（logs/webctp.log）")
    print("  - 可以使用 grep '⚠️' logs/webctp.log 查看所有告警")
    print("  - 可以使用 grep 'metrics_alert' logs/webctp.log 过滤告警日志")
    print("  - 在生产环境中，建议根据实际情况调整告警阈值")


if __name__ == "__main__":
    asyncio.run(demo_alerts())
