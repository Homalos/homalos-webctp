# SyncStrategyApi 使用示例

本目录包含 SyncStrategyApi 的各种使用示例，帮助您快速上手。

## 示例列表

### 1. 简单演示（推荐新手）
**文件：** `example_simple_demo.py`

展示 SyncStrategyApi 的基本用法：
- 获取行情快照
- 查询持仓信息
- 等待行情更新

**运行：**
```bash
python examples/example_simple_demo.py
```

### 2. 双均线策略
**文件：** `example_dual_ma_strategy.py`

实现经典的双均线交易策略：
- 快速均线上穿慢速均线时开多仓
- 快速均线下穿慢速均线时开空仓
- 展示 get_quote()、get_position()、open_close() 的使用

**运行：**
```bash
python examples/example_dual_ma_strategy.py
```

### 3. 行情监控策略
**文件：** `example_quote_monitor.py`

实时监控并打印行情数据：
- 使用 wait_quote_update() 阻塞等待行情更新
- 实时打印行情数据

**运行：**
```bash
python examples/example_quote_monitor.py
```

### 4. 持仓监控策略
**文件：** `example_position_monitor.py`

定期查询并打印持仓信息：
- 使用 get_position() 查询持仓
- 定期打印持仓数据

**运行：**
```bash
python examples/example_position_monitor.py
```

### 5. 多策略并发运行
**文件：** `example_multi_strategy.py`

展示如何同时运行多个策略：
- 使用 run_strategy() 在独立线程中运行策略
- 多个策略并发执行，互不干扰

**运行：**
```bash
python examples/example_multi_strategy.py
```

## 配置文件

**文件：** `config_example.py`

所有示例共享的配置文件，包含：
- CTP 连接配置（用户名、密码、配置文件路径）
- 策略参数（合约代码、均线周期、交易手数等）
- 合约信息（合约乘数等）

**修改配置：**
编辑 `config_example.py` 文件，修改您的 CTP 账号信息和策略参数。

## 注意事项

1. **修改账号信息**：运行示例前，请先修改 `config_example.py` 中的用户名和密码
2. **合约信息**：建议在 `INSTRUMENT_INFO` 中提供合约乘数，避免 CTP 查询失败
3. **非交易时间**：非交易时间段运行示例时，行情更新会超时并返回缓存数据
4. **SimNow 环境**：示例默认使用 SimNow 7x24 模拟环境

## 旧版示例

**文件：** `sync_strategy_example.py`

包含所有示例的旧版本，通过交互式菜单选择运行哪个示例。
建议使用新的独立脚本，更方便测试和调试。
