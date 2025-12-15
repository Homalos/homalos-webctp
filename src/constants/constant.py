#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : constant.py
@Date       : 2025/12/3 13:50
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: 消息类型常量
"""
class CommonConstant(object):
    MessageType = "MsgType"
    RspInfo = "RspInfo"
    RequestID = "RequestID"
    IsLast = "IsLast"

    OnRspUserLogin = "RspUserLogin"

    ReqUserLogin = "ReqUserLogin"
    RspUserLogin = "RspUserLogin"
    
    # Heartbeat
    Ping = "Ping"
    Pong = "Pong"


class MdConstant(CommonConstant):

    # Request MessageType
    SubscribeMarketData = "SubscribeMarketData"
    UnSubscribeMarketData = "UnSubscribeMarketData"  # 注意：大写 S，与 CTP API 保持一致

    # Response MessageType
    OnRspSubMarketData = "RspSubMarketData"
    OnRspUnSubMarketData = "RspUnSubMarketData"

    # RtnMessageType
    OnRtnDepthMarketData = "RtnDepthMarketData"

    # Request Field
    InstrumentID = "InstrumentID"

    # Response Field
    SpecificInstrument = "SpecificInstrument"
    DepthMarketData = "DepthMarketData"
    
    # 策略管理相关消息类型
    RegisterStrategy = "RegisterStrategy"
    UnregisterStrategy = "UnregisterStrategy"
    StartStrategy = "StartStrategy"
    StopStrategy = "StopStrategy"
    QueryStrategyStatus = "QueryStrategyStatus"
    ListStrategies = "ListStrategies"
    
    # 策略管理响应消息类型
    OnRspRegisterStrategy = "RspRegisterStrategy"
    OnRspUnregisterStrategy = "RspUnregisterStrategy"
    OnRspStartStrategy = "RspStartStrategy"
    OnRspStopStrategy = "RspStopStrategy"
    OnRspQueryStrategyStatus = "RspQueryStrategyStatus"
    OnRspListStrategies = "RspListStrategies"
    
    # 策略管理请求字段
    StrategyID = "StrategyID"
    StrategyName = "StrategyName"
    StrategyConfig = "StrategyConfig"
    SubscribedInstruments = "SubscribedInstruments"
    
    # 策略管理响应字段
    StrategyInfo = "StrategyInfo"
    StrategyList = "StrategyList"
    Success = "Success"


class TdConstant(CommonConstant):

    # MessageType
    OnRspUserLogin = "RspUserLogin"
    OnRspAuthenticate = "RspAuthenticate"
    OnRspQryInstrument = "RspQryInstrument"
    OnRspQryExchange = "RspQryExchange"
    OnRspQryProduct = "RspQryProduct"
    OnRspQryDepthMarketData = "RspQryDepthMarketData"
    OnRspQryInvestorPositionDetail = "RspQryInvestorPositionDetail"
    OnRspQryExchangeMarginRate = "RspQryExchangeMarginRate"
    OnRspQryInstrumentOrderCommRate = "RspQryInstrumentOrderCommRate"
    OnRspQryOptionInstrTradeCost = "RspQryOptionInstrTradeCost"
    OnRspQryOptionInstrCommRate = "RspQryOptionInstrCommRate"
    OnRspUserPasswordUpdate = "RspUserPasswordUpdate"
    OnRspOrderInsert = "RspOrderInsert"
    OnErrRtnOrderInsert = "ErrRtnOrderInsert"
    OnRtnOrder = "RtnOrder"
    OnRtnTrade = "RtnTrade"
    OnRspOrderAction = "RspOrderAction"
    OnErrRtnOrderAction = "ErrRtnOrderAction"
    OnRspQryMaxOrderVolume = "RspQryMaxOrderVolume"
    OnRspQryOrder = "RspQryOrder"
    OnRspQryTrade = "RspQryTrade"
    OnRspQryInvestorPosition = "RspQryInvestorPosition"
    OnRspQryTradingAccount = "RspQryTradingAccount"
    OnRspQryInvestor = "RspQryInvestor"
    OnRspQryTradingCode = "RspQryTradingCode"
    OnRspQryInstrumentMarginRate = "RspQryInstrumentMarginRate"
    OnRspQryInstrumentCommissionRate = "RspQryInstrumentCommissionRate"
    OnRspQrySettlementInfoConfirm = "RspQrySettlementInfoConfirm"

    # RequestField
    QryInstrument = "QryInstrument"
    QryExchange = "QryExchange"
    QryProduct = "QryProduct"
    QryDepthMarketData = "QryDepthMarketData"
    QryInvestorPositionDetail = "QryInvestorPositionDetail"
    QryExchangeMarginRate = "QryExchangeMarginRate"
    QryInstrumentOrderCommRate = "QryInstrumentOrderCommRate"
    QryOptionInstrTradeCost = "QryOptionInstrTradeCost"
    QryOptionInstrCommRate = "QryOptionInstrCommRate"
    UserPasswordUpdate = "UserPasswordUpdate"
    InputOrder = "InputOrder"
    InputOrderAction = "InputOrderAction"
    QryMaxOrderVolume = "QryMaxOrderVolume"
    QryOrder = "QryOrder"
    QryTrade = "QryTrade"
    QryInvestorPosition = "QryInvestorPosition"
    QryTradingAccount = "QryTradingAccount"
    QryInvestor = "QryInvestor"
    QryTradingCode = "QryTradingCode"
    QryInstrumentMarginRate = "QryInstrumentMarginRate"
    QryInstrumentCommissionRate = "QryInstrumentCommissionRate"
    QrySettlementInfoConfirm = "QrySettlementInfoConfirm"

    # ResponseField
    Instrument = "Instrument"
    Order = "Order"
    Trade = "Trade"
    OrderAction = "OrderAction"
    Exchange = "Exchange"
    Product = "Product"
    InvestorPositionDetail = "InvestorPositionDetail"
    ExchangeMarginRate = "ExchangeMarginRate"
    InstrumentOrderCommRate = "InstrumentOrderCommRate"
    OptionInstrTradeCost = "OptionInstrTradeCost"
    OptionInstrCommRate = "OptionInstrCommRate"
    DepthMarketData = "DepthMarketData"
    InvestorPosition = "InvestorPosition"
    TradingAccount = "TradingAccount"
    Investor = "Investor"
    TradingCode = "TradingCode"
    InstrumentMarginRate = "InstrumentMarginRate"
    InstrumentCommissionRate = "InstrumentCommissionRate"
    SettlementInfoConfirm = "SettlementInfoConfirm"

    # RequestMethod
    ReqQryInstrument = "ReqQryInstrument"
    ReqQryExchange = "ReqQryExchange"
    ReqQryProduct = "ReqQryProduct"
    ReqQryDepthMarketData = "ReqQryDepthMarketData"
    ReqQryInvestorPositionDetail = "ReqQryInvestorPositionDetail"
    ReqQryExchangeMarginRate = "ReqQryExchangeMarginRate"
    ReqQryInstrumentOrderCommRate = "ReqQryInstrumentOrderCommRate"
    ReqQryOptionInstrTradeCost = "ReqQryOptionInstrTradeCost"
    ReqQryOptionInstrCommRate = "ReqQryOptionInstrCommRate"
    ReqUserPasswordUpdate = "ReqUserPasswordUpdate"
    ReqOrderInsert = "ReqOrderInsert"
    ReqOrderAction = "ReqOrderAction"
    ReqQryMaxOrderVolume = "ReqQryMaxOrderVolume"
    ReqQryOrder = "ReqQryOrder"
    ReqQryTrade = "ReqQryTrade"
    ReqQryInvestorPosition = "ReqQryInvestorPosition"
    ReqQryTradingAccount = "ReqQryTradingAccount"
    ReqQryInvestor = "ReqQryInvestor"
    ReqQryTradingCode = "ReqQryTradingCode"
    ReqQryInstrumentMarginRate = "ReqQryInstrumentMarginRate"
    ReqQryInstrumentCommissionRate = "ReqQryInstrumentCommissionRate"
    ReqQrySettlementInfoConfirm = "ReqQrySettlementInfoConfirm"
