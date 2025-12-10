# 日志工具使用指南

## 概述

homalos-webctp 项目使用基于 `loguru` 的日志工具类 `Logger`，提供强大的日志记录功能。

### 主要特性

- ✅ **标签分类**：使用 `tag` 参数对日志进行分类
- ✅ **Trace ID 追踪**：支持请求级别的追踪 ID
- ✅ **多输出目标**：同时输出到控制台和文件
- ✅ **自动轮转**：日志文件自动轮转和压缩
- ✅ **线程安全**：支持多线程和异步操作
- ✅ **详细堆栈**：异常时包含完整堆栈跟踪

## Tag 说明

### 什么是 Tag？

`tag` 是日志的**分类标签**，用于：

- **日志分类** - 快速识别日志来自哪个模块或功能
- **日志过滤** - 在日志文件中快速查找特定类型的日志
- **问题追踪** - 通过 tag 追踪特定功能的执行流程
- **性能分析** - 统计不同模块的日志数量和性能指标

### 常见 Tag 使用场景

| Tag | 使用场景 | 示例 |
|-----|---------|------|
| `auth` | 认证和授权相关 | 登录、权限验证 |
| `database` | 数据库操作 | 查询、插入、更新、删除 |
| `websocket` | WebSocket 通信 | 连接、断开、消息收发 |
| `request` | HTTP 请求处理 | 请求接收、响应发送 |
| `payment` | 支付相关 | 支付处理、退款 |
| `order` | 订单相关 | 订单创建、更新、取消 |
| `cache` | 缓存操作 | 缓存命中、缓存更新 |
| `email` | 邮件发送 | 邮件发送、模板渲染 |
| `file` | 文件操作 | 上传、下载、删除 |
| `connection` | 连接管理 | 连接建立、断开 |
| `retry` | 重试逻辑 | 重试次数、退避策略 |
| `validation` | 数据验证 | 参数验证、业务规则验证 |

### Tag 命名规范

1. **使用小写字母** - `auth`, `database`, `websocket`
2. **使用下划线分隔** - `user_auth`, `db_query`, `ws_connect`
3. **保持简洁** - 通常 1-2 个单词
4. **表示功能/模块** - 而不是日志级别
5. **保持一致性** - 同一功能使用相同的 tag

## 快速开始

### 基础使用

```python
from utils import logger

# 不指定 tag - 日志不带标签
logger.debug("调试信息")
logger.info("普通信息")
logger.success("成功信息")
logger.warning("警告信息")
logger.error("错误信息")
logger.critical("严重错误")

# 指定 tag - 日志带标签
logger.info("普通信息", tag="auth")
logger.error("错误信息", tag="database")
logger.success("成功信息", tag="payment")
```

### 使用 Trace ID

Logger 支持三种方式使用 trace_id：

#### 方式 1：为单条日志添加 trace_id

```python
from utils import logger

# 自动生成 UUID 作为 trace_id
logger.info("处理请求", trace_id=True)
logger.info("查询数据库", tag="database", trace_id=True)

# 指定 trace_id
logger.info("处理请求", trace_id="req-12345")
logger.error("数据库错误", tag="database", trace_id="req-12345")
```

**输出：**
```
INFO     | [trace_id=550e8400-e29b-41d4-a716-446655440000] 处理请求
INFO     | [trace_id=550e8400-e29b-41d4-a716-446655440001] [database] 查询数据库
INFO     | [trace_id=req-12345] 处理请求
ERROR    | [trace_id=req-12345] [database] 数据库错误
```

#### 方式 2：全局设置 trace_id

```python
from utils import logger

# 设置全局 trace_id
logger.set_trace_id("req-12345")
logger.info("处理请求", tag="request")
logger.info("查询数据库", tag="database")

# 清除 trace_id
logger.clear_trace_id()
```

#### 方式 3：自动生成全局 trace_id

```python
from utils import logger

# 自动生成 UUID 作为全局 trace_id
trace_id = logger.set_trace_id()
logger.info("处理请求", tag="request")
logger.info("查询数据库", tag="database")

# 清除 trace_id
logger.clear_trace_id()
```

### 异常记录

```python
from utils import logger

try:
    result = 1 / 0
except Exception as e:
    logger.exception("发生异常", tag="error")
    # 自动记录完整的堆栈跟踪
```

## 实际应用场景

### 1. WebSocket 连接处理

```python
from fastapi import WebSocket
from utils import logger

async def websocket_endpoint(websocket: WebSocket):
    try:
        await websocket.accept()
        # 为连接建立事件添加 trace_id
        logger.info("WebSocket 连接建立", tag="connection", trace_id=True)
        
        while True:
            data = await websocket.receive_text()
            # 为每条消息添加 trace_id
            logger.debug(f"收到数据: {data}", tag="websocket", trace_id=True)
            
            # 处理数据
            result = process_data(data)
            await websocket.send_text(result)
            logger.debug("发送响应", tag="websocket", trace_id=True)
            
    except Exception as e:
        logger.exception("WebSocket 处理异常", tag="connection", trace_id=True)
    finally:
        logger.info("WebSocket 连接关闭", tag="connection", trace_id=True)
```

