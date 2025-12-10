<p align="center">
  English |
  <a href="logger_guide_CN.md">简体中文</a>
</p>

# Logger Guide

## Overview

The homalos-webctp project uses a `Logger` utility class based on `loguru`, providing powerful logging capabilities.

### Key Features

- ✅ **Tag Classification**: Categorize logs using the `tag` parameter
- ✅ **Trace ID Tracking**: Support request-level tracking IDs
- ✅ **Multiple Output Targets**: Output to console and file simultaneously
- ✅ **Automatic Rotation**: Log files are automatically rotated and compressed
- ✅ **Thread Safety**: Supports multi-threaded and asynchronous operations
- ✅ **Detailed Stack Traces**: Includes full stack traces on exceptions

## Tag Explanation

### What is a Tag?

A `tag` is a **classification label** for logs, used for:

- **Log Classification** - Quickly identify which module or feature a log comes from
- **Log Filtering** - Quickly find specific types of logs in log files
- **Issue Tracking** - Track the execution flow of specific features via tags
- **Performance Analysis** - Statistics on log quantity and performance metrics for different modules

### Common Tag Usage Scenes

| Tag | Usage Scenario | Example |
|-----|----------------|---------|
| `auth` | Authentication and Authorization | Login, Permission Verification |
| `database` | Database Operations | Query, Insert, Update, Delete |
| `websocket` | WebSocket Communication | Connect, Disconnect, Message Send/Receive |
| `request` | HTTP Request Processing | Request Receive, Response Send |
| `payment` | Payment Related | Payment Processing, Refunds |
| `order` | Order Related | Order Creation, Update, Cancellation |
| `cache` | Cache Operations | Cache Hit, Cache Update |
| `email` | Email Sending | Email Sending, Template Rendering |
| `file` | File Operations | Upload, Download, Delete |
| `connection` | Connection Management | Connection Establish, Disconnect |
| `retry` | Retry Logic | Retry Count, Backoff Strategy |
| `validation` | Data Validation | Parameter Validation, Business Rule Validation |

### Tag Naming Conventions

1. **Use Lowercase** - `auth`, `database`, `websocket`
2. **Use Underscores** - `user_auth`, `db_query`, `ws_connect`
3. **Keep it Concise** - Usually 1-2 words
4. **Indicate Integration/Module** - Rather than log level
5. **Consistency** - Use the same tag for the same functionality

## Quick Start

### Basic Usage

```python
from utils import logger

# No tag specified - Log without label
logger.debug("Debug Info")
logger.info("Info Message")
logger.success("Success Message")
logger.warning("Warning Message")
logger.error("Error Message")
logger.critical("Critical Error")

# Tag specified - Log with label
logger.info("Info Message", tag="auth")
logger.error("Error Message", tag="database")
logger.success("Success Message", tag="payment")
```

### Using Trace ID

Logger supports three ways to use `trace_id`:

#### Method 1: Add trace_id to a single log

```python
from utils import logger

# Automatically generate UUID as trace_id
logger.info("Processing Request", trace_id=True)
logger.info("Querying Database", tag="database", trace_id=True)

# Specify trace_id
logger.info("Processing Request", trace_id="req-12345")
logger.error("Database Error", tag="database", trace_id="req-12345")
```

**Output:**
```
INFO     | [trace_id=550e8400-e29b-41d4-a716-446655440000] Processing Request
INFO     | [trace_id=550e8400-e29b-41d4-a716-446655440001] [database] Querying Database
INFO     | [trace_id=req-12345] Processing Request
ERROR    | [trace_id=req-12345] [database] Database Error
```

#### Method 2: Set Global trace_id

```python
from utils import logger

# Set global trace_id
logger.set_trace_id("req-12345")
logger.info("Processing Request", tag="request")
logger.info("Querying Database", tag="database")

# Clear trace_id
logger.clear_trace_id()
```

#### Method 3: Automatically Generate Global trace_id

```python
from utils import logger

# Automatically generate UUID as global trace_id
trace_id = logger.set_trace_id()
logger.info("Processing Request", tag="request")
logger.info("Querying Database", tag="database")

# Clear trace_id
logger.clear_trace_id()
```

### Exception Logging

```python
from utils import logger

try:
    result = 1 / 0
except Exception as e:
    logger.exception("An exception occurred", tag="error")
    # Automatically records full stack trace
```

## Practical Scenarios

### 1. WebSocket Connection Handling

