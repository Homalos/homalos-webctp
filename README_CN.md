<p align="center">
  <font size="5px">✨ 基于Python CTP API 开发的提供 websocket 接口的 CTP 服务✨</font>
</p>

<p align="center">
  <a href="https://qun.qq.com/universal-share/share?ac=1&authKey=dzGDk%2F%2Bpy%2FwpVyR%2BTrt9%2B5cxLZrEHL793cZlFWvOXuV5I8szMnOU4Wf3ylap7Ph0&busi_data=eyJncm91cENvZGUiOiI0NDYwNDI3NzciLCJ0b2tlbiI6IlFrM0ZhZmRLd0xIaFdsZE9FWjlPcHFwSWxBRFFLY2xZbFhaTUh4K2RldisvcXlBckZ4NVIrQzVTdDNKUFpCNi8iLCJ1aW4iOiI4MjEzMDAwNzkifQ%3D%3D&data=O1Bf7_yhnvrrLsJxc3g5-p-ga6TWx6EExnG0S1kDNJTyK4sV_Nd9m4p-bkG4rhj_5TdtS5lMjVZRBv4amHyvEA&svctype=4&tempid=h5_group_info"><img alt="Group#1" title="Group#1"
src="https://img.shields.io/badge/Group%231-Join-blue"/></a>
</p>

<p align="center">
  简体中文 |
  <a href="README.md">English</a>
</p>

## 目录

