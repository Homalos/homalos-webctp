from typing import Any

import anyio

from ..clients import CTPMdClient
from ..constants import CallError
from ..constants import CommonConstant as Constant
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
        """
        处理客户端请求的异步方法

        Args:
            request: 请求字典，包含消息类型和相关数据

        Note:
            - 如果是登录请求(ReqUserLogin)，会启动客户端连接
            - 如果是其他已注册的消息类型，会调用对应的映射方法
            - 如果是未注册的消息类型，会返回对应的错误响应
        """
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
        """创建CTP行情客户端实例

        Args:
            user_id: 交易账号用户名
            password: 交易账号密码

        Returns:
            CTPMdClient: CTP行情客户端实例
        """
        return CTPMdClient(user_id, password)

    def _get_client_type(self) -> str:
        """
        获取客户端类型

        Returns:
            str: 返回客户端类型字符串，固定为"md"
        """
        return "md"

    def _init_call_map(self):
        """
        初始化调用映射表

        将客户端的订阅和取消订阅方法注册到调用映射表中，
        用于处理对应的消息类型请求
        """
        self._call_map["subscribe_marketdata"] = self._client.subscribe_marketdata
        self._call_map["unsubscribe_marketdata"] = self._client.unsubscribe_marketdata