```python
from fastapi import WebSocket
from utils import logger

async def websocket_endpoint(websocket: WebSocket):
    try:
        await websocket.accept()
        # Add trace_id for connection establishment event
        logger.info("WebSocket Connection Established", tag="connection", trace_id=True)
        
        while True:
            data = await websocket.receive_text()
            # Add trace_id for every message
            logger.debug(f"Received data: {data}", tag="websocket", trace_id=True)
            
            # Process data
            result = process_data(data)
            await websocket.send_text(result)
            logger.debug("Sent Response", tag="websocket", trace_id=True)
            
    except Exception as e:
        logger.exception("WebSocket Processing Exception", tag="connection", trace_id=True)
    finally:
        logger.info("WebSocket Connection Closed", tag="connection", trace_id=True)
```

### 2. Database Operations

```python
from utils import logger

def query_user(user_id: int):
    logger.debug(f"Querying User: {user_id}", tag="database")
    
    try:
        # Execute query
        user = db.query(User).filter(User.id == user_id).first()
        
        if user:
            logger.info(f"User Query Successful: {user.name}", tag="database")
            return user
        else:
            logger.warning(f"User Not Found: {user_id}", tag="database")
            return None
            
    except Exception as e:
        logger.exception(f"User Query Exception: {user_id}", tag="database")
        raise
```

### 3. Business Logic Processing

```python
from utils import logger

async def process_order(order_id: str):
    logger.info(f"Start Processing Order: {order_id}", tag="order")
    
    try:
        # Validate order
        order = validate_order(order_id)
        logger.debug("Order Validation Passed", tag="order")
        
        # Payment processing
        payment_result = await process_payment(order)
        logger.info("Payment Processing Completed", tag="payment")
        
        # Shipping
        shipping_result = await create_shipping(order)
        logger.success("Order Processing Completed", tag="order")
        
        return shipping_result
        
    except ValidationError as e:
        logger.warning(f"Order Validation Failed: {e}", tag="order")
        raise
    except PaymentError as e:
        logger.error(f"Payment Failed: {e}", tag="payment")
        raise
    except Exception as e:
        logger.exception("Order Processing Exception", tag="order")
        raise
```

### 4. Authentication and Authorization

```python
from utils import logger

def authenticate_user(username: str, password: str):
    logger.debug(f"Authenticating User: {username}", tag="auth")
    
    try:
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            logger.warning(f"User Not Found: {username}", tag="auth")
            return None
        
        if not verify_password(password, user.password_hash):
            logger.warning(f"Incorrect Password: {username}", tag="auth")
            return None
        
        logger.success(f"User Authentication Successful: {username}", tag="auth")
        return user
        
    except Exception as e:
        logger.exception(f"Authentication Exception: {username}", tag="auth")
        raise
```

## Log Output Examples

### Console Output

```
DEBUG    | utils.log.logger:debug:189 | [trace_id=req-12345] [database] Querying User: 123
INFO     | services.td_client:call:67 | [trace_id=req-12345] [request] Processing Request
SUCCESS  | services.td_client:call:75 | [trace_id=req-12345] [request] Order Processing Completed
WARNING  | utils.log.logger:warning:225 | [trace_id=req-12345] [auth] Incorrect Password: user123
ERROR    | services.connection:run:45 | [trace_id=req-12345] [connection] WebSocket Connection Exception
```

### File Output

Log file location: `logs/` directory

- `webctp.log` - All logs (DEBUG and above)
- `webctp_error.log` - Error logs only (ERROR and above)

File Format:
```
2025-12-03 14:30:45.123 | DEBUG    | utils.log.logger:debug:189 | [trace_id=req-12345] [database] Querying User: 123
2025-12-03 14:30:46.456 | INFO     | services.td_client:call:67 | [trace_id=req-12345] [request] Processing Request
2025-12-03 14:30:47.789 | SUCCESS  | services.td_client:call:75 | [trace_id=req-12345] [request] Order Processing Completed
```

## API Reference

### Logger Class

#### Log Methods

```python
# All log methods support tag and trace_id parameters
logger.debug(message: str, tag: Optional[str] = None, trace_id: Optional[str] = None, **kwargs) -> None
logger.info(message: str, tag: Optional[str] = None, trace_id: Optional[str] = None, **kwargs) -> None
logger.success(message: str, tag: Optional[str] = None, trace_id: Optional[str] = None, **kwargs) -> None
logger.warning(message: str, tag: Optional[str] = None, trace_id: Optional[str] = None, **kwargs) -> None
logger.error(message: str, tag: Optional[str] = None, trace_id: Optional[str] = None, **kwargs) -> None
logger.critical(message: str, tag: Optional[str] = None, trace_id: Optional[str] = None, **kwargs) -> None
logger.exception(message: str, tag: Optional[str] = None, trace_id: Optional[str] = None, **kwargs) -> None

# trace_id parameter explanation:
# - True: Automatically generate UUID
# - str: Use specified trace_id
# - None/False: Do not add trace_id
```

#### Trace ID Methods

