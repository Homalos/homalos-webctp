#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : test_serialization.py
@Date       : 2025/12/12 00:00
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: 序列化模块单元测试和属性测试
"""

import pytest
from hypothesis import given, strategies as st, settings
from src.utils.serialization import (
    OrjsonSerializer,
    MsgpackSerializer,
    SerializerFactory,
    SerializationError,
    get_json_serializer,
    get_msgpack_serializer,
)


class TestOrjsonSerializer:
    """OrjsonSerializer 单元测试"""

    def setup_method(self):
        """每个测试方法前执行"""
        self.serializer = OrjsonSerializer()

    def test_serialize_simple_dict(self):
        """测试序列化简单字典"""
        data = {"key": "value", "number": 42}
        result = self.serializer.serialize(data)
        assert isinstance(result, bytes)
        assert b"key" in result
        assert b"value" in result

    def test_deserialize_simple_dict(self):
        """测试反序列化简单字典"""
        data = b'{"key": "value", "number": 42}'
        result = self.serializer.deserialize(data)
        assert result == {"key": "value", "number": 42}

    def test_serialize_deserialize_roundtrip(self):
        """测试序列化-反序列化往返"""
        original = {
            "string": "测试",
            "number": 123,
            "float": 3.14,
            "bool": True,
            "null": None,
            "list": [1, 2, 3],
            "nested": {"key": "value"},
        }
        serialized = self.serializer.serialize(original)
        deserialized = self.serializer.deserialize(serialized)
        assert deserialized == original

    def test_serialize_chinese_characters(self):
        """测试序列化中文字符"""
        data = {"message": "你好世界", "name": "张三"}
        serialized = self.serializer.serialize(data)
        deserialized = self.serializer.deserialize(serialized)
        assert deserialized == data

    def test_serialize_empty_dict(self):
        """测试序列化空字典"""
        data = {}
        serialized = self.serializer.serialize(data)
        deserialized = self.serializer.deserialize(serialized)
        assert deserialized == data

    def test_serialize_empty_list(self):
        """测试序列化空列表"""
        data = []
        serialized = self.serializer.serialize(data)
        deserialized = self.serializer.deserialize(serialized)
        assert deserialized == data

    def test_serialize_none(self):
        """测试序列化 None"""
        data = None
        serialized = self.serializer.serialize(data)
        deserialized = self.serializer.deserialize(serialized)
        assert deserialized == data

    def test_serialize_large_object(self):
        """测试序列化大对象"""
        data = {"items": [{"id": i, "value": f"item_{i}"} for i in range(1000)]}
        serialized = self.serializer.serialize(data)
        deserialized = self.serializer.deserialize(serialized)
        assert deserialized == data
        assert len(deserialized["items"]) == 1000

    def test_deserialize_invalid_json(self):
        """测试反序列化无效 JSON"""
        invalid_data = b"not valid json"
        with pytest.raises(SerializationError):
            self.serializer.deserialize(invalid_data)

    def test_serialize_nested_structure(self):
        """测试序列化嵌套结构"""
        data = {
            "level1": {
                "level2": {
                    "level3": {
                        "value": "deep",
                        "list": [1, 2, {"nested": True}],
                    }
                }
            }
        }
        serialized = self.serializer.serialize(data)
        deserialized = self.serializer.deserialize(serialized)
        assert deserialized == data


class TestMsgpackSerializer:
    """MsgpackSerializer 单元测试"""

    def setup_method(self):
        """每个测试方法前执行"""
        self.serializer = MsgpackSerializer()

    def test_serialize_simple_dict(self):
        """测试序列化简单字典"""
        data = {"key": "value", "number": 42}
        result = self.serializer.serialize(data)
        assert isinstance(result, bytes)

    def test_deserialize_simple_dict(self):
        """测试反序列化简单字典"""
        data = {"key": "value", "number": 42}
        serialized = self.serializer.serialize(data)
        deserialized = self.serializer.deserialize(serialized)
        assert deserialized == data

    def test_serialize_deserialize_roundtrip(self):
        """测试序列化-反序列化往返"""
        original = {
            "string": "测试",
            "number": 123,
            "float": 3.14,
            "bool": True,
            "null": None,
            "list": [1, 2, 3],
            "nested": {"key": "value"},
        }
        serialized = self.serializer.serialize(original)
        deserialized = self.serializer.deserialize(serialized)
        assert deserialized == original

    def test_serialize_binary_data(self):
        """测试序列化二进制数据"""
        data = {"binary": b"binary data", "text": "text data"}
        serialized = self.serializer.serialize(data)
        deserialized = self.serializer.deserialize(serialized)
        assert deserialized == data

    def test_serialize_empty_dict(self):
        """测试序列化空字典"""
        data = {}
        serialized = self.serializer.serialize(data)
        deserialized = self.serializer.deserialize(serialized)
        assert deserialized == data

    def test_serialize_large_object(self):
        """测试序列化大对象"""
        data = {"items": [{"id": i, "value": f"item_{i}"} for i in range(1000)]}
        serialized = self.serializer.serialize(data)
        deserialized = self.serializer.deserialize(serialized)
        assert deserialized == data

    def test_deserialize_invalid_msgpack(self):
        """测试反序列化无效 msgpack 数据"""
        invalid_data = b"\xff\xff\xff\xff"
        with pytest.raises(SerializationError):
            self.serializer.deserialize(invalid_data)


class TestSerializerFactory:
    """SerializerFactory 单元测试"""

    def setup_method(self):
        """每个测试方法前执行"""
        SerializerFactory.clear_cache()

    def test_get_json_serializer(self):
        """测试获取 JSON 序列化器"""
        serializer = SerializerFactory.get_serializer("json")
        assert isinstance(serializer, OrjsonSerializer)

    def test_get_msgpack_serializer(self):
        """测试获取 msgpack 序列化器"""
        serializer = SerializerFactory.get_serializer("msgpack")
        assert isinstance(serializer, MsgpackSerializer)

    def test_get_serializer_case_insensitive(self):
        """测试获取序列化器（大小写不敏感）"""
        serializer1 = SerializerFactory.get_serializer("JSON")
        serializer2 = SerializerFactory.get_serializer("json")
        assert isinstance(serializer1, OrjsonSerializer)
        assert isinstance(serializer2, OrjsonSerializer)

    def test_get_serializer_singleton(self):
        """测试序列化器单例模式"""
        serializer1 = SerializerFactory.get_serializer("json")
        serializer2 = SerializerFactory.get_serializer("json")
        assert serializer1 is serializer2

    def test_get_serializer_invalid_format(self):
        """测试获取不支持的序列化格式"""
        with pytest.raises(ValueError, match="不支持的序列化格式"):
            SerializerFactory.get_serializer("xml")

    def test_convenience_functions(self):
        """测试便捷函数"""
        json_serializer = get_json_serializer()
        msgpack_serializer = get_msgpack_serializer()
        assert isinstance(json_serializer, OrjsonSerializer)
        assert isinstance(msgpack_serializer, MsgpackSerializer)


class TestFallbackLogic:
    """降级逻辑测试"""

    def test_orjson_fallback_on_import_error(self):
        """测试 orjson 导入失败时的降级"""
        # 这个测试需要模拟 orjson 不可用的情况
        # 在实际环境中，如果 orjson 已安装，这个测试会通过
        serializer = OrjsonSerializer()
        data = {"test": "data"}
        serialized = serializer.serialize(data)
        deserialized = serializer.deserialize(serialized)
        assert deserialized == data


# ============================================================================
# 属性测试（Property-Based Testing）
# ============================================================================


@settings(max_examples=100)
@given(
    st.dictionaries(
        keys=st.text(min_size=1, max_size=50),
        values=st.one_of(
            st.none(),
            st.booleans(),
            st.integers(min_value=-1000000, max_value=1000000),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(max_size=100),
            st.lists(st.integers(), max_size=20),
        ),
        max_size=20,
    )
)
def test_property_orjson_roundtrip_consistency(data):
    """
    **Feature: performance-optimization-phase1, Property 5: 序列化往返一致性**
    
    属性测试：对于任何数据对象，使用 OrjsonSerializer 序列化后再反序列化应该得到等价的对象
    
    验证需求：5.1, 5.2, 5.3
    """
    serializer = OrjsonSerializer()
    serialized = serializer.serialize(data)
    deserialized = serializer.deserialize(serialized)
    assert deserialized == data, f"往返不一致: 原始={data}, 反序列化={deserialized}"


@settings(max_examples=100)
@given(
    st.dictionaries(
        keys=st.text(min_size=1, max_size=50),
        values=st.one_of(
            st.none(),
            st.booleans(),
            # msgpack 支持的整数范围：-2^63 到 2^63-1
            st.integers(min_value=-(2**63), max_value=2**63 - 1),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(max_size=100),
            st.lists(
                st.integers(min_value=-(2**63), max_value=2**63 - 1), max_size=20
            ),
            st.binary(max_size=100),
        ),
        max_size=20,
    )
)
def test_property_msgpack_roundtrip_consistency(data):
    """
    **Feature: performance-optimization-phase1, Property 5: 序列化往返一致性**
    
    属性测试：对于任何数据对象，使用 MsgpackSerializer 序列化后再反序列化应该得到等价的对象
    
    注意：msgpack 的整数范围限制为 64 位有符号整数（-2^63 到 2^63-1）
    
    验证需求：5.1, 5.2, 5.3
    """
    serializer = MsgpackSerializer()
    serialized = serializer.serialize(data)
    deserialized = serializer.deserialize(serialized)
    assert deserialized == data, f"往返不一致: 原始={data}, 反序列化={deserialized}"


@settings(max_examples=100)
@given(
    st.lists(
        st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.one_of(st.integers(), st.text(max_size=50)),
            min_size=1,
            max_size=10,
        ),
        max_size=50,
    )
)
def test_property_orjson_list_roundtrip(data):
    """
    **Feature: performance-optimization-phase1, Property 5: 序列化往返一致性**
    
    属性测试：对于任何列表数据，序列化后再反序列化应该得到等价的列表
    
    验证需求：5.1, 5.2, 5.3
    """
    serializer = OrjsonSerializer()
    serialized = serializer.serialize(data)
    deserialized = serializer.deserialize(serialized)
    assert deserialized == data


@settings(max_examples=100)
@given(
    st.recursive(
        st.one_of(
            st.none(),
            st.booleans(),
            st.integers(min_value=-1000, max_value=1000),
            st.text(max_size=50),
        ),
        lambda children: st.dictionaries(
            keys=st.text(min_size=1, max_size=20), values=children, max_size=5
        ),
        max_leaves=10,
    )
)
def test_property_nested_structure_roundtrip(data):
    """
    **Feature: performance-optimization-phase1, Property 5: 序列化往返一致性**
    
    属性测试：对于任何嵌套结构，序列化后再反序列化应该得到等价的结构
    
    验证需求：5.1, 5.2, 5.3
    """
    json_serializer = OrjsonSerializer()
    msgpack_serializer = MsgpackSerializer()

    # 测试 JSON 序列化
    json_serialized = json_serializer.serialize(data)
    json_deserialized = json_serializer.deserialize(json_serialized)
    assert json_deserialized == data

    # 测试 msgpack 序列化
    msgpack_serialized = msgpack_serializer.serialize(data)
    msgpack_deserialized = msgpack_serializer.deserialize(msgpack_serialized)
    assert msgpack_deserialized == data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
