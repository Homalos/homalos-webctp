import logging
from typing import Callable, Any

from .client_helper import build_order_to_dict, build_order_insert_to_dict
from ..ctp import thosttraderapi as tdapi

from ..constants import CallError
from ..constants import TdConstant as Constant
from ..utils import CTPObjectHelper, GlobalConfig, MathHelper


class TdClient(tdapi.CThostFtdcTraderSpi):

    def __init__(self, user_id, password):
        super().__init__()
        self._front_address:str = GlobalConfig.TdFrontAddress
        self._broker_id:str = GlobalConfig.BrokerID
        self._auth_code:str = GlobalConfig.AuthCode
        self._app_id:str = GlobalConfig.AppID
        self._user_id:str = user_id
        self._password: str = password
        logging.debug(f"Td front_address: {self._front_address}, broker_id: {self._broker_id}, auth_code: {self._auth_code}, app_id: {self._app_id}, user_id: {self._user_id}")
        self._rsp_callback: Callable[[dict[str, Any]], None] | None = None
        self._api: tdapi.CThostFtdcTraderApi | None = None
        self._connected: bool = False

    @property
    def rsp_callback(self) -> Callable[[dict[str, Any]], None]:
        """获取响应回调函数

        Returns:
            Callable[[dict[str, Any]], None]: 返回当前设置的响应回调函数，
                该函数接收一个字典参数并返回None
        """
        return self._rsp_callback

    @rsp_callback.setter
    def rsp_callback(self, callback: Callable[[dict[str, Any]], None]):
        """设置响应回调函数

        Args:
            callback: 回调函数，接收一个字典参数并返回None
                     字典包含响应数据的具体内容
        """
        self._rsp_callback = callback

    def method_called(self, msg_type: str, ret: int):
        """处理API方法调用结果

        当API方法调用返回错误码时（ret != 0），构建错误响应并通过回调函数通知

        Args:
            msg_type: 消息类型，标识调用的具体API方法
            ret: 方法调用返回值，0表示成功，非0表示错误

        Notes:
            仅当ret不为0时才会构建响应并触发回调
        """
        if ret != 0:
            response = CTPObjectHelper.build_response_dict(msg_type)
            response[Constant.RspInfo] = CallError.get_rsp_info(ret)
            self.rsp_callback(response)

    def release(self) -> None:
        """
        释放API连接并清理资源

        该方法用于安全断开与CTP交易API的连接，执行以下操作：
        1. 注销SPI回调接口
        2. 释放API实例
        3. 清理API引用
        4. 重置连接状态

        注意：调用此方法后，实例将不再可用，需要重新创建才能再次连接
        """
        self._api.RegisterSpi(None)
        self._api.Release()
        self._api = None
        self._connected = False

    def connect(self) -> None:
        """
        连接到CTP交易API

        根据当前连接状态执行不同的操作：
        - 如果未连接：创建API实例并初始化
        - 如果已连接：执行认证流程

        Note:
            该方法会修改实例的连接状态，首次调用会将_connected设置为True
        """
        if not self._connected:
            self.create_api()
            self._api.Init()
            self._connected = True
        else:
            self.authenticate()

    def create_api(self) -> tdapi.CThostFtdcTraderApi:
        """
        创建并初始化CTP交易API实例

        方法会:
        1. 根据用户ID生成连接文件路径
        2. 创建交易API实例
        3. 注册SPI回调接口
        4. 订阅私有和公共主题
        5. 注册前置机地址

        Returns:
            tdapi.CThostFtdcTraderApi: 初始化完成的CTP交易API实例
        """
        con_file_path = GlobalConfig.get_con_file_path("td" + self._user_id)
        self._api: tdapi.CThostFtdcTraderApi = tdapi.CThostFtdcTraderApi.CreateFtdcTraderApi(con_file_path)
        self._api.RegisterSpi(self)
        self._api.SubscribePrivateTopic(tdapi.THOST_TERT_QUICK)
        self._api.SubscribePublicTopic(tdapi.THOST_TERT_QUICK)
        self._api.RegisterFront(self._front_address)
        return self._api

    def OnFrontConnected(self):
        """
        当交易前端连接成功时触发的回调函数

        功能:
            - 记录连接成功日志
            - 自动触发认证流程

        注意:
            此函数由CTP API框架自动调用，开发者不应手动调用
        """
        logging.info("Td client connected")
        self.authenticate()

    def OnFrontDisconnected(self, reason):
        """
        交易前端断开连接回调函数

        当与CTP交易前端的网络连接断开时，该方法会被自动调用。

        Args:
            reason (int): 断开连接的原因代码，具体错误码参考CTP API文档
        """
        logging.info(f"Td client disconnected, error_code={reason}")

    def authenticate(self):
        """
        发送交易身份认证请求

        使用配置的经纪商ID、用户ID、应用ID和认证码构造认证请求字段，
        并调用API接口发送认证请求。

        Args:
            无显式参数，使用实例属性：
            self._broker_id: 经纪商ID
            self._user_id: 用户ID
            self._app_id: 应用ID
            self._auth_code: 认证码

        Returns:
            None: 此方法无返回值，认证结果通过回调函数返回
        """
        req = tdapi.CThostFtdcReqAuthenticateField()
        req.BrokerID = self._broker_id
        req.UserID = self._user_id
        req.AppID = self._app_id
        req.AuthCode = self._auth_code
        self._api.ReqAuthenticate(req, 0)

    def OnRspAuthenticate(
            self,
            rsp_authenticate_field: tdapi.CThostFtdcRspAuthenticateField,
            rsp_info_field: tdapi.CThostFtdcRspInfoField,
            request_id: int,
            is_last: bool
    ):
        """
        处理认证请求的响应回调

        Args:
            rsp_authenticate_field: 认证响应字段，包含认证相关信息
            rsp_info_field: 响应信息字段，包含错误代码和错误消息
            request_id: 请求ID，用于标识对应的请求
            is_last: 标识是否为该请求的最后一个响应包

        Returns:
            None: 此方法无返回值，认证结果通过日志输出和后续操作处理
        """
        if rsp_info_field is None or rsp_info_field.ErrorID == 0:
            logging.info("authenticate success, start to login")
            self.login()
        else:
            logging.info("authenticate failed, please try again")
            self.process_connect_result(Constant.OnRspAuthenticate, rsp_info_field)

    def login(self):
        """
        向CTP交易服务器发送用户登录请求

        使用配置的经纪商ID、用户ID、密码和产品信息构造登录请求，
        并调用底层API的ReqUserLogin方法发起登录。

        Returns:
            None: 该方法不直接返回结果，登录结果通过异步回调返回
        """
        req = tdapi.CThostFtdcReqUserLoginField()
        req.BrokerID = self._broker_id
        req.UserID = self._user_id
        req.Password = self._password
        req.UserProductInfo = "homalos"
        self._api.ReqUserLogin(req, 0)

    def OnRspUserLogin(
            self,
            rsp_user_login_field: tdapi.CThostFtdcRspUserLoginField,
            rsp_info_field: tdapi.CThostFtdcRspInfoField,
            request_id: int,
            is_last: bool
    ):
        """
        处理用户登录响应回调

        当CTP交易接口返回登录响应时被调用，处理登录成功或失败的情况

        Args:
            rsp_user_login_field: 用户登录响应信息，包含登录结果相关字段
            rsp_info_field: 响应信息，包含错误码和错误消息
            request_id: 请求ID，用于标识对应的请求
            is_last: 指示是否为该请求的最后一个响应片段

        Returns:
            None: 该回调函数不返回任何值，结果通过异步事件处理
        """
        if rsp_info_field is None or rsp_info_field.ErrorID == 0:
            logging.info("loging success, start to confirm settlement info")
            self.settlement_confirm()
            self.process_connect_result(Constant.OnRspUserLogin, rsp_info_field, rsp_user_login_field)
        else:
            self.process_connect_result(Constant.OnRspUserLogin, rsp_info_field)
            logging.info("login failed, please try again")

    def settlement_confirm(self):
        """
        发送结算单确认请求

        构造并发送结算单确认请求到CTP交易系统，使用当前实例的经纪商ID和用户ID。

        Note:
            该方法会构造一个CThostFtdcSettlementInfoConfirmField请求对象，
            并调用CTP API的ReqSettlementInfoConfirm方法发送请求。
        """
        req = tdapi.CThostFtdcSettlementInfoConfirmField()
        req.BrokerID = self._broker_id
        req.InvestorID = self._user_id
        self._api.ReqSettlementInfoConfirm(req, 0)

    def OnRspQrySettlementInfoConfirm(
            self,
            settlement_info_confirm_field: tdapi.CThostFtdcSettlementInfoConfirmField,
            rsp_info_field: tdapi.CThostFtdcRspInfoField,
            request_id: int,
            is_last: bool
    ):
        """
        查询结算信息确认响应回调函数

        当客户端发起查询结算信息确认请求后，服务器返回确认信息时触发此回调

        Args:
            settlement_info_confirm_field: 结算信息确认字段，包含确认的详细信息
            rsp_info_field: 响应信息字段，包含错误码和错误消息
            request_id: 请求ID，用于标识对应的请求
            is_last: 是否为最后一次响应，True表示这是该请求的最后一次响应

        Returns:
            None
        """
        logging.info("confirm settlement info success")
        if rsp_info_field is not None:
            logging.info(f"settlement confirm rsp info, ErrorID: {rsp_info_field.ErrorID}, ErrorMsg: {rsp_info_field.ErrorMsg}")

    def process_connect_result(
            self,
            message_type: str,
            rsp_info_field: tdapi.CThostFtdcRspInfoField,
            rsp_user_login_field: tdapi.CThostFtdcRspUserLoginField = None
    ):
        """处理CTP交易连接结果回调

        将CTP交易接口的连接结果转换为标准响应格式，并通过回调函数返回。

        Args:
            message_type: 消息类型标识
            rsp_info_field: CTP响应信息结构体，包含错误代码和信息
            rsp_user_login_field: CTP用户登录响应结构体，包含登录相关信息，可选

        Returns:
            无返回值，通过self.rsp_callback返回处理后的响应数据
        """
        response = CTPObjectHelper.build_response_dict(message_type, rsp_info_field, 0, True)
        if rsp_user_login_field:
            response[Constant.RspUserLogin] = {
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

        self.rsp_callback(response)

    def req_qry_instrument(self, request: dict[str, Any]) -> None:
        req, request_id = CTPObjectHelper.extract_request(request, Constant.QryInstrument, tdapi.CThostFtdcQryInstrumentField)
        ret = self._api.ReqQryInstrument(req, request_id)
        self.method_called(Constant.OnRspQryInstrument, ret)

    def OnRspQryInstrument(
            self,
            instrument_field: tdapi.CThostFtdcInstrumentField,
            rsp_info: tdapi.CThostFtdcRspInfoField,
            request_id: int,
            is_last: bool
    ):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspQryInstrument, rsp_info, request_id, is_last)
        rsp_instrument = {}
        if instrument_field:
            rsp_instrument = {
                "InstrumentID": instrument_field.InstrumentID,
                "ExchangeID": instrument_field.ExchangeID,
                "InstrumentName": instrument_field.InstrumentName,
                "ExchangeInstID": instrument_field.ExchangeInstID,
                "ProductID": instrument_field.ProductID,
                "ProductClass": instrument_field.ProductClass,
                "DeliveryYear": instrument_field.DeliveryYear,
                "DeliveryMonth": instrument_field.DeliveryMonth,
                "MaxMarketOrderVolume": instrument_field.MaxMarketOrderVolume,
                "MinMarketOrderVolume": instrument_field.MinMarketOrderVolume,
                "MaxLimitOrderVolume": instrument_field.MaxLimitOrderVolume,
                "MinLimitOrderVolume": instrument_field.MinLimitOrderVolume,
                "VolumeMultiple": instrument_field.VolumeMultiple,
                "PriceTick": instrument_field.PriceTick,
                "CreateDate": instrument_field.CreateDate,
                "OpenDate": instrument_field.OpenDate,
                "ExpireDate": instrument_field.ExpireDate,
                "StartDelivDate": instrument_field.StartDelivDate,
                "EndDelivDate": instrument_field.EndDelivDate,
                "InstLifePhase": instrument_field.InstLifePhase,
                "IsTrading": instrument_field.IsTrading,
                "PositionType": instrument_field.PositionType,
                "PositionDateType": instrument_field.PositionDateType,
                "LongMarginRatio": instrument_field.LongMarginRatio,
                "ShortMarginRatio": instrument_field.ShortMarginRatio,
                "MaxMarginSideAlgorithm": instrument_field.MaxMarginSideAlgorithm,
                "UnderlyingInstrID": instrument_field.UnderlyingInstrID,
                "StrikePrice": instrument_field.StrikePrice,
                "OptionsType": instrument_field.OptionsType,
                "UnderlyingMultiple": instrument_field.UnderlyingMultiple,
                "CombinationType": instrument_field.CombinationType
            }
        response[Constant.Instrument] = rsp_instrument
        self.rsp_callback(response)

    def req_qry_exchange(self, request: dict[str, Any]) -> None:
        req, request_id = CTPObjectHelper.extract_request(request, Constant.QryExchange, tdapi.CThostFtdcQryExchangeField)
        ret = self._api.ReqQryExchange(req, request_id)
        self.method_called(Constant.OnRspQryExchange, ret)

    def OnRspQryExchange(
            self,
            exchange_field: tdapi.CThostFtdcExchangeField,
            rsp_info_field: tdapi.CThostFtdcRspInfoField,
            request_id: int,
            is_last: bool
    ):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspQryExchange, rsp_info_field, request_id, is_last)
        result = {}
        if exchange_field:
            result = {
                "ExchangeID": exchange_field.ExchangeID,
                "ExchangeName": exchange_field.ExchangeName,
                "ExchangeProperty": exchange_field.ExchangeProperty
            }
        response[Constant.Exchange] = result
        self.rsp_callback(response)

    def req_qry_product(self, request: dict[str, Any]) -> None:
        req, request_id = CTPObjectHelper.extract_request(request, Constant.QryProduct, tdapi.CThostFtdcQryProductField)
        ret = self._api.ReqQryProduct(req, request_id)
        self.method_called(Constant.OnRspQryProduct, ret)

    def OnRspQryProduct(
            self,
            product_field: tdapi.CThostFtdcProductField,
            rsp_info_field: tdapi.CThostFtdcRspInfoField,
            request_id: int,
            is_last: bool
    ):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspQryProduct, rsp_info_field, request_id, is_last)
        result = {}
        if product_field:
            result = {
                "CloseDealType": product_field.CloseDealType,
                "ExchangeID": product_field.ExchangeID,
                "ExchangeProductID": product_field.ExchangeProductID,
                "MaxLimitOrderVolume": product_field.MaxLimitOrderVolume,
                "MaxMarketOrderVolume": product_field.MaxMarketOrderVolume,
                "MinLimitOrderVolume": product_field.MinLimitOrderVolume,
                "MinMarketOrderVolume": product_field.MinMarketOrderVolume,
                "MortgageFundUseRange": product_field.MortgageFundUseRange,
                "OpenLimitControlLevel": product_field.OpenLimitControlLevel,
                "OrderFreqControlLevel": product_field.OrderFreqControlLevel,
                "PositionDateType": product_field.PositionDateType,
                "PositionType": product_field.PositionType,
                "PriceTick": product_field.PriceTick,
                "ProductClass": product_field.ProductClass,
                "ProductID": product_field.ProductID,
                "ProductName": product_field.ProductName,
                "TradeCurrencyID": product_field.TradeCurrencyID,
                "UnderlyingMultiple": product_field.UnderlyingMultiple,
                "VolumeMultiple": product_field.VolumeMultiple
            }
        response[Constant.Product] = result
        self.rsp_callback(response)

    def req_qry_depth_marketdata(self, request: dict[str, Any]) -> None:
        req, request_id = CTPObjectHelper.extract_request(request, Constant.QryDepthMarketData, tdapi.CThostFtdcQryDepthMarketDataField)
        ret = self._api.ReqQryDepthMarketData(req, request_id)
        self.method_called(Constant.OnRspQryDepthMarketData, ret)

    def OnRspQryDepthMarketData(
            self,
            depth_marketdata: tdapi.CThostFtdcDepthMarketDataField,
            rsp_info_field: tdapi.CThostFtdcRspInfoField,
            request_id: int,
            is_last: bool
    ):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspQryDepthMarketData, rsp_info_field, request_id, is_last)
        result = {}
        if depth_marketdata:
            result = {
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
                "BidPrice5": MathHelper.adjust_price(depth_marketdata.BidPrice5),
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
                "PreSettlementPrice": depth_marketdata.PreSettlementPrice,
                "SettlementPrice": MathHelper.adjust_price(depth_marketdata.SettlementPrice),
                "TradingDay": depth_marketdata.TradingDay,
                "Turnover": depth_marketdata.Turnover,
                "UpdateMillisec": depth_marketdata.UpdateMillisec,
                "UpdateTime": depth_marketdata.UpdateTime,
                "UpperLimitPrice": MathHelper.adjust_price(depth_marketdata.UpperLimitPrice),
                "Volume": depth_marketdata.Volume
            }
        response[Constant.DepthMarketData] = result
        self.rsp_callback(response)

    def req_qry_investor_position_detail(self, request: dict[str, Any]) -> None:
        req, request_id = CTPObjectHelper.extract_request(request, Constant.QryInvestorPositionDetail, tdapi.CThostFtdcQryInvestorPositionDetailField)
        ret = self._api.ReqQryInvestorPositionDetail(req, request_id)
        self.method_called(Constant.OnRspQryInvestorPositionDetail, ret)

    def OnRspQryInvestorPositionDetail(
            self,
            investor_position_detail_field: tdapi.CThostFtdcInvestorPositionDetailField,
            rsp_info_field: tdapi.CThostFtdcRspInfoField,
            request_id: int,
            is_last: bool
    ):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspQryInvestorPositionDetail, rsp_info_field, request_id, is_last)
        result = {}
        if investor_position_detail_field:
            result = {
                "BrokerID": investor_position_detail_field.BrokerID,
                "CloseAmount": investor_position_detail_field.CloseAmount,
                "CloseProfitByDate": investor_position_detail_field.CloseProfitByDate,
                "CloseProfitByTrade": investor_position_detail_field.CloseProfitByTrade,
                "CloseVolume": investor_position_detail_field.CloseVolume,
                "CombInstrumentID": investor_position_detail_field.CombInstrumentID,
                "Direction": investor_position_detail_field.Direction,
                "ExchMargin": investor_position_detail_field.ExchMargin,
                "ExchangeID": investor_position_detail_field.ExchangeID,
                "HedgeFlag": investor_position_detail_field.HedgeFlag,
                "InstrumentID": investor_position_detail_field.InstrumentID,
                "InvestUnitID": investor_position_detail_field.InvestUnitID,
                "InvestorID": investor_position_detail_field.InvestorID,
                "LastSettlementPrice": investor_position_detail_field.LastSettlementPrice,
                "Margin": investor_position_detail_field.Margin,
                "MarginRateByMoney": investor_position_detail_field.MarginRateByMoney,
                "MarginRateByVolume": investor_position_detail_field.MarginRateByVolume,
                "OpenDate": investor_position_detail_field.OpenDate,
                "OpenPrice": investor_position_detail_field.OpenPrice,
                "PositionProfitByDate": investor_position_detail_field.PositionProfitByDate,
                "PositionProfitByTrade": investor_position_detail_field.PositionProfitByTrade,
                "SettlementID": investor_position_detail_field.SettlementID,
                "SettlementPrice": investor_position_detail_field.SettlementPrice,
                "SpecPosiType": investor_position_detail_field.SpecPosiType,
                "TimeFirstVolume": investor_position_detail_field.TimeFirstVolume,
                "TradeID": investor_position_detail_field.TradeID,
                "TradeType": investor_position_detail_field.TradeType,
                "TradingDay": investor_position_detail_field.TradingDay,
                "Volume": investor_position_detail_field.Volume
            }
        response[Constant.InvestorPositionDetail] = result
        self.rsp_callback(response)

    def req_qry_exchange_margin_rate(self, request: dict[str, Any]) -> None:
        req, request_id = CTPObjectHelper.extract_request(request, Constant.QryExchangeMarginRate, tdapi.CThostFtdcQryExchangeMarginRateField)
        ret = self._api.ReqQryExchangeMarginRate(req, request_id)
        self.method_called(Constant.OnRspQryExchangeMarginRate, ret)

    def OnRspQryExchangeMarginRate(
            self,
            exchange_margin_rate_field: tdapi.CThostFtdcExchangeMarginRateField,
            rsp_info_field: tdapi.CThostFtdcRspInfoField,
            request_id: int,
            is_last: bool
    ):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspQryExchangeMarginRate, rsp_info_field, request_id, is_last)
        result = {}
        if exchange_margin_rate_field:
            result = {
                "BrokerID": exchange_margin_rate_field.BrokerID,
                "ExchangeID": exchange_margin_rate_field.ExchangeID,
                "HedgeFlag": exchange_margin_rate_field.HedgeFlag,
                "InstrumentID": exchange_margin_rate_field.InstrumentID,
                "LongMarginRatioByMoney": exchange_margin_rate_field.LongMarginRatioByMoney,
                "LongMarginRatioByVolume": exchange_margin_rate_field.LongMarginRatioByVolume,
                "ShortMarginRatioByMoney": exchange_margin_rate_field.ShortMarginRatioByMoney,
                "ShortMarginRatioByVolume": exchange_margin_rate_field.ShortMarginRatioByVolume
            }
        response[Constant.ExchangeMarginRate] = result
        self.rsp_callback(response)

    def req_qry_instrument_order_comm_rate(self, request: dict[str, Any]) -> None:
        req, request_id = CTPObjectHelper.extract_request(request, Constant.QryInstrumentOrderCommRate, tdapi.CThostFtdcQryInstrumentOrderCommRateField)
        ret = self._api.ReqQryInstrumentOrderCommRate(req, request_id)
        self.method_called(Constant.OnRspQryInstrumentOrderCommRate, ret)

    def OnRspQryInstrumentOrderCommRate(
            self,
            instrument_order_comm_rate_field: tdapi.CThostFtdcInstrumentOrderCommRateField,
            rsp_info_field: tdapi.CThostFtdcRspInfoField,
            request_id: int,
            is_last: bool
    ):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspQryInstrumentOrderCommRate, rsp_info_field, request_id, is_last)
        result = {}
        if instrument_order_comm_rate_field:
            result = {
                "BrokerID": instrument_order_comm_rate_field.BrokerID,
                "ExchangeID": instrument_order_comm_rate_field.ExchangeID,
                "HedgeFlag": instrument_order_comm_rate_field.HedgeFlag,
                "InstrumentID": instrument_order_comm_rate_field.InstrumentID,
                "InvestUnitID": instrument_order_comm_rate_field.InvestUnitID,
                "InvestorID": instrument_order_comm_rate_field.InvestorID,
                "InvestorRange": instrument_order_comm_rate_field.InvestorRange,
                "OrderActionCommByTrade": instrument_order_comm_rate_field.OrderActionCommByTrade,
                "OrderActionCommByVolume": instrument_order_comm_rate_field.OrderActionCommByVolume,
                "OrderCommByTrade": instrument_order_comm_rate_field.OrderCommByTrade,
                "OrderCommByVolume": instrument_order_comm_rate_field.OrderCommByVolume
            }
        response[Constant.InstrumentOrderCommRate] = result
        self.rsp_callback(response)

    def req_qry_option_instr_trade_cost(self, request: dict[str, Any]) -> None:
        req, request_id = CTPObjectHelper.extract_request(request, Constant.QryOptionInstrTradeCost, tdapi.CThostFtdcQryOptionInstrTradeCostField)
        ret = self._api.ReqQryOptionInstrTradeCost(req, request_id)
        self.method_called(Constant.OnRspQryOptionInstrTradeCost, ret)

    def OnRspQryOptionInstrTradeCost(
            self,
            option_instr_trade_cost_field: tdapi.CThostFtdcOptionInstrTradeCostField,
            rsp_info_field: tdapi.CThostFtdcRspInfoField,
            request_id: int,
            is_last: bool
    ):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspQryOptionInstrTradeCost, rsp_info_field, request_id, is_last)
        result = {}
        if option_instr_trade_cost_field:
            result = {
                "BrokerID": option_instr_trade_cost_field.BrokerID,
                "ExchFixedMargin": option_instr_trade_cost_field.ExchFixedMargin,
                "ExchMiniMargin": option_instr_trade_cost_field.ExchMiniMargin,
                "ExchangeID": option_instr_trade_cost_field.ExchangeID,
                "FixedMargin": option_instr_trade_cost_field.FixedMargin,
                "HedgeFlag": option_instr_trade_cost_field.HedgeFlag,
                "InstrumentID": option_instr_trade_cost_field.InstrumentID,
                "InvestUnitID": option_instr_trade_cost_field.InvestUnitID,
                "InvestorID": option_instr_trade_cost_field.InvestorID,
                "MiniMargin": option_instr_trade_cost_field.MiniMargin,
                "Royalty": option_instr_trade_cost_field.Royalty
            }
        response[Constant.OptionInstrTradeCost] = result
        self.rsp_callback(response)

    def req_qry_option_instr_comm_rate(self, request: dict[str, Any]) -> None:
        req, request_id = CTPObjectHelper.extract_request(request, Constant.QryOptionInstrCommRate, tdapi.CThostFtdcQryOptionInstrCommRateField)
        ret = self._api.ReqQryOptionInstrCommRate(req, request_id)
        self.method_called(Constant.OnRspQryOptionInstrCommRate, ret)

    def OnRspQryOptionInstrCommRate(
            self,
            option_instr_comm_rate_field: tdapi.CThostFtdcOptionInstrCommRateField,
            rsp_info_field: tdapi.CThostFtdcRspInfoField,
            request_id: int,
            is_last: bool
    ):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspQryOptionInstrCommRate, rsp_info_field, request_id, is_last)
        result = {}
        if option_instr_comm_rate_field:
            result = {
                "InvestorRange": option_instr_comm_rate_field.InvestorRange,
                "BrokerID": option_instr_comm_rate_field.BrokerID,
                "InvestorID": option_instr_comm_rate_field.InvestorID,
                "OpenRatioByMoney": option_instr_comm_rate_field.OpenRatioByMoney,
                "OpenRatioByVolume": option_instr_comm_rate_field.OpenRatioByVolume,
                "CloseRatioByMoney": option_instr_comm_rate_field.CloseRatioByMoney,
                "CloseRatioByVolume": option_instr_comm_rate_field.CloseRatioByVolume,
                "CloseTodayRatioByMoney": option_instr_comm_rate_field.CloseTodayRatioByMoney,
                "CloseTodayRatioByVolume": option_instr_comm_rate_field.CloseTodayRatioByVolume,
                "StrikeRatioByMoney": option_instr_comm_rate_field.StrikeRatioByMoney,
                "StrikeRatioByVolume": option_instr_comm_rate_field.StrikeRatioByVolume,
                "ExchangeID": option_instr_comm_rate_field.ExchangeID,
                "InvestUnitID": option_instr_comm_rate_field.InvestUnitID,
                "InstrumentID": option_instr_comm_rate_field.InstrumentID
            }
        response[Constant.OptionInstrCommRate] = result
        self.rsp_callback(response)

    def req_user_password_update(self, request: dict[str, Any]) -> None:
        req, request_id = CTPObjectHelper.extract_request(request, Constant.UserPasswordUpdate, tdapi.CThostFtdcUserPasswordUpdateField)
        ret = self._api.ReqUserPasswordUpdate(req, request_id)
        self.method_called(Constant.OnRspUserPasswordUpdate, ret)

    def OnRspUserPasswordUpdate(
            self,
            user_password_update_field: tdapi.CThostFtdcUserPasswordUpdateField,
            rsp_info_field: tdapi.CThostFtdcRspInfoField,
            request_id: int,
            is_last: bool
    ):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspUserPasswordUpdate, rsp_info_field, request_id, is_last)
        user_password_update = None
        if user_password_update_field:
            user_password_update = {
                "BrokerID": user_password_update_field.BrokerID,
                "UserID": user_password_update_field.UserID,
                "OldPassword": user_password_update_field.OldPassword,
                "NewPassword": user_password_update_field.NewPassword
            }
        response[Constant.UserPasswordUpdate] = user_password_update
        self.rsp_callback(response)

    def req_order_insert(self, request: dict[str, Any]) -> None:
        req, request_id = CTPObjectHelper.extract_request(request, Constant.InputOrder, tdapi.CThostFtdcInputOrderField)
        ret = self._api.ReqOrderInsert(req, request_id)
        self.method_called(Constant.OnRspOrderInsert, ret)

    def OnRspOrderInsert(
            self,
            input_order_field: tdapi.CThostFtdcInputOrderField,
            rsp_info_field: tdapi.CThostFtdcRspInfoField,
            request_id: int,
            is_last: bool
    ):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspOrderInsert, rsp_info_field, request_id, is_last)
        order_insert = {}
        if input_order_field:
            order_insert = build_order_insert_to_dict(input_order_field)
        response[Constant.InputOrder] = order_insert
        self.rsp_callback(response)

    def OnErrRtnOrderInsert(
            self,
            input_order_field: tdapi.CThostFtdcInputOrderField,
            rsp_info_field: tdapi.CThostFtdcRspInfoField
    ):
        response = CTPObjectHelper.build_response_dict(Constant.OnErrRtnOrderInsert, rsp_info_field)
        err_rtn_order_insert = {}
        if input_order_field:
            err_rtn_order_insert = build_order_insert_to_dict(input_order_field)
        response[Constant.InputOrder] = err_rtn_order_insert
        self.rsp_callback(response)

    def OnRtnOrder(self, order_field: tdapi.CThostFtdcOrderField):
        response = CTPObjectHelper.build_response_dict(Constant.OnRtnOrder)
        rtn_order = None
        if order_field:
            rtn_order = build_order_to_dict(order_field)
        response[Constant.Order] = rtn_order
        self.rsp_callback(response)

    def OnRtnTrade(self, trade_field: tdapi.CThostFtdcTradeField):
        response = CTPObjectHelper.build_response_dict(Constant.OnRtnTrade)
        rtn_trade = None
        if trade_field:
            rtn_trade = {
                "BrokerID": trade_field.BrokerID,
                "InvestorID": trade_field.InvestorID,
                "OrderRef": trade_field.OrderRef,
                "UserID": trade_field.UserID,
                "ExchangeID": trade_field.ExchangeID,
                "TradeID": trade_field.TradeID,
                "Direction": trade_field.Direction,
                "OrderSysID": trade_field.OrderSysID,
                "ParticipantID": trade_field.ParticipantID,
                "ClientID": trade_field.ClientID,
                "TradingRole": trade_field.TradingRole,
                "OffsetFlag": trade_field.OffsetFlag,
                "HedgeFlag": trade_field.HedgeFlag,
                "Price": trade_field.Price,
                "Volume": trade_field.Volume,
                "TradeDate": trade_field.TradeDate,
                "TradeTime": trade_field.TradeTime,
                "TradeType": trade_field.TradeType,
                "PriceSource": trade_field.PriceSource,
                "TraderID": trade_field.TraderID,
                "OrderLocalID": trade_field.OrderLocalID,
                "ClearingPartID": trade_field.ClearingPartID,
                "BusinessUnit": trade_field.BusinessUnit,
                "SequenceNo": trade_field.SequenceNo,
                "TradingDay": trade_field.TradingDay,
                "SettlementID": trade_field.SettlementID,
                "BrokerOrderSeq": trade_field.BrokerOrderSeq,
                "TradeSource": trade_field.TradeSource,
                "InvestUnitID": trade_field.InvestUnitID,
                "InstrumentID": trade_field.InstrumentID,
                "ExchangeInstID": trade_field.ExchangeInstID,
            }
        response[Constant.Trade] = rtn_trade
        self.rsp_callback(response)

    def req_order_action(self, request: dict[str, Any]) -> None:
        req, request_id = CTPObjectHelper.extract_request(request, Constant.InputOrderAction, tdapi.CThostFtdcInputOrderActionField)
        ret = self._api.ReqOrderAction(req, request_id)
        self.method_called(Constant.OnRspOrderAction, ret)

    def OnRspOrderAction(
            self,
            input_order_action_field: tdapi.CThostFtdcInputOrderActionField,
            rsp_info_field: tdapi.CThostFtdcRspInfoField,
            request_id: int,
            is_last: bool
    ):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspOrderAction, rsp_info_field, request_id, is_last)
        order_action = None
        if input_order_action_field:
            order_action = {
                "BrokerID": input_order_action_field.BrokerID,
                "InvestorID": input_order_action_field.InvestorID,
                "OrderActionRef": input_order_action_field.OrderActionRef,
                "OrderRef": input_order_action_field.OrderRef,
                "RequestID": input_order_action_field.RequestID,
                "FrontID": input_order_action_field.FrontID,
                "SessionID": input_order_action_field.SessionID,
                "ExchangeID": input_order_action_field.ExchangeID,
                "OrderSysID": input_order_action_field.OrderSysID,
                "ActionFlag": input_order_action_field.ActionFlag,
                "LimitPrice": input_order_action_field.LimitPrice,
                "VolumeChange": input_order_action_field.VolumeChange,
                "UserID": input_order_action_field.UserID,
                "InvestUnitID": input_order_action_field.InvestUnitID,
                "MacAddress": input_order_action_field.MacAddress,
                "InstrumentID": input_order_action_field.InstrumentID,
                "IPAddress": input_order_action_field.IPAddress
            }
        response[Constant.InputOrderAction] = order_action
        self.rsp_callback(response)

    def OnErrRtnOrderAction(
            self,
            order_action_filed: tdapi.CThostFtdcOrderActionField,
            rsp_info_field: tdapi.CThostFtdcRspInfoField
    ):
        response = CTPObjectHelper.build_response_dict(Constant.OnErrRtnOrderAction, rsp_info_field)
        order_action = None
        if order_action_filed:
            order_action = {
                "BrokerID": order_action_filed.BrokerID,
                "InvestorID": order_action_filed.InvestorID,
                "OrderActionRef": order_action_filed.OrderActionRef,
                "OrderRef": order_action_filed.OrderRef,
                "RequestID": order_action_filed.RequestID,
                "FrontID": order_action_filed.FrontID,
                "SessionID": order_action_filed.SessionID,
                "ExchangeID": order_action_filed.ExchangeID,
                "OrderSysID": order_action_filed.OrderSysID,
                "ActionFlag": order_action_filed.ActionFlag,
                "LimitPrice": order_action_filed.LimitPrice,
                "VolumeChange": order_action_filed.VolumeChange,
                "ActionDate": order_action_filed.ActionDate,
                "ActionTime": order_action_filed.ActionTime,
                "TraderID": order_action_filed.TraderID,
                "InstallID": order_action_filed.InstallID,
                "OrderLocalID": order_action_filed.OrderLocalID,
                "ActionLocalID": order_action_filed.ActionLocalID,
                "ParticipantID": order_action_filed.ParticipantID,
                "ClientID": order_action_filed.ClientID,
                "BusinessUnit": order_action_filed.BusinessUnit,
                "OrderActionStatus": order_action_filed.OrderActionStatus,
                "UserID": order_action_filed.UserID,
                "StatusMsg": order_action_filed.StatusMsg,
                "BranchID": order_action_filed.BranchID,
                "InvestUnitID": order_action_filed.InvestUnitID,
                "MacAddress": order_action_filed.MacAddress,
                "InstrumentID": order_action_filed.InstrumentID,
                "IPAddress": order_action_filed.IPAddress
            }
        response[Constant.OrderAction] = order_action
        self.rsp_callback(response)

    def req_qry_max_order_volume(self, request: dict[str, Any]) -> None:
        req, request_id = CTPObjectHelper.extract_request(request, Constant.QryMaxOrderVolume, tdapi.CThostFtdcQryMaxOrderVolumeField)
        ret = self._api.ReqQryMaxOrderVolume(req, request_id)
        self.method_called(Constant.OnRspQryMaxOrderVolume, ret)

    def OnRspQryMaxOrderVolume(
            self,
            qry_max_order_volume_filed: tdapi.CThostFtdcQryMaxOrderVolumeField,
            rsp_info_field: tdapi.CThostFtdcRspInfoField,
            request_id: int,
            is_last: bool
    ):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspQryMaxOrderVolume, rsp_info_field, request_id, is_last)
        max_order_volume = None
        if qry_max_order_volume_filed:
            max_order_volume = {
                "BrokerID": qry_max_order_volume_filed.BrokerID,
                "InvestorID": qry_max_order_volume_filed.InvestorID,
                "InstrumentID": qry_max_order_volume_filed.InstrumentID,
                "ExchangeID": qry_max_order_volume_filed.ExchangeID,
                "InvestUnitID": qry_max_order_volume_filed.InvestUnitID,
                "MaxVolume": qry_max_order_volume_filed.MaxVolume,
                "Direction": qry_max_order_volume_filed.Direction,
                "OffsetFlag": qry_max_order_volume_filed.OffsetFlag,
                "HedgeFlag": qry_max_order_volume_filed.HedgeFlag
            }
        response[Constant.QryMaxOrderVolume] = max_order_volume
        self.rsp_callback(response)

    def req_qry_order(self, request: dict[str, Any]) -> None:
        req, request_id = CTPObjectHelper.extract_request(request, Constant.QryOrder, tdapi.CThostFtdcQryOrderField)
        ret = self._api.ReqQryOrder(req, request_id)
        self.method_called(Constant.OnRspQryOrder, ret)

    def OnRspQryOrder(
            self, order_field: tdapi.CThostFtdcOrderField,
            rsp_info_field: tdapi.CThostFtdcRspInfoField,
            request_id: int,
            is_last: bool
    ):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspQryOrder, rsp_info_field, request_id, is_last)
        qry_order = {}
        if order_field:
            qry_order = build_order_to_dict(order_field)
        response[Constant.Order] = qry_order
        self.rsp_callback(response)


    def req_qry_trade(self, request: dict[str, Any]) -> None:
        req, request_id = CTPObjectHelper.extract_request(request, Constant.QryTrade, tdapi.CThostFtdcQryTradeField)
        ret = self._api.ReqQryTrade(req, request_id)
        self.method_called(Constant.OnRspQryTrade, ret)

    def OnRspQryTrade(self, trade_field: tdapi.CThostFtdcTradeField, rsp_info_field: tdapi.CThostFtdcRspInfoField, request_id: int, is_last: bool):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspQryTrade, rsp_info_field, request_id, is_last)
        qry_trade = {}
        if trade_field:
            qry_trade = {
                "BrokerID": trade_field.BrokerID,
                "BrokerOrderSeq": trade_field.BrokerOrderSeq,
                "BusinessUnit": trade_field.BusinessUnit,
                "ClearingPartID": trade_field.ClearingPartID,
                "ClientID": trade_field.ClientID,
                "Direction": trade_field.Direction,
                "ExchangeID": trade_field.ExchangeID,
                "ExchangeInstID": trade_field.ExchangeInstID,
                "HedgeFlag": trade_field.HedgeFlag,
                "InstrumentID": trade_field.InstrumentID,
                "InvestUnitID": trade_field.InvestUnitID,
                "InvestorID": trade_field.InvestorID,
                "OffsetFlag": trade_field.OffsetFlag,
                "OrderLocalID": trade_field.OrderLocalID,
                "OrderRef": trade_field.OrderRef,
                "OrderSysID": trade_field.OrderSysID,
                "ParticipantID": trade_field.ParticipantID,
                "Price": trade_field.Price,
                "PriceSource": trade_field.PriceSource,
                "SequenceNo": trade_field.SequenceNo,
                "SettlementID": trade_field.SettlementID,
                "TradeDate": trade_field.TradeDate,
                "TradeID": trade_field.TradeID,
                "TradeSource": trade_field.TradeSource,
                "TradeTime": trade_field.TradeTime,
                "TradeType": trade_field.TradeType,
                "TraderID": trade_field.TraderID,
                "TradingDay": trade_field.TradingDay,
                "TradingRole": trade_field.TradingRole,
                "UserID": trade_field.UserID,
                "Volume": trade_field.Volume
                }
        response[Constant.Trade] = qry_trade
        self.rsp_callback(response)

    def req_qry_investor_position(self, request: dict[str, Any]) -> None:
        req, request_id = CTPObjectHelper.extract_request(request, Constant.QryInvestorPosition, tdapi.CThostFtdcQryInvestorPositionField)
        ret = self._api.ReqQryInvestorPosition(req, request_id)
        self.method_called(Constant.OnRspQryInvestorPosition, ret)

    def OnRspQryInvestorPosition(
            self,
            investor_position_field: tdapi.CThostFtdcInvestorPositionField,
            rsp_info_field: tdapi.CThostFtdcRspInfoField,
            request_id: int,
            is_last: bool
    ):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspQryInvestorPosition, rsp_info_field, request_id, is_last)
        qry_investor_position = None
        if investor_position_field:
            qry_investor_position = {
                "AbandonFrozen": investor_position_field.AbandonFrozen,
                "BrokerID": investor_position_field.BrokerID,
                "CashIn": investor_position_field.CashIn,
                "CloseAmount": investor_position_field.CloseAmount,
                "CloseProfit": investor_position_field.CloseProfit,
                "CloseProfitByDate": investor_position_field.CloseProfitByDate,
                "CloseProfitByTrade": investor_position_field.CloseProfitByTrade,
                "CloseVolume": investor_position_field.CloseVolume,
                "CombLongFrozen": investor_position_field.CombLongFrozen,
                "CombPosition": investor_position_field.CombPosition,
                "CombShortFrozen": investor_position_field.CombShortFrozen,
                "Commission": investor_position_field.Commission,
                "ExchangeID": investor_position_field.ExchangeID,
                "ExchangeMargin": investor_position_field.ExchangeMargin,
                "FrozenCash": investor_position_field.FrozenCash,
                "FrozenCommission": investor_position_field.FrozenCommission,
                "FrozenMargin": investor_position_field.FrozenMargin,
                "HedgeFlag": investor_position_field.HedgeFlag,
                "InstrumentID": investor_position_field.InstrumentID,
                "InvestUnitID": investor_position_field.InvestUnitID,
                "InvestorID": investor_position_field.InvestorID,
                "LongFrozen": investor_position_field.LongFrozen,
                "LongFrozenAmount": investor_position_field.LongFrozenAmount,
                "MarginRateByMoney": investor_position_field.MarginRateByMoney,
                "MarginRateByVolume": investor_position_field.MarginRateByVolume,
                "OpenAmount": investor_position_field.OpenAmount,
                "OpenCost": investor_position_field.OpenCost,
                "OpenVolume": investor_position_field.OpenVolume,
                "PosiDirection": investor_position_field.PosiDirection,
                "Position": investor_position_field.Position,
                "PositionCost": investor_position_field.PositionCost,
                "PositionCostOffset": investor_position_field.PositionCostOffset,
                "PositionDate": investor_position_field.PositionDate,
                "PositionProfit": investor_position_field.PositionProfit,
                "PreMargin": investor_position_field.PreMargin,
                "PreSettlementPrice": investor_position_field.PreSettlementPrice,
                "SettlementID": investor_position_field.SettlementID,
                "SettlementPrice": investor_position_field.SettlementPrice,
                "ShortFrozen": investor_position_field.ShortFrozen,
                "ShortFrozenAmount": investor_position_field.ShortFrozenAmount,
                "StrikeFrozen": investor_position_field.StrikeFrozen,
                "StrikeFrozenAmount": investor_position_field.StrikeFrozenAmount,
                "TasPosition": investor_position_field.TasPosition,
                "TasPositionCost": investor_position_field.TasPositionCost,
                "TodayPosition": investor_position_field.TodayPosition,
                "TradingDay": investor_position_field.TradingDay,
                "UseMargin": investor_position_field.UseMargin,
                "YdPosition": investor_position_field.YdPosition,
                "YdStrikeFrozen": investor_position_field.YdStrikeFrozen
                }
        response[Constant.InvestorPosition] = qry_investor_position
        self.rsp_callback(response)

    def req_qry_trading_account(self, request: dict[str, Any]) -> None:
        req, request_id = CTPObjectHelper.extract_request(request, Constant.QryTradingAccount, tdapi.CThostFtdcQryTradingAccountField)
        ret = self._api.ReqQryTradingAccount(req, request_id)
        self.method_called(Constant.OnRspQryTradingAccount, ret)

    def OnRspQryTradingAccount(
            self,
            trading_account_field: tdapi.CThostFtdcTradingAccountField,
            rsp_info_field: tdapi.CThostFtdcRspInfoField,
            request_id: int,
            is_last: bool
    ):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspQryTradingAccount, rsp_info_field, request_id, is_last)
        qry_trading_account = None
        if trading_account_field:
            qry_trading_account = {
                "AccountID": trading_account_field.AccountID,
                "Available": trading_account_field.Available,
                "Balance": trading_account_field.Balance,
                "BizType": trading_account_field.BizType,
                "BrokerID": trading_account_field.BrokerID,
                "CashIn": trading_account_field.CashIn,
                "CloseProfit": trading_account_field.CloseProfit,
                "Commission": trading_account_field.Commission,
                "Credit": trading_account_field.Credit,
                "CurrMargin": trading_account_field.CurrMargin,
                "CurrencyID": trading_account_field.CurrencyID,
                "DeliveryMargin": trading_account_field.DeliveryMargin,
                "Deposit": trading_account_field.Deposit,
                "ExchangeDeliveryMargin": trading_account_field.ExchangeDeliveryMargin,
                "ExchangeMargin": trading_account_field.ExchangeMargin,
                "FrozenCash": trading_account_field.FrozenCash,
                "FrozenCommission": trading_account_field.FrozenCommission,
                "FrozenMargin": trading_account_field.FrozenMargin,
                "FrozenSwap": trading_account_field.FrozenSwap,
                "FundMortgageAvailable": trading_account_field.FundMortgageAvailable,
                "FundMortgageIn": trading_account_field.FundMortgageIn,
                "FundMortgageOut": trading_account_field.FundMortgageOut,
                "Interest": trading_account_field.Interest,
                "InterestBase": trading_account_field.InterestBase,
                "Mortgage": trading_account_field.Mortgage,
                "MortgageableFund": trading_account_field.MortgageableFund,
                "PositionProfit": trading_account_field.PositionProfit,
                "PreBalance": trading_account_field.PreBalance,
                "PreCredit": trading_account_field.PreCredit,
                "PreDeposit": trading_account_field.PreDeposit,
                "PreFundMortgageIn": trading_account_field.PreFundMortgageIn,
                "PreFundMortgageOut": trading_account_field.PreFundMortgageOut,
                "PreMargin": trading_account_field.PreMargin,
                "PreMortgage": trading_account_field.PreMortgage,
                "RemainSwap": trading_account_field.RemainSwap,
                "Reserve": trading_account_field.Reserve,
                "ReserveBalance": trading_account_field.ReserveBalance,
                "SettlementID": trading_account_field.SettlementID,
                "SpecProductCloseProfit": trading_account_field.SpecProductCloseProfit,
                "SpecProductCommission": trading_account_field.SpecProductCommission,
                "SpecProductExchangeMargin": trading_account_field.SpecProductExchangeMargin,
                "SpecProductFrozenCommission": trading_account_field.SpecProductFrozenCommission,
                "SpecProductFrozenMargin": trading_account_field.SpecProductFrozenMargin,
                "SpecProductMargin": trading_account_field.SpecProductMargin,
                "SpecProductPositionProfit": trading_account_field.SpecProductPositionProfit,
                "SpecProductPositionProfitByAlg": trading_account_field.SpecProductPositionProfitByAlg,
                "TradingDay": trading_account_field.TradingDay,
                "Withdraw": trading_account_field.Withdraw,
                "WithdrawQuota": trading_account_field.WithdrawQuota
                }
        response[Constant.TradingAccount] = qry_trading_account
        self.rsp_callback(response)

    def req_qry_investor(self, request: dict[str, Any]) -> None:
        req, request_id = CTPObjectHelper.extract_request(request, Constant.QryInvestor, tdapi.CThostFtdcQryInvestorField)
        ret = self._api.ReqQryInvestor(req, request_id)
        self.method_called(Constant.OnRspQryInvestor, ret)

    def OnRspQryInvestor(
            self,
            investor_field: tdapi.CThostFtdcInvestorField,
            rsp_info_field: tdapi.CThostFtdcRspInfoField,
            request_id: int,
            is_last: bool
    ):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspQryInvestor, rsp_info_field, request_id, is_last)
        qry_investor = None
        if investor_field:
            qry_investor = {
                "Address": investor_field.Address,
                "BrokerID": investor_field.BrokerID,
                "CommModelID": investor_field.CommModelID,
                "IdentifiedCardNo": investor_field.IdentifiedCardNo,
                "IdentifiedCardType": investor_field.IdentifiedCardType,
                "InvestorGroupID": investor_field.InvestorGroupID,
                "InvestorID": investor_field.InvestorID,
                "InvestorName": investor_field.InvestorName,
                "IsActive": investor_field.IsActive,
                "MarginModelID": investor_field.MarginModelID,
                "Mobile": investor_field.Mobile,
                "OpenDate": investor_field.OpenDate,
                "Telephone": investor_field.Telephone
                }
        response[Constant.Investor] = qry_investor
        self.rsp_callback(response)

    def req_qry_trading_code(self, request: dict[str, Any]) -> None:
        req, request_id = CTPObjectHelper.extract_request(request, Constant.QryTradingCode, tdapi.CThostFtdcQryTradingCodeField)
        ret = self._api.ReqQryTradingCode(req, request_id)
        self.method_called(Constant.OnRspQryTradingCode, ret)

    def OnRspQryTradingCode(
            self,
            trading_code_field: tdapi.CThostFtdcTradingCodeField,
            rsp_info_field: tdapi.CThostFtdcRspInfoField,
            request_id: int,
            is_last: bool
    ):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspQryTradingCode, rsp_info_field, request_id, is_last)
        qry_trading_code = None
        if trading_code_field:
            qry_trading_code = {
                "BizType": trading_code_field.BizType,
                "BranchID": trading_code_field.BranchID,
                "BrokerID": trading_code_field.BrokerID,
                "ClientID": trading_code_field.ClientID,
                "ClientIDType": trading_code_field.ClientIDType,
                "ExchangeID": trading_code_field.ExchangeID,
                "InvestUnitID": trading_code_field.InvestUnitID,
                "InvestorID": trading_code_field.InvestorID,
                "IsActive": trading_code_field.IsActive
                }
        response[Constant.TradingCode] = qry_trading_code
        self.rsp_callback(response)

    def req_qry_instrument_margin_rate(self, request: dict[str, Any]) -> None:
        req, request_id = CTPObjectHelper.extract_request(request, Constant.QryInstrumentMarginRate, tdapi.CThostFtdcQryInstrumentMarginRateField)
        ret = self._api.ReqQryInstrumentMarginRate(req, request_id)
        self.method_called(Constant.OnRspQryInstrumentMarginRate, ret)

    def OnRspQryInstrumentMarginRate(
            self,
            instrument_margin_rate: tdapi.CThostFtdcInstrumentMarginRateField,
            rsp_info_field: tdapi.CThostFtdcRspInfoField,
            request_id: int,
            is_last: bool
    ):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspQryInstrumentMarginRate, rsp_info_field, request_id, is_last)
        qry_instrument_margin_rate = None
        if instrument_margin_rate:
            qry_instrument_margin_rate = {
                "BrokerID": instrument_margin_rate.BrokerID,
                "ExchangeID": instrument_margin_rate.ExchangeID,
                "HedgeFlag": instrument_margin_rate.HedgeFlag,
                "InstrumentID": instrument_margin_rate.InstrumentID,
                "InvestUnitID": instrument_margin_rate.InvestUnitID,
                "InvestorID": instrument_margin_rate.InvestorID,
                "InvestorRange": instrument_margin_rate.InvestorRange,
                "IsRelative": instrument_margin_rate.IsRelative,
                "LongMarginRatioByMoney": instrument_margin_rate.LongMarginRatioByMoney,
                "LongMarginRatioByVolume": instrument_margin_rate.LongMarginRatioByVolume,
                "ShortMarginRatioByMoney": instrument_margin_rate.ShortMarginRatioByMoney,
                "ShortMarginRatioByVolume": instrument_margin_rate.ShortMarginRatioByVolume
                }
        response[Constant.InstrumentMarginRate] = qry_instrument_margin_rate
        self.rsp_callback(response)

    def req_qry_instrument_commission_rate(self, request: dict[str, Any]) -> None:
        req, request_id = CTPObjectHelper.extract_request(request, Constant.QryInstrumentCommissionRate, tdapi.CThostFtdcQryInstrumentCommissionRateField)
        ret = self._api.ReqQryInstrumentCommissionRate(req, request_id)
        self.method_called(Constant.OnRspQryInstrumentCommissionRate, ret)

    def OnRspQryInstrumentCommissionRate(
            self,
            instrument_commission_rate_field: tdapi.CThostFtdcInstrumentCommissionRateField,
            rsp_info_field: tdapi.CThostFtdcRspInfoField,
            request_id: int,
            is_last: bool
    ):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspQryInstrumentCommissionRate, rsp_info_field, request_id, is_last)
        qry_instrument_commission_rate = None
        if instrument_commission_rate_field:
            qry_instrument_commission_rate = {
                "BizType": instrument_commission_rate_field.BizType,
                "BrokerID": instrument_commission_rate_field.BrokerID,
                "CloseRatioByMoney": instrument_commission_rate_field.CloseRatioByMoney,
                "CloseRatioByVolume": instrument_commission_rate_field.CloseRatioByVolume,
                "CloseTodayRatioByMoney": instrument_commission_rate_field.CloseTodayRatioByMoney,
                "CloseTodayRatioByVolume": instrument_commission_rate_field.CloseTodayRatioByVolume,
                "ExchangeID": instrument_commission_rate_field.ExchangeID,
                "InstrumentID": instrument_commission_rate_field.InstrumentID,
                "InvestUnitID": instrument_commission_rate_field.InvestUnitID,
                "InvestorID": instrument_commission_rate_field.InvestorID,
                "InvestorRange": instrument_commission_rate_field.InvestorRange,
                "OpenRatioByMoney": instrument_commission_rate_field.OpenRatioByMoney,
                "OpenRatioByVolume": instrument_commission_rate_field.OpenRatioByVolume
                }
        response[Constant.InstrumentCommissionRate] = qry_instrument_commission_rate
        self.rsp_callback(response)