```python
# Generate unique trace_id (UUID)
trace_id = logger.generate_trace_id() -> str

# Set global trace_id (automatically generated if not specified)
trace_id = logger.set_trace_id(trace_id: Optional[str] = None) -> str

# Get current global trace_id
logger.get_trace_id() -> Optional[str]

# Clear global trace_id
logger.clear_trace_id() -> None
```

## Synergy of Tag and Trace ID

The combination of `tag` and `trace_id` is very powerful for quickly locating and tracking issues:

```python
# trace_id is used to track the full flow of a single request
# tag is used to quickly locate the module where the issue is

# View all logs for a specific request
# grep "trace_id=req-123" logs/webctp.log

# View all issues for a specific module
# grep "\[payment\]" logs/webctp_error.log

# View logs for a specific request in a specific module
# grep "trace_id=req-123" logs/webctp.log | grep "\[payment\]"
```

### Practical Application Example

**Tracking the full flow of a request:**

```python
# All related logs carry trace_id and corresponding tag
with logger.trace():  # Automatically generate trace_id
    logger.info("Received Order Request", tag="request")
    
    # Database operations
    logger.debug("Querying User Info", tag="database")
    logger.debug("Querying Order Items", tag="database")
    
    # Payment processing
    logger.info("Calling Payment Interface", tag="payment")
    logger.success("Payment Successful", tag="payment")
    
    # Order update
    logger.info("Updating Order Status", tag="order")
    logger.success("Order Processing Completed", tag="order")
```

**Log Output Example:**
```
INFO     | [trace_id=abc-123] [request] Received Order Request
DEBUG    | [trace_id=abc-123] [database] Querying User Info
DEBUG    | [trace_id=abc-123] [database] Querying Order Items
INFO     | [trace_id=abc-123] [payment] Calling Payment Interface
SUCCESS  | [trace_id=abc-123] [payment] Payment Successful
INFO     | [trace_id=abc-123] [order] Updating Order Status
SUCCESS  | [trace_id=abc-123] [order] Order Processing Completed
```

## Best Practices

### 1. When to use Tag

```python
# ✅ Good Practice: Use tag where classification is needed

# Authentication related
logger.info("User Login Successful", tag="auth")
logger.warning("Login Failed", tag="auth")

# Database related
logger.debug("Executing Query", tag="database")
logger.error("Database Connection Failed", tag="database")

# Payment related
logger.info("Payment Processing Started", tag="payment")
logger.success("Payment Successful", tag="payment")

# ✅ Good Practice: Tag can be omitted when classification is not needed
logger.info("System Startup")
logger.debug("Processing Completed")
```

### 2. Use Meaningful Tags

```python
# ✅ Good Practice
logger.error("Database Connection Failed", tag="database")
logger.warning("Low Cache Hit Rate", tag="cache")
logger.info("Order Created Successfully", tag="order")

# ❌ Bad Practice
logger.error("Database Connection Failed", tag="error")  # tag should indicate functional module
logger.warning("Low Cache Hit Rate", tag="warning")  # tag should not be log level
logger.info("Order Created Successfully", tag="success")  # tag should not be operation result
```

### 3. Using trace_id Parameter

```python
# ✅ Best Practice: Add trace_id parameter for logs that need tracking
def process_payment(order_id: str):
    # Add trace_id for key operations
    logger.info(f"Start Processing Payment: {order_id}", tag="payment", trace_id=True)
    
    try:
        # Validation
        logger.debug("Validating Order", tag="payment", trace_id=True)
        
        # Processing
        result = call_payment_api(order_id)
        logger.success("Payment Successful", tag="payment", trace_id=True)
        return result
        
    except Exception as e:
        logger.exception("Payment Failed", tag="payment", trace_id=True)
        raise

# ✅ Good Practice: Use the same trace_id for related logs
trace_id = logger.generate_trace_id()
logger.info("Start Processing", trace_id=trace_id)
logger.debug("Step 1", trace_id=trace_id)
logger.debug("Step 2", trace_id=trace_id)
logger.success("Processing Completed", trace_id=trace_id)
```

### 4. Using Appropriate Log Levels

```python
# DEBUG - Detailed debug info
logger.debug("Executing SQL: SELECT * FROM users")  # Automatically uses tag="query_database"

# INFO - General info
logger.info("User Login Successful")  # Automatically uses tag="login"

# SUCCESS - Operation success
logger.success("Order Created Successfully")  # Automatically uses tag="create_order"

# WARNING - Warning info
logger.warning("Too Many Retries", tag="retry")

# ERROR - Error info
logger.error("Payment Failed", tag="payment")

# CRITICAL - Critical error
logger.critical("System Crash", tag="system")
```

### 5. Exception Handling

