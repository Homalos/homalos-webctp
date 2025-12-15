#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : cache_manager.py
@Date       : 2025/12/13 00:00
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: Redis 缓存管理器 - 提供统一的缓存操作接口
"""

from typing import Optional, AsyncIterator, Dict, Any
import asyncio

try:
    import redis.asyncio as aioredis
    from redis.asyncio import Redis, ConnectionPool
    from redis.exceptions import RedisError, ConnectionError as RedisConnectionError, TimeoutError as RedisTimeoutError
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    Redis = Any
    ConnectionPool = Any
    RedisError = Exception
    RedisConnectionError = Exception
    RedisTimeoutError = Exception

from loguru import logger

from ..utils.config import CacheConfig
from ..utils.serialization import get_msgpack_serializer


class CacheManager:
    """
    Redis 缓存管理器
    
    提供统一的 Redis 缓存操作接口，支持：
    - 基础 Key-Value 操作
    - Hash 操作
    - Pub/Sub 消息发布订阅
    - Sorted Set 操作
    - 健康检查和降级处理
    """

    def __init__(self):
        """初始化 CacheManager"""
        self._pool: Optional[ConnectionPool] = None
        self._redis: Optional[Redis] = None
        self._config: Optional[CacheConfig] = None
        self._available: bool = False
        self._serializer = get_msgpack_serializer()
        self._health_check_task: Optional[asyncio.Task] = None
        self._metrics_collector: Optional[Any] = None  # 避免循环导入

    def set_metrics_collector(self, metrics_collector: Any) -> None:
        """
        设置性能指标收集器实例

        Args:
            metrics_collector: MetricsCollector 实例，用于收集性能指标
        """
        self._metrics_collector = metrics_collector
        logger.info("CacheManager: MetricsCollector 已注入")

    async def initialize(self, config: CacheConfig) -> None:
        """
        初始化 Redis 连接池

        Args:
            config: Redis 缓存配置对象

        Raises:
            ImportError: Redis 库未安装时抛出
            RedisConnectionError: Redis 连接失败时抛出
        """
        if not REDIS_AVAILABLE:
            logger.error("redis 库未安装，无法使用缓存功能")
            raise ImportError("redis 库未安装，请运行: uv add redis")

        self._config = config

        if not config.enabled:
            logger.info("Redis 缓存未启用")
            self._available = False
            return

        try:
            # 创建连接池
            self._pool = ConnectionPool(
                host=config.host,
                port=config.port,
                password=config.password,
                db=config.db,
                max_connections=config.max_connections,
                socket_timeout=config.socket_timeout,
                socket_connect_timeout=config.socket_connect_timeout,
                decode_responses=False,  # 使用字节模式，配合 msgpack
            )

            # 创建 Redis 客户端
            self._redis = Redis(connection_pool=self._pool)

            # 测试连接
            await self._redis.ping()
            self._available = True
            logger.info(
                f"Redis 连接成功: {config.host}:{config.port}, DB={config.db}"
            )

            # 启动健康检查任务
            self._health_check_task = asyncio.create_task(self._periodic_health_check())

        except (RedisConnectionError, RedisTimeoutError) as e:
            logger.error(f"Redis 连接失败: {e}")
            self._available = False
            raise
        except Exception as e:
            logger.error(f"Redis 初始化失败: {e}")
            self._available = False
            raise

    async def close(self) -> None:
        """
        关闭 Redis 连接池和健康检查任务
        """
        # 取消健康检查任务
        if self._health_check_task and not self._health_check_task.done():
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        # 关闭 Redis 连接
        if self._redis:
            await self._redis.aclose()
            self._redis = None

        # 关闭连接池
        if self._pool:
            await self._pool.aclose()
            self._pool = None

        self._available = False
        logger.info("Redis 连接已关闭")

    def is_available(self) -> bool:
        """
        检查 Redis 是否可用

        Returns:
            bool: Redis 可用返回 True，否则返回 False
        """
        return self._available

    async def health_check(self) -> bool:
        """
        执行 Redis 健康检查

        Returns:
            bool: 健康检查通过返回 True，否则返回 False
        """
        if not self._redis or not self._available:
            return False

        try:
            await asyncio.wait_for(
                self._redis.ping(),
                timeout=self._config.socket_timeout if self._config else 5.0
            )
            if not self._available:
                self._available = True
                logger.info("Redis 健康检查通过，恢复可用状态")
            return True
        except (RedisError, asyncio.TimeoutError) as e:
            if self._available:
                logger.warning(f"Redis 健康检查失败: {e}")
                self._available = False
            return False

    async def _periodic_health_check(self) -> None:
        """
        定期执行健康检查（每 30 秒）
        """
        while True:
            try:
                await asyncio.sleep(30)
                await self.health_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"健康检查任务异常: {e}")

    async def get(self, key: str) -> Optional[bytes]:
        """
        获取缓存数据 (Cache-Aside 模式)

        Args:
            key: 缓存键

        Returns:
            Optional[bytes]: 缓存数据（msgpack 序列化的字节流），未找到返回 None

        Raises:
            RedisError: Redis 操作失败时抛出
        """
        if not self._available or not self._redis:
            logger.debug(f"Redis 不可用，跳过 get 操作: {key}")
            return None

        import time
        start_time = time.time()
        
        try:
            data = await asyncio.wait_for(
                self._redis.get(key),
                timeout=self._config.socket_timeout if self._config else 5.0
            )
            
            # 记录 Redis 操作延迟
            if self._metrics_collector:
                latency_ms = (time.time() - start_time) * 1000
                self._metrics_collector.record_latency("redis_get_latency", latency_ms)
                
                # 记录缓存命中/未命中
                if data is not None:
                    self._metrics_collector.record_counter("cache_hit")
                else:
                    self._metrics_collector.record_counter("cache_miss")
            
            return data
        except (RedisError, asyncio.TimeoutError) as e:
            logger.warning(f"Redis get 操作失败: {key}, 错误: {e}")
            self._available = False
            raise

    async def set(
        self, key: str, value: bytes, ttl: Optional[int] = None
    ) -> bool:
        """
        设置缓存数据

        Args:
            key: 缓存键
            value: 缓存值（msgpack 序列化的字节流）
            ttl: 过期时间（秒），None 表示永不过期

        Returns:
            bool: 设置成功返回 True，失败返回 False

        Raises:
            RedisError: Redis 操作失败时抛出
        """
        if not self._available or not self._redis:
            logger.debug(f"Redis 不可用，跳过 set 操作: {key}")
            return False

        import time
        start_time = time.time()
        
        try:
            if ttl:
                result = await asyncio.wait_for(
                    self._redis.setex(key, ttl, value),
                    timeout=self._config.socket_timeout if self._config else 5.0
                )
            else:
                result = await asyncio.wait_for(
                    self._redis.set(key, value),
                    timeout=self._config.socket_timeout if self._config else 5.0
                )
            
            # 记录 Redis 操作延迟
            if self._metrics_collector:
                latency_ms = (time.time() - start_time) * 1000
                self._metrics_collector.record_latency("redis_set_latency", latency_ms)
            
            return bool(result)
        except (RedisError, asyncio.TimeoutError) as e:
            logger.warning(f"Redis set 操作失败: {key}, 错误: {e}")
            self._available = False
            raise

    async def delete(self, key: str) -> bool:
        """
        删除缓存数据

        Args:
            key: 缓存键

        Returns:
            bool: 删除成功返回 True，失败返回 False

        Raises:
            RedisError: Redis 操作失败时抛出
        """
        if not self._available or not self._redis:
            logger.debug(f"Redis 不可用，跳过 delete 操作: {key}")
            return False

        try:
            result = await asyncio.wait_for(
                self._redis.delete(key),
                timeout=self._config.socket_timeout if self._config else 5.0
            )
            return result > 0
        except (RedisError, asyncio.TimeoutError) as e:
            logger.warning(f"Redis delete 操作失败: {key}, 错误: {e}")
            self._available = False
            raise

    async def hget(self, name: str, key: str) -> Optional[bytes]:
        """
        获取 Hash 字段值

        Args:
            name: Hash 名称
            key: 字段名

        Returns:
            Optional[bytes]: 字段值（msgpack 序列化的字节流），未找到返回 None

        Raises:
            RedisError: Redis 操作失败时抛出
        """
        if not self._available or not self._redis:
            logger.debug(f"Redis 不可用，跳过 hget 操作: {name}.{key}")
            return None

        import time
        start_time = time.time()
        
        try:
            data = await asyncio.wait_for(
                self._redis.hget(name, key),
                timeout=self._config.socket_timeout if self._config else 5.0
            )
            
            # 记录 Redis 操作延迟
            if self._metrics_collector:
                latency_ms = (time.time() - start_time) * 1000
                self._metrics_collector.record_latency("redis_hget_latency", latency_ms)
                
                # 记录缓存命中/未命中
                if data is not None:
                    self._metrics_collector.record_counter("cache_hit")
                else:
                    self._metrics_collector.record_counter("cache_miss")
            
            return data
        except (RedisError, asyncio.TimeoutError) as e:
            logger.warning(f"Redis hget 操作失败: {name}.{key}, 错误: {e}")
            self._available = False
            raise

    async def hset(self, name: str, key: str, value: bytes) -> bool:
        """
        设置 Hash 字段值

        Args:
            name: Hash 名称
            key: 字段名
            value: 字段值（msgpack 序列化的字节流）

        Returns:
            bool: 设置成功返回 True，失败返回 False

        Raises:
            RedisError: Redis 操作失败时抛出
        """
        if not self._available or not self._redis:
            logger.debug(f"Redis 不可用，跳过 hset 操作: {name}.{key}")
            return False

        import time
        start_time = time.time()
        
        try:
            result = await asyncio.wait_for(
                self._redis.hset(name, key, value),
                timeout=self._config.socket_timeout if self._config else 5.0
            )
            
            # 记录 Redis 操作延迟
            if self._metrics_collector:
                latency_ms = (time.time() - start_time) * 1000
                self._metrics_collector.record_latency("redis_hset_latency", latency_ms)
            
            return result >= 0
        except (RedisError, asyncio.TimeoutError) as e:
            logger.warning(f"Redis hset 操作失败: {name}.{key}, 错误: {e}")
            self._available = False
            raise

    async def hgetall(self, name: str) -> Dict[bytes, bytes]:
        """
        获取 Hash 所有字段

        Args:
            name: Hash 名称

        Returns:
            Dict[bytes, bytes]: 所有字段的字典，键和值都是字节流

        Raises:
            RedisError: Redis 操作失败时抛出
        """
        if not self._available or not self._redis:
            logger.debug(f"Redis 不可用，跳过 hgetall 操作: {name}")
            return {}

        try:
            data = await asyncio.wait_for(
                self._redis.hgetall(name),
                timeout=self._config.socket_timeout if self._config else 5.0
            )
            return data
        except (RedisError, asyncio.TimeoutError) as e:
            logger.warning(f"Redis hgetall 操作失败: {name}, 错误: {e}")
            self._available = False
            raise

    async def publish(self, channel: str, message: bytes) -> int:
        """
        发布消息到 Pub/Sub 频道

        Args:
            channel: 频道名称
            message: 消息内容（msgpack 序列化的字节流）

        Returns:
            int: 接收消息的订阅者数量

        Raises:
            RedisError: Redis 操作失败时抛出
        """
        if not self._available or not self._redis:
            logger.debug(f"Redis 不可用，跳过 publish 操作: {channel}")
            return 0

        import time
        start_time = time.time()
        
        try:
            result = await asyncio.wait_for(
                self._redis.publish(channel, message),
                timeout=self._config.socket_timeout if self._config else 5.0
            )
            
            # 记录 Redis 操作延迟
            if self._metrics_collector:
                latency_ms = (time.time() - start_time) * 1000
                self._metrics_collector.record_latency("redis_publish_latency", latency_ms)
            
            return result
        except (RedisError, asyncio.TimeoutError) as e:
            logger.warning(f"Redis publish 操作失败: {channel}, 错误: {e}")
            self._available = False
            raise

    async def subscribe(self, channel: str) -> AsyncIterator[bytes]:
        """
        订阅 Pub/Sub 频道

        Args:
            channel: 频道名称

        Yields:
            bytes: 接收到的消息（msgpack 序列化的字节流）

        Raises:
            RedisError: Redis 操作失败时抛出
        """
        if not self._available or not self._redis:
            logger.warning(f"Redis 不可用，无法订阅频道: {channel}")
            return

        pubsub = None
        try:
            pubsub = self._redis.pubsub()
            await pubsub.subscribe(channel)
            logger.info(f"成功订阅 Redis 频道: {channel}")

            async for message in pubsub.listen():
                if message["type"] == "message":
                    yield message["data"]

        except (RedisError, asyncio.TimeoutError) as e:
            logger.error(f"Redis subscribe 操作失败: {channel}, 错误: {e}")
            self._available = False
            raise
        finally:
            if pubsub:
                await pubsub.unsubscribe(channel)
                await pubsub.aclose()

    async def zadd(
        self, name: str, mapping: Dict[str, float], ttl: Optional[int] = None
    ) -> int:
        """
        添加到 Sorted Set

        Args:
            name: Sorted Set 名称
            mapping: 成员和分数的映射字典 {member: score}
            ttl: 过期时间（秒），None 表示永不过期

        Returns:
            int: 添加的新成员数量

        Raises:
            RedisError: Redis 操作失败时抛出
        """
        if not self._available or not self._redis:
            logger.debug(f"Redis 不可用，跳过 zadd 操作: {name}")
            return 0

        try:
            result = await asyncio.wait_for(
                self._redis.zadd(name, mapping),
                timeout=self._config.socket_timeout if self._config else 5.0
            )

            # 设置 TTL
            if ttl:
                await asyncio.wait_for(
                    self._redis.expire(name, ttl),
                    timeout=self._config.socket_timeout if self._config else 5.0
                )

            return result
        except (RedisError, asyncio.TimeoutError) as e:
            logger.warning(f"Redis zadd 操作失败: {name}, 错误: {e}")
            self._available = False
            raise

    async def zrange(
        self, name: str, start: int, end: int, withscores: bool = False
    ) -> list:
        """
        获取 Sorted Set 范围内的成员

        Args:
            name: Sorted Set 名称
            start: 起始索引
            end: 结束索引
            withscores: 是否返回分数

        Returns:
            list: 成员列表，如果 withscores=True，返回 [(member, score), ...]

        Raises:
            RedisError: Redis 操作失败时抛出
        """
        if not self._available or not self._redis:
            logger.debug(f"Redis 不可用，跳过 zrange 操作: {name}")
            return []

        try:
            result = await asyncio.wait_for(
                self._redis.zrange(name, start, end, withscores=withscores),
                timeout=self._config.socket_timeout if self._config else 5.0
            )
            return result
        except (RedisError, asyncio.TimeoutError) as e:
            logger.warning(f"Redis zrange 操作失败: {name}, 错误: {e}")
            self._available = False
            raise


# 全局单例实例（可选）
_cache_manager_instance: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """
    获取全局 CacheManager 单例实例

    Returns:
        CacheManager: 全局缓存管理器实例
    """
    global _cache_manager_instance
    if _cache_manager_instance is None:
        _cache_manager_instance = CacheManager()
    return _cache_manager_instance


if __name__ == "__main__":
    import asyncio
    from ..utils.config import CacheConfig

    async def test_cache_manager():
        """测试 CacheManager 基本功能"""
        # 创建测试配置
        config = CacheConfig(
            enabled=True,
            host="localhost",
            port=6379,
            db=0,
        )

        # 初始化缓存管理器
        cache = CacheManager()
        try:
            await cache.initialize(config)
            print(f"Redis 可用: {cache.is_available()}")

            # 测试基础操作
            serializer = get_msgpack_serializer()
            test_data = {"name": "测试", "value": 123}
            serialized = serializer.serialize(test_data)

            # Set
            await cache.set("test:key", serialized, ttl=60)
            print("Set 操作完成")

            # Get
            data = await cache.get("test:key")
            if data:
                deserialized = serializer.deserialize(data)
                print(f"Get 操作结果: {deserialized}")

            # Hash 操作
            await cache.hset("test:hash", "field1", serialized)
            hash_data = await cache.hget("test:hash", "field1")
            if hash_data:
                print(f"Hash 操作结果: {serializer.deserialize(hash_data)}")

            # 清理
            await cache.delete("test:key")
            await cache.delete("test:hash")

        finally:
            await cache.close()

    # 运行测试
    asyncio.run(test_cache_manager())
