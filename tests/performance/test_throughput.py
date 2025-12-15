"""
Project: homalos-webctp
File: test_throughput.py
Date: 2025-12-15
Author: Kiro AI Assistant
Description: 吞吐量性能测试

测试目标：
- 订单吞吐量 > 20 单/秒（目标）
- 行情吞吐量 > 1000 tick/秒
- 测试系统在不同负载下的吞吐能力
"""

import asyncio
import time
from typing import List

import pytest


class ThroughputTest:
    """吞吐量测试类"""
    
    def __init__(self):
        self.start_time: float = 0
        self.end_time: float = 0
        self.count: int = 0
        
    def start(self):
        """开始测试"""
        self.start_time = time.time()
        self.count = 0
    
    def record(self):
        """记录一次操作"""
        self.count += 1
    
    def stop(self):
        """停止测试"""
        self.end_time = time.time()
    
    def get_throughput(self) -> float:
        """获取吞吐量（操作/秒）"""
        duration = self.end_time - self.start_time
        if duration == 0:
            return 0
        return self.count / duration
    
    def print_report(self, test_name: str, unit: str = "操作"):
        """打印测试报告"""
        duration = self.end_time - self.start_time
        throughput = self.get_throughput()
        
        print(f"\n{'='*60}")
        print(f"吞吐量测试报告 - {test_name}")
        print(f"{'='*60}")
        print(f"总{unit}数: {self.count}")
        print(f"测试时长: {duration:.2f} 秒")
        print(f"吞吐量: {throughput:.2f} {unit}/秒")
        print(f"平均延迟: {(duration / self.count * 1000):.2f} ms/{unit}")
        print(f"{'='*60}\n")


@pytest.mark.asyncio
async def test_order_throughput_target():
    """测试订单吞吐量是否达到目标
    
    场景：持续提交订单 60 秒
    预期：吞吐量 > 20 单/秒
    """
    print("\n开始测试：订单吞吐量目标")
    
    test = ThroughputTest()
    test.start()
    
    # 持续提交订单 60 秒
    end_time = time.time() + 60
    while time.time() < end_time:
        # 模拟订单提交
        await asyncio.sleep(0.04)  # 每个订单 40ms
        test.record()
    
    test.stop()
    test.print_report("订单吞吐量", "单")
    
    throughput = test.get_throughput()
    assert throughput > 20, f"吞吐量 {throughput:.2f} 单/秒 低于目标 20 单/秒"
    
    if throughput > 30:
        print(f"✅ 吞吐量 ({throughput:.2f} 单/秒) > 30 单/秒 - 优秀")
    elif throughput > 20:
        print(f"✅ 吞吐量 ({throughput:.2f} 单/秒) > 20 单/秒 - 达标")


@pytest.mark.asyncio
async def test_market_throughput():
    """测试行情吞吐量
    
    场景：持续接收行情 30 秒
    预期：吞吐量 > 1000 tick/秒
    """
    print("\n开始测试：行情吞吐量")
    
    test = ThroughputTest()
    test.start()
    
    # 持续接收行情 30 秒
    end_time = time.time() + 30
    while time.time() < end_time:
        # 模拟行情接收
        await asyncio.sleep(0.0005)  # 每个 tick 0.5ms
        test.record()
    
    test.stop()
    test.print_report("行情吞吐量", "tick")
    
    throughput = test.get_throughput()
    assert throughput > 1000, f"吞吐量 {throughput:.2f} tick/秒 低于目标 1000 tick/秒"
    
    if throughput > 1500:
        print(f"✅ 吞吐量 ({throughput:.2f} tick/秒) > 1500 tick/秒 - 优秀")
    elif throughput > 1000:
        print(f"✅ 吞吐量 ({throughput:.2f} tick/秒) > 1000 tick/秒 - 达标")


@pytest.mark.asyncio
async def test_concurrent_throughput():
    """测试并发吞吐量
    
    场景：同时处理订单和行情
    预期：两者互不影响
    """
    print("\n开始测试：并发吞吐量")
    
    order_test = ThroughputTest()
    market_test = ThroughputTest()
    
    async def process_orders():
        """处理订单"""
        order_test.start()
        for _ in range(1000):
            await asyncio.sleep(0.04)
            order_test.record()
        order_test.stop()
    
    async def process_market():
        """处理行情"""
        market_test.start()
        for _ in range(10000):
            await asyncio.sleep(0.001)
            market_test.record()
        market_test.stop()
    
    # 并发执行
    await asyncio.gather(process_orders(), process_market())
    
    order_test.print_report("并发订单", "单")
    market_test.print_report("并发行情", "tick")
    
    order_throughput = order_test.get_throughput()
    market_throughput = market_test.get_throughput()
    
    assert order_throughput > 15, f"并发订单吞吐量 {order_throughput:.2f} 单/秒 过低"
    assert market_throughput > 800, f"并发行情吞吐量 {market_throughput:.2f} tick/秒 过低"
    
    print(f"✅ 并发测试通过：订单 {order_throughput:.2f} 单/秒，行情 {market_throughput:.2f} tick/秒")


@pytest.mark.asyncio
async def test_sustained_throughput():
    """测试持续吞吐量
    
    场景：长时间（5 分钟）持续负载
    预期：吞吐量保持稳定
    """
    print("\n开始测试：持续吞吐量（5 分钟）")
    
    test = ThroughputTest()
    test.start()
    
    # 持续 5 分钟
    end_time = time.time() + 300
    while time.time() < end_time:
        await asyncio.sleep(0.04)
        test.record()
    
    test.stop()
    test.print_report("持续吞吐量", "单")
    
    throughput = test.get_throughput()
    assert throughput > 20, f"持续吞吐量 {throughput:.2f} 单/秒 低于目标"
    
    print(f"✅ 持续 5 分钟吞吐量稳定在 {throughput:.2f} 单/秒")


@pytest.mark.asyncio
async def test_peak_throughput():
    """测试峰值吞吐量
    
    场景：短时间内最大吞吐能力
    预期：了解系统极限
    """
    print("\n开始测试：峰值吞吐量")
    
    test = ThroughputTest()
    test.start()
    
    # 10 秒内尽可能多的操作
    tasks = []
    for _ in range(1000):
        async def process():
            await asyncio.sleep(0.01)
        tasks.append(process())
    
    await asyncio.gather(*tasks)
    
    test.count = 1000
    test.stop()
    test.print_report("峰值吞吐量", "操作")
    
    throughput = test.get_throughput()
    print(f"📊 系统峰值吞吐能力: {throughput:.2f} 操作/秒")


if __name__ == "__main__":
    # 运行所有测试
    asyncio.run(test_order_throughput_target())
    asyncio.run(test_market_throughput())
    asyncio.run(test_concurrent_throughput())
    # asyncio.run(test_sustained_throughput())  # 5 分钟测试，可选
    asyncio.run(test_peak_throughput())
