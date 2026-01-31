# 故障排查指南

**版本**: 1.0\
**更新日期**: 2025-12-15

## 目录

- [概述](#%E6%A6%82%E8%BF%B0)
- [故障排查流程](#%E6%95%85%E9%9A%9C%E6%8E%92%E6%9F%A5%E6%B5%81%E7%A8%8B)
- [连接问题](#%E8%BF%9E%E6%8E%A5%E9%97%AE%E9%A2%98)
- [性能问题](#%E6%80%A7%E8%83%BD%E9%97%AE%E9%A2%98)
- [缓存问题](#%E7%BC%93%E5%AD%98%E9%97%AE%E9%A2%98)
- [配置问题](#%E9%85%8D%E7%BD%AE%E9%97%AE%E9%A2%98)
- [日志分析](#%E6%97%A5%E5%BF%97%E5%88%86%E6%9E%90)
- [诊断工具](#%E8%AF%8A%E6%96%AD%E5%B7%A5%E5%85%B7)
- [错误代码参考](#%E9%94%99%E8%AF%AF%E4%BB%A3%E7%A0%81%E5%8F%82%E8%80%83)
- [获取帮助](#%E8%8E%B7%E5%8F%96%E5%B8%AE%E5%8A%A9)

## 概述

本指南帮助您快速诊断和解决 homalos-webctp 系统中的常见问题。

### 故障分类

**连接问题**:

- WebSocket 连接失败
- CTP 连接失败
- Redis 连接失败

**性能问题**:

- 延迟过高
- 吞吐量低
- 系统资源占用高

**缓存问题**:

- Redis 不可用
- 缓存命中率低
- 数据不一致

**配置问题**:

- 配置文件错误
- 环境变量问题
- 权限问题

### 诊断原则

1. **查看日志**: 首先查看错误日志
2. **检查配置**: 确认配置文件正确
3. **验证连接**: 测试各个连接是否正常
4. **监控指标**: 查看性能报告和告警
5. **隔离问题**: 逐个排查可能的原因
6. **记录过程**: 记录排查步骤和结果

### 常用工具

- **日志文件**: `logs/webctp.log`, `logs/webctp_error.log`
- **性能报告**: 日志中的性能指标报告
- **Redis CLI**: `redis-cli` 命令行工具
- **系统监控**: Windows 性能监视器 / Linux top/htop
- **网络工具**: ping, telnet, curl

## 故障排查流程

### 快速诊断流程

```
1. 服务是否启动？
   ├─ 否 → 检查启动错误
   └─ 是 → 继续

2. 能否连接 WebSocket？
   ├─ 否 → 检查网络和端口
   └─ 是 → 继续

3. 能否登录？
   ├─ 否 → 检查账号和 CTP 连接
   └─ 是 → 继续

4. 功能是否正常？
   ├─ 否 → 检查具体功能错误
   └─ 是 → 检查性能问题

5. 性能是否达标？
   ├─ 否 → 查看性能报告和告警
   └─ 是 → 系统正常
```

### 详细排查步骤

#### 步骤 1: 检查服务状态

**检查服务是否运行**:

```bash
# Windows
tasklist | findstr python

# Linux
ps aux | grep python
```

**检查端口是否监听**:

```bash
# Windows
netstat -ano | findstr :8080
netstat -ano | findstr :8081

# Linux
netstat -tlnp | grep 8080
netstat -tlnp | grep 8081
```

**预期结果**:

- 应该看到 python 进程
- 端口 8080 (MD) 和 8081 (TD) 应该在监听状态

#### 步骤 2: 检查日志

**查看最新日志**:

```bash
# Windows PowerShell
Get-Content logs\webctp.log -Tail 50

# Linux
tail -50 logs/webctp.log
```

**查看错误日志**:

```bash
# Windows PowerShell
Get-Content logs\webctp_error.log -Tail 50

# Linux
tail -50 logs/webctp_error.log
```

**关注关键信息**:

- 启动信息
- 连接状态
- 错误消息
- 告警信息

#### 步骤 3: 测试连接

**测试 WebSocket 连接**:

```python
import asyncio
import websockets

async def test_connection():
    try:
        async with websockets.connect("ws://localhost:8080/ws") as ws:
            print("WebSocket 连接成功")
    except Exception as e:
        print(f"WebSocket 连接失败: {e}")

asyncio.run(test_connection())
```

**测试 Redis 连接**:

```bash
redis-cli ping
# 应该返回 PONG
```

**测试 CTP 连接**:

- 查看日志中的 CTP 连接状态
- 确认前置地址可访问

#### 步骤 4: 检查配置

**验证配置文件**:

```bash
# 检查配置文件语法
python -c "import yaml; yaml.safe_load(open('config/config_md.yaml'))"
```

**检查关键配置项**:

- 前置地址是否正确
- 端口是否冲突
- Redis 配置是否正确
- 日志级别是否合适

#### 步骤 5: 查看性能指标

**查看性能报告**:

```bash
# 查看最近的性能报告
grep "性能指标报告" logs/webctp.log -A 30 | tail -35
```

**查看告警**:

```bash
# 查看所有告警
grep "⚠️" logs/webctp.log
```

**分析指标**:

- 延迟是否正常
- 吞吐量是否达标
- 资源使用是否合理
- 缓存命中率是否正常

## 连接问题

### 问题 1: WebSocket 连接失败

#### 症状

- 客户端无法连接到 WebSocket
- 连接超时或被拒绝
- 浏览器显示 "WebSocket connection failed"

#### 可能原因

**1. 服务未启动**

```bash
# 检查服务是否运行
tasklist | findstr python
```

**解决方案**: 启动服务

```bash
.venv\Scripts\activate
python main.py --config=./config/config_md.yaml --app_type=md
```

**2. 端口被占用**

```bash
# 检查端口占用
netstat -ano | findstr :8080
```

**解决方案**:

- 终止占用端口的进程
- 或修改配置文件中的端口号

**3. 防火墙阻止**

**解决方案**:

```bash
# Windows 防火墙添加规则
netsh advfirewall firewall add rule name="WebCTP MD" dir=in action=allow protocol=TCP localport=8080
netsh advfirewall firewall add rule name="WebCTP TD" dir=in action=allow protocol=TCP localport=8081
```

**4. 绑定地址错误**

**检查配置**:

```yaml
Host: 127.0.0.1  # 只允许本地连接
# 或
Host: 0.0.0.0    # 允许所有网络接口
```

**解决方案**: 根据需求修改 Host 配置

#### 诊断步骤

1. 确认服务已启动
2. 确认端口未被占用
3. 测试本地连接
4. 检查防火墙设置
5. 查看错误日志

#### 日志示例

**正常启动**:

```
INFO | Application startup complete
INFO | Uvicorn running on http://127.0.0.1:8080
```

**端口占用**:

```
ERROR | [Errno 10048] error while attempting to bind on address ('127.0.0.1', 8080): 通常每个套接字地址(协议/网络地址/端口)只允许使用一次。
```

### 问题 2: CTP 连接失败

#### 症状

- 登录失败
- 无法订阅行情
- 无法提交订单
- 日志显示 CTP 连接错误

#### 可能原因

**1. 前置地址错误**

**检查配置**:

```yaml
TdFrontAddress: tcp://182.254.243.31:40001
MdFrontAddress: tcp://182.254.243.31:40011
```

**解决方案**:

- 确认前置地址正确
- SimNow 7x24: tcp://182.254.243.31:40001 (交易), tcp://182.254.243.31:40011 (行情)
- SimNow 标准: tcp://180.168.146.187:10130 (交易), tcp://180.168.146.187:10131 (行情)

**2. 账号密码错误**

**检查配置**:

```yaml
BrokerID: "9999"
AuthCode: "0000000000000000"
AppID: simnow_client_test
```

**解决方案**:

- 确认 BrokerID 正确（SimNow 为 "9999"）
- 确认 AuthCode 和 AppID 正确
- 检查用户名和密码

**3. 网络连接问题**

**测试连接**:

```bash
# Windows
telnet 182.254.243.31 40001

# 或使用 PowerShell
Test-NetConnection -ComputerName 182.254.243.31 -Port 40001
```

**解决方案**:

- 检查网络连接
- 检查防火墙设置
- 尝试使用 VPN 或代理

**4. CTP 服务器维护**

**解决方案**:

- 查看 SimNow 官网公告
- 等待服务器恢复
- 尝试使用备用前置地址

#### 诊断步骤

1. 检查配置文件
2. 测试网络连接
3. 查看 CTP 错误码
4. 检查账号状态
5. 查看服务器公告

#### 常见错误码

| 错误码 | 说明             | 解决方案               |
| ------ | ---------------- | ---------------------- |
| 3      | CTP:不合法的登录 | 检查用户名密码         |
| 7      | CTP:还没有初始化 | 等待初始化完成         |
| 63     | CTP:网络连接失败 | 检查网络和前置地址     |
| 90     | CTP:认证失败     | 检查 AuthCode 和 AppID |

#### 日志示例

**连接成功**:

```
INFO | CTP 前置连接成功
INFO | 用户登录成功: UserID=123456
```

**连接失败**:

```
ERROR | CTP 前置连接失败: 网络连接失败
ERROR | 用户登录失败: ErrorID=3, ErrorMsg=CTP:不合法的登录
```

### 问题 3: Redis 连接失败

#### 症状

- 日志显示 "Redis 连接失败"
- 缓存功能不可用
- 性能报告显示命中率为 0

#### 可能原因

**1. Redis 服务未启动**

**检查 Redis 状态**:

```bash
# Windows (WSL)
wsl
redis-cli ping

# Linux
systemctl status redis
```

**解决方案**: 启动 Redis

```bash
# Windows (WSL)
redis-server

# Linux
sudo systemctl start redis
```

**2. Redis 配置错误**

**检查配置**:

```yaml
Redis:
  Enabled: true
  Host: localhost
  Port: 6379
  Password: ""
```

**解决方案**:

- 确认 Host 和 Port 正确
- 如果 Redis 设置了密码，填写 Password

**3. Redis 连接数超限**

**检查连接数**:

```bash
redis-cli info clients
```

**解决方案**:

- 增加 Redis maxclients 配置
- 减少应用的 MaxConnections 配置

**4. Redis 内存不足**

**检查内存**:

```bash
redis-cli info memory
```

**解决方案**:

- 增加 Redis maxmemory 配置
- 清理过期数据
- 调整淘汰策略

#### 诊断步骤

1. 确认 Redis 服务运行
2. 测试 Redis 连接
3. 检查配置文件
4. 查看 Redis 日志
5. 检查系统资源

#### 降级机制

**重要**: Redis 连接失败时，系统会自动降级到直接查询模式，不影响核心功能。

**日志示例**:

```
WARNING | Redis 连接失败: Connection refused
INFO | Redis 不可用，使用降级模式
```

**验证降级**:

- 系统仍然可以正常运行
- 性能会有所下降
- 缓存命中率为 0

### 问题 4: 心跳超时

#### 症状

- WebSocket 连接频繁断开
- 日志显示 "心跳超时"
- 客户端需要频繁重连

#### 可能原因

**1. 网络不稳定**

**解决方案**:

- 使用更稳定的网络
- 缩短心跳间隔

**配置调整**:

```yaml
HeartbeatInterval: 15.0  # 从 30 秒缩短到 15 秒
HeartbeatTimeout: 30.0   # 从 60 秒缩短到 30 秒
```

**2. 客户端未响应心跳**

**解决方案**:

- 确保客户端正确处理心跳消息
- 客户端应该响应 ping 消息

**3. 服务器负载过高**

**解决方案**:

- 检查系统资源使用
- 优化性能
- 增加服务器资源

#### 诊断步骤

1. 检查网络质量
2. 查看心跳日志
3. 检查客户端实现
4. 监控服务器负载
5. 调整心跳配置


## 性能问题

### 问题 5: 延迟过高

#### 症状

- 订单延迟 P95 > 200 ms
- 行情延迟 > 100 ms
- 频繁收到延迟告警

#### 可能原因和解决方案

**1. Redis 未启用或命中率低**

**检查**:

```bash
# 查看 Redis 命中率
grep "Redis 命中率" logs/webctp.log | tail -5
```

**解决方案**:

```yaml
# 启用 Redis
Redis:
  Enabled: true
  Host: localhost
  Port: 6379
```

**2. 系统资源不足**

**检查**:

```bash
# 查看系统资源
grep "系统资源" logs/webctp.log | tail -5
```

**解决方案**:

- CPU > 80%: 优化代码、增加 CPU 资源
- 内存 > 80%: 清理缓存、增加内存
- 降低采样率减少监控开销

**3. 网络延迟高**

**检查**:

```bash
# 测试网络延迟
ping 182.254.243.31
```

**解决方案**:

- 使用更快的网络连接
- 选择地理位置近的前置服务器
- 考虑使用专线

**4. CTP API 响应慢**

**特征**:

- 延迟主要来自 CTP 回调
- 其他操作正常

**解决方案**:

- 这是外部因素，难以优化
- 考虑使用生产环境（比 SimNow 快）
- 实施请求合并策略

**5. 序列化开销大**

**检查**:

- 确认使用 orjson（不是标准 json）
- 查看日志中的序列化错误

**解决方案**:

```bash
# 确认 orjson 已安装
uv pip list | grep orjson
```

#### 优化建议

**低负载场景**:

```yaml
Metrics:
  SampleRate: 1.0  # 100% 采样
  ReportInterval: 120  # 较长报告间隔
```

**高负载场景**:

```yaml
Metrics:
  SampleRate: 0.2  # 20% 采样
  ReportInterval: 60

Redis:
  MaxConnections: 100  # 增加连接池
```

### 问题 6: 吞吐量低

#### 症状

- 订单吞吐量 \< 10 单/秒
- 系统无法处理高频交易
- 请求排队严重

#### 可能原因和解决方案

**1. 连接池太小**

**解决方案**:

```yaml
Redis:
  MaxConnections: 100  # 增加到 100
```

**2. 同步阻塞**

**检查日志**:

- 查找 "blocking" 或 "waiting" 相关日志

**解决方案**:

- 确保所有 I/O 操作都是异步的
- 检查是否有同步调用阻塞事件循环

**3. 策略数量过多**

**检查**:

```bash
# 查看活跃策略数
grep "active_strategies" logs/webctp.log | tail -1
```

**解决方案**:

```yaml
Strategy:
  MaxStrategies: 5  # 减少最大策略数
```

**4. 消息队列积压**

**特征**:

- 内存持续增长
- 延迟持续上升

**解决方案**:

- 增加处理速度
- 限制队列大小
- 实施背压机制

### 问题 7: 系统资源占用高

#### CPU 使用率过高

**症状**:

- CPU > 80%
- 频繁收到 CPU 告警

**可能原因**:

**1. 采样率过高**

```yaml
Metrics:
  SampleRate: 0.2  # 降低到 20%
```

**2. 策略计算密集**

- 优化策略算法
- 限制策略 CPU 使用

**3. 序列化开销**

- 确认使用 orjson
- 减少不必要的序列化

**4. 日志级别过低**

```yaml
LogLevel: INFO  # 不要使用 DEBUG
```

#### 内存使用率过高

**症状**:

- 内存 > 80%
- 频繁收到内存告警
- 可能出现 OOM

**可能原因**:

**1. 内存泄漏**

**诊断**:

```python
# 使用 memory_profiler
from memory_profiler import profile

@profile
def your_function():
    pass
```

**2. 缓存数据过多**

**解决方案**:

```yaml
Redis:
  MarketSnapshotTTL: 30  # 缩短 TTL
  MarketTickTTL: 3
```

**3. 滑动窗口过大**

**解决方案**:

- 修改 MetricsCollector.WINDOW_SIZE_SECONDS
- 从 600 秒减少到 300 秒

**4. 策略内存泄漏**

**解决方案**:

```yaml
Strategy:
  DefaultMaxMemoryMB: 256  # 限制单策略内存
```

### 问题 8: 性能抖动

#### 症状

- 延迟波动大
- 偶尔出现极高延迟
- P99 远高于 P95

#### 可能原因

**1. GC (垃圾回收) 暂停**

**解决方案**:

- 减少对象创建
- 使用对象池
- 优化内存使用

**2. 网络波动**

**诊断**:

```bash
# 持续 ping 测试
ping -t 182.254.243.31
```

**解决方案**:

- 使用更稳定的网络
- 实施重试机制

**3. Redis 慢查询**

**检查**:

```bash
redis-cli slowlog get 10
```

**解决方案**:

- 优化 Redis 查询
- 增加 Redis 内存
- 调整淘汰策略

**4. CTP 服务器波动**

**特征**:

- 所有请求同时变慢
- 与本地系统无关

**解决方案**:

- 这是外部因素
- 考虑使用多个前置地址
- 实施故障转移

## 缓存问题

### 问题 9: Redis 命中率低

#### 症状

- 缓存命中率 \< 60%
- 频繁收到命中率告警
- 性能提升不明显

#### 可能原因和解决方案

**1. TTL 设置过短**

**当前配置**:

```yaml
Redis:
  MarketSnapshotTTL: 60
  MarketTickTTL: 5
  OrderTTL: 86400
```

**解决方案**: 延长 TTL

```yaml
Redis:
  MarketSnapshotTTL: 120  # 延长到 2 分钟
  MarketTickTTL: 10       # 延长到 10 秒
```

**2. 查询的数据变化频繁**

**特征**:

- 实时 tick 数据命中率低是正常的
- 快照数据命中率应该较高

**解决方案**:

- 接受实时数据的低命中率
- 优化快照数据的缓存策略

**3. Redis 内存不足导致数据被驱逐**

**检查**:

```bash
redis-cli info memory
redis-cli info stats | grep evicted
```

**解决方案**:

```conf
# redis.conf
maxmemory 4gb
maxmemory-policy allkeys-lru
```

**4. 缓存预热不充分**

**解决方案**:

- 启动时预加载热点数据
- 实施缓存预热策略

**5. 查询模式不适合缓存**

**特征**:

- 大量一次性查询
- 查询分布非常分散

**解决方案**:

- 分析查询模式
- 调整缓存策略
- 考虑是否需要缓存

#### 优化建议

**分析命中率**:

```bash
# 查看命中率趋势
grep "Redis 命中率" logs/webctp.log | tail -20
```

**调整阈值**:

```yaml
Metrics:
  CacheHitRateWarningThreshold: 40.0  # 降低阈值
```

### 问题 10: 缓存数据不一致

#### 症状

- 缓存数据与 CTP 数据不一致
- 查询结果不准确
- 偶尔出现脏数据

#### 可能原因和解决方案

**1. TTL 设置过长**

**问题**:

- 数据已更新，但缓存未过期

**解决方案**:

```yaml
Redis:
  MarketSnapshotTTL: 30  # 缩短 TTL
```

**2. 缓存更新失败**

**检查日志**:

```bash
grep "Redis.*失败" logs/webctp.log
```

**解决方案**:

- 检查 Redis 连接状态
- 实施重试机制
- 添加更新失败告警

**3. 并发更新冲突**

**问题**:

- 多个进程同时更新缓存
- 最后写入的数据覆盖了正确数据

**解决方案**:

- 使用 Redis 事务
- 实施乐观锁
- 使用版本号

**4. 缓存穿透**

**问题**:

- 查询不存在的数据
- 绕过缓存直接查询 CTP

**解决方案**:

- 缓存空结果（短 TTL）
- 使用布隆过滤器

#### 数据一致性检查

**手动验证**:

```python
# 比较缓存和 CTP 数据
cached_data = await cache.get("market:au2602")
ctp_data = await ctp_client.query_market("au2602")

if cached_data != ctp_data:
    print("数据不一致!")
```

**自动检查**:

- 定期抽样检查
- 记录不一致情况
- 自动刷新缓存

### 问题 11: Redis 性能下降

#### 症状

- Redis 操作延迟增加
- 缓存操作超时
- 系统整体性能下降

#### 可能原因和解决方案

**1. Redis 内存碎片**

**检查**:

```bash
redis-cli info memory | grep mem_fragmentation_ratio
```

**解决方案**:

```bash
# 如果碎片率 > 1.5
redis-cli memory purge
```

**2. Redis 持久化影响性能**

**检查配置**:

```conf
# redis.conf
save 900 1
save 300 10
save 60 10000
appendfsync everysec
```

**解决方案**:

- 调整持久化策略
- 使用 SSD 存储
- 考虑禁用持久化（如果可以接受数据丢失）

**3. Redis 慢查询**

**检查**:

```bash
redis-cli slowlog get 10
```

**解决方案**:

- 优化查询命令
- 避免使用 KEYS 命令
- 使用 SCAN 替代 KEYS

**4. Redis 连接数过多**

**检查**:

```bash
redis-cli info clients
```

**解决方案**:

```yaml
Redis:
  MaxConnections: 50  # 减少连接池大小
```

**5. Redis 服务器资源不足**

**检查**:

- CPU 使用率
- 内存使用率
- 磁盘 I/O

**解决方案**:

- 增加服务器资源
- 优化 Redis 配置
- 考虑 Redis 集群

## 配置问题

### 问题 12: 配置文件错误

#### 症状

- 服务启动失败
- 日志显示配置解析错误
- 功能异常

#### 常见配置错误

**1. YAML 语法错误**

**错误示例**:

```yaml
Redis:
  Enabled: true
  Host localhost  # 缺少冒号
  Port: 6379
```

**正确格式**:

```yaml
Redis:
  Enabled: true
  Host: localhost  # 添加冒号
  Port: 6379
```

**验证语法**:

```bash
python -c "import yaml; yaml.safe_load(open('config/config_md.yaml'))"
```

**2. 缩进错误**

**错误示例**:

```yaml
Redis:
  Enabled: true
Host: localhost  # 缩进错误
  Port: 6379
```

**正确格式**:

```yaml
Redis:
  Enabled: true
  Host: localhost  # 正确缩进
  Port: 6379
```

**3. 数据类型错误**

**错误示例**:

```yaml
Port: "8080"  # 字符串，应该是数字
Enabled: "true"  # 字符串，应该是布尔值
```

**正确格式**:

```yaml
Port: 8080  # 数字
Enabled: true  # 布尔值
```

**4. 必需字段缺失**

**错误示例**:

```yaml
# 缺少 TdFrontAddress
MdFrontAddress: tcp://182.254.243.31:40011
BrokerID: "9999"
```

**正确格式**:

```yaml
TdFrontAddress: tcp://182.254.243.31:40001  # 添加必需字段
MdFrontAddress: tcp://182.254.243.31:40011
BrokerID: "9999"
```

#### 配置验证清单

- [ ] YAML 语法正确
- [ ] 缩进一致（使用空格，不用 Tab）
- [ ] 数据类型正确
- [ ] 所有必需字段存在
- [ ] 端口号未被占用
- [ ] 前置地址正确
- [ ] Redis 配置正确（如果启用）

### 问题 13: 环境变量问题

#### 症状

- 配置未生效
- 使用了错误的配置值
- 环境变量覆盖了配置文件

#### 环境变量优先级

```
环境变量 > 配置文件 > 默认值
```

#### 常见问题

**1. 环境变量未设置**

**检查**:

```bash
# Windows CMD
echo %WEBCTP_REDIS_HOST%

# Windows PowerShell
$env:WEBCTP_REDIS_HOST

# Linux
echo $WEBCTP_REDIS_HOST
```

**设置**:

```bash
# Windows CMD
set WEBCTP_REDIS_HOST=localhost

# Windows PowerShell
$env:WEBCTP_REDIS_HOST="localhost"

# Linux
export WEBCTP_REDIS_HOST=localhost
```

**2. 环境变量命名错误**

**正确格式**:

```bash
WEBCTP_REDIS_HOST=localhost
WEBCTP_REDIS_PORT=6379
WEBCTP_METRICS_ENABLED=true
```

**错误格式**:

```bash
REDIS_HOST=localhost  # 缺少 WEBCTP_ 前缀
webctp_redis_host=localhost  # 应该全大写
```

**3. 环境变量类型错误**

**正确设置**:

```bash
# 布尔值
set WEBCTP_METRICS_ENABLED=true

# 数字
set WEBCTP_REDIS_PORT=6379

# 字符串
set WEBCTP_REDIS_HOST=localhost
```

**4. 环境变量未持久化**

**问题**:

- 关闭终端后环境变量丢失

**解决方案**:

```bash
# Windows: 设置系统环境变量
setx WEBCTP_REDIS_HOST localhost

# Linux: 添加到 ~/.bashrc
echo 'export WEBCTP_REDIS_HOST=localhost' >> ~/.bashrc
source ~/.bashrc
```

### 问题 14: 权限问题

#### 症状

- 无法创建日志文件
- 无法写入 con_file 目录
- 无法读取配置文件

#### 常见权限问题

**1. 日志目录权限不足**

**错误日志**:

```
PermissionError: [Errno 13] Permission denied: 'logs/webctp.log'
```

**解决方案**:

```bash
# Windows
icacls logs /grant Users:F

# Linux
chmod 755 logs
```

**2. con_file 目录权限不足**

**解决方案**:

```bash
# Windows
icacls con_file /grant Users:F

# Linux
chmod 755 con_file
```

**3. 配置文件权限不足**

**解决方案**:

```bash
# Windows
icacls config /grant Users:R

# Linux
chmod 644 config/*.yaml
```

**4. 虚拟环境权限问题**

**解决方案**:

```bash
# 重新创建虚拟环境
rm -rf .venv
uv sync
```

### 问题 15: 端口冲突

#### 症状

- 服务启动失败
- 错误信息: "Address already in use"
- 端口被占用

#### 诊断和解决

**1. 查找占用端口的进程**

```bash
# Windows
netstat -ano | findstr :8080
tasklist | findstr <PID>

# Linux
lsof -i :8080
```

**2. 终止占用进程**

```bash
# Windows
taskkill /PID <PID> /F

# Linux
kill -9 <PID>
```

**3. 修改配置使用其他端口**

```yaml
# config_md.yaml
Port: 8082  # 改为其他端口

# config_td.yaml
Port: 8083  # 改为其他端口
```

**4. 检查防火墙规则**

```bash
# Windows
netsh advfirewall firewall show rule name=all | findstr 8080

# Linux
sudo iptables -L -n | grep 8080
```

## 日志分析

### 日志文件位置

**主日志文件**:

- `logs/webctp.log` - 所有日志（INFO 及以上）
- `logs/webctp_error.log` - 错误日志（ERROR 及以上）

### 日志级别

| 级别     | 说明     | 用途         |
| -------- | -------- | ------------ |
| DEBUG    | 调试信息 | 开发调试     |
| INFO     | 一般信息 | 正常运行日志 |
| WARNING  | 警告信息 | 潜在问题     |
| ERROR    | 错误信息 | 错误和异常   |
| CRITICAL | 严重错误 | 系统崩溃     |

### 日志格式

```
2025-12-15 10:30:45 | INFO | src.apps.md_app:startup:45 | 行情服务启动成功
```

**格式说明**:

- `2025-12-15 10:30:45` - 时间戳
- `INFO` - 日志级别
- `src.apps.md_app:startup:45` - 模块:函数:行号
- `行情服务启动成功` - 日志消息

### 常用日志查询

#### 查看最新日志

```bash
# Windows PowerShell
Get-Content logs\webctp.log -Tail 50

# Linux
tail -50 logs/webctp.log
```

#### 实时监控日志

```bash
# Windows PowerShell
Get-Content logs\webctp.log -Wait -Tail 50

# Linux
tail -f logs/webctp.log
```

#### 查找错误日志

```bash
# Windows PowerShell
Select-String -Path logs\webctp.log -Pattern "ERROR"

# Linux
grep "ERROR" logs/webctp.log
```

#### 查找特定时间段的日志

```bash
# Linux
sed -n '/2025-12-15 10:00/,/2025-12-15 11:00/p' logs/webctp.log
```

#### 查找特定模块的日志

```bash
# 查找 Redis 相关日志
grep "cache_manager" logs/webctp.log

# 查找 CTP 相关日志
grep "ctp" logs/webctp.log
```

#### 查找性能报告

```bash
# 查看最近的性能报告
grep "性能指标报告" logs/webctp.log -A 30 | tail -35
```

#### 查找告警

```bash
# 查看所有告警
grep "⚠️" logs/webctp.log

# 查看特定类型的告警
grep "延迟告警" logs/webctp.log
grep "Redis 命中率告警" logs/webctp.log
grep "CPU 使用率告警" logs/webctp.log
```

### 日志分析技巧

#### 1. 识别启动问题

**查找启动相关日志**:

```bash
grep "startup\|启动" logs/webctp.log | tail -20
```

**正常启动标志**:

```
INFO | Application startup complete
INFO | Uvicorn running on http://127.0.0.1:8080
INFO | CTP 前置连接成功
```

**启动失败标志**:

```
ERROR | 配置文件加载失败
ERROR | Redis 连接失败
ERROR | CTP 前置连接失败
```

#### 2. 识别连接问题

**查找连接相关日志**:

```bash
grep "连接\|connection" logs/webctp.log | tail -20
```

**连接成功标志**:

```
INFO | WebSocket 连接建立
INFO | CTP 前置连接成功
INFO | Redis 连接成功
```

**连接失败标志**:

```
ERROR | WebSocket 连接失败
ERROR | CTP 前置连接失败
ERROR | Redis 连接失败
```

#### 3. 识别性能问题

**查找性能相关日志**:

```bash
grep "延迟\|latency\|性能" logs/webctp.log | tail -20
```

**性能正常标志**:

```
INFO | order_latency P95: 78.6 ms
INFO | market_latency P95: 35.4 ms
INFO | Redis 命中率: 87.3%
```

**性能异常标志**:

```
WARNING | ⚠️ 延迟告警: order_latency P95 延迟 (150.25 ms) 超过阈值
WARNING | ⚠️ Redis 命中率告警: 当前命中率 (35.50%) 低于阈值
WARNING | ⚠️ CPU 使用率告警: 当前 CPU 使用率 (85.3%) 超过阈值
```

#### 4. 识别错误模式

**查找重复错误**:

```bash
# 统计错误类型
grep "ERROR" logs/webctp.log | cut -d'|' -f4 | sort | uniq -c | sort -rn
```

**查找异常堆栈**:

```bash
grep -A 10 "Traceback" logs/webctp.log
```

### 日志管理

#### 日志轮转

**配置日志轮转**:

```python
# 在代码中配置
logger.add(
    "logs/webctp.log",
    rotation="500 MB",      # 单文件 500MB
    retention="7 days",     # 保留 7 天
    compression="zip"       # 压缩旧日志
)
```

#### 清理旧日志

```bash
# Windows PowerShell
Get-ChildItem logs\*.log | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-7)} | Remove-Item

# Linux
find logs/ -name "*.log" -mtime +7 -delete
```

#### 日志大小监控

```bash
# Windows PowerShell
Get-ChildItem logs\*.log | Select-Object Name, @{Name="Size(MB)";Expression={$_.Length/1MB}}

# Linux
du -h logs/*.log
```

### 日志级别调整

#### 临时调整

**修改配置文件**:

```yaml
LogLevel: DEBUG  # 临时启用 DEBUG 级别
```

**重启服务**:

```bash
# 停止服务 (Ctrl+C)
# 重新启动
python main.py --config=./config/config_md.yaml --app_type=md
```

#### 生产环境建议

```yaml
LogLevel: INFO  # 生产环境使用 INFO
```

**原因**:

- DEBUG 级别会产生大量日志
- 影响性能
- 占用大量磁盘空间

## 诊断工具

### 内置诊断工具

#### 1. 性能报告

**查看性能报告**:

```bash
grep "性能指标报告" logs/webctp.log -A 30 | tail -35
```

**报告内容**:

- 延迟指标（P50, P95, P99）
- 计数器（订单数、行情数）
- Redis 命中率
- 吞吐量
- 瞬时值（活跃连接数）
- 系统资源（CPU、内存）

**使用场景**:

- 性能基线测试
- 性能问题诊断
- 优化效果验证

#### 2. 告警系统

**查看告警**:

```bash
grep "⚠️" logs/webctp.log
```

**告警类型**:

- 延迟告警
- Redis 命中率告警
- CPU 使用率告警
- 内存使用率告警

**使用场景**:

- 实时监控
- 异常检测
- 性能预警

#### 3. 健康检查

**Redis 健康检查**:

```bash
redis-cli ping
# 应该返回 PONG
```

**WebSocket 健康检查**:

```python
import asyncio
import websockets

async def health_check():
    try:
        async with websockets.connect("ws://localhost:8080/ws") as ws:
            print("✅ WebSocket 健康")
    except Exception as e:
        print(f"❌ WebSocket 异常: {e}")

asyncio.run(health_check())
```

### 外部诊断工具

#### 1. Redis 监控工具

**Redis CLI**:

```bash
# 查看 Redis 信息
redis-cli info

# 查看内存使用
redis-cli info memory

# 查看统计信息
redis-cli info stats

# 查看客户端连接
redis-cli info clients

# 查看慢查询
redis-cli slowlog get 10

# 监控命令
redis-cli monitor
```

**Redis Desktop Manager**:

- 图形化 Redis 管理工具
- 可视化数据浏览
- 性能监控

#### 2. 系统监控工具

**Windows 性能监视器**:

```bash
# 启动性能监视器
perfmon
```

**监控指标**:

- CPU 使用率
- 内存使用率
- 磁盘 I/O
- 网络 I/O

**Linux 工具**:

```bash
# CPU 和内存
top
htop

# 网络连接
netstat -tlnp

# 磁盘 I/O
iostat

# 系统资源
vmstat
```

#### 3. 网络诊断工具

**Ping**:

```bash
ping 182.254.243.31
```

**Telnet**:

```bash
telnet 182.254.243.31 40001
```

**PowerShell Test-NetConnection**:

```powershell
Test-NetConnection -ComputerName 182.254.243.31 -Port 40001
```

**Wireshark**:

- 网络抓包工具
- 分析网络流量
- 诊断网络问题

#### 4. Python 性能分析工具

**cProfile**:

```python
import cProfile
import pstats

# 性能分析
cProfile.run('your_function()', 'profile_stats')

# 查看结果
p = pstats.Stats('profile_stats')
p.sort_stats('cumulative')
p.print_stats(20)
```

**memory_profiler**:

```python
from memory_profiler import profile

@profile
def your_function():
    # 你的代码
    pass
```

**py-spy**:

```bash
# 安装
pip install py-spy

# 采样分析
py-spy top --pid <PID>

# 生成火焰图
py-spy record -o profile.svg --pid <PID>
```

### 诊断脚本

#### 系统健康检查脚本

```python
# scripts/health_check.py
import asyncio
import redis
import websockets
import psutil

async def check_health():
    """系统健康检查"""
    print("=== 系统健康检查 ===\n")
    
    # 1. WebSocket 检查
    try:
        async with websockets.connect("ws://localhost:8080/ws", timeout=5) as ws:
            print("✅ WebSocket (MD): 正常")
    except Exception as e:
        print(f"❌ WebSocket (MD): 异常 - {e}")
    
    try:
        async with websockets.connect("ws://localhost:8081/ws", timeout=5) as ws:
            print("✅ WebSocket (TD): 正常")
    except Exception as e:
        print(f"❌ WebSocket (TD): 异常 - {e}")
    
    # 2. Redis 检查
    try:
        r = redis.Redis(host='localhost', port=6379, socket_timeout=5)
        r.ping()
        print("✅ Redis: 正常")
    except Exception as e:
        print(f"❌ Redis: 异常 - {e}")
    
    # 3. 系统资源检查
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    
    print(f"\n📊 系统资源:")
    print(f"  CPU: {cpu_percent:.1f}%")
    print(f"  内存: {memory.percent:.1f}% ({memory.used/1024/1024:.0f} MB)")
    
    if cpu_percent > 80:
        print("  ⚠️ CPU 使用率过高")
    if memory.percent > 80:
        print("  ⚠️ 内存使用率过高")

if __name__ == "__main__":
    asyncio.run(check_health())
```

#### 性能测试脚本

```python
# scripts/performance_test.py
import asyncio
import time
import websockets
import json
from statistics import quantiles

async def test_latency(uri, count=100):
    """测试延迟"""
    latencies = []
    
    async with websockets.connect(uri) as ws:
        # 登录
        login_msg = {
            "MsgType": "ReqUserLogin",
            "BrokerID": "9999",
            "UserID": "your_user_id",
            "Password": "your_password"
        }
        await ws.send(json.dumps(login_msg))
        await ws.recv()
        
        # 测试延迟
        for i in range(count):
            start = time.time()
            
            # 发送查询请求
            query_msg = {
                "MsgType": "ReqQryInvestorPosition",
                "InstrumentID": ""
            }
            await ws.send(json.dumps(query_msg))
            await ws.recv()
            
            latency = (time.time() - start) * 1000
            latencies.append(latency)
            
            await asyncio.sleep(0.1)
        
        # 计算统计
        sorted_lat = sorted(latencies)
        p50 = sorted_lat[len(sorted_lat) // 2]
        p95 = sorted_lat[int(len(sorted_lat) * 0.95)]
        p99 = sorted_lat[int(len(sorted_lat) * 0.99)]
        
        print(f"延迟统计 ({count} 次请求):")
        print(f"  P50: {p50:.2f} ms")
        print(f"  P95: {p95:.2f} ms")
        print(f"  P99: {p99:.2f} ms")
        print(f"  平均: {sum(latencies)/len(latencies):.2f} ms")

if __name__ == "__main__":
    asyncio.run(test_latency("ws://localhost:8081/ws"))
```

### 日志分析脚本

```python
# scripts/analyze_logs.py
import re
from collections import defaultdict

def analyze_errors(log_file):
    """分析错误日志"""
    error_counts = defaultdict(int)
    
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            if 'ERROR' in line:
                # 提取错误类型
                match = re.search(r'ERROR.*?:\s*(.+?)(?:\n|$)', line)
                if match:
                    error_type = match.group(1)[:50]  # 前50个字符
                    error_counts[error_type] += 1
    
    print("=== 错误统计 ===")
    for error, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"{count:4d} - {error}")

def analyze_performance(log_file):
    """分析性能报告"""
    latencies = []
    
    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # 提取 P95 延迟
        matches = re.findall(r'order_latency.*?P95:\s*([\d.]+)\s*ms', content)
        latencies = [float(m) for m in matches]
    
    if latencies:
        print("\n=== 订单延迟趋势 ===")
        print(f"最小 P95: {min(latencies):.2f} ms")
        print(f"最大 P95: {max(latencies):.2f} ms")
        print(f"平均 P95: {sum(latencies)/len(latencies):.2f} ms")
        print(f"样本数: {len(latencies)}")

if __name__ == "__main__":
    analyze_errors("logs/webctp.log")
    analyze_performance("logs/webctp.log")
```

## 错误代码参考

### CTP 错误代码

#### 常见错误码

| 错误码 | 说明           | 可能原因               | 解决方案         |
| ------ | -------------- | ---------------------- | ---------------- |
| 0      | 正确           | -                      | -                |
| 3      | 不合法的登录   | 用户名或密码错误       | 检查账号密码     |
| 4      | 用户不活跃     | 账号被冻结             | 联系券商         |
| 7      | 还没有初始化   | CTP 未初始化完成       | 等待初始化       |
| 22     | 重复的报单     | 订单重复提交           | 检查订单逻辑     |
| 31     | 报单不存在     | 订单号不存在           | 检查订单号       |
| 36     | 超过最大报单数 | 报单数量超限           | 减少报单频率     |
| 50     | 资金不足       | 账户资金不足           | 充值或减少订单量 |
| 63     | 网络连接失败   | 网络问题               | 检查网络连接     |
| 90     | 认证失败       | AuthCode 或 AppID 错误 | 检查认证信息     |

#### 错误码查询

**在日志中查找错误码**:

```bash
grep "ErrorID" logs/webctp.log
```

**错误码格式**:

```
ERROR | 用户登录失败: ErrorID=3, ErrorMsg=CTP:不合法的登录
```

### 系统错误代码

#### Python 异常

| 异常类型          | 说明       | 常见原因             |
| ----------------- | ---------- | -------------------- |
| ConnectionError   | 连接错误   | 网络问题、服务未启动 |
| TimeoutError      | 超时错误   | 操作超时             |
| PermissionError   | 权限错误   | 文件权限不足         |
| FileNotFoundError | 文件未找到 | 配置文件缺失         |
| ValueError        | 值错误     | 配置值类型错误       |
| KeyError          | 键错误     | 配置项缺失           |

#### Redis 错误

| 错误               | 说明       | 解决方案        |
| ------------------ | ---------- | --------------- |
| Connection refused | 连接被拒绝 | 启动 Redis 服务 |
| NOAUTH             | 需要认证   | 提供 Redis 密码 |
| OOM                | 内存不足   | 增加 Redis 内存 |
| READONLY           | 只读模式   | 检查 Redis 配置 |

### 应用错误代码

#### WebSocket 错误

| 状态码 | 说明         | 原因               |
| ------ | ------------ | ------------------ |
| 1000   | 正常关闭     | 正常断开连接       |
| 1001   | 端点离开     | 服务器关闭         |
| 1002   | 协议错误     | WebSocket 协议错误 |
| 1003   | 不支持的数据 | 数据类型错误       |
| 1006   | 异常关闭     | 连接异常断开       |
| 1011   | 服务器错误   | 服务器内部错误     |

#### HTTP 错误

| 状态码 | 说明       | 原因           |
| ------ | ---------- | -------------- |
| 400    | 错误请求   | 请求格式错误   |
| 401    | 未授权     | 需要认证       |
| 403    | 禁止访问   | 权限不足       |
| 404    | 未找到     | 资源不存在     |
| 500    | 服务器错误 | 服务器内部错误 |
| 503    | 服务不可用 | 服务暂时不可用 |

## 获取帮助

### 自助资源

**文档**:

- [README](../README_CN.md) - 项目概述和快速开始
- [开发文档](./development_CN.md) - 开发指南和架构说明
- [监控指南](./monitoring_guide_CN.md) - 性能监控配置
- [迁移指南](./migration_guide_CN.md) - 版本升级指南
- [性能报告](./performance_report_CN.md) - 性能优化成果

**日志分析**:

```bash
# 查看错误日志
grep "ERROR" logs/webctp.log | tail -50

# 查看告警
grep "⚠️" logs/webctp.log

# 查看性能报告
grep "性能指标报告" logs/webctp.log -A 30 | tail -35
```

### 社区支持

**QQ 群**: 446042777

**GitHub Issues**:

- 报告 Bug
- 功能请求
- 技术讨论

### 问题报告模板

提交问题时，请提供以下信息：

```markdown
## 环境信息
- 操作系统: Windows 11 / Linux Ubuntu 22.04
- Python 版本: 3.13.0
- 项目版本: v0.2.0
- Redis 版本: 7.2.3 (如果使用)

## 问题描述
[清晰描述遇到的问题]

## 复现步骤
1. [步骤 1]
2. [步骤 2]
3. [步骤 3]

## 预期行为
[描述预期的正常行为]

## 实际行为
[描述实际发生的情况]

## 错误日志
```

\[粘贴相关的错误日志\]

````

## 配置文件
```yaml
[粘贴相关的配置内容，隐藏敏感信息]
````

## 已尝试的解决方案

\[列出已经尝试过的解决方法\]

## 其他信息

\[任何其他相关信息\]

````

### 紧急问题处理

**严重问题**:
- 系统崩溃
- 数据丢失
- 安全漏洞

**处理流程**:
1. 立即停止服务
2. 备份日志和数据
3. 记录问题现场
4. 联系技术支持
5. 等待指导后再重启

### 常见问题快速索引

**连接问题**:
- [WebSocket 连接失败](#问题-1-websocket-连接失败)
- [CTP 连接失败](#问题-2-ctp-连接失败)
- [Redis 连接失败](#问题-3-redis-连接失败)

**性能问题**:
- [延迟过高](#问题-5-延迟过高)
- [吞吐量低](#问题-6-吞吐量低)
- [系统资源占用高](#问题-7-系统资源占用高)

**缓存问题**:
- [Redis 命中率低](#问题-9-redis-命中率低)
- [缓存数据不一致](#问题-10-缓存数据不一致)
- [Redis 性能下降](#问题-11-redis-性能下降)

**配置问题**:
- [配置文件错误](#问题-12-配置文件错误)
- [环境变量问题](#问题-13-环境变量问题)
- [权限问题](#问题-14-权限问题)

### 技术支持联系方式

**邮箱**: donnymoving@gmail.com

**响应时间**:
- 工作日: 24 小时内
- 周末: 48 小时内
- 紧急问题: 尽快响应

---

## 附录

### A. 故障排查清单

**启动问题**:
- [ ] 检查 Python 版本（3.13）
- [ ] 检查虚拟环境已激活
- [ ] 检查依赖已安装（uv sync）
- [ ] 检查配置文件语法
- [ ] 检查端口未被占用
- [ ] 检查日志目录权限

**连接问题**:
- [ ] 检查服务已启动
- [ ] 检查端口监听状态
- [ ] 检查防火墙设置
- [ ] 检查网络连接
- [ ] 检查前置地址正确
- [ ] 检查账号密码正确

**性能问题**:
- [ ] 查看性能报告
- [ ] 检查 Redis 状态
- [ ] 检查系统资源
- [ ] 检查网络延迟
- [ ] 检查配置是否优化
- [ ] 查看告警日志

**缓存问题**:
- [ ] 检查 Redis 运行
- [ ] 检查 Redis 配置
- [ ] 查看命中率
- [ ] 检查 TTL 设置
- [ ] 检查 Redis 内存
- [ ] 查看慢查询

### B. 常用命令速查

```bash
# 服务管理
python main.py --config=./config/config_md.yaml --app_type=md
python main.py --config=./config/config_td.yaml --app_type=td

# 日志查看
tail -f logs/webctp.log
grep "ERROR" logs/webctp.log
grep "⚠️" logs/webctp.log

# Redis 管理
redis-cli ping
redis-cli info
redis-cli monitor

# 系统监控
top
htop
netstat -tlnp

# 网络测试
ping 182.254.243.31
telnet 182.254.243.31 40001
````

### C. 相关文档

- [README](../README_CN.md) - 项目概述
- [开发文档](./development_CN.md) - 开发指南
- [监控指南](./monitoring_guide_CN.md) - 监控配置
- [迁移指南](./migration_guide_CN.md) - 升级指南
- [性能报告](./performance_report_CN.md) - 性能数据

______________________________________________________________________

**文档版本**: 1.0\
**最后更新**: 2025-12-15\
**维护者**: homalos-webctp 团队
