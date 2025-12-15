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
import time

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
        self._strategy_manager: Optional[Any] = None  # 避免循环导入
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

    def set_strategy_manager(self, strategy_manager: Any) -> None:
        """
        设置策略管理器实例

        Args:
            strategy_manager: StrategyManager 实例，用于管理策略
        """
        self._strategy_manager = strategy_manager
        logger.info("MdClient 已注入 StrategyManager")

    async def call(self, request: dict[str, Any]) -> None:
        """
        处理客户端请求的异步方法

        Args:
            request: 请求字典，包含消息类型和相关数据

        Note:
            - 如果是登录请求(ReqUserLogin)，会启动客户端连接
            - 如果是策略管理请求，会调用对应的策略管理方法
            - 如果是其他已注册的消息类型，会调用对应的映射方法
            - 如果是未注册的消息类型，会返回对应的错误响应
        """
        message_type = request[Constant.MessageType]
        
        # 处理登录请求
        if message_type == Constant.ReqUserLogin:
            user_id: str = request[Constant.ReqUserLogin]["UserID"]
            password: str = request[Constant.ReqUserLogin]["Password"]
            await self.start(user_id, password)
            return
        
        # 处理策略管理请求（异步处理）
        if message_type == MdConstant.RegisterStrategy:
            await self.handle_register_strategy(request)
            return
        elif message_type == MdConstant.UnregisterStrategy:
            await self.handle_unregister_strategy(request)
            return
        elif message_type == MdConstant.StartStrategy:
            await self.handle_start_strategy(request)
            return
        elif message_type == MdConstant.StopStrategy:
            await self.handle_stop_strategy(request)
            return
        elif message_type == MdConstant.QueryStrategyStatus:
            await self.handle_query_strategy_status(request)
            return
        elif message_type == MdConstant.ListStrategies:
            await self.handle_list_strategies(request)
            return
        
        # 处理其他 CTP 相关请求（同步处理）
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
        处理来自CTP客户端的响应或返回数据（重写以支持 Redis 缓存和策略分发）

        对于行情数据，会：
        1. 更新行情快照缓存（Hash 结构）
        2. 通过 StrategyManager 广播到所有订阅策略（包含 Redis Pub/Sub）
        3. 记录分发延迟指标
        4. 如果 Redis 不可用，降级到直接推送

        Args:
            data: 包含响应或返回数据的字典，格式为{字段名: 字段值}

        Returns:
            None: 该方法无返回值
        """
        # 记录 CTP 回调开始时间
        callback_start_time = time.time()
        
        # 检查是否为行情数据推送
        message_type = data.get(Constant.MessageType)
        
        if message_type == MdConstant.OnRtnDepthMarketData:
            # 提取行情数据
            market_data = data.get(MdConstant.DepthMarketData)
            
            if market_data:
                # 记录分发开始时间
                broadcast_start_time = time.time()
                
                # 1. Redis 快照缓存操作（不包含 Pub/Sub）
                if self._cache_manager and self._cache_manager.is_available():
                    try:
                        instrument_id = market_data.get("InstrumentID")
                        if instrument_id:
                            # 异步执行 Redis 快照缓存（不阻塞主流程）
                            asyncio.create_task(
                                self._cache_market_snapshot(instrument_id, market_data)
                            )
                    except Exception as e:
                        # Redis 操作失败不影响核心推送功能
                        logger.warning(f"Redis 快照缓存操作失败: {e}")
                
                # 2. 通过 StrategyManager 广播行情到所有订阅策略
                # StrategyManager 内部会处理 Redis Pub/Sub 发布
                if self._strategy_manager:
                    try:
                        # 异步广播行情数据（不阻塞主流程）
                        asyncio.create_task(
                            self._broadcast_with_metrics(market_data, broadcast_start_time)
                        )
                    except Exception as e:
                        logger.warning(f"广播行情到策略管理器失败: {e}")

        # 保持原有逻辑：将数据放入队列
        self._queue.put_nowait(data)
        
        # 记录 CTP 回调到队列的延迟
        if self._metrics_collector:
            callback_latency_ms = (time.time() - callback_start_time) * 1000
            self._metrics_collector.record_latency("md_callback_to_queue_latency", callback_latency_ms)

    async def _broadcast_with_metrics(
        self, market_data: dict[str, Any], start_time: float
    ) -> None:
        """
        广播行情数据并记录分发延迟指标

        Args:
            market_data: 行情数据字典
            start_time: 分发开始时间戳

        Returns:
            None
        """
        try:
            # 调用 StrategyManager 广播
            await self._strategy_manager.broadcast_market_data(market_data)
            
            # 记录分发延迟
            if self._metrics_collector:
                broadcast_latency_ms = (time.time() - start_time) * 1000
                self._metrics_collector.record_latency(
                    "market_broadcast_latency", 
                    broadcast_latency_ms
                )
                
                # 记录分发计数
                self._metrics_collector.record_counter("market_broadcast_count")
                
        except Exception as e:
            logger.error(f"广播行情数据失败: {e}")
            # 记录失败计数
            if self._metrics_collector:
                self._metrics_collector.record_counter("market_broadcast_error")

    async def _cache_market_snapshot(
        self, instrument_id: str, market_data: dict[str, Any]
    ) -> None:
        """
        缓存行情快照到 Redis（仅快照，不包含 Pub/Sub）

        Args:
            instrument_id: 合约代码
            market_data: 行情数据字典

        Returns:
            None
        """
        try:
            # 序列化行情数据
            serialized_data = self._serializer.serialize(market_data)

            # 更新行情快照缓存（Hash 结构）
            snapshot_key = f"market:snapshot:{instrument_id}"
            await self._cache_manager.hset(
                snapshot_key, "data", serialized_data
            )
            
            # 设置快照 TTL（从配置读取，默认 60 秒）
            snapshot_ttl = 60  # 默认值
            if hasattr(GlobalConfig, 'Cache') and GlobalConfig.Cache:
                snapshot_ttl = GlobalConfig.Cache.market_snapshot_ttl
            
            await self._cache_manager._redis.expire(snapshot_key, snapshot_ttl)
            
            logger.debug(
                f"已更新行情快照缓存: {snapshot_key}, TTL={snapshot_ttl}秒"
            )

        except SerializationError as e:
            logger.error(f"行情数据序列化失败: {instrument_id}, 错误: {e}")
        except Exception as e:
            logger.error(f"Redis 缓存行情快照失败: {instrument_id}, 错误: {e}")
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


    # ==================== 策略管理相关方法 ====================

    def _create_error_rsp_info(self, error_code: int, error_msg: str) -> dict[str, Any]:
        """
        创建自定义错误响应信息
        
        Args:
            error_code: 错误代码
            error_msg: 错误消息
            
        Returns:
            dict[str, Any]: 错误响应信息字典
        """
        return {
            "ErrorID": error_code,
            "ErrorMsg": error_msg
        }

    async def handle_register_strategy(self, request: dict[str, Any]) -> None:
        """
        处理策略注册请求

        Args:
            request: 请求字典，包含策略ID、名称、配置等信息
        """
        if not self._strategy_manager:
            response = {
                Constant.MessageType: MdConstant.OnRspRegisterStrategy,
                MdConstant.Success: False,
                Constant.RspInfo: self._create_error_rsp_info(500, "策略管理器未初始化")
            }
            if self.rsp_callback:
                await self.rsp_callback(response)
            return

        try:
            # 提取请求参数
            strategy_id = request.get(MdConstant.StrategyID)
            strategy_name = request.get(MdConstant.StrategyName, strategy_id)
            config_data = request.get(MdConstant.StrategyConfig, {})
            subscribed_instruments = request.get(MdConstant.SubscribedInstruments, [])

            if not strategy_id:
                response = {
                    Constant.MessageType: MdConstant.OnRspRegisterStrategy,
                    MdConstant.Success: False,
                    Constant.RspInfo: CallError.get_rsp_info(400)
                }
                if self.rsp_callback:
                    await self.rsp_callback(response)
                return

            # 创建策略配置
            from ..services.strategy_manager import StrategyConfig
            
            strategy_config = StrategyConfig(
                strategy_id=strategy_id,
                name=strategy_name,
                enabled=config_data.get("enabled", True),
                max_memory_mb=config_data.get("max_memory_mb", 512),
                max_cpu_percent=config_data.get("max_cpu_percent", 50.0),
                subscribed_instruments=subscribed_instruments,
                error_threshold=config_data.get("error_threshold", 10)
            )

            # 创建一个简单的策略函数（实际应用中应该由客户端提供）
            async def default_strategy(market_data: dict):
                """默认策略函数，仅记录日志"""
                instrument_id = market_data.get("InstrumentID", "unknown")
                last_price = market_data.get("LastPrice", 0.0)
                logger.debug(
                    f"策略 {strategy_id} 收到行情 - 合约: {instrument_id}, 价格: {last_price}"
                )

            # 注册策略
            success = await self._strategy_manager.register_strategy(
                strategy_id, default_strategy, strategy_config
            )

            # 返回响应
            response = {
                Constant.MessageType: MdConstant.OnRspRegisterStrategy,
                MdConstant.StrategyID: strategy_id,
                MdConstant.Success: success,
                Constant.RspInfo: CallError.get_rsp_info(0) if success else CallError.get_rsp_info(500)
            }
            if self.rsp_callback:
                await self.rsp_callback(response)

        except Exception as e:
            logger.error(f"处理策略注册请求失败: {e}", exc_info=True)
            response = {
                Constant.MessageType: MdConstant.OnRspRegisterStrategy,
                MdConstant.Success: False,
                Constant.RspInfo: self._create_error_rsp_info(500, str(e))
            }
            if self.rsp_callback:
                await self.rsp_callback(response)

    async def handle_unregister_strategy(self, request: dict[str, Any]) -> None:
        """
        处理策略注销请求

        Args:
            request: 请求字典，包含策略ID
        """
        if not self._strategy_manager:
            response = {
                Constant.MessageType: MdConstant.OnRspUnregisterStrategy,
                MdConstant.Success: False,
                Constant.RspInfo: self._create_error_rsp_info(500, "策略管理器未初始化")
            }
            if self.rsp_callback:
                await self.rsp_callback(response)
            return

        try:
            strategy_id = request.get(MdConstant.StrategyID)
            if not strategy_id:
                response = {
                    Constant.MessageType: MdConstant.OnRspUnregisterStrategy,
                    MdConstant.Success: False,
                    Constant.RspInfo: CallError.get_rsp_info(400)
                }
                if self.rsp_callback:
                    await self.rsp_callback(response)
                return

            # 注销策略
            success = await self._strategy_manager.unregister_strategy(strategy_id)

            # 返回响应
            response = {
                Constant.MessageType: MdConstant.OnRspUnregisterStrategy,
                MdConstant.StrategyID: strategy_id,
                MdConstant.Success: success,
                Constant.RspInfo: CallError.get_rsp_info(0) if success else CallError.get_rsp_info(500)
            }
            if self.rsp_callback:
                await self.rsp_callback(response)

        except Exception as e:
            logger.error(f"处理策略注销请求失败: {e}", exc_info=True)
            response = {
                Constant.MessageType: MdConstant.OnRspUnregisterStrategy,
                MdConstant.Success: False,
                Constant.RspInfo: self._create_error_rsp_info(500, str(e))
            }
            if self.rsp_callback:
                await self.rsp_callback(response)

    async def handle_start_strategy(self, request: dict[str, Any]) -> None:
        """
        处理策略启动请求

        Args:
            request: 请求字典，包含策略ID
        """
        if not self._strategy_manager:
            response = {
                Constant.MessageType: MdConstant.OnRspStartStrategy,
                MdConstant.Success: False,
                Constant.RspInfo: self._create_error_rsp_info(500, "策略管理器未初始化")
            }
            if self.rsp_callback:
                await self.rsp_callback(response)
            return

        try:
            strategy_id = request.get(MdConstant.StrategyID)
            if not strategy_id:
                response = {
                    Constant.MessageType: MdConstant.OnRspStartStrategy,
                    MdConstant.Success: False,
                    Constant.RspInfo: CallError.get_rsp_info(400)
                }
                if self.rsp_callback:
                    await self.rsp_callback(response)
                return

            # 启动策略
            success = await self._strategy_manager.start_strategy(strategy_id)

            # 返回响应
            response = {
                Constant.MessageType: MdConstant.OnRspStartStrategy,
                MdConstant.StrategyID: strategy_id,
                MdConstant.Success: success,
                Constant.RspInfo: CallError.get_rsp_info(0) if success else CallError.get_rsp_info(500)
            }
            if self.rsp_callback:
                await self.rsp_callback(response)

        except Exception as e:
            logger.error(f"处理策略启动请求失败: {e}", exc_info=True)
            response = {
                Constant.MessageType: MdConstant.OnRspStartStrategy,
                MdConstant.Success: False,
                Constant.RspInfo: self._create_error_rsp_info(500, str(e))
            }
            if self.rsp_callback:
                await self.rsp_callback(response)

    async def handle_stop_strategy(self, request: dict[str, Any]) -> None:
        """
        处理策略停止请求

        Args:
            request: 请求字典，包含策略ID
        """
        if not self._strategy_manager:
            response = {
                Constant.MessageType: MdConstant.OnRspStopStrategy,
                MdConstant.Success: False,
                Constant.RspInfo: self._create_error_rsp_info(500, "策略管理器未初始化")
            }
            if self.rsp_callback:
                await self.rsp_callback(response)
            return

        try:
            strategy_id = request.get(MdConstant.StrategyID)
            if not strategy_id:
                response = {
                    Constant.MessageType: MdConstant.OnRspStopStrategy,
                    MdConstant.Success: False,
                    Constant.RspInfo: CallError.get_rsp_info(400)
                }
                if self.rsp_callback:
                    await self.rsp_callback(response)
                return

            # 停止策略
            success = await self._strategy_manager.stop_strategy(strategy_id)

            # 返回响应
            response = {
                Constant.MessageType: MdConstant.OnRspStopStrategy,
                MdConstant.StrategyID: strategy_id,
                MdConstant.Success: success,
                Constant.RspInfo: CallError.get_rsp_info(0) if success else CallError.get_rsp_info(500)
            }
            if self.rsp_callback:
                await self.rsp_callback(response)

        except Exception as e:
            logger.error(f"处理策略停止请求失败: {e}", exc_info=True)
            response = {
                Constant.MessageType: MdConstant.OnRspStopStrategy,
                MdConstant.Success: False,
                Constant.RspInfo: self._create_error_rsp_info(500, str(e))
            }
            if self.rsp_callback:
                await self.rsp_callback(response)

    async def handle_query_strategy_status(self, request: dict[str, Any]) -> None:
        """
        处理策略状态查询请求

        Args:
            request: 请求字典，包含策略ID
        """
        if not self._strategy_manager:
            response = {
                Constant.MessageType: MdConstant.OnRspQueryStrategyStatus,
                MdConstant.Success: False,
                Constant.RspInfo: self._create_error_rsp_info(500, "策略管理器未初始化")
            }
            if self.rsp_callback:
                await self.rsp_callback(response)
            return

        try:
            strategy_id = request.get(MdConstant.StrategyID)
            if not strategy_id:
                response = {
                    Constant.MessageType: MdConstant.OnRspQueryStrategyStatus,
                    MdConstant.Success: False,
                    Constant.RspInfo: CallError.get_rsp_info(400)
                }
                if self.rsp_callback:
                    await self.rsp_callback(response)
                return

            # 查询策略状态
            strategy_info = self._strategy_manager.get_strategy_status(strategy_id)

            if strategy_info:
                # 转换为字典格式
                info_dict = {
                    "strategy_id": strategy_info.strategy_id,
                    "name": strategy_info.name,
                    "status": strategy_info.status.value,
                    "subscribed_instruments": strategy_info.subscribed_instruments,
                    "error_count": strategy_info.error_count,
                    "last_error": strategy_info.last_error,
                    "start_time": strategy_info.start_time,
                    "stop_time": strategy_info.stop_time
                }

                response = {
                    Constant.MessageType: MdConstant.OnRspQueryStrategyStatus,
                    MdConstant.StrategyID: strategy_id,
                    MdConstant.StrategyInfo: info_dict,
                    MdConstant.Success: True,
                    Constant.RspInfo: CallError.get_rsp_info(0)
                }
            else:
                response = {
                    Constant.MessageType: MdConstant.OnRspQueryStrategyStatus,
                    MdConstant.StrategyID: strategy_id,
                    MdConstant.Success: False,
                    Constant.RspInfo: CallError.get_rsp_info(404)
                }

            if self.rsp_callback:
                await self.rsp_callback(response)

        except Exception as e:
            logger.error(f"处理策略状态查询请求失败: {e}", exc_info=True)
            response = {
                Constant.MessageType: MdConstant.OnRspQueryStrategyStatus,
                MdConstant.Success: False,
                Constant.RspInfo: self._create_error_rsp_info(500, str(e))
            }
            if self.rsp_callback:
                await self.rsp_callback(response)

    async def handle_list_strategies(self, request: dict[str, Any]) -> None:
        """
        处理策略列表查询请求

        Args:
            request: 请求字典
        """
        if not self._strategy_manager:
            response = {
                Constant.MessageType: MdConstant.OnRspListStrategies,
                MdConstant.Success: False,
                Constant.RspInfo: self._create_error_rsp_info(500, "策略管理器未初始化")
            }
            if self.rsp_callback:
                await self.rsp_callback(response)
            return

        try:
            # 获取所有策略信息
            strategies = self._strategy_manager.list_strategies()

            # 转换为字典列表
            strategy_list = []
            for strategy_info in strategies:
                info_dict = {
                    "strategy_id": strategy_info.strategy_id,
                    "name": strategy_info.name,
                    "status": strategy_info.status.value,
                    "subscribed_instruments": strategy_info.subscribed_instruments,
                    "error_count": strategy_info.error_count,
                    "last_error": strategy_info.last_error,
                    "start_time": strategy_info.start_time,
                    "stop_time": strategy_info.stop_time
                }
                strategy_list.append(info_dict)

            response = {
                Constant.MessageType: MdConstant.OnRspListStrategies,
                MdConstant.StrategyList: strategy_list,
                MdConstant.Success: True,
                Constant.RspInfo: CallError.get_rsp_info(0)
            }
            if self.rsp_callback:
                await self.rsp_callback(response)

        except Exception as e:
            logger.error(f"处理策略列表查询请求失败: {e}", exc_info=True)
            response = {
                Constant.MessageType: MdConstant.OnRspListStrategies,
                MdConstant.Success: False,
                Constant.RspInfo: self._create_error_rsp_info(500, str(e))
            }
            if self.rsp_callback:
                await self.rsp_callback(response)
