# homalos-webctp 性能调优指南

**版本**: v0.2.0  
**更新日期**: 2025-12-15  
**适用场景**: 生产环境性能优化

---

## 概述

本指南提供了 homalos-webctp 系统的性能调优建议，帮助用户根据实际部署场景优化系统性能。通过合理配置参数，可以在延迟、吞吐量、资源使用等方面获得显著提升。

### 调优目标

- **降低延迟**: 订单延迟 P95 < 100ms，行情延迟 P95 < 50ms
- **提高吞吐量**: 订单吞吐量 > 20 单/秒
- **优化资源使用**: 降低 CPU 和内存占用
- **提高可靠性**: 快速降级，保证核心功能可用

---

## 配置参数详解

### 1. Redis 缓存配置

Redis 缓存是性能优化的核心组件，合理配置可以显著提升系统性能。

#### 1.1 连接池大小 (MaxConnections)

**默认值**: 50  
**推荐值**: 根据并发客户端数调整

**调优建议**:
```yaml
# 小规模部署（< 10 个客户端）
MaxConnections: 20

# 中等规模部署（10-50 个客户端）
MaxConnections: 50

# 大规模部署（> 50 个客户端）
MaxConnections: 100
```

**计算公式**:
```
MaxConnections = 并发客户端数 × 每客户端平均并发请求数 × 1.5（冗余系数）
```

**影响**:
- 过小：连接等待，增加延迟
- 过大：资源浪费，增加 Redis 负担

#### 1.2 超时配置 (SocketTimeout / SocketConnectTimeout)

**默认值**: 2.0 秒（优化后）  
**原始值**: 5.0 秒

**调优建议**:
```yaml
# 本地 Redis 部署（推荐）
SocketTimeout: 2.0
SocketConnectTimeout: 2.0

# 远程 Redis 部署
SocketTimeout: 3.0
SocketConnectTimeout: 5.0

# 高延迟网络环境
SocketTimeout: 5.0
SocketConnectTimeout: 10.0
```

**优化效果**:
- 本地部署从 5s 降低到 2s，降级响应速度提升 60%
- 减少因 Redis 超时导致的请求阻塞

**权衡**:
- 超时过短：可能误判 Redis 故障，频繁降级
- 超时过长：降级响应慢，影响用户体验

#### 1.3 缓存 TTL 配置

##### 行情快照 TTL (MarketSnapshotTTL)

**默认值**: 30 秒（优化后）  
**原始值**: 60 秒

**调优建议**:
```yaml
# 高频交易场景（推荐）
MarketSnapshotTTL: 30

# 低频交易场景
MarketSnapshotTTL: 60

# 极低频场景（如日内策略）
MarketSnapshotTTL: 120
```

**优化效果**:
- 从 60s 降低到 30s，减少 50% 的过期数据返回概率
- 提高行情数据的实时性

**权衡**:
- TTL 过短：缓存命中率降低，增加 CTP API 查询
- TTL 过长：可能返回过期数据，影响交易决策

##### 实时 Tick TTL (MarketTickTTL)

**默认值**: 5 秒  
**推荐值**: 保持 5 秒

**说明**: 实时 tick 数据时效性要求高，5 秒 TTL 已经比较合理，不建议调整。

##### 订单 TTL (OrderTTL)

**默认值**: 86400 秒（24 小时）  
**推荐值**: 根据业务需求调整

**调优建议**:
```yaml
# 日内交易（推荐）
OrderTTL: 3600  # 1 小时

# 短期持仓
OrderTTL: 86400  # 24 小时

# 长期持仓
OrderTTL: 604800  # 7 天
```

**优化效果**:
- 从 24 小时降低到 1 小时，减少 96% 的 Redis 内存占用
- 适合日内交易场景，减少历史订单查询

---

### 2. 性能监控配置

性能监控对系统性能有一定影响，合理配置可以平衡监控需求和性能开销。

#### 2.1 采样率 (SampleRate)

**默认值**: 1.0（100% 采样）  
**推荐值**: 根据环境调整

**调优建议**:
```yaml
# 开发/测试环境
SampleRate: 1.0  # 100% 采样，便于调试

# 生产环境（推荐）
SampleRate: 0.5  # 50% 采样，平衡性能和监控

# 高负载生产环境
SampleRate: 0.3  # 30% 采样，降低监控开销

# 极高负载环境
SampleRate: 0.1  # 10% 采样，最小化性能影响
```

**优化效果**:
- 从 100% 降低到 50%，监控开销降低约 50%
- 在高负载下可以显著降低 CPU 使用率

