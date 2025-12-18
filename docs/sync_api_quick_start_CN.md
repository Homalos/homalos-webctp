# SyncStrategyApi 快速开始指南

## 简介

SyncStrategyApi 是 homalos-webctp 项目提供的同步策略 API，为量化策略开发者提供简单易用的同步阻塞式接口。通过这个 API，您可以使用类似 PeopleQuant 的编程风格编写策略，无需理解复杂的异步编程概念。

### 核心特性

- **同步阻塞式 API**：使用简单的函数调用获取行情、查询持仓、执行交易
- **自动连接管理**：自动处理 CTP 连接、登录、重连等底层细节
- **多策略并发**：支持同时运行多个策略，每个策略在独立线程中运行
- **线程安全**：内部使用锁和队列机制确保数据一致性
- **异常隔离**：单个策略的异常不会影响其他策略运行

### 适用场景

- 量化策略开发和回测
- 期货自动交易系统
- 行情监控和分析工具
- 多策略组合管理

## 环境准备

### 1. 安装依赖

确保已安装 Python 3.13 和 UV 包管理器：

```bash
# 安装 UV（Windows）
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 通过 UV 安装 Python 3.13
uv python install 3.13

# 安装项目依赖
uv sync
```

### 2. 激活虚拟环境

在运行任何代码之前，需要激活虚拟环境：

```bash
# Windows CMD
.venv\Scripts\activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

### 3. 准备配置文件

复制示例配置文件并修改：

```bash
copy config\config.sample.yaml config\config.yaml
```

编辑 `config/config.yaml`，配置 CTP 服务器地址和认证信息。

## 第一个策略

### 最简单的示例

以下是一个最简单的示例，展示如何获取行情数据：

```python
from src.strategy.sync_api import SyncStrategyApi

# 创建 API 实例并连接
api = SyncStrategyApi(
    user_id="你的用户ID",
    password="你的密码",
    config_path="./config/config.yaml",
    timeout=30.0  # 连接超时时间
)

try:
    # 获取行情
    quote = api.get_quote("rb2505")
    print(f"合约: {quote.InstrumentID}")
    print(f"最新价: {quote.LastPrice}")
    print(f"买一价: {quote.BidPrice1}")
    print(f"卖一价: {quote.AskPrice1}")
    
finally:
    # 停止服务
    api.stop()
```

### 完整的策略示例

以下是一个简单的双均线策略：

```python
import time
from src.strategy.sync_api import SyncStrategyApi

def dual_ma_strategy(api, symbol, fast_period=5, slow_period=20):
    """双均线策略"""
    price_history = []
    
    while True:
        # 获取最新行情
        quote = api.get_quote(symbol)
        
        # 添加到历史价格
        price_history.append(quote.LastPrice)
        if len(price_history) > slow_period:
            price_history.pop(0)
        
        # 等待足够的数据
        if len(price_history) < slow_period:
            time.sleep(1)
            continue
        
        # 计算均线
        fast_ma = sum(price_history[-fast_period:]) / fast_period
        slow_ma = sum(price_history[-slow_period:]) / slow_period
        
        print(f"价格: {quote.LastPrice:.2f}, 快线: {fast_ma:.2f}, 慢线: {slow_ma:.2f}")
        
        # 获取当前持仓
        position = api.get_position(symbol)
        
        # 交易逻辑
        if fast_ma > slow_ma and position.pos_long == 0:
            # 快线上穿慢线，开多
            print("信号: 开多")
            result = api.open_close(symbol, "kaiduo", 1, quote.AskPrice1)
            if result["success"]:
                print(f"开多成功: {result['order_ref']}")
        
        elif fast_ma < slow_ma and position.pos_short == 0:
            # 快线下穿慢线，开空
            print("信号: 开空")
            result = api.open_close(symbol, "kaikong", 1, quote.BidPrice1)
            if result["success"]:
                print(f"开空成功: {result['order_ref']}")
        
        time.sleep(1)

# 主程序
if __name__ == "__main__":
    api = SyncStrategyApi(
        user_id="你的用户ID",
        password="你的密码",
        config_path="./config/config.yaml"
    )
    
    try:
        # 运行策略
        dual_ma_strategy(api, "rb2505")
    except KeyboardInterrupt:
        print("策略被用户中断")
    finally:
        api.stop()
