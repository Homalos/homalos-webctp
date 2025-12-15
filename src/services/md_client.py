#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : md_client.py
@Date       : 2025/12/3 14:20
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: 行情服务 (继承 BaseClient)
"""
from typing import Any, Optional, Dict
import asyncio

import anyio
from loguru import logger

from ..clients import CTPMdClient
from ..constants import CallError
from ..constants import CommonConstant as Constant
from ..constants import MdConstant
from .base_client import BaseClient
from .cache_manager import CacheManager
from ..utils.serialization import get_msgpack_serializer, SerializationError
from ..utils.config import GlobalConfig
from ..utils.metrics import MetricsCollector


class MdClient(BaseClient):
    """
    MdClient 是 websocket 和客户端之间的边界，也是异步代码和同步代码之间的边界。它负责控制 ctp 客户端的状态。
    """

    def __init__(self) -> None:
        super().__init__()
        self._client: CTPMdClient | None = None
        self._cache_manager: Optional[CacheManager] = None
        self._metrics_collector: Optional[MetricsCollector] = None
        self._serializer = get_msgpack_serializer()

    def set_cache_manager(self, cache_manager: CacheManager) -> None:
        """
        设置缓存管理器实例

        Args:
            cache_manager: CacheManager 实例，用于 Redis 缓存操作
        """
        self._cache_manager = cache_manager
        logger.info("MdClient 已注入 CacheManager")

    def set_metrics_collector(self, metrics_collector: MetricsCollector) -> None:
        """
        设置性能指标收集器实例

        Args:
            metrics_collector: MetricsCollector 实例，用于收集性能指标
        """
        self._metrics_collector = metrics_collector
        logger.info("MdClient 已注入 MetricsCollector")

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
                if self.rsp_callback:
                    await self.rsp_callback(response)
            else:
                response = {
                    Constant.MessageType: message_type,
                    Constant.RspInfo: CallError.get_rsp_info(404)
                }
                if self.rsp_callback:
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
        self._call_map[MdConstant.SubscribeMarketData] = self._client.subscribe_marketdata
        self._call_map[MdConstant.UnSubscribeMarketData] = self._client.unsubscribe_marketdata

    def on_rsp_or_rtn(self, data: dict[str, Any]) -> None:
        """
        处理来自CTP客户端的响应或返回数据（重写以支持 Redis 缓存）

        对于行情数据，会：
        1. 发布到 Redis Pub/Sub 频道（用于策略订阅）
        2. 更新行情快照缓存（Hash 结构）
        3. 设置适当的 TTL
        4. 如果 Redis 不可用，降级到直接推送

        Args:
            data: 包含响应或返回数据的字典，格式为{字段名: 字段值}

        Returns:
            None: 该方法无返回值
        """
        # 检查是否为行情数据推送
        message_type = data.get(Constant.MessageType)
        
        if message_type == MdConstant.OnRtnDepthMarketData and self._cache_manager:
            # 尝试进行 Redis 缓存操作
            try:
                if self._cache_manager.is_available():
                    # 提取行情数据
                    market_data = data.get(MdConstant.DepthMarketData)
                    if market_data:
                        instrument_id = market_data.get("InstrumentID")
                        if instrument_id:
                            # 异步执行 Redis 操作（不阻塞主流程）
                            asyncio.create_task(
                                self._cache_market_data(instrument_id, market_data)
                            )
            except Exception as e:
                # Redis 操作失败不影响核心推送功能
                logger.warning(f"Redis 缓存操作失败，降级到直接推送: {e}")

        # 保持原有逻辑：将数据放入队列
        self._queue.put_nowait(data)

    async def _cache_market_data(
        self, instrument_id: str, market_data: dict[str, Any]
    ) -> None:
        """
        缓存行情数据到 Redis

        Args:
            instrument_id: 合约代码
            market_data: 行情数据字典

        Returns:
            None
        """
        try:
            # 序列化行情数据
            serialized_data = self._serializer.serialize(market_data)

            # 1. 发布到 Pub/Sub 频道（用于实时推送）
            channel = f"market:tick:{instrument_id}"
            await self._cache_manager.publish(channel, serialized_data)
            logger.debug(f"已发布行情到 Redis Pub/Sub: {channel}")

            # 2. 更新行情快照缓存（Hash 结构）
            snapshot_key = f"market:snapshot:{instrument_id}"
            await self._cache_manager.hset(
                snapshot_key, "data", serialized_data
            )
            
            # 设置快照 TTL（从配置读取，默认 60 秒）
            snapshot_ttl = 60  # 默认值
            if hasattr(GlobalConfig, 'Cache') and GlobalConfig.Cache:
                snapshot_ttl = GlobalConfig.Cache.market_snapshot_ttl
            # 注意：Redis Hash 的 TTL 是针对整个 Hash 的，不是单个字段
            # 我们需要在 hset 后设置整个 key 的过期时间
            await self._cache_manager._redis.expire(snapshot_key, snapshot_ttl)
            
            logger.debug(
                f"已更新行情快照缓存: {snapshot_key}, TTL={snapshot_ttl}秒"
            )

        except SerializationError as e:
            logger.error(f"行情数据序列化失败: {instrument_id}, 错误: {e}")
        except Exception as e:
            logger.error(f"Redis 缓存行情数据失败: {instrument_id}, 错误: {e}")
            # 标记 Redis 不可用
            if self._cache_manager:
                self._cache_manager._available = False

    async def query_market_snapshot(
        self, instrument_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        查询行情快照（Cache-Aside 模式）

        从 Redis 缓存中查询指定合约的最新行情快照。
        如果缓存未命中或 Redis 不可用，返回 None。

        Args:
            instrument_id: 合约代码

        Returns:
            Optional[Dict[str, Any]]: 行情数据字典，未找到返回 None

        Note:
            - CTP 行情 API 是推送模式，没有主动查询接口
            - 此方法只从缓存读取，不会触发 CTP 查询
            - 缓存命中率会被记录到性能指标中
        """
        # 检查 CacheManager 是否可用
        if not self._cache_manager or not self._cache_manager.is_available():
            logger.debug(f"Redis 不可用，无法查询行情快照: {instrument_id}")
            # 记录缓存未命中
            if self._metrics_collector:
                self._metrics_collector.record_counter("cache_miss_market_snapshot")
            return None

        try:
            # 从 Redis Hash 读取行情快照
            snapshot_key = f"market:snapshot:{instrument_id}"
            serialized_data = await self._cache_manager.hget(snapshot_key, "data")

            if serialized_data:
                # 反序列化数据
                market_data = self._serializer.deserialize(serialized_data)
                
                # 记录缓存命中
                if self._metrics_collector:
                    self._metrics_collector.record_counter("cache_hit_market_snapshot")
                
                logger.debug(f"从缓存查询到行情快照: {instrument_id}")
                return market_data
            else:
                # 缓存未命中
                if self._metrics_collector:
                    self._metrics_collector.record_counter("cache_miss_market_snapshot")
                
                logger.debug(f"缓存未命中，行情快照不存在: {instrument_id}")
                return None

        except SerializationError as e:
            logger.error(f"反序列化行情快照失败: {instrument_id}, 错误: {e}")
            if self._metrics_collector:
                self._metrics_collector.record_counter("cache_miss_market_snapshot")
            return None
        except Exception as e:
            logger.error(f"查询行情快照失败: {instrument_id}, 错误: {e}")
            if self._metrics_collector:
                self._metrics_collector.record_counter("cache_miss_market_snapshot")
            # 标记 Redis 不可用
            if self._cache_manager:
                self._cache_manager._available = False
            return None

