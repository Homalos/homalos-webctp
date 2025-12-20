#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : test_data_models.py
@Date       : 2025/12/20
@Author     : Kiro AI Assistant
@Email      : -
@Software   : PyCharm
@Description: Quote 和 Position 数据类的单元测试
"""

import math
import pytest
from hypothesis import given, strategies as st, settings
from src.strategy.internal.data_models import Quote, Position


class TestQuote:
    """Quote 数据类单元测试"""

    @settings(max_examples=100)
    @given(
        st.fixed_dictionaries({
            'InstrumentID': st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Nd'))),
            'LastPrice': st.floats(min_value=0.01, max_value=100000.0, allow_nan=False, allow_infinity=False),
            'BidPrice1': st.floats(min_value=0.01, max_value=100000.0, allow_nan=False, allow_infinity=False),
            'BidVolume1': st.integers(min_value=0, max_value=1000000),
            'AskPrice1': st.floats(min_value=0.01, max_value=100000.0, allow_nan=False, allow_infinity=False),
            'AskVolume1': st.integers(min_value=0, max_value=1000000),
            'Volume': st.integers(min_value=0, max_value=10000000),
            'OpenInterest': st.floats(min_value=0.0, max_value=10000000.0, allow_nan=False, allow_infinity=False),
            'UpdateTime': st.text(min_size=0, max_size=20),
            'UpdateMillisec': st.integers(min_value=0, max_value=999)
        })
    )
    def test_property_dual_access_equivalence(self, quote_data):
        """
        **Feature: sync-strategy-api, Property 14: 数据对象双重访问**
        
        属性测试：对于任何 Quote 对象，应该同时支持属性访问（quote.LastPrice）
        和字典访问（quote["LastPrice"]），且两种方式返回相同的值。
        
        **Validates: Requirements 6.1, 6.2**
        """
        quote = Quote(
            InstrumentID=quote_data['InstrumentID'],
            LastPrice=quote_data['LastPrice'],
            BidPrice1=quote_data['BidPrice1'],
            BidVolume1=quote_data['BidVolume1'],
            AskPrice1=quote_data['AskPrice1'],
            AskVolume1=quote_data['AskVolume1'],
            Volume=quote_data['Volume'],
            OpenInterest=quote_data['OpenInterest'],
            UpdateTime=quote_data['UpdateTime'],
            UpdateMillisec=quote_data['UpdateMillisec']
        )
        
        fields_to_test = [
            'InstrumentID', 'LastPrice', 'BidPrice1', 'BidVolume1',
            'AskPrice1', 'AskVolume1', 'Volume', 'OpenInterest',
            'UpdateTime', 'UpdateMillisec'
        ]
        
        for field_name in fields_to_test:
            attr_value = getattr(quote, field_name)
            dict_value = quote[field_name]
            
            assert attr_value == dict_value, \
                f"字段 {field_name} 的属性访问和字典访问返回不同的值"
            
            assert attr_value == quote_data[field_name], \
                f"字段 {field_name} 的值与原始数据不一致"

    def test_quote_attribute_access(self, sample_quote_data):
        """测试 Quote 的属性访问方式"""
        quote = Quote(**sample_quote_data)
        
        assert quote.InstrumentID == sample_quote_data['InstrumentID']
        assert quote.LastPrice == sample_quote_data['LastPrice']
        assert quote.BidPrice1 == sample_quote_data['BidPrice1']
        assert quote.BidVolume1 == sample_quote_data['BidVolume1']
        assert quote.AskPrice1 == sample_quote_data['AskPrice1']
        assert quote.AskVolume1 == sample_quote_data['AskVolume1']
        assert quote.Volume == sample_quote_data['Volume']
        assert quote.OpenInterest == sample_quote_data['OpenInterest']
        assert quote.UpdateTime == sample_quote_data['UpdateTime']
        assert quote.UpdateMillisec == sample_quote_data['UpdateMillisec']

    def test_quote_dict_access(self, sample_quote_data):
        """测试 Quote 的字典访问方式"""
        quote = Quote(**sample_quote_data)
        
        assert quote["InstrumentID"] == sample_quote_data['InstrumentID']
        assert quote["LastPrice"] == sample_quote_data['LastPrice']
        assert quote["BidPrice1"] == sample_quote_data['BidPrice1']
        assert quote["BidVolume1"] == sample_quote_data['BidVolume1']
        assert quote["AskPrice1"] == sample_quote_data['AskPrice1']
        assert quote["AskVolume1"] == sample_quote_data['AskVolume1']

    def test_quote_attribute_and_dict_access_equivalence(self, sample_quote_data):
        """测试 Quote 的属性访问和字典访问返回相同值"""
        quote = Quote(**sample_quote_data)
        
        assert quote.InstrumentID == quote["InstrumentID"]
        assert quote.LastPrice == quote["LastPrice"]
        assert quote.BidPrice1 == quote["BidPrice1"]
        assert quote.BidVolume1 == quote["BidVolume1"]
        assert quote.AskPrice1 == quote["AskPrice1"]
        assert quote.AskVolume1 == quote["AskVolume1"]
        assert quote.Volume == quote["Volume"]
        assert quote.OpenInterest == quote["OpenInterest"]
        assert quote.UpdateTime == quote["UpdateTime"]

    def test_quote_invalid_price_nan(self):
        """测试 Quote 的无效价格使用 NaN 表示"""
        quote = Quote(InstrumentID="rb2505")
        
        assert math.isnan(quote.LastPrice)
        assert math.isnan(quote.BidPrice1)
        assert math.isnan(quote.AskPrice1)
        
        quote_with_nan = Quote(
            InstrumentID="rb2505",
            LastPrice=float('nan'),
            BidPrice1=float('nan'),
            AskPrice1=float('nan')
        )
        
        assert math.isnan(quote_with_nan.LastPrice)
        assert math.isnan(quote_with_nan.BidPrice1)
        assert math.isnan(quote_with_nan.AskPrice1)

    def test_quote_dict_access_invalid_key(self):
        """测试 Quote 字典访问不存在的键时抛出异常"""
        quote = Quote(InstrumentID="rb2505", LastPrice=3500.0)
        
        with pytest.raises(AttributeError):
            _ = quote["NonExistentField"]

    def test_quote_default_values(self):
        """测试 Quote 的默认值初始化"""
        quote = Quote()
        
        assert quote.InstrumentID == ""
        assert math.isnan(quote.LastPrice)
        assert math.isnan(quote.BidPrice1)
        assert quote.BidVolume1 == 0
        assert math.isnan(quote.AskPrice1)
        assert quote.AskVolume1 == 0
        assert quote.Volume == 0
        assert quote.OpenInterest == 0
        assert quote.UpdateTime == ""
        assert quote.UpdateMillisec == 0
        assert quote.ctp_datetime is None


class TestPosition:
    """Position 数据类单元测试"""

    def test_position_field_initialization(self, sample_position_data):
        """测试 Position 的字段初始化"""
        position = Position(**sample_position_data)
        
        assert position.pos_long == sample_position_data['pos_long']
        assert position.pos_long_today == sample_position_data['pos_long_today']
        assert position.pos_long_his == sample_position_data['pos_long_his']
        assert position.open_price_long == sample_position_data['open_price_long']
        assert position.pos_short == sample_position_data['pos_short']
        assert position.pos_short_today == sample_position_data['pos_short_today']
        assert position.pos_short_his == sample_position_data['pos_short_his']
        assert position.open_price_short == sample_position_data['open_price_short']

    def test_position_default_values(self):
        """测试 Position 的默认值"""
        position = Position()
        
        assert position.pos_long == 0
        assert position.pos_long_today == 0
        assert position.pos_long_his == 0
        assert math.isnan(position.open_price_long)
        assert position.pos_short == 0
        assert position.pos_short_today == 0
        assert position.pos_short_his == 0
        assert math.isnan(position.open_price_short)

    def test_position_custom_values(self):
        """测试 Position 的自定义值初始化"""
        position = Position(
            pos_long=20,
            pos_long_today=10,
            pos_long_his=10,
            open_price_long=3480.0
        )
        
        assert position.pos_long == 20
        assert position.pos_long_today == 10
        assert position.pos_long_his == 10
        assert position.open_price_long == 3480.0
        
        assert position.pos_short == 0
        assert position.pos_short_today == 0
        assert position.pos_short_his == 0
        assert math.isnan(position.open_price_short)

    def test_position_invalid_price_nan(self):
        """测试 Position 的开仓均价使用 NaN 表示无效价格"""
        position = Position()
        assert math.isnan(position.open_price_long)
        assert math.isnan(position.open_price_short)
        
        position_with_nan = Position(
            pos_long=10,
            open_price_long=float('nan'),
            pos_short=5,
            open_price_short=float('nan')
        )
        assert math.isnan(position_with_nan.open_price_long)
        assert math.isnan(position_with_nan.open_price_short)
        
        position_partial = Position(
            pos_long=10,
            open_price_long=3500.0,
            pos_short=5
        )
        assert position_partial.open_price_long == 3500.0
        assert math.isnan(position_partial.open_price_short)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