**权衡**:
- 采样率过低：可能遗漏性能问题
- 采样率过高：增加系统开销

#### 2.2 报告间隔 (ReportInterval)

**默认值**: 60 秒  
**推荐值**: 保持 60 秒

**调优建议**:
```yaml
# 详细监控
ReportInterval: 30  # 30 秒

# 标准监控（推荐）
ReportInterval: 60  # 60 秒

# 轻量监控
ReportInterval: 300  # 5 分钟
```

---

### 3. 策略管理配置

策略管理配置影响多策略并行运行的性能。

#### 3.1 最大策略数量 (MaxStrategies)

**默认值**: 10  
**推荐值**: 根据服务器资源调整

**调优建议**:
```yaml
# 小型服务器（2 核 4GB）
MaxStrategies: 5

# 中型服务器（4 核 8GB）
MaxStrategies: 10

# 大型服务器（8 核 16GB+）
MaxStrategies: 20
```

#### 3.2 单策略资源配额

**默认值**:
- DefaultMaxMemoryMB: 512
- DefaultMaxCPUPercent: 50.0

**调优建议**:
```yaml
# 轻量级策略
DefaultMaxMemoryMB: 256
DefaultMaxCPUPercent: 30.0

# 标准策略（推荐）
DefaultMaxMemoryMB: 512
DefaultMaxCPUPercent: 50.0

# 重量级策略
DefaultMaxMemoryMB: 1024
DefaultMaxCPUPercent: 80.0
```

---

## 按场景调优

### 场景 1：高频交易（低延迟优先）

**特点**: 订单频繁，对延迟敏感

**推荐配置**:
```yaml
Redis:
  Enabled: true
  MaxConnections: 100
  SocketTimeout: 1.0
  SocketConnectTimeout: 2.0
  MarketSnapshotTTL: 30
  MarketTickTTL: 3
  OrderTTL: 3600

Metrics:
  Enabled: true
  ReportInterval: 60
  SampleRate: 0.3  # 降低监控开销

Strategy:
  MaxStrategies: 5  # 限制策略数量，保证单策略性能
```

**预期效果**:
- 订单延迟 P95 < 50ms
- 行情延迟 P95 < 30ms
- 订单吞吐量 > 30 单/秒

---

### 场景 2：多策略并行（吞吐量优先）

**特点**: 多个策略同时运行，对吞吐量要求高

**推荐配置**:
```yaml
Redis:
  Enabled: true
  MaxConnections: 100
  SocketTimeout: 2.0
  SocketConnectTimeout: 2.0
  MarketSnapshotTTL: 30
  MarketTickTTL: 5
  OrderTTL: 86400

Metrics:
  Enabled: true
  ReportInterval: 60
  SampleRate: 0.5

Strategy:
  MaxStrategies: 20  # 支持更多策略
  DefaultMaxMemoryMB: 256  # 降低单策略内存
  DefaultMaxCPUPercent: 30.0  # 降低单策略 CPU
```

**预期效果**:
- 支持 10-20 个策略并行
- 总吞吐量 > 50 单/秒
- 策略间隔离良好

---

### 场景 3：低频交易（资源优化）

**特点**: 订单不频繁，优化资源使用

**推荐配置**:
```yaml
Redis:
  Enabled: true
  MaxConnections: 20
  SocketTimeout: 3.0
  SocketConnectTimeout: 5.0
  MarketSnapshotTTL: 60
  MarketTickTTL: 10
  OrderTTL: 86400

Metrics:
  Enabled: true
  ReportInterval: 300  # 5 分钟报告一次
  SampleRate: 0.1  # 最小化监控开销

Strategy:
  MaxStrategies: 5
```

**预期效果**:
- CPU 使用率 < 30%
- 内存使用率 < 50%
- 满足基本性能要求

---

### 场景 4：无 Redis 部署（降级模式）

**特点**: 不使用 Redis，直接查询 CTP API

**推荐配置**:
```yaml
Redis:
  Enabled: false  # 禁用 Redis

Metrics:
  Enabled: true
  ReportInterval: 60
  SampleRate: 1.0  # 可以提高采样率，因为没有 Redis 开销

Strategy:
  MaxStrategies: 5  # 限制策略数量
```

**预期效果**:
- 订单延迟 P95 < 100ms（无缓存加速）
- 系统简单，易于部署
- 适合测试和小规模部署

---

## 调优效果验证

### 1. 使用配置验证脚本

```bash
# 激活虚拟环境
.venv\Scripts\activate

# 运行配置验证
python tests/performance/verify_tuning.py --config config/config_md.yaml
```

