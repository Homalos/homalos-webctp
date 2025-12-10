<p align="center">
  <font size="5px">✨ A CTP service providing a WebSocket interface, developed based on the Python CTP API✨</font>
</p>

<p align="center">
  <a href="https://qun.qq.com/universal-share/share?ac=1&authKey=dzGDk%2F%2Bpy%2FwpVyR%2BTrt9%2B5cxLZrEHL793cZlFWvOXuV5I8szMnOU4Wf3ylap7Ph0&busi_data=eyJncm91cENvZGUiOiI0NDYwNDI3NzciLCJ0b2tlbiI6IlFrM0ZhZmRLd0xIaFdsZE9FWjlPcHFwSWxBRFFLY2xZbFhaTUh4K2RldisvcXlBckZ4NVIrQzVTdDNKUFpCNi8iLCJ1aW4iOiI4MjEzMDAwNzkifQ%3D%3D&data=O1Bf7_yhnvrrLsJxc3g5-p-ga6TWx6EExnG0S1kDNJTyK4sV_Nd9m4p-bkG4rhj_5TdtS5lMjVZRBv4amHyvEA&svctype=4&tempid=h5_group_info"><img alt="Group#1" title="Group#1"
src="https://img.shields.io/badge/Group%231-Join-blue"/></a>
</p>

<p align="center">
  English |
  <a href="README_CN.md">简体中文</a>
</p>

---

