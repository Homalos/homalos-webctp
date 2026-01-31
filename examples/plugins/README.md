# SyncStrategyApi 插件开发指南

本文档提供 SyncStrategyApi 插件系统的完整开发指南，包括插件架构、开发流程、最佳实践和示例代码。

## 目录

- [插件系统概述](#%E6%8F%92%E4%BB%B6%E7%B3%BB%E7%BB%9F%E6%A6%82%E8%BF%B0)
- [插件架构](#%E6%8F%92%E4%BB%B6%E6%9E%B6%E6%9E%84)
- [快速开始](#%E5%BF%AB%E9%80%9F%E5%BC%80%E5%A7%8B)
- [插件开发教程](#%E6%8F%92%E4%BB%B6%E5%BC%80%E5%8F%91%E6%95%99%E7%A8%8B)
- [示例插件](#%E7%A4%BA%E4%BE%8B%E6%8F%92%E4%BB%B6)
- [高级主题](#%E9%AB%98%E7%BA%A7%E4%B8%BB%E9%A2%98)
- [最佳实践](#%E6%9C%80%E4%BD%B3%E5%AE%9E%E8%B7%B5)
- [常见问题](#%E5%B8%B8%E8%A7%81%E9%97%AE%E9%A2%98)
- [故障排查](#%E6%95%85%E9%9A%9C%E6%8E%92%E6%9F%A5)

## 插件系统概述

插件系统允许你在不修改核心代码的情况下扩展 SyncStrategyApi 的功能。插件基于钩子（Hook）机制，在特定事件发生时执行自定义逻辑。

### 为什么使用插件？

1. **代码解耦**: 将特定功能从核心代码中分离，提高可维护性
1. **灵活扩展**: 在不修改核心代码的情况下添加新功能
1. **动态配置**: 可以动态注册和注销插件，支持热插拔
1. **功能组合**: 多个插件可以链式调用，实现复杂的数据处理流程

### 适用场景

插件系统适合以下场景：

- **行情数据预处理**: 过滤异常数据、数据转换、数据增强
- **交易信号生成**: 基于行情数据生成交易信号
- **风险控制**: 实时监控持仓、价格变动、交易频率等
- **日志记录**: 记录行情、交易、订单等数据
- **性能统计**: 统计策略性能指标
- **数据存储**: 将数据保存到数据库或文件
- **监控告警**: 监控异常情况并发送告警

## 插件架构

### StrategyPlugin 抽象基类

所有插件必须继承自 `StrategyPlugin` 抽象基类。这个基类定义了插件的生命周期和钩子方法。

```python
from src.strategy.sync_api import StrategyPlugin, Quote

class MyPlugin(StrategyPlugin):
    def on_init(self, api):
        """插件初始化钩子 - 必须实现"""
        pass
    
    def on_quote(self, quote: Quote) -> Quote:
        """行情数据钩子 - 可选实现"""
        return quote
    
    def on_trade(self, trade_data: dict) -> dict:
        """交易数据钩子 - 可选实现"""
        return trade_data
    
    def on_stop(self):
        """插件停止钩子 - 可选实现"""
        pass
```

### 插件生命周期

插件的生命周期包括以下阶段：

1. **创建阶段**: 实例化插件对象
1. **注册阶段**: 调用 `api.register_plugin(plugin)`，触发 `on_init()`
1. **运行阶段**: 在行情和交易事件发生时调用 `on_quote()` 和 `on_trade()`
1. **停止阶段**: 调用 `api.stop()` 或 `api.unregister_plugin(plugin)`，触发 `on_stop()`

```
创建 -> 注册(on_init) -> 运行(on_quote/on_trade) -> 停止(on_stop)
```

### 钩子方法详解

#### 1. on_init(api)

**调用时机**: 插件注册时

**参数**:

- `api`: SyncStrategyApi 实例，可以调用所有公共方法

**返回**: 无

**用途**:

- 保存 API 引用以便后续使用
- 初始化插件状态（计数器、缓存等）
- 加载配置文件
- 创建数据库连接
- 初始化日志记录器

**示例**:

```python
def on_init(self, api):
    self.api = api
    self.quote_count = 0
    self.last_prices = {}
    logger.info("插件初始化完成")
```

#### 2. on_quote(quote)

**调用时机**: 每次收到行情推送时

**参数**:

- `quote`: Quote 对象，包含最新行情数据

**返回**:

- Quote 对象: 处理后的行情数据（可以是原始数据或修改后的数据）
- None: 过滤该行情，不会传递给后续插件和缓存

**用途**:

- 行情数据验证和过滤
- 数据转换和增强
- 异常数据检测
- 行情数据记录
- 生成交易信号

**示例**:

```python
def on_quote(self, quote: Quote) -> Quote:
    # 过滤无效价格
    if math.isnan(quote.LastPrice) or quote.LastPrice <= 0:
        logger.warning(f"过滤无效行情: {quote.InstrumentID}")
        return None
    
    # 记录行情
    logger.info(f"行情: {quote.InstrumentID} @ {quote.LastPrice}")
    
    # 返回原始数据
    return quote
```

#### 3. on_trade(trade_data)

**调用时机**: 每次收到交易数据回调时（订单回报、成交回报等）

**参数**:

- `trade_data`: 字典，包含交易数据（订单、成交、持仓等）

**返回**:

- dict: 处理后的交易数据
- None: 过滤该数据，不会传递给后续插件

**用途**:

- 交易数据验证
- 风险控制检查
- 交易数据记录
- 持仓监控
- 订单状态跟踪

**示例**:

```python
def on_trade(self, trade_data: dict) -> dict:
    msg_type = trade_data.get('MsgType', '')
    
    # 处理成交回报
    if 'RtnTrade' in msg_type:
        trade = trade_data.get('Trade', {})
        instrument_id = trade.get('InstrumentID')
        volume = trade.get('Volume', 0)
        logger.info(f"成交: {instrument_id}, 数量: {volume}")
    
    return trade_data
```

#### 4. on_stop()

**调用时机**: API 停止或插件注销时

**参数**: 无

**返回**: 无

**用途**:

- 关闭文件句柄
- 保存数据到磁盘
- 关闭数据库连接
- 释放其他资源
- 记录统计信息

**示例**:

```python
def on_stop(self):
    # 保存统计数据
    logger.info(f"插件停止，共处理 {self.quote_count} 条行情")
    
    # 关闭文件
    if hasattr(self, 'log_file'):
        self.log_file.close()
```

### 插件链式调用

多个插件按注册顺序依次调用，形成插件链：

```
原始数据 -> 插件1 -> 插件2 -> 插件3 -> 缓存/核心逻辑
```

**规则**:

1. 前一个插件的输出是下一个插件的输入
1. 如果任何插件返回 None，链中断，后续插件不会被调用
1. 插件异常会被捕获，不影响其他插件和核心功能

**示例**:

```python
# 注册插件链
api.register_plugin(ValidationPlugin())  # 验证数据
api.register_plugin(FilterPlugin())      # 过滤异常数据
api.register_plugin(LoggingPlugin())     # 记录数据

# 数据流:
# 原始行情 -> 验证 -> 过滤 -> 记录 -> 缓存
```

## 快速开始

### 5分钟创建你的第一个插件

#### 步骤 1: 创建插件类

创建文件 `my_first_plugin.py`:

```python
from src.strategy.sync_api import StrategyPlugin, Quote
from loguru import logger

class MyFirstPlugin(StrategyPlugin):
    def on_init(self, api):
        """初始化插件"""
        self.api = api
        self.quote_count = 0
        logger.info("我的第一个插件已初始化")
    
    def on_quote(self, quote: Quote) -> Quote:
        """处理行情数据"""
        self.quote_count += 1
        logger.info(f"收到第 {self.quote_count} 条行情: {quote.InstrumentID} @ {quote.LastPrice}")
        return quote
    
    def on_stop(self):
        """清理资源"""
        logger.info(f"插件停止，共处理 {self.quote_count} 条行情")
```

#### 步骤 2: 使用插件

```python
from src.strategy.sync_api import SyncStrategyApi
from my_first_plugin import MyFirstPlugin

# 创建 API 实例
api = SyncStrategyApi(
    user_id="your_user_id",
    password="your_password",
    config_path="./config/config_td.yaml"
)

# 注册插件
plugin = MyFirstPlugin()
api.register_plugin(plugin)

# 订阅行情
quote = api.get_quote("rb2605")

# 停止 API（会自动停止插件）
api.stop()
```

#### 步骤 3: 运行并查看结果

```bash
python your_strategy.py
```

你会看到类似的输出：

```
[INFO] 我的第一个插件已初始化
[INFO] 收到第 1 条行情: rb2605 @ 3500.0
[INFO] 收到第 2 条行情: rb2605 @ 3501.0
[INFO] 插件停止，共处理 2 条行情
```

恭喜！你已经创建了第一个插件。

## 插件开发教程

### 教程 1: 创建价格过滤插件

**目标**: 过滤掉价格异常的行情数据

```python
import math
from src.strategy.sync_api import StrategyPlugin, Quote
from loguru import logger

class PriceFilterPlugin(StrategyPlugin):
    def __init__(self, min_price=0, max_price=float('inf')):
        """
        初始化价格过滤插件
        
        Args:
            min_price: 最小有效价格
            max_price: 最大有效价格
        """
        self.min_price = min_price
        self.max_price = max_price
        self.filtered_count = 0
    
    def on_init(self, api):
        self.api = api
        logger.info(f"价格过滤插件已初始化: {self.min_price} - {self.max_price}")
    
    def on_quote(self, quote: Quote) -> Quote:
        # 检查价格是否有效
        if math.isnan(quote.LastPrice):
            logger.warning(f"过滤无效价格(NaN): {quote.InstrumentID}")
            self.filtered_count += 1
            return None
        
        # 检查价格范围
        if quote.LastPrice < self.min_price or quote.LastPrice > self.max_price:
            logger.warning(
                f"过滤异常价格: {quote.InstrumentID} @ {quote.LastPrice} "
                f"(范围: {self.min_price} - {self.max_price})"
            )
            self.filtered_count += 1
            return None
        
        return quote
    
    def on_stop(self):
        logger.info(f"价格过滤插件停止，共过滤 {self.filtered_count} 条异常行情")
```

**使用示例**:

```python
# 只接受价格在 3000-4000 之间的行情
plugin = PriceFilterPlugin(min_price=3000, max_price=4000)
api.register_plugin(plugin)
```

### 教程 2: 创建持仓监控插件

**目标**: 实时监控持仓变化并记录

```python
from src.strategy.sync_api import StrategyPlugin
from loguru import logger

class PositionMonitorPlugin(StrategyPlugin):
    def __init__(self):
        self.positions = {}  # 持仓缓存
    
    def on_init(self, api):
        self.api = api
        logger.info("持仓监控插件已初始化")
    
    def on_trade(self, trade_data: dict) -> dict:
        msg_type = trade_data.get('MsgType', '')
        
        # 监控成交回报
        if 'RtnTrade' in msg_type:
            trade = trade_data.get('Trade', {})
            instrument_id = trade.get('InstrumentID')
            direction = trade.get('Direction')  # '0'=买, '1'=卖
            volume = trade.get('Volume', 0)
            price = trade.get('Price', 0)
            
            # 更新持仓记录
            if instrument_id not in self.positions:
                self.positions[instrument_id] = {'long': 0, 'short': 0}
            
            if direction == '0':  # 买入
                self.positions[instrument_id]['long'] += volume
            elif direction == '1':  # 卖出
                self.positions[instrument_id]['short'] += volume
            
            # 记录持仓变化
            logger.info(
                f"持仓变化: {instrument_id}, "
                f"方向: {'买入' if direction == '0' else '卖出'}, "
                f"数量: {volume}, 价格: {price}, "
                f"当前持仓: 多{self.positions[instrument_id]['long']} "
                f"空{self.positions[instrument_id]['short']}"
            )
        
        return trade_data
    
    def on_stop(self):
        logger.info("持仓监控插件停止")
        logger.info(f"最终持仓: {self.positions}")
```

### 教程 3: 创建数据记录插件

**目标**: 将行情数据保存到 CSV 文件

```python
import csv
from datetime import datetime
from src.strategy.sync_api import StrategyPlugin, Quote
from loguru import logger

class DataRecorderPlugin(StrategyPlugin):
    def __init__(self, output_file="quotes.csv"):
        self.output_file = output_file
        self.csv_file = None
        self.csv_writer = None
    
    def on_init(self, api):
        self.api = api
        
        # 打开 CSV 文件
        self.csv_file = open(self.output_file, 'w', newline='', encoding='utf-8')
        self.csv_writer = csv.writer(self.csv_file)
        
        # 写入表头
        self.csv_writer.writerow([
            'Timestamp', 'InstrumentID', 'LastPrice', 
            'BidPrice1', 'AskPrice1', 'Volume'
        ])
        
        logger.info(f"数据记录插件已初始化，输出文件: {self.output_file}")
    
    def on_quote(self, quote: Quote) -> Quote:
        # 记录行情数据
        self.csv_writer.writerow([
            datetime.now().isoformat(),
            quote.InstrumentID,
            quote.LastPrice,
            quote.BidPrice1,
            quote.AskPrice1,
            quote.Volume
        ])
        
        # 立即刷新到磁盘
        self.csv_file.flush()
        
        return quote
    
    def on_stop(self):
        # 关闭文件
        if self.csv_file:
            self.csv_file.close()
        logger.info("数据记录插件停止")
```

### 教程 4: 创建交易信号插件

**目标**: 基于简单的均线策略生成交易信号

```python
from collections import deque
from src.strategy.sync_api import StrategyPlugin, Quote
from loguru import logger

class MovingAverageSignalPlugin(StrategyPlugin):
    def __init__(self, period=5):
        """
        移动平均线信号插件
        
        Args:
            period: 均线周期
        """
        self.period = period
        self.prices = {}  # 价格队列
    
    def on_init(self, api):
        self.api = api
        logger.info(f"移动平均线信号插件已初始化，周期: {self.period}")
    
    def on_quote(self, quote: Quote) -> Quote:
        instrument_id = quote.InstrumentID
        price = quote.LastPrice
        
        # 初始化价格队列
        if instrument_id not in self.prices:
            self.prices[instrument_id] = deque(maxlen=self.period)
        
        # 添加新价格
        self.prices[instrument_id].append(price)
        
        # 计算均线
        if len(self.prices[instrument_id]) == self.period:
            ma = sum(self.prices[instrument_id]) / self.period
            
            # 生成信号
            if price > ma * 1.01:  # 价格突破均线 1%
                logger.info(f"买入信号: {instrument_id} @ {price}, MA: {ma:.2f}")
            elif price < ma * 0.99:  # 价格跌破均线 1%
                logger.info(f"卖出信号: {instrument_id} @ {price}, MA: {ma:.2f}")
        
        return quote
```

## 示例插件

### 1. LoggingPlugin - 日志记录插件

记录所有行情和交易数据到日志文件。

**文件**: `logging_plugin.py`

**功能**:

- 记录行情更新(合约代码、价格、成交量等)
- 记录交易数据(订单、成交等)
- 可配置日志级别

**使用示例**:

```python
from examples.plugins.logging_plugin import LoggingPlugin

plugin = LoggingPlugin(log_quotes=True, log_trades=True)
api.register_plugin(plugin)
```

### 2. RiskControlPlugin - 风险控制插件

提供基本的风险控制功能。

**文件**: `risk_control_plugin.py`

**功能**:

- 过滤无效行情(价格为 NaN 或 0)
- 检测价格异常变动
- 验证交易数据完整性

**使用示例**:

```python
from examples.plugins.risk_control_plugin import RiskControlPlugin

# 设置最大价格变动为 10%
plugin = RiskControlPlugin(max_price_change_pct=10.0)
api.register_plugin(plugin)
```

## 开发自定义插件

### 步骤 1: 创建插件类

```python
from src.strategy.sync_api import StrategyPlugin, Quote
from loguru import logger

class MyCustomPlugin(StrategyPlugin):
    def __init__(self, param1, param2):
        """初始化插件参数"""
        self.param1 = param1
        self.param2 = param2
        self.api = None
    
    def on_init(self, api):
        """保存 API 引用"""
        self.api = api
        logger.info(f"自定义插件已初始化: {self.param1}, {self.param2}")
    
    def on_quote(self, quote: Quote) -> Quote:
        """处理行情数据"""
        # 你的自定义逻辑
        return quote
    
    def on_stop(self):
        """清理资源"""
        logger.info("自定义插件已停止")
```

### 步骤 2: 注册插件

```python
plugin = MyCustomPlugin(param1="value1", param2="value2")
api.register_plugin(plugin)
```

### 步骤 3: 测试插件

```python
# 订阅行情测试
api.subscribe(["rb2605"])
quote = api.get_quote("rb2605")

# 检查插件是否正常工作
```

## 插件最佳实践

### 1. 异常处理

插件中的异常会被自动捕获,不会影响核心功能:

```python
def on_quote(self, quote: Quote) -> Quote:
    try:
        # 你的处理逻辑
        return quote
    except Exception as e:
        logger.error(f"插件处理失败: {e}")
        return quote  # 返回原始数据
```

### 2. 性能优化

避免在插件中执行耗时操作:

```python
def on_quote(self, quote: Quote) -> Quote:
    # 不好: 同步写文件
    # with open("quotes.txt", "a") as f:
    #     f.write(str(quote))
    
    # 好: 使用队列异步处理
    self.quote_queue.put(quote)
    return quote
```

### 3. 状态管理

使用实例变量保存插件状态:

```python
def __init__(self):
    self.quote_count = 0
    self.last_prices = {}

def on_quote(self, quote: Quote) -> Quote:
    self.quote_count += 1
    self.last_prices[quote.InstrumentID] = quote.LastPrice
    return quote
```

### 4. 日志记录

使用 loguru 记录插件活动:

```python
from loguru import logger

def on_quote(self, quote: Quote) -> Quote:
    logger.debug(f"处理行情: {quote.InstrumentID}")
    return quote
```

## 常见问题

### Q: 插件的执行顺序是什么?

A: 插件按注册顺序依次执行。如果某个插件返回 None,后续插件不会被调用。

### Q: 插件异常会影响核心功能吗?

A: 不会。插件管理器会自动捕获所有插件异常,并记录到日志中。

### Q: 如何在插件中访问 API 方法?

A: 在 `on_init()` 中保存 API 引用:

```python
def on_init(self, api):
    self.api = api

def on_quote(self, quote: Quote) -> Quote:
    # 现在可以调用 API 方法
    position = self.api.get_position(quote.InstrumentID)
    return quote
```

### Q: 可以在插件中修改行情数据吗?

A: 可以,但要注意 Quote 是 dataclass,需要创建新实例:

```python
from dataclasses import replace

def on_quote(self, quote: Quote) -> Quote:
    # 修改价格
    return replace(quote, LastPrice=quote.LastPrice * 1.01)
```

## 更多示例

查看 `examples/` 目录下的其他示例,了解如何在实际策略中使用插件系统。

## 技术支持

如有问题或建议,请提交 Issue 或 Pull Request。

## 示例插件

本目录包含以下示例插件：

### 1. LoggingPlugin - 日志记录插件

**文件**: `logging_plugin.py`

**功能**:

- 记录所有行情更新（合约代码、价格、成交量等）
- 记录所有交易数据（订单、成交等）
- 可配置日志级别和输出格式

**使用示例**:

```python
from examples.plugins.logging_plugin import LoggingPlugin

# 只记录行情
plugin = LoggingPlugin(log_quotes=True, log_trades=False)
api.register_plugin(plugin)

# 记录所有数据
plugin = LoggingPlugin(log_quotes=True, log_trades=True)
api.register_plugin(plugin)
```

### 2. RiskControlPlugin - 风险控制插件

**文件**: `risk_control_plugin.py`

**功能**:

- 过滤无效行情（价格为 NaN 或 0）
- 检测价格异常变动（超过设定百分比）
- 验证交易数据完整性
- 监控持仓风险

**使用示例**:

```python
from examples.plugins.risk_control_plugin import RiskControlPlugin

# 设置最大价格变动为 10%
plugin = RiskControlPlugin(max_price_change_pct=10.0)
api.register_plugin(plugin)
```

## 高级主题

### 1. 插件间通信

插件可以通过 API 实例进行间接通信：

```python
class ProducerPlugin(StrategyPlugin):
    def on_init(self, api):
        self.api = api
        # 在 API 上设置共享数据
        if not hasattr(api, 'shared_data'):
            api.shared_data = {}
    
    def on_quote(self, quote: Quote) -> Quote:
        # 生产数据
        self.api.shared_data['last_price'] = quote.LastPrice
        return quote

class ConsumerPlugin(StrategyPlugin):
    def on_init(self, api):
        self.api = api
    
    def on_quote(self, quote: Quote) -> Quote:
        # 消费数据
        if hasattr(self.api, 'shared_data'):
            last_price = self.api.shared_data.get('last_price')
            logger.info(f"从共享数据读取: {last_price}")
        return quote
```

### 2. 异步处理

对于耗时操作，使用队列和后台线程：

```python
import queue
import threading
from src.strategy.sync_api import StrategyPlugin, Quote

class AsyncProcessingPlugin(StrategyPlugin):
    def on_init(self, api):
        self.api = api
        self.data_queue = queue.Queue()
        
        # 启动后台处理线程
        self.worker_thread = threading.Thread(target=self._process_data, daemon=True)
        self.worker_thread.start()
    
    def on_quote(self, quote: Quote) -> Quote:
        # 快速返回，数据放入队列
        self.data_queue.put(quote)
        return quote
    
    def _process_data(self):
        """后台线程处理数据"""
        while True:
            try:
                quote = self.data_queue.get(timeout=1.0)
                # 执行耗时操作
                self._save_to_database(quote)
            except queue.Empty:
                continue
    
    def _save_to_database(self, quote):
        """保存到数据库（耗时操作）"""
        pass
    
    def on_stop(self):
        # 等待队列清空
        self.data_queue.join()
```

### 3. 配置文件支持

使用配置文件管理插件参数：

```python
import yaml
from src.strategy.sync_api import StrategyPlugin

class ConfigurablePlugin(StrategyPlugin):
    def __init__(self, config_file="plugin_config.yaml"):
        self.config_file = config_file
        self.config = {}
    
    def on_init(self, api):
        self.api = api
        
        # 加载配置
        with open(self.config_file, 'r') as f:
            self.config = yaml.safe_load(f)
        
        logger.info(f"插件配置已加载: {self.config}")
```

配置文件 `plugin_config.yaml`:

```yaml
min_price: 3000
max_price: 4000
log_level: INFO
alert_email: admin@example.com
```

### 4. 数据库集成

将数据保存到数据库：

```python
import sqlite3
from src.strategy.sync_api import StrategyPlugin, Quote

class DatabasePlugin(StrategyPlugin):
    def on_init(self, api):
        self.api = api
        
        # 连接数据库
        self.conn = sqlite3.connect('quotes.db')
        self.cursor = self.conn.cursor()
        
        # 创建表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS quotes (
                timestamp TEXT,
                instrument_id TEXT,
                last_price REAL,
                volume INTEGER
            )
        ''')
        self.conn.commit()
    
    def on_quote(self, quote: Quote) -> Quote:
        # 插入数据
        self.cursor.execute(
            'INSERT INTO quotes VALUES (?, ?, ?, ?)',
            (datetime.now().isoformat(), quote.InstrumentID, 
             quote.LastPrice, quote.Volume)
        )
        self.conn.commit()
        return quote
    
    def on_stop(self):
        # 关闭连接
        self.conn.close()
```

### 5. 告警通知

发送告警通知：

```python
import smtplib
from email.mime.text import MIMEText
from src.strategy.sync_api import StrategyPlugin, Quote

class AlertPlugin(StrategyPlugin):
    def __init__(self, alert_threshold=5.0, email_to="admin@example.com"):
        self.alert_threshold = alert_threshold
        self.email_to = email_to
        self.last_prices = {}
    
    def on_init(self, api):
        self.api = api
    
    def on_quote(self, quote: Quote) -> Quote:
        instrument_id = quote.InstrumentID
        current_price = quote.LastPrice
        
        # 检查价格变动
        if instrument_id in self.last_prices:
            last_price = self.last_prices[instrument_id]
            change_pct = abs(current_price - last_price) / last_price * 100
            
            if change_pct > self.alert_threshold:
                self._send_alert(
                    f"价格异常变动: {instrument_id}, "
                    f"变动: {change_pct:.2f}%, "
                    f"当前价格: {current_price}"
                )
        
        self.last_prices[instrument_id] = current_price
        return quote
    
    def _send_alert(self, message):
        """发送邮件告警"""
        # 实现邮件发送逻辑
        logger.warning(f"告警: {message}")
```

## 最佳实践

### 1. 性能优化

**避免在钩子中执行耗时操作**:

```python
# 不好：同步写文件
def on_quote(self, quote: Quote) -> Quote:
    with open("quotes.txt", "a") as f:
        f.write(str(quote))  # 阻塞 I/O
    return quote

# 好：使用队列异步处理
def on_quote(self, quote: Quote) -> Quote:
    self.queue.put(quote)  # 快速返回
    return quote
```

**批量处理数据**:

```python
def on_quote(self, quote: Quote) -> Quote:
    self.buffer.append(quote)
    
    # 每 100 条数据批量写入
    if len(self.buffer) >= 100:
        self._batch_save(self.buffer)
        self.buffer.clear()
    
    return quote
```

### 2. 错误处理

**捕获并记录异常**:

```python
def on_quote(self, quote: Quote) -> Quote:
    try:
        # 你的处理逻辑
        result = self._process(quote)
        return result
    except Exception as e:
        logger.error(f"插件处理失败: {e}", exc_info=True)
        return quote  # 返回原始数据，不中断流程
```

**验证数据完整性**:

```python
def on_quote(self, quote: Quote) -> Quote:
    # 验证必要字段
    if not quote.InstrumentID:
        logger.warning("合约代码为空，过滤该行情")
        return None
    
    if math.isnan(quote.LastPrice):
        logger.warning(f"价格无效: {quote.InstrumentID}")
        return None
    
    return quote
```

### 3. 资源管理

**使用上下文管理器**:

```python
class FileWriterPlugin(StrategyPlugin):
    def on_init(self, api):
        self.api = api
        self.file = open("output.txt", "w")
    
    def on_stop(self):
        # 确保文件被关闭
        if self.file:
            self.file.close()
```

**及时释放资源**:

```python
def on_stop(self):
    # 关闭数据库连接
    if hasattr(self, 'conn'):
        self.conn.close()
    
    # 停止后台线程
    if hasattr(self, 'worker_thread'):
        self.stop_flag.set()
        self.worker_thread.join(timeout=5.0)
```

### 4. 日志记录

**使用结构化日志**:

```python
from loguru import logger

def on_quote(self, quote: Quote) -> Quote:
    logger.info(
        "行情更新",
        instrument_id=quote.InstrumentID,
        price=quote.LastPrice,
        volume=quote.Volume
    )
    return quote
```

**设置日志级别**:

```python
def on_init(self, api):
    self.api = api
    
    # 根据配置设置日志级别
    if self.debug_mode:
        logger.level("DEBUG")
    else:
        logger.level("INFO")
```

### 5. 测试

**编写单元测试**:

```python
import unittest
from src.strategy.internal.data_models import Quote
from my_plugin import MyPlugin

class TestMyPlugin(unittest.TestCase):
    def setUp(self):
        self.plugin = MyPlugin()
        self.plugin.on_init(None)  # 模拟初始化
    
    def test_filter_invalid_price(self):
        # 测试过滤无效价格
        quote = Quote(InstrumentID="rb2605", LastPrice=float('nan'))
        result = self.plugin.on_quote(quote)
        self.assertIsNone(result)
    
    def test_pass_valid_price(self):
        # 测试通过有效价格
        quote = Quote(InstrumentID="rb2605", LastPrice=3500.0)
        result = self.plugin.on_quote(quote)
        self.assertIsNotNone(result)
        self.assertEqual(result.LastPrice, 3500.0)
```

**集成测试**:

```python
def test_plugin_integration():
    # 创建 API 实例
    api = SyncStrategyApi("user_id", "password")
    
    # 注册插件
    plugin = MyPlugin()
    api.register_plugin(plugin)
    
    # 测试功能
    quote = api.get_quote("rb2605")
    assert quote is not None
    
    # 清理
    api.stop()
```

## 常见问题

### Q1: 插件的执行顺序是什么？

**A**: 插件按注册顺序依次执行。如果某个插件返回 None，后续插件不会被调用。

```python
api.register_plugin(Plugin1())  # 第一个执行
api.register_plugin(Plugin2())  # 第二个执行
api.register_plugin(Plugin3())  # 第三个执行
```

### Q2: 插件异常会影响核心功能吗？

**A**: 不会。插件管理器会自动捕获所有插件异常，并记录到日志中。核心功能和其他插件不受影响。

### Q3: 如何在插件中访问 API 方法？

**A**: 在 `on_init()` 中保存 API 引用：

```python
def on_init(self, api):
    self.api = api

def on_quote(self, quote: Quote) -> Quote:
    # 现在可以调用 API 方法
    position = self.api.get_position(quote.InstrumentID)
    return quote
```

### Q4: 可以在插件中修改行情数据吗？

**A**: 可以，但要注意 Quote 是 dataclass，需要创建新实例：

```python
from dataclasses import replace

def on_quote(self, quote: Quote) -> Quote:
    # 修改价格（创建新实例）
    return replace(quote, LastPrice=quote.LastPrice * 1.01)
```

### Q5: 如何在插件之间共享数据？

**A**: 可以通过 API 实例的属性共享数据：

```python
# 插件 1：生产数据
def on_init(self, api):
    self.api = api
    api.shared_data = {}

def on_quote(self, quote: Quote) -> Quote:
    self.api.shared_data['last_price'] = quote.LastPrice
    return quote

# 插件 2：消费数据
def on_quote(self, quote: Quote) -> Quote:
    last_price = self.api.shared_data.get('last_price')
    return quote
```

### Q6: 插件可以调用其他插件吗？

**A**: 不建议直接调用。插件应该保持独立，通过插件链机制自然组合。如果需要复杂的交互，考虑使用共享数据或事件机制。

### Q7: 如何调试插件？

**A**: 使用日志记录和断点调试：

```python
def on_quote(self, quote: Quote) -> Quote:
    # 添加调试日志
    logger.debug(f"处理行情: {quote}")
    
    # 可以在这里设置断点
    result = self._process(quote)
    
    logger.debug(f"处理结果: {result}")
    return result
```

### Q8: 插件会影响性能吗？

**A**: 会有一定影响。插件在关键路径上执行，应该保持简单快速。对于耗时操作，使用异步处理。

## 故障排查

### 问题 1: 插件未被调用

**症状**: 注册了插件但钩子方法没有被调用

**排查步骤**:

1. 检查插件是否正确注册：`api.register_plugin(plugin)`
1. 检查钩子方法签名是否正确
1. 检查是否有其他插件返回了 None（中断了插件链）
1. 查看日志中是否有插件异常

**解决方案**:

```python
# 确保正确注册
plugin = MyPlugin()
api.register_plugin(plugin)

# 检查插件是否在列表中
logger.info(f"已注册插件数量: {len(api._plugin_manager._plugins)}")
```

### 问题 2: 插件异常导致数据丢失

**症状**: 插件抛出异常后，数据没有被处理

**排查步骤**:

1. 查看日志中的异常信息
1. 检查插件是否正确处理了异常
1. 确认插件返回了有效数据

**解决方案**:

```python
def on_quote(self, quote: Quote) -> Quote:
    try:
        # 处理逻辑
        return self._process(quote)
    except Exception as e:
        logger.error(f"处理失败: {e}", exc_info=True)
        return quote  # 返回原始数据，不丢失
```

### 问题 3: 插件性能问题

**症状**: 注册插件后系统变慢

**排查步骤**:

1. 使用性能分析工具（如 cProfile）
1. 检查插件中是否有耗时操作
1. 查看日志中的处理时间

**解决方案**:

```python
import time

def on_quote(self, quote: Quote) -> Quote:
    start_time = time.time()
    
    # 处理逻辑
    result = self._process(quote)
    
    elapsed = time.time() - start_time
    if elapsed > 0.01:  # 超过 10ms
        logger.warning(f"插件处理耗时: {elapsed:.3f}s")
    
    return result
```

### 问题 4: 资源泄漏

**症状**: 长时间运行后内存或文件句柄增加

**排查步骤**:

1. 检查 `on_stop()` 是否正确实现
1. 检查是否有未关闭的文件或连接
1. 使用内存分析工具

**解决方案**:

```python
def on_init(self, api):
    self.api = api
    self.resources = []
    
    # 记录所有打开的资源
    file = open("output.txt", "w")
    self.resources.append(file)

def on_stop(self):
    # 关闭所有资源
    for resource in self.resources:
        try:
            resource.close()
        except Exception as e:
            logger.error(f"关闭资源失败: {e}")
```

## 更多资源

- **源代码**: `src/strategy/internal/plugin.py`
- **示例插件**: `examples/plugins/`
- **测试代码**: `tests/strategy/internal/test_plugin.py`
- **API 文档**: `src/strategy/sync_api.py`

## 贡献

欢迎贡献新的插件示例！请遵循以下步骤：

1. Fork 项目
1. 创建插件文件
1. 添加文档和示例
1. 编写测试
1. 提交 Pull Request

## 技术支持

如有问题或建议，请：

- 提交 Issue
- 发送邮件
- 查看项目文档

______________________________________________________________________

**祝你开发愉快！** 🚀