### 2. 数据库操作

```python
from utils import logger

def query_user(user_id: int):
    logger.debug(f"查询用户: {user_id}", tag="database")
    
    try:
        # 执行查询
        user = db.query(User).filter(User.id == user_id).first()
        
        if user:
            logger.info(f"用户查询成功: {user.name}", tag="database")
            return user
        else:
            logger.warning(f"用户不存在: {user_id}", tag="database")
            return None
            
    except Exception as e:
        logger.exception(f"查询用户异常: {user_id}", tag="database")
        raise
```

### 3. 业务逻辑处理

```python
from utils import logger

async def process_order(order_id: str):
    logger.info(f"开始处理订单: {order_id}", tag="order")
    
    try:
        # 验证订单
        order = validate_order(order_id)
        logger.debug("订单验证通过", tag="order")
        
        # 支付处理
        payment_result = await process_payment(order)
        logger.info("支付处理完成", tag="payment")
        
        # 发货
        shipping_result = await create_shipping(order)
        logger.success("订单处理完成", tag="order")
        
        return shipping_result
        
    except ValidationError as e:
        logger.warning(f"订单验证失败: {e}", tag="order")
        raise
    except PaymentError as e:
        logger.error(f"支付失败: {e}", tag="payment")
        raise
    except Exception as e:
        logger.exception("订单处理异常", tag="order")
        raise
```

### 4. 认证和授权

```python
from utils import logger

def authenticate_user(username: str, password: str):
    logger.debug(f"认证用户: {username}", tag="auth")
    
    try:
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            logger.warning(f"用户不存在: {username}", tag="auth")
            return None
        
        if not verify_password(password, user.password_hash):
            logger.warning(f"密码错误: {username}", tag="auth")
            return None
        
        logger.success(f"用户认证成功: {username}", tag="auth")
        return user
        
    except Exception as e:
        logger.exception(f"认证异常: {username}", tag="auth")
        raise
```

## 日志输出示例

### 控制台输出

```
DEBUG    | utils.log.logger:debug:189 | [trace_id=req-12345] [database] 查询用户: 123
INFO     | services.td_client:call:67 | [trace_id=req-12345] [request] 处理请求
SUCCESS  | services.td_client:call:75 | [trace_id=req-12345] [request] 订单处理完成
WARNING  | utils.log.logger:warning:225 | [trace_id=req-12345] [auth] 密码错误: user123
ERROR    | services.connection:run:45 | [trace_id=req-12345] [connection] WebSocket 连接异常
```

### 文件输出

日志文件位置：`logs/` 目录

- `webctp.log` - 所有日志（DEBUG 及以上）
- `webctp_error.log` - 仅错误日志（ERROR 及以上）

文件格式：
```
2025-12-03 14:30:45.123 | DEBUG    | utils.log.logger:debug:189 | [trace_id=req-12345] [database] 查询用户: 123
2025-12-03 14:30:46.456 | INFO     | services.td_client:call:67 | [trace_id=req-12345] [request] 处理请求
2025-12-03 14:30:47.789 | SUCCESS  | services.td_client:call:75 | [trace_id=req-12345] [request] 订单处理完成
```

## API 参考

### Logger 类

#### 日志方法

```python
# 所有日志方法都支持 tag 和 trace_id 参数
logger.debug(message: str, tag: Optional[str] = None, trace_id: Optional[str] = None, **kwargs) -> None
logger.info(message: str, tag: Optional[str] = None, trace_id: Optional[str] = None, **kwargs) -> None
logger.success(message: str, tag: Optional[str] = None, trace_id: Optional[str] = None, **kwargs) -> None
logger.warning(message: str, tag: Optional[str] = None, trace_id: Optional[str] = None, **kwargs) -> None
logger.error(message: str, tag: Optional[str] = None, trace_id: Optional[str] = None, **kwargs) -> None
logger.critical(message: str, tag: Optional[str] = None, trace_id: Optional[str] = None, **kwargs) -> None
logger.exception(message: str, tag: Optional[str] = None, trace_id: Optional[str] = None, **kwargs) -> None

# trace_id 参数说明：
# - True: 自动生成 UUID
# - str: 使用指定的 trace_id
# - None/False: 不添加 trace_id
```

#### Trace ID 方法

