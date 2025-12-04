import logging
from typing import Callable, Any

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
            rsp_info: tdapi.CThostFtdcRspInfoField,
            request_id: int,
            is_last: bool
    ):
        """
        处理认证请求的响应回调

        Args:
            rsp_authenticate_field: 认证响应字段，包含认证相关信息
            rsp_info: 响应信息字段，包含错误代码和错误消息
            request_id: 请求ID，用于标识对应的请求
            is_last: 标识是否为该请求的最后一个响应包

        Returns:
            None: 此方法无返回值，认证结果通过日志输出和后续操作处理
        """
        if rsp_info is None or rsp_info.ErrorID == 0:
            logging.info("authenticate success, start to login")
            self.login()
        else:
            logging.info("authenticate failed, please try again")
            self.processConnectResult(Constant.OnRspAuthenticate, rsp_info)

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
            rsp_user_login: tdapi.CThostFtdcRspUserLoginField,
            rsp_info: tdapi.CThostFtdcRspInfoField,
            request_id: int,
            is_last: bool
    ):
        """
        处理用户登录响应回调

        当CTP交易接口返回登录响应时被调用，处理登录成功或失败的情况

        Args:
            rsp_user_login: 用户登录响应信息，包含登录结果相关字段
            rsp_info: 响应信息，包含错误码和错误消息
            request_id: 请求ID，用于标识对应的请求
            is_last: 指示是否为该请求的最后一个响应片段

        Returns:
            None: 该回调函数不返回任何值，结果通过异步事件处理
        """
        if rsp_info is None or rsp_info.ErrorID == 0:
            logging.info("loging success, start to confirm settlement info")
            self.settlementConfirm()
            self.processConnectResult(Constant.OnRspUserLogin, rsp_info, rsp_user_login)
        else:
            self.processConnectResult(Constant.OnRspUserLogin, rsp_info)
            logging.info("login failed, please try again")

    def settlementConfirm(self):
        req = tdapi.CThostFtdcSettlementInfoConfirmField()
        req.BrokerID = self._broker_id
        req.InvestorID = self._user_id
        self._api.ReqSettlementInfoConfirm(req, 0)

    def OnRspQrySettlementInfoConfirm(
            self,
            pSettlementInfoConfirm: tdapi.CThostFtdcSettlementInfoConfirmField,
            pRspInfo: tdapi.CThostFtdcRspInfoField,
            nRequestID: int,
            bIsLast: bool
    ):
        logging.info("confirm settlement info success")
        if pRspInfo is not None:
            logging.info(f"settlemnt confirm rsp info, ErrorID: {pRspInfo.ErrorID}, ErrorMsg: {pRspInfo.ErrorMsg}")

    def processConnectResult(
            self,
            messageType: str,
            pRspInfo: tdapi.CThostFtdcRspInfoField,
            pRspUserLogin: tdapi.CThostFtdcRspUserLoginField = None
    ):
        response = CTPObjectHelper.build_response_dict(messageType, pRspInfo, 0, True)
        if pRspUserLogin:
            response[Constant.RspUserLogin] = {
                "TradingDay": pRspUserLogin.TradingDay,
                "LoginTime": pRspUserLogin.LoginTime,
                "BrokerID": pRspUserLogin.BrokerID,
                "UserID": pRspUserLogin.UserID,
                "SystemName": pRspUserLogin.SystemName,
                "FrontID": pRspUserLogin.FrontID,
                "SessionID": pRspUserLogin.SessionID,
                "MaxOrderRef": pRspUserLogin.MaxOrderRef,
                "SHFETime": pRspUserLogin.SHFETime,
                "DCETime": pRspUserLogin.DCETime,
                "CZCETime": pRspUserLogin.CZCETime,
                "FFEXTime": pRspUserLogin.FFEXTime,
                "INETime": pRspUserLogin.INETime
            }

        self.rsp_callback(response)

    def reqQryInstrument(self, request: dict[str, Any]) -> int:
        req, requestId = CTPObjectHelper.extract_request(request, Constant.QryInstrument, tdapi.CThostFtdcQryInstrumentField)
        ret = self._api.ReqQryInstrument(req, requestId)
        self.method_called(Constant.OnRspQryInstrument, ret)

    def OnRspQryInstrument(self, pInstrument: tdapi.CThostFtdcInstrumentField, pRspInfo: tdapi.CThostFtdcRspInfoField, nRequestID: int, bIsLast: bool):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspQryInstrument, pRspInfo, nRequestID, bIsLast)
        instrument = {}
        if pInstrument:
            instrument = {
                "InstrumentID": pInstrument.InstrumentID,
                "ExchangeID": pInstrument.ExchangeID,
                "InstrumentName": pInstrument.InstrumentName,
                "ExchangeInstID": pInstrument.ExchangeInstID,
                "ProductID": pInstrument.ProductID,
                "ProductClass": pInstrument.ProductClass,
                "DeliveryYear": pInstrument.DeliveryYear,
                "DeliveryMonth": pInstrument.DeliveryMonth,
                "MaxMarketOrderVolume": pInstrument.MaxMarketOrderVolume,
                "MinMarketOrderVolume": pInstrument.MinMarketOrderVolume,
                "MaxLimitOrderVolume": pInstrument.MaxLimitOrderVolume,
                "MinLimitOrderVolume": pInstrument.MinLimitOrderVolume,
                "VolumeMultiple": pInstrument.VolumeMultiple,
                "PriceTick": pInstrument.PriceTick,
                "CreateDate": pInstrument.CreateDate,
                "OpenDate": pInstrument.OpenDate,
                "ExpireDate": pInstrument.ExpireDate,
                "StartDelivDate": pInstrument.StartDelivDate,
                "EndDelivDate": pInstrument.EndDelivDate,
                "InstLifePhase": pInstrument.InstLifePhase,
                "IsTrading": pInstrument.IsTrading,
                "PositionType": pInstrument.PositionType,
                "PositionDateType": pInstrument.PositionDateType,
                "LongMarginRatio": pInstrument.LongMarginRatio,
                "ShortMarginRatio": pInstrument.ShortMarginRatio,
                "MaxMarginSideAlgorithm": pInstrument.MaxMarginSideAlgorithm,
                "UnderlyingInstrID": pInstrument.UnderlyingInstrID,
                "StrikePrice": pInstrument.StrikePrice,
                "OptionsType": pInstrument.OptionsType,
                "UnderlyingMultiple": pInstrument.UnderlyingMultiple,
                "CombinationType": pInstrument.CombinationType
            }
        response[Constant.Instrument] = instrument
        self.rsp_callback(response)

    def ReqQryExchange(self, request: dict[str, Any]) -> int:
        req, requestId = CTPObjectHelper.extract_request(request, Constant.QryExchange, tdapi.CThostFtdcQryExchangeField)
        ret = self._api.ReqQryExchange(req, requestId)
        self.method_called(Constant.OnRspQryExchange, ret)

    def OnRspQryExchange(self, pExchange: tdapi.CThostFtdcExchangeField, pRspInfo: tdapi.CThostFtdcRspInfoField, nRequestID: int, bIsLast: bool):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspQryExchange, pRspInfo, nRequestID, bIsLast)
        result = {}
        if pExchange:
            result = {
                "ExchangeID": pExchange.ExchangeID,
                "ExchangeName": pExchange.ExchangeName,
                "ExchangeProperty": pExchange.ExchangeProperty
            }
        response[Constant.Exchange] = result
        self.rsp_callback(response)

    def ReqQryProduct(self, request: dict[str, Any]) -> int:
        req, requestId = CTPObjectHelper.extract_request(request, Constant.QryProduct, tdapi.CThostFtdcQryProductField)
        ret = self._api.ReqQryProduct(req, requestId)
        self.method_called(Constant.OnRspQryProduct, ret)

    def OnRspQryProduct(self, pProduct: tdapi.CThostFtdcProductField, pRspInfo: tdapi.CThostFtdcRspInfoField, nRequestID: int, bIsLast: bool):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspQryProduct, pRspInfo, nRequestID, bIsLast)
        result = {}
        if pProduct:
            result = {
                "CloseDealType": pProduct.CloseDealType,
                "ExchangeID": pProduct.ExchangeID,
                "ExchangeProductID": pProduct.ExchangeProductID,
                "MaxLimitOrderVolume": pProduct.MaxLimitOrderVolume,
                "MaxMarketOrderVolume": pProduct.MaxMarketOrderVolume,
                "MinLimitOrderVolume": pProduct.MinLimitOrderVolume,
                "MinMarketOrderVolume": pProduct.MinMarketOrderVolume,
                "MortgageFundUseRange": pProduct.MortgageFundUseRange,
                "OpenLimitControlLevel": pProduct.OpenLimitControlLevel,
                "OrderFreqControlLevel": pProduct.OrderFreqControlLevel,
                "PositionDateType": pProduct.PositionDateType,
                "PositionType": pProduct.PositionType,
                "PriceTick": pProduct.PriceTick,
                "ProductClass": pProduct.ProductClass,
                "ProductID": pProduct.ProductID,
                "ProductName": pProduct.ProductName,
                "TradeCurrencyID": pProduct.TradeCurrencyID,
                "UnderlyingMultiple": pProduct.UnderlyingMultiple,
                "VolumeMultiple": pProduct.VolumeMultiple
            }
        response[Constant.Product] = result
        self.rsp_callback(response)

    def ReqQryDepthMarketData(self, request: dict[str, Any]) -> int:
        req, requestId = CTPObjectHelper.extract_request(request, Constant.QryDepthMarketData, tdapi.CThostFtdcQryDepthMarketDataField)
        ret = self._api.ReqQryDepthMarketData(req, requestId)
        self.method_called(Constant.OnRspQryDepthMarketData, ret)

    def OnRspQryDepthMarketData(self, pDepthMarketData: tdapi.CThostFtdcDepthMarketDataField, pRspInfo: tdapi.CThostFtdcRspInfoField, nRequestID: int, bIsLast: bool):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspQryDepthMarketData, pRspInfo, nRequestID, bIsLast)
        result = {}
        if pDepthMarketData:
            result = {
                "ActionDay": pDepthMarketData.ActionDay,
                "AskPrice1": MathHelper.adjust_price(pDepthMarketData.AskPrice1),
                "AskPrice2": MathHelper.adjust_price(pDepthMarketData.AskPrice2),
                "AskPrice3": MathHelper.adjust_price(pDepthMarketData.AskPrice3),
                "AskPrice4": MathHelper.adjust_price(pDepthMarketData.AskPrice4),
                "AskPrice5": MathHelper.adjust_price(pDepthMarketData.AskPrice5),
                "AskVolume1": pDepthMarketData.AskVolume1,
                "AskVolume2": pDepthMarketData.AskVolume2,
                "AskVolume3": pDepthMarketData.AskVolume3,
                "AskVolume4": pDepthMarketData.AskVolume4,
                "AskVolume5": pDepthMarketData.AskVolume5,
                "AveragePrice": MathHelper.adjust_price(pDepthMarketData.AveragePrice),
                "BandingLowerPrice": MathHelper.adjust_price(pDepthMarketData.BandingLowerPrice),
                "BandingUpperPrice": MathHelper.adjust_price(pDepthMarketData.BandingUpperPrice),
                "BidPrice1": MathHelper.adjust_price(pDepthMarketData.BidPrice1),
                "BidPrice2": MathHelper.adjust_price(pDepthMarketData.BidPrice2),
                "BidPrice3": MathHelper.adjust_price(pDepthMarketData.BidPrice3),
                "BidPrice4": MathHelper.adjust_price(pDepthMarketData.BidPrice4),
                "BidPrice5": MathHelper.adjust_price(pDepthMarketData.BidPrice5),
                "BidVolume1": pDepthMarketData.BidVolume1,
                "BidVolume2": pDepthMarketData.BidVolume2,
                "BidVolume3": pDepthMarketData.BidVolume3,
                "BidVolume4": pDepthMarketData.BidVolume4,
                "BidVolume5": pDepthMarketData.BidVolume5,
                "ClosePrice": MathHelper.adjust_price(pDepthMarketData.ClosePrice),
                "CurrDelta": pDepthMarketData.CurrDelta,
                "ExchangeID": pDepthMarketData.ExchangeID,
                "ExchangeInstID": pDepthMarketData.ExchangeInstID,
                "HighestPrice": MathHelper.adjust_price(pDepthMarketData.HighestPrice),
                "InstrumentID": pDepthMarketData.InstrumentID,
                "LastPrice": MathHelper.adjust_price(pDepthMarketData.LastPrice),
                "LowerLimitPrice": MathHelper.adjust_price(pDepthMarketData.LowerLimitPrice),
                "LowestPrice": MathHelper.adjust_price(pDepthMarketData.LowestPrice),
                "OpenInterest": pDepthMarketData.OpenInterest,
                "OpenPrice": MathHelper.adjust_price(pDepthMarketData.OpenPrice),
                "PreClosePrice": MathHelper.adjust_price(pDepthMarketData.PreClosePrice),
                "PreDelta": pDepthMarketData.PreDelta,
                "PreOpenInterest": pDepthMarketData.PreOpenInterest,
                "PreSettlementPrice": pDepthMarketData.PreSettlementPrice,
                "SettlementPrice": MathHelper.adjust_price(pDepthMarketData.SettlementPrice),
                "TradingDay": pDepthMarketData.TradingDay,
                "Turnover": pDepthMarketData.Turnover,
                "UpdateMillisec": pDepthMarketData.UpdateMillisec,
                "UpdateTime": pDepthMarketData.UpdateTime,
                "UpperLimitPrice": MathHelper.adjust_price(pDepthMarketData.UpperLimitPrice),
                "Volume": pDepthMarketData.Volume
            }
        response[Constant.DepthMarketData] = result
        self.rsp_callback(response)

    def ReqQryInvestorPositionDetail(self, request: dict[str, Any]) -> int:
        req, requestId = CTPObjectHelper.extract_request(request, Constant.QryInvestorPositionDetail, tdapi.CThostFtdcQryInvestorPositionDetailField)
        ret = self._api.ReqQryInvestorPositionDetail(req, requestId)
        self.method_called(Constant.OnRspQryInvestorPositionDetail, ret)

    def OnRspQryInvestorPositionDetail(self, pInvestorPositionDetail: tdapi.CThostFtdcInvestorPositionDetailField, pRspInfo: tdapi.CThostFtdcRspInfoField, nRequestID: int, bIsLast: bool):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspQryInvestorPositionDetail, pRspInfo, nRequestID, bIsLast)
        result = {}
        if pInvestorPositionDetail:
            result = {
                "BrokerID": pInvestorPositionDetail.BrokerID,
                "CloseAmount": pInvestorPositionDetail.CloseAmount,
                "CloseProfitByDate": pInvestorPositionDetail.CloseProfitByDate,
                "CloseProfitByTrade": pInvestorPositionDetail.CloseProfitByTrade,
                "CloseVolume": pInvestorPositionDetail.CloseVolume,
                "CombInstrumentID": pInvestorPositionDetail.CombInstrumentID,
                "Direction": pInvestorPositionDetail.Direction,
                "ExchMargin": pInvestorPositionDetail.ExchMargin,
                "ExchangeID": pInvestorPositionDetail.ExchangeID,
                "HedgeFlag": pInvestorPositionDetail.HedgeFlag,
                "InstrumentID": pInvestorPositionDetail.InstrumentID,
                "InvestUnitID": pInvestorPositionDetail.InvestUnitID,
                "InvestorID": pInvestorPositionDetail.InvestorID,
                "LastSettlementPrice": pInvestorPositionDetail.LastSettlementPrice,
                "Margin": pInvestorPositionDetail.Margin,
                "MarginRateByMoney": pInvestorPositionDetail.MarginRateByMoney,
                "MarginRateByVolume": pInvestorPositionDetail.MarginRateByVolume,
                "OpenDate": pInvestorPositionDetail.OpenDate,
                "OpenPrice": pInvestorPositionDetail.OpenPrice,
                "PositionProfitByDate": pInvestorPositionDetail.PositionProfitByDate,
                "PositionProfitByTrade": pInvestorPositionDetail.PositionProfitByTrade,
                "SettlementID": pInvestorPositionDetail.SettlementID,
                "SettlementPrice": pInvestorPositionDetail.SettlementPrice,
                "SpecPosiType": pInvestorPositionDetail.SpecPosiType,
                "TimeFirstVolume": pInvestorPositionDetail.TimeFirstVolume,
                "TradeID": pInvestorPositionDetail.TradeID,
                "TradeType": pInvestorPositionDetail.TradeType,
                "TradingDay": pInvestorPositionDetail.TradingDay,
                "Volume": pInvestorPositionDetail.Volume
            }
        response[Constant.InvestorPositionDetail] = result
        self.rsp_callback(response)

    def ReqQryExchangeMarginRate(self, request: dict[str, Any]) -> int:
        req, requestId = CTPObjectHelper.extract_request(request, Constant.QryExchangeMarginRate, tdapi.CThostFtdcQryExchangeMarginRateField)
        ret = self._api.ReqQryExchangeMarginRate(req, requestId)
        self.method_called(Constant.OnRspQryExchangeMarginRate, ret)

    def OnRspQryExchangeMarginRate(self, pExchangeMarginRate: tdapi.CThostFtdcExchangeMarginRateField, pRspInfo: tdapi.CThostFtdcRspInfoField, nRequestID: int, bIsLast: bool):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspQryExchangeMarginRate, pRspInfo, nRequestID, bIsLast)
        result = {}
        if pExchangeMarginRate:
            result = {
                "BrokerID": pExchangeMarginRate.BrokerID,
                "ExchangeID": pExchangeMarginRate.ExchangeID,
                "HedgeFlag": pExchangeMarginRate.HedgeFlag,
                "InstrumentID": pExchangeMarginRate.InstrumentID,
                "LongMarginRatioByMoney": pExchangeMarginRate.LongMarginRatioByMoney,
                "LongMarginRatioByVolume": pExchangeMarginRate.LongMarginRatioByVolume,
                "ShortMarginRatioByMoney": pExchangeMarginRate.ShortMarginRatioByMoney,
                "ShortMarginRatioByVolume": pExchangeMarginRate.ShortMarginRatioByVolume
            }
        response[Constant.ExchangeMarginRate] = result
        self.rsp_callback(response)

    def ReqQryInstrumentOrderCommRate(self, request: dict[str, Any]) -> int:
        req, requestId = CTPObjectHelper.extract_request(request, Constant.QryInstrumentOrderCommRate, tdapi.CThostFtdcQryInstrumentOrderCommRateField)
        ret = self._api.ReqQryInstrumentOrderCommRate(req, requestId)
        self.method_called(Constant.OnRspQryInstrumentOrderCommRate, ret)

    def OnRspQryInstrumentOrderCommRate(self, pInstrumentOrderCommRate: tdapi.CThostFtdcInstrumentOrderCommRateField, pRspInfo: tdapi.CThostFtdcRspInfoField, nRequestID: int, bIsLast: bool):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspQryInstrumentOrderCommRate, pRspInfo, nRequestID, bIsLast)
        result = {}
        if pInstrumentOrderCommRate:
            result = {
                "BrokerID": pInstrumentOrderCommRate.BrokerID,
                "ExchangeID": pInstrumentOrderCommRate.ExchangeID,
                "HedgeFlag": pInstrumentOrderCommRate.HedgeFlag,
                "InstrumentID": pInstrumentOrderCommRate.InstrumentID,
                "InvestUnitID": pInstrumentOrderCommRate.InvestUnitID,
                "InvestorID": pInstrumentOrderCommRate.InvestorID,
                "InvestorRange": pInstrumentOrderCommRate.InvestorRange,
                "OrderActionCommByTrade": pInstrumentOrderCommRate.OrderActionCommByTrade,
                "OrderActionCommByVolume": pInstrumentOrderCommRate.OrderActionCommByVolume,
                "OrderCommByTrade": pInstrumentOrderCommRate.OrderCommByTrade,
                "OrderCommByVolume": pInstrumentOrderCommRate.OrderCommByVolume
            }
        response[Constant.InstrumentOrderCommRate] = result
        self.rsp_callback(response)

    def ReqQryOptionInstrTradeCost(self, request: dict[str, Any]) -> int:
        req, requestId = CTPObjectHelper.extract_request(request, Constant.QryOptionInstrTradeCost, tdapi.CThostFtdcQryOptionInstrTradeCostField)
        ret = self._api.ReqQryOptionInstrTradeCost(req, requestId)
        self.method_called(Constant.OnRspQryOptionInstrTradeCost, ret)

    def OnRspQryOptionInstrTradeCost(self, pOptionInstrTradeCost: tdapi.CThostFtdcOptionInstrTradeCostField, pRspInfo: tdapi.CThostFtdcRspInfoField, nRequestID: int, bIsLast: bool):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspQryOptionInstrTradeCost, pRspInfo, nRequestID, bIsLast)
        result = {}
        if pOptionInstrTradeCost:
            result = {
                "BrokerID": pOptionInstrTradeCost.BrokerID,
                "ExchFixedMargin": pOptionInstrTradeCost.ExchFixedMargin,
                "ExchMiniMargin": pOptionInstrTradeCost.ExchMiniMargin,
                "ExchangeID": pOptionInstrTradeCost.ExchangeID,
                "FixedMargin": pOptionInstrTradeCost.FixedMargin,
                "HedgeFlag": pOptionInstrTradeCost.HedgeFlag,
                "InstrumentID": pOptionInstrTradeCost.InstrumentID,
                "InvestUnitID": pOptionInstrTradeCost.InvestUnitID,
                "InvestorID": pOptionInstrTradeCost.InvestorID,
                "MiniMargin": pOptionInstrTradeCost.MiniMargin,
                "Royalty": pOptionInstrTradeCost.Royalty
            }
        response[Constant.OptionInstrTradeCost] = result
        self.rsp_callback(response)

    def ReqQryOptionInstrCommRate(self, request: dict[str, Any]) -> int:
        req, requestId = CTPObjectHelper.extract_request(request, Constant.QryOptionInstrCommRate, tdapi.CThostFtdcQryOptionInstrCommRateField)
        ret = self._api.ReqQryOptionInstrCommRate(req, requestId)
        self.method_called(Constant.OnRspQryOptionInstrCommRate, ret)

    def OnRspQryOptionInstrCommRate(self, pOptionInstrCommRate: tdapi.CThostFtdcOptionInstrCommRateField, pRspInfo: tdapi.CThostFtdcRspInfoField, nRequestID: int, bIsLast: bool):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspQryOptionInstrCommRate, pRspInfo, nRequestID, bIsLast)
        result = {}
        if pOptionInstrCommRate:
            result = {
                "InvestorRange": pOptionInstrCommRate.InvestorRange,
                "BrokerID": pOptionInstrCommRate.BrokerID,
                "InvestorID": pOptionInstrCommRate.InvestorID,
                "OpenRatioByMoney": pOptionInstrCommRate.OpenRatioByMoney,
                "OpenRatioByVolume": pOptionInstrCommRate.OpenRatioByVolume,
                "CloseRatioByMoney": pOptionInstrCommRate.CloseRatioByMoney,
                "CloseRatioByVolume": pOptionInstrCommRate.CloseRatioByVolume,
                "CloseTodayRatioByMoney": pOptionInstrCommRate.CloseTodayRatioByMoney,
                "CloseTodayRatioByVolume": pOptionInstrCommRate.CloseTodayRatioByVolume,
                "StrikeRatioByMoney": pOptionInstrCommRate.StrikeRatioByMoney,
                "StrikeRatioByVolume": pOptionInstrCommRate.StrikeRatioByVolume,
                "ExchangeID": pOptionInstrCommRate.ExchangeID,
                "InvestUnitID": pOptionInstrCommRate.InvestUnitID,
                "InstrumentID": pOptionInstrCommRate.InstrumentID
            }
        response[Constant.OptionInstrCommRate] = result
        self.rsp_callback(response)

    # ReqUserPasswordUpdate
    def reqUserPasswordUpdate(self, request: dict[str, Any]) -> None:
        req, requestId = CTPObjectHelper.extract_request(request, Constant.UserPasswordUpdate, tdapi.CThostFtdcUserPasswordUpdateField)
        ret = self._api.ReqUserPasswordUpdate(req, requestId)
        self.method_called(Constant.OnRspUserPasswordUpdate, ret)

    def OnRspUserPasswordUpdate(self, pUserPasswordUpdate: tdapi.CThostFtdcUserPasswordUpdateField, pRspInfo: tdapi.CThostFtdcRspInfoField, nRequestID: int, bIsLast: bool):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspUserPasswordUpdate, pRspInfo, nRequestID, bIsLast)
        userPasswordUpdate = None
        if pUserPasswordUpdate:
            userPasswordUpdate = {
                "BrokerID": pUserPasswordUpdate.BrokerID,
                "UserID": pUserPasswordUpdate.UserID,
                "OldPassword": pUserPasswordUpdate.OldPassword,
                "NewPassword": pUserPasswordUpdate.NewPassword
            }
        response[Constant.UserPasswordUpdate] = userPasswordUpdate
        self.rsp_callback(response)

    def reqOrderInsert(self, request: dict[str, Any]) -> None:
        req, requestId = CTPObjectHelper.extract_request(request, Constant.InputOrder, tdapi.CThostFtdcInputOrderField)
        ret = self._api.ReqOrderInsert(req, requestId)
        self.method_called(Constant.OnRspOrderInsert, ret)

    def OnRspOrderInsert(self, pInputOrder: tdapi.CThostFtdcInputOrderField, pRspInfo: tdapi.CThostFtdcRspInfoField, nRequestID: int, bIsLast: bool):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspOrderInsert, pRspInfo, nRequestID, bIsLast)
        inputOrder = None
        if pInputOrder:
            inputOrder = {
                "BrokerID": pInputOrder.BrokerID,
                "InvestorID": pInputOrder.InvestorID,
                "OrderRef": pInputOrder.OrderRef,
                "UserID": pInputOrder.UserID,
                "OrderPriceType": pInputOrder.OrderPriceType,
                "Direction": pInputOrder.Direction,
                "CombOffsetFlag": pInputOrder.CombOffsetFlag,
                "CombHedgeFlag": pInputOrder.CombHedgeFlag,
                "LimitPrice": pInputOrder.LimitPrice,
                "VolumeTotalOriginal": pInputOrder.VolumeTotalOriginal,
                "TimeCondition": pInputOrder.TimeCondition,
                "GTDDate": pInputOrder.GTDDate,
                "VolumeCondition": pInputOrder.VolumeCondition,
                "MinVolume": pInputOrder.MinVolume,
                "ContingentCondition": pInputOrder.ContingentCondition,
                "StopPrice": pInputOrder.StopPrice,
                "ForceCloseReason": pInputOrder.ForceCloseReason,
                "IsAutoSuspend": pInputOrder.IsAutoSuspend,
                "BusinessUnit": pInputOrder.BusinessUnit,
                "RequestID": pInputOrder.RequestID,
                "UserForceClose": pInputOrder.UserForceClose,
                "IsSwapOrder": pInputOrder.IsSwapOrder,
                "ExchangeID": pInputOrder.ExchangeID,
                "InvestUnitID": pInputOrder.InvestUnitID,
                "AccountID": pInputOrder.AccountID,
                "CurrencyID": pInputOrder.CurrencyID,
                "ClientID": pInputOrder.ClientID,
                "MacAddress": pInputOrder.MacAddress,
                "InstrumentID": pInputOrder.InstrumentID,
                "IPAddress": pInputOrder.IPAddress
            }
        response[Constant.InputOrder] = inputOrder
        self.rsp_callback(response)

    def OnErrRtnOrderInsert(self, pInputOrder: tdapi.CThostFtdcInputOrderField, pRspInfo: tdapi.CThostFtdcRspInfoField):
        response = CTPObjectHelper.build_response_dict(Constant.OnErrRtnOrderInsert, pRspInfo)
        inputOrder = None
        if pInputOrder:
            inputOrder = {
                "BrokerID": pInputOrder.BrokerID,
                "InvestorID": pInputOrder.InvestorID,
                "OrderRef": pInputOrder.OrderRef,
                "UserID": pInputOrder.UserID,
                "OrderPriceType": pInputOrder.OrderPriceType,
                "Direction": pInputOrder.Direction,
                "CombOffsetFlag": pInputOrder.CombOffsetFlag,
                "CombHedgeFlag": pInputOrder.CombHedgeFlag,
                "LimitPrice": pInputOrder.LimitPrice,
                "VolumeTotalOriginal": pInputOrder.VolumeTotalOriginal,
                "TimeCondition": pInputOrder.TimeCondition,
                "GTDDate": pInputOrder.GTDDate,
                "VolumeCondition": pInputOrder.VolumeCondition,
                "MinVolume": pInputOrder.MinVolume,
                "ContingentCondition": pInputOrder.ContingentCondition,
                "StopPrice": pInputOrder.StopPrice,
                "ForceCloseReason": pInputOrder.ForceCloseReason,
                "IsAutoSuspend": pInputOrder.IsAutoSuspend,
                "BusinessUnit": pInputOrder.BusinessUnit,
                "RequestID": pInputOrder.RequestID,
                "UserForceClose": pInputOrder.UserForceClose,
                "IsSwapOrder": pInputOrder.IsSwapOrder,
                "ExchangeID": pInputOrder.ExchangeID,
                "InvestUnitID": pInputOrder.InvestUnitID,
                "AccountID": pInputOrder.AccountID,
                "CurrencyID": pInputOrder.CurrencyID,
                "ClientID": pInputOrder.ClientID,
                "MacAddress": pInputOrder.MacAddress,
                "InstrumentID": pInputOrder.InstrumentID,
                "IPAddress": pInputOrder.IPAddress
            }
        response[Constant.InputOrder] = inputOrder
        self.rsp_callback(response)

    def OnRtnOrder(self, pOrder: tdapi.CThostFtdcOrderField):
        response = CTPObjectHelper.build_response_dict(Constant.OnRtnOrder)
        order = None
        if pOrder:
            order = {
                "BrokerID": pOrder.BrokerID,
                "InvestorID": pOrder.InvestorID,
                "OrderRef": pOrder.OrderRef,
                "UserID": pOrder.UserID,
                "OrderPriceType": pOrder.OrderPriceType,
                "Direction": pOrder.Direction,
                "CombOffsetFlag": pOrder.CombOffsetFlag,
                "CombHedgeFlag": pOrder.CombHedgeFlag,
                "LimitPrice": pOrder.LimitPrice,
                "VolumeTotalOriginal": pOrder.VolumeTotalOriginal,
                "TimeCondition": pOrder.TimeCondition,
                "GTDDate": pOrder.GTDDate,
                "VolumeCondition": pOrder.VolumeCondition,
                "MinVolume": pOrder.MinVolume,
                "ContingentCondition": pOrder.ContingentCondition,
                "StopPrice": pOrder.StopPrice,
                "ForceCloseReason": pOrder.ForceCloseReason,
                "IsAutoSuspend": pOrder.IsAutoSuspend,
                "BusinessUnit": pOrder.BusinessUnit,
                "RequestID": pOrder.RequestID,
                "OrderLocalID": pOrder.OrderLocalID,
                "ExchangeID": pOrder.ExchangeID,
                "ParticipantID": pOrder.ParticipantID,
                "ClientID": pOrder.ClientID,
                "TraderID": pOrder.TraderID,
                "InstallID": pOrder.InstallID,
                "OrderSubmitStatus": pOrder.OrderSubmitStatus,
                "NotifySequence": pOrder.NotifySequence,
                "TradingDay": pOrder.TradingDay,
                "SettlementID": pOrder.SettlementID,
                "OrderSysID": pOrder.OrderSysID,
                "OrderSource": pOrder.OrderSource,
                "OrderStatus": pOrder.OrderStatus,
                "OrderType": pOrder.OrderType,
                "VolumeTraded": pOrder.VolumeTraded,
                "VolumeTotal": pOrder.VolumeTotal,
                "InsertDate": pOrder.InsertDate,
                "InsertTime": pOrder.InsertTime,
                "ActiveTime": pOrder.ActiveTime,
                "SuspendTime": pOrder.SuspendTime,
                "UpdateTime": pOrder.UpdateTime,
                "CancelTime": pOrder.CancelTime,
                "ActiveTraderID": pOrder.ActiveTraderID,
                "ClearingPartID": pOrder.ClearingPartID,
                "SequenceNo": pOrder.SequenceNo,
                "FrontID": pOrder.FrontID,
                "SessionID": pOrder.SessionID,
                "UserProductInfo": pOrder.UserProductInfo,
                "StatusMsg": pOrder.StatusMsg,
                "UserForceClose": pOrder.UserForceClose,
                "ActiveUserID": pOrder.ActiveUserID,
                "BrokerOrderSeq": pOrder.BrokerOrderSeq,
                "RelativeOrderSysID": pOrder.RelativeOrderSysID,
                "ZCETotalTradedVolume": pOrder.ZCETotalTradedVolume,
                "IsSwapOrder": pOrder.IsSwapOrder,
                "BranchID": pOrder.BranchID,
                "InvestUnitID": pOrder.InvestUnitID,
                "AccountID": pOrder.AccountID,
                "CurrencyID": pOrder.CurrencyID,
                "MacAddress": pOrder.MacAddress,
                "InstrumentID": pOrder.InstrumentID,
                "ExchangeInstID": pOrder.ExchangeInstID,
                "IPAddress": pOrder.IPAddress
            }
        response[Constant.Order] = order
        self.rsp_callback(response)

    def OnRtnTrade(self, pTrade: tdapi.CThostFtdcTradeField):
        response = CTPObjectHelper.build_response_dict(Constant.OnRtnTrade)
        trade = None
        if pTrade:
            trade = {
                "BrokerID": pTrade.BrokerID,
                "InvestorID": pTrade.InvestorID,
                "OrderRef": pTrade.OrderRef,
                "UserID": pTrade.UserID,
                "ExchangeID": pTrade.ExchangeID,
                "TradeID": pTrade.TradeID,
                "Direction": pTrade.Direction,
                "OrderSysID": pTrade.OrderSysID,
                "ParticipantID": pTrade.ParticipantID,
                "ClientID": pTrade.ClientID,
                "TradingRole": pTrade.TradingRole,
                "OffsetFlag": pTrade.OffsetFlag,
                "HedgeFlag": pTrade.HedgeFlag,
                "Price": pTrade.Price,
                "Volume": pTrade.Volume,
                "TradeDate": pTrade.TradeDate,
                "TradeTime": pTrade.TradeTime,
                "TradeType": pTrade.TradeType,
                "PriceSource": pTrade.PriceSource,
                "TraderID": pTrade.TraderID,
                "OrderLocalID": pTrade.OrderLocalID,
                "ClearingPartID": pTrade.ClearingPartID,
                "BusinessUnit": pTrade.BusinessUnit,
                "SequenceNo": pTrade.SequenceNo,
                "TradingDay": pTrade.TradingDay,
                "SettlementID": pTrade.SettlementID,
                "BrokerOrderSeq": pTrade.BrokerOrderSeq,
                "TradeSource": pTrade.TradeSource,
                "InvestUnitID": pTrade.InvestUnitID,
                "InstrumentID": pTrade.InstrumentID,
                "ExchangeInstID": pTrade.ExchangeInstID,
            }
        response[Constant.Trade] = trade
        self.rsp_callback(response)

    def reqOrderAction(self, request: dict[str, Any]) -> None:
        req, requestId = CTPObjectHelper.extract_request(request, Constant.InputOrderAction, tdapi.CThostFtdcInputOrderActionField)
        ret = self._api.ReqOrderAction(req, requestId)
        self.method_called(Constant.OnRspOrderAction, ret)

    def OnRspOrderAction(self, pInputOrderAction: tdapi.CThostFtdcInputOrderActionField, pRspInfo: tdapi.CThostFtdcRspInfoField, nRequestID: int, bIsLast: bool):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspOrderAction, pRspInfo, nRequestID, bIsLast)
        inputOrderAction = None
        if pInputOrderAction:
            inputOrderAction = {
                "BrokerID": pInputOrderAction.BrokerID,
                "InvestorID": pInputOrderAction.InvestorID,
                "OrderActionRef": pInputOrderAction.OrderActionRef,
                "OrderRef": pInputOrderAction.OrderRef,
                "RequestID": pInputOrderAction.RequestID,
                "FrontID": pInputOrderAction.FrontID,
                "SessionID": pInputOrderAction.SessionID,
                "ExchangeID": pInputOrderAction.ExchangeID,
                "OrderSysID": pInputOrderAction.OrderSysID,
                "ActionFlag": pInputOrderAction.ActionFlag,
                "LimitPrice": pInputOrderAction.LimitPrice,
                "VolumeChange": pInputOrderAction.VolumeChange,
                "UserID": pInputOrderAction.UserID,
                "InvestUnitID": pInputOrderAction.InvestUnitID,
                "MacAddress": pInputOrderAction.MacAddress,
                "InstrumentID": pInputOrderAction.InstrumentID,
                "IPAddress": pInputOrderAction.IPAddress
            }
        response[Constant.InputOrderAction] = inputOrderAction
        self.rsp_callback(response)

    def OnErrRtnOrderAction(self, pOrderAction: tdapi.CThostFtdcOrderActionField, pRspInfo: tdapi.CThostFtdcRspInfoField):
        response = CTPObjectHelper.build_response_dict(Constant.OnErrRtnOrderAction, pRspInfo)
        orderAction = None
        if pOrderAction:
            orderAction = {
                "BrokerID": pOrderAction.BrokerID,
                "InvestorID": pOrderAction.InvestorID,
                "OrderActionRef": pOrderAction.OrderActionRef,
                "OrderRef": pOrderAction.OrderRef,
                "RequestID": pOrderAction.RequestID,
                "FrontID": pOrderAction.FrontID,
                "SessionID": pOrderAction.SessionID,
                "ExchangeID": pOrderAction.ExchangeID,
                "OrderSysID": pOrderAction.OrderSysID,
                "ActionFlag": pOrderAction.ActionFlag,
                "LimitPrice": pOrderAction.LimitPrice,
                "VolumeChange": pOrderAction.VolumeChange,
                "ActionDate": pOrderAction.ActionDate,
                "ActionTime": pOrderAction.ActionTime,
                "TraderID": pOrderAction.TraderID,
                "InstallID": pOrderAction.InstallID,
                "OrderLocalID": pOrderAction.OrderLocalID,
                "ActionLocalID": pOrderAction.ActionLocalID,
                "ParticipantID": pOrderAction.ParticipantID,
                "ClientID": pOrderAction.ClientID,
                "BusinessUnit": pOrderAction.BusinessUnit,
                "OrderActionStatus": pOrderAction.OrderActionStatus,
                "UserID": pOrderAction.UserID,
                "StatusMsg": pOrderAction.StatusMsg,
                "BranchID": pOrderAction.BranchID,
                "InvestUnitID": pOrderAction.InvestUnitID,
                "MacAddress": pOrderAction.MacAddress,
                "InstrumentID": pOrderAction.InstrumentID,
                "IPAddress": pOrderAction.IPAddress
            }
        response[Constant.OrderAction] = orderAction
        self.rsp_callback(response)

    def reqQryMaxOrderVolume(self, request: dict[str, Any]) -> None:
        req, requestId = CTPObjectHelper.extract_request(request, Constant.QryMaxOrderVolume, tdapi.CThostFtdcQryMaxOrderVolumeField)
        ret = self._api.ReqQryMaxOrderVolume(req, requestId)
        self.method_called(Constant.OnRspQryMaxOrderVolume, ret)

    def OnRspQryMaxOrderVolume(self, pQryMaxOrderVolume: tdapi.CThostFtdcQryMaxOrderVolumeField, pRspInfo: tdapi.CThostFtdcRspInfoField, nRequestID: int, bIsLast: bool):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspQryMaxOrderVolume, pRspInfo, nRequestID, bIsLast)
        qryMaxOrderVolume = None
        if pQryMaxOrderVolume:
            qryMaxOrderVolume = {
                "BrokerID": pQryMaxOrderVolume.BrokerID,
                "InvestorID": pQryMaxOrderVolume.InvestorID,
                "InstrumentID": pQryMaxOrderVolume.InstrumentID,
                "ExchangeID": pQryMaxOrderVolume.ExchangeID,
                "InvestUnitID": pQryMaxOrderVolume.InvestUnitID,
                "MaxVolume": pQryMaxOrderVolume.MaxVolume,
                "Direction": pQryMaxOrderVolume.Direction,
                "OffsetFlag": pQryMaxOrderVolume.OffsetFlag,
                "HedgeFlag": pQryMaxOrderVolume.HedgeFlag
            }
        response[Constant.QryMaxOrderVolume] = qryMaxOrderVolume
        self.rsp_callback(response)

    def reqQryOrder(self, request: dict[str, Any]) -> None:
        req, requestId = CTPObjectHelper.extract_request(request, Constant.QryOrder, tdapi.CThostFtdcQryOrderField)
        ret = self._api.ReqQryOrder(req, requestId)
        self.method_called(Constant.OnRspQryOrder, ret)

    def OnRspQryOrder(self, pOrder: tdapi.CThostFtdcOrderField, pRspInfo: tdapi.CThostFtdcRspInfoField, nRequestID: int, bIsLast: bool):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspQryOrder, pRspInfo, nRequestID, bIsLast)
        order = None
        if pOrder:
            order = {
                "BrokerID": pOrder.BrokerID,
                "InvestorID": pOrder.InvestorID,
                "OrderRef": pOrder.OrderRef,
                "UserID": pOrder.UserID,
                "OrderPriceType": pOrder.OrderPriceType,
                "Direction": pOrder.Direction,
                "CombOffsetFlag": pOrder.CombOffsetFlag,
                "CombHedgeFlag": pOrder.CombHedgeFlag,
                "LimitPrice": pOrder.LimitPrice,
                "VolumeTotalOriginal": pOrder.VolumeTotalOriginal,
                "TimeCondition": pOrder.TimeCondition,
                "GTDDate": pOrder.GTDDate,
                "VolumeCondition": pOrder.VolumeCondition,
                "MinVolume": pOrder.MinVolume,
                "ContingentCondition": pOrder.ContingentCondition,
                "StopPrice": pOrder.StopPrice,
                "ForceCloseReason": pOrder.ForceCloseReason,
                "IsAutoSuspend": pOrder.IsAutoSuspend,
                "BusinessUnit": pOrder.BusinessUnit,
                "RequestID": pOrder.RequestID,
                "OrderLocalID": pOrder.OrderLocalID,
                "ExchangeID": pOrder.ExchangeID,
                "ParticipantID": pOrder.ParticipantID,
                "ClientID": pOrder.ClientID,
                "TraderID": pOrder.TraderID,
                "InstallID": pOrder.InstallID,
                "OrderSubmitStatus": pOrder.OrderSubmitStatus,
                "NotifySequence": pOrder.NotifySequence,
                "TradingDay": pOrder.TradingDay,
                "SettlementID": pOrder.SettlementID,
                "OrderSysID": pOrder.OrderSysID,
                "OrderSource": pOrder.OrderSource,
                "OrderStatus": pOrder.OrderStatus,
                "OrderType": pOrder.OrderType,
                "VolumeTraded": pOrder.VolumeTraded,
                "VolumeTotal": pOrder.VolumeTotal,
                "InsertDate": pOrder.InsertDate,
                "InsertTime": pOrder.InsertTime,
                "ActiveTime": pOrder.ActiveTime,
                "SuspendTime": pOrder.SuspendTime,
                "UpdateTime": pOrder.UpdateTime,
                "CancelTime": pOrder.CancelTime,
                "ActiveTraderID": pOrder.ActiveTraderID,
                "ClearingPartID": pOrder.ClearingPartID,
                "SequenceNo": pOrder.SequenceNo,
                "FrontID": pOrder.FrontID,
                "SessionID": pOrder.SessionID,
                "UserProductInfo": pOrder.UserProductInfo,
                "StatusMsg": pOrder.StatusMsg,
                "UserForceClose": pOrder.UserForceClose,
                "ActiveUserID": pOrder.ActiveUserID,
                "BrokerOrderSeq": pOrder.BrokerOrderSeq,
                "RelativeOrderSysID": pOrder.RelativeOrderSysID,
                "ZCETotalTradedVolume": pOrder.ZCETotalTradedVolume,
                "IsSwapOrder": pOrder.IsSwapOrder,
                "BranchID": pOrder.BranchID,
                "InvestUnitID": pOrder.InvestUnitID,
                "AccountID": pOrder.AccountID,
                "CurrencyID": pOrder.CurrencyID,
                "MacAddress": pOrder.MacAddress,
                "InstrumentID": pOrder.InstrumentID,
                "ExchangeInstID": pOrder.ExchangeInstID,
                "IPAddress": pOrder.IPAddress
            }
        response[Constant.Order] = order
        self.rsp_callback(response)


    def reqQryTrade(self, request: dict[str, Any]) -> None:
        req, requestId = CTPObjectHelper.extract_request(request, Constant.QryTrade, tdapi.CThostFtdcQryTradeField)
        ret = self._api.ReqQryTrade(req, requestId)
        self.method_called(Constant.OnRspQryTrade, ret)

    def OnRspQryTrade(self, pTrade: tdapi.CThostFtdcTradeField, pRspInfo: tdapi.CThostFtdcRspInfoField, nRequestID: int, bIsLast: bool):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspQryTrade, pRspInfo, nRequestID, bIsLast)
        qryTrade = None
        if pTrade:
            qryTrade = {
                "BrokerID": pTrade.BrokerID,
                "BrokerOrderSeq": pTrade.BrokerOrderSeq,
                "BusinessUnit": pTrade.BusinessUnit,
                "ClearingPartID": pTrade.ClearingPartID,
                "ClientID": pTrade.ClientID,
                "Direction": pTrade.Direction,
                "ExchangeID": pTrade.ExchangeID,
                "ExchangeInstID": pTrade.ExchangeInstID,
                "HedgeFlag": pTrade.HedgeFlag,
                "InstrumentID": pTrade.InstrumentID,
                "InvestUnitID": pTrade.InvestUnitID,
                "InvestorID": pTrade.InvestorID,
                "OffsetFlag": pTrade.OffsetFlag,
                "OrderLocalID": pTrade.OrderLocalID,
                "OrderRef": pTrade.OrderRef,
                "OrderSysID": pTrade.OrderSysID,
                "ParticipantID": pTrade.ParticipantID,
                "Price": pTrade.Price,
                "PriceSource": pTrade.PriceSource,
                "SequenceNo": pTrade.SequenceNo,
                "SettlementID": pTrade.SettlementID,
                "TradeDate": pTrade.TradeDate,
                "TradeID": pTrade.TradeID,
                "TradeSource": pTrade.TradeSource,
                "TradeTime": pTrade.TradeTime,
                "TradeType": pTrade.TradeType,
                "TraderID": pTrade.TraderID,
                "TradingDay": pTrade.TradingDay,
                "TradingRole": pTrade.TradingRole,
                "UserID": pTrade.UserID,
                "Volume": pTrade.Volume
                }
        response[Constant.Trade] = qryTrade
        self.rsp_callback(response)

    def reqQryInvestorPosition(self, request: dict[str, Any]) -> None:
        req, requestId = CTPObjectHelper.extract_request(request, Constant.QryInvestorPosition, tdapi.CThostFtdcQryInvestorPositionField)
        ret = self._api.ReqQryInvestorPosition(req, requestId)
        self.method_called(Constant.OnRspQryInvestorPosition, ret)

    def OnRspQryInvestorPosition(self, pInvestorPosition: tdapi.CThostFtdcInvestorPositionField, pRspInfo: tdapi.CThostFtdcRspInfoField, nRequestID: int, bIsLast: bool):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspQryInvestorPosition, pRspInfo, nRequestID, bIsLast)
        qryInvestorPosition = None
        if pInvestorPosition:
            qryInvestorPosition = {
                "AbandonFrozen": pInvestorPosition.AbandonFrozen,
                "BrokerID": pInvestorPosition.BrokerID,
                "CashIn": pInvestorPosition.CashIn,
                "CloseAmount": pInvestorPosition.CloseAmount,
                "CloseProfit": pInvestorPosition.CloseProfit,
                "CloseProfitByDate": pInvestorPosition.CloseProfitByDate,
                "CloseProfitByTrade": pInvestorPosition.CloseProfitByTrade,
                "CloseVolume": pInvestorPosition.CloseVolume,
                "CombLongFrozen": pInvestorPosition.CombLongFrozen,
                "CombPosition": pInvestorPosition.CombPosition,
                "CombShortFrozen": pInvestorPosition.CombShortFrozen,
                "Commission": pInvestorPosition.Commission,
                "ExchangeID": pInvestorPosition.ExchangeID,
                "ExchangeMargin": pInvestorPosition.ExchangeMargin,
                "FrozenCash": pInvestorPosition.FrozenCash,
                "FrozenCommission": pInvestorPosition.FrozenCommission,
                "FrozenMargin": pInvestorPosition.FrozenMargin,
                "HedgeFlag": pInvestorPosition.HedgeFlag,
                "InstrumentID": pInvestorPosition.InstrumentID,
                "InvestUnitID": pInvestorPosition.InvestUnitID,
                "InvestorID": pInvestorPosition.InvestorID,
                "LongFrozen": pInvestorPosition.LongFrozen,
                "LongFrozenAmount": pInvestorPosition.LongFrozenAmount,
                "MarginRateByMoney": pInvestorPosition.MarginRateByMoney,
                "MarginRateByVolume": pInvestorPosition.MarginRateByVolume,
                "OpenAmount": pInvestorPosition.OpenAmount,
                "OpenCost": pInvestorPosition.OpenCost,
                "OpenVolume": pInvestorPosition.OpenVolume,
                "PosiDirection": pInvestorPosition.PosiDirection,
                "Position": pInvestorPosition.Position,
                "PositionCost": pInvestorPosition.PositionCost,
                "PositionCostOffset": pInvestorPosition.PositionCostOffset,
                "PositionDate": pInvestorPosition.PositionDate,
                "PositionProfit": pInvestorPosition.PositionProfit,
                "PreMargin": pInvestorPosition.PreMargin,
                "PreSettlementPrice": pInvestorPosition.PreSettlementPrice,
                "SettlementID": pInvestorPosition.SettlementID,
                "SettlementPrice": pInvestorPosition.SettlementPrice,
                "ShortFrozen": pInvestorPosition.ShortFrozen,
                "ShortFrozenAmount": pInvestorPosition.ShortFrozenAmount,
                "StrikeFrozen": pInvestorPosition.StrikeFrozen,
                "StrikeFrozenAmount": pInvestorPosition.StrikeFrozenAmount,
                "TasPosition": pInvestorPosition.TasPosition,
                "TasPositionCost": pInvestorPosition.TasPositionCost,
                "TodayPosition": pInvestorPosition.TodayPosition,
                "TradingDay": pInvestorPosition.TradingDay,
                "UseMargin": pInvestorPosition.UseMargin,
                "YdPosition": pInvestorPosition.YdPosition,
                "YdStrikeFrozen": pInvestorPosition.YdStrikeFrozen
                }
        response[Constant.InvestorPosition] = qryInvestorPosition
        self.rsp_callback(response)

    def reqQryTradingAccount(self, request: dict[str, Any]) -> None:
        req, requestId = CTPObjectHelper.extract_request(request, Constant.QryTradingAccount, tdapi.CThostFtdcQryTradingAccountField)
        ret = self._api.ReqQryTradingAccount(req, requestId)
        self.method_called(Constant.OnRspQryTradingAccount, ret)

    def OnRspQryTradingAccount(self, pTradingAccount: tdapi.CThostFtdcTradingAccountField, pRspInfo: tdapi.CThostFtdcRspInfoField, nRequestID: int, bIsLast: bool):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspQryTradingAccount, pRspInfo, nRequestID, bIsLast)
        qryTradingAccount = None
        if pTradingAccount:
            qryTradingAccount = {
                "AccountID": pTradingAccount.AccountID,
                "Available": pTradingAccount.Available,
                "Balance": pTradingAccount.Balance,
                "BizType": pTradingAccount.BizType,
                "BrokerID": pTradingAccount.BrokerID,
                "CashIn": pTradingAccount.CashIn,
                "CloseProfit": pTradingAccount.CloseProfit,
                "Commission": pTradingAccount.Commission,
                "Credit": pTradingAccount.Credit,
                "CurrMargin": pTradingAccount.CurrMargin,
                "CurrencyID": pTradingAccount.CurrencyID,
                "DeliveryMargin": pTradingAccount.DeliveryMargin,
                "Deposit": pTradingAccount.Deposit,
                "ExchangeDeliveryMargin": pTradingAccount.ExchangeDeliveryMargin,
                "ExchangeMargin": pTradingAccount.ExchangeMargin,
                "FrozenCash": pTradingAccount.FrozenCash,
                "FrozenCommission": pTradingAccount.FrozenCommission,
                "FrozenMargin": pTradingAccount.FrozenMargin,
                "FrozenSwap": pTradingAccount.FrozenSwap,
                "FundMortgageAvailable": pTradingAccount.FundMortgageAvailable,
                "FundMortgageIn": pTradingAccount.FundMortgageIn,
                "FundMortgageOut": pTradingAccount.FundMortgageOut,
                "Interest": pTradingAccount.Interest,
                "InterestBase": pTradingAccount.InterestBase,
                "Mortgage": pTradingAccount.Mortgage,
                "MortgageableFund": pTradingAccount.MortgageableFund,
                "PositionProfit": pTradingAccount.PositionProfit,
                "PreBalance": pTradingAccount.PreBalance,
                "PreCredit": pTradingAccount.PreCredit,
                "PreDeposit": pTradingAccount.PreDeposit,
                "PreFundMortgageIn": pTradingAccount.PreFundMortgageIn,
                "PreFundMortgageOut": pTradingAccount.PreFundMortgageOut,
                "PreMargin": pTradingAccount.PreMargin,
                "PreMortgage": pTradingAccount.PreMortgage,
                "RemainSwap": pTradingAccount.RemainSwap,
                "Reserve": pTradingAccount.Reserve,
                "ReserveBalance": pTradingAccount.ReserveBalance,
                "SettlementID": pTradingAccount.SettlementID,
                "SpecProductCloseProfit": pTradingAccount.SpecProductCloseProfit,
                "SpecProductCommission": pTradingAccount.SpecProductCommission,
                "SpecProductExchangeMargin": pTradingAccount.SpecProductExchangeMargin,
                "SpecProductFrozenCommission": pTradingAccount.SpecProductFrozenCommission,
                "SpecProductFrozenMargin": pTradingAccount.SpecProductFrozenMargin,
                "SpecProductMargin": pTradingAccount.SpecProductMargin,
                "SpecProductPositionProfit": pTradingAccount.SpecProductPositionProfit,
                "SpecProductPositionProfitByAlg": pTradingAccount.SpecProductPositionProfitByAlg,
                "TradingDay": pTradingAccount.TradingDay,
                "Withdraw": pTradingAccount.Withdraw,
                "WithdrawQuota": pTradingAccount.WithdrawQuota
                }
        response[Constant.TradingAccount] = qryTradingAccount
        self.rsp_callback(response)

    def reqQryInvestor(self, request: dict[str, Any]) -> None:
        req, requestId = CTPObjectHelper.extract_request(request, Constant.QryInvestor, tdapi.CThostFtdcQryInvestorField)
        ret = self._api.ReqQryInvestor(req, requestId)
        self.method_called(Constant.OnRspQryInvestor, ret)

    def OnRspQryInvestor(self, pInvestor: tdapi.CThostFtdcInvestorField, pRspInfo: tdapi.CThostFtdcRspInfoField, nRequestID: int, bIsLast: bool):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspQryInvestor, pRspInfo, nRequestID, bIsLast)
        qryInvestor = None
        if pInvestor:
            qryInvestor = {
                "Address": pInvestor.Address,
                "BrokerID": pInvestor.BrokerID,
                "CommModelID": pInvestor.CommModelID,
                "IdentifiedCardNo": pInvestor.IdentifiedCardNo,
                "IdentifiedCardType": pInvestor.IdentifiedCardType,
                "InvestorGroupID": pInvestor.InvestorGroupID,
                "InvestorID": pInvestor.InvestorID,
                "InvestorName": pInvestor.InvestorName,
                "IsActive": pInvestor.IsActive,
                "MarginModelID": pInvestor.MarginModelID,
                "Mobile": pInvestor.Mobile,
                "OpenDate": pInvestor.OpenDate,
                "Telephone": pInvestor.Telephone
                }
        response[Constant.Investor] = qryInvestor
        self.rsp_callback(response)

    def reqQryTradingCode(self, request: dict[str, Any]) -> None:
        req, requestId = CTPObjectHelper.extract_request(request, Constant.QryTradingCode, tdapi.CThostFtdcQryTradingCodeField)
        ret = self._api.ReqQryTradingCode(req, requestId)
        self.method_called(Constant.OnRspQryTradingCode, ret)

    def OnRspQryTradingCode(self, pTradingCode: tdapi.CThostFtdcTradingCodeField, pRspInfo: tdapi.CThostFtdcRspInfoField, nRequestID: int, bIsLast: bool):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspQryTradingCode, pRspInfo, nRequestID, bIsLast)
        qryTradingCode = None
        if pTradingCode:
            qryTradingCode = {
                "BizType": pTradingCode.BizType,
                "BranchID": pTradingCode.BranchID,
                "BrokerID": pTradingCode.BrokerID,
                "ClientID": pTradingCode.ClientID,
                "ClientIDType": pTradingCode.ClientIDType,
                "ExchangeID": pTradingCode.ExchangeID,
                "InvestUnitID": pTradingCode.InvestUnitID,
                "InvestorID": pTradingCode.InvestorID,
                "IsActive": pTradingCode.IsActive
                }
        response[Constant.TradingCode] = qryTradingCode
        self.rsp_callback(response)

    def reqQryInstrumentMarginRate(self, request: dict[str, Any]) -> None:
        req, requestId = CTPObjectHelper.extract_request(request, Constant.QryInstrumentMarginRate, tdapi.CThostFtdcQryInstrumentMarginRateField)
        ret = self._api.ReqQryInstrumentMarginRate(req, requestId)
        self.method_called(Constant.OnRspQryInstrumentMarginRate, ret)

    def OnRspQryInstrumentMarginRate(self, pInstrumentMarginRate: tdapi.CThostFtdcInstrumentMarginRateField, pRspInfo: tdapi.CThostFtdcRspInfoField, nRequestID: int, bIsLast: bool):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspQryInstrumentMarginRate, pRspInfo, nRequestID, bIsLast)
        qryInstrumentMarginRate = None
        if pInstrumentMarginRate:
            qryInstrumentMarginRate = {
                "BrokerID": pInstrumentMarginRate.BrokerID,
                "ExchangeID": pInstrumentMarginRate.ExchangeID,
                "HedgeFlag": pInstrumentMarginRate.HedgeFlag,
                "InstrumentID": pInstrumentMarginRate.InstrumentID,
                "InvestUnitID": pInstrumentMarginRate.InvestUnitID,
                "InvestorID": pInstrumentMarginRate.InvestorID,
                "InvestorRange": pInstrumentMarginRate.InvestorRange,
                "IsRelative": pInstrumentMarginRate.IsRelative,
                "LongMarginRatioByMoney": pInstrumentMarginRate.LongMarginRatioByMoney,
                "LongMarginRatioByVolume": pInstrumentMarginRate.LongMarginRatioByVolume,
                "ShortMarginRatioByMoney": pInstrumentMarginRate.ShortMarginRatioByMoney,
                "ShortMarginRatioByVolume": pInstrumentMarginRate.ShortMarginRatioByVolume
                }
        response[Constant.InstrumentMarginRate] = qryInstrumentMarginRate
        self.rsp_callback(response)

    def reqQryInstrumentCommissionRate(self, request: dict[str, Any]) -> None:
        req, requestId = CTPObjectHelper.extract_request(request, Constant.QryInstrumentCommissionRate, tdapi.CThostFtdcQryInstrumentCommissionRateField)
        ret = self._api.ReqQryInstrumentCommissionRate(req, requestId)
        self.method_called(Constant.OnRspQryInstrumentCommissionRate, ret)

    def OnRspQryInstrumentCommissionRate(self, pInstrumentCommissionRate: tdapi.CThostFtdcInstrumentCommissionRateField , pRspInfo: tdapi.CThostFtdcRspInfoField, nRequestID: int, bIsLast: bool):
        response = CTPObjectHelper.build_response_dict(Constant.OnRspQryInstrumentCommissionRate, pRspInfo, nRequestID, bIsLast)
        qryInstrumentCommissionRate = None
        if pInstrumentCommissionRate:
            qryInstrumentCommissionRate = {
                "BizType": pInstrumentCommissionRate.BizType,
                "BrokerID": pInstrumentCommissionRate.BrokerID,
                "CloseRatioByMoney": pInstrumentCommissionRate.CloseRatioByMoney,
                "CloseRatioByVolume": pInstrumentCommissionRate.CloseRatioByVolume,
                "CloseTodayRatioByMoney": pInstrumentCommissionRate.CloseTodayRatioByMoney,
                "CloseTodayRatioByVolume": pInstrumentCommissionRate.CloseTodayRatioByVolume,
                "ExchangeID": pInstrumentCommissionRate.ExchangeID,
                "InstrumentID": pInstrumentCommissionRate.InstrumentID,
                "InvestUnitID": pInstrumentCommissionRate.InvestUnitID,
                "InvestorID": pInstrumentCommissionRate.InvestorID,
                "InvestorRange": pInstrumentCommissionRate.InvestorRange,
                "OpenRatioByMoney": pInstrumentCommissionRate.OpenRatioByMoney,
                "OpenRatioByVolume": pInstrumentCommissionRate.OpenRatioByVolume
                }
        response[Constant.InstrumentCommissionRate] = qryInstrumentCommissionRate
        self.rsp_callback(response)
