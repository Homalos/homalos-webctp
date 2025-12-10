<p align="center">
  English |
  <a href="md_protocol_CN.md">简体中文</a>
</p>

## Market Data Protocol

### Table of contents


* [Login](#login)
* [Subscribe Market Data](#subscribe-market-data)
* [Unsubscribe Market Data](#unsubscribe-market-data)
* [Market Data Push](#market-data-push)

### Login

#### Request

Market data login does not require UserID and Password, but it is recommended to provide UserID to be used as the name of the con file, otherwise a random uuid will be used as the name of the con file.

```json
{
  "MsgType": "ReqUserLogin",
  "ReqUserLogin": {
    "UserID": "028742",
    "Password": "123456"
  }
}
```

#### Response

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

### Subscribe Market Data

#### Request

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

#### Response

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

### Market Data Push

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


### Unsubscribe Market Data

#### Request

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

#### Response

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
