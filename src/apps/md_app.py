from fastapi import FastAPI, WebSocket
from ..services.connection import MdConnection


app = FastAPI()

@app.websocket("/")
async def md_websocket(websocket: WebSocket):
    """
    WebSocket端点，用于处理CTP行情数据连接

    Args:
        websocket: FastAPI WebSocket连接对象

    Returns:
        None: 无返回值，通过WebSocket持续发送和接收数据
    """
    connection = MdConnection(websocket)
    await connection.run()