* [Overview](#Overview)
* [Installation and Operation](#Installation and Operation)
    * [Environment Dependencies](#Environment Dependencies)
    * [Environment Setup](#Environment Setup)
    * [Run](#Run)
* [Request Example](#Request Example)
* [Protocol](#Protocol)
    * [General Protocol Format](#General Protocol Format)
    * [Explanation of Some General Error Codes](#Explanation of Some General Error Codes)
    * [Detailed API Documentation](#Detailed API Documentation)
* [Project Structure](#Project Structure)
* [Architecture Description](#Architecture Description)
* [Test](#Test)
* [Other Notes](#Other Notes)

---

## Overview

homalos-webctp is a CTP service based on the Python CTP API that provides a WebSocket interface. It aims to provide an interface for the operation and development of futures quantitative trading.

- **Current Status:** Under Development

## Installation and Operation

### Environment Dependencies

- **Python** ：3.13

- **Tools: UV**

- **CTP API**：6.7.10

### Environment Setup

1. Environment Preparation

   Install UV lamp; UV lamps are recommended.

2. <details>
   <summary>👈Method 1: System-wide installation. This method is recommended. Other Python projects can also use UV management.</summary>


   Install on Windows system

   ```bash
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

   Installing on a Linux system

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
   </details>

   <details>
   <summary>👈Method 2: Install on an existing Python installation</summary>
   Choose one of the two methods above. If method one is executed, method two will be skipped. The UV (unique visitors) for this installation method can only be used in this Python environment.

   ```bash
   pip install uv
   ```
   </details>

3. Install Python

   If you selected to install UV globally in step 1, you need to perform this step; otherwise, skip it.

   ```bash
   uv python install 3.13
   ```

   <details>
   <summary>👈Tips</summary>
   This method installs Python globally, isolating it from the Python environment in the project, and does not affect it.
   </details>

4. Cloning project

   ```bash
   git clone https://github.com/Homalos/homalos-webctp.git
   cd homalos-webctp
   ```

5. Install dependencies

   ```bash
   uv sync
   ```

   Based on the information in pyproject.toml, automatically create a Python virtual environment named .venv in the current project root directory and install all dependencies.

6. Configuration

   <details>
   <summary>👈Configuration Reference</summary>

   
   > :pushpin:The configuration example is config.example.yaml. The example uses the front-end address for market data and trading. The default configuration is the SimNow 7x24 environment. For more detailed information on the SimNow environment, please refer to [SimNow Official Website](https://www.simnow.com.cn/product.action) and [OpenCTP Environment Monitoring](http://121.37.80.177). You can change it to other trading environment that supports CTPAPI (official implementation) as needed. 
   >
   > :pushpin: SimNow 7x24 environment：
   >
   > <table>
   > <tr>
   > 	<th colspan="3">Front Information</th>
   > </tr>
   > <tr>
   > 	<td>BrokerID</td>
   > 	<td>9999</td>
   > 	<td>Brokerage ID</td>
   > </tr>
   > <tr>
   > 	<td>Trade Front</td>
   > 	<td>182.254.243.31:40001</td>
   > 	<td rowspan="2">A transparent front-end system uses a monitoring center to generate keys.</td>
   > </tr>
   > <tr>
   > 	<td>Market Front</td>
   > 	<td>182.254.243.31:40011</td>
   > </tr>
   > <tr>
   > 	<td rowspan="2">Transaction phase (service time)</td>
   > 	<td>Trading days, 16:00 to 09:00 the following day</td>
   > 	<td></td>
   > </tr>
   > <tr>
   > 	<td>On non-trading days, from 16:00 to 12:00 the following day</td>
   > 	<td></td>
   > </tr>
   > </table>
   >
   >
   > - This environment is only for CTP API development enthusiasts and is only provided for users' CTP API testing needs. It does not provide other services such as settlement.
   >
   > - Newly registered users will need to wait until the third trading day to use the second environment.
   >
   > - The account, funds, and warehouses remain consistent with the previous trading day's environment.
   >
   > :pushpin:  SimNow Non-7x24 environment：
   >
   > <table>
   > <tr>
   > 	<th colspan="4">Font Information</th>
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
   > 	<td colspan="3">0000000000000000（16 zeros）</td>
   > </tr>
   > <tr>
   > 	<td rowspan="2">Group 1</td>
   > 	<td>Trade Front</td>
   > 	<td>182.254.243.31:30001</td>
   > 	<td rowspan="6">A transparent front-end system uses a monitoring center to generate keys.</td>
   > </tr>
   > <tr>
   > 	<td>Market Front</td>
   > 	<td>182.254.243.31:30012</td>
   > </tr>
   > <tr>
   > 	<td rowspan="2">Group 2</td>
   > 	<td>Trade Front</td>
   > 	<td>182.254.243.31:30002</td>
   > </tr>
   > <tr>
   > 	<td>Market Front</td>
   > 	<td>182.254.243.31:30012</td>
   > </tr>
   > <tr>
   > 	<td rowspan="2">Group 3</td>
   > 	<td>Trade Front</td>
   > 	<td>182.254.243.31:30003</td>
   > </tr>
   > <tr>
   > 	<td>Market Front</td>
   > 	<td>182.254.243.31:30013</td>
   > </tr>
   > <tr>
   > 	<td>Transaction phase (service time)</td>
   > 	<td colspan="3">It should be consistent with the actual production environment.</td>
   > </tr>
   > </table>
   >
   >
   > - Supports options from the Shanghai Futures Exchange, the National Energy Exchange, the China Financial Futures Exchange, the Guangzhou Futures Exchange, the Zhengzhou Commodity Exchange, and the Dalian Commodity Exchange.
   >
   > - After user registration, the default APPID is simnow_client_test, and the authentication code is 0000000000000000 (16 zeros). Terminal authentication is enabled by default, but programmatic users can choose not to enable terminal authentication for access.
   >
   > - Trading instruments: All futures instruments traded on the six exchanges, as well as all options instruments traded on the Shanghai Futures Exchange, the Energy Exchange, the China Financial Futures Exchange, and the Guangzhou Futures Exchange, and some options instruments traded on the Zhengzhou Commodity Exchange and the Dalian Commodity Exchange.
   > - Account funds: Initial capital of 20 million, supports deposits, up to three times per day.
>
   > 见 [SimNow官网](https://www.simnow.com.cn/product.action)
> </details>

   Create your own market data configuration file: config_md.yaml

   ```yaml
   TdFrontAddress: tcp://182.254.243.31:40001	# Trade Front Address
   MdFrontAddress: tcp://182.254.243.31:40011	# Market Front Address
   BrokerID: "9999"							# Brokerage ID
   AuthCode: "0000000000000000"				# Authentication code
   AppID: simnow_client_test					# Application ID
   Port: 8080									# the listening port, default 8080
Host: 127.0.0.1								# the bind ip address, default 127.0.0.1
   LogLevel: INFO								# NOTSET, DEBUG, INFO, WARN, ERROR, CRITICAL
   ```

   Create your own trading configuration file config_td.yaml:
   ```yaml 
   TdFrontAddress: tcp://182.254.243.31:40001	# Trade Front Address
   MdFrontAddress: tcp://182.254.243.31:40011	# Market Front Address
   BrokerID: "9999"							# Brokerage ID
   AuthCode: "0000000000000000"				# Authentication code
   AppID: simnow_client_test					# Application ID
   Port: 8081									# the listening port, default 8081
   Host: 127.0.0.1								# the bind ip address, default 127.0.0.1
   LogLevel: INFO								# NOTSET, DEBUG, INFO, WARN, ERROR, CRITICAL
   ```

### Run

```bash
# Activate the virtual environment in the project root directory. Deactivating it will use the system default Python environment instead of the one required by the project.
.venv\Scripts\activate
# Start trading service
python main.py --config=./config/config_td.yaml --app_type=td
# Start market data service
python main.py --config=./config/config_md.yaml --app_type=md
```

## Request Example

> :pushpin: See [md_protocol.md](docs/md_protocol.md)、[td_protocol.md](docs/td_protocol.md)

### Partial Examples

The example is based on the SimNow Telecom 1 environment. Data may differ in different environments, and the example data below may not be universally applicable. Adjustments should be made according to your environment.

Market data link: ws://127.0.0.1:8080/md/

Trading link: ws://127.0.0.1:8081/td/

<details>
<summary>Log in</summary>

request

```json
{
  "MsgType": "ReqUserLogin",
  "ReqUserLogin": {
    "UserID": "028742",
    "Password": "123456"
  }
}
```

response

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
<summary>Subscribe to market data</summary>

request

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

response

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

In-depth market response

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
<summary>Cancel subscription market data</summary>

request

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

response

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

## Protocol

### General Protocol Format

``` python
# request
{
  "MsgType": "{method_name}",
  "{request_field}": {
    "filed1": {value1},
    "...": "...",
    "fieldn": {valuen}
  },
  "RequestID": 1
}

# response
{
    "MsgType": "{rsp_of_method}",
    "RspInfo": {
        "ErrorID": 0,
        "ErrorMsg": "OK"
    },
    "IsLast": true,
    "RequestID": 1
    "{response_filed}": {response_body}  # Please refer to the detailed documentation for details.
}
```

### Explanation of Some General Error Codes

<details>
<summary>👈</summary>

```bash
ErrorID="-400" ErrorMsg="Incorrect parameters"
ErrorID="-401" ErrorMsg="Not logged in"
ErrorID="-404" ErrorMsg="This method has not yet been implemented."
ErrorID="-1" ErrorMsg="CTP:Request failed"
ErrorID="-2" ErrorMsg="CTP:Unprocessed requests exceed the number of licenses"
ErrorID="-3" ErrorMsg="CTP:The number of requests sent per second exceeded the number of licenses."
ErrorID="0" ErrorMsg="CTP:correct"
ErrorID="1" ErrorMsg="CTP:Not in synchronized state"
ErrorID="2" ErrorMsg="CTP:Inconsistent session information"
ErrorID="3" ErrorMsg="CTP:Invalid login"
ErrorID="4" ErrorMsg="CTP:User inactive"
ErrorID="5" ErrorMsg="CTP:Duplicate logins"
ErrorID="6" ErrorMsg="CTP:Not logged in yet"
ErrorID="7" ErrorMsg="CTP:Not initialized yet"
ErrorID="8" ErrorMsg="CTP:Pre-inactive"
ErrorID="9" ErrorMsg="CTP:No permission required"
ErrorID="10" ErrorMsg="CTP:Change other people's passwords"
ErrorID="11" ErrorMsg="CTP:User not found"
ErrorID="12" ErrorMsg="CTP:The brokerage firm could not be found."
ErrorID="13" ErrorMsg="CTP:Cannot find investors"
ErrorID="14" ErrorMsg="CTP:Original password does not match"
ErrorID="15" ErrorMsg="CTP:The order field is incorrect."
ErrorID="16" ErrorMsg="CTP:Contract not found"
```
</details>

### Detailed API Documentation

[Transaction Service Agreement Document](./docs/td_protocol.md)

[Market Data Service Agreement Document](./docs/md_protocol.md)

## Project Structure

```reStructuredText
homalos-webctp/
├── 📁 config/					# Project Configuration
├── 📁 docs/					# Project Documentation
├── 📁 libs/					# Third-party libraries, including the original CTP dynamic library
├── 📁 src/						# Core source code
├── 📁 tests/					# test script
├── 📁 CHANGELOG.md				# Historical Updates
├── 📁 LICENSE.txt				# License file
├── 📁 README.md				# Documentation
├── 📁 main.py					# Project entrance
├── 📁 pyproject.toml			# Project configuration files, dependencies managed by UV.
└── 📁 uv.lock					# UV file lock, managed by UV
```

## Architecture Description

### Three-Tier Architecture

1. **Application Layer (apps/)**: FastAPI WebSocket endpoint
2. **Service Layer (services/)**: Asynchronous/synchronous boundary handling, message routing
3. **Client Layer (clients/): CTP API Encapsulation**

### Core components

- **BaseClient**: An abstract base class that provides common client management logic.
- **TdClient/MdClient (services)**: Handling WebSocket messages and interactions with CTP clients
- **TdClient/MdClient (clients)**: Encapsulate CTP API calls

## Test

It is recommended to conduct thorough testing in the SimNow simulation environment before connecting to the production environment.

For more detailed information, please refer to the [Development Documentation](./docs/development.md).

## Other Notes

* Due to limited resources, only a simple test of the SimNow platform was conducted. Please conduct thorough testing yourself before integrating it into the production environment.
* Users are solely responsible for any consequences arising from real-money trading.
