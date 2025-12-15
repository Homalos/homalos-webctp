#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : client_helper.py
@Date       : 2025/12/5 10:40
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: 客户端工具函数，将md_client.py和td_client.py中的公共代码抽离出来，提高代码复用率
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


def extract_login_response_fields(rsp_user_login_field) -> dict:
    """提取登录响应字段为字典
    
    将CTP用户登录响应结构体的所有字段提取为Python字典，
    避免CTP对象生命周期问题。
    
    Args:
        rsp_user_login_field: CTP用户登录响应结构体
        
    Returns:
        dict: 包含所有登录响应字段的字典
    """
    return {
        "TradingDay": rsp_user_login_field.TradingDay,
        "LoginTime": rsp_user_login_field.LoginTime,
        "BrokerID": rsp_user_login_field.BrokerID,
        "UserID": rsp_user_login_field.UserID,
        "SystemName": rsp_user_login_field.SystemName,
        "FrontID": rsp_user_login_field.FrontID,
        "SessionID": rsp_user_login_field.SessionID,
        "MaxOrderRef": rsp_user_login_field.MaxOrderRef,
        "SHFETime": rsp_user_login_field.SHFETime,
        "DCETime": rsp_user_login_field.DCETime,
        "CZCETime": rsp_user_login_field.CZCETime,
        "FFEXTime": rsp_user_login_field.FFEXTime,
        "INETime": rsp_user_login_field.INETime
    }


class ReconnectionController:
    """CTP 客户端重连控制器"""
    
    def __init__(self, max_attempts: int = 5, interval: float = 10.0, client_type: str = "CTP"):
        """
        初始化重连控制器
        
        Args:
            max_attempts: 最大重连尝试次数
            interval: 重连间隔阈值（秒）
            client_type: 客户端类型
        """
        self.reconnect_count: int = 0
        self.max_reconnect_attempts: int = max_attempts
        self.last_connect_time: float = 0.0
        self.reconnect_interval: float = interval
        self.client_type: str = client_type
    
    def check_on_connected(self, callback, message_type: str, logger, current_time: float) -> bool:
        """在 OnFrontConnected 中检查重连状态"""
        if current_time - self.last_connect_time < self.reconnect_interval:
            self.reconnect_count += 1
            if self.reconnect_count > self.max_reconnect_attempts:
                error_msg = (
                    f"Exceeded maximum reconnection attempts ({self.max_reconnect_attempts}). "
                    "Possible reasons: non-trading hours, incorrect broker/front address, or network issues."
                )
                logger.error(error_msg)
                if callback:
                    callback({"MsgType": message_type, "RspInfo": {"ErrorID": -4097, "ErrorMsg": error_msg}})
                return False
            logger.warning(f"Reconnection attempt {self.reconnect_count}/{self.max_reconnect_attempts}")
        else:
            self.reconnect_count = 0
        self.last_connect_time = current_time
        return True
    
    def track_on_disconnected(self, reason: int, callback, logger, current_time: float) -> None:
        """在 OnFrontDisconnected 中跟踪断开次数"""
        if self.last_connect_time == 0:
            self.reconnect_count = 1
            logger.debug("First disconnection, count=1")
        elif current_time - self.last_connect_time < self.reconnect_interval:
            self.reconnect_count += 1
            logger.debug(f"Reconnection count increased to {self.reconnect_count}")
        else:
            self.reconnect_count = 1
            logger.debug(f"Reconnection count reset to 1 (time gap: {current_time - self.last_connect_time:.1f}s)")
        self.last_connect_time = current_time
        if callback and self.reconnect_count >= self.max_reconnect_attempts:
            error_msg = (
                f"CTP connection failed after {self.max_reconnect_attempts} attempts (error_code={reason}). "
                "Possible reasons: non-trading hours, incorrect broker/front address, or network issues."
            )
            logger.error(error_msg)
            callback({"MsgType": "OnFrontDisconnected", "RspInfo": {"ErrorID": reason, "ErrorMsg": error_msg}})
