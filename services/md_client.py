import logging
from typing import Any

import anyio
from constants import CallError
from constants import CommonConstant as Constant
from clients import CTPMdClient
from .base_client import BaseClient


class MdClient(BaseClient):
    """
    MdClient is the boundary of websocket and client,
    and the boundary of async code and sync code.
    It is responsible for controlling the status of
    ctp client.
    """

    def __init__(self) -> None:
        super().__init__()
        self._client: CTPMdClient = None

    async def call(self, request: dict[str, Any]) -> None:
        message_type = request[Constant.MessageType]
        if message_type == Constant.ReqUserLogin:
            user_id: str = request[Constant.ReqUserLogin]["UserID"]
            password: str = request[Constant.ReqUserLogin]["Password"]
            await self.start(user_id, password)
        else:
            if message_type in self._call_map:
                await anyio.to_thread.run_sync(self._call_map[message_type], request)
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
        """Create the MdClient CTP instance"""
        return CTPMdClient(user_id, password)
    
    def _get_client_type(self) -> str:
        """Return client type for logging"""
        return "md"

    def _init_call_map(self):
        self._call_map["SubscribeMarketData"] = self._client.subscribeMarketData
        self._call_map["UnSubscribeMarketData"] = self._client.unSubscribeMarketData

