# 迁移指南 - 升级到性能优化版本

**版本**: 从 v0.1.x 升级到 v0.2.0  
**更新日期**: 2025-12-15

## 目录

- [概述](#概述)
- [版本变更说明](#版本变更说明)
- [兼容性说明](#兼容性说明)
- [迁移前准备](#迁移前准备)
- [迁移步骤](#迁移步骤)
- [配置文件变更](#配置文件变更)
- [新功能使用](#新功能使用)
- [迁移检查清单](#迁移检查清单)
- [常见问题](#常见问题)
- [回滚方案](#回滚方案)

## 概述

本指南帮助您从 homalos-webctp v0.1.x 升级到 v0.2.0（性能优化版本）。

### 主要变更

v0.2.0 引入了以下重大改进：

- ✅ **Redis 缓存支持**: 可选的 Redis 缓存层，提升查询性能
- ✅ **优化的序列化**: 使用 orjson 和 msgpack 提升性能
- ✅ **多策略支持**: 支持多个交易策略并行运行
- ✅ **性能监控**: 完整的性能指标收集和监控
- ✅ **智能告警**: 自动检测性能异常并发出告警

### 升级收益

- **性能提升**: 预期订单延迟降低 30-50%
- **更好的可观测性**: 实时性能监控和告警
- **更高的可靠性**: 缓存降级机制和错误隔离
- **更强的扩展性**: 支持多策略并行运行

### 升级风险

- **低风险**: 完全向后兼容，现有客户端无需修改
- **可选功能**: 所有新功能都是可选的，不启用不影响现有功能
- **平滑升级**: 支持渐进式启用新功能

## 版本变更说明

### v0.2.0 (2025-12-15)

**新增功能**:
- Redis 缓存集成
- 性能监控和告警系统
- 多策略管理支持
- 优化的消息序列化

**改进**:
- 提升系统性能
- 增强错误处理
- 完善日志记录

**依赖变更**:
- 新增: `redis>=5.0.0`
- 新增: `orjson>=3.9.0`
- 新增: `msgpack>=1.0.0`
- 新增: `psutil>=5.9.0`（可选，用于系统资源监控）

**配置变更**:
- 新增: `Redis` 配置节（可选）
- 新增: `Metrics` 配置节（可选）
- 新增: `Strategy` 配置节（可选）

**API 变更**:
- 无破坏性变更
- 新增策略管理相关 WebSocket 接口（可选使用）

## 兼容性说明

### 向后兼容

✅ **完全向后兼容**

- 现有 WebSocket 客户端无需修改
- JSON 协议格式保持不变
- 所有现有 API 端点保持不变
- 配置文件向后兼容（新配置项可选）

### 客户端兼容性

| 客户端版本 | v0.2.0 兼容性 | 说明 |
|-----------|--------------|------|
| v0.1.x | ✅ 完全兼容 | 无需修改 |
| 自定义客户端 | ✅ 完全兼容 | 只要遵循 JSON 协议即可 |

### 配置兼容性

| 配置项 | v0.1.x | v0.2.0 | 说明 |
|-------|--------|--------|------|
| 基础配置 | ✅ | ✅ | 完全兼容 |
| Redis 配置 | ❌ | ✅ | 新增，可选 |
| Metrics 配置 | ❌ | ✅ | 新增，可选 |
| Strategy 配置 | ❌ | ✅ | 新增，可选 |

## 迁移前准备

### 1. 备份

**备份配置文件**:
```bash
# Windows
copy config\config_md.yaml config\config_md.yaml.backup
copy config\config_td.yaml config\config_td.yaml.backup

# Linux/Mac
cp config/config_md.yaml config/config_md.yaml.backup
cp config/config_td.yaml config/config_td.yaml.backup
```

**备份数据**:
```bash
# 备份 con_file 目录（CTP 连接文件）
# Windows
xcopy /E /I con_file con_file_backup

# Linux/Mac
cp -r con_file con_file_backup
```

### 2. 检查环境

**检查 Python 版本**:
```bash
python --version
# 应该是 Python 3.13.x
```

**检查 UV 版本**:
```bash
uv --version
# 应该是最新版本
```

### 3. 准备 Redis（可选）

如果计划使用 Redis 缓存功能：

**Windows**:
```bash
# 下载 Redis for Windows
# https://github.com/microsoftarchive/redis/releases

# 或使用 WSL 安装 Redis
wsl --install
wsl
sudo apt-get update
sudo apt-get install redis-server
redis-server
```

**Linux/Mac**:
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis

# macOS
brew install redis
brew services start redis

# 验证 Redis 运行
redis-cli ping
# 应该返回 PONG
```

### 4. 测试环境准备

建议先在测试环境（如 SimNow）进行升级测试：

1. 准备测试账号
2. 准备测试客户端
3. 准备性能测试脚本

## 迁移步骤

### 步骤 1: 停止现有服务

```bash
# 停止行情服务和交易服务
# 按 Ctrl+C 或关闭终端窗口
```

### 步骤 2: 更新代码

**从 Git 更新**:
```bash
# 保存当前更改
git stash

# 拉取最新代码
git pull origin main

# 切换到 v0.2.0 标签
git checkout v0.2.0

# 恢复本地更改（如果有）
git stash pop
```

**或下载发布包**:
```bash
# 下载 v0.2.0 发布包
# 解压并替换文件
```

### 步骤 3: 更新依赖

```bash
# 激活虚拟环境
.venv\Scripts\activate

# 更新依赖
uv sync

# 验证依赖安装
uv pip list | grep redis
uv pip list | grep orjson
uv pip list | grep msgpack
```

### 步骤 4: 更新配置文件

**最小化升级**（不启用新功能）:

配置文件无需修改，直接使用现有配置即可。

**启用新功能**:

参考 [配置文件变更](#配置文件变更) 章节添加新配置。

### 步骤 5: 运行测试

```bash
# 激活虚拟环境
.venv\Scripts\activate

# 运行测试套件
pytest

# 确保所有测试通过
```

### 步骤 6: 启动服务

```bash
# 激活虚拟环境
.venv\Scripts\activate

# 启动行情服务
python main.py --config=./config/config_md.yaml --app_type=md

# 启动交易服务（新终端）
python main.py --config=./config/config_td.yaml --app_type=td
```

### 步骤 7: 验证功能

**验证基础功能**:
1. 连接 WebSocket
2. 登录
3. 订阅行情
4. 查询账户信息
5. 提交测试订单

**验证新功能**（如果启用）:
1. 检查 Redis 连接状态
2. 查看性能报告
3. 测试缓存功能

### 步骤 8: 监控运行

```bash
# 实时查看日志
tail -f logs/webctp.log

# 查看性能报告
grep "性能指标报告" logs/webctp.log -A 30

# 查看告警
grep "⚠️" logs/webctp.log
```


## 配置文件变更

### 基础配置（无变更）

以下配置保持不变：

```yaml
TdFrontAddress: tcp://182.254.243.31:40001
MdFrontAddress: tcp://182.254.243.31:40011
BrokerID: "9999"
AuthCode: "0000000000000000"
AppID: simnow_client_test
Port: 8080
Host: 127.0.0.1
LogLevel: INFO
HeartbeatInterval: 30.0
HeartbeatTimeout: 60.0
```

### 新增配置（可选）

#### Redis 缓存配置

**添加到配置文件**:
```yaml
# Redis 缓存配置（可选，默认禁用）
Redis:
  Enabled: true                    # 启用 Redis 缓存
  Host: localhost                  # Redis 服务器地址
  Port: 6379                       # Redis 端口
  Password: ""                     # Redis 密码（如果有）
  DB: 0                            # Redis 数据库编号
  MaxConnections: 50               # 最大连接数
  SocketTimeout: 5.0               # 套接字超时（秒）
  SocketConnectTimeout: 5.0        # 连接超时（秒）
  MarketSnapshotTTL: 60            # 行情快照 TTL（秒）
  MarketTickTTL: 5                 # 实时 tick TTL（秒）
  OrderTTL: 86400                  # 订单 TTL（秒，24小时）
```

**配置说明**:
- `Enabled`: 是否启用 Redis 缓存
  - `true`: 启用（需要 Redis 服务器）
  - `false`: 禁用（默认）
- `Host`: Redis 服务器地址
- `Port`: Redis 端口，默认 6379
- `Password`: Redis 密码，如果没有设置密码则留空
- `DB`: Redis 数据库编号，默认 0
- `MaxConnections`: 连接池最大连接数
- `SocketTimeout`: 套接字操作超时时间
- `SocketConnectTimeout`: 连接超时时间
- `MarketSnapshotTTL`: 行情快照缓存过期时间
- `MarketTickTTL`: 实时 tick 缓存过期时间
- `OrderTTL`: 订单缓存过期时间

**环境变量配置**:
```bash
# Windows CMD
set WEBCTP_REDIS_ENABLED=true
set WEBCTP_REDIS_HOST=localhost
set WEBCTP_REDIS_PORT=6379

# Windows PowerShell
$env:WEBCTP_REDIS_ENABLED="true"
$env:WEBCTP_REDIS_HOST="localhost"
$env:WEBCTP_REDIS_PORT="6379"
```

#### 性能监控配置

**添加到配置文件**:
```yaml
# 性能监控配置（可选，默认启用）
Metrics:
  Enabled: true                              # 启用性能监控
  ReportInterval: 60                         # 报告间隔（秒）
  SampleRate: 1.0                            # 采样率（0.0-1.0）
  
  # 告警阈值配置
  LatencyWarningThresholdMs: 100.0           # 延迟告警阈值（毫秒）
  CacheHitRateWarningThreshold: 50.0         # Redis 命中率告警阈值（百分比）
  CpuWarningThreshold: 80.0                  # CPU 使用率告警阈值（百分比）
  MemoryWarningThreshold: 80.0               # 内存使用率告警阈值（百分比）
```

**配置说明**:
- `Enabled`: 是否启用性能监控，默认 `true`
- `ReportInterval`: 性能报告生成间隔（秒）
- `SampleRate`: 延迟指标采样率（0.0-1.0）
- `LatencyWarningThresholdMs`: 延迟告警阈值（毫秒）
- `CacheHitRateWarningThreshold`: Redis 命中率告警阈值（百分比）
- `CpuWarningThreshold`: CPU 使用率告警阈值（百分比）
- `MemoryWarningThreshold`: 内存使用率告警阈值（百分比）

**环境变量配置**:
```bash
# Windows CMD
set WEBCTP_METRICS_ENABLED=true
set WEBCTP_METRICS_INTERVAL=60
set WEBCTP_METRICS_LATENCY_WARNING_THRESHOLD=100.0

# Windows PowerShell
$env:WEBCTP_METRICS_ENABLED="true"
$env:WEBCTP_METRICS_INTERVAL="60"
$env:WEBCTP_METRICS_LATENCY_WARNING_THRESHOLD="100.0"
```

#### 策略管理配置

**添加到配置文件**:
```yaml
# 策略管理配置（可选）
Strategy:
  MaxStrategies: 10                          # 最大策略数量
  DefaultMaxMemoryMB: 512                    # 默认单策略最大内存（MB）
  DefaultMaxCPUPercent: 50.0                 # 默认单策略最大CPU使用率（%）
```

**配置说明**:
- `MaxStrategies`: 系统允许的最大策略数量
- `DefaultMaxMemoryMB`: 单个策略的默认最大内存限制
- `DefaultMaxCPUPercent`: 单个策略的默认最大 CPU 使用率

### 完整配置示例

**config_md.yaml** (启用所有新功能):
```yaml
# CTP 配置
TdFrontAddress: tcp://182.254.243.31:40001
MdFrontAddress: tcp://182.254.243.31:40011
BrokerID: "9999"
AuthCode: "0000000000000000"
AppID: simnow_client_test
Port: 8080
Host: 127.0.0.1
LogLevel: INFO
HeartbeatInterval: 30.0
HeartbeatTimeout: 60.0

# Redis 缓存配置
Redis:
  Enabled: true
  Host: localhost
  Port: 6379
  Password: ""
  DB: 0
  MaxConnections: 50
  SocketTimeout: 5.0
  SocketConnectTimeout: 5.0
  MarketSnapshotTTL: 60
  MarketTickTTL: 5
  OrderTTL: 86400

# 性能监控配置
Metrics:
  Enabled: true
  ReportInterval: 60
  SampleRate: 1.0
  LatencyWarningThresholdMs: 100.0
  CacheHitRateWarningThreshold: 50.0
  CpuWarningThreshold: 80.0
  MemoryWarningThreshold: 80.0

# 策略管理配置
Strategy:
  MaxStrategies: 10
  DefaultMaxMemoryMB: 512
  DefaultMaxCPUPercent: 50.0
```

**config_td.yaml** (启用所有新功能):
```yaml
# CTP 配置
TdFrontAddress: tcp://182.254.243.31:40001
MdFrontAddress: tcp://182.254.243.31:40011
BrokerID: "9999"
AuthCode: "0000000000000000"
AppID: simnow_client_test
Port: 8081                                   # 注意：交易服务使用不同端口
Host: 127.0.0.1
LogLevel: INFO
HeartbeatInterval: 30.0
HeartbeatTimeout: 60.0

# Redis 缓存配置
Redis:
  Enabled: true
  Host: localhost
  Port: 6379
  Password: ""
  DB: 0
  MaxConnections: 50
  SocketTimeout: 5.0
  SocketConnectTimeout: 5.0
  MarketSnapshotTTL: 60
  MarketTickTTL: 5
  OrderTTL: 86400

# 性能监控配置
Metrics:
  Enabled: true
  ReportInterval: 60
  SampleRate: 1.0
  LatencyWarningThresholdMs: 100.0
  CacheHitRateWarningThreshold: 50.0
  CpuWarningThreshold: 80.0
  MemoryWarningThreshold: 80.0
```

### 渐进式启用策略

**阶段 1: 最小化升级**（不启用新功能）
- 不添加任何新配置
- 系统以兼容模式运行
- 适合保守升级

**阶段 2: 启用性能监控**
```yaml
Metrics:
  Enabled: true
  ReportInterval: 60
```
- 只启用性能监控
- 了解系统性能基线
- 无风险

**阶段 3: 启用 Redis 缓存**
```yaml
Redis:
  Enabled: true
  Host: localhost
  Port: 6379
```
- 启用 Redis 缓存
- 提升查询性能
- 需要 Redis 服务器

**阶段 4: 启用策略管理**
```yaml
Strategy:
  MaxStrategies: 10
```
- 启用策略管理
- 支持多策略运行
- 适合策略交易场景

## 新功能使用

### 使用 Redis 缓存

**1. 启动 Redis 服务器**:
```bash
# Windows (使用 WSL)
wsl
redis-server

# Linux/Mac
redis-server

# 或作为服务启动
sudo systemctl start redis
```

**2. 配置 Redis**:
```yaml
Redis:
  Enabled: true
  Host: localhost
  Port: 6379
```

**3. 验证缓存工作**:
```bash
# 查看日志
grep "Redis 连接成功" logs/webctp.log

# 查看缓存命中率
grep "Redis 命中率" logs/webctp.log
```

**4. 监控缓存性能**:
```bash
# 查看 Redis 状态
redis-cli info stats

# 查看缓存键
redis-cli keys "market:*"
redis-cli keys "account:*"
```

### 使用性能监控

**1. 启用性能监控**:
```yaml
Metrics:
  Enabled: true
  ReportInterval: 60
```

**2. 查看性能报告**:
```bash
# 查看最新的性能报告
grep "性能指标报告" logs/webctp.log -A 30 | tail -35

# 实时监控性能
tail -f logs/webctp.log | grep -A 30 "性能指标报告"
```

**3. 配置告警阈值**:
```yaml
Metrics:
  LatencyWarningThresholdMs: 100.0
  CacheHitRateWarningThreshold: 50.0
  CpuWarningThreshold: 80.0
  MemoryWarningThreshold: 80.0
```

**4. 查看告警**:
```bash
# 查看所有告警
grep "⚠️" logs/webctp.log

# 查看特定类型的告警
grep "延迟告警" logs/webctp.log
```

### 使用策略管理

**1. 启用策略管理**:
```yaml
Strategy:
  MaxStrategies: 10
```

**2. 注册策略**（通过 WebSocket）:
```json
{
  "MsgType": "RegisterStrategy",
  "StrategyID": "my_strategy_1",
  "StrategyName": "我的策略",
  "SubscribedInstruments": ["au2602", "rb2605"]
}
```

**3. 启动策略**:
```json
{
  "MsgType": "StartStrategy",
  "StrategyID": "my_strategy_1"
}
```

**4. 查询策略状态**:
```json
{
  "MsgType": "QueryStrategyStatus",
  "StrategyID": "my_strategy_1"
}
```

**5. 停止策略**:
```json
{
  "MsgType": "StopStrategy",
  "StrategyID": "my_strategy_1"
}
```

## 迁移检查清单

### 升级前检查

- [ ] 备份配置文件
- [ ] 备份 con_file 目录
- [ ] 检查 Python 版本（3.13.x）
- [ ] 检查 UV 版本
- [ ] 准备 Redis 服务器（如果需要）
- [ ] 准备测试环境
- [ ] 通知相关人员升级计划

### 升级过程检查

- [ ] 停止现有服务
- [ ] 更新代码到 v0.2.0
- [ ] 更新依赖（uv sync）
- [ ] 更新配置文件
- [ ] 运行测试套件
- [ ] 启动服务
- [ ] 验证基础功能
- [ ] 验证新功能（如果启用）

### 升级后检查

- [ ] WebSocket 连接正常
- [ ] 登录功能正常
- [ ] 行情订阅正常
- [ ] 交易功能正常
- [ ] Redis 连接正常（如果启用）
- [ ] 性能报告生成正常
- [ ] 告警功能正常
- [ ] 日志记录正常
- [ ] 性能符合预期
- [ ] 无异常错误

### 监控检查

- [ ] 查看性能报告
- [ ] 检查延迟指标
- [ ] 检查 Redis 命中率
- [ ] 检查系统资源使用
- [ ] 检查告警频率
- [ ] 检查日志文件大小
- [ ] 设置日志轮转
- [ ] 配置告警通知


## 常见问题

### Q1: 升级后现有客户端是否需要修改？

**A**: 不需要。v0.2.0 完全向后兼容，现有客户端无需任何修改即可继续使用。

### Q2: 是否必须使用 Redis？

**A**: 不是必须的。Redis 是可选功能，不启用 Redis 系统仍然可以正常运行，只是没有缓存加速功能。

### Q3: 如何禁用性能监控？

**A**: 在配置文件中设置：
```yaml
Metrics:
  Enabled: false
```
或删除整个 `Metrics` 配置节。

### Q4: 升级后性能是否会下降？

**A**: 不会。即使不启用新功能，性能也不会下降。启用新功能后，性能会有显著提升。

### Q5: Redis 连接失败会影响系统运行吗？

**A**: 不会。系统有完善的降级机制，Redis 不可用时会自动切换到直接查询模式，不影响核心功能。

### Q6: 如何查看系统是否使用了缓存？

**A**: 查看日志中的 Redis 命中率：
```bash
grep "Redis 命中率" logs/webctp.log
```

### Q7: 告警太多怎么办？

**A**: 可以调整告警阈值：
```yaml
Metrics:
  LatencyWarningThresholdMs: 150.0      # 放宽延迟阈值
  CacheHitRateWarningThreshold: 30.0    # 放宽命中率阈值
  CpuWarningThreshold: 90.0             # 放宽 CPU 阈值
  MemoryWarningThreshold: 90.0          # 放宽内存阈值
```

### Q8: 如何验证升级成功？

**A**: 检查以下几点：
1. 服务正常启动
2. WebSocket 连接正常
3. 基础功能正常
4. 日志中有性能报告（如果启用）
5. 无异常错误

### Q9: 升级后如何回滚？

**A**: 参考 [回滚方案](#回滚方案) 章节。

### Q10: 性能监控会影响系统性能吗？

**A**: 影响极小。性能监控使用异步方式收集指标，对系统性能的影响可以忽略不计（< 1%）。

### Q11: 如何在生产环境中安全升级？

**A**: 建议采用以下策略：
1. 先在测试环境完整测试
2. 选择业务低峰期升级
3. 准备回滚方案
4. 渐进式启用新功能
5. 密切监控系统运行

### Q12: 多个服务可以共享一个 Redis 吗？

**A**: 可以。建议使用不同的 DB 编号：
```yaml
# 行情服务
Redis:
  DB: 0

# 交易服务
Redis:
  DB: 1
```

### Q13: 如何优化 Redis 性能？

**A**: 
1. 调整 TTL 配置
2. 增加连接池大小
3. 使用 Redis 持久化
4. 监控 Redis 内存使用
5. 定期清理过期数据

### Q14: 策略管理功能如何使用？

**A**: 参考 [使用策略管理](#使用策略管理) 章节和 [README](../README_CN.md) 中的策略管理部分。

### Q15: 如何集成到现有监控系统？

**A**: 参考 [监控指南](./monitoring_guide_CN.md) 中的"集成到监控系统"章节。

## 回滚方案

如果升级后遇到问题，可以按以下步骤回滚到 v0.1.x：

### 方案 1: 使用备份回滚

**步骤 1: 停止服务**
```bash
# 停止行情服务和交易服务
# 按 Ctrl+C 或关闭终端窗口
```

**步骤 2: 恢复代码**
```bash
# 切换到 v0.1.x 分支或标签
git checkout v0.1.x

# 或恢复备份的代码
```

**步骤 3: 恢复配置**
```bash
# Windows
copy config\config_md.yaml.backup config\config_md.yaml
copy config\config_td.yaml.backup config\td.yaml

# Linux/Mac
cp config/config_md.yaml.backup config/config_md.yaml
cp config/config_td.yaml.backup config/config_td.yaml
```

**步骤 4: 恢复依赖**
```bash
# 激活虚拟环境
.venv\Scripts\activate

# 重新安装依赖
uv sync
```

**步骤 5: 启动服务**
```bash
# 启动行情服务
python main.py --config=./config/config_md.yaml --app_type=md

# 启动交易服务
python main.py --config=./config/config_td.yaml --app_type=td
```

### 方案 2: 禁用新功能

如果只是新功能有问题，可以禁用新功能而不回滚代码：

**禁用 Redis 缓存**:
```yaml
Redis:
  Enabled: false
```

**禁用性能监控**:
```yaml
Metrics:
  Enabled: false
```

**禁用策略管理**:
删除或注释掉 `Strategy` 配置节。

### 回滚检查清单

- [ ] 停止 v0.2.0 服务
- [ ] 恢复代码到 v0.1.x
- [ ] 恢复配置文件
- [ ] 恢复依赖
- [ ] 启动服务
- [ ] 验证基础功能
- [ ] 检查日志
- [ ] 通知相关人员

### 回滚后注意事项

1. **数据一致性**: 
   - Redis 缓存数据会丢失（如果使用了 Redis）
   - CTP 数据不受影响

2. **性能监控数据**:
   - 历史性能数据会丢失
   - 可以备份日志文件保留历史数据

3. **策略状态**:
   - 运行中的策略会停止
   - 需要重新启动策略

## 技术支持

### 获取帮助

如果在迁移过程中遇到问题，可以通过以下方式获取帮助：

**文档**:
- [README](../README_CN.md) - 项目概述
- [开发文档](./development_CN.md) - 开发指南
- [监控指南](./monitoring_guide_CN.md) - 监控配置
- [日志指南](./logger_guide_CN.md) - 日志使用

**社区**:
- GitHub Issues: 报告问题和建议
- QQ 群: 446042777

**日志分析**:
```bash
# 查看错误日志
grep "ERROR" logs/webctp.log

# 查看警告日志
grep "WARNING" logs/webctp.log

# 查看最近的日志
tail -100 logs/webctp.log
```

### 问题报告

报告问题时，请提供以下信息：

1. **环境信息**:
   - 操作系统版本
   - Python 版本
   - UV 版本
   - Redis 版本（如果使用）

2. **配置信息**:
   - 配置文件内容（隐藏敏感信息）
   - 环境变量设置

3. **错误信息**:
   - 错误日志
   - 堆栈跟踪
   - 复现步骤

4. **系统状态**:
   - 性能报告
   - 资源使用情况
   - Redis 状态（如果使用）

## 附录

### A. 版本对比

| 功能 | v0.1.x | v0.2.0 |
|------|--------|--------|
| WebSocket 接口 | ✅ | ✅ |
| CTP API 封装 | ✅ | ✅ |
| Redis 缓存 | ❌ | ✅ |
| 性能监控 | ❌ | ✅ |
| 智能告警 | ❌ | ✅ |
| 策略管理 | ❌ | ✅ |
| 优化的序列化 | ❌ | ✅ |
| 向后兼容 | - | ✅ |

### B. 性能对比

| 指标 | v0.1.x | v0.2.0 (无缓存) | v0.2.0 (有缓存) |
|------|--------|----------------|----------------|
| 订单延迟 P95 | ~150ms | ~120ms | ~80ms |
| 行情延迟 | ~80ms | ~60ms | ~40ms |
| 吞吐量 | ~15 单/秒 | ~18 单/秒 | ~25 单/秒 |
| CPU 使用率 | 基准 | -10% | -15% |
| 内存使用 | 基准 | +5% | +10% |

*注: 以上数据为预期值，实际性能取决于硬件配置和网络环境*

### C. 依赖变更详情

**新增依赖**:
```toml
[project.dependencies]
redis = ">=5.0.0"      # Redis 客户端
orjson = ">=3.9.0"     # 快速 JSON 序列化
msgpack = ">=1.0.0"    # 二进制序列化
psutil = ">=5.9.0"     # 系统资源监控（可选）
```

**依赖大小**:
- redis: ~500 KB
- orjson: ~200 KB
- msgpack: ~100 KB
- psutil: ~400 KB
- 总计: ~1.2 MB

### D. 配置模板

**最小配置** (config_minimal.yaml):
```yaml
TdFrontAddress: tcp://182.254.243.31:40001
MdFrontAddress: tcp://182.254.243.31:40011
BrokerID: "9999"
AuthCode: "0000000000000000"
AppID: simnow_client_test
Port: 8080
Host: 127.0.0.1
LogLevel: INFO
```

**推荐配置** (config_recommended.yaml):
```yaml
TdFrontAddress: tcp://182.254.243.31:40001
MdFrontAddress: tcp://182.254.243.31:40011
BrokerID: "9999"
AuthCode: "0000000000000000"
AppID: simnow_client_test
Port: 8080
Host: 127.0.0.1
LogLevel: INFO

Redis:
  Enabled: true
  Host: localhost
  Port: 6379

Metrics:
  Enabled: true
  ReportInterval: 60
```

**完整配置** (config_full.yaml):
```yaml
TdFrontAddress: tcp://182.254.243.31:40001
MdFrontAddress: tcp://182.254.243.31:40011
BrokerID: "9999"
AuthCode: "0000000000000000"
AppID: simnow_client_test
Port: 8080
Host: 127.0.0.1
LogLevel: INFO
HeartbeatInterval: 30.0
HeartbeatTimeout: 60.0

Redis:
  Enabled: true
  Host: localhost
  Port: 6379
  Password: ""
  DB: 0
  MaxConnections: 50
  SocketTimeout: 5.0
  SocketConnectTimeout: 5.0
  MarketSnapshotTTL: 60
  MarketTickTTL: 5
  OrderTTL: 86400

Metrics:
  Enabled: true
  ReportInterval: 60
  SampleRate: 1.0
  LatencyWarningThresholdMs: 100.0
  CacheHitRateWarningThreshold: 50.0
  CpuWarningThreshold: 80.0
  MemoryWarningThreshold: 80.0

Strategy:
  MaxStrategies: 10
  DefaultMaxMemoryMB: 512
  DefaultMaxCPUPercent: 50.0
```

---

## 总结

v0.2.0 是一个重要的性能优化版本，引入了 Redis 缓存、性能监控、智能告警和策略管理等功能。升级过程简单，完全向后兼容，建议所有用户升级。

**升级建议**:
1. 先在测试环境验证
2. 渐进式启用新功能
3. 密切监控系统运行
4. 根据实际情况调整配置

**关键要点**:
- ✅ 完全向后兼容
- ✅ 所有新功能可选
- ✅ 性能显著提升
- ✅ 更好的可观测性
- ✅ 简单的回滚方案

如有任何问题，请参考文档或联系技术支持。

---

**文档版本**: 1.0  
**最后更新**: 2025-12-15  
**维护者**: homalos-webctp 团队