### 2. 运行性能测试

```bash
# 运行优化后性能测试
python tests/performance/run_optimized_test.py

# 对比基线结果
# 查看 tests/performance/optimized_results.json
```

### 3. 监控关键指标

**延迟指标**:
- 订单延迟 P95 < 100ms
- 行情延迟 P95 < 50ms

**吞吐量指标**:
- 订单吞吐量 > 20 单/秒
- 行情吞吐量 > 1000 tick/秒

**资源指标**:
- CPU 使用率 < 70%
- 内存使用率 < 80%
- Redis 命中率 > 65%

### 4. 查看性能报告

系统会每分钟输出性能报告到日志：

```bash
# 查看日志
type logs\webctp.log | findstr "性能报告"
```

---

## 常见问题

### Q1: Redis 超时频繁，如何调优？

**症状**: 日志中频繁出现 "Redis 操作超时" 警告

**原因**:
1. Redis 服务器负载过高
2. 网络延迟较大
3. 超时配置过短

**解决方案**:
```yaml
# 增加超时时间
Redis:
  SocketTimeout: 5.0  # 从 2.0 增加到 5.0
  SocketConnectTimeout: 10.0  # 从 2.0 增加到 10.0
```

---

### Q2: 缓存命中率低，如何优化？

**症状**: Redis 命中率 < 50%

**原因**:
1. TTL 设置过短
2. 查询的数据不在缓存中
3. 缓存预热不足

**解决方案**:
```yaml
# 增加 TTL
Redis:
  MarketSnapshotTTL: 60  # 从 30 增加到 60
  
# 或实现缓存预热逻辑
```

---

### Q3: 系统延迟高，如何排查？

**排查步骤**:

1. **查看性能报告**
```bash
type logs\webctp.log | findstr "P95"
```

2. **检查 Redis 状态**
```bash
redis-cli info stats
```

3. **检查系统资源**
```bash
# CPU 使用率
wmic cpu get loadpercentage

# 内存使用率
wmic OS get FreePhysicalMemory,TotalVisibleMemorySize
```

4. **调整配置**
- 降低采样率（SampleRate: 0.3）
- 增加连接池（MaxConnections: 100）
- 优化 TTL 配置

---

### Q4: 监控开销过大，如何降低？

**症状**: CPU 使用率高，性能下降

**解决方案**:
```yaml
Metrics:
  SampleRate: 0.1  # 降低到 10% 采样
  ReportInterval: 300  # 增加到 5 分钟
```

---

## 调优检查清单

使用以下检查清单确保配置正确：

- [ ] Redis 超时配置符合部署环境（本地 2s，远程 3-5s）
- [ ] 行情快照 TTL 符合交易频率（高频 30s，低频 60s）
- [ ] 性能监控采样率符合环境（开发 1.0，生产 0.5）
- [ ] 连接池大小符合并发需求
- [ ] 策略数量限制符合服务器资源
- [ ] 已运行配置验证脚本
- [ ] 已运行性能测试验证效果
- [ ] 已查看性能报告确认指标达标

---

## 进阶调优

### 1. 使用 uvloop（可选）

uvloop 是 asyncio 的高性能替代品，可以提升 20-30% 的性能。

**安装**:
```bash
uv add uvloop
```

**使用**:
```python
import uvloop
uvloop.install()
```

### 2. 使用 Redis 集群（可选）

对于高并发场景，可以使用 Redis 集群提高吞吐量。

**配置**:
```yaml
Redis:
  # 使用 Redis Sentinel 或 Cluster
  Host: redis-cluster-endpoint
  Port: 6379
```

### 3. 使用专用网络（可选）

将 Redis 和应用部署在同一网络，减少网络延迟。

---

## 相关文档

- [性能基线报告](./performance_baseline_report.md) - 基线测试结果
- [性能优化报告](./performance_report_CN.md) - 优化前后对比
- [监控指南](./monitoring_guide_CN.md) - 性能监控配置
- [故障排查](./troubleshooting_CN.md) - 性能问题排查

---

## 总结

通过合理配置 Redis 超时、缓存 TTL、性能监控采样率等参数，可以在不修改代码的情况下显著提升系统性能。建议：

1. **从保守优化开始**: 先调整超时和 TTL，验证效果
2. **根据场景调整**: 不同场景使用不同配置
3. **持续监控**: 使用性能报告持续监控系统状态
4. **渐进式优化**: 逐步调整参数，避免过度优化

---

**文档版本**: 1.0  
**最后更新**: 2025-12-15  
**维护者**: homalos-webctp 团队