```python
# 生成唯一的 trace_id（UUID）
trace_id = logger.generate_trace_id() -> str

# 设置全局 trace_id（如果不指定则自动生成）
trace_id = logger.set_trace_id(trace_id: Optional[str] = None) -> str

# 获取当前全局 trace_id
logger.get_trace_id() -> Optional[str]

# 清除全局 trace_id
logger.clear_trace_id() -> None
```

## Tag 与 Trace ID 的协同

`tag` 和 `trace_id` 的组合非常强大，可以快速定位和追踪问题：

```python
# trace_id 用于追踪单个请求的完整流程
# tag 用于快速定位问题所在的模块

# 查看某个请求的所有日志
# grep "trace_id=req-123" logs/webctp.log

# 查看某个模块的所有问题
# grep "\[payment\]" logs/webctp_error.log

# 查看某个请求在某个模块的日志
# grep "trace_id=req-123" logs/webctp.log | grep "\[payment\]"
```

### 实际应用示例

**追踪一个请求的完整流程：**

```python
# 所有相关日志都带有 trace_id 和对应的 tag
with logger.trace():  # 自动生成 trace_id
    logger.info("收到订单请求", tag="request")
    
    # 数据库操作
    logger.debug("查询用户信息", tag="database")
    logger.debug("查询订单商品", tag="database")
    
    # 支付处理
    logger.info("调用支付接口", tag="payment")
    logger.success("支付成功", tag="payment")
    
    # 订单更新
    logger.info("更新订单状态", tag="order")
    logger.success("订单处理完成", tag="order")
```

**输出日志示例：**
```
INFO     | [trace_id=abc-123] [request] 收到订单请求
DEBUG    | [trace_id=abc-123] [database] 查询用户信息
DEBUG    | [trace_id=abc-123] [database] 查询订单商品
INFO     | [trace_id=abc-123] [payment] 调用支付接口
SUCCESS  | [trace_id=abc-123] [payment] 支付成功
INFO     | [trace_id=abc-123] [order] 更新订单状态
SUCCESS  | [trace_id=abc-123] [order] 订单处理完成
```

## 最佳实践

### 1. 何时使用 Tag

```python
# ✅ 好的做法：在需要分类的地方使用 tag

# 认证相关
logger.info("用户登录成功", tag="auth")
logger.warning("登录失败", tag="auth")

# 数据库相关
logger.debug("执行查询", tag="database")
logger.error("数据库连接失败", tag="database")

# 支付相关
logger.info("支付处理开始", tag="payment")
logger.success("支付成功", tag="payment")

# ✅ 好的做法：不需要分类时可以不指定 tag
logger.info("系统启动")
logger.debug("处理完成")
```

### 2. 使用有意义的标签

```python
# ✅ 好的做法
logger.error("数据库连接失败", tag="database")
logger.warning("缓存命中率低", tag="cache")
logger.info("订单创建成功", tag="order")

# ❌ 不好的做法
logger.error("数据库连接失败", tag="error")  # tag 应该表示功能模块
logger.warning("缓存命中率低", tag="warning")  # tag 不应该是日志级别
logger.info("订单创建成功", tag="success")  # tag 不应该是操作结果
```

### 3. 使用 trace_id 参数

```python
# ✅ 最佳做法：为需要追踪的日志添加 trace_id 参数
def process_payment(order_id: str):
    # 为关键操作添加 trace_id
    logger.info(f"开始处理支付: {order_id}", tag="payment", trace_id=True)
    
    try:
        # 验证
        logger.debug("验证订单", tag="payment", trace_id=True)
        
        # 处理
        result = call_payment_api(order_id)
        logger.success("支付成功", tag="payment", trace_id=True)
        return result
        
    except Exception as e:
        logger.exception("支付失败", tag="payment", trace_id=True)
        raise

# ✅ 好的做法：为相关的日志使用相同的 trace_id
trace_id = logger.generate_trace_id()
logger.info("开始处理", trace_id=trace_id)
logger.debug("步骤 1", trace_id=trace_id)
logger.debug("步骤 2", trace_id=trace_id)
logger.success("处理完成", trace_id=trace_id)
```

### 4. 使用适当的日志级别

```python
# DEBUG - 详细的调试信息
logger.debug("执行 SQL: SELECT * FROM users")  # 自动使用 tag="query_database"

# INFO - 一般信息
logger.info("用户登录成功")  # 自动使用 tag="login"

# SUCCESS - 操作成功
logger.success("订单创建成功")  # 自动使用 tag="create_order"

# WARNING - 警告信息
logger.warning("重试次数过多", tag="retry")

# ERROR - 错误信息
logger.error("支付失败", tag="payment")

# CRITICAL - 严重错误
logger.critical("系统崩溃", tag="system")
```

### 5. 异常处理

```python
# ✅ 好的做法
try:
    result = risky_operation()
except SpecificException as e:
    logger.exception("操作失败", tag="operation")
    raise

# ❌ 不好的做法
try:
    result = risky_operation()
except Exception:
    logger.error("操作失败")  # 没有堆栈跟踪
```

