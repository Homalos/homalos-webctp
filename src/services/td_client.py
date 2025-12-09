from typing import Any

import anyio

from .base_client import BaseClient
from ..clients import CTPTdClient
from ..constants import CallError
from ..constants import TdConstant as Constant
from ..model import REQUEST_PAYLOAD


class TdClient(BaseClient):
    """
    TdClient is the boundary of websocket and client,
    and the boundary of async code and sync code.
    It is responsible for controlling the status of
    ctp client.
    """

    def __init__(self) -> None:
        super().__init__()
        self._client: CTPTdClient | None = None

    def validate_request(self, message_type, data):
        """
        验证请求数据的有效性

        根据消息类型获取对应的数据类，并验证传入数据是否符合该类的结构定义。
        如果消息类型不存在或数据验证失败，返回相应的错误信息。

        Args:
            message_type: 请求消息类型，用于获取对应的数据模型类
            data: 请求数据字典，需要验证的数据内容

        Returns:
            dict: 验证结果字典，包含：
                - 如果验证成功：返回None（隐式返回）
                - 如果消息类型不存在：包含错误信息的字典
                - 如果数据验证失败：包含错误信息和详细描述字典
        """
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

    async def call(self, request: dict[str, Any]) -> None:
        """
        处理客户端请求的核心方法

        根据请求的消息类型进行相应的处理，包括参数验证、登录处理、方法调用等。
        支持异步处理不同类型的交易请求。

        Args:
            request: 包含请求信息的字典，必须包含MessageType字段

        Returns:
            None: 该方法通过回调函数返回响应结果
        """
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
        """创建CTP交易客户端实例

        Args:
            user_id (str): CTP交易账号用户名
            password (str): CTP交易账号密码

        Returns:
            CTPTdClient: CTP交易客户端实例对象
        """
        return CTPTdClient(user_id, password)

    def _get_client_type(self) -> str:
        """
        获取客户端类型标识符

        Returns:
            str: 客户端类型字符串，固定返回 "td" 表示交易客户端
        """
        return "td"

    def _init_call_map(self) -> None:
        """初始化API调用映射表

        将常量请求类型映射到对应的客户端API方法，用于统一处理各种CTP交易接口请求。
        此方法在对象初始化时被调用，建立请求类型与方法之间的对应关系。

        映射包含以下请求类型：
        - 查询合约信息(ReqQryInstrument)
        - 查询交易所信息(ReqQryExchange)
        - 查询产品信息(ReqQryProduct)
        - 查询深度行情(ReqQryDepthMarketData)
        - 查询投资者持仓详情(ReqQryInvestorPositionDetail)
        - 查询交易所保证金率(ReqQryExchangeMarginRate)
        - 查询合约手续费率(ReqQryInstrumentOrderCommRate)
        - 查询期权交易成本(ReqQryOptionInstrTradeCost)
        - 查询期权手续费率(ReqQryOptionInstrCommRate)
        - 查询报单(ReqQryOrder)
        - 查询最大报单量(ReqQryMaxOrderVolume)
        - 报单操作(ReqOrderAction)
        - 报单录入(ReqOrderInsert)
        - 用户密码更新(ReqUserPasswordUpdate)
        - 查询成交(ReqQryTrade)
        - 查询投资者持仓(ReqQryInvestorPosition)
        - 查询资金账户(ReqQryTradingAccount)
        - 查询投资者(ReqQryInvestor)
        - 查询交易编码(ReqQryTradingCode)
        - 查询合约保证金率(ReqQryInstrumentMarginRate)
        - 查询合约手续费率(ReqQryInstrumentCommissionRate)
        """
        self._call_map[Constant.ReqQryInstrument] = self._client.req_qry_instrument
        self._call_map[Constant.ReqQryExchange] = self._client.req_qry_exchange
        self._call_map[Constant.ReqQryProduct] = self._client.req_qry_product
        self._call_map[Constant.ReqQryDepthMarketData] = self._client.req_qry_depth_marketdata
        self._call_map[Constant.ReqQryInvestorPositionDetail] = self._client.req_qry_investor_position_detail
        self._call_map[Constant.ReqQryExchangeMarginRate] = self._client.req_qry_exchange_margin_rate
        self._call_map[Constant.ReqQryInstrumentOrderCommRate] = self._client.req_qry_instrument_order_comm_rate
        self._call_map[Constant.ReqQryOptionInstrTradeCost] = self._client.req_qry_option_instr_trade_cost
        self._call_map[Constant.ReqQryOptionInstrCommRate] = self._client.req_qry_option_instr_comm_rate
        self._call_map[Constant.ReqQryOrder] = self._client.req_qry_order
        self._call_map[Constant.ReqQryMaxOrderVolume] = self._client.req_qry_max_order_volume
        self._call_map[Constant.ReqOrderAction] = self._client.req_order_action
        self._call_map[Constant.ReqOrderInsert] = self._client.req_order_insert
        self._call_map[Constant.ReqUserPasswordUpdate] = self._client.req_user_password_update
        self._call_map[Constant.ReqQryTrade] = self._client.req_qry_trade
        self._call_map[Constant.ReqQryInvestorPosition] = self._client.req_qry_investor_position
        self._call_map[Constant.ReqQryTradingAccount] = self._client.req_qry_trading_account
        self._call_map[Constant.ReqQryInvestor] = self._client.req_qry_investor
        self._call_map[Constant.ReqQryTradingCode] = self._client.req_qry_trading_code
        self._call_map[Constant.ReqQryInstrumentMarginRate] = self._client.req_qry_instrument_margin_rate
        self._call_map[Constant.ReqQryInstrumentCommissionRate] = self._client.req_qry_instrument_commission_rate