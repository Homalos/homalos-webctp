#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : benchmark_performance.py
@Date       : 2025/12/19
@Author     : Kiro AI Assistant
@Email      : -
@Software   : PyCharm
@Description: SyncStrategyApi 性能基准测试
"""

import time
import statistics
from typing import List

# 注意：这是一个性能基准测试脚本，用于记录重构前的性能数据
# 实际运行需要连接到 CTP 服务器，这里提供测试框架

def measure_execution_time(func, iterations: int = 100) -> List[float]:
    """
    测量函数执行时间
    
    Args:
        func: 要测量的函数
        iterations: 迭代次数
        
    Returns:
        执行时间列表（秒）
    """
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        times.append(end - start)
    return times


def print_statistics(name: str, times: List[float]) -> None:
    """
    打印统计信息
    
    Args:
        name: 测试名称
        times: 执行时间列表
    """
    mean = statistics.mean(times)
    median = statistics.median(times)
    stdev = statistics.stdev(times) if len(times) > 1 else 0
    min_time = min(times)
    max_time = max(times)
    
    print(f"\n{name}:")
    print(f"  平均: {mean*1000:.2f} ms")
    print(f"  中位数: {median*1000:.2f} ms")
    print(f"  标准差: {stdev*1000:.2f} ms")
    print(f"  最小: {min_time*1000:.2f} ms")
    print(f"  最大: {max_time*1000:.2f} ms")


def benchmark_quote_cache():
    """测试行情缓存性能"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.strategy.internal.cache_manager import _QuoteCache
    
    cache = _QuoteCache()
    
    # 测试更新性能
    def update_quote():
        market_data = {
            'LastPrice': 3500.0,
            'BidPrice1': 3499.0,
            'AskPrice1': 3501.0,
            'Volume': 1000,
        }
        cache.update_from_market_data('rb2605', market_data)
    
    times = measure_execution_time(update_quote, iterations=1000)
    print_statistics("行情缓存更新", times)
    
    # 测试读取性能
    def get_quote():
        cache.get('rb2605')
    
    times = measure_execution_time(get_quote, iterations=1000)
    print_statistics("行情缓存读取", times)


def benchmark_position_cache():
    """测试持仓缓存性能"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.strategy.internal.cache_manager import _PositionCache
    
    cache = _PositionCache()
    
    # 测试更新性能
    def update_position():
        position_data = {
            'pos_long': 5,
            'pos_long_today': 5,
            'pos_long_his': 0,
            'open_price_long': 3500.0,
        }
        cache.update_from_position_data('rb2605', position_data)
    
    times = measure_execution_time(update_position, iterations=1000)
    print_statistics("持仓缓存更新", times)
    
    # 测试读取性能
    def get_position():
        cache.get('rb2605')
    
    times = measure_execution_time(get_position, iterations=1000)
    print_statistics("持仓缓存读取", times)


def benchmark_data_models():
    """测试数据模型性能"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.strategy.internal.data_models import Quote, Position
    
    # 测试 Quote 创建
    def create_quote():
        Quote(
            InstrumentID='rb2605',
            LastPrice=3500.0,
            BidPrice1=3499.0,
            AskPrice1=3501.0,
            Volume=1000,
        )
    
    times = measure_execution_time(create_quote, iterations=10000)
    print_statistics("Quote 对象创建", times)
    
    # 测试 Quote 字典访问
    quote = Quote(InstrumentID='rb2605', LastPrice=3500.0)
    
    def access_quote():
        _ = quote['LastPrice']
    
    times = measure_execution_time(access_quote, iterations=10000)
    print_statistics("Quote 字典访问", times)
    
    # 测试 Position 创建
    def create_position():
        Position(
            pos_long=5,
            pos_long_today=5,
            open_price_long=3500.0,
        )
    
    times = measure_execution_time(create_position, iterations=10000)
    print_statistics("Position 对象创建", times)


def main():
    """运行所有性能基准测试"""
    print("=" * 60)
    print("SyncStrategyApi 性能基准测试")
    print("=" * 60)
    
    print("\n[1] 数据模型性能测试")
    benchmark_data_models()
    
    print("\n[2] 行情缓存性能测试")
    benchmark_quote_cache()
    
    print("\n[3] 持仓缓存性能测试")
    benchmark_position_cache()
    
    print("\n" + "=" * 60)
    print("性能基准测试完成")
    print("=" * 60)
    print("\n注意：这些数据将作为重构后的对比基准")


if __name__ == '__main__':
    main()