## Tag 分类建议

根据不同的功能模块，建议使用以下 tag 分类：

### 基础设施层

```python
logger.debug("执行 SQL: SELECT * FROM users", tag="database")
logger.info("缓存命中", tag="cache")
logger.error("文件上传失败", tag="file")
logger.warning("连接超时", tag="connection")
```

### 业务层

```python
logger.info("用户登录成功", tag="auth")
logger.debug("验证权限", tag="auth")
logger.info("订单创建成功", tag="order")
logger.error("支付失败", tag="payment")
logger.warning("库存不足", tag="inventory")
```

### 通信层

```python
logger.info("WebSocket 连接建立", tag="websocket")
logger.debug("收到消息", tag="websocket")
logger.info("HTTP 请求处理", tag="request")
logger.error("邮件发送失败", tag="email")
```

### 系统层

```python
logger.warning("重试次数过多", tag="retry")
logger.error("参数验证失败", tag="validation")
logger.critical("系统崩溃", tag="system")
logger.error("未捕获的异常", tag="error_handler")
```

## 常见问题

### Q: 如何修改日志级别？

A: 编辑 `utils/log/logger.py` 中的 `level` 参数：

```python
_logger.add(
    sys.stdout,
    level="INFO",  # 改为 INFO、WARNING 等
)
```

### Q: 如何修改日志格式？

A: 修改 `_get_console_format()` 或 `_get_file_format()` 方法。

### Q: 日志文件会无限增长吗？

A: 不会。日志文件设置了自动轮转和压缩：
- 单个文件超过 500MB 时自动轮转
- 保留 7 天的日志（错误日志保留 30 天）
- 旧日志自动压缩为 zip 文件

### Q: 如何在异步代码中使用 trace_id？

A: `contextvars` 自动支持异步上下文，无需特殊处理：

```python
async def async_function():
    logger.set_trace_id("req-123")
    
    async def nested_function():
        # 自动继承 trace_id
        logger.info("嵌套函数中的日志")
    
    await nested_function()
```

### Q: 如何快速查找特定 tag 的日志？

A: 使用 `grep` 命令查询日志文件：

```bash
# 查看所有支付相关的日志
grep "\[payment\]" logs/webctp.log

# 查看所有错误日志
grep "\[payment\]" logs/webctp_error.log

# 查看特定请求的所有日志
grep "trace_id=req-123" logs/webctp.log

# 结合 tag 和 trace_id 查看
grep "trace_id=req-123" logs/webctp.log | grep "\[payment\]"

# 统计某个 tag 的日志数量
grep -c "\[database\]" logs/webctp.log

# 查看最近的 100 条支付日志
grep "\[payment\]" logs/webctp.log | tail -100
```

### Q: 如何为现有代码添加日志？

A: 在关键位置添加日志，根据需要指定 tag：

```python
# ✅ 好的做法
def process_payment(order_id: str, amount: float):
    logger.info(f"开始处理支付: {order_id}", tag="payment")
    
    try:
        # 验证金额
        if amount <= 0:
            logger.warning(f"无效金额: {amount}", tag="payment")
            raise ValueError("金额必须大于 0")
        
        # 调用支付接口
        result = call_payment_api(order_id, amount)
        logger.info(f"支付成功: {order_id}", tag="payment")
        return result
        
    except PaymentError as e:
        logger.error(f"支付失败: {e}", tag="payment")
        raise
    except Exception as e:
        logger.exception(f"支付异常: {e}", tag="payment")
        raise
```

### Q: Tag 是否是必需的？

A: 不是必需的。Tag 是可选的：

- 当需要对日志进行分类时，使用 tag
- 当不需要分类时，可以不指定 tag
- 日志仍然会被记录和输出，只是没有标签

```python
# 都是有效的用法
logger.info("消息")  # 没有 tag
logger.info("消息", tag="auth")  # 有 tag
```

### Q: 如何在生产环境中管理日志？

A: 建议的做法：

1. **使用统一的 tag 规范** - 团队内保持一致
2. **集中日志收集** - 使用 ELK Stack、Datadog 等
3. **结构化日志** - 便于分析和查询
4. **日志采样** - 在高流量场景中使用采样
5. **定期清理** - 清理旧的日志文件

## 性能考虑

- Logger 使用单例模式，全局只有一个实例
- 日志写入是异步的，不会阻塞主线程
- 建议在生产环境设置日志级别为 INFO 或 WARNING
- 定期清理 `logs/` 目录中的旧日志文件

## 相关文件

- `utils/log/logger.py` - 日志工具类实现
- `utils/log/__init__.py` - 日志模块导出
- `logs/` - 日志文件目录（自动创建）