```

## 核心 API 使用

### 1. 初始化 API

```python
api = SyncStrategyApi(
    user_id="你的用户ID",      # 必需：CTP 用户 ID
    password="你的密码",        # 必需：CTP 密码
    config_path="config.yaml",  # 可选：配置文件路径
    timeout=30.0                # 可选：连接超时时间（秒）
)
```

**参数说明：**
- `user_id`：CTP 用户 ID（必需）
- `password`：CTP 密码（必需）
- `config_path`：配置文件路径（可选，不提供则使用默认配置）
- `timeout`：CTP 连接超时时间（可选，默认使用配置文件中的值）

**注意事项：**
- 初始化时会自动连接 CTP 服务器并登录
- 如果连接超时，会抛出 `TimeoutError` 异常
- 如果登录失败，会抛出 `RuntimeError` 异常

### 2. 获取行情

```python
# 获取行情（如果未订阅会自动订阅）
quote = api.get_quote("rb2505", timeout=10.0)

# 访问行情数据（属性访问）
print(f"最新价: {quote.LastPrice}")
print(f"买一价: {quote.BidPrice1}")
print(f"卖一价: {quote.AskPrice1}")
print(f"成交量: {quote.Volume}")

# 也支持字典访问
print(f"最新价: {quote['LastPrice']}")
```

**参数说明：**
- `instrument_id`：合约代码（必需）
- `timeout`：超时时间（可选，默认使用配置文件中的值）

**返回值：**
- `Quote` 对象，包含行情数据

**异常：**
- `TimeoutError`：等待行情数据超时
- `RuntimeError`：订阅失败或服务不可用

### 3. 等待行情更新

```python
# 阻塞等待行情更新
quote = api.wait_quote_update("rb2505", timeout=30.0)
print(f"收到新行情: {quote.LastPrice}")
```

**参数说明：**
- `instrument_id`：合约代码（必需）
- `timeout`：超时时间（可选，默认使用配置文件中的值）

**返回值：**
- `Quote` 对象，包含更新后的行情数据

**异常：**
- `TimeoutError`：等待超时
- `RuntimeError`：订阅失败或服务不可用

**使用场景：**
- 实时监控行情变化
- 等待特定价格触发交易信号

### 4. 获取持仓

```python
# 获取持仓信息
position = api.get_position("rb2505")

# 访问持仓数据
print(f"多头持仓: {position.pos_long}")
print(f"多头今仓: {position.pos_long_today}")
print(f"多头昨仓: {position.pos_long_his}")
print(f"多头均价: {position.open_price_long}")

print(f"空头持仓: {position.pos_short}")
print(f"空头今仓: {position.pos_short_today}")
print(f"空头昨仓: {position.pos_short_his}")
print(f"空头均价: {position.open_price_short}")
```

**参数说明：**
- `instrument_id`：合约代码（必需）
- `timeout`：超时时间（可选，默认使用配置文件中的值）

**返回值：**
- `Position` 对象，包含持仓信息
- 如果查询超时或失败，返回空持仓对象（所有字段为默认值）

**注意事项：**
- 与 `get_quote()` 不同，持仓查询超时时不会抛出异常，而是返回空持仓对象
- 这是因为持仓为空是正常情况，不应该被视为错误

### 5. 开平仓操作

```python
# 开多仓
result = api.open_close(
    "rb2505",           # 合约代码
    "kaiduo",           # 动作：kaiduo, kaikong, pingduo, pingkong
    1,                  # 数量
    3500.0,             # 价格
    block=True,         # 是否阻塞等待成交
    timeout=10.0        # 超时时间
)

# 检查结果
if result["success"]:
    print(f"订单成功: {result['order_ref']}")
else:
    print(f"订单失败: {result['error_msg']}")