```python
# ✅ Good Practice
try:
    result = risky_operation()
except SpecificException as e:
    logger.exception("Operation Failed", tag="operation")
    raise

# ❌ Bad Practice
try:
    result = risky_operation()
except Exception:
    logger.error("Operation Failed")  # No stack trace
```

## Tag Classification Suggestions

Depending on different functional modules, the following tag classifications are recommended:

### Infrastructure Layer

```python
logger.debug("Executing SQL: SELECT * FROM users", tag="database")
logger.info("Cache Hit", tag="cache")
logger.error("File Upload Failed", tag="file")
logger.warning("Connection Timeout", tag="connection")
```

### Business Layer

```python
logger.info("User Login Successful", tag="auth")
logger.debug("Verifying Permissions", tag="auth")
logger.info("Order Created Successfully", tag="order")
logger.error("Payment Failed", tag="payment")
logger.warning("Insufficient Inventory", tag="inventory")
```

### Communication Layer

```python
logger.info("WebSocket Connection Established", tag="websocket")
logger.debug("Message Received", tag="websocket")
logger.info("HTTP Request Processing", tag="request")
logger.error("Email Sending Failed", tag="email")
```

### System Layer

```python
logger.warning("Too Many Retries", tag="retry")
logger.error("Parameter Validation Failed", tag="validation")
logger.critical("System Crash", tag="system")
logger.error("Uncaught Exception", tag="error_handler")
```

## Common Questions

### Q: How to change the log level?

A: Edit the `level` parameter in `utils/log/logger.py`:

```python
_logger.add(
    sys.stdout,
    level="INFO",  # Change to INFO, WARNING, etc.
)
```

### Q: How to change the log format?

A: Modify the `_get_console_format()` or `_get_file_format()` methods.

### Q: Will the log file grow infinitely?

A: No. Log files are set to automatically rotate and compress:
- Automatically rotates when a single file exceeds 500MB
- Keeps logs for 7 days (error logs for 30 days)
- Old logs are automatically compressed into zip files

### Q: How to use trace_id in asynchronous code?

A: `contextvars` automatically supports asynchronous contexts, no special handling is required:

```python
async def async_function():
    logger.set_trace_id("req-123")
    
    async def nested_function():
        # Automatically inherits trace_id
        logger.info("Log in nested function")
    
    await nested_function()
```

### Q: How to quickly find logs with a specific tag?

A: Use `grep` command to query log files:

```bash
# View all payment related logs
grep "\[payment\]" logs/webctp.log

# View all error logs
grep "\[payment\]" logs/webctp_error.log

# View all logs for a specific request
grep "trace_id=req-123" logs/webctp.log

# Combine tag and trace_id view
grep "trace_id=req-123" logs/webctp.log | grep "\[payment\]"

# Count logs for a specific tag
grep -c "\[database\]" logs/webctp.log

# View the last 100 payment logs
grep "\[payment\]" logs/webctp.log | tail -100
```

### Q: How to add logs to existing code?

A: Add logs at key locations, specifying tags as needed:

```python
# ✅ Good Practice
def process_payment(order_id: str, amount: float):
    logger.info(f"Start Processing Payment: {order_id}", tag="payment")
    
    try:
        # Validate amount
        if amount <= 0:
            logger.warning(f"Invalid Amount: {amount}", tag="payment")
            raise ValueError("Amount must be greater than 0")
        
        # Call payment interface
        result = call_payment_api(order_id, amount)
        logger.info(f"Payment Successful: {order_id}", tag="payment")
        return result
        
    except PaymentError as e:
        logger.error(f"Payment Failed: {e}", tag="payment")
        raise
    except Exception as e:
        logger.exception(f"Payment Exception: {e}", tag="payment")
        raise
```

### Q: Is Tag mandatory?

A: No. Tag is optional:

- When you need to classify logs, use tag
- When classification is not needed, you can omit tag
- Logs will still be recorded and output, just without a label

```python
# Both are valid usages
logger.info("Message")  # No tag
logger.info("Message", tag="auth")  # With tag
```

### Q: How to manage logs in production?

A: Recommended practices:

1. **Use unified tag standards** - Maintain consistency within the team
2. **Centralized Log Collection** - Use ELK Stack, Datadog, etc.
3. **Structured Logs** - Facilitate analysis and querying
4. **Log Sampling** - Use sampling in high-traffic scenarios
5. **Regular Cleanup** - Clean up old log files

## Performance Considerations

- Logger uses the singleton pattern, only one instance globally
- Log writing is asynchronous and will not block the main thread
- It is recommended to set the log level to INFO or WARNING in production environments
- Regularly clean up old log files in the `logs/` directory

## Related Files

- `utils/log/logger.py` - Logger utility class implementation
- `utils/log/__init__.py` - Log module export
- `logs/` - Log file directory (automatically created)
