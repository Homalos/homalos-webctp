#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : md_client.py
@Date       : 2025/12/3 13:40
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: 行情客户端 (继承 CThostFtdcMdSpi)
"""
import time
import uuid
from typing import Callable, Any

from ..ctp import thostmduserapi as mdapi

from ..constants import CallError
from ..constants import MdConstant as Constant
from ..utils import CTPObjectHelper, GlobalConfig, MathHelper, logger
from .client_helper import ReconnectionController


class MdClient(mdapi.CThostFtdcMdSpi):

    def __init__(self, user_id, password):
        super().__init__()
        self._front_address: str = GlobalConfig.MdFrontAddress
        self._broker_id: str = GlobalConfig.BrokerID
        self._user_id: str = user_id or str(uuid.uuid4())
        self._password: str = password
        self._rsp_callback: Callable[[dict[str, Any]], None] | None = None
        self._api: mdapi.CThostFtdcMdApi | None = None
        self._connected: bool = False
        # Reconnection control
        self._reconnection_ctrl = ReconnectionController(max_attempts=5, interval=10.0, client_type="Md")
        logger.info(f"Md front_address: {self._front_address}", tag='md_client')

    @property
    def rsp_callback(self) -> Callable[[dict[str, Any]], None]:
        """
        响应回调函数的只读属性

        Returns:
            返回当前设置的响应回调函数，该函数接收字典参数并返回None
        """
        return self._rsp_callback

    @rsp_callback.setter
    def rsp_callback(self, callback: Callable[[dict[str, Any]], None]):
        """
        设置响应回调函数

        Args:
            callback: 回调函数，接收一个字典参数（包含响应信息）并返回None
        """
        self._rsp_callback = callback

    def method_called(self, msg_type: str, ret: int):
        """
        处理CTP API方法调用结果

        当API方法调用返回非零错误码时，构建错误响应并触发回调函数

        Args:
            msg_type: 消息类型，标识调用的API方法
            ret: 方法调用返回码，0表示成功，非0表示错误

        Returns:
            None: 无返回值，通过回调函数返回错误信息
        """
        if ret != 0:
            response = CTPObjectHelper.build_response_dict(msg_type)
            response[Constant.RspInfo] = CallError.get_rsp_info(ret)
            self.rsp_callback(response)

    def release(self) -> None:
        """
        释放行情客户端资源

        该方法会断开与CTP行情服务器的连接，释放API实例并重置连接状态。
        包括取消回调接口注册和释放底层API资源。

        Returns:
            None: 该方法没有返回值
        """
        logger.debug(f"release md client: {self._user_id}")
        self._api.RegisterSpi(None)
        self._api.Release()
        self._api = None
        self._connected = False

    def connect(self) -> None:
        """Not thread-safe"""
        if not self._connected:
            self.create_api()
            self._api.Init()
            self._connected = True
        else:
            self.login()

    def create_api(self) -> mdapi.CThostFtdcMdApi:
        """
        创建并初始化CTP行情API实例

        该方法会:
        1. 获取连接配置文件路径
        2. 创建CTP行情API实例
        3. 注册SPI回调接口
        4. 注册前置机地址

        Returns:
            mdapi.CThostFtdcMdApi: 初始化完成的CTP行情API实例
        """
        con_file_path = GlobalConfig.get_con_file_path("md" + self._user_id)
        self._api: mdapi.CThostFtdcMdApi = mdapi.CThostFtdcMdApi.CreateFtdcMdApi(con_file_path)
        self._api.RegisterSpi(self)
        self._api.RegisterFront(self._front_address)
        return self._api

    def OnFrontConnected(self):
        """
        前端连接成功回调方法

        当CTP行情前端服务器连接成功时调用，主要负责：
        1. 记录连接日志信息
        2. 控制重连频率，防止因配置错误导致的无限重连循环
        3. 在达到最大重试次数时停止重连并提示检查配置
        4. 重置重连计数器（当足够时间已过时）
        5. 触发登录流程

        重连控制逻辑：
        - 检查当前时间与上次连接时间的间隔
        - 如果间隔小于重连间隔，增加重连计数
        - 如果超过最大重连尝试次数，记录错误并停止重连
        - 否则记录警告信息并继续重连流程

        Note:
            该方法由CTP API自动调用，不应手动调用
        """
        logger.info("Md client connected")
        if not self._reconnection_ctrl.check_on_connected(
            callback=self._rsp_callback,
            message_type=Constant.OnRspUserLogin,
            logger=logger,
            current_time=time.time()
        ):
            return
        self.login()

    def OnFrontDisconnected(self, reason):
        """
        前端连接断开回调函数

        CTP API在检测到与行情前置机连接断开时自动调用此方法。

        Args:
            reason (int): 断开原因错误码，具体错误码定义参见CTP API文档

        Note:
            此方法为CTP API标准回调接口，无需手动调用
        """
        logger.warning(f"Md client disconnected, error_code={reason}")
        self._reconnection_ctrl.track_on_disconnected(
            reason=reason,
            callback=self._rsp_callback,
            logger=logger,
            current_time=time.time()
        )

    def login(self):
        """
        执行CTP行情服务器登录操作

        方法会创建登录请求字段，设置必要的登录信息（经纪商ID、用户ID、密码），
        并通过CTP API向服务器发送登录请求。

        Returns:
            int: CTP API请求ID，用于标识本次登录请求
        """
        logger.info(f"start to login for {self._user_id}")
        req = mdapi.CThostFtdcReqUserLoginField()
        req.BrokerID = self._broker_id
        req.UserID = self._user_id
        req.Password = self._password
        return self._api.ReqUserLogin(req, 0)

    def OnRspUserLogin(
            self,
            rsp_user_login: mdapi.CThostFtdcRspUserLoginField,
            rsp_info: mdapi.CThostFtdcRspInfoField,
            request_id,
            is_last
    ):
        """
        处理用户登录响应回调

        当CTP行情服务器返回用户登录结果时调用此方法，处理登录成功或失败的逻辑，
        并将登录响应信息转换为标准字典格式通过回调函数返回。

        Args:
            rsp_user_login: 用户登录响应字段，包含登录成功后的会话信息
            rsp_info: 响应信息字段，包含错误代码和错误消息
            request_id: 请求ID，用于匹配对应的请求
            is_last: 标识是否为该请求的最后一个响应包

        Returns:
            None: 无直接返回值，通过self.rsp_callback方法返回处理后的响应数据
        """
        if rsp_info is None or rsp_info.ErrorID == 0:
            logger.info("Md client login success")
        else:
            logger.info("Md client login failed, please try again")

        response = CTPObjectHelper.build_response_dict(Constant.OnRspUserLogin, rsp_info, request_id, is_last)
        response[Constant.RspUserLogin] = {
            "BrokerID": rsp_user_login.BrokerID,
            "CZCETime": rsp_user_login.CZCETime,
            "DCETime": rsp_user_login.DCETime,
            "FFEXTime": rsp_user_login.FFEXTime,
            "FrontID": rsp_user_login.FrontID,
            "INETime": rsp_user_login.INETime,
            "LoginTime": rsp_user_login.LoginTime,
            "MaxOrderRef": rsp_user_login.MaxOrderRef,
            "SessionID": rsp_user_login.SessionID,
            "SHFETime": rsp_user_login.SHFETime,
            "SystemName": rsp_user_login.SystemName,
            "SysVersion": rsp_user_login.SysVersion,
            "TradingDay": rsp_user_login.TradingDay,
            "UserID": rsp_user_login.UserID
        }
        self.rsp_callback(response)

    def OnRspSubMarketData(
            self,
            specific_instrument: mdapi.CThostFtdcSpecificInstrumentField,
            rsp_info,
            request_id,
            is_last
    ):
        """
        处理订阅行情数据的响应回调

        Args:
            specific_instrument: 特定合约信息对象，包含合约代码等字段
            rsp_info: 响应信息对象，包含错误码和错误消息
            request_id: 请求ID，用于匹配请求和响应
            is_last: 是否最后一个响应

        Returns:
            None: 无直接返回值，通过rsp_callback回调返回处理结果
        """
        response = CTPObjectHelper.build_response_dict(Constant.OnRspSubMarketData, rsp_info, request_id, is_last)
        if specific_instrument:
            response[Constant.SpecificInstrument] = {
                Constant.InstrumentID: specific_instrument.InstrumentID
            }
        self.rsp_callback(response)

    def OnRtnDepthMarketData(self, depth_marketdata: mdapi.CThostFtdcDepthMarketDataField):
        """
        处理深度市场数据回调

        当接收到CTP接口推送的深度市场数据时调用此方法，将原始数据转换为标准字典格式，
        并通过回调函数返回处理后的数据。

        Args:
            depth_marketdata: CThostFtdcDepthMarketDataField对象，包含完整的深度市场行情数据

        Returns:
            None: 无直接返回值，通过self.rsp_callback回调函数返回处理后的数据
        """
        logger.debug(f"receive depth market data: {depth_marketdata.InstrumentID}")
        depth_data = {
            "ActionDay": depth_marketdata.ActionDay,
            "AskPrice1": MathHelper.adjust_price(depth_marketdata.AskPrice1),
            "AskPrice2": MathHelper.adjust_price(depth_marketdata.AskPrice2),
            "AskPrice3": MathHelper.adjust_price(depth_marketdata.AskPrice3),
            "AskPrice4": MathHelper.adjust_price(depth_marketdata.AskPrice4),
            "AskPrice5": MathHelper.adjust_price(depth_marketdata.AskPrice5),
            "AskVolume1": depth_marketdata.AskVolume1,
            "AskVolume2": depth_marketdata.AskVolume2,
            "AskVolume3": depth_marketdata.AskVolume3,
            "AskVolume4": depth_marketdata.AskVolume4,
            "AskVolume5": depth_marketdata.AskVolume5,
            "AveragePrice": MathHelper.adjust_price(depth_marketdata.AveragePrice),
            "BandingLowerPrice": MathHelper.adjust_price(depth_marketdata.BandingLowerPrice),
            "BandingUpperPrice": MathHelper.adjust_price(depth_marketdata.BandingUpperPrice),
            "BidPrice1": MathHelper.adjust_price(depth_marketdata.BidPrice1),
            "BidPrice2": MathHelper.adjust_price(depth_marketdata.BidPrice2),
            "BidPrice3": MathHelper.adjust_price(depth_marketdata.BidPrice3),
            "BidPrice4": MathHelper.adjust_price(depth_marketdata.BidPrice4),
            "BidPrice5": MathHelper.adjust_price( depth_marketdata.BidPrice5),
            "BidVolume1": depth_marketdata.BidVolume1,
            "BidVolume2": depth_marketdata.BidVolume2,
            "BidVolume3": depth_marketdata.BidVolume3,
            "BidVolume4": depth_marketdata.BidVolume4,
            "BidVolume5": depth_marketdata.BidVolume5,
            "ClosePrice": MathHelper.adjust_price(depth_marketdata.ClosePrice),
            "CurrDelta": depth_marketdata.CurrDelta,
            "ExchangeID": depth_marketdata.ExchangeID,
            "ExchangeInstID": depth_marketdata.ExchangeInstID,
            "HighestPrice": MathHelper.adjust_price(depth_marketdata.HighestPrice),
            "InstrumentID": depth_marketdata.InstrumentID,
            "LastPrice": MathHelper.adjust_price(depth_marketdata.LastPrice),
            "LowerLimitPrice": MathHelper.adjust_price(depth_marketdata.LowerLimitPrice),
            "LowestPrice": MathHelper.adjust_price(depth_marketdata.LowestPrice),
            "OpenInterest": depth_marketdata.OpenInterest,
            "OpenPrice": MathHelper.adjust_price(depth_marketdata.OpenPrice),
            "PreClosePrice": MathHelper.adjust_price(depth_marketdata.PreClosePrice),
            "PreDelta": depth_marketdata.PreDelta,
            "PreOpenInterest": depth_marketdata.PreOpenInterest,
            "PreSettlementPrice": MathHelper.adjust_price(depth_marketdata.PreSettlementPrice),
            "SettlementPrice": MathHelper.adjust_price(depth_marketdata.SettlementPrice),
            "TradingDay": depth_marketdata.TradingDay,
            "Turnover": depth_marketdata.Turnover,
            "UpdateMillisec": depth_marketdata.UpdateMillisec,
            "UpdateTime": depth_marketdata.UpdateTime,
            "UpperLimitPrice": MathHelper.adjust_price(depth_marketdata.UpperLimitPrice),
            "Volume": depth_marketdata.Volume,
            "reserve1": depth_marketdata.reserve1,
            "reserve2": depth_marketdata.reserve2
            }
        response = {
            Constant.MessageType: Constant.OnRtnDepthMarketData,
            Constant.DepthMarketData: depth_data
        }
        self.rsp_callback(response)

    def OnRspUnSubMarketData(
            self,
            specific_instrument: mdapi.CThostFtdcSpecificInstrumentField,
            rsp_info,
            request_id,
            is_last
    ):
        """
        处理取消订阅行情数据的响应回调

        Args:
            specific_instrument: 特定合约信息，包含被取消订阅的合约代码
            rsp_info: 响应信息，包含错误代码和错误消息
            request_id: 请求ID，用于标识对应的请求
            is_last: 是否为最后一条响应

        Returns:
            None: 无直接返回值，通过回调函数返回响应数据
        """
        logger.debug("recv unsub market data")
        response = CTPObjectHelper.build_response_dict(Constant.OnRspUnSubMarketData, rsp_info, request_id, is_last)
        if specific_instrument:
            response[Constant.SpecificInstrument] = {
                Constant.InstrumentID: specific_instrument.InstrumentID
            }
        self.rsp_callback(response)

    def subscribe_marketdata(self, request: dict[str, Any]) -> None:
        """
        订阅市场行情数据

        向CTP API发送订阅指定合约行情数据的请求

        Args:
            request: 请求字典，包含以下字段：
                - InstrumentID: 合约代码列表

        Returns:
            None: 无直接返回值，通过回调函数返回响应数据
        """
        instrument_ids = request[Constant.InstrumentID]
        instrument_ids = list(map(lambda i: i.encode(), instrument_ids))
        logger.debug(f"subscribe data for {instrument_ids}")
        ret = self._api.SubscribeMarketData(instrument_ids, len(instrument_ids))
        self.method_called(Constant.OnRspSubMarketData, ret)

    def unsubscribe_marketdata(self, request: dict[str, Any]) -> None:
        """
        取消订阅市场数据

        从CTP API取消订阅指定合约的市场数据。

        Args:
            request: 包含取消订阅参数的字典，必须包含Constant.InstrumentID键
                - InstrumentID: 要取消订阅的合约ID列表

        Returns:
            None
        """
        instrument_ids = request[Constant.InstrumentID]
        instrument_ids = list(map(lambda i: i.encode(), instrument_ids))
        logger.debug(f"unsubscribe data for {instrument_ids}")
        ret = self._api.UnSubscribeMarketData(instrument_ids, len(instrument_ids))
        self.method_called(Constant.OnRspUnSubMarketData, ret)
