# 性能监控和告警指南

**版本**: 1.0  
**更新日期**: 2025-12-15

## 目录

- [概述](#概述)
- [性能指标说明](#性能指标说明)
- [配置性能监控](#配置性能监控)
- [配置告警阈值](#配置告警阈值)
- [查看性能报告](#查看性能报告)
- [解读告警消息](#解读告警消息)
- [集成到监控系统](#集成到监控系统)
- [最佳实践](#最佳实践)
- [故障排查](#故障排查)

## 概述

homalos-webctp 内置了完整的性能监控和告警系统，可以实时监控系统性能并在出现异常时自动发出告警。

### 主要功能

- ✅ **实时性能监控**: 自动收集延迟、吞吐量、资源使用等指标
- ✅ **定期性能报告**: 每分钟（可配置）生成性能报告
- ✅ **智能告警**: 自动检测性能异常并发出告警
- ✅ **灵活配置**: 支持 YAML 配置文件和环境变量
- ✅ **零侵入**: 无需修改业务代码，自动集成

### 监控架构

```
┌─────────────────────────────────────────────────────────┐
│                    应用层 (FastAPI)                      │
│  ┌──────────────┐  ┌──────────────┐                    │
│  │  md_app.py   │  │  td_app.py   │                    │
│  └──────┬───────┘  └──────┬───────┘                    │
└─────────┼──────────────────┼──────────────────────────┘
          │                  │
          │  注入 MetricsCollector
          │                  │
┌─────────▼──────────────────▼──────────────────────────┐
│              MetricsCollector                          │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │  延迟指标    │  │  计数器      │  │  瞬时值     │ │
│  └──────────────┘  └──────────────┘  └─────────────┘ │
│  ┌──────────────┐  ┌──────────────┐                  │
│  │  性能报告    │  │  告警检查    │                  │
│  └──────────────┘  └──────────────┘                  │
└────────────────────────────────────────────────────────┘
          │                  │
          ▼                  ▼
    ┌──────────┐      ┌──────────┐
    │  日志文件 │      │  告警系统 │
    └──────────┘      └──────────┘
```

## 性能指标说明

### 延迟指标

延迟指标记录操作从开始到完成的时间，以毫秒为单位。

**指标名称**:
- `order_latency`: 订单延迟（从接收到 CTP 确认）
- `market_latency`: 行情延迟（从 CTP 回调到 WebSocket 发送）
- `redis_get_latency`: Redis 读取延迟
- `redis_set_latency`: Redis 写入延迟
- `redis_hget_latency`: Redis Hash 读取延迟
- `redis_hset_latency`: Redis Hash 写入延迟
- `redis_publish_latency`: Redis 发布延迟
- `md_message_latency`: 行情消息处理延迟
- `td_message_latency`: 交易消息处理延迟

**统计值**:
- **P50**: 50% 的请求延迟低于此值（中位数）
- **P95**: 95% 的请求延迟低于此值
- **P99**: 99% 的请求延迟低于此值

**示例**:
```
order_latency (样本数: 1000):
  P50: 45.23 ms
  P95: 87.56 ms
  P99: 125.34 ms
```


### 计数器指标

计数器记录事件发生的次数。

**指标名称**:
- `order_count`: 订单总数
- `market_data_count`: 行情数据总数
- `cache_hit`: 缓存命中次数
- `cache_miss`: 缓存未命中次数
- `strategy_error_count`: 策略错误次数

**示例**:
```
【计数器】
  order_count: 1523
  cache_hit: 8542
  cache_miss: 1234
```

### 瞬时值指标

瞬时值记录某个时刻的状态值。

**指标名称**:
- `md_active_connections`: 行情服务活跃连接数
- `td_active_connections`: 交易服务活跃连接数
- `active_strategies`: 活跃策略数量

**示例**:
```
【瞬时值】
  md_active_connections: 5
  td_active_connections: 3
  active_strategies: 2
```

### 系统资源指标

系统资源指标记录服务器的资源使用情况。

**指标名称**:
- `cpu_percent`: CPU 使用率（百分比）
- `memory_percent`: 内存使用率（百分比）
- `memory_used_mb`: 内存使用量（MB）
- `network_sent_mb`: 网络发送量（MB，累计）
- `network_recv_mb`: 网络接收量（MB，累计）

**示例**:
```
【系统资源】
  CPU 使用率: 45.2%
  内存使用率: 62.8%
  内存使用量: 2048.5 MB
  网络 I/O: 发送 125.34 MB, 接收 89.67 MB
```

### Redis 命中率

Redis 命中率表示缓存的有效性。

**计算公式**:
```
命中率 = (cache_hit / (cache_hit + cache_miss)) × 100%
```

**示例**:
```
【Redis 命中率】
  命中: 8542, 未命中: 1234
  命中率: 87.38%
```

**解读**:
- **> 80%**: 优秀，缓存工作良好
- **60-80%**: 良好，可以考虑优化缓存策略
- **40-60%**: 一般，需要检查缓存配置
- **< 40%**: 较差，缓存效果不佳，需要优化

### 吞吐量

吞吐量表示单位时间内处理的请求数量。

**计算方式**:
```
吞吐量 = (当前计数 - 上次计数) / 时间间隔
```

**示例**:
```
【吞吐量】
  order_count: 15.23 /秒, 913.80 /分钟
  market_data_count: 234.56 /秒, 14073.60 /分钟
```

## 配置性能监控

### 基础配置

在配置文件（`config_md.yaml` 或 `config_td.yaml`）中添加：

```yaml
# 性能监控配置
Metrics:
  Enabled: true              # 启用性能监控
  ReportInterval: 60         # 报告间隔（秒），默认 60 秒
  SampleRate: 1.0            # 采样率（0.0-1.0），默认 1.0（100%）
```

### 配置说明

**Enabled** (布尔值):
- `true`: 启用性能监控（推荐）
- `false`: 禁用性能监控

**ReportInterval** (整数):
- 性能报告的生成间隔，单位为秒
- 默认值: 60 秒
- 推荐值: 30-300 秒
- 注意: 间隔太短会产生大量日志

**SampleRate** (浮点数):
- 延迟指标的采样率，范围 0.0-1.0
- 1.0 表示记录所有请求（100%）
- 0.1 表示记录 10% 的请求
- 默认值: 1.0
- 推荐值: 高负载时可以降低到 0.1-0.5

### 环境变量配置

也可以通过环境变量配置：

```bash
# Windows CMD
set WEBCTP_METRICS_ENABLED=true
set WEBCTP_METRICS_INTERVAL=60

# Windows PowerShell
$env:WEBCTP_METRICS_ENABLED="true"
$env:WEBCTP_METRICS_INTERVAL="60"

# Linux/Mac
export WEBCTP_METRICS_ENABLED=true
export WEBCTP_METRICS_INTERVAL=60
```

### 禁用性能监控

如果不需要性能监控，可以禁用：

```yaml
Metrics:
  Enabled: false
```

或删除整个 `Metrics` 配置节（默认启用）。

## 配置告警阈值

### 基础配置

在配置文件中添加告警阈值配置：

```yaml
Metrics:
  Enabled: true
  ReportInterval: 60
  SampleRate: 1.0
  
  # 告警阈值配置
  LatencyWarningThresholdMs: 100.0        # 延迟告警阈值（毫秒）
  CacheHitRateWarningThreshold: 50.0      # Redis 命中率告警阈值（百分比）
  CpuWarningThreshold: 80.0               # CPU 使用率告警阈值（百分比）
  MemoryWarningThreshold: 80.0            # 内存使用率告警阈值（百分比）
```

### 阈值说明

**LatencyWarningThresholdMs** (浮点数):
- 延迟告警阈值，单位为毫秒
- 当任何延迟指标的 P95 值超过此阈值时触发告警
- 默认值: 100.0 ms
- 推荐值:
  - 低延迟要求: 50-80 ms
  - 一般要求: 100-150 ms
  - 宽松要求: 200-300 ms

**CacheHitRateWarningThreshold** (浮点数):
- Redis 命中率告警阈值，单位为百分比
- 当缓存命中率低于此阈值时触发告警
- 默认值: 50.0%
- 推荐值:
  - 严格要求: 70-80%
  - 一般要求: 50-60%
  - 宽松要求: 30-40%

**CpuWarningThreshold** (浮点数):
- CPU 使用率告警阈值，单位为百分比
- 当 CPU 使用率超过此阈值时触发告警
- 默认值: 80.0%
- 推荐值:
  - 保守配置: 60-70%
  - 一般配置: 80-85%
  - 激进配置: 90-95%

**MemoryWarningThreshold** (浮点数):
- 内存使用率告警阈值，单位为百分比
- 当内存使用率超过此阈值时触发告警
- 默认值: 80.0%
- 推荐值:
  - 保守配置: 70-75%
  - 一般配置: 80-85%
  - 激进配置: 90-95%

### 环境变量配置

也可以通过环境变量配置告警阈值：

```bash
# Windows CMD
set WEBCTP_METRICS_LATENCY_WARNING_THRESHOLD=100.0
set WEBCTP_METRICS_CACHE_HIT_RATE_WARNING_THRESHOLD=50.0
set WEBCTP_METRICS_CPU_WARNING_THRESHOLD=80.0
set WEBCTP_METRICS_MEMORY_WARNING_THRESHOLD=80.0

# Windows PowerShell
$env:WEBCTP_METRICS_LATENCY_WARNING_THRESHOLD="100.0"
$env:WEBCTP_METRICS_CACHE_HIT_RATE_WARNING_THRESHOLD="50.0"
$env:WEBCTP_METRICS_CPU_WARNING_THRESHOLD="80.0"
$env:WEBCTP_METRICS_MEMORY_WARNING_THRESHOLD="80.0"
```

### 根据环境调整阈值

**开发环境**:
```yaml
LatencyWarningThresholdMs: 200.0        # 宽松的延迟要求
CacheHitRateWarningThreshold: 30.0      # 宽松的命中率要求
CpuWarningThreshold: 90.0               # 宽松的 CPU 要求
MemoryWarningThreshold: 90.0            # 宽松的内存要求
```

**测试环境**:
```yaml
LatencyWarningThresholdMs: 150.0
CacheHitRateWarningThreshold: 40.0
CpuWarningThreshold: 85.0
MemoryWarningThreshold: 85.0
```

**生产环境**:
```yaml
LatencyWarningThresholdMs: 100.0        # 严格的延迟要求
CacheHitRateWarningThreshold: 60.0      # 严格的命中率要求
CpuWarningThreshold: 75.0               # 保守的 CPU 要求
MemoryWarningThreshold: 75.0            # 保守的内存要求
```


## 查看性能报告

### 日志文件位置

性能报告会记录在日志文件中：

- **主日志文件**: `logs/webctp.log`
- **错误日志文件**: `logs/webctp_error.log`

### 性能报告格式

每个报告间隔（默认 60 秒），系统会生成一份性能报告：

```
=== 性能指标报告 ===

【延迟指标】
  order_latency (样本数: 1000):
    P50: 45.23 ms
    P95: 87.56 ms
    P99: 125.34 ms
  market_latency (样本数: 5000):
    P50: 12.34 ms
    P95: 28.67 ms
    P99: 45.89 ms

【计数器】
  order_count: 1523
  market_data_count: 12345
  cache_hit: 8542
  cache_miss: 1234

【Redis 命中率】
  命中: 8542, 未命中: 1234
  命中率: 87.38%

【吞吐量】
  order_count: 15.23 /秒, 913.80 /分钟
  market_data_count: 234.56 /秒, 14073.60 /分钟

【瞬时值】
  md_active_connections: 5
  td_active_connections: 3

【系统资源】
  CPU 使用率: 45.2%
  内存使用率: 62.8%
  内存使用量: 2048.5 MB
  网络 I/O: 发送 125.34 MB, 接收 89.67 MB
==============================
```

### 查看实时报告

**Windows CMD**:
```bash
# 实时查看日志
type logs\webctp.log

# 持续监控日志（需要安装 tail 工具）
tail -f logs\webctp.log
```

**Windows PowerShell**:
```powershell
# 实时查看日志
Get-Content logs\webctp.log -Tail 50

# 持续监控日志
Get-Content logs\webctp.log -Wait -Tail 50
```

**Linux/Mac**:
```bash
# 实时查看日志
tail -f logs/webctp.log

# 查看最近的性能报告
grep -A 30 "性能指标报告" logs/webctp.log | tail -35
```

### 过滤性能报告

**只查看性能报告**:
```bash
# Windows PowerShell
Select-String -Path logs\webctp.log -Pattern "性能指标报告" -Context 0,30

# Linux/Mac
grep -A 30 "性能指标报告" logs/webctp.log
```

**查看特定指标**:
```bash
# 查看延迟指标
grep "延迟指标" logs/webctp.log -A 10

# 查看 Redis 命中率
grep "Redis 命中率" logs/webctp.log -A 3

# 查看系统资源
grep "系统资源" logs/webctp.log -A 5
```

## 解读告警消息

### 告警消息格式

告警消息使用 ⚠️ 符号标识，并包含专用标签 `metrics_alert`：

```
WARNING | src.utils.metrics:_report:271 | [metrics_alert] ⚠️ 延迟告警: order_latency P95 延迟 (150.25 ms) 超过阈值 (100.00 ms)
```

### 告警类型

#### 1. 延迟告警

**消息格式**:
```
⚠️ 延迟告警: {metric_name} P95 延迟 ({current_value} ms) 超过阈值 ({threshold} ms)
```

**示例**:
```
⚠️ 延迟告警: order_latency P95 延迟 (150.25 ms) 超过阈值 (100.00 ms)
```

**含义**: 订单延迟的 P95 值为 150.25 ms，超过了配置的阈值 100 ms

**可能原因**:
- CTP API 响应慢
- 网络延迟高
- 系统负载过高
- 数据库查询慢

**处理建议**:
1. 检查 CTP 连接状态
2. 检查网络连接质量
3. 检查系统资源使用情况
4. 优化业务逻辑
5. 考虑调整阈值（如果当前阈值过于严格）

#### 2. Redis 命中率告警

**消息格式**:
```
⚠️ Redis 命中率告警: 当前命中率 ({current_rate}%) 低于阈值 ({threshold}%)
```

**示例**:
```
⚠️ Redis 命中率告警: 当前命中率 (35.50%) 低于阈值 (50.00%)
```

**含义**: Redis 缓存命中率为 35.50%，低于配置的阈值 50%

**可能原因**:
- 缓存 TTL 设置过短
- 查询的数据变化频繁
- Redis 内存不足导致数据被驱逐
- 缓存预热不充分

**处理建议**:
1. 检查 Redis 内存使用情况
2. 调整缓存 TTL 配置
3. 实施缓存预热策略
4. 检查是否有大量冷数据查询
5. 考虑增加 Redis 内存

#### 3. CPU 使用率告警

**消息格式**:
```
⚠️ CPU 使用率告警: 当前 CPU 使用率 ({current_value}%) 超过阈值 ({threshold}%)
```

**示例**:
```
⚠️ CPU 使用率告警: 当前 CPU 使用率 (85.3%) 超过阈值 (80.0%)
```

**含义**: CPU 使用率为 85.3%，超过了配置的阈值 80%

**可能原因**:
- 系统负载过高
- 策略计算密集
- 序列化/反序列化开销大
- 其他进程占用 CPU

**处理建议**:
1. 检查是否有异常进程
2. 优化策略算法
3. 减少不必要的计算
4. 考虑增加 CPU 资源
5. 调整采样率降低开销

#### 4. 内存使用率告警

**消息格式**:
```
⚠️ 内存使用率告警: 当前内存使用率 ({current_value}%) 超过阈值 ({threshold}%)
```

**示例**:
```
⚠️ 内存使用率告警: 当前内存使用率 (87.2%) 超过阈值 (80.0%)
```

**含义**: 内存使用率为 87.2%，超过了配置的阈值 80%

**可能原因**:
- 内存泄漏
- 缓存数据过多
- 策略占用内存过大
- 其他进程占用内存

**处理建议**:
1. 检查是否有内存泄漏
2. 清理不必要的缓存数据
3. 限制策略内存使用
4. 考虑增加内存资源
5. 重启服务释放内存

### 查看告警

**查看所有告警**:
```bash
# Windows PowerShell
Select-String -Path logs\webctp.log -Pattern "⚠️"

# Linux/Mac
grep "⚠️" logs/webctp.log
```

**查看特定类型的告警**:
```bash
# 延迟告警
grep "延迟告警" logs/webctp.log

# Redis 命中率告警
grep "Redis 命中率告警" logs/webctp.log

# CPU 使用率告警
grep "CPU 使用率告警" logs/webctp.log

# 内存使用率告警
grep "内存使用率告警" logs/webctp.log
```

**使用日志标签过滤**:
```bash
# 只查看告警日志
grep "metrics_alert" logs/webctp.log
```

### 告警统计

**统计告警数量**:
```bash
# Windows PowerShell
(Select-String -Path logs\webctp.log -Pattern "⚠️").Count

# Linux/Mac
grep -c "⚠️" logs/webctp.log
```

**按类型统计**:
```bash
# Linux/Mac
echo "延迟告警: $(grep -c '延迟告警' logs/webctp.log)"
echo "Redis 命中率告警: $(grep -c 'Redis 命中率告警' logs/webctp.log)"
echo "CPU 使用率告警: $(grep -c 'CPU 使用率告警' logs/webctp.log)"
echo "内存使用率告警: $(grep -c '内存使用率告警' logs/webctp.log)"
```


## 集成到监控系统

### 日志收集

#### 使用 Filebeat

**安装 Filebeat**:
```bash
# 下载并安装 Filebeat
# 参考: https://www.elastic.co/downloads/beats/filebeat
```

**配置 Filebeat** (`filebeat.yml`):
```yaml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - D:/Project/homalos-webctp/logs/webctp.log
  fields:
    service: homalos-webctp
    log_type: application
  
  # 多行日志处理
  multiline.pattern: '^\d{4}-\d{2}-\d{2}'
  multiline.negate: true
  multiline.match: after

# 输出到 Elasticsearch
output.elasticsearch:
  hosts: ["localhost:9200"]
  index: "homalos-webctp-%{+yyyy.MM.dd}"

# 或输出到 Logstash
output.logstash:
  hosts: ["localhost:5044"]
```

#### 使用 Fluentd

**配置 Fluentd** (`fluent.conf`):
```xml
<source>
  @type tail
  path D:/Project/homalos-webctp/logs/webctp.log
  pos_file D:/Project/homalos-webctp/logs/webctp.log.pos
  tag homalos.webctp
  <parse>
    @type multiline
    format_firstline /^\d{4}-\d{2}-\d{2}/
    format1 /^(?<time>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| (?<level>\w+) \| (?<message>.*)/
  </parse>
</source>

<match homalos.webctp>
  @type elasticsearch
  host localhost
  port 9200
  index_name homalos-webctp
  type_name _doc
</match>
```

### 告警通知

#### 钉钉机器人

**Python 脚本** (`send_dingtalk_alert.py`):
```python
import requests
import json

def send_dingtalk_alert(webhook_url, message):
    """发送告警到钉钉"""
    headers = {'Content-Type': 'application/json'}
    data = {
        "msgtype": "text",
        "text": {
            "content": f"⚠️ homalos-webctp 告警\n\n{message}"
        }
    }
    response = requests.post(webhook_url, headers=headers, data=json.dumps(data))
    return response.json()

# 使用示例
webhook_url = "https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN"
message = "延迟告警: order_latency P95 延迟 (150.25 ms) 超过阈值 (100.00 ms)"
send_dingtalk_alert(webhook_url, message)
```

**集成到日志系统**:
```python
from loguru import logger

# 配置 loguru 将告警发送到钉钉
def dingtalk_sink(message):
    record = message.record
    if record["extra"].get("tag") == "metrics_alert":
        send_dingtalk_alert(webhook_url, record["message"])

logger.add(dingtalk_sink, filter=lambda record: record["extra"].get("tag") == "metrics_alert")
```

#### 企业微信机器人

**Python 脚本** (`send_wechat_alert.py`):
```python
import requests
import json

def send_wechat_alert(webhook_url, message):
    """发送告警到企业微信"""
    headers = {'Content-Type': 'application/json'}
    data = {
        "msgtype": "text",
        "text": {
            "content": f"⚠️ homalos-webctp 告警\n\n{message}"
        }
    }
    response = requests.post(webhook_url, headers=headers, data=json.dumps(data))
    return response.json()
```

#### 邮件通知

**Python 脚本** (`send_email_alert.py`):
```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email_alert(smtp_server, smtp_port, sender, password, recipients, subject, message):
    """发送告警邮件"""
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    msg['Subject'] = subject
    
    body = f"⚠️ homalos-webctp 告警\n\n{message}"
    msg.attach(MIMEText(body, 'plain'))
    
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(sender, password)
    text = msg.as_string()
    server.sendmail(sender, recipients, text)
    server.quit()

# 使用示例
send_email_alert(
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    sender="your_email@gmail.com",
    password="your_password",
    recipients=["admin@example.com"],
    subject="homalos-webctp 性能告警",
    message="延迟告警: order_latency P95 延迟 (150.25 ms) 超过阈值 (100.00 ms)"
)
```

### Prometheus 集成

虽然当前系统使用日志记录指标，但可以通过以下方式集成到 Prometheus：

#### 方案 1: 使用 Prometheus Pushgateway

**安装 Pushgateway**:
```bash
# 下载并运行 Pushgateway
# 参考: https://github.com/prometheus/pushgateway
```

**推送指标到 Pushgateway**:
```python
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

registry = CollectorRegistry()

# 创建指标
order_latency_p95 = Gauge('order_latency_p95', 'Order latency P95', registry=registry)
cache_hit_rate = Gauge('cache_hit_rate', 'Cache hit rate', registry=registry)

# 设置指标值
order_latency_p95.set(87.56)
cache_hit_rate.set(87.38)

# 推送到 Pushgateway
push_to_gateway('localhost:9091', job='homalos-webctp', registry=registry)
```

#### 方案 2: 使用 Prometheus Exporter

创建自定义 Exporter 暴露指标：

```python
from prometheus_client import start_http_server, Gauge
import time

# 创建指标
order_latency_p95 = Gauge('order_latency_p95', 'Order latency P95')
cache_hit_rate = Gauge('cache_hit_rate', 'Cache hit rate')

# 启动 HTTP 服务器
start_http_server(8000)

# 定期更新指标
while True:
    # 从 MetricsCollector 获取指标
    metrics = collector.get_summary()
    
    # 更新 Prometheus 指标
    if 'order_latency' in metrics['latencies']:
        p95 = metrics['latencies']['order_latency']['percentiles'].get(0.95, 0)
        order_latency_p95.set(p95)
    
    # 计算命中率
    cache_hit = metrics['counters'].get('cache_hit', 0)
    cache_miss = metrics['counters'].get('cache_miss', 0)
    if cache_hit + cache_miss > 0:
        hit_rate = (cache_hit / (cache_hit + cache_miss)) * 100
        cache_hit_rate.set(hit_rate)
    
    time.sleep(60)
```

### Grafana 可视化

**创建 Grafana Dashboard**:

1. 添加 Prometheus 数据源
2. 创建新的 Dashboard
3. 添加面板：

**延迟面板**:
```promql
# P95 延迟
order_latency_p95
market_latency_p95

# 延迟趋势
rate(order_latency_p95[5m])
```

**Redis 命中率面板**:
```promql
# 命中率
cache_hit_rate

# 命中率趋势
rate(cache_hit_rate[5m])
```

**系统资源面板**:
```promql
# CPU 使用率
cpu_percent

# 内存使用率
memory_percent
```

## 最佳实践

### 1. 合理设置报告间隔

**推荐配置**:
- **开发环境**: 30-60 秒（快速反馈）
- **测试环境**: 60-120 秒（平衡性能和日志量）
- **生产环境**: 60-300 秒（减少日志量）

**注意事项**:
- 间隔太短会产生大量日志
- 间隔太长可能错过短期异常
- 根据磁盘空间和日志轮转策略调整

### 2. 调整采样率

**推荐配置**:
- **低负载** (< 100 请求/秒): 1.0（100%）
- **中负载** (100-1000 请求/秒): 0.5（50%）
- **高负载** (> 1000 请求/秒): 0.1-0.2（10-20%）

**注意事项**:
- 采样率影响延迟指标的准确性
- 计数器和瞬时值不受采样率影响
- 高负载时降低采样率可以减少性能开销

### 3. 根据业务调整阈值

**延迟阈值**:
- 考虑业务对延迟的容忍度
- 参考历史数据设置合理阈值
- 定期review和调整

**Redis 命中率阈值**:
- 考虑缓存策略和数据特性
- 新系统可以设置较低阈值
- 成熟系统应该有较高命中率

**资源阈值**:
- 考虑硬件配置
- 留有足够的安全余量
- 避免频繁触发告警

### 4. 定期审查性能报告

**建议频率**:
- **每日**: 快速浏览关键指标
- **每周**: 详细分析性能趋势
- **每月**: 生成性能报告和优化建议

**关注重点**:
- 延迟趋势（是否持续上升）
- Redis 命中率（是否稳定）
- 系统资源使用（是否接近上限）
- 告警频率（是否需要调整阈值）

### 5. 建立告警响应流程

**告警分级**:
- **P0**: 严重影响业务（如系统崩溃）
- **P1**: 影响性能（如延迟超标）
- **P2**: 潜在问题（如命中率下降）
- **P3**: 信息提示（如资源使用上升）

**响应流程**:
1. 接收告警通知
2. 确认告警真实性
3. 评估影响范围
4. 采取应对措施
5. 记录处理过程
6. 事后分析和改进

### 6. 日志管理

**日志轮转**:
```yaml
# loguru 配置
logger.add(
    "logs/webctp.log",
    rotation="500 MB",      # 单个文件最大 500MB
    retention="7 days",     # 保留 7 天
    compression="zip"       # 压缩旧日志
)
```

**日志清理**:
```bash
# Windows PowerShell
# 删除 7 天前的日志
Get-ChildItem logs\*.log | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-7)} | Remove-Item

# Linux/Mac
# 删除 7 天前的日志
find logs/ -name "*.log" -mtime +7 -delete
```

## 故障排查

### 问题 1: 性能报告未生成

**症状**: 日志中没有性能报告

**可能原因**:
1. 性能监控未启用
2. 报告间隔设置过长
3. 日志级别设置过高

**解决方案**:
```yaml
# 检查配置
Metrics:
  Enabled: true              # 确保启用
  ReportInterval: 60         # 检查间隔

# 检查日志级别
LogLevel: INFO               # 不要设置为 ERROR 或 CRITICAL
```

### 问题 2: 告警过多

**症状**: 频繁收到告警通知

**可能原因**:
1. 阈值设置过于严格
2. 系统确实存在性能问题
3. 短期波动触发告警

**解决方案**:
1. 分析告警原因
2. 调整阈值配置
3. 优化系统性能
4. 考虑添加告警静默期

### 问题 3: Redis 命中率低

**症状**: 频繁收到 Redis 命中率告警

**可能原因**:
1. 缓存 TTL 设置过短
2. 查询的数据变化频繁
3. Redis 内存不足
4. 缓存预热不充分

**解决方案**:
```yaml
# 调整 TTL 配置
Redis:
  MarketSnapshotTTL: 120     # 增加到 120 秒
  MarketTickTTL: 10          # 增加到 10 秒
  OrderTTL: 172800           # 增加到 48 小时
```

### 问题 4: 系统资源告警

**症状**: 频繁收到 CPU 或内存告警

**可能原因**:
1. 系统负载过高
2. 策略计算密集
3. 内存泄漏
4. 其他进程占用资源

**解决方案**:
1. 检查系统负载
2. 优化策略算法
3. 检查内存泄漏
4. 增加硬件资源
5. 调整采样率

### 问题 5: 延迟持续超标

**症状**: 延迟告警持续触发

**可能原因**:
1. CTP API 响应慢
2. 网络延迟高
3. 系统资源不足
4. 数据库查询慢

**解决方案**:
1. 检查 CTP 连接状态
2. 检查网络质量
3. 优化查询逻辑
4. 增加缓存使用
5. 升级硬件资源

---

## 附录

### A. 完整配置示例

```yaml
# config_md.yaml 或 config_td.yaml

# CTP 配置
TdFrontAddress: tcp://182.254.243.31:40001
MdFrontAddress: tcp://182.254.243.31:40011
BrokerID: "9999"
AuthCode: "0000000000000000"
AppID: simnow_client_test
Port: 8080
Host: 127.0.0.1
LogLevel: INFO

# Redis 配置
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

### B. 常用命令速查

```bash
# 查看性能报告
grep "性能指标报告" logs/webctp.log -A 30

# 查看所有告警
grep "⚠️" logs/webctp.log

# 查看延迟告警
grep "延迟告警" logs/webctp.log

# 查看 Redis 命中率告警
grep "Redis 命中率告警" logs/webctp.log

# 统计告警数量
grep -c "⚠️" logs/webctp.log

# 实时监控日志
tail -f logs/webctp.log

# 查看最近的性能报告
grep "性能指标报告" logs/webctp.log | tail -1 -A 30
```

### C. 相关文档

- [README](../README_CN.md) - 项目概述和快速开始
- [开发文档](./development_CN.md) - 开发指南和架构说明
- [迁移指南](./migration_guide_CN.md) - 从旧版本升级指南
- [日志指南](./logger_guide_CN.md) - 日志配置和使用

---

**文档版本**: 1.0  
**最后更新**: 2025-12-15  
**维护者**: homalos-webctp 团队
