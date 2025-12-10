<p align="center">
  English |
  <a href="development_CN.md">简体中文</a>
</p>

# Development Documentation

## Table of contents

- [Project Overview](#project-overview)
- [Architecture Design](#architecture-design)

- [Development Environment Setup](#development-environment-setup)

- [Project Structure](#project-structure)

- [Development Guide](#development-guide)

- [Testing Guidelines](#testing-guidelines)

- [Frequently Asked Questions](#frequently-asked-questions)

## Project Overview

homalos-webctp is a CTP interface service based on FastAPI and WebSocket. It encapsulates the traditional CTP API into a WebSocket interface, making it easier for web applications to access futures trading systems.

### Technology Stack

- **Python 3.10+**: Programming language
- **FastAPI**: Web framework
- **WebSocket**: Real-time communication protocol
- **anyio**: Asynchronous I/O library
- **ctp api**: CTP Python Binding
- **PyYAML**: Configuration file parsing

## Architecture Design

### Overall Architecture

```
┌─────────────┐
│   Client    │ (Browser/Application)
└──────┬──────┘
       │ WebSocket
┌──────▼──────────────────────┐
│   FastAPI Application       │
│  (apps/md_app.py|td_app.py) │
└──────┬──────────────────────┘
       │
┌──────▼────────────────────────────────────────┐
│   Service Layer                               │
│  (services/base_client.py)                    │
│  - Asynchronous/Synchronous Boundary Handling │
│  - Message Queue Management                   │
│  - Request routing                            │
└──────┬────────────────────────────────────────┘
       │
┌──────▼──────────────────────┐
│   CTP Client Layer          │
│  (clients/md|td_client.py)  │
│  - CTP API Packaging        │
│  - Callback handling        │
└──────┬──────────────────────┘
       │
┌──────▼──────────────────────┐
│   CTP API (openctp-ctp)     │
└─────────────────────────────┘
```

### Core Design Patterns

#### 1. Template Method Pattern (BaseClient)

`BaseClient` defines the general process for client creation, while subclasses implement specific CTP client creation logic:

```python
class BaseClient(ABC):
    async def start(self, user_id, password):
        # General startup process
        self._client = self._create_ctp_client(user_id, password)
        # ...
    
    @abstractmethod
    def _create_ctp_client(self, user_id, password):
        # Subclasses implement specific client creation
        pass
```

#### 2. Asynchronous/Synchronous Boundary Handling

The CTP API is synchronous, while WebSocket is asynchronous; the boundary is handled through `anyio.to_thread.run_sync`.

```python
# Calling a synchronous CTP API in an asynchronous context
await anyio.to_thread.run_sync(self._client.connect)
```

#### 3. Message Queue Pattern

Use queues to decouple CTP callbacks and WebSocket sending:

```
CTP Callback → Queue → Background Task → WebSocket Send
```

## Development environment setup

### 1. Cloning project

```bash
git clone https://github.com/Homalos/homalos-webctp.git
cd homalos-webctp
```

### 2. Install dependencies

**Use UV (Recommended)**

```bash
# Synchronous Dependencies
uv sync
```

**Using pip**

```bash
pip install -e .
```

### 3. Configuration File

Copy the example configuration and modify it:

```bash
cp config.sample.yaml config_md.yaml
cp config.sample.yaml config_td.yaml
```

Edit the configuration file and fill in the correct information:

```yaml
TdFrontAddress: tcp://182.254.243.31:40001
MdFrontAddress: tcp://182.254.243.31:40011
BrokerID: "9999"
AuthCode: "0000000000000000"
AppID: simnow_client_test
Port: 8080
Host: 0.0.0.0
LogLevel: INFO
```

### 4. Start Service

```bash
# Market data service
python main.py --config=config_md.yaml --app_type=md

# Transaction services
python main.py --config=config_td.yaml --app_type=td
```

## Project Structure

### Project Structure Description

```reStructuredText
webctp/
├── apps/                  # Application Entry
│   ├── __init__.py
│   ├── md_app.py          # Market data service FastAPI application
│   └── td_app.py          # FastAPI application for trading services
│
├── clients/               # CTP Client Encapsulation
│   ├── __init__.py
│   ├── md_client.py       # Market data client (inherited from CThostFtdcMdSpi)
│   └── td_client.py       # Trading client (inherited from CThostFtdcTraderSpi)
│
├── services/              # Service layer
│   ├── __init__.py
│   ├── base_client.py     # Client base class (abstract class)
│   ├── md_client.py       # Market data service (inherited from BaseClient)
│   ├── td_client.py       # Transaction services (inherited from BaseClient)
│   └── connection.py      # WebSocket connection management
│
├── constants/             # Constant definition
│   ├── __init__.py
│   ├── call_errors.py     # Error code definition
│   └── constant.py        # Message type constants
│
├── model/                 # Data Model
│   ├── __init__.py
│   └── request.py         # Request data model
│
├── utils/                 # utility functions
│   ├── __init__.py
│   ├── config.py          # Configuration Management
│   ├── ctp_object_helper.py  # CTP object helper functions
│   └── math_helper.py     # Mathematical auxiliary functions
│
├── docs/                  # document
│   ├── md_protocol.md     # Market data protocol document
│   ├── td_protocol.md     # Transaction Agreement Document
│   └── development.md     # Development Documentation (This File)
│
├── main.py                # Main entrance
├── pyproject.toml         # Project configuration and dependencies
└── README.md              # Project Description
```

### Key document description

#### `services/base_client.py`

An abstract base class that provides:

- Client lifecycle management (start/stop/run)

- Message queue handling

- Asynchronous/synchronous boundary handling

- Public properties and methods

#### `services/td_client.py` & `services/md_client.py`

Specific service implementation:

- Inherit from `BaseClient`

- Implement abstract methods

- Handle specific business logic

- Request authentication and routing

#### `clients/td_client.py` & `clients/md_client.py`

CTP API Encapsulation:

- Inherit from the CTP Spi class

- Implement callback methods

- Encapsulate API calls

- Data transformation

## Development Guide

### Add new API interface

Let's take adding a new query interface as an example:

#### 1. Add constants to `constants/constant.py`

```python
class TdConstant(CommonConstant):
    # Request Method
    ReqQryNewApi = "ReqQryNewApi"
    
    # Response Type
    OnRspQryNewApi = "RspQryNewApi"
    
    # Request/Response Field
    QryNewApi = "QryNewApi"
    NewApiData = "NewApiData"
```

#### 2. Add API wrapper to `clients/td_client.py`

```python
def reqQryNewApi(self, request: dict[str, Any]) -> None:
    req, requestId = CTPObjectHelper.extract_request(
        request, 
        Constant.QryNewApi, 
        tdapi.CThostFtdcQryNewApiField
    )
    ret = self._api.ReqQryNewApi(req, requestId)
    self.method_called(Constant.OnRspQryNewApi, ret)

def OnRspQryNewApi(self, pData, pRspInfo, nRequestID, bIsLast):
    response = CTPObjectHelper.build_response_dict(
        Constant.OnRspQryNewApi, 
        pRspInfo, 
        nRequestID, 
        bIsLast
    )
    if pData:
        response[Constant.NewApiData] = {
            "Field1": pData.Field1,
            "Field2": pData.Field2,
            # ... Other fields
        }
    self.rsp_callback(response)
```

#### 3. Register the method in `services/td_client.py`

```python
def _init_call_map(self):
    # ... Other mappings
    self._call_map[Constant.ReqQryNewApi] = self._client.reqQryNewApi
```

#### 4. Update Protocol Documentation

Add interface descriptions to `docs/td_protocol.md`.

### Best Practices for Error Handling

#### 1. Use Uniform Error Codes

```python
from constants import CallError

# Error returned
response = {
    "MsgType": message_type,
    "RspInfo": CallError.get_rsp_info(404)
}
```

#### 2. Record Detailed Logs

```python
import logging

# Use appropriate logging levels
logging.debug("detailed debug information")
logging.info("general information")
logging.warning("warning information")
logging.error("error information")
logging.exception("exception information, including stack trace")
```

#### 3. Exception Handling

```python
try:
    # Code that may cause errors
    result = await some_operation()
except SpecificException as e:
    logging.exception(f"Operation failed: {e}")
```

### Reconnection Control

The market data client implements a reconnection control mechanism to prevent excessive reconnections caused by configuration errors:

```python
# clients/md_client.py
def OnFrontConnected(self):
    current_time = time.time()
    if current_time - self._last_connect_time < self._reconnect_interval:
        self._reconnect_count += 1
        if self._reconnect_count > self._max_reconnect_attempts:
            logging.error("Exceeding the maximum number of reconnections")
            return
    else:
        self._reconnect_count = 0
    
    self._last_connect_time = current_time
    self.login()
```

## Testing Guidelines

### Unit Testing

(To be supplemented)

### Integration Testing

Testing using the SimNow emulation environment:

1. Register a SimNow account

2. Configure the test environment

3. Run the service

4. Test using a WebSocket client

### Testing Tools

- **Apifox**: API testing tool

- **wscat**: WebSocket command-line tool

- **Browser developer tools**: WebSocket debugging

## Frequently Asked Questions

### Q: How to handle CTP flow control limitations?

A: CTP has request frequency limits. Recommendations:

- Control request frequency

- Implement request queues

- Handle flow control error codes (-2, -3)

### Q: What to do after a WebSocket connection is lost?

A:

- Implement automatic reconnection on the client side

- The server handles `WebSocketDisconnect` in `connection.py`

- Clean up resources and release CTP connections

### Q: How to debug CTP callbacks?

A:

- Set the log level to DEBUG

- Add logging to the callback method

- Use the CTP stream file to view detailed information

### Q: Production deployment considerations?

A:

- Deploy after thorough testing

- Configure an appropriate log level

- Monitor service status

- Implement a fault recovery mechanism

- Note the CTP connection limit

## Contribution Guidelines

Welcome to contribute code! Please follow these steps:

1. Fork the project

2. Create a feature branch

3. Commit changes

4. Push to the branch

5. Create a Pull Request

### Code Review Checklist

- Code style conforms to PEP 8

- Add necessary type annotations

- Include appropriate error handling

- Update relevant documentation

- Pass tests

## License

Please refer to the LICENSE file in the project root directory.

## Contact Information

- Project homepage: https://github.com/Homalos/homalos-webctp