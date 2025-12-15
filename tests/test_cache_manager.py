#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : test_cache_manager.py
@Date       : 2025/12/13 00:00
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: CacheManager 单元测试和属性测试
"""

import pytest
import pytest_asyncio
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from hypothesis import given, strategies as st, settings
import fakeredis.aioredis

from src.services.cache_manager import CacheManager
from src.utils.config import CacheConfig
from src.utils.serialization import get_msgpack_serializer


# ============================================================================
# Fixtures
# ============================================================================


@pytest_asyncio.fixture
async def fake_redis_server():
    """创建 fakeredis 服务器实例"""
    server = fakeredis.FakeServer()
    yield server
    # 清理
    server.connected = False


@pytest_asyncio.fixture
async def cache_config():
    """创建测试用的缓存配置"""
    return CacheConfig(
        enabled=True,
        host="localhost",
        port=6379,
        db=0,
        max_connections=10,
        socket_timeout=5.0,
        socket_connect_timeout=5.0,
        market_snapshot_ttl=60,
        market_tick_ttl=5,
        order_ttl=86400,
    )


@pytest_asyncio.fixture
async def cache_manager_with_fake_redis(fake_redis_server, cache_config):
    """创建使用 fakeredis 的 CacheManager 实例"""
    cache_manager = CacheManager()
    
    # 使用 fakeredis 替换真实的 Redis 连接
    with patch('src.services.cache_manager.Redis') as mock_redis_class:
        fake_redis = fakeredis.aioredis.FakeRedis(server=fake_redis_server, decode_responses=False)
        mock_redis_class.return_value = fake_redis
        
        await cache_manager.initialize(cache_config)
        
        # 手动设置 redis 实例为 fakeredis
        cache_manager._redis = fake_redis
        
        yield cache_manager
        
        # 清理
        await cache_manager.close()


@pytest.fixture
def serializer():
    """创建 msgpack 序列化器"""
    return get_msgpack_serializer()


# ============================================================================
# TestCacheManagerBasicOperations - 基础操作测试
# ============================================================================


class TestCacheManagerBasicOperations:
    """CacheManager 基础操作测试"""

    @pytest.mark.asyncio
    async def test_initialize_success(self, fake_redis_server, cache_config):
        """测试成功初始化 Redis 连接"""
        cache_manager = CacheManager()
        
        with patch('src.services.cache_manager.Redis') as mock_redis_class:
            fake_redis = fakeredis.aioredis.FakeRedis(server=fake_redis_server, decode_responses=False)
            mock_redis_class.return_value = fake_redis
            
            await cache_manager.initialize(cache_config)
            
            assert cache_manager.is_available() is True
            assert cache_manager._config == cache_config
            
            await cache_manager.close()

    @pytest.mark.asyncio
    async def test_initialize_disabled(self):
        """测试禁用 Redis 时的初始化"""
        cache_manager = CacheManager()
        config = CacheConfig(enabled=False)
        
        await cache_manager.initialize(config)
        
        assert cache_manager.is_available() is False

    @pytest.mark.asyncio
    async def test_set_and_get(self, cache_manager_with_fake_redis, serializer):
        """测试 set 和 get 操作"""
        cache = cache_manager_with_fake_redis
        
        # 准备测试数据
        test_data = {"name": "测试", "value": 123}
        serialized = serializer.serialize(test_data)
        
        # Set 操作
        result = await cache.set("test:key", serialized)
        assert result is True
        
        # Get 操作
        retrieved = await cache.get("test:key")
        assert retrieved is not None
        deserialized = serializer.deserialize(retrieved)
        assert deserialized == test_data

    @pytest.mark.asyncio
    async def test_set_with_ttl(self, cache_manager_with_fake_redis, serializer):
        """测试带 TTL 的 set 操作"""
        cache = cache_manager_with_fake_redis
        
        test_data = {"ttl_test": True}
        serialized = serializer.serialize(test_data)
        
        # 设置 TTL 为 1 秒
        result = await cache.set("test:ttl", serialized, ttl=1)
        assert result is True
        
        # 立即获取应该成功
        retrieved = await cache.get("test:ttl")
        assert retrieved is not None
        
        # 等待 TTL 过期
        await asyncio.sleep(1.1)
        
        # 过期后应该返回 None
        expired = await cache.get("test:ttl")
        assert expired is None

    @pytest.mark.asyncio
    async def test_delete(self, cache_manager_with_fake_redis, serializer):
        """测试 delete 操作"""
        cache = cache_manager_with_fake_redis
        
        test_data = {"delete_test": True}
        serialized = serializer.serialize(test_data)
        
        # 先设置数据
        await cache.set("test:delete", serialized)
        
        # 删除数据
        result = await cache.delete("test:delete")
        assert result is True
        
        # 验证已删除
        retrieved = await cache.get("test:delete")
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, cache_manager_with_fake_redis):
        """测试获取不存在的键"""
        cache = cache_manager_with_fake_redis
        
        result = await cache.get("nonexistent:key")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_key(self, cache_manager_with_fake_redis):
        """测试删除不存在的键"""
        cache = cache_manager_with_fake_redis
        
        result = await cache.delete("nonexistent:key")
        assert result is False


# ============================================================================
# TestCacheManagerHashOperations - Hash 操作测试
# ============================================================================


class TestCacheManagerHashOperations:
    """CacheManager Hash 操作测试"""

    @pytest.mark.asyncio
    async def test_hset_and_hget(self, cache_manager_with_fake_redis, serializer):
        """测试 hset 和 hget 操作"""
        cache = cache_manager_with_fake_redis
        
        test_data = {"field_value": "测试字段"}
        serialized = serializer.serialize(test_data)
        
        # Hset 操作
        result = await cache.hset("test:hash", "field1", serialized)
        assert result is True
        
        # Hget 操作
        retrieved = await cache.hget("test:hash", "field1")
        assert retrieved is not None
        deserialized = serializer.deserialize(retrieved)
        assert deserialized == test_data

    @pytest.mark.asyncio
    async def test_hgetall(self, cache_manager_with_fake_redis, serializer):
        """测试 hgetall 操作"""
        cache = cache_manager_with_fake_redis
        
        # 设置多个字段
        data1 = {"field": "value1"}
        data2 = {"field": "value2"}
        
        await cache.hset("test:hash:all", "field1", serializer.serialize(data1))
        await cache.hset("test:hash:all", "field2", serializer.serialize(data2))
        
        # 获取所有字段
        all_fields = await cache.hgetall("test:hash:all")
        
        assert len(all_fields) == 2
        assert b"field1" in all_fields
        assert b"field2" in all_fields
        
        # 验证值
        deserialized1 = serializer.deserialize(all_fields[b"field1"])
        deserialized2 = serializer.deserialize(all_fields[b"field2"])
        assert deserialized1 == data1
        assert deserialized2 == data2

    @pytest.mark.asyncio
    async def test_hget_nonexistent_field(self, cache_manager_with_fake_redis):
        """测试获取不存在的 Hash 字段"""
        cache = cache_manager_with_fake_redis
        
        result = await cache.hget("test:hash", "nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_hgetall_empty_hash(self, cache_manager_with_fake_redis):
        """测试获取空 Hash"""
        cache = cache_manager_with_fake_redis
        
        result = await cache.hgetall("nonexistent:hash")
        assert result == {}


# ============================================================================
# TestCacheManagerPubSub - Pub/Sub 测试
# ============================================================================


class TestCacheManagerPubSub:
    """CacheManager Pub/Sub 测试"""

    @pytest.mark.asyncio
    async def test_publish(self, cache_manager_with_fake_redis, serializer):
        """测试 publish 操作"""
        cache = cache_manager_with_fake_redis
        
        test_message = {"message": "测试消息"}
        serialized = serializer.serialize(test_message)
        
        # 发布消息（没有订阅者时返回 0）
        result = await cache.publish("test:channel", serialized)
        assert result >= 0

    @pytest.mark.asyncio
    async def test_subscribe_and_publish(self, cache_manager_with_fake_redis, serializer):
        """测试 subscribe 和 publish 操作"""
        cache = cache_manager_with_fake_redis
        
        test_message = {"message": "测试消息"}
        serialized = serializer.serialize(test_message)
        
        received_messages = []
        
        async def subscriber():
            """订阅者协程"""
            async for message in cache.subscribe("test:channel"):
                received_messages.append(message)
                break  # 收到一条消息后退出
        
        async def publisher():
            """发布者协程"""
            await asyncio.sleep(0.1)  # 等待订阅者准备好
            await cache.publish("test:channel", serialized)
        
        # 并发运行订阅者和发布者
        await asyncio.gather(
            subscriber(),
            publisher(),
        )
        
        # 验证收到的消息
        assert len(received_messages) == 1
        deserialized = serializer.deserialize(received_messages[0])
        assert deserialized == test_message


# ============================================================================
# TestCacheManagerSortedSet - Sorted Set 测试
# ============================================================================


class TestCacheManagerSortedSet:
    """CacheManager Sorted Set 测试"""

    @pytest.mark.asyncio
    async def test_zadd_and_zrange(self, cache_manager_with_fake_redis, serializer):
        """测试 zadd 和 zrange 操作"""
        cache = cache_manager_with_fake_redis
        
        # 添加成员到 Sorted Set
        mapping = {
            "member1": 1.0,
            "member2": 2.0,
            "member3": 3.0,
        }
        
        result = await cache.zadd("test:zset", mapping)
        assert result == 3
        
        # 获取范围内的成员
        members = await cache.zrange("test:zset", 0, -1)
        assert len(members) == 3
        assert b"member1" in members
        assert b"member2" in members
        assert b"member3" in members

    @pytest.mark.asyncio
    async def test_zadd_with_ttl(self, cache_manager_with_fake_redis):
        """测试带 TTL 的 zadd 操作"""
        cache = cache_manager_with_fake_redis
        
        mapping = {"member1": 1.0}
        
        # 设置 TTL 为 1 秒
        result = await cache.zadd("test:zset:ttl", mapping, ttl=1)
        assert result == 1
        
        # 立即获取应该成功
        members = await cache.zrange("test:zset:ttl", 0, -1)
        assert len(members) == 1
        
        # 等待 TTL 过期
        await asyncio.sleep(1.1)
        
        # 过期后应该返回空列表
        expired = await cache.zrange("test:zset:ttl", 0, -1)
        assert len(expired) == 0

    @pytest.mark.asyncio
    async def test_zrange_with_scores(self, cache_manager_with_fake_redis):
        """测试带分数的 zrange 操作"""
        cache = cache_manager_with_fake_redis
        
        mapping = {
            "member1": 1.0,
            "member2": 2.0,
        }
        
        await cache.zadd("test:zset:scores", mapping)
        
        # 获取成员和分数
        members_with_scores = await cache.zrange("test:zset:scores", 0, -1, withscores=True)
        
        assert len(members_with_scores) == 2
        # fakeredis 返回格式是 [(member, score), ...]
        # 检查是否包含 member1
        members = [item[0] if isinstance(item, tuple) else item for item in members_with_scores]
        assert b"member1" in members or "member1" in str(members)


# ============================================================================
# TestCacheManagerConnectionFailure - 连接失败场景测试
# ============================================================================


class TestCacheManagerConnectionFailure:
    """CacheManager 连接失败场景测试"""

    @pytest.mark.asyncio
    async def test_operations_when_redis_unavailable(self, serializer):
        """测试 Redis 不可用时的操作"""
        cache = CacheManager()
        cache._available = False
        cache._redis = None
        
        test_data = {"test": "data"}
        serialized = serializer.serialize(test_data)
        
        # Get 操作应该返回 None
        result = await cache.get("test:key")
        assert result is None
        
        # Set 操作应该返回 False
        result = await cache.set("test:key", serialized)
        assert result is False
        
        # Delete 操作应该返回 False
        result = await cache.delete("test:key")
        assert result is False
        
        # Hget 操作应该返回 None
        result = await cache.hget("test:hash", "field")
        assert result is None
        
        # Hset 操作应该返回 False
        result = await cache.hset("test:hash", "field", serialized)
        assert result is False
        
        # Hgetall 操作应该返回空字典
        result = await cache.hgetall("test:hash")
        assert result == {}
        
        # Publish 操作应该返回 0
        result = await cache.publish("test:channel", serialized)
        assert result == 0
        
        # Zadd 操作应该返回 0
        result = await cache.zadd("test:zset", {"member": 1.0})
        assert result == 0
        
        # Zrange 操作应该返回空列表
        result = await cache.zrange("test:zset", 0, -1)
        assert result == []

    @pytest.mark.asyncio
    async def test_initialize_connection_failure(self):
        """测试 Redis 连接失败时的初始化"""
        cache = CacheManager()
        config = CacheConfig(
            enabled=True,
            host="invalid_host",
            port=9999,
            socket_connect_timeout=0.1,
        )
        
        # 模拟连接失败
        with patch('src.services.cache_manager.Redis') as mock_redis_class:
            mock_redis = AsyncMock()
            mock_redis.ping.side_effect = Exception("Connection failed")
            mock_redis_class.return_value = mock_redis
            
            with pytest.raises(Exception):
                await cache.initialize(config)
            
            assert cache.is_available() is False

    @pytest.mark.asyncio
    async def test_operation_timeout(self, cache_manager_with_fake_redis):
        """测试操作超时场景"""
        cache = cache_manager_with_fake_redis
        
        # 模拟超时
        with patch.object(cache._redis, 'get', side_effect=asyncio.TimeoutError()):
            with pytest.raises(asyncio.TimeoutError):
                await cache.get("test:key")
            
            # 超时后应该标记为不可用
            assert cache.is_available() is False


# ============================================================================
# TestCacheManagerHealthCheck - 健康检查测试
# ============================================================================


class TestCacheManagerHealthCheck:
    """CacheManager 健康检查测试"""

    @pytest.mark.asyncio
    async def test_health_check_success(self, cache_manager_with_fake_redis):
        """测试健康检查成功"""
        cache = cache_manager_with_fake_redis
        
        result = await cache.health_check()
        assert result is True
        assert cache.is_available() is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, cache_manager_with_fake_redis):
        """测试健康检查失败"""
        cache = cache_manager_with_fake_redis
        
        # 导入 RedisError
        from redis.exceptions import RedisError
        
        # 模拟 ping 失败 - 需要返回一个 awaitable 并抛出 RedisError
        async def mock_ping_failure():
            raise RedisError("Ping failed")
        
        with patch.object(cache._redis, 'ping', side_effect=mock_ping_failure):
            result = await cache.health_check()
            assert result is False
            assert cache.is_available() is False

    @pytest.mark.asyncio
    async def test_health_check_when_unavailable(self):
        """测试 Redis 不可用时的健康检查"""
        cache = CacheManager()
        cache._available = False
        cache._redis = None
        
        result = await cache.health_check()
        assert result is False

    @pytest.mark.asyncio
    async def test_health_check_recovery(self, cache_manager_with_fake_redis):
        """测试健康检查恢复"""
        cache = cache_manager_with_fake_redis
        
        # 确保 Redis 连接仍然有效
        assert cache._redis is not None
        
        # 先标记为不可用，但不影响 health_check 的逻辑
        # health_check 会在 _available 为 False 时直接返回 False
        # 所以我们需要测试从失败状态恢复的场景
        # 这里我们模拟一个场景：先让 ping 失败，然后恢复
        
        from redis.exceptions import RedisError
        
        # 第一次调用失败
        async def mock_ping_failure():
            raise RedisError("Ping failed")
        
        with patch.object(cache._redis, 'ping', side_effect=mock_ping_failure):
            result = await cache.health_check()
            assert result is False
            assert cache.is_available() is False
        
        # 第二次调用成功（不再 patch，使用真实的 fakeredis）
        # 但是由于 _available 已经是 False，health_check 会直接返回 False
        # 这是 CacheManager 的设计：一旦标记为不可用，需要重新初始化
        # 所以我们需要手动设置 _available 为 True 来模拟恢复
        cache._available = True
        result = await cache.health_check()
        assert result is True
        assert cache.is_available() is True


# ============================================================================
# 属性测试（Property-Based Testing）
# ============================================================================


@settings(max_examples=100)
@given(
    st.lists(
        st.tuples(
            st.text(min_size=1, max_size=50),  # key
            st.dictionaries(
                keys=st.text(min_size=1, max_size=20),
                values=st.one_of(
                    st.none(),
                    st.booleans(),
                    st.integers(min_value=-(2**63), max_value=2**63 - 1),
                    st.text(max_size=50),
                ),
                max_size=10,
            ),  # value
        ),
        min_size=1,
        max_size=10,
    )
)
@pytest.mark.asyncio
async def test_property_degradation_transparency(data):
    """
    **Feature: performance-optimization-phase1, Property 2: 降级透明性**
    
    属性测试：对于任何 Redis 操作失败，系统应该降级到直接查询 CTP API，
    且客户端不应感知到差异（不抛出异常，返回合理的默认值）
    
    验证需求：2.2, 10.1, 10.2
    """
    cache = CacheManager()
    cache._available = False
    cache._redis = None
    
    serializer = get_msgpack_serializer()
    
    # 测试所有操作在 Redis 不可用时都能优雅降级
    for key, value in data:
        serialized = serializer.serialize(value)
        
        # Get 操作应该返回 None（不抛出异常）
        result = await cache.get(key)
        assert result is None, f"Get 操作在 Redis 不可用时应返回 None，而不是抛出异常"
        
        # Set 操作应该返回 False（不抛出异常）
        result = await cache.set(key, serialized)
        assert result is False, f"Set 操作在 Redis 不可用时应返回 False，而不是抛出异常"
        
        # Delete 操作应该返回 False（不抛出异常）
        result = await cache.delete(key)
        assert result is False, f"Delete 操作在 Redis 不可用时应返回 False，而不是抛出异常"
        
        # Hash 操作
        result = await cache.hget(key, "field")
        assert result is None, f"Hget 操作在 Redis 不可用时应返回 None"
        
        result = await cache.hset(key, "field", serialized)
        assert result is False, f"Hset 操作在 Redis 不可用时应返回 False"
        
        result = await cache.hgetall(key)
        assert result == {}, f"Hgetall 操作在 Redis 不可用时应返回空字典"
        
        # Pub/Sub 操作
        result = await cache.publish(key, serialized)
        assert result == 0, f"Publish 操作在 Redis 不可用时应返回 0"
        
        # Sorted Set 操作
        result = await cache.zadd(key, {"member": 1.0})
        assert result == 0, f"Zadd 操作在 Redis 不可用时应返回 0"
        
        result = await cache.zrange(key, 0, -1)
        assert result == [], f"Zrange 操作在 Redis 不可用时应返回空列表"


@settings(max_examples=50)
@given(
    st.dictionaries(
        keys=st.text(min_size=1, max_size=50),
        values=st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.one_of(
                st.none(),
                st.booleans(),
                st.integers(min_value=-(2**63), max_value=2**63 - 1),
                st.text(max_size=50),
            ),
            max_size=5,
        ),
        min_size=1,
        max_size=5,
    )
)
@pytest.mark.asyncio
async def test_property_cache_consistency(data):
    """
    **Feature: performance-optimization-phase1, Property 1: 缓存一致性**
    
    属性测试：对于任何账户状态更新，当数据写入 Redis 缓存后，
    从缓存读取应该返回相同的数据
    
    验证需求：4.1, 4.2
    """
    # 创建 fakeredis 实例
    fake_server = fakeredis.FakeServer()
    fake_redis = fakeredis.aioredis.FakeRedis(server=fake_server, decode_responses=False)
    
    cache = CacheManager()
    cache._redis = fake_redis
    cache._available = True
    cache._config = CacheConfig(enabled=True)
    
    serializer = get_msgpack_serializer()
    
    try:
        # 测试所有数据的写入和读取一致性
        for key, value in data.items():
            serialized = serializer.serialize(value)
            
            # 写入缓存
            write_result = await cache.set(key, serialized)
            assert write_result is True, f"写入缓存失败: {key}"
            
            # 读取缓存
            read_result = await cache.get(key)
            assert read_result is not None, f"读取缓存失败: {key}"
            
            # 反序列化并验证一致性
            deserialized = serializer.deserialize(read_result)
            assert deserialized == value, f"缓存一致性验证失败: 原始={value}, 读取={deserialized}"
    finally:
        await cache.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