- [概述](#%E6%A6%82%E8%BF%B0)
- [安装及运行](#%E5%AE%89%E8%A3%85%E5%8F%8A%E8%BF%90%E8%A1%8C)
  - [环境依赖](#%E7%8E%AF%E5%A2%83%E4%BE%9D%E8%B5%96)
  - [环境搭建](#%E7%8E%AF%E5%A2%83%E6%90%AD%E5%BB%BA)
  - [运行](#%E8%BF%90%E8%A1%8C)
- [性能优化功能](#%E6%80%A7%E8%83%BD%E4%BC%98%E5%8C%96%E5%8A%9F%E8%83%BD)
  - [Redis 缓存](#redis-%E7%BC%93%E5%AD%98)
  - [性能监控和告警](#%E6%80%A7%E8%83%BD%E7%9B%91%E6%8E%A7%E5%92%8C%E5%91%8A%E8%AD%A6)
  - [策略管理](#%E7%AD%96%E7%95%A5%E7%AE%A1%E7%90%86)
- [请求示例](#%E8%AF%B7%E6%B1%82%E7%A4%BA%E4%BE%8B)
  - [部分示例](#%E9%83%A8%E5%88%86%E7%A4%BA%E4%BE%8B)
- [协议](#%E5%8D%8F%E8%AE%AE)
  - [通用协议格式](#%E9%80%9A%E7%94%A8%E5%8D%8F%E8%AE%AE%E6%A0%BC%E5%BC%8F)
  - [部分通用错误码说明](#%E9%83%A8%E5%88%86%E9%80%9A%E7%94%A8%E9%94%99%E8%AF%AF%E7%A0%81%E8%AF%B4%E6%98%8E)
  - [详细接口文档](#%E8%AF%A6%E7%BB%86%E6%8E%A5%E5%8F%A3%E6%96%87%E6%A1%A3)
- [项目结构](#%E9%A1%B9%E7%9B%AE%E7%BB%93%E6%9E%84)
- [架构说明](#%E6%9E%B6%E6%9E%84%E8%AF%B4%E6%98%8E)
  - [三层架构](#%E4%B8%89%E5%B1%82%E6%9E%B6%E6%9E%84)
  - [核心组件](#%E6%A0%B8%E5%BF%83%E7%BB%84%E4%BB%B6)
- [测试](#%E6%B5%8B%E8%AF%95)
- [文档](#%E6%96%87%E6%A1%A3)
- [其他说明](#%E5%85%B6%E4%BB%96%E8%AF%B4%E6%98%8E)

## 概述

homalos-webctp 是一个基于 Python CTP API 的开发的提供 Websocket 接口的 CTP 服务，旨在提供接口的方式进行期货量化交易的操作和开发。

- **当前状态**: 核心功能已完成，性能优化阶段 1 已完成

### 主要特性

- ✅ **WebSocket 接口**: 基于 FastAPI 的 WebSocket 服务，支持跨平台客户端
- ✅ **双服务架构**: 独立的行情服务 (MD) 和交易服务 (TD)
- ✅ **Redis 缓存**: 集成 Redis 缓存层，提升查询性能和降低 CTP API 调用频率
- ✅ **优化的序列化**: 使用 orjson 和 msgpack 优化消息序列化性能
- ✅ **多策略支持**: 支持多个交易策略并行运行，策略间相互隔离
- ✅ **性能监控**: 完整的性能指标收集和监控系统
- ✅ **智能告警**: 自动检测性能异常并发出告警
- ✅ **向后兼容**: 保持 JSON 协议不变，现有客户端无需修改

## 安装及运行

### 环境依赖

- **Python** ：3.13

- **工具**：UV

- **CTP API**：6.7.10

### 环境搭建

1. 准备环境

   安装 UV，推荐使用 UV

   <details>
   <summary>👈方式一、系统全局安装，推荐此种方式，其他 Python 项目也可以使用 UV 管理。</summary>

   在 Windows 系统安装

   ```bash
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

   在 Linux 系统安装

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

   </details>

   <details>
   <summary>👈方式二、在已有 Python 中安装</summary>

   和上述方式二选一，如果执行了方式一，则方式二直接跳过。此种安装方式的 UV 只能在这一个 Python 环境中使用。

   ```bash
   pip install uv
   ```

   </details>

1. 安装 Python

   如果在步骤1中选择了全局安装 UV，则需要执行这一步，已安装直接跳过

   ```bash
   uv python install 3.13
   ```

   <details>
   <summary>👈Tips</summary>
   此种方式是全局安装 Python，与项目中的 Python 环境是隔离的，互不影响
   </details>

1. 克隆项目

   ```bash
   git clone https://github.com/Homalos/homalos-webctp.git
   cd homalos-webctp
   ```

1. 安装依赖

   ```bash
   uv sync
   ```

   根据 pyproject.toml 中的信息，自动在当前项目根目录下创建名为 .venv 的 Python 虚拟环境及所有依赖安装

1. 配置

   <details>
   <summary>👈配置参考</summary>

   > :pushpin: 配置参考示例 config.example.yaml，示例中行情和交易前置地址，默认配置的是 SimNow 7x24 环境， 更多 SimNow 环境详细信息参考 [SimNow官网](https://www.simnow.com.cn/product.action)、[openctp环境监控](http://121.37.80.177)，可根据需变更为其他支持CTPAPI(官方实现)的柜台环境。
   >
   > :pushpin: SimNow 7x24 环境：
   >
   > <table>
   > <tr>
   > 	<th colspan="3">前置信息</th>
   > </tr>
   > <tr>
   > 	<td>BrokerID</td>
   > 	<td>9999</td>
   > 	<td>券商ID</td>
   > </tr>
   > <tr>
   > 	<td>Trade Front</td>
   > 	<td>182.254.243.31:40001</td>
   > 	<td rowspan="2">看穿式前置，使用监控中心生产秘钥</td>
   > </tr>
   > <tr>
   > 	<td>Market Front</td>
   > 	<td>182.254.243.31:40011</td>
   > </tr>
   > <tr>
   > 	<td rowspan="2">交易阶段(服务时间)</td>
   > 	<td>交易日，16:00～次日09:00</td>
   > 	<td></td>
   > </tr>
   > <tr>
   > 	<td>非交易日，16:00～次日12:00</td>
   > 	<td></td>
   > </tr>
   > </table>
   >
   > - 该环境仅服务于CTP API开发爱好者，仅为用户提供CTP API测试需求，不提供结算等其它服务。
   >
   > - 新注册用户，需要等到第三个交易日才能使用第二套环境。
   >
   > - 账户、钱、仓跟第一套环境上一个交易日保持一致。
   >
   > :pushpin:  SimNow 非7x24环境：
   >
   > <table>
   > <tr>
   > 	<th colspan="4">前置信息</th>
   > </tr>
   > <tr>
   > 	<td>BrokerID</td>
   > 	<td colspan="3">9999</td>
   > </tr>
   > <tr>
   > 	<td>APPID</td>
   > 	<td colspan="3">simnow_client_test</td>
   > </tr>
   > <tr>
   > 	<td>AuthCode</td>
   > 	<td colspan="3">0000000000000000（16个0）</td>
   > </tr>
   > <tr>
   > 	<td rowspan="2">第一组</td>
   > 	<td>Trade Front</td>
   > 	<td>182.254.243.31:30001</td>
   > 	<td rowspan="6">看穿式前置，使用监控中心生产秘钥</td>
   > </tr>
   > <tr>
   > 	<td>Market Front</td>
   > 	<td>182.254.243.31:30012</td>
   > </tr>
   > <tr>
   > 	<td rowspan="2">第二组</td>
   > 	<td>Trade Front</td>
   > 	<td>182.254.243.31:30002</td>
   > </tr>
   > <tr>
   > 	<td>Market Front</td>
   > 	<td>182.254.243.31:30012</td>
   > </tr>
   > <tr>
   > 	<td rowspan="2">第三组</td>
   > 	<td>Trade Front</td>
   > 	<td>182.254.243.31:30003</td>
   > </tr>
   > <tr>
   > 	<td>Market Front</td>
   > 	<td>182.254.243.31:30013</td>
   > </tr>
   > <tr>
   > 	<td>交易阶段(服务时间)</td>
   > 	<td colspan="3">与实际生产环境保持一致。</td>
   > </tr>
   > </table>
   >
   > - 支持上期所期权、能源中心期权、中金所期权、广期所期权、郑商所期权、大商所期权
   >
   > - 用户注册后，默认的 APPID 为 simnow_client_test，认证码为 0000000000000000（16个0），默认开启终端认证，程序化用户可以选择不开终端认证接入。
   >
   > - 交易品种：六所所有期货品种以及上期所、能源中心、中金所、广期所所有期权品种，以及郑商所、大商所部分期权品种。
   >
   > - 账户资金：初始资金两千万，支持入金，每日最多三次。
   >
   > 见 [SimNow官网](https://www.simnow.com.cn/product.action)

   </details>

   创建自己的行情配置 config_md.yaml :

   ```yaml
   TdFrontAddress: tcp://182.254.243.31:40001	# 交易前置地址
   MdFrontAddress: tcp://182.254.243.31:40011	# 行情前置地址
   BrokerID: "9999"							# 券商ID
   AuthCode: "0000000000000000"				# 认证码
   AppID: simnow_client_test					# 应用ID
   Port: 8080									# the listening port, default 8080
   Host: 127.0.0.1								# the bind ip address, default 127.0.0.1
   LogLevel: INFO								# NOTSET, DEBUG, INFO, WARN, ERROR, CRITICAL
   ```

   创建自己的交易配置 config_td.yaml :

   ```yaml
   TdFrontAddress: tcp://182.254.243.31:40001	# 交易前置地址
   MdFrontAddress: tcp://182.254.243.31:40011	# 行情前置地址
   BrokerID: "9999"							# 券商ID
   AuthCode: "0000000000000000"				# 认证码
   AppID: simnow_client_test					# 应用ID
   Port: 8081									# the listening port, default 8081
   Host: 127.0.0.1								# the bind ip address, default 127.0.0.1
   LogLevel: INFO								# NOTSET, DEBUG, INFO, WARN, ERROR, CRITICAL
   ```

### 运行

```bash
# 激活项目根目录下的虚拟环境，不激活用的是系统默认 Python 而不是项目所需要的 Python环境
.venv\Scripts\activate
# 启动交易服务
python main.py --config=./config/config_td.yaml --app_type=td
# 启动行情服务
python main.py --config=./config/config_md.yaml --app_type=md

# 或者运行脚本
start_td_server.bat
start_md_server.bat
```

## 性能优化功能

### SyncStrategyApi 模块化重构

**重构完成！** SyncStrategyApi 已完成模块化重构，代码质量和可维护性得到显著提升。

#### 重构成果

- ✅ **模块化架构**: 将 2300+ 行的单一文件拆分为多个职责清晰的模块
- ✅ **代码复用**: 通用缓存管理器和事件管理器消除了重复代码
- ✅ **插件系统**: 支持在不修改核心代码的情况下扩展功能
- ✅ **向后兼容**: 完全保持 API 接口不变，现有代码无需修改
- ✅ **测试完善**: 完整的单元测试和属性测试覆盖
- ✅ **文档齐全**: 详细的模块文档和插件开发指南

#### 模块结构

```
src/strategy/
├── sync_api.py (~400 行)           # 主模块，提供公共接口
└── internal/                        # 内部模块
    ├── data_models.py              # Quote 和 Position 数据类
    ├── cache_manager.py            # 通用缓存管理器
    ├── event_manager.py            # 统一事件管理器
    ├── event_loop_thread.py        # 后台事件循环线程
    ├── plugin.py                   # 插件系统
    ├── order_helper.py             # 订单处理辅助函数
    └── instrument_helper.py        # 合约信息处理辅助函数
```

#### 插件系统

插件系统允许你在不修改核心代码的情况下扩展功能：

```python
from src.strategy.sync_api import SyncStrategyApi, StrategyPlugin

class MyPlugin(StrategyPlugin):
    def on_init(self, api):
        print("插件初始化")
    
    def on_quote(self, quote):
        print(f"收到行情: {quote.InstrumentID} @ {quote.LastPrice}")
        return quote

api = SyncStrategyApi("user_id", "password")
api.register_plugin(MyPlugin())
```

**插件示例**:

- `examples/plugins/logging_plugin.py` - 日志记录插件
- `examples/plugins/risk_control_plugin.py` - 风控插件

**插件开发指南**: 参见 [examples/plugins/README.md](examples/plugins/README.md)

#### 使用示例

基本用法（与重构前完全相同）：

```python
from src.strategy.sync_api import SyncStrategyApi

# 初始化 API（自动连接和登录）
api = SyncStrategyApi(
    user_id="your_user_id",
    password="your_password",
    config_path="config.yaml"
)

# 获取行情
quote = api.get_quote("rb2605")
print(f"最新价: {quote.LastPrice}")

# 获取持仓
position = api.get_position("rb2605")
print(f"多头持仓: {position.pos_long}")

# 开仓
result = api.open_close("rb2605", "kaiduo", 1, 3500.0)
if result["success"]:
    print(f"订单成功: {result['order_ref']}")

# 停止服务
api.stop()
```

#### 重构优势

1. **更易维护**: 每个模块不超过 300 行，职责单一
1. **更易测试**: 模块化的测试结构，测试覆盖率更高
1. **更易扩展**: 插件系统支持功能扩展，无需修改核心代码
1. **更易理解**: 清晰的模块边界和文档说明

详细信息请参考：

- [重构设计文档](.kiro/specs/sync-api-refactoring/design.md)
- [插件开发指南](examples/plugins/README.md)
- [性能验证报告](tests/strategy/PERFORMANCE_VALIDATION_REPORT.md)

### Redis 缓存

系统集成了 Redis 缓存层，可以显著提升查询性能并降低对 CTP API 的调用频率。

#### 配置 Redis

在配置文件中添加 Redis 配置（可选）：

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

#### 缓存功能

- **行情快照缓存**: 缓存最新的行情数据，减少重复查询
- **账户状态缓存**: 缓存持仓、资金、订单信息
- **Redis Pub/Sub**: 通过 Redis 发布/订阅模式分发行情数据
- **自动降级**: Redis 不可用时自动切换到直接查询模式

#### 环境变量配置

也可以通过环境变量配置 Redis：

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

### 性能监控和告警

系统内置完整的性能监控和告警功能。

#### 配置性能监控

在配置文件中添加性能监控配置（可选）：

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

#### 监控指标

系统自动收集以下性能指标：

- **延迟指标**: 订单延迟、行情延迟、Redis 操作延迟（P50, P95, P99）
- **吞吐量**: 每秒/每分钟的订单数、行情数
- **Redis 命中率**: 缓存命中次数和未命中次数
- **系统资源**: CPU 使用率、内存使用率、网络 I/O

#### 性能告警

系统会自动检测以下异常情况并发出告警：

- ⚠️ **延迟告警**: 当 P95 延迟超过阈值时
- ⚠️ **Redis 命中率告警**: 当缓存命中率低于阈值时
- ⚠️ **CPU 使用率告警**: 当 CPU 使用率超过阈值时
- ⚠️ **内存使用率告警**: 当内存使用率超过阈值时

告警会记录在日志文件中，可以通过以下命令查看：

```bash
# 查看所有告警
grep "⚠️" logs/webctp.log

# 查看特定类型的告警
grep "延迟告警" logs/webctp.log
grep "Redis 命中率告警" logs/webctp.log

# 使用日志标签过滤
grep "metrics_alert" logs/webctp.log
```

#### 性能报告

系统每分钟（可配置）自动生成性能报告，包含：

- 延迟统计（P50, P95, P99）
- 吞吐量统计
- Redis 命中率
- 系统资源使用情况

### 策略管理

系统支持多个交易策略并行运行，策略间相互隔离。

#### 配置策略管理

在配置文件中添加策略管理配置（可选）：

```yaml
# 策略管理配置（可选）
Strategy:
  MaxStrategies: 10                          # 最大策略数量
  DefaultMaxMemoryMB: 512                    # 默认单策略最大内存（MB）
  DefaultMaxCPUPercent: 50.0                 # 默认单策略最大CPU使用率（%）
```

#### 策略功能

- **策略注册**: 注册新的交易策略
- **策略控制**: 启动、停止策略
- **行情分发**: 自动将行情数据分发到所有订阅的策略
- **错误隔离**: 单个策略崩溃不影响其他策略
- **资源管理**: 限制单个策略的内存和 CPU 使用

#### 策略 WebSocket 接口

通过行情服务的 WebSocket 接口管理策略：

```json
// 注册策略
{
  "MsgType": "RegisterStrategy",
  "StrategyID": "my_strategy_1",
  "StrategyName": "我的策略",
  "SubscribedInstruments": ["au2602", "rb2605"]
}

// 启动策略
{
  "MsgType": "StartStrategy",
  "StrategyID": "my_strategy_1"
}

// 停止策略
{
  "MsgType": "StopStrategy",
  "StrategyID": "my_strategy_1"
}

// 查询策略状态
{
  "MsgType": "QueryStrategyStatus",
  "StrategyID": "my_strategy_1"
}
```

## 请求示例

> :pushpin: 见 [md_protocol.md](docs/md_protocol.md)、[td_protocol.md](docs/td_protocol.md)

### 部分示例

示例是基于 SimNow 电信1环境，不同环境的数据存在差异，以下示例数据未必可全部通过，根据环境调整即可。

行情连接地址：ws://127.0.0.1:8080/md/

交易连接地址：ws://127.0.0.1:8081/td/

<details>
<summary>登录</summary>

请求

```json
{
  "MsgType": "ReqUserLogin",
  "ReqUserLogin": {
    "UserID": "028742",
    "Password": "123456"
  }
}
```

应答

```json
{
    "MsgType": "RspUserLogin",
    "RspInfo": {
        "ErrorID": 0,
        "ErrorMsg": "CTP:No Error"
    },
    "IsLast": true,
    "RspUserLogin": {
        "BrokerID": "",
        "CZCETime": "",
        "DCETime": "",
        "FFEXTime": "",
        "FrontID": 0,
        "INETime": "",
        "LoginTime": "",
        "MaxOrderRef": "",
        "SessionID": 0,
        "SHFETime": "",
        "SystemName": "",
        "SysVersion": "",
        "TradingDay": "20251203",
        "UserID": ""
    }
}
```

</details>

<details>
<summary>订阅行情</summary>

请求

```json
{
  "MsgType": "SubscribeMarketData",
  "InstrumentID": [
    "au2602",
    "rb2605",
    "TA601"
  ]
}
```

应答

```json
{
    "MsgType": "RspSubMarketData",
    "RspInfo": {
        "ErrorID": 0,
        "ErrorMsg": "CTP:No Error"
    },
    "SpecificInstrument": {
        "InstrumentID": "au2602"
    }
}
```

```json
{
    "MsgType": "RspSubMarketData",
    "RspInfo": {
        "ErrorID": 0,
        "ErrorMsg": "CTP:No Error"
    },
    "SpecificInstrument": {
        "InstrumentID": "rb2605"
    }
}
```

```json
{
    "MsgType": "RspSubMarketData",
    "RspInfo": {
        "ErrorID": 0,
        "ErrorMsg": "CTP:No Error"
    },
    "IsLast": true,
    "SpecificInstrument": {
        "InstrumentID": "TA601"
    }
}
```

深度行情应答

```json
{
    "MsgType": "RtnDepthMarketData",
    "DepthMarketData": {
        "ActionDay": "20251203",
        "AskPrice1": 956.62,
        "AskPrice2": 0,
        "AskPrice3": 0,
        "AskPrice4": 0,
        "AskPrice5": 0,
        "AskVolume1": 3,
        "AskVolume2": 0,
        "AskVolume3": 0,
        "AskVolume4": 0,
        "AskVolume5": 0,
        "AveragePrice": 956858.858479762,
        "BandingLowerPrice": 0.0,
        "BandingUpperPrice": 0.0,
        "BidPrice1": 956.6,
        "BidPrice2": 0,
        "BidPrice3": 0,
        "BidPrice4": 0,
        "BidPrice5": 0,
        "BidVolume1": 9,
        "BidVolume2": 0,
        "BidVolume3": 0,
        "BidVolume4": 0,
        "BidVolume5": 0,
        "ClosePrice": 0,
        "CurrDelta": 1.7976931348623157e+308,
        "ExchangeID": "",
        "ExchangeInstID": "",
        "HighestPrice": 962.1800000000001,
        "InstrumentID": "au2602",
        "LastPrice": 956.62,
        "LowerLimitPrice": 827.32,
        "LowestPrice": 948.1800000000001,
        "OpenInterest": 199696.0,
        "OpenPrice": 958.0,
        "PreClosePrice": 958.42,
        "PreDelta": 0.0,
        "PreOpenInterest": 202038.0,
        "PreSettlementPrice": 962.02,
        "SettlementPrice": 0,
        "TradingDay": "20251203",
        "Turnover": 253162846200.0,
        "UpdateMillisec": 500,
        "UpdateTime": "13:41:23",
        "UpperLimitPrice": 1096.7,
        "Volume": 264577,
        "reserve1": "au2602",
        "reserve2": ""
    }
}
```

```json
{
    "MsgType": "RtnDepthMarketData",
    "DepthMarketData": {
        "ActionDay": "20251203",
        "AskPrice1": 3170.0,
        "AskPrice2": 0,
        "AskPrice3": 0,
        "AskPrice4": 0,
        "AskPrice5": 0,
        "AskVolume1": 261,
        "AskVolume2": 0,
        "AskVolume3": 0,
        "AskVolume4": 0,
        "AskVolume5": 0,
        "AveragePrice": 31645.592201667798,
        "BandingLowerPrice": 0.0,
        "BandingUpperPrice": 0.0,
        "BidPrice1": 3169.0,
        "BidPrice2": 0,
        "BidPrice3": 0,
        "BidPrice4": 0,
        "BidPrice5": 0,
        "BidVolume1": 624,
        "BidVolume2": 0,
        "BidVolume3": 0,
        "BidVolume4": 0,
        "BidVolume5": 0,
        "ClosePrice": 0,
        "CurrDelta": 1.7976931348623157e+308,
        "ExchangeID": "",
        "ExchangeInstID": "",
        "HighestPrice": 3174.0,
        "InstrumentID": "rb2605",
        "LastPrice": 3170.0,
        "LowerLimitPrice": 3010.0,
        "LowestPrice": 3154.0,
        "OpenInterest": 1288823.0,
        "OpenPrice": 3167.0,
        "PreClosePrice": 3169.0,
        "PreDelta": 0.0,
        "PreOpenInterest": 1175559.0,
        "PreSettlementPrice": 3169.0,
        "SettlementPrice": 0,
        "TradingDay": "20251203",
        "Turnover": 18507703080.0,
        "UpdateMillisec": 500,
        "UpdateTime": "13:41:23",
        "UpperLimitPrice": 3327.0,
        "Volume": 584843,
        "reserve1": "rb2605",
        "reserve2": ""
    }
}
```

```json
{
    "MsgType": "RtnDepthMarketData",
    "DepthMarketData": {
        "ActionDay": "20251203",
        "AskPrice1": 4734.0,
        "AskPrice2": 0.0,
        "AskPrice3": 0.0,
        "AskPrice4": 0.0,
        "AskPrice5": 0.0,
        "AskVolume1": 300,
        "AskVolume2": 0,
        "AskVolume3": 0,
        "AskVolume4": 0,
        "AskVolume5": 0,
        "AveragePrice": 4734.0,
        "BandingLowerPrice": 0.0,
        "BandingUpperPrice": 0.0,
        "BidPrice1": 4732.0,
        "BidPrice2": 0.0,
        "BidPrice3": 0.0,
        "BidPrice4": 0.0,
        "BidPrice5": 0.0,
        "BidVolume1": 282,
        "BidVolume2": 0,
        "BidVolume3": 0,
        "BidVolume4": 0,
        "BidVolume5": 0,
        "ClosePrice": 0,
        "CurrDelta": 1.7976931348623157e+308,
        "ExchangeID": "",
        "ExchangeInstID": "",
        "HighestPrice": 4754.0,
        "InstrumentID": "TA601",
        "LastPrice": 4734.0,
        "LowerLimitPrice": 4466.0,
        "LowestPrice": 4716.0,
        "OpenInterest": 885382.0,
        "OpenPrice": 4742.0,
        "PreClosePrice": 4752.0,
        "PreDelta": 0.0,
        "PreOpenInterest": 899833.0,
        "PreSettlementPrice": 4752.0,
        "SettlementPrice": 4736.0,
        "TradingDay": "20251203",
        "Turnover": 1930738230.0,
        "UpdateMillisec": 500,
        "UpdateTime": "13:41:23",
        "UpperLimitPrice": 5038.0,
        "Volume": 407845,
        "reserve1": "TA601",
        "reserve2": ""
    }
}
```

</details>

<details>
<summary>取消订阅行情</summary>

请求

```json
{
  "MsgType": "UnSubscribeMarketData",
  "InstrumentID": [
    "au2602",
    "rb2605",
    "TA601"
  ]
}
```

应答

```json
{
    "MsgType": "RspUnSubMarketData",
    "RspInfo": {
        "ErrorID": 0,
        "ErrorMsg": "CTP:No Error"
    },
    "SpecificInstrument": {
        "InstrumentID": "au2602"
    }
}
```

```json
{
    "MsgType": "RspUnSubMarketData",
    "RspInfo": {
        "ErrorID": 0,
        "ErrorMsg": "CTP:No Error"
    },
    "SpecificInstrument": {
        "InstrumentID": "rb2605"
    }
}
```

```json
{
    "MsgType": "RspUnSubMarketData",
    "RspInfo": {
        "ErrorID": 0,
        "ErrorMsg": "CTP:No Error"
    },
    "IsLast": true,
    "SpecificInstrument": {
        "InstrumentID": "TA601"
    }
}
```

</details>

## 协议

### 通用协议格式

```python
# 请求
{
  "MsgType": "{method_name}",
  "{request_field}": {
    "filed1": {value1},
    "...": "...",
    "fieldn": {valuen}
  },
  "RequestID": 1
}

# 响应
{
    "MsgType": "{rsp_of_method}",
    "RspInfo": {
        "ErrorID": 0,
        "ErrorMsg": "OK"
    },
    "IsLast": true,
    "RequestID": 1
    "{response_filed}": {response_body}  # 具体参见详细文档
}
```

### 详细接口文档部分通用错误码说明

<details>
<summary>👈</summary>

```bash
ErrorID="-400" ErrorMsg="参数有误"
ErrorID="-401" ErrorMsg="未登录"
ErrorID="-404" ErrorMsg="还未实现该方法"
ErrorID="-1" ErrorMsg="CTP:请求失败"
ErrorID="-2" ErrorMsg="CTP:未处理请求超过许可数"
ErrorID="-3" ErrorMsg="CTP:每秒发送请求数超过许可数"
ErrorID="0" ErrorMsg="CTP:正确"
ErrorID="1" ErrorMsg="CTP:不在已同步状态"
ErrorID="2" ErrorMsg="CTP:会话信息不一致"
ErrorID="3" ErrorMsg="CTP:不合法的登录"
ErrorID="4" ErrorMsg="CTP:用户不活跃"
ErrorID="5" ErrorMsg="CTP:重复的登录"
ErrorID="6" ErrorMsg="CTP:还没有登录"
ErrorID="7" ErrorMsg="CTP:还没有初始化"
ErrorID="8" ErrorMsg="CTP:前置不活跃"
ErrorID="9" ErrorMsg="CTP:无此权限"
ErrorID="10" ErrorMsg="CTP:修改别人的口令"
ErrorID="11" ErrorMsg="CTP:找不到该用户"
ErrorID="12" ErrorMsg="CTP:找不到该经纪公司"
ErrorID="13" ErrorMsg="CTP:找不到投资者"
ErrorID="14" ErrorMsg="CTP:原口令不匹配"
ErrorID="15" ErrorMsg="CTP:报单字段有误"
ErrorID="16" ErrorMsg="CTP:找不到合约"
```

</details>

### 详细接口文档

[交易服务协议文档](./docs/td_protocol.md)

[行情服务协议文档](./docs/md_protocol.md)

## 项目结构

```reStructuredText
homalos-webctp/
├── 📁 config/					# 项目配置
├── 📁 docs/					# 项目其它文档
├── 📁 libs/					# 第三方库，包括CTP原始动态库
├── 📁 src/						# 核心源代码
├── 📁 tests/					# 测试脚本
├── 📁 CHANGELOG.md				# 历史更新
├── 📁 LICENSE.txt				# License文件
├── 📁 README.md				# 项目英文文档
├── 📁 README_CN.md				# 项目中文文档
├── 📁 main.py					# 项目主入口
├── 📁 pyproject.toml			# 项目配置文件，依赖由UV管理
├── 📁 start_md_server.bat		# 行情服务启动脚本
├── 📁 start_td_server.bat		# 交易服务启动脚本
└── 📁 uv.lock					# UV文件锁，由UV管理
```

## 架构说明

### 三层架构

1. **应用层 (apps/)**: FastAPI WebSocket 端点
1. **服务层 (services/)**: 异步/同步边界处理，消息路由
1. **客户端层 (clients/)**: CTP API 封装

### 核心组件

- **BaseClient**: 抽象基类，提供公共的客户端管理逻辑
- **TdClient/MdClient (services)**: 处理 WebSocket 消息和 CTP 客户端的交互
- **TdClient/MdClient (clients)**: 封装 CTP API 调用

## 测试

建议在 SimNow 仿真环境中进行充分测试后再接入生产环境。

运行测试：

```bash
# 激活虚拟环境
.venv\Scripts\activate

# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_cache_manager.py
pytest tests/test_metrics.py
pytest tests/test_strategy_manager.py
```

更多详细信息请参考 [开发文档](./docs/development_CN.md)

## 文档

- [开发文档](./docs/development_CN.md) - 开发指南和架构说明
- [行情协议文档](./docs/md_protocol_CN.md) - 行情服务 WebSocket 协议
- [交易协议文档](./docs/td_protocol_CN.md) - 交易服务 WebSocket 协议
- [日志指南](./docs/logger_guide_CN.md) - 日志配置和使用
- [监控指南](./docs/monitoring_guide_CN.md) - 性能监控和告警配置
- [迁移指南](./docs/migration_guide_CN.md) - 从旧版本升级指南

## 其他说明

- 由于精力有限，只进行了 SimNow 平台的简单的测试，请自行充分测试后再接入生产环境。
- 进行实盘交易的后果完全有使用者自行承担。

______________________________________________________________________

## 性能优化成果

性能优化阶段 1 已完成，主要成果：

- ✅ **Redis 缓存集成**: 减少 CTP API 调用，提升查询性能
- ✅ **消息序列化优化**: 使用 orjson 和 msgpack，提升 20-30% 性能
- ✅ **多策略并行支持**: 支持最多 10 个策略同时运行
- ✅ **完整的性能监控**: 实时监控延迟、吞吐量、资源使用
- ✅ **智能告警系统**: 自动检测性能异常并发出告警

**性能目标**:

- 订单延迟 P95 \< 100ms
- 行情延迟 \< 50ms
- 吞吐量 > 20 单/秒

详细信息请参考 [性能优化报告](./PHASE1_CORE_COMPLETION_REPORT.md)

______________________________________________________________________

*最后更新日期：2025-12-20*
