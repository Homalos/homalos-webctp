# 性能测试套件

**项目**: homalos-webctp  
**版本**: v0.2.0  
**创建日期**: 2025-12-15

---

## 概述

本目录包含 homalos-webctp 的性能测试脚本，用于验证系统性能是否达到目标。

## 测试文件

### 1. test_order_latency.py
**订单延迟测试**

测试场景：
- 低负载：每秒 5 个订单
- 正常负载：每秒 20 个订单
- 高负载：每秒 50 个订单
- 突发负载：1 秒内 100 个订单

性能目标：
- P95 < 100 ms（目标）
- P95 < 150 ms（适中阈值）

### 2. test_market_latency.py
**行情延迟测试**

测试场景：
- 单合约：1 个合约，1000 个 tick
- 多合约：10 个合约，每个 100 个 tick
- 高频行情：每秒 500 个 tick
- 带缓存：测试 Redis 缓存效果

性能目标：
- P95 < 50 ms（目标）
- P95 < 80 ms（适中阈值）

### 3. test_throughput.py
**吞吐量测试**

测试场景：
- 订单吞吐量：持续 60 秒
- 行情吞吐量：持续 30 秒
- 并发吞吐量：同时处理订单和行情
- 持续吞吐量：5 分钟持续负载
- 峰值吞吐量：短时间最大能力

性能目标：
- 订单吞吐量 > 20 单/秒
- 行情吞吐量 > 1000 tick/秒

---

## 运行测试

### 运行所有性能测试
```bash
# 激活虚拟环境
.venv\Scripts\activate

# 运行所有性能测试
pytest tests/performance/ -v

# 运行特定测试
pytest tests/performance/test_order_latency.py -v
pytest tests/performance/test_market_latency.py -v
pytest tests/performance/test_throughput.py -v
```

### 运行单个测试函数
```bash
# 运行特定测试函数
pytest tests/performance/test_order_latency.py::test_order_latency_low_load -v
```

### 直接运行脚本
```bash
# 直接运行测试脚本（不使用 pytest）
python tests/performance/test_order_latency.py
python tests/performance/test_market_latency.py
python tests/performance/test_throughput.py
```

---

## 测试报告示例

### 订单延迟测试报告
```
============================================================
订单延迟测试报告 - 低负载
============================================================
样本数: 300
最小值: 40.12 ms
最大值: 45.67 ms
平均值: 42.34 ms
中位数: 42.15 ms
P50: 42.15 ms
P95: 44.23 ms
P99: 45.12 ms
============================================================

✅ P95 延迟 (44.23 ms) < 100 ms - 达标
```

### 行情延迟测试报告
```
============================================================
行情延迟测试报告 - 单合约
============================================================
样本数: 1000
最小值: 20.05 ms
最大值: 25.34 ms
平均值: 22.15 ms
中位数: 22.10 ms
P50: 22.10 ms
P95: 23.45 ms
P99: 24.12 ms
============================================================

✅ P95 延迟 (23.45 ms) < 50 ms - 达标
```

### 吞吐量测试报告
```
============================================================
吞吐量测试报告 - 订单吞吐量
============================================================
总单数: 1500
测试时长: 60.00 秒
吞吐量: 25.00 单/秒
平均延迟: 40.00 ms/单
============================================================

✅ 吞吐量 (25.00 单/秒) > 20 单/秒 - 达标
```

---

## 注意事项

### 1. 测试环境
- 这些是模拟测试，使用 `asyncio.sleep()` 模拟处理时间
- 实际性能需要在真实环境（SimNow）中测试
- 建议在生产环境部署前进行完整测试

### 2. 性能目标
- 目标值基于 v0.2.0 的性能优化成果
- 实际性能可能因硬件、网络等因素有所不同
- 可根据实际情况调整阈值

### 3. 测试时长
- 部分测试（如持续吞吐量）需要较长时间（5 分钟）
- 可以根据需要跳过长时间测试
- 建议在 CI/CD 中只运行快速测试

---

## 与真实环境集成

### 集成到 SimNow 测试

要在真实环境中测试，需要：

1. 启动 homalos-webctp 服务
2. 使用 WebSocket 客户端连接
3. 发送真实的订单和行情请求
4. 记录实际延迟和吞吐量

示例代码：
```python
import asyncio
import websockets
import time

async def test_real_order_latency():
    uri = "ws://localhost:8081"
    async with websockets.connect(uri) as websocket:
        # 发送订单
        start_time = time.time()
        await websocket.send(json.dumps({
            "action": "insert_order",
            "data": {...}
        }))
        
        # 接收回报
        response = await websocket.recv()
        end_time = time.time()
        
        latency_ms = (end_time - start_time) * 1000
        print(f"订单延迟: {latency_ms:.2f} ms")
```

---

## 相关文档

- [性能报告](../../docs/performance_report_CN.md) - 详细的性能测试结果
- [监控指南](../../docs/monitoring_guide_CN.md) - 性能监控配置
- [故障排查](../../docs/troubleshooting_CN.md) - 性能问题排查

---

**最后更新**: 2025-12-15  
**维护者**: homalos-webctp 团队
