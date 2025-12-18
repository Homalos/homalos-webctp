# SyncStrategyApi API 参考文档

## 概述

本文档提供 SyncStrategyApi 的完整 API 参考，包括所有类、方法、数据结构的详细说明。

## 目录

- [SyncStrategyApi 类](#syncstrategyapi-类)
- [数据类](#数据类)
  - [Quote 类](#quote-类)
  - [Position 类](#position-类)
- [异常](#异常)
- [配置](#配置)

---

## SyncStrategyApi 类

同步策略 API 主类，提供同步阻塞式的策略编写接口。

### 构造函数

```python
SyncStrategyApi(
    user_id: str,
    password: str,
    config_path: Optional[str] = None,
    timeout: Optional[float] = None
)
```

创建 SyncStrategyApi 实例并连接到 CTP 服务器。

**参数：**

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `user_id` | `str` | 是 | - | CTP 用户 ID |
| `password` | `str` | 是 | - | CTP 密码 |
| `config_path` | `Optional[str]` | 否 | `None` | 配置文件路径 |
| `timeout` | `Optional[float]` | 否 | `None` | CTP 连接超时时间（秒），None 表示使用配置文件中的默认值 |

**返回值：**
- `SyncStrategyApi` 实例

**异常：**
- `TimeoutError`：CTP 连接超时
- `RuntimeError`：初始化失败或登录失败

**示例：**

```python
# 使用默认配置
api = SyncStrategyApi("user_id", "password")

# 使用自定义配置文件
api = SyncStrategyApi("user_id", "password", config_path="config.yaml")

# 使用自定义超时时间
api = SyncStrategyApi("user_id", "password", timeout=60.0)
```

**说明：**
- 初始化时会自动执行以下操作：
  1. 加载配置文件（如果提供）
  2. 初始化内部数据结构
  3. 启动后台事件循环线程
  4. 创建 MdClient 和 TdClient 实例
  5. 自动执行 CTP 登录流程
  6. 等待连接就绪

---

### get_quote()

```python
get_quote(
    instrument_id: str,
    timeout: Optional[float] = None
) -> Quote
```

获取合约行情（同步阻塞）。

**参数：**

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `instrument_id` | `str` | 是 | - | 合约代码，如 "rb2505" |
| `timeout` | `Optional[float]` | 否 | `None` | 超时时间（秒），None 表示使用配置文件中的默认值 |

**返回值：**
- `Quote` 对象，包含最新行情数据

**异常：**
- `TimeoutError`：等待行情数据超时
- `RuntimeError`：订阅失败或服务不可用

**示例：**

```python
# 获取行情
quote = api.get_quote("rb2505")
print(f"最新价: {quote.LastPrice}")

# 使用自定义超时时间
quote = api.get_quote("rb2505", timeout=10.0)
```

**说明：**
- 如果合约未订阅，会自动订阅并等待首次行情数据
- 如果合约已订阅且缓存中有数据，直接返回缓存数据
- 返回的是行情数据的副本，避免并发修改

---

### wait_quote_update()

```python
wait_quote_update(
    instrument_id: str,
    timeout: Optional[float] = None
) -> Quote
```

等待行情更新（阻塞直到有新行情）。

**参数：**

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `instrument_id` | `str` | 是 | - | 合约代码 |
| `timeout` | `Optional[float]` | 否 | `None` | 超时时间（秒），None 表示使用配置文件中的默认值 |

**返回值：**
- `Quote` 对象，包含更新后的行情数据

**异常：**
- `TimeoutError`：等待超时
- `RuntimeError`：订阅失败或服务不可用

**示例：**

```python
# 等待行情更新
quote = api.wait_quote_update("rb2505", timeout=30.0)
print(f"收到新行情: {quote.LastPrice}")

# 在循环中使用
while True:
    quote = api.wait_quote_update("rb2505")
    print(f"价格: {quote.LastPrice}, 时间: {quote.UpdateTime}")
```

**说明：**
- 该方法会阻塞当前线程，直到指定合约有新的行情推送
- 如果合约未订阅，会自动订阅
- 返回的行情时间戳应该晚于调用前的行情时间戳

---

### get_position()

```python
get_position(
    instrument_id: str,
    timeout: Optional[float] = None
) -> Position
```

获取合约持仓（同步阻塞）。

**参数：**

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `instrument_id` | `str` | 是 | - | 合约代码 |
| `timeout` | `Optional[float]` | 否 | `None` | 超时时间（秒），None 表示使用配置文件中的默认值 |

**返回值：**
- `Position` 对象，包含多空持仓信息
- 如果查询超时或失败，返回空持仓对象（所有字段为默认值）

**异常：**
- 无（查询失败时返回空持仓对象，不抛出异常）

**示例：**

```python
# 获取持仓
position = api.get_position("rb2505")
print(f"多头持仓: {position.pos_long}")
print(f"空头持仓: {position.pos_short}")

# 检查是否有持仓
if position.pos_long > 0:
    print(f"多头均价: {position.open_price_long}")
```

**说明：**
- 如果持仓缓存不存在，会触发 CTP 查询并等待结果返回
- 如果持仓缓存已存在，直接返回缓存数据
- 与 `get_quote()` 不同，持仓查询超时时不会抛出异常
- 这是因为持仓为空是正常情况，不应该被视为错误
- 返回的是持仓数据的副本，避免并发修改

---

### open_close()

```python
open_close(
    instrument_id: str,
    action: str,
    volume: int,
    price: float,
    block: bool = True,
    timeout: Optional[float] = None
) -> dict
```

开平仓操作（同步阻塞）。

**参数：**

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `instrument_id` | `str` | 是 | - | 合约代码 |
| `action` | `str` | 是 | - | 交易动作："kaiduo", "kaikong", "pingduo", "pingkong" |
| `volume` | `int` | 是 | - | 下单数量（手） |
| `price` | `float` | 是 | - | 限价价格 |
| `block` | `bool` | 否 | `True` | 是否阻塞等待订单响应 |
| `timeout` | `Optional[float]` | 否 | `None` | 超时时间（秒），None 表示使用配置文件中的默认值 |

**交易动作说明：**

| action | 说明 | CTP Direction | CTP CombOffsetFlag |
|--------|------|---------------|-------------------|
| `"kaiduo"` | 开多（买入开仓） | 买(0) | 开仓(0) |
| `"kaikong"` | 开空（卖出开仓） | 卖(1) | 开仓(0) |
| `"pingduo"` | 平多（卖出平仓） | 卖(1) | 平仓(1) |
| `"pingkong"` | 平空（买入平仓） | 买(0) | 平仓(1) |

**返回值：**

订单结果字典，包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | `bool` | 订单是否成功提交 |
| `order_ref` | `str` | 订单引用（如果成功） |
| `error_id` | `int` | 错误代码（如果失败） |
| `error_msg` | `str` | 错误消息（如果失败） |
| `instrument_id` | `str` | 合约代码 |
| `action` | `str` | 交易动作 |
| `volume` | `int` | 下单数量 |
| `price` | `float` | 下单价格 |

**异常：**
- `TimeoutError`：等待订单响应超时（仅在 block=True 时）
- `ValueError`：参数错误（如 volume <= 0 或 price <= 0）
- `RuntimeError`：服务不可用

**示例：**

```python
# 开多仓（阻塞等待）
result = api.open_close("rb2505", "kaiduo", 1, 3500.0)
if result["success"]:
    print(f"订单成功: {result['order_ref']}")
else:
    print(f"订单失败: {result['error_msg']}")

# 开空仓（不阻塞）
result = api.open_close("rb2505", "kaikong", 1, 3500.0, block=False)
print("订单已提交")

# 平多仓
result = api.open_close("rb2505", "pingduo", 1, 3500.0)

# 平空仓
result = api.open_close("rb2505", "pingkong", 1, 3500.0)
```

**说明：**
- 当 `block=True` 时，方法会阻塞等待订单响应或超时
- 当 `block=False` 时，方法会立即返回，不等待订单响应
- 订单类型固定为限价单
- 时间条件固定为当日有效
- 成交量条件固定为任意数量

---

### run_strategy()

```python
run_strategy(
    strategy_func: Callable,
    *args,
    **kwargs
) -> threading.Thread
```

在独立线程中运行策略。

**参数：**

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `strategy_func` | `Callable` | 是 | - | 策略函数，可以是任何可调用对象 |
| `*args` | - | 否 | - | 传递给策略函数的位置参数 |
| `**kwargs` | - | 否 | - | 传递给策略函数的关键字参数 |

**返回值：**
- `threading.Thread` 对象，可用于外部管理（如 join()）

**异常：**
- `RuntimeError`：如果达到最大策略数量限制

**示例：**

```python
# 定义策略函数
def my_strategy(api, symbol, param1, param2=10):
    while True:
        quote = api.get_quote(symbol)
        print(f"价格: {quote.LastPrice}")
        time.sleep(1)

# 运行策略（传递位置参数）
thread = api.run_strategy(my_strategy, api, "rb2505", "value1")

# 运行策略（传递关键字参数）
thread = api.run_strategy(my_strategy, api, "rb2505", "value1", param2=20)

# 等待策略完成
thread.join()
```

**说明：**
- 策略函数在独立线程中运行，不会阻塞主线程
- 策略函数中的异常会被自动捕获并记录，不会影响其他策略
- 策略线程是守护线程，主程序退出时会自动结束
- 可以同时运行多个策略，每个策略在独立线程中运行
- 策略数量受配置文件中 `max_strategies` 参数限制

---

### get_running_strategies()

```python
get_running_strategies() -> Dict[str, threading.Thread]
```

获取当前运行中的策略列表。

**参数：**
- 无

**返回值：**
- 字典，键为策略名称，值为线程对象

**异常：**
- 无

**示例：**

```python
# 获取运行中的策略
strategies = api.get_running_strategies()

# 遍历策略
for name, thread in strategies.items():
    print(f"策略: {name}, 运行中: {thread.is_alive()}")

# 检查特定策略是否在运行
if "my_strategy" in strategies:
    print("my_strategy 正在运行")
```

**说明：**
- 返回的是策略注册表的副本，避免外部修改
- 策略名称是策略函数的 `__name__` 属性

---

### stop()

```python
stop(timeout: Optional[float] = None) -> None
```

停止所有策略和服务。

**参数：**

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `timeout` | `Optional[float]` | 否 | `None` | 等待策略线程停止的超时时间（秒），None 表示使用配置文件中的默认值 |

**返回值：**
- 无

**异常：**
- 可能抛出异常，但会记录日志

**示例：**

```python
# 停止服务（使用默认超时）
api.stop()

# 停止服务（使用自定义超时）
api.stop(timeout=10.0)

# 在 try-finally 中使用
try:
    # ... 运行策略 ...
    pass
finally:
    api.stop()
```

**说明：**
- 该方法会按顺序执行以下操作：
  1. 等待所有运行中的策略线程完成（设置超时）
  2. 停止异步事件循环
  3. 断开 CTP 连接并释放客户端对象
  4. 清理内部数据结构
- 程序退出前应该调用 `stop()` 方法清理资源
- 建议在 `try-finally` 块中使用，确保资源被正确释放

---

## 数据类

### Quote 类

行情快照数据类，包含合约的实时行情信息。

**字段：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `InstrumentID` | `str` | 合约代码 |
| `LastPrice` | `float` | 最新价 |
| `BidPrice1` | `float` | 买一价 |
| `BidVolume1` | `int` | 买一量 |
| `AskPrice1` | `float` | 卖一价 |
| `AskVolume1` | `int` | 卖一量 |
| `Volume` | `int` | 成交量 |
| `OpenInterest` | `float` | 持仓量 |
| `UpdateTime` | `str` | 更新时间（格式：HH:MM:SS） |
| `UpdateMillisec` | `int` | 更新毫秒 |
| `ctp_datetime` | `Any` | CTP 日期时间对象 |

**方法：**

```python
def __getitem__(self, key: str) -> Any
```

支持字典式访问。

**示例：**

```python
quote = api.get_quote("rb2505")

# 属性访问
print(f"最新价: {quote.LastPrice}")
print(f"买一价: {quote.BidPrice1}")
print(f"卖一价: {quote.AskPrice1}")

# 字典访问
print(f"最新价: {quote['LastPrice']}")
print(f"买一价: {quote['BidPrice1']}")
print(f"卖一价: {quote['AskPrice1']}")

# 检查价格是否有效
import math
if not math.isnan(quote.LastPrice):
    print(f"有效价格: {quote.LastPrice}")
```

**说明：**
- 无效价格使用 `float('nan')` 表示
- 支持属性访问和字典访问两种方式
- 从 API 返回的 Quote 对象是副本，避免并发修改

---

### Position 类

持仓信息数据类，包含合约的持仓详情。

**字段：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `pos_long` | `int` | 多头持仓总量 |
| `pos_long_today` | `int` | 多头今仓 |
| `pos_long_his` | `int` | 多头昨仓 |
| `open_price_long` | `float` | 多头开仓均价 |
| `pos_short` | `int` | 空头持仓总量 |
| `pos_short_today` | `int` | 空头今仓 |
| `pos_short_his` | `int` | 空头昨仓 |
| `open_price_short` | `float` | 空头开仓均价 |

**示例：**

```python
position = api.get_position("rb2505")

# 访问多头持仓
print(f"多头持仓: {position.pos_long}")
print(f"多头今仓: {position.pos_long_today}")
print(f"多头昨仓: {position.pos_long_his}")
print(f"多头均价: {position.open_price_long}")

# 访问空头持仓
print(f"空头持仓: {position.pos_short}")
print(f"空头今仓: {position.pos_short_today}")
print(f"空头昨仓: {position.pos_short_his}")
print(f"空头均价: {position.open_price_short}")

# 检查是否有持仓
if position.pos_long > 0:
    print("有多头持仓")
if position.pos_short > 0:
    print("有空头持仓")

# 检查均价是否有效
import math
if not math.isnan(position.open_price_long):
    print(f"多头均价: {position.open_price_long}")
```

**说明：**
- 无效价格使用 `float('nan')` 表示
- 持仓总量 = 今仓 + 昨仓
- 从 API 返回的 Position 对象是副本，避免并发修改
- 如果查询失败或超时，返回空持仓对象（所有字段为默认值）

---

## 异常

### TimeoutError

等待超时时抛出。

**使用场景：**
- `get_quote()` 等待行情数据超时
- `wait_quote_update()` 等待行情更新超时
- `open_close()` 等待订单响应超时（仅在 block=True 时）
- `SyncStrategyApi.__init__()` CTP 连接超时

**示例：**

```python
try:
    quote = api.get_quote("rb2505", timeout=5.0)
except TimeoutError as e:
    print(f"获取行情超时: {e}")
```

---

### RuntimeError

运行时错误，通常表示系统状态异常。

**使用场景：**
- `SyncStrategyApi.__init__()` 初始化失败或登录失败
- `get_quote()` 订阅失败或服务不可用
- `wait_quote_update()` 订阅失败或服务不可用
- `open_close()` 服务不可用
- `run_strategy()` 达到最大策略数量限制

**示例：**

```python
try:
    api = SyncStrategyApi("user_id", "password")
except RuntimeError as e:
    print(f"初始化失败: {e}")
```

---

### ValueError

参数错误。

**使用场景：**
- `open_close()` 参数错误（如 volume <= 0 或 price <= 0）
- `open_close()` 不支持的 action 参数

**示例：**

```python
try:
    result = api.open_close("rb2505", "invalid_action", 1, 3500.0)
except ValueError as e:
    print(f"参数错误: {e}")
```

---

## 配置

SyncStrategyApi 支持通过配置文件自定义参数。配置文件格式为 YAML。

### 配置文件示例

```yaml
# config/config.yaml

# 同步策略 API 配置
sync_api:
  connect_timeout: 30.0        # CTP 连接超时时间（秒）
  quote_timeout: 10.0          # 行情查询超时时间（秒）
  quote_update_timeout: 30.0   # 行情更新等待超时时间（秒）
  position_timeout: 10.0       # 持仓查询超时时间（秒）
  order_timeout: 10.0          # 订单提交超时时间（秒）
  stop_timeout: 5.0            # 停止服务超时时间（秒）
  max_strategies: 10           # 最大策略数量
```

### 配置项说明

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `connect_timeout` | `float` | `30.0` | CTP 连接超时时间（秒） |
| `quote_timeout` | `float` | `10.0` | 行情查询超时时间（秒） |
| `quote_update_timeout` | `float` | `30.0` | 行情更新等待超时时间（秒） |
| `position_timeout` | `float` | `10.0` | 持仓查询超时时间（秒） |
| `order_timeout` | `float` | `10.0` | 订单提交超时时间（秒） |
| `stop_timeout` | `float` | `5.0` | 停止服务超时时间（秒） |
| `max_strategies` | `int` | `10` | 最大策略数量 |

### 使用配置文件

```python
# 使用配置文件
api = SyncStrategyApi(
    user_id="user_id",
    password="password",
    config_path="./config/config.yaml"
)

# 不使用配置文件（使用默认值）
api = SyncStrategyApi(
    user_id="user_id",
    password="password"
)
```

### 配置优先级

1. 方法参数（如 `timeout` 参数）
2. 配置文件中的值
3. 默认值

**示例：**

```python
# 配置文件中 quote_timeout = 10.0

# 使用配置文件中的值（10.0 秒）
quote = api.get_quote("rb2505")

# 使用方法参数覆盖配置文件中的值（5.0 秒）
quote = api.get_quote("rb2505", timeout=5.0)
```

---

## 线程安全

SyncStrategyApi 是线程安全的，可以在多个线程中同时调用 API 方法。

**内部机制：**
- 使用 `threading.RLock` 保护共享数据结构
- 使用 `queue.Queue` 实现行情更新通知
- 使用 `asyncio.run_coroutine_threadsafe()` 安全调用异步方法

**示例：**

```python
import threading

def thread1_func():
    while True:
        quote = api.get_quote("rb2505")
        print(f"线程1: {quote.LastPrice}")
        time.sleep(1)

def thread2_func():
    while True:
        position = api.get_position("rb2505")
        print(f"线程2: 多头={position.pos_long}, 空头={position.pos_short}")
        time.sleep(1)

# 创建线程
t1 = threading.Thread(target=thread1_func)
t2 = threading.Thread(target=thread2_func)

# 启动线程
t1.start()
t2.start()

# 等待线程
t1.join()
t2.join()
```

---

## 性能考虑

### 行情缓存

- `get_quote()` 会缓存行情数据，重复调用不会触发重复订阅
- 缓存的行情数据会自动更新（通过 CTP 推送）
- 返回的是行情数据的副本，避免并发修改

### 持仓缓存

- `get_position()` 会缓存持仓数据，重复调用不会触发重复查询
- 缓存的持仓数据会在成交回报时自动更新
- 返回的是持仓数据的副本，避免并发修改

### 订阅管理

- 每个合约只会订阅一次，重复调用 `get_quote()` 不会重复订阅
- 订阅状态在内部维护，无需手动管理

### 策略线程

- 每个策略在独立线程中运行，不会相互阻塞
- 策略数量受配置文件中 `max_strategies` 参数限制
- 策略线程是守护线程，主程序退出时会自动结束

---

## 相关文档

- [快速开始指南](sync_api_quick_start_CN.md)
- [常见问题和最佳实践](sync_api_faq_CN.md)
- [示例代码](../examples/sync_strategy_example.py)

---

## 版本信息

- 当前版本：1.0.0
- 最后更新：2025-12-17
