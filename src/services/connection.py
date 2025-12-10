#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : connection.py
@Date       : 2025/12/3 14:18
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: WebSocket 连接管理
"""
import abc
import anyio
import json
import logging
from typing import Any
from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from ..constants.call_errors import CallError
from ..constants.constant import CommonConstant as Constant
from ..utils.config import GlobalConfig
from .heartbeat import HeartbeatManager
from .td_client import TdClient
from .md_client import MdClient


class BaseConnection(abc.ABC):

    def __init__(self, websocket: WebSocket) -> None:
        """
        初始化基础连接对象

        Args:
            websocket: WebSocket连接对象，用于与客户端进行双向通信
        """
        self._ws: WebSocket = websocket
        self._client: TdClient | MdClient | None = None
        self._heartbeat: HeartbeatManager | None = None

    async def connect(self):
        """
        建立WebSocket连接并初始化客户端

        该方法执行两个主要操作：
        1. 接受WebSocket连接请求
        2. 创建并初始化对应的客户端实例（交易客户端或行情客户端）

        Raises:
            WebSocketDisconnect: 当WebSocket连接过程中发生异常时抛出
        """
        await self._ws.accept()
        self._client = self.create_client()

    async def disconnect(self) -> None:
        """断开与客户端的连接

        此方法用于异步关闭与客户端的连接，停止所有正在进行的通信。

        Returns:
            None: 此方法不返回任何值
        """
        if self._heartbeat:
            await self._heartbeat.stop()
        await self._client.stop()

    async def send(self, data: dict[str, Any]) -> None:
        """
        向WebSocket连接发送JSON数据

        Args:
            data: 要发送的字典数据，将被序列化为JSON格式

        Note:
            仅在WebSocket连接状态为CONNECTED时才会实际发送数据
        """
        if self._ws.client_state == WebSocketState.CONNECTED:
            await self._ws.send_json(data)

    async def recv(self) -> dict[str, Any]:
        """
        从WebSocket连接接收JSON数据

        Returns:
            包含接收到的JSON数据的字典

        Raises:
            WebSocketDisconnect: 当WebSocket连接断开时抛出
            JSONDecodeError: 当接收到的数据不是有效的JSON时抛出
        """
        return await self._ws.receive_json()

    async def run(self):
        """
        运行WebSocket连接的主循环

        此方法负责：
        1. 建立WebSocket连接
        2. 创建任务组用于并发处理
        3. 持续接收消息并转发给客户端处理
        4. 处理JSON解码异常
        5. 在连接断开时进行清理

        Raises:
            WebSocketDisconnect: 当WebSocket连接断开时
        """
        await self.connect()
        
        # 启动心跳
        self._heartbeat = HeartbeatManager(
            interval=GlobalConfig.HeartbeatInterval,
            timeout=GlobalConfig.HeartbeatTimeout
        )
        await self._heartbeat.start(
            send_callback=self.send,
            disconnect_callback=self.disconnect
        )

        async with anyio.create_task_group() as task_group:
            self._client.task_group = task_group
            try:
                while True:
                    try:
                        data = await self.recv()
                        
                        # 处理 Pong 消息
                        if data.get(Constant.MessageType) == Constant.Pong:
                            self._heartbeat.on_pong_received()
                            continue
                        
                        await self._client.call(data)
                    except json.decoder.JSONDecodeError as err:
                        await self.send({
                            Constant.MessageType: "",
                            Constant.RspInfo: CallError.get_rsp_info(400),
                            "Detail": str(err),
                        })
            except WebSocketDisconnect:
                logging.debug("websocket disconnect")
                await self.disconnect()

    @abc.abstractmethod
    def create_client(self):
        """
        创建并初始化对应的客户端实例

        抽象方法，由具体子类实现以创建特定类型的客户端
        （交易客户端TdClient或行情客户端MdClient）

        Returns:
            TdClient | MdClient: 初始化完成的客户端实例，具体类型取决于子类实现
        """
        pass


class TdConnection(BaseConnection):
    def __init__(self, websocket: WebSocket) -> None:
        super().__init__(websocket)

    def create_client(self):
        """
        创建并配置一个交易客户端实例

        Returns:
            TdClient: 配置好的交易客户端实例，已设置响应回调函数
        """
        client = TdClient()
        client.rsp_callback = self.send
        return client


class MdConnection(BaseConnection):
    def __init__(self, websocket: WebSocket) -> None:
        super().__init__(websocket)

    def create_client(self):
        """
        创建行情客户端实例并配置回调函数

        该方法实例化MdClient对象，并设置其响应回调为当前连接的send方法，
        用于将CTP行情服务器的响应通过WebSocket发送给客户端

        Returns:
            MdClient: 配置好的行情客户端实例，已设置响应回调
        """
        client = MdClient()
        client.rsp_callback = self.send
        return client
