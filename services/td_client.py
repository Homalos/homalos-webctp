import logging
from typing import Any

import anyio
from constants import CallError
from constants import TdConstant as Constant
from clients import CTPTdClient
from model import REQUEST_PAYLOAD
from .base_client import BaseClient


class TdClient(BaseClient):
    """
    TdClient is the boundary of websocket and client,
    and the boundary of async code and sync code.
    It is responsible for controlling the status of
    ctp client.
    """

    def __init__(self) -> None:
        super().__init__()
        self._client: CTPTdClient = None

    def validate_request(self, message_type, data):
        class_ = REQUEST_PAYLOAD.get(message_type)
        if class_ is None:
            return {
                Constant.MessageType: message_type,
                Constant.RspInfo: CallError.get_rsp_info(404)
            }

        try:
            class_(**data)
        except Exception as err:
            return {
                Constant.MessageType: message_type,
                Constant.RspInfo: CallError.get_rsp_info(400),
                "Detail": str(err),
            }

    async def call(self, request: dict[str, Any]) -> dict[str, Any]:
        message_type = request[Constant.MessageType]
        ret = self.validate_request(message_type, request)
        if ret is not None:
            await self.rsp_callback(ret)
        else:
            if message_type == Constant.ReqUserLogin:
                user_id: str = request[Constant.ReqUserLogin]["UserID"]
                password: str = request[Constant.ReqUserLogin]["Password"]
                await self.start(user_id, password)
            else:
                if message_type in self._call_map:
                    await anyio.to_thread.run_sync(
                        self._call_map[message_type], request)
                elif not self._call_map:
                    response = {
                        Constant.MessageType: message_type,
                        Constant.RspInfo: CallError.get_rsp_info(401)
                    }
                    await self.rsp_callback(response)

                else:
                    response = {
                        Constant.MessageType: message_type,
                        Constant.RspInfo: CallError.get_rsp_info(404)
                    }
                    await self.rsp_callback(response)

    def _create_ctp_client(self, user_id: str, password: str):
        """Create the TdClient CTP instance"""
        return CTPTdClient(user_id, password)
    
    def _get_client_type(self) -> str:
        """Return client type for logging"""
        return "td"

    def _init_call_map(self):
        self._call_map[Constant.ReqQryInstrument] = self._client.reqQryInstrument
        self._call_map[Constant.ReqQryExchange] = self._client.ReqQryExchange
        self._call_map[Constant.ReqQryProduct] = self._client.ReqQryProduct
        self._call_map[Constant.ReqQryDepthMarketData] = self._client.ReqQryDepthMarketData
        self._call_map[Constant.ReqQryInvestorPositionDetail] = self._client.ReqQryInvestorPositionDetail
        self._call_map[Constant.ReqQryExchangeMarginRate] = self._client.ReqQryExchangeMarginRate
        self._call_map[Constant.ReqQryInstrumentOrderCommRate] = self._client.ReqQryInstrumentOrderCommRate
        self._call_map[Constant.ReqQryOptionInstrTradeCost] = self._client.ReqQryOptionInstrTradeCost
        self._call_map[Constant.ReqQryOptionInstrCommRate] = self._client.ReqQryOptionInstrCommRate
        self._call_map[Constant.ReqQryOrder] = self._client.reqQryOrder
        self._call_map[Constant.ReqQryMaxOrderVolume] = self._client.reqQryMaxOrderVolume
        self._call_map[Constant.ReqOrderAction] = self._client.reqOrderAction
        self._call_map[Constant.ReqOrderInsert] = self._client.reqOrderInsert
        self._call_map[Constant.ReqUserPasswordUpdate] = self._client.reqUserPasswordUpdate
        self._call_map[Constant.ReqQryTrade] = self._client.reqQryTrade
        self._call_map[Constant.ReqQryInvestorPosition] = self._client.reqQryInvestorPosition
        self._call_map[Constant.ReqQryTradingAccount] = self._client.reqQryTradingAccount
        self._call_map[Constant.ReqQryInvestor] = self._client.reqQryInvestor
        self._call_map[Constant.ReqQryTradingCode] = self._client.reqQryTradingCode
        self._call_map[Constant.ReqQryInstrumentMarginRate] = self._client.reqQryInstrumentMarginRate
        self._call_map[Constant.ReqQryInstrumentCommissionRate] = self._client.reqQryInstrumentCommissionRate