```

**参数说明：**
- `instrument_id`：合约代码（必需）
- `action`：交易动作（必需），支持以下值：
  - `"kaiduo"`：开多（买入开仓）
  - `"kaikong"`：开空（卖出开仓）
  - `"pingduo"`：平多（卖出平仓）
  - `"pingkong"`：平空（买入平仓）
- `volume`：下单数量（必需，手）
- `price`：限价价格（必需）
- `block`：是否阻塞等待订单响应（可选，默认 True）
- `timeout`：超时时间（可选，默认使用配置文件中的值）

**返回值：**
- 订单结果字典，包含以下字段：
  - `success`：bool - 订单是否成功提交
  - `order_ref`：str - 订单引用（如果成功）
  - `error_id`：int - 错误代码（如果失败）
  - `error_msg`：str - 错误消息（如果失败）
  - `instrument_id`：str - 合约代码
  - `action`：str - 交易动作
  - `volume`：int - 下单数量
  - `price`：float - 下单价格

**异常：**
- `TimeoutError`：等待订单响应超时（仅在 block=True 时）
- `ValueError`：参数错误
- `RuntimeError`：服务不可用

### 6. 运行策略

```python
# 定义策略函数
def my_strategy(api, symbol):
    while True:
        quote = api.get_quote(symbol)
        print(f"价格: {quote.LastPrice}")
        time.sleep(1)

# 在独立线程中运行策略
thread = api.run_strategy(my_strategy, api, "rb2505")

# 等待策略完成（可选）
thread.join()
```

**参数说明：**
- `strategy_func`：策略函数（必需）
- `*args`：传递给策略函数的位置参数
- `**kwargs`：传递给策略函数的关键字参数

**返回值：**
- `threading.Thread` 对象，可用于外部管理

**注意事项：**
- 策略函数中的异常会被自动捕获并记录，不会影响其他策略
- 策略线程是守护线程，主程序退出时会自动结束
- 可以同时运行多个策略，每个策略在独立线程中运行

### 7. 停止服务

```python
# 停止所有策略和服务
api.stop()
```

**参数说明：**
- `timeout`：等待策略线程停止的超时时间（可选，默认使用配置文件中的值）

**执行步骤：**
1. 等待所有运行中的策略线程完成
2. 停止异步事件循环
3. 断开 CTP 连接并释放资源
4. 清理内部数据结构

**注意事项：**
- 程序退出前应该调用 `stop()` 方法清理资源
- 建议在 `try-finally` 块中使用，确保资源被正确释放

## 多策略并发运行

SyncStrategyApi 支持同时运行多个策略，每个策略在独立线程中运行：

```python
from src.strategy.sync_api import SyncStrategyApi
import time

def strategy1(api, symbol):
    """策略 1：双均线策略"""
    # ... 策略逻辑 ...
    pass

def strategy2(api, symbol):
    """策略 2：行情监控"""
    while True:
        quote = api.get_quote(symbol)
        print(f"[监控] {symbol}: {quote.LastPrice}")
        time.sleep(1)

def strategy3(api, symbol):
    """策略 3：持仓监控"""
    while True:
        position = api.get_position(symbol)
        print(f"[持仓] 多头: {position.pos_long}, 空头: {position.pos_short}")
        time.sleep(5)

# 主程序
if __name__ == "__main__":
    api = SyncStrategyApi(
        user_id="你的用户ID",
        password="你的密码"
    )
    
    try:
        # 启动多个策略
        thread1 = api.run_strategy(strategy1, api, "rb2505")
        thread2 = api.run_strategy(strategy2, api, "rb2505")
        thread3 = api.run_strategy(strategy3, api, "rb2505")
        
        print("所有策略已启动，按 Ctrl+C 停止...")
        
        # 等待所有策略
        thread1.join()
        thread2.join()
        thread3.join()
        
    except KeyboardInterrupt:
        print("收到停止信号...")
    finally:
        api.stop()
```

## 配置文件

SyncStrategyApi 支持通过配置文件自定义参数：

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

**配置项说明：**
- `connect_timeout`：CTP 连接超时时间
- `quote_timeout`：行情查询超时时间
- `quote_update_timeout`：行情更新等待超时时间
- `position_timeout`：持仓查询超时时间
- `order_timeout`：订单提交超时时间
- `stop_timeout`：停止服务超时时间
- `max_strategies`：最大策略数量限制

## 下一步

- 查看 [API 参考文档](sync_api_reference_CN.md) 了解完整的 API 说明
- 查看 [常见问题和最佳实践](sync_api_faq_CN.md) 了解使用技巧
- 查看 `examples/sync_strategy_example.py` 了解更多示例

## 技术支持

如有问题，请查看项目文档或提交 Issue。
