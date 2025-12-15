#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : serialization.py
@Date       : 2025/12/12 00:00
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: 序列化模块 - 提供统一的序列化接口，支持多种格式
"""

import json
from abc import ABC, abstractmethod
from typing import Any

try:
    import orjson
    ORJSON_AVAILABLE = True
except ImportError:
    ORJSON_AVAILABLE = False

try:
    import msgpack
    MSGPACK_AVAILABLE = True
except ImportError:
    MSGPACK_AVAILABLE = False

from loguru import logger


class SerializationError(Exception):
    """序列化错误基类"""
    pass


class Serializer(ABC):
    """序列化器抽象基类"""

    @abstractmethod
    def serialize(self, obj: Any) -> bytes:
        """
        序列化对象为字节流

        Args:
            obj: 要序列化的对象

        Returns:
            bytes: 序列化后的字节流

        Raises:
            SerializationError: 序列化失败时抛出
        """
        pass

    @abstractmethod
    def deserialize(self, data: bytes) -> Any:
        """
        反序列化字节流为对象

        Args:
            data: 要反序列化的字节流

        Returns:
            Any: 反序列化后的对象

        Raises:
            SerializationError: 反序列化失败时抛出
        """
        pass


class OrjsonSerializer(Serializer):
    """
    orjson 序列化器（用于 WebSocket JSON）
    
    使用 orjson 库进行高性能 JSON 序列化，如果 orjson 不可用或失败，
    自动降级到标准 json 库。
    """

    def __init__(self):
        """初始化 OrjsonSerializer"""
        self._fallback_used = False
        self._metrics_collector = None
        if not ORJSON_AVAILABLE:
            logger.warning("orjson 不可用，将使用标准 json 库作为降级方案")
            self._fallback_used = True

    def set_metrics_collector(self, metrics_collector: Any) -> None:
        """
        设置性能指标收集器实例

        Args:
            metrics_collector: MetricsCollector 实例，用于收集性能指标
        """
        self._metrics_collector = metrics_collector

    def serialize(self, obj: Any) -> bytes:
        """
        序列化对象为 JSON 字节流

        Args:
            obj: 要序列化的对象

        Returns:
            bytes: JSON 格式的字节流

        Raises:
            SerializationError: 序列化失败时抛出
        """
        import time
        start_time = time.time()
        
        try:
            if ORJSON_AVAILABLE and not self._fallback_used:
                # 使用 orjson 进行序列化
                result = orjson.dumps(obj)
            else:
                # 降级到标准 json
                result = json.dumps(obj, ensure_ascii=False).encode('utf-8')
            
            # 记录序列化耗时
            if self._metrics_collector:
                latency_ms = (time.time() - start_time) * 1000
                self._metrics_collector.record_latency("serialization_json_encode", latency_ms)
            
            return result
        except (TypeError, ValueError, orjson.JSONEncodeError if ORJSON_AVAILABLE else Exception) as e:
            if ORJSON_AVAILABLE and not self._fallback_used:
                logger.warning(f"orjson 序列化失败，降级到标准 json: {e}")
                self._fallback_used = True
                try:
                    result = json.dumps(obj, ensure_ascii=False).encode('utf-8')
                    
                    # 记录序列化耗时
                    if self._metrics_collector:
                        latency_ms = (time.time() - start_time) * 1000
                        self._metrics_collector.record_latency("serialization_json_encode", latency_ms)
                    
                    return result
                except (TypeError, ValueError) as fallback_error:
                    raise SerializationError(f"JSON 序列化失败: {fallback_error}") from fallback_error
            else:
                raise SerializationError(f"JSON 序列化失败: {e}") from e

    def deserialize(self, data: bytes) -> Any:
        """
        反序列化 JSON 字节流为对象

        Args:
            data: JSON 格式的字节流

        Returns:
            Any: 反序列化后的对象

        Raises:
            SerializationError: 反序列化失败时抛出
        """
        import time
        start_time = time.time()
        
        try:
            if ORJSON_AVAILABLE and not self._fallback_used:
                # 使用 orjson 进行反序列化
                result = orjson.loads(data)
            else:
                # 降级到标准 json
                result = json.loads(data.decode('utf-8'))
            
            # 记录反序列化耗时
            if self._metrics_collector:
                latency_ms = (time.time() - start_time) * 1000
                self._metrics_collector.record_latency("serialization_json_decode", latency_ms)
            
            return result
        except (json.JSONDecodeError, orjson.JSONDecodeError if ORJSON_AVAILABLE else Exception, UnicodeDecodeError) as e:
            if ORJSON_AVAILABLE and not self._fallback_used:
                logger.warning(f"orjson 反序列化失败，降级到标准 json: {e}")
                self._fallback_used = True
                try:
                    result = json.loads(data.decode('utf-8'))
                    
                    # 记录反序列化耗时
                    if self._metrics_collector:
                        latency_ms = (time.time() - start_time) * 1000
                        self._metrics_collector.record_latency("serialization_json_decode", latency_ms)
                    
                    return result
                except (json.JSONDecodeError, UnicodeDecodeError) as fallback_error:
                    raise SerializationError(f"JSON 反序列化失败: {fallback_error}") from fallback_error
            else:
                raise SerializationError(f"JSON 反序列化失败: {e}") from e


class MsgpackSerializer(Serializer):
    """
    msgpack 序列化器（用于 Redis 存储）
    
    使用 msgpack 库进行高效的二进制序列化，适合 Redis 缓存存储。
    """

    def __init__(self):
        """初始化 MsgpackSerializer"""
        if not MSGPACK_AVAILABLE:
            raise ImportError("msgpack 库未安装，无法使用 MsgpackSerializer")
        self._metrics_collector = None

    def set_metrics_collector(self, metrics_collector: Any) -> None:
        """
        设置性能指标收集器实例

        Args:
            metrics_collector: MetricsCollector 实例，用于收集性能指标
        """
        self._metrics_collector = metrics_collector

    def serialize(self, obj: Any) -> bytes:
        """
        序列化对象为 msgpack 字节流

        Args:
            obj: 要序列化的对象

        Returns:
            bytes: msgpack 格式的字节流

        Raises:
            SerializationError: 序列化失败时抛出
        """
        import time
        start_time = time.time()
        
        try:
            result = msgpack.packb(obj, use_bin_type=True)
            
            # 记录序列化耗时
            if self._metrics_collector:
                latency_ms = (time.time() - start_time) * 1000
                self._metrics_collector.record_latency("serialization_msgpack_encode", latency_ms)
            
            return result
        except (TypeError, ValueError, msgpack.PackException) as e:
            raise SerializationError(f"msgpack 序列化失败: {e}") from e

    def deserialize(self, data: bytes) -> Any:
        """
        反序列化 msgpack 字节流为对象

        Args:
            data: msgpack 格式的字节流

        Returns:
            Any: 反序列化后的对象

        Raises:
            SerializationError: 反序列化失败时抛出
        """
        import time
        start_time = time.time()
        
        try:
            result = msgpack.unpackb(data, raw=False)
            
            # 记录反序列化耗时
            if self._metrics_collector:
                latency_ms = (time.time() - start_time) * 1000
                self._metrics_collector.record_latency("serialization_msgpack_decode", latency_ms)
            
            return result
        except (ValueError, msgpack.UnpackException) as e:
            raise SerializationError(f"msgpack 反序列化失败: {e}") from e


class SerializerFactory:
    """
    序列化器工厂类
    
    提供统一的接口来获取不同类型的序列化器实例。
    """

    _serializers = {}

    @staticmethod
    def get_serializer(format: str) -> Serializer:
        """
        获取指定格式的序列化器实例

        Args:
            format: 序列化格式，支持 'json' 和 'msgpack'

        Returns:
            Serializer: 对应格式的序列化器实例

        Raises:
            ValueError: 不支持的序列化格式时抛出
        """
        format = format.lower()

        # 使用单例模式，避免重复创建实例
        if format not in SerializerFactory._serializers:
            if format == 'json':
                SerializerFactory._serializers[format] = OrjsonSerializer()
            elif format == 'msgpack':
                SerializerFactory._serializers[format] = MsgpackSerializer()
            else:
                raise ValueError(f"不支持的序列化格式: {format}，支持的格式: json, msgpack")

        return SerializerFactory._serializers[format]

    @staticmethod
    def clear_cache():
        """清除序列化器缓存（主要用于测试）"""
        SerializerFactory._serializers.clear()


# 便捷函数
def get_json_serializer() -> OrjsonSerializer:
    """获取 JSON 序列化器实例"""
    return SerializerFactory.get_serializer('json')


def get_msgpack_serializer() -> MsgpackSerializer:
    """获取 msgpack 序列化器实例"""
    return SerializerFactory.get_serializer('msgpack')


if __name__ == "__main__":
    # 测试代码
    print("=== 测试 OrjsonSerializer ===")
    json_serializer = get_json_serializer()
    
    test_data = {
        "name": "测试",
        "value": 123,
        "nested": {"key": "value"},
        "list": [1, 2, 3]
    }
    
    serialized = json_serializer.serialize(test_data)
    print(f"序列化结果: {serialized}")
    
    deserialized = json_serializer.deserialize(serialized)
    print(f"反序列化结果: {deserialized}")
    print(f"数据一致: {test_data == deserialized}")
    
    print("\n=== 测试 MsgpackSerializer ===")
    msgpack_serializer = get_msgpack_serializer()
    
    serialized_msgpack = msgpack_serializer.serialize(test_data)
    print(f"序列化结果: {serialized_msgpack}")
    
    deserialized_msgpack = msgpack_serializer.deserialize(serialized_msgpack)
    print(f"反序列化结果: {deserialized_msgpack}")
    print(f"数据一致: {test_data == deserialized_msgpack}")
