#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : td_app.py
@Date       : 2025/12/3 13:1020
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: td_app
"""
from fastapi import FastAPI, WebSocket

from ..services.connection import TdConnection


app = FastAPI()

@app.websocket("/")
async def td_websocket(websocket: WebSocket):
    """
    处理交易端WebSocket连接

    建立与客户端的WebSocket连接并启动交易服务

    Args:
        websocket: WebSocket连接对象

    Returns:
        None: 该函数会持续运行直到连接断开
    """
    connection = TdConnection(websocket)
    await connection.run()
