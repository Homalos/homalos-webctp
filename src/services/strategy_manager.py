#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : strategy_manager.py
@Date       : 2025/12/15 00:00
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: 策略管理器 - 管理多策略并行运行、行情分发和错误隔离
"""

import asyncio
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Awaitable

from loguru import logger

try:
    from .cache_manager import CacheManager
    from ..utils.serialization import get_msgpack_serializer, SerializationError
    from ..utils.config import GlobalConfig
except ImportError:
    from cache_manager import CacheManager
    from src.utils.serialization import get_msgpack_serializer, SerializationError
    from src.utils.config import GlobalConfig


class StrategyStatus(str, Enum):
    """策略状态枚举"""
    REGISTERED = "registered"  # 已注册但未启动
    RUNNING = "running"        # 正在运行
    STOPPED = "stopped"        # 已停止
    ERROR = "error"            # 错误状态


@dataclass
class StrategyInfo:
    """策略信息数据类
    
    存储策略的元数据和运行状态信息
    """
    strategy_id: str                          # 策略唯一标识
    name: str                                 # 策略名称
    status: StrategyStatus                    # 当前状态
    subscribed_instruments: List[str]         # 订阅的合约列表
    error_count: int = 0                      # 错误计数
    last_error: Optional[str] = None          # 最后一次错误信息
    start_time: Optional[float] = None        # 启动时间戳
    stop_time: Optional[float] = None         # 停止时间戳


@dataclass
class StrategyConfig:
    """单个策略的配置
    
    定义策略的运行参数和资源限制
    """
    strategy_id: str                          # 策略ID
    name: str                                 # 策略名称
    enabled: bool = True                      # 是否启用
    max_memory_mb: int = 512                  # 最大内存限制（MB）
    max_cpu_percent: float = 50.0             # 最大CPU使用率（%）
    subscribed_instruments: List[str] = field(default_factory=list)  # 订阅合约列表
    error_threshold: int = 10                 # 错误阈值（连续错误次数）


class StrategyManager:
    """策略管理器
    
    功能：
    - 管理策略生命周期（注册、启动、停止、注销）
    - 使用 asyncio.TaskGroup 管理策略协程池
    - 通过 Redis Pub/Sub 广播行情数据到所有订阅策略
    - 实现策略错误隔离（单个策略崩溃不影响其他策略）
    - 提供策略状态查询接口
    
    使用示例：
        # 创建策略管理器
        cache_manager = CacheManager()
        await cache_manager.initialize(config)
        
        strategy_manager = StrategyManager(cache_manager, max_strategies=10)
        
        # 定义策略函数
        async def my_strategy(market_data: dict):
            print(f"收到行情: {market_data}")
        
        # 注册策略
        config = StrategyConfig(
            strategy_id="strategy_1",
            name="测试策略",
            subscribed_instruments=["rb2505", "au2506"]
        )
        await strategy_manager.register_strategy("strategy_1", my_strategy, config)
        
        # 启动策略
        await strategy_manager.start_strategy("strategy_1")
        
        # 广播行情
        await strategy_manager.broadcast_market_data({
            "InstrumentID": "rb2505",
            "LastPrice": 3500.0
        })
        
        # 停止策略
        await strategy_manager.stop_strategy("strategy_1")
    """
    
    def __init__(
        self, 
        cache_manager: Optional[CacheManager] = None,
        max_strategies: int = None
    ):
        """初始化策略管理器
        
        Args:
            cache_manager: Redis 缓存管理器实例，用于 Pub/Sub 行情分发
            max_strategies: 最大策略数量，如果为 None 则从配置读取
        """
        self._cache_manager = cache_manager
        self._serializer = get_msgpack_serializer()
        
        # 从配置读取最大策略数量
        if max_strategies is None:
            if hasattr(GlobalConfig, 'Strategy'):
                max_strategies = GlobalConfig.Strategy.max_strategies
            else:
                max_strategies = 10
        self._max_strategies = max_strategies
        
        # 策略信息存储
        self._strategies: Dict[str, StrategyInfo] = {}           # 策略信息字典
        self._strategy_tasks: Dict[str, asyncio.Task] = {}       # 策略任务字典
        self._strategy_funcs: Dict[str, Callable] = {}           # 策略函数字典
        self._strategy_configs: Dict[str, StrategyConfig] = {}   # 策略配置字典
        
        # 运行状态
        self._running: bool = False
        
        logger.info(
            f"StrategyManager 初始化完成，最大策略数量: {self._max_strategies}",
            tag="strategy"
        )

    async def register_strategy(
        self, 
        strategy_id: str, 
        strategy_func: Callable[[dict], Awaitable[None]], 
        config: StrategyConfig
    ) -> bool:
        """注册新策略
        
        将策略函数和配置注册到管理器中。注册后的策略处于 REGISTERED 状态，
        需要调用 start_strategy() 才能启动运行。
        
        Args:
            strategy_id: 策略唯一标识符
            strategy_func: 策略函数，接收行情数据字典作为参数
            config: 策略配置对象
        
        Returns:
            bool: 注册成功返回 True，失败返回 False
        
        注意：
            - 策略ID必须唯一
            - 策略数量不能超过最大限制
            - 策略函数必须是异步函数
        """
        # 验证策略ID唯一性
        if strategy_id in self._strategies:
            logger.warning(
                f"策略注册失败：策略ID已存在 - {strategy_id}",
                tag="strategy"
            )
            return False
        
        # 检查策略数量限制
        if len(self._strategies) >= self._max_strategies:
            logger.warning(
                f"策略注册失败：已达到最大策略数量限制 ({self._max_strategies})",
                tag="strategy"
            )
            return False
        
        # 验证策略函数是否为协程函数
        if not asyncio.iscoroutinefunction(strategy_func):
            logger.error(
                f"策略注册失败：策略函数必须是异步函数 - {strategy_id}",
                tag="strategy"
            )
            return False
        
        try:
            # 创建策略信息
            strategy_info = StrategyInfo(
                strategy_id=strategy_id,
                name=config.name,
                status=StrategyStatus.REGISTERED,
                subscribed_instruments=config.subscribed_instruments.copy(),
                error_count=0,
                last_error=None,
                start_time=None,
                stop_time=None
            )
            
            # 存储策略信息
            self._strategies[strategy_id] = strategy_info
            self._strategy_funcs[strategy_id] = strategy_func
            self._strategy_configs[strategy_id] = config
            
            logger.info(
                f"策略注册成功 - ID: {strategy_id}, 名称: {config.name}, "
                f"订阅合约: {config.subscribed_instruments}",
                tag="strategy"
            )
            return True
            
        except Exception as e:
            logger.error(
                f"策略注册失败 - {strategy_id}: {e}",
                tag="strategy"
            )
            return False
    
    async def unregister_strategy(self, strategy_id: str) -> bool:
        """注销策略
        
        从管理器中移除策略。如果策略正在运行，会先停止策略再注销。
        
        Args:
            strategy_id: 策略唯一标识符
        
        Returns:
            bool: 注销成功返回 True，失败返回 False
        """
        # 检查策略是否存在
        if strategy_id not in self._strategies:
            logger.warning(
                f"策略注销失败：策略不存在 - {strategy_id}",
                tag="strategy"
            )
            return False
        
        try:
            # 如果策略正在运行，先停止
            strategy_info = self._strategies[strategy_id]
            if strategy_info.status == StrategyStatus.RUNNING:
                logger.info(
                    f"策略正在运行，先停止策略 - {strategy_id}",
                    tag="strategy"
                )
                await self.stop_strategy(strategy_id)
            
            # 清理策略相关资源
            del self._strategies[strategy_id]
            del self._strategy_funcs[strategy_id]
            del self._strategy_configs[strategy_id]
            
            # 清理任务引用（如果存在）
            if strategy_id in self._strategy_tasks:
                del self._strategy_tasks[strategy_id]
            
            logger.info(
                f"策略注销成功 - {strategy_id}",
                tag="strategy"
            )
            return True
            
        except Exception as e:
            logger.error(
                f"策略注销失败 - {strategy_id}: {e}",
                tag="strategy"
            )
            return False
    
    async def start_strategy(self, strategy_id: str) -> bool:
        """启动指定策略
        
        启动策略后，策略会开始订阅行情数据并执行策略逻辑。
        
        Args:
            strategy_id: 策略唯一标识符
        
        Returns:
            bool: 启动成功返回 True，失败返回 False
        
        注意：
            - 策略必须已注册
            - 策略不能已经在运行
            - 需要 Redis 可用才能订阅行情
        """
        # 检查策略是否存在
        if strategy_id not in self._strategies:
            logger.warning(
                f"策略启动失败：策略不存在 - {strategy_id}",
                tag="strategy"
            )
            return False
        
        strategy_info = self._strategies[strategy_id]
        
        # 检查策略状态
        if strategy_info.status == StrategyStatus.RUNNING:
            logger.warning(
                f"策略启动失败：策略已在运行 - {strategy_id}",
                tag="strategy"
            )
            return False
        
        # 检查配置是否启用
        config = self._strategy_configs[strategy_id]
        if not config.enabled:
            logger.warning(
                f"策略启动失败：策略未启用 - {strategy_id}",
                tag="strategy"
            )
            return False
        
        try:
            # 创建策略任务
            task = asyncio.create_task(
                self._run_strategy(strategy_id),
                name=f"strategy-{strategy_id}"
            )
            self._strategy_tasks[strategy_id] = task
            
            # 更新策略状态
            strategy_info.status = StrategyStatus.RUNNING
            strategy_info.start_time = time.time()
            strategy_info.error_count = 0
            strategy_info.last_error = None
            
            logger.info(
                f"策略启动成功 - {strategy_id}",
                tag="strategy"
            )
            return True
            
        except Exception as e:
            logger.error(
                f"策略启动失败 - {strategy_id}: {e}",
                tag="strategy"
            )
            strategy_info.status = StrategyStatus.ERROR
            strategy_info.last_error = str(e)
            return False
    
    async def stop_strategy(self, strategy_id: str) -> bool:
        """停止指定策略
        
        停止策略后，策略会停止接收行情数据并停止执行。
        
        Args:
            strategy_id: 策略唯一标识符
        
        Returns:
            bool: 停止成功返回 True，失败返回 False
        """
        # 检查策略是否存在
        if strategy_id not in self._strategies:
            logger.warning(
                f"策略停止失败：策略不存在 - {strategy_id}",
                tag="strategy"
            )
            return False
        
        strategy_info = self._strategies[strategy_id]
        
        # 检查策略状态
        if strategy_info.status != StrategyStatus.RUNNING:
            logger.warning(
                f"策略停止失败：策略未在运行 - {strategy_id}",
                tag="strategy"
            )
            return False
        
        try:
            # 取消策略任务
            if strategy_id in self._strategy_tasks:
                task = self._strategy_tasks[strategy_id]
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                
                # 清理任务引用
                del self._strategy_tasks[strategy_id]
            
            # 更新策略状态
            strategy_info.status = StrategyStatus.STOPPED
            strategy_info.stop_time = time.time()
            
            logger.info(
                f"策略停止成功 - {strategy_id}",
                tag="strategy"
            )
            return True
            
        except Exception as e:
            logger.error(
                f"策略停止失败 - {strategy_id}: {e}",
                tag="strategy"
            )
            return False
    
    async def broadcast_market_data(self, data: dict) -> None:
        """广播行情数据到所有订阅策略
        
        通过 Redis Pub/Sub 将行情数据发布到对应的频道。
        订阅了该合约的策略会自动接收到行情数据。
        
        Args:
            data: 行情数据字典，必须包含 InstrumentID 字段
        
        注意：
            - 需要 Redis 可用
            - 如果 Redis 不可用，会记录警告但不抛出异常
        """
        # 检查 Redis 是否可用
        if not self._cache_manager or not self._cache_manager.is_available():
            logger.debug(
                "Redis 不可用，无法广播行情数据",
                tag="strategy"
            )
            return
        
        try:
            # 提取合约代码
            instrument_id = data.get("InstrumentID")
            if not instrument_id:
                logger.warning(
                    "行情数据缺少 InstrumentID 字段，无法广播",
                    tag="strategy"
                )
                return
            
            # 序列化行情数据
            serialized_data = self._serializer.serialize(data)
            
            # 发布到 Redis Pub/Sub 频道
            channel = f"market:tick:{instrument_id}"
            subscriber_count = await self._cache_manager.publish(channel, serialized_data)
            
            logger.debug(
                f"行情数据已广播 - 合约: {instrument_id}, 订阅者: {subscriber_count}",
                tag="strategy"
            )
            
        except SerializationError as e:
            logger.error(
                f"行情数据序列化失败: {e}",
                tag="strategy"
            )
        except Exception as e:
            logger.error(
                f"广播行情数据失败: {e}",
                tag="strategy"
            )
    
    def get_strategy_status(self, strategy_id: str) -> Optional[StrategyInfo]:
        """获取指定策略的状态信息
        
        Args:
            strategy_id: 策略唯一标识符
        
        Returns:
            Optional[StrategyInfo]: 策略信息对象，策略不存在返回 None
        """
        return self._strategies.get(strategy_id)
    
    def list_strategies(self) -> List[StrategyInfo]:
        """列出所有策略的信息
        
        Returns:
            List[StrategyInfo]: 所有策略的信息列表
        """
        return list(self._strategies.values())

    async def _run_strategy(self, strategy_id: str) -> None:
        """策略执行包装器（私有方法）
        
        包装策略执行逻辑，实现错误隔离和监控。
        单个策略的异常不会影响其他策略的运行。
        
        Args:
            strategy_id: 策略唯一标识符
        """
        strategy_info = self._strategies.get(strategy_id)
        if not strategy_info:
            logger.error(
                f"策略执行失败：策略不存在 - {strategy_id}",
                tag="strategy"
            )
            return
        
        config = self._strategy_configs.get(strategy_id)
        if not config:
            logger.error(
                f"策略执行失败：配置不存在 - {strategy_id}",
                tag="strategy"
            )
            return
        
        logger.info(
            f"策略开始执行 - {strategy_id}",
            tag="strategy"
        )
        
        try:
            # 订阅行情数据并执行策略
            await self._subscribe_market_data(strategy_id)
            
        except asyncio.CancelledError:
            # 策略被取消（正常停止）
            logger.info(
                f"策略已取消 - {strategy_id}",
                tag="strategy"
            )
            raise
            
        except Exception as e:
            # 策略执行异常（错误隔离）
            logger.error(
                f"策略执行异常 - {strategy_id}: {e}",
                tag="strategy",
                exc_info=True
            )
            
            # 更新错误信息
            strategy_info.error_count += 1
            strategy_info.last_error = str(e)
            
            # 检查是否达到错误阈值
            if strategy_info.error_count >= config.error_threshold:
                logger.error(
                    f"策略错误次数达到阈值 ({config.error_threshold})，自动停止 - {strategy_id}",
                    tag="strategy"
                )
                strategy_info.status = StrategyStatus.ERROR
                strategy_info.stop_time = time.time()
            else:
                # 未达到阈值，尝试重启
                logger.warning(
                    f"策略将在 5 秒后重启 - {strategy_id} "
                    f"(错误次数: {strategy_info.error_count}/{config.error_threshold})",
                    tag="strategy"
                )
                await asyncio.sleep(5)
                
                # 重新创建任务
                if strategy_info.status == StrategyStatus.RUNNING:
                    task = asyncio.create_task(
                        self._run_strategy(strategy_id),
                        name=f"strategy-{strategy_id}"
                    )
                    self._strategy_tasks[strategy_id] = task
    
    async def _subscribe_market_data(self, strategy_id: str) -> None:
        """订阅行情数据并执行策略（私有方法）
        
        从 Redis Pub/Sub 接收行情数据，并调用策略函数处理。
        
        Args:
            strategy_id: 策略唯一标识符
        
        Raises:
            Exception: 订阅或执行过程中的任何异常
        """
        strategy_info = self._strategies.get(strategy_id)
        config = self._strategy_configs.get(strategy_id)
        strategy_func = self._strategy_funcs.get(strategy_id)
        
        if not all([strategy_info, config, strategy_func]):
            logger.error(
                f"策略信息不完整 - {strategy_id}",
                tag="strategy"
            )
            return
        
        # 检查 Redis 是否可用
        if not self._cache_manager or not self._cache_manager.is_available():
            logger.error(
                f"Redis 不可用，无法订阅行情 - {strategy_id}",
                tag="strategy"
            )
            raise RuntimeError("Redis 不可用")
        
        # 检查是否有订阅合约
        if not config.subscribed_instruments:
            logger.warning(
                f"策略未订阅任何合约 - {strategy_id}",
                tag="strategy"
            )
            # 策略没有订阅合约，进入等待状态
            while strategy_info.status == StrategyStatus.RUNNING:
                await asyncio.sleep(1)
            return
        
        # 为每个订阅的合约创建订阅任务
        async def subscribe_instrument(instrument_id: str):
            """订阅单个合约的行情"""
            channel = f"market:tick:{instrument_id}"
            logger.info(
                f"策略开始订阅行情 - {strategy_id}, 合约: {instrument_id}",
                tag="strategy"
            )
            
            try:
                async for message in self._cache_manager.subscribe(channel):
                    # 检查策略是否仍在运行
                    if strategy_info.status != StrategyStatus.RUNNING:
                        logger.info(
                            f"策略已停止，退出订阅 - {strategy_id}, 合约: {instrument_id}",
                            tag="strategy"
                        )
                        break
                    
                    try:
                        # 反序列化行情数据
                        market_data = self._serializer.deserialize(message)
                        
                        # 调用策略函数处理行情
                        await strategy_func(market_data)
                        
                    except SerializationError as e:
                        logger.error(
                            f"反序列化行情数据失败 - {strategy_id}: {e}",
                            tag="strategy"
                        )
                    except Exception as e:
                        logger.error(
                            f"策略处理行情失败 - {strategy_id}: {e}",
                            tag="strategy",
                            exc_info=True
                        )
                        # 策略函数异常，向上传播以触发错误处理
                        raise
                        
            except asyncio.CancelledError:
                logger.info(
                    f"订阅任务已取消 - {strategy_id}, 合约: {instrument_id}",
                    tag="strategy"
                )
                raise
            except Exception as e:
                logger.error(
                    f"订阅行情失败 - {strategy_id}, 合约: {instrument_id}: {e}",
                    tag="strategy"
                )
                raise
        
        # 为所有订阅的合约创建并发订阅任务
        try:
            async with asyncio.TaskGroup() as tg:
                for instrument_id in config.subscribed_instruments:
                    tg.create_task(
                        subscribe_instrument(instrument_id),
                        name=f"subscribe-{strategy_id}-{instrument_id}"
                    )
        except* Exception as eg:
            # TaskGroup 中的异常会被包装为 ExceptionGroup
            logger.error(
                f"订阅任务组异常 - {strategy_id}: {eg}",
                tag="strategy"
            )
            raise


# 全局单例实例（可选）
_strategy_manager_instance: Optional[StrategyManager] = None


def get_strategy_manager(
    cache_manager: Optional[CacheManager] = None,
    max_strategies: int = None
) -> StrategyManager:
    """获取全局 StrategyManager 单例实例
    
    Args:
        cache_manager: Redis 缓存管理器实例
        max_strategies: 最大策略数量
    
    Returns:
        StrategyManager: 全局策略管理器实例
    """
    global _strategy_manager_instance
    if _strategy_manager_instance is None:
        _strategy_manager_instance = StrategyManager(cache_manager, max_strategies)
    return _strategy_manager_instance


if __name__ == "__main__":
    # 测试代码
    async def test_strategy_manager():
        """测试策略管理器基本功能"""
        from cache_manager import CacheManager
        from src.utils.config import CacheConfig
        
        # 初始化缓存管理器
        cache_config = CacheConfig(
            enabled=True,
            host="localhost",
            port=6379,
            db=0,
        )
        
        cache_manager = CacheManager()
        try:
            await cache_manager.initialize(cache_config)
        except Exception as e:
            print(f"Redis 初始化失败: {e}")
            print("跳过测试（需要 Redis 运行）")
            return
        
        # 创建策略管理器
        strategy_manager = StrategyManager(cache_manager, max_strategies=5)
        
        # 定义测试策略
        async def test_strategy(market_data: dict):
            """测试策略函数"""
            instrument_id = market_data.get("InstrumentID", "unknown")
            last_price = market_data.get("LastPrice", 0.0)
            print(f"策略收到行情 - 合约: {instrument_id}, 价格: {last_price}")
        
        # 注册策略
        config = StrategyConfig(
            strategy_id="test_strategy_1",
            name="测试策略1",
            subscribed_instruments=["rb2505", "au2506"]
        )
        
        success = await strategy_manager.register_strategy(
            "test_strategy_1",
            test_strategy,
            config
        )
        print(f"策略注册: {'成功' if success else '失败'}")
        
        # 启动策略
        success = await strategy_manager.start_strategy("test_strategy_1")
        print(f"策略启动: {'成功' if success else '失败'}")
        
        # 模拟广播行情
        await asyncio.sleep(1)
        await strategy_manager.broadcast_market_data({
            "InstrumentID": "rb2505",
            "LastPrice": 3500.0
        })
        
        # 等待一段时间
        await asyncio.sleep(2)
        
        # 查询策略状态
        status = strategy_manager.get_strategy_status("test_strategy_1")
        if status:
            print(f"策略状态: {status.status}, 错误次数: {status.error_count}")
        
        # 停止策略
        success = await strategy_manager.stop_strategy("test_strategy_1")
        print(f"策略停止: {'成功' if success else '失败'}")
        
        # 注销策略
        success = await strategy_manager.unregister_strategy("test_strategy_1")
        print(f"策略注销: {'成功' if success else '失败'}")
        
        # 关闭缓存管理器
        await cache_manager.close()
    
    # 运行测试
    asyncio.run(test_strategy_manager())
