#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : test_trade_report_triggers_position_update.py
@Date       : 2025/12/16
@Author     : Kiro AI Assistant
@Email      : -
@Software   : PyCharm
@Description: 测试成交回报触发持仓更新的功能
"""

import time
import threading
from unittest.mock import Mock, patch
import pytest
from src.strategy.sync_api import SyncStrategyApi


class TestTradeReportTriggersPositionUpdate:
    """测试成交回报触发持仓更新"""

    def test_trade_report_triggers_position_query(self):
        """
        测试：当收到成交回报时，应该自动触发持仓查询
        
        验证 Requirements 2.4: WHEN 持仓数据更新时 THEN SyncStrategyApi SHALL 自动更新内部缓存
        """
        api = SyncStrategyApi()
        
        # Mock _query_position_async 方法
        query_called = threading.Event()
        queried_instrument = []
        
        def mock_query_position_async(instrument_id: str):
            """记录查询调用"""
            queried_instrument.append(instrument_id)
            query_called.set()
        
        api._query_position_async = mock_query_position_async
        
        # 构造成交回报
        from src.constants.constant import TdConstant as Constant
        trade_response = {
            'msg_type': f'{Constant.OnRtnTrade}',  # 确保是字符串
            Constant.Trade: {
                'InstrumentID': 'rb2505',
                'Volume': 1,
                'Price': 3500.0,
                'Direction': '0',  # 买
                'OffsetFlag': '0'  # 开仓
            }
        }
        
        # 打印调试信息
        print(f"msg_type: {trade_response['msg_type']}")
        print(f"Constant.OnRtnTrade: {Constant.OnRtnTrade}")
        
        # 调用 _on_trade_data 处理成交回报
        api._on_trade_data(trade_response)
        
        # 等待查询被触发（最多等待 1 秒）
        query_called.wait(timeout=1.0)
        
        # 验证：应该触发了持仓查询
        assert query_called.is_set(), "收到成交回报后应该触发持仓查询"
        assert len(queried_instrument) == 1, "应该查询了一个合约"
        assert queried_instrument[0] == 'rb2505', f"应该查询 rb2505，实际查询: {queried_instrument[0]}"

    def test_trade_report_without_instrument_id(self):
        """测试：成交回报缺少合约代码时不触发查询"""
        api = SyncStrategyApi()
        
        # Mock _query_position_async 方法
        query_called = threading.Event()
        
        def mock_query_position_async(instrument_id: str):
            query_called.set()
        
        api._query_position_async = mock_query_position_async
        
        # 构造缺少 InstrumentID 的成交回报
        from src.constants.constant import TdConstant as Constant
        trade_response = {
            'msg_type': Constant.OnRtnTrade,
            Constant.Trade: {
                'Volume': 1,
                'Price': 3500.0
                # 缺少 InstrumentID
            }
        }
        
        # 调用 _on_trade_data 处理成交回报
        api._on_trade_data(trade_response)
        
        # 等待一小段时间
        time.sleep(0.1)
        
        # 验证：不应该触发查询
        assert not query_called.is_set(), "缺少合约代码时不应该触发持仓查询"

    def test_trade_report_with_empty_trade_data(self):
        """测试：成交回报数据为空时不触发查询"""
        api = SyncStrategyApi()
        
        # Mock _query_position_async 方法
        query_called = threading.Event()
        
        def mock_query_position_async(instrument_id: str):
            query_called.set()
        
        api._query_position_async = mock_query_position_async
        
        # 构造空的成交回报
        from src.constants.constant import TdConstant as Constant
        trade_response = {
            'msg_type': Constant.OnRtnTrade,
            Constant.Trade: None  # 空数据
        }
        
        # 调用 _on_trade_data 处理成交回报
        api._on_trade_data(trade_response)
        
        # 等待一小段时间
        time.sleep(0.1)
        
        # 验证：不应该触发查询
        assert not query_called.is_set(), "成交数据为空时不应该触发持仓查询"

    def test_multiple_trade_reports_trigger_multiple_queries(self):
        """测试：多个成交回报触发多次持仓查询"""
        api = SyncStrategyApi()
        
        # Mock _query_position_async 方法
        queried_instruments = []
        query_lock = threading.Lock()
        
        def mock_query_position_async(instrument_id: str):
            with query_lock:
                queried_instruments.append(instrument_id)
        
        api._query_position_async = mock_query_position_async
        
        # 构造多个成交回报
        from src.constants.constant import TdConstant as Constant
        instruments = ['rb2505', 'cu2506', 'au2512']
        
        for inst_id in instruments:
            trade_response = {
                'msg_type': Constant.OnRtnTrade,
                Constant.Trade: {
                    'InstrumentID': inst_id,
                    'Volume': 1,
                    'Price': 3500.0
                }
            }
            api._on_trade_data(trade_response)
        
        # 等待所有查询完成
        time.sleep(0.5)
        
        # 验证：应该触发了多次查询
        assert len(queried_instruments) == 3, f"应该查询了 3 个合约，实际: {len(queried_instruments)}"
        assert set(queried_instruments) == set(instruments), \
            f"查询的合约不匹配，期望: {instruments}, 实际: {queried_instruments}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
