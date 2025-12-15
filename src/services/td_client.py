#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : td_client.py
@Date       : 2025/12/3 14:30
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: 交易服务 (继承 BaseClient)
"""
from typing import Any, Optional
import time
from queue import Queue

import anyio

from .base_client import BaseClient
from .cache_manager import CacheManager
from ..clients import CTPTdClient
from ..constants import CallError
from ..constants import TdConstant as Constant
from ..model import REQUEST_PAYLOAD
from ..utils.serialization import get_msgpack_serializer
from ..utils.metrics import MetricsCollector
from loguru import logger


class TdClient(BaseClient):
    """
    TdClient 是 websocket 和客户端之间的边界，也是异步代码和同步代码之间的边界。它负责控制 ctp 客户端的状态。
    """

    def __init__(self) -> None:
        super().__init__()
        self._client: CTPTdClient | None = None
        self._cache_manager: Optional[CacheManager] = None
        self._serializer = get_msgpack_serializer()
        self._user_id: Optional[str] = None
        self._metrics_collector: Optional[MetricsCollector] = None
        self._cache_queue: Queue = Queue()  # 缓存任务队列

    def set_cache_manager(self, cache_manager: CacheManager) -> None:
        """
        注入 CacheManager 实例

        Args:
            cache_manager: Redis 缓存管理器实例
        """
        self._cache_manager = cache_manager
        logger.info("TdClient: CacheManager 已注入")

    def set_metrics_collector(self, metrics_collector: MetricsCollector) -> None:
        """
        设置性能指标收集器实例

        Args:
            metrics_collector: MetricsCollector 实例，用于收集性能指标
        """
        self._metrics_collector = metrics_collector
        logger.info("TdClient: MetricsCollector 已注入")

    def on_rsp_or_rtn(self, data: dict[str, Any]) -> None:
        """
        处理来自CTP客户端的响应或返回数据，并同步写入缓存

        重写父类方法，在推送到队列前先尝试写入 Redis 缓存。
        如果缓存失败，不影响正常的消息推送流程（降级处理）。

        Args:
            data: 包含响应或返回数据的字典，格式为{字段名: 字段值}

        Returns:
            None: 该方法无返回值
        """
        # 记录 CTP 回调开始时间
        callback_start_time = time.time()
        
        # 异步缓存处理（不阻塞消息推送）
        message_type = data.get(Constant.MessageType, "")

        # 根据消息类型判断是否需要缓存，将任务放入队列
        if message_type in (
            Constant.OnRspQryInvestorPosition,
            Constant.OnRspQryTradingAccount,
            Constant.OnRtnOrder
        ):
            try:
                self._cache_queue.put_nowait((message_type, data))
            except Exception as e:
                logger.warning(f"TdClient: 缓存任务入队失败: {e}")

        # 调用父类方法，推送到队列
        super().on_rsp_or_rtn(data)
        
        # 记录 CTP 回调到队列的延迟
        if self._metrics_collector:
            callback_latency_ms = (time.time() - callback_start_time) * 1000
            self._metrics_collector.record_latency("td_callback_to_queue_latency", callback_latency_ms)

    async def _process_cache_queue(self) -> None:
        """
        处理缓存任务队列

        从队列中取出缓存任务并执行对应的缓存方法。
        此方法在异步上下文中运行，避免了跨线程异步调用问题。
        """
        from queue import Empty
        
        while self._running:
            try:
                # 非阻塞获取任务，避免阻塞事件循环
                message_type, data = self._cache_queue.get_nowait()
                
                # 根据消息类型执行对应的缓存方法
                if message_type == Constant.OnRspQryInvestorPosition:
                    await self._cache_position_data(data)
                elif message_type == Constant.OnRspQryTradingAccount:
                    await self._cache_account_data(data)
                elif message_type == Constant.OnRtnOrder:
                    await self._cache_order_data(data)
                    
            except Empty:
                # 队列为空，短暂休眠避免CPU占用过高
                await anyio.sleep(0.01)
            except Exception as e:
                logger.warning(f"TdClient: 处理缓存任务失败: {e}")

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
            if self.rsp_callback:
                await self.rsp_callback(ret)
        else:
            if message_type == Constant.ReqUserLogin:
                user_id: str = request[Constant.ReqUserLogin]["UserID"]
                password: str = request[Constant.ReqUserLogin]["Password"]
                # 保存用户ID用于缓存
                self._user_id = user_id
                await self.start(user_id, password)
            else:
                if message_type in self._call_map:
                    # 记录订单操作的开始时间（用于延迟统计）
                    start_time = None
                    if self._metrics_collector and message_type in [
                        Constant.ReqOrderInsert,
                        Constant.ReqOrderAction
                    ]:
                        start_time = time.time()
                    
                    # 执行 CTP API 调用
                    await anyio.to_thread.run_sync(
                        self._call_map[message_type], request)
                    
                    # 记录订单延迟指标
                    if start_time and self._metrics_collector:
                        latency_ms = (time.time() - start_time) * 1000
                        self._metrics_collector.record_latency("td_order_latency", latency_ms)
                        
                elif not self._call_map:
                    response = {
                        Constant.MessageType: message_type,
                        Constant.RspInfo: CallError.get_rsp_info(401)
                    }
                    if self.rsp_callback:
                        await self.rsp_callback(response)

                else:
                    response = {
                        Constant.MessageType: message_type,
                        Constant.RspInfo: CallError.get_rsp_info(404)
                    }
                    if self.rsp_callback:
                        await self.rsp_callback(response)
    async def run(self) -> None:
        """
        运行客户端协程的主循环

        重写父类方法，同时启动消息处理循环和缓存队列处理循环。

        Returns:
            None: 此方法不返回值
        """
        import logging
        
        logging.info(f"start to run new {self._get_client_type()} coroutine")
        self._stop_event = anyio.Event()
        self._running = True
        
        # 使用task_group同时运行消息处理和缓存处理
        async with anyio.create_task_group() as tg:
            # 启动缓存队列处理协程
            tg.start_soon(self._process_cache_queue)
            
            # 启动消息处理循环
            while self._running:
                await self._process_a_message(1.0)
            
            # task_group 会自动等待所有任务完成（优雅停止）
        
        logging.info(f"stop running {self._get_client_type()} coroutine")
        self._stop_event.set()

    async def stop(self) -> None:
        """
        停止客户端并清理缓存队列
        
        重写父类方法，在停止前：
        1. 给缓存队列处理一个短暂的时间窗口处理剩余任务
        2. 清空缓存队列避免内存泄漏
        """
        import logging
        
        logging.debug(f"stopping {self._get_client_type()} client")
        self._running = False
        
        # 给缓存队列一个短暂的时间窗口处理剩余任务（最多0.5秒）
        try:
            await anyio.sleep(0.5)
        except Exception:
            pass
        
        # 清空缓存队列
        cleared_count = 0
        try:
            while not self._cache_queue.empty():
                self._cache_queue.get_nowait()
                cleared_count += 1
        except Exception:
            pass
        
        if cleared_count > 0:
            logging.debug(f"TdClient: 清空了 {cleared_count} 个未处理的缓存任务")
        
        # 等待停止事件
        if self._stop_event:
            await self._stop_event.wait()
            self._stop_event = None
        
        # 释放客户端资源
        if self._client:
            await anyio.to_thread.run_sync(self._client.release)
        
        logging.debug(f"{self._get_client_type()} client stopped")

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

    async def _cache_position_data(self, data: dict) -> None:
        """
        缓存持仓数据到 Redis Hash

        Args:
            data: 持仓回报数据字典
        """
        if not self._cache_manager or not self._cache_manager.is_available():
            return

        if not self._user_id:
            logger.warning("TdClient: 用户ID未设置，跳过持仓缓存")
            return

        try:
            # 提取持仓数据
            position_data = data.get(Constant.InvestorPosition)
            if not position_data:
                return

            instrument_id = position_data.get("InstrumentID", "")
            if not instrument_id:
                return

            # 序列化持仓数据
            serialized_data = self._serializer.serialize(position_data)

            # 写入 Redis Hash
            # Key: account:position:{user_id}
            # Field: {instrument_id}
            cache_key = f"account:position:{self._user_id}"
            await self._cache_manager.hset(cache_key, instrument_id, serialized_data)

            logger.debug(f"TdClient: 持仓数据已缓存 - {instrument_id}")

        except Exception as e:
            logger.warning(f"TdClient: 缓存持仓数据失败: {e}")
            # 降级：不影响正常流程

    async def _cache_account_data(self, data: dict) -> None:
        """
        缓存资金数据到 Redis String

        Args:
            data: 资金回报数据字典
        """
        if not self._cache_manager or not self._cache_manager.is_available():
            return

        if not self._user_id:
            logger.warning("TdClient: 用户ID未设置，跳过资金缓存")
            return

        try:
            # 提取资金数据
            account_data = data.get(Constant.TradingAccount)
            if not account_data:
                return

            # 序列化资金数据
            serialized_data = self._serializer.serialize(account_data)

            # 写入 Redis String
            # Key: account:funds:{user_id}
            cache_key = f"account:funds:{self._user_id}"
            await self._cache_manager.set(cache_key, serialized_data)

            logger.debug(f"TdClient: 资金数据已缓存 - {self._user_id}")

        except Exception as e:
            logger.warning(f"TdClient: 缓存资金数据失败: {e}")
            # 降级：不影响正常流程

    async def _cache_order_data(self, data: dict) -> None:
        """
        缓存订单数据到 Redis Sorted Set

        Args:
            data: 订单回报数据字典
        """
        if not self._cache_manager or not self._cache_manager.is_available():
            return

        if not self._user_id:
            logger.warning("TdClient: 用户ID未设置，跳过订单缓存")
            return

        try:
            # 提取订单数据
            order_data = data.get(Constant.Order)
            if not order_data:
                return

            # 序列化订单数据
            serialized_data = self._serializer.serialize(order_data)

            # 生成唯一的订单标识（使用 OrderRef 或 OrderSysID）
            order_ref = order_data.get("OrderRef", "")
            order_sys_id = order_data.get("OrderSysID", "")
            order_key = order_sys_id if order_sys_id else order_ref

            if not order_key:
                logger.warning("TdClient: 订单数据缺少标识，跳过缓存")
                return

            # 写入 Redis Sorted Set
            # Key: account:orders:{user_id}
            # Score: 当前时间戳
            # Member: 序列化的订单数据（带订单标识前缀）
            cache_key = f"account:orders:{self._user_id}"
            score = time.time()
            member_key = f"{order_key}:{serialized_data.hex()}"

            # 使用 zadd 添加到 Sorted Set，并设置 24 小时 TTL
            from ..utils.config import GlobalConfig
            ttl = GlobalConfig.Cache.order_ttl if hasattr(GlobalConfig, 'Cache') else 86400

            await self._cache_manager.zadd(
                cache_key,
                {member_key: score},
                ttl=ttl
            )

            logger.debug(f"TdClient: 订单数据已缓存 - {order_key}")

        except Exception as e:
            logger.warning(f"TdClient: 缓存订单数据失败: {e}")
            # 降级：不影响正常流程

    async def query_position_cached(
        self, instrument_id: Optional[str] = None
    ) -> Optional[dict[str, Any]]:
        """
        从 Redis 缓存查询持仓数据

        Args:
            instrument_id: 合约代码，None 表示查询所有持仓

        Returns:
            Optional[dict[str, Any]]: 持仓数据字典
                - 如果指定 instrument_id，返回单个合约的持仓数据
                - 如果未指定 instrument_id，返回所有合约的持仓数据字典 {instrument_id: position_data}
                - Redis 不可用或未找到数据时返回 None
        """
        if not self._cache_manager or not self._cache_manager.is_available():
            logger.debug("TdClient: Redis 不可用，无法查询持仓缓存")
            return None

        if not self._user_id:
            logger.warning("TdClient: 用户ID未设置，无法查询持仓缓存")
            return None

        try:
            cache_key = f"account:position:{self._user_id}"

            if instrument_id:
                # 查询单个合约持仓
                data = await self._cache_manager.hget(cache_key, instrument_id)
                if data:
                    position_data = self._serializer.deserialize(data)
                    logger.debug(f"TdClient: 从缓存读取持仓数据 - {instrument_id}")
                    
                    # 记录缓存命中
                    if self._metrics_collector:
                        self._metrics_collector.record_counter("cache_hit_position")
                    
                    return position_data
                else:
                    logger.debug(f"TdClient: 缓存中未找到持仓数据 - {instrument_id}")
                    
                    # 记录缓存未命中
                    if self._metrics_collector:
                        self._metrics_collector.record_counter("cache_miss_position")
                    
                    return None
            else:
                # 查询所有持仓
                all_data = await self._cache_manager.hgetall(cache_key)
                if all_data:
                    result = {}
                    for inst_id_bytes, data_bytes in all_data.items():
                        inst_id = inst_id_bytes.decode('utf-8')
                        position_data = self._serializer.deserialize(data_bytes)
                        result[inst_id] = position_data
                    logger.debug(f"TdClient: 从缓存读取所有持仓数据，共 {len(result)} 个合约")
                    
                    # 记录缓存命中
                    if self._metrics_collector:
                        self._metrics_collector.record_counter("cache_hit_position")
                    
                    return result
                else:
                    logger.debug("TdClient: 缓存中未找到持仓数据")
                    
                    # 记录缓存未命中
                    if self._metrics_collector:
                        self._metrics_collector.record_counter("cache_miss_position")
                    
                    return None

        except Exception as e:
            logger.warning(f"TdClient: 查询持仓缓存失败: {e}")
            return None

    async def query_account_cached(self) -> Optional[dict[str, Any]]:
        """
        从 Redis 缓存查询资金账户数据

        Returns:
            Optional[dict[str, Any]]: 资金账户数据字典
                - Redis 不可用或未找到数据时返回 None
        """
        if not self._cache_manager or not self._cache_manager.is_available():
            logger.debug("TdClient: Redis 不可用，无法查询资金缓存")
            return None

        if not self._user_id:
            logger.warning("TdClient: 用户ID未设置，无法查询资金缓存")
            return None

        try:
            cache_key = f"account:funds:{self._user_id}"
            data = await self._cache_manager.get(cache_key)

            if data:
                account_data = self._serializer.deserialize(data)
                logger.debug(f"TdClient: 从缓存读取资金数据 - {self._user_id}")
                
                # 记录缓存命中
                if self._metrics_collector:
                    self._metrics_collector.record_counter("cache_hit_account")
                
                return account_data
            else:
                logger.debug("TdClient: 缓存中未找到资金数据")
                
                # 记录缓存未命中
                if self._metrics_collector:
                    self._metrics_collector.record_counter("cache_miss_account")
                
                return None

        except Exception as e:
            logger.warning(f"TdClient: 查询资金缓存失败: {e}")
            return None

    async def query_orders_cached(
        self, start: int = 0, end: int = -1
    ) -> list[dict[str, Any]]:
        """
        从 Redis 缓存查询订单数据

        Args:
            start: 起始索引（默认 0，表示最新的订单）
            end: 结束索引（默认 -1，表示所有订单）

        Returns:
            list[dict[str, Any]]: 订单数据列表，按时间倒序排列
                - Redis 不可用或未找到数据时返回空列表
        """
        if not self._cache_manager or not self._cache_manager.is_available():
            logger.debug("TdClient: Redis 不可用，无法查询订单缓存")
            return []

        if not self._user_id:
            logger.warning("TdClient: 用户ID未设置，无法查询订单缓存")
            return []

        try:
            cache_key = f"account:orders:{self._user_id}"

            # 从 Sorted Set 读取订单数据（倒序，最新的在前）
            members = await self._cache_manager.zrange(
                cache_key, start, end, withscores=False
            )

            if not members:
                logger.debug("TdClient: 缓存中未找到订单数据")
                
                # 记录缓存未命中
                if self._metrics_collector:
                    self._metrics_collector.record_counter("cache_miss_orders")
                
                return []

            # 解析订单数据
            orders = []
            for member in reversed(members):  # 倒序，最新的在前
                try:
                    # 解析 member 格式: {order_key}:{hex_data}
                    member_str = member.decode('utf-8') if isinstance(member, bytes) else member
                    parts = member_str.split(':', 1)
                    if len(parts) == 2:
                        order_key, hex_data = parts
                        # 将 hex 字符串转换回字节
                        serialized_data = bytes.fromhex(hex_data)
                        order_data = self._serializer.deserialize(serialized_data)
                        orders.append(order_data)
                except Exception as e:
                    logger.warning(f"TdClient: 解析订单数据失败: {e}")
                    continue

            logger.debug(f"TdClient: 从缓存读取订单数据，共 {len(orders)} 条")
            
            # 记录缓存命中
            if self._metrics_collector:
                self._metrics_collector.record_counter("cache_hit_orders")
            
            return orders

        except Exception as e:
            logger.warning(f"TdClient: 查询订单缓存失败: {e}")
            return []

    async def refresh_cache(self) -> dict[str, bool]:
        """
        手动刷新缓存

        清除当前用户的所有缓存数据，并触发 CTP API 查询以重新填充缓存。

        Returns:
            dict[str, bool]: 刷新结果状态字典
                {
                    "position_cleared": bool,  # 持仓缓存是否清除成功
                    "account_cleared": bool,   # 资金缓存是否清除成功
                    "orders_cleared": bool,    # 订单缓存是否清除成功
                }
        """
        result = {
            "position_cleared": False,
            "account_cleared": False,
            "orders_cleared": False,
        }

        if not self._cache_manager or not self._cache_manager.is_available():
            logger.warning("TdClient: Redis 不可用，无法刷新缓存")
            return result

        if not self._user_id:
            logger.warning("TdClient: 用户ID未设置，无法刷新缓存")
            return result

        try:
            # 清除持仓缓存
            position_key = f"account:position:{self._user_id}"
            result["position_cleared"] = await self._cache_manager.delete(position_key)

            # 清除资金缓存
            account_key = f"account:funds:{self._user_id}"
            result["account_cleared"] = await self._cache_manager.delete(account_key)

            # 清除订单缓存
            orders_key = f"account:orders:{self._user_id}"
            result["orders_cleared"] = await self._cache_manager.delete(orders_key)

            logger.info(
                f"TdClient: 缓存刷新完成 - "
                f"持仓: {result['position_cleared']}, "
                f"资金: {result['account_cleared']}, "
                f"订单: {result['orders_cleared']}"
            )

            # 注意：这里不主动触发 CTP API 查询
            # 缓存会在下次查询时自动填充（Cache-Aside 模式）
            # 或者在收到 CTP 回报时自动更新

        except Exception as e:
            logger.error(f"TdClient: 刷新缓存失败: {e}")

        return result

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
