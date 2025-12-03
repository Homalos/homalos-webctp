import logging
import time
import uuid
from typing import Callable, Any

from ..ctp import thostmduserapi as mdapi

from ..constants import CallError
from ..constants import MdConstant as Constant
from ..utils import CTPObjectHelper, GlobalConfig, MathHelper


class MdClient(mdapi.CThostFtdcMdSpi):

    def __init__(self, user_id, password):
        super().__init__()
        self._front_address: str = GlobalConfig.MdFrontAddress
        logging.debug(f"Md front_address: {self._front_address}")
        self._broker_id: str = GlobalConfig.BrokerID
        self._user_id: str = user_id or str(uuid.uuid4())
        self._password: str = password
        self._rsp_callback: Callable[[dict[str, Any]], None] | None = None
        self._api: mdapi.CThostFtdcMdApi | None = None
        self._connected: bool = False
        # Reconnection control to prevent infinite reconnection loops
        self._reconnect_count: int = 0
        self._max_reconnect_attempts: int = 5
        self._last_connect_time: float = 0
        self._reconnect_interval: float = 5.0  # seconds
    
    @property
    def rsp_callback(self) -> Callable[[dict[str, Any]], None]:
        return self._rsp_callback

    @rsp_callback.setter
    def rsp_callback(self, callback: Callable[[dict[str, Any]], None]):
        self._rsp_callback = callback
    
    def method_called(self, msg_type: str, ret: int):
        if ret != 0:
            response = CTPObjectHelper.build_response_dict(msg_type)
            response[Constant.RspInfo] = CallError.get_rsp_info(ret)
            self.rsp_callback(response)
    
    def release(self) -> None:
        logging.debug(f"release md client: {self._user_id}")
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
        con_file_path = GlobalConfig.get_con_file_path("md" + self._user_id)
        self._api: mdapi.CThostFtdcMdApi = mdapi.CThostFtdcMdApi.CreateFtdcMdApi(con_file_path)
        self._api.RegisterSpi(self)
        self._api.RegisterFront(self._front_address)
        return self._api
    
    def OnFrontConnected(self):
        logging.info("Md client connected")
        # Reconnection control: prevent infinite reconnection loops due to configuration errors
        current_time = time.time()
        if current_time - self._last_connect_time < self._reconnect_interval:
            self._reconnect_count += 1
            if self._reconnect_count > self._max_reconnect_attempts:
                logging.error(
                    f"Exceeded maximum reconnection attempts ({self._max_reconnect_attempts}). "
                    "Please check your configuration (broker, front address, etc.)"
                )
                return
            logging.warning(f"Reconnection attempt {self._reconnect_count}/{self._max_reconnect_attempts}")
        else:
            # Reset counter if enough time has passed
            self._reconnect_count = 0
        
        self._last_connect_time = current_time
        self.login()
    
    def OnFrontDisconnected(self, reason):
        logging.warning(f"Md client disconnected, error_code={reason}")
    
    def login(self):
        logging.info(f"start to login for {self._user_id}")
        req = mdapi.CThostFtdcReqUserLoginField()
        req.BrokerID = ""
        req.UserID = "" 
        req.Password = ""
        return self._api.ReqUserLogin(req, 0)
    
    def OnRspUserLogin(
            self,
            rsp_user_login: mdapi.CThostFtdcRspUserLoginField,
            rsp_info: mdapi.CThostFtdcRspInfoField,
            request_id,
            is_last
    ):
        if rsp_info is None or rsp_info.ErrorID == 0:
            logging.info("Md client login success")
        else:
            logging.info("Md client login failed, please try again")
        
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
        response = CTPObjectHelper.build_response_dict(Constant.OnRspSubMarketData, rsp_info, request_id, is_last)
        if specific_instrument:
            response[Constant.SpecificInstrument] = {
                Constant.InstrumentID: specific_instrument.InstrumentID
            }
        self.rsp_callback(response)
    
    def OnRtnDepthMarketData(self, depth_marketdata: mdapi.CThostFtdcDepthMarketDataField):
        logging.debug(f"receive depth market data: {depth_marketdata.InstrumentID}")
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

    # OnRspUnSubMarketData from CThostFtdcMdSpi
    def OnRspUnSubMarketData(
            self,
            specific_instrument: mdapi.CThostFtdcSpecificInstrumentField,
            rsp_info,
            request_id,
            is_last
    ):
        logging.debug(f"recv unsub market data")
        response = CTPObjectHelper.build_response_dict(Constant.OnRspUnSubMarketData, rsp_info, request_id, is_last)
        if specific_instrument:
            response[Constant.SpecificInstrument] = {
                Constant.InstrumentID: specific_instrument.InstrumentID
            }
        self.rsp_callback(response)

    def subscribe_marketdata(self, request: dict[str, Any]) -> None:
        instrument_ids = request[Constant.InstrumentID]
        instrument_ids = list(map(lambda i: i.encode(), instrument_ids))
        logging.debug(f"subscribe data for {instrument_ids}")
        ret = self._api.SubscribeMarketData(instrument_ids, len(instrument_ids))
        self.method_called(Constant.OnRspSubMarketData, ret)

    # unsubscribe market data
    def unsubscribe_marketdata(self, request: dict[str, Any]) -> None:
        instrument_ids = request[Constant.InstrumentID]
        instrument_ids = list(map(lambda i: i.encode(), instrument_ids))
        logging.debug(f"unsubscribe data for {instrument_ids}")
        ret = self._api.UnSubscribeMarketData(instrument_ids, len(instrument_ids))
        self.method_called(Constant.OnRspUnSubMarketData, ret)
