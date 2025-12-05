#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : client_helper.py
@Date       : 2025/12/5 10:40
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: 客户端工具函数
"""

def build_order_insert_to_dict(input_order_field) -> dict:
    """
    将CTP输入报单字段对象转换为字典格式

    Args:
        input_order_field: CTP输入报单字段对象，包含报单相关属性

    Returns:
        dict: 包含报单信息的字典，键值对包括：
            - BrokerID: 经纪公司代码
            - InvestorID: 投资者代码
            - OrderRef: 报单引用
            - UserID: 用户代码
            - OrderPriceType: 报单价格条件
            - Direction: 买卖方向
            - CombOffsetFlag: 组合开平标志
            - CombHedgeFlag: 组合投机套保标志
            - LimitPrice: 价格
            - VolumeTotalOriginal: 数量
            - TimeCondition: 有效期类型
            - GTDDate: GTD日期
            - VolumeCondition: 成交量类型
            - MinVolume: 最小成交量
            - ContingentCondition: 触发条件
            - StopPrice: 止损价
            - ForceCloseReason: 强平原因
            - IsAutoSuspend: 自动挂起标志
            - BusinessUnit: 业务单元
            - RequestID: 请求编号
            - UserForceClose: 用户强平标志
            - IsSwapOrder: 互换单标志
            - ExchangeID: 交易所代码
            - InvestUnitID: 投资单元代码
            - AccountID: 资金账号
            - CurrencyID: 币种代码
            - ClientID: 交易编码
            - MacAddress: Mac地址
            - InstrumentID: 合约代码
            - IPAddress: IP地址
    """

    return {
        "BrokerID": input_order_field.BrokerID,
        "InvestorID": input_order_field.InvestorID,
        "OrderRef": input_order_field.OrderRef,
        "UserID": input_order_field.UserID,
        "OrderPriceType": input_order_field.OrderPriceType,
        "Direction": input_order_field.Direction,
        "CombOffsetFlag": input_order_field.CombOffsetFlag,
        "CombHedgeFlag": input_order_field.CombHedgeFlag,
        "LimitPrice": input_order_field.LimitPrice,
        "VolumeTotalOriginal": input_order_field.VolumeTotalOriginal,
        "TimeCondition": input_order_field.TimeCondition,
        "GTDDate": input_order_field.GTDDate,
        "VolumeCondition": input_order_field.VolumeCondition,
        "MinVolume": input_order_field.MinVolume,
        "ContingentCondition": input_order_field.ContingentCondition,
        "StopPrice": input_order_field.StopPrice,
        "ForceCloseReason": input_order_field.ForceCloseReason,
        "IsAutoSuspend": input_order_field.IsAutoSuspend,
        "BusinessUnit": input_order_field.BusinessUnit,
        "RequestID": input_order_field.RequestID,
        "UserForceClose": input_order_field.UserForceClose,
        "IsSwapOrder": input_order_field.IsSwapOrder,
        "ExchangeID": input_order_field.ExchangeID,
        "InvestUnitID": input_order_field.InvestUnitID,
        "AccountID": input_order_field.AccountID,
        "CurrencyID": input_order_field.CurrencyID,
        "ClientID": input_order_field.ClientID,
        "MacAddress": input_order_field.MacAddress,
        "InstrumentID": input_order_field.InstrumentID,
        "IPAddress": input_order_field.IPAddress
    }

def build_order_to_dict(order_field) -> dict:
    """
    将CTP订单字段对象转换为字典格式

    Args:
        order_field: CTP订单字段对象，包含所有订单相关信息

    Returns:
        dict: 包含所有订单字段的字典，键为字段名，值为对应的字段值
    """

    return {
        "BrokerID": order_field.BrokerID,
        "InvestorID": order_field.InvestorID,
        "OrderRef": order_field.OrderRef,
        "UserID": order_field.UserID,
        "OrderPriceType": order_field.OrderPriceType,
        "Direction": order_field.Direction,
        "CombOffsetFlag": order_field.CombOffsetFlag,
        "CombHedgeFlag": order_field.CombHedgeFlag,
        "LimitPrice": order_field.LimitPrice,
        "VolumeTotalOriginal": order_field.VolumeTotalOriginal,
        "TimeCondition": order_field.TimeCondition,
        "GTDDate": order_field.GTDDate,
        "VolumeCondition": order_field.VolumeCondition,
        "MinVolume": order_field.MinVolume,
        "ContingentCondition": order_field.ContingentCondition,
        "StopPrice": order_field.StopPrice,
        "ForceCloseReason": order_field.ForceCloseReason,
        "IsAutoSuspend": order_field.IsAutoSuspend,
        "BusinessUnit": order_field.BusinessUnit,
        "RequestID": order_field.RequestID,
        "OrderLocalID": order_field.OrderLocalID,
        "ExchangeID": order_field.ExchangeID,
        "ParticipantID": order_field.ParticipantID,
        "ClientID": order_field.ClientID,
        "TraderID": order_field.TraderID,
        "InstallID": order_field.InstallID,
        "OrderSubmitStatus": order_field.OrderSubmitStatus,
        "NotifySequence": order_field.NotifySequence,
        "TradingDay": order_field.TradingDay,
        "SettlementID": order_field.SettlementID,
        "OrderSysID": order_field.OrderSysID,
        "OrderSource": order_field.OrderSource,
        "OrderStatus": order_field.OrderStatus,
        "OrderType": order_field.OrderType,
        "VolumeTraded": order_field.VolumeTraded,
        "VolumeTotal": order_field.VolumeTotal,
        "InsertDate": order_field.InsertDate,
        "InsertTime": order_field.InsertTime,
        "ActiveTime": order_field.ActiveTime,
        "SuspendTime": order_field.SuspendTime,
        "UpdateTime": order_field.UpdateTime,
        "CancelTime": order_field.CancelTime,
        "ActiveTraderID": order_field.ActiveTraderID,
        "ClearingPartID": order_field.ClearingPartID,
        "SequenceNo": order_field.SequenceNo,
        "FrontID": order_field.FrontID,
        "SessionID": order_field.SessionID,
        "UserProductInfo": order_field.UserProductInfo,
        "StatusMsg": order_field.StatusMsg,
        "UserForceClose": order_field.UserForceClose,
        "ActiveUserID": order_field.ActiveUserID,
        "BrokerOrderSeq": order_field.BrokerOrderSeq,
        "RelativeOrderSysID": order_field.RelativeOrderSysID,
        "ZCETotalTradedVolume": order_field.ZCETotalTradedVolume,
        "IsSwapOrder": order_field.IsSwapOrder,
        "BranchID": order_field.BranchID,
        "InvestUnitID": order_field.InvestUnitID,
        "AccountID": order_field.AccountID,
        "CurrencyID": order_field.CurrencyID,
        "MacAddress": order_field.MacAddress,
        "InstrumentID": order_field.InstrumentID,
        "ExchangeInstID": order_field.ExchangeInstID,
        "IPAddress": order_field.IPAddress
    }