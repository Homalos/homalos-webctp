# 行情协议

## 目录

* [登录](#登录)
* [订阅行情](#订阅行情)
* [取消订阅行情](#取消订阅行情)
* [深度行情推送](#深度行情推送)

### 登录

#### 请求

行情登录不需要 UserID 和 Password，但是建议提供 UserID 来作为 con file 的名称，否则会用随机的 uuid 作为 con file 的名称

```json
{
  "MsgType": "ReqUserLogin",
  "ReqUserLogin": {
    "UserID": "028742",
    "Password": "123456"
  }
}
```

#### 应答

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
        "TradingDay": "20251201",
        "UserID": ""
    }
}
```

### 订阅行情

#### 订阅行情请求

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

#### 订阅行情应答

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

### 深度行情推送

```json
{
    "MsgType": "RtnDepthMarketData",
    "DepthMarketData": {
        "ActionDay": "20251130",
        "AskPrice1": 962.7,
        "AskPrice2": 0,
        "AskPrice3": 0,
        "AskPrice4": 0,
        "AskPrice5": 0,
        "AskVolume1": 5,
        "AskVolume2": 0,
        "AskVolume3": 0,
        "AskVolume4": 0,
        "AskVolume5": 0,
        "AveragePrice": 958095.5959201817,
        "BandingLowerPrice": 0.0,
        "BandingUpperPrice": 0.0,
        "BidPrice1": 962.68,
        "BidPrice2": 0,
        "BidPrice3": 0,
        "BidPrice4": 0,
        "BidPrice5": 0,
        "BidVolume1": 2,
        "BidVolume2": 0,
        "BidVolume3": 0,
        "BidVolume4": 0,
        "BidVolume5": 0,
        "ClosePrice": 0.0,
        "CurrDelta": 0.0,
        "ExchangeID": "",
        "ExchangeInstID": "",
        "HighestPrice": 968.16,
        "InstrumentID": "au2602",
        "LastPrice": 962.7,
        "LowerLimitPrice": 817.52,
        "LowestPrice": 948.14,
        "OpenInterest": 205287.0,
        "OpenPrice": 951.92,
        "PreClosePrice": 953.92,
        "PreDelta": 0.0,
        "PreOpenInterest": 202129.0,
        "PreSettlementPrice": 950.62,
        "SettlementPrice": 0.0,
        "TradingDay": "20251201",
        "Turnover": 310361654960.0,
        "UpdateMillisec": 0,
        "UpdateTime": "18:06:31",
        "UpperLimitPrice": 1083.7,
        "Volume": 323936,
        "reserve1": "au2602",
        "reserve2": ""
    }
}
```

### 取消订阅行情

#### 取消订阅行情请求

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

#### 取消订阅行情应答

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

## 心跳机制

服务端会定期发送 Ping 消息（默认每 30 秒），客户端需要响应 Pong 消息以保持连接活跃。

### Ping 消息（服务端  客户端）

```json
{
  "MsgType": "Ping",
  "Timestamp": 1702198765123
}
```

### Pong 消息（客户端  服务端）

```json
{
  "MsgType": "Pong",
  "Timestamp": 1702198765123
}
```

**注意事项：**

* 心跳间隔：默认 30 秒（可通过配置文件调整）
* 超时时间：默认 60 秒（可通过配置文件调整）
* 如果客户端在超时时间内未响应 Pong，服务端将主动断开连接
* Timestamp 字段为服务端发送 Ping 时的时间戳（毫秒），客户端应原样返回
