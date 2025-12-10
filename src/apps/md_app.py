#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : md_app.py
@Date       : 2025/12/3 13:20
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: 行情服务 FastAPI 应用
"""
from fastapi import FastAPI, WebSocket
from ..services.connection import MdConnection
from ..utils import GlobalConfig



app = FastAPI()

@app.websocket("/")
async def md_websocket(websocket: WebSocket, token: str | None = None):

    """
    WebSocket端点，用于处理CTP行情数据连接

    Args:
        websocket: FastAPI WebSocket连接对象

    Returns:
        None: 无返回值，通过WebSocket持续发送和接收数据
    """


    if GlobalConfig.Token and token != GlobalConfig.Token:
        await websocket.close(code=1008)
        return

    connection = MdConnection(websocket)

    await connection.run()
