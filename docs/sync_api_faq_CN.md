# SyncStrategyApi 常见问题和最佳实践

## 目录

- [常见问题](#常见问题)
- [最佳实践](#最佳实践)
- [性能优化](#性能优化)
- [错误处理](#错误处理)
- [调试技巧](#调试技巧)

---

## 常见问题

### Q1: 如何处理连接超时？

**问题：** 初始化 SyncStrategyApi 时出现 `TimeoutError`。

**解决方案：**

1. 增加超时时间：

```python
api = SyncStrategyApi(
    user_id="user_id",
    password="password",
    timeout=60.0  # 增加到 60 秒
)
```

2. 检查网络连接和 CTP 服务器状态
3. 检查配置文件中的服务器地址是否正确
4. 确认用户 ID 和密码是否正确

---

### Q2: 如何处理行情订阅失败？

**问题：** `get_quote()` 抛出 `TimeoutError`。

**可能原因：**
- 合约代码错误
- 合约不存在或已过期
- 网络连接问题
- CTP 服务器限制

**解决方案：**

```python
try:
    quote = api.get_quote("rb2505", timeout=10.0)
except TimeoutError:
    print("行情订阅超时，请检查合约代码是否正确")
    # 可以尝试重试或使用其他合约
```

---

### Q3: 如何同时交易多个合约？

**解决方案：** 为每个合约启动独立的策略线程。

```python
def strategy_for_symbol(api, symbol):
    while True:
        quote = api.get_quote(symbol)
        # ... 策略逻辑 ...
        time.sleep(1)

# 为多个合约启动策略
symbols = ["rb2505", "hc2505", "i2505"]
threads = []

for symbol in symbols:
    thread = api.run_strategy(strategy_for_symbol, api, symbol)
    threads.append(thread)

# 等待所有策略
for thread in threads:
    thread.join()
```

---

### Q4: 策略异常会影响其他策略吗？

**答案：** 不会。每个策略在独立线程中运行，异常会被自动捕获并记录。

**示例：**

```python
def strategy1(api):
    # 这个策略会抛出异常
    raise Exception("策略1异常")

def strategy2(api):
    # 这个策略不受影响
    while True:
        quote = api.get_quote("rb2505")
        print(f"策略2正常运行: {quote.LastPrice}")
        time.sleep(1)

# 启动两个策略
api.run_strategy(strategy1, api)  # 会抛出异常但不影响其他策略
api.run_strategy(strategy2, api)  # 继续正常运行
```


---

### Q5: 如何处理持仓查询失败？

**问题：** `get_position()` 返回空持仓对象。

**可能原因：**
- 确实没有持仓（正常情况）
- 持仓查询超时
- 持仓查询失败

**解决方案：**

```python
position = api.get_position("rb2505")

# 检查是否有持仓
if position.pos_long > 0 or position.pos_short > 0:
    print("有持仓")
else:
    print("无持仓或查询失败")
    # 可以尝试重新查询
    position = api.get_position("rb2505", timeout=15.0)
```

---

### Q6: 如何处理订单提交失败？

**问题：** `open_close()` 返回 `success=False`。

**解决方案：**

```python
result = api.open_close("rb2505", "kaiduo", 1, 3500.0)

if not result["success"]:
    error_id = result.get("error_id", -1)
    error_msg = result.get("error_msg", "未知错误")
    
    print(f"订单失败: [{error_id}] {error_msg}")
    
    # 根据错误代码处理
    if error_id == 22:  # 资金不足
        print("资金不足，无法开仓")
    elif error_id == 31:  # 超过最大报单数
        print("超过最大报单数")
    else:
        print("其他错误，请检查日志")
```

---

### Q7: 如何优雅地停止策略？

**解决方案：** 使用标志变量控制策略循环。

```python
import threading

# 创建停止标志
stop_flag = threading.Event()

def my_strategy(api, symbol):
    while not stop_flag.is_set():
        quote = api.get_quote(symbol)
        print(f"价格: {quote.LastPrice}")
        time.sleep(1)
    
    print("策略已停止")

# 启动策略
thread = api.run_strategy(my_strategy, api, "rb2505")

# 运行一段时间后停止
time.sleep(10)
stop_flag.set()

# 等待策略完成
thread.join()

# 停止 API 服务
api.stop()
```

---

### Q8: 如何处理价格为 NaN 的情况？

**问题：** Quote 对象的价格字段为 `float('nan')`。

**解决方案：**

```python
import math

quote = api.get_quote("rb2505")

# 检查价格是否有效
if math.isnan(quote.LastPrice):
    print("价格无效，可能是行情数据异常")
else:
    print(f"有效价格: {quote.LastPrice}")

# 或者使用 try-except
try:
    if quote.LastPrice > 0:
        print(f"价格: {quote.LastPrice}")
except:
    print("价格无效")
```

---

### Q9: 如何实现策略的定时执行？

**解决方案：** 使用 `time.sleep()` 控制执行频率。

```python
import time

def scheduled_strategy(api, symbol, interval=60):
    """每隔 interval 秒执行一次"""
    while True:
        # 执行策略逻辑
        quote = api.get_quote(symbol)
        position = api.get_position(symbol)
        
        print(f"定时检查: 价格={quote.LastPrice}, 持仓={position.pos_long}")
        
        # 等待下一次执行
        time.sleep(interval)

# 每 60 秒执行一次
api.run_strategy(scheduled_strategy, api, "rb2505", 60)
```

---

### Q10: 如何实现策略的条件触发？

**解决方案：** 使用 `wait_quote_update()` 等待行情更新。

```python
def condition_strategy(api, symbol, trigger_price):
    """当价格达到 trigger_price 时触发"""
    while True:
        quote = api.wait_quote_update(symbol, timeout=30.0)
        
        if quote.LastPrice >= trigger_price:
            print(f"价格达到触发条件: {quote.LastPrice} >= {trigger_price}")
            # 执行交易逻辑
            result = api.open_close(symbol, "kaiduo", 1, quote.AskPrice1)
            if result["success"]:
                print("触发交易成功")
                break

# 当价格达到 3600 时触发
api.run_strategy(condition_strategy, api, "rb2505", 3600.0)
```

---

## 最佳实践

### 1. 使用 try-finally 确保资源释放

```python
api = SyncStrategyApi("user_id", "password")

try:
    # 运行策略
    # ...
    pass
finally:
    # 确保资源被释放
    api.stop()
```

---

### 2. 合理设置超时时间

```python
# 根据网络状况和策略需求设置超时时间
api = SyncStrategyApi(
    user_id="user_id",
    password="password",
    timeout=30.0  # 连接超时
)

# 行情查询使用较短的超时
quote = api.get_quote("rb2505", timeout=5.0)

# 行情更新等待使用较长的超时
quote = api.wait_quote_update("rb2505", timeout=30.0)
```

---

### 3. 使用配置文件管理参数

```yaml
# config/config.yaml
sync_api:
  connect_timeout: 30.0
  quote_timeout: 10.0
  quote_update_timeout: 30.0
  position_timeout: 10.0
  order_timeout: 10.0
  stop_timeout: 5.0
  max_strategies: 10
```

```python
# 使用配置文件
api = SyncStrategyApi(
    user_id="user_id",
    password="password",
    config_path="./config/config.yaml"
)
```

---

### 4. 策略函数应该包含异常处理

```python
def robust_strategy(api, symbol):
    """健壮的策略函数"""
    try:
        while True:
            try:
                # 获取行情
                quote = api.get_quote(symbol, timeout=10.0)
                
                # 策略逻辑
                # ...
                
            except TimeoutError:
                print("行情超时，重试...")
                continue
            except Exception as e:
                print(f"策略异常: {e}")
                time.sleep(1)
                continue
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("策略被用户中断")
```

---

### 5. 使用日志记录策略运行状态

```python
from loguru import logger

def logged_strategy(api, symbol):
    """带日志的策略"""
    logger.info(f"策略启动: {symbol}")
    
    try:
        while True:
            quote = api.get_quote(symbol)
            logger.debug(f"行情: {symbol} = {quote.LastPrice}")
            
            # 策略逻辑
            # ...
            
            time.sleep(1)
            
    except Exception as e:
        logger.error(f"策略异常: {e}", exc_info=True)
    finally:
        logger.info(f"策略结束: {symbol}")
```

---

### 6. 避免在策略中执行耗时操作

```python
# 不推荐：在策略中执行耗时操作
def bad_strategy(api, symbol):
    while True:
        quote = api.get_quote(symbol)
        
        # 耗时操作会阻塞策略
        time.sleep(60)  # 不推荐
        
        # 复杂计算
        result = complex_calculation()  # 不推荐

# 推荐：使用独立线程处理耗时操作
def good_strategy(api, symbol):
    while True:
        quote = api.get_quote(symbol)
        
        # 使用独立线程处理耗时操作
        threading.Thread(
            target=complex_calculation,
            args=(quote,),
            daemon=True
        ).start()
        
        time.sleep(1)
```

---

### 7. 合理使用行情缓存

```python
# 推荐：使用 get_quote() 获取缓存的行情
def efficient_strategy(api, symbol):
    while True:
        # 第一次调用会订阅并等待行情
        # 后续调用直接返回缓存的行情
        quote = api.get_quote(symbol)
        
        # 策略逻辑
        # ...
        
        time.sleep(1)

# 不推荐：频繁使用 wait_quote_update()
def inefficient_strategy(api, symbol):
    while True:
        # 每次都阻塞等待新行情，效率低
        quote = api.wait_quote_update(symbol)
        
        # 策略逻辑
        # ...
```

---

### 8. 策略应该有明确的退出条件

```python
def strategy_with_exit(api, symbol, max_iterations=1000):
    """有退出条件的策略"""
    iteration = 0
    
    while iteration < max_iterations:
        quote = api.get_quote(symbol)
        
        # 策略逻辑
        # ...
        
        iteration += 1
        time.sleep(1)
    
    print(f"策略完成: 执行了 {iteration} 次迭代")
```

---

## 性能优化

### 1. 减少不必要的 API 调用

```python
# 不推荐：频繁查询持仓
def inefficient_position_check(api, symbol):
    while True:
        position = api.get_position(symbol)  # 每次都查询
        # ...
        time.sleep(0.1)

# 推荐：缓存持仓信息，定期更新
def efficient_position_check(api, symbol):
    position = api.get_position(symbol)
    last_update = time.time()
    
    while True:
        # 每 5 秒更新一次持仓
        if time.time() - last_update > 5:
            position = api.get_position(symbol)
            last_update = time.time()
        
        # 使用缓存的持仓信息
        # ...
        
        time.sleep(0.1)
```

---

### 2. 使用批量操作

```python
# 推荐：批量订阅多个合约
def batch_subscribe(api, symbols):
    """批量订阅合约"""
    for symbol in symbols:
        # get_quote 会自动订阅
        try:
            api.get_quote(symbol, timeout=5.0)
        except TimeoutError:
            print(f"订阅 {symbol} 超时")
```

---

### 3. 合理设置策略执行频率

```python
# 根据策略类型设置合适的执行频率

# 高频策略：使用 wait_quote_update()
def high_frequency_strategy(api, symbol):
    while True:
        quote = api.wait_quote_update(symbol)
        # 每次行情更新都执行
        # ...

# 中频策略：使用 get_quote() + sleep
def medium_frequency_strategy(api, symbol):
    while True:
        quote = api.get_quote(symbol)
        # 每秒执行一次
        # ...
        time.sleep(1)

# 低频策略：使用较长的 sleep
def low_frequency_strategy(api, symbol):
    while True:
        quote = api.get_quote(symbol)
        # 每分钟执行一次
        # ...
        time.sleep(60)
```

---

## 错误处理

### 1. 处理连接错误

```python
def handle_connection_error():
    """处理连接错误"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            api = SyncStrategyApi(
                user_id="user_id",
                password="password",
                timeout=30.0
            )
            print("连接成功")
            return api
            
        except TimeoutError:
            retry_count += 1
            print(f"连接超时，重试 {retry_count}/{max_retries}")
            time.sleep(5)
            
        except RuntimeError as e:
            print(f"连接失败: {e}")
            break
    
    raise RuntimeError("连接失败，已达到最大重试次数")
```

---

### 2. 处理行情异常

```python
def handle_quote_error(api, symbol):
    """处理行情异常"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            quote = api.get_quote(symbol, timeout=10.0)
            
            # 检查价格是否有效
            if math.isnan(quote.LastPrice):
                print("价格无效，重试...")
                retry_count += 1
                time.sleep(1)
                continue
            
            return quote
            
        except TimeoutError:
            retry_count += 1
            print(f"行情超时，重试 {retry_count}/{max_retries}")
            time.sleep(1)
    
    raise RuntimeError(f"获取 {symbol} 行情失败")
```

---

### 3. 处理订单异常

```python
def handle_order_error(api, symbol, action, volume, price):
    """处理订单异常"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            result = api.open_close(
                symbol, action, volume, price,
                block=True, timeout=10.0
            )
            
            if result["success"]:
                print(f"订单成功: {result['order_ref']}")
                return result
            else:
                error_id = result.get("error_id", -1)
                error_msg = result.get("error_msg", "未知错误")
                
                # 某些错误不需要重试
                if error_id in [22, 31]:  # 资金不足、超过最大报单数
                    print(f"订单失败（不重试）: [{error_id}] {error_msg}")
                    return result
                
                # 其他错误重试
                retry_count += 1
                print(f"订单失败，重试 {retry_count}/{max_retries}: [{error_id}] {error_msg}")
                time.sleep(1)
                
        except TimeoutError:
            retry_count += 1
            print(f"订单超时，重试 {retry_count}/{max_retries}")
            time.sleep(1)
    
    raise RuntimeError(f"提交订单失败: {symbol} {action} {volume}@{price}")
```

---

## 调试技巧

### 1. 启用详细日志

```python
from loguru import logger

# 设置日志级别为 DEBUG
logger.remove()
logger.add(
    "strategy.log",
    level="DEBUG",
    rotation="1 day",
    retention="7 days"
)

# 在策略中使用日志
def debug_strategy(api, symbol):
    logger.debug(f"策略启动: {symbol}")
    
    while True:
        quote = api.get_quote(symbol)
        logger.debug(f"行情: {symbol} = {quote.LastPrice}")
        
        # 策略逻辑
        # ...
        
        time.sleep(1)
```

---

### 2. 使用断点调试

```python
def debug_strategy(api, symbol):
    while True:
        quote = api.get_quote(symbol)
        
        # 在关键位置设置断点
        import pdb; pdb.set_trace()
        
        # 策略逻辑
        # ...
        
        time.sleep(1)
```

---

### 3. 打印中间结果

```python
def debug_strategy(api, symbol):
    price_history = []
    
    while True:
        quote = api.get_quote(symbol)
        price_history.append(quote.LastPrice)
        
        # 打印中间结果
        print(f"价格历史: {price_history[-5:]}")
        
        if len(price_history) >= 20:
            fast_ma = sum(price_history[-5:]) / 5
            slow_ma = sum(price_history[-20:]) / 20
            
            # 打印均线值
            print(f"快线: {fast_ma:.2f}, 慢线: {slow_ma:.2f}")
        
        time.sleep(1)
```

---

### 4. 使用模拟模式测试

```python
# 在 SimNow 7x24 环境中测试策略
api = SyncStrategyApi(
    user_id="simnow_user_id",
    password="simnow_password",
    config_path="./config/config_simnow.yaml"
)

# 测试策略
try:
    # 运行策略
    # ...
    pass
finally:
    api.stop()
```

---

## 相关文档

- [快速开始指南](sync_api_quick_start_CN.md)
- [API 参考文档](sync_api_reference_CN.md)
- [示例代码](../examples/sync_strategy_example.py)

---

## 技术支持

如有问题，请查看项目文档或提交 Issue。
