# homalos-webctp

homalos-webctp 是一个基于 CTP API 开发的提供 websocket 接口的 CTP 服务。

---

* [安装及运行](#安装及运行)
    * [环境搭建](#环境搭建)
    * [运行](#运行)
* [请求示例](#请求示例)
* [协议](#协议)
    * [通用协议格式](#通用协议格式)
    * [部分通用错误码说明](#部分通用错误码说明)
* [开发说明](#开发说明)
* [其他说明](#其他说明)

---

## 安装及运行

### 环境搭建

1. 准备 Python 环境(**建议 3.13，推荐使用 UV，如果你熟悉 UV 可跳过步骤1**)

    - 安装 UV(系统中全局安装，推荐此种方式，其他 Python 项目也可以使用 UV 管理)

      在 Windows 系统

      ```bash
      powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
      ```

      在 Linux 系统

      ```bash
      curl -LsSf https://astral.sh/uv/install.sh | sh
      ```
    - 将 UV 安装在已有的 Python 环境中(和上面方式二选一，如果执行了上一步，则这一步跳过。此种方式 UV 只能在这一个 Python 环境中使用)
      ```bash
      pip install uv
      ```

2. 使用 UV 全局安装 Python(**如果在步骤1中选择了全局安装 UV，则需要执行这一步**)
   
   ```bash
   uv python install 3.13
   ```
   
   Tips：全局安装的 Python 与项目中的 Python 环境是隔离的，互不影响
   
3. 克隆 homalos-webctp

   ```bash
   git clone https://github.com/Homalos/homalos-webctp.git
   cd homalos-webctp
   ```

4. 安装依赖

   ```bash
   uv sync
   ```

   根据 pyproject.toml 中的信息，自动在当前项目根目录下创建名为 .venv 的 Python 虚拟环境及所有依赖安装

5. 配置

   > :pushpin: 项目使用 pyproject.toml 管理依赖，默认使用 CTP 版本为 6.7.10
   >
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
   > 该环境仅服务于CTP API开发爱好者，仅为用户提供CTP API测试需求，不提供结算等其它服务。
   >
   > 新注册用户，需要等到第三个交易日才能使用第二套环境。
   >
   > 账户、钱、仓跟第一套环境上一个交易日保持一致。
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
   > 支持上期所期权、能源中心期权、中金所期权、广期所期权、郑商所期权、大商所期权
   >
   > 用户注册后，默认的 APPID 为 simnow_client_test，认证码为 0000000000000000（16个0），默认开启终端认证，程序化用户可以选择不开终端认证接入。
   >
   > 交易品种：六所所有期货品种以及上期所、能源中心、中金所、广期所所有期权品种，以及郑商所、大商所部分期权品种。
   > 账户资金：初始资金两千万，支持入金，每日最多三次。
   >
   > 见 [SimNow官网](https://www.simnow.com.cn/product.action)

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

``` python
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

### 部分通用错误码说明

```bash
ErrorID="-400" ErrorMsg="参数有误"
ErrorID="-401" ErrorMsg="未登录"
ErrorID="-404" ErrorMsg="Webctp还未实现该方法"
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

### 详细接口文档

[交易服务协议文档](./docs/td_protocol.md)

[行情服务协议文档](./docs/md_protocol.md)

# 开发说明

## 项目结构

```
homalos-webctp
```

## 架构说明

### 三层架构

1. **应用层 (apps/)**: FastAPI WebSocket 端点
2. **服务层 (services/)**: 异步/同步边界处理，消息路由
3. **客户端层 (clients/)**: CTP API 封装

### 核心组件

- **BaseClient**: 抽象基类，提供公共的客户端管理逻辑
- **TdClient/MdClient (services)**: 处理 WebSocket 消息和 CTP 客户端的交互
- **TdClient/MdClient (clients)**: 封装 CTP API 调用

## 开发指南

### 本地开发

1. 安装开发依赖
   ```bash
   # 激活 python 环境
   $ .venv\Scripts\activate
   ```
# 安装依赖
   $ uv sync --dev
   ```
   
2. 配置文件
   ```bash
   # 编辑配置文件，填入正确的前置地址和认证信息
   $ cp config.sample.yaml config_md.yaml
   $ cp config.sample.yaml config_td.yaml
   ```

3. 启动服务
   ```bash
   # 启动行情服务
   $ python main.py --config config/config_md.yaml --app_type md
   # 启动交易服务
   $ python main.py --config ./config/config_td.yaml --app_type td
   ```

### 代码规范

- 使用类型注解 (Type Hints)
- 遵循 PEP 8 代码风格
- 使用有意义的变量和函数名
- 添加必要的文档字符串

### 添加新的 API

1. 在 `clients/` 中添加 CTP API 封装方法
2. 在 `services/` 的 `_init_call_map` 中注册新方法
3. 在 `constants/` 中添加相应的常量定义
4. 更新协议文档

### 测试

建议在 SimNow 仿真环境中进行充分测试后再接入生产环境。

更多详细信息请参考 [开发文档](./docs/development.md)

# 其他说明

* 由于精力有限，只进行了 SimNow 平台的简单的测试，请自行充分测试后再接入生产环境。
* 使用 webctp 进行实盘交易的后果完全有使用者自行承担。
