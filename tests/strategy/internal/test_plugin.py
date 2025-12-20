#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : test_plugin.py
@Date       : 2025/12/20
@Author     : Kiro AI Assistant
@Email      : -
@Software   : PyCharm
@Description: 插件系统的单元测试
"""

import pytest
from unittest.mock import Mock
from src.strategy.internal.plugin import StrategyPlugin, PluginManager
from src.strategy.internal.data_models import Quote


class TestStrategyPlugin:
    """StrategyPlugin 抽象基类测试"""

    def test_cannot_instantiate_abstract_class(self):
        """测试不能直接实例化抽象基类"""
        with pytest.raises(TypeError):
            StrategyPlugin()

    def test_concrete_plugin_implementation(self):
        """测试具体插件实现"""
        class ConcretePlugin(StrategyPlugin):
            def on_init(self, api):
                self.api = api
        
        plugin = ConcretePlugin()
        mock_api = Mock()
        
        plugin.on_init(mock_api)
        assert plugin.api == mock_api

    def test_plugin_default_methods(self):
        """测试插件默认方法实现"""
        class MinimalPlugin(StrategyPlugin):
            def on_init(self, api):
                pass
        
        plugin = MinimalPlugin()
        mock_api = Mock()
        
        plugin.on_init(mock_api)
        
        # 默认方法应该返回原始数据
        quote = Quote(InstrumentID="rb2505", LastPrice=3500.0)
        assert plugin.on_quote(quote) == quote
        
        trade_data = {"test": "data"}
        assert plugin.on_trade(trade_data) == trade_data
        
        # on_stop 默认不做任何事
        plugin.on_stop()


class TestPluginManager:
    """PluginManager 类单元测试"""

    def test_initialization(self):
        """测试 PluginManager 初始化"""
        manager = PluginManager()
        
        assert manager._plugins == []
        assert manager._lock is not None

    def test_register_plugin(self):
        """测试注册插件"""
        class TestPlugin(StrategyPlugin):
            def __init__(self):
                self.initialized = False
            
            def on_init(self, api):
                self.initialized = True
                self.api = api
        
        manager = PluginManager()
        plugin = TestPlugin()
        mock_api = Mock()
        
        manager.register(plugin, mock_api)
        
        assert len(manager._plugins) == 1
        assert plugin.initialized is True
        assert plugin.api == mock_api

    def test_register_multiple_plugins(self):
        """测试注册多个插件"""
        class TestPlugin(StrategyPlugin):
            def on_init(self, api):
                pass
        
        manager = PluginManager()
        mock_api = Mock()
        
        plugin1 = TestPlugin()
        plugin2 = TestPlugin()
        plugin3 = TestPlugin()
        
        manager.register(plugin1, mock_api)
        manager.register(plugin2, mock_api)
        manager.register(plugin3, mock_api)
        
        assert len(manager._plugins) == 3

    def test_unregister_plugin(self):
        """测试注销插件"""
        class TestPlugin(StrategyPlugin):
            def __init__(self):
                self.stopped = False
            
            def on_init(self, api):
                pass
            
            def on_stop(self):
                self.stopped = True
        
        manager = PluginManager()
        plugin = TestPlugin()
        mock_api = Mock()
        
        manager.register(plugin, mock_api)
        assert len(manager._plugins) == 1
        
        manager.unregister(plugin)
        
        assert len(manager._plugins) == 0
        assert plugin.stopped is True

    def test_unregister_nonexistent_plugin(self):
        """测试注销不存在的插件不抛出异常"""
        class TestPlugin(StrategyPlugin):
            def on_init(self, api):
                pass
        
        manager = PluginManager()
        plugin = TestPlugin()
        
        # 应该不会抛出异常
        manager.unregister(plugin)

    def test_call_on_quote(self):
        """测试调用 on_quote 钩子"""
        class TestPlugin(StrategyPlugin):
            def on_init(self, api):
                pass
            
            def on_quote(self, quote):
                # 修改价格
                quote.LastPrice = quote.LastPrice + 1.0
                return quote
        
        manager = PluginManager()
        plugin = TestPlugin()
        mock_api = Mock()
        
        manager.register(plugin, mock_api)
        
        quote = Quote(InstrumentID="rb2505", LastPrice=3500.0)
        result = manager.call_on_quote(quote)
        
        assert result is not None
        assert result.LastPrice == 3501.0

    def test_call_on_quote_filter(self):
        """测试 on_quote 钩子过滤行情"""
        class FilterPlugin(StrategyPlugin):
            def on_init(self, api):
                pass
            
            def on_quote(self, quote):
                # 过滤掉价格低于 3500 的行情
                if quote.LastPrice < 3500.0:
                    return None
                return quote
        
        manager = PluginManager()
        plugin = FilterPlugin()
        mock_api = Mock()
        
        manager.register(plugin, mock_api)
        
        # 价格高于 3500，应该通过
        quote1 = Quote(InstrumentID="rb2505", LastPrice=3600.0)
        result1 = manager.call_on_quote(quote1)
        assert result1 is not None
        
        # 价格低于 3500，应该被过滤
        quote2 = Quote(InstrumentID="rb2505", LastPrice=3400.0)
        result2 = manager.call_on_quote(quote2)
        assert result2 is None

    def test_call_on_quote_chain(self):
        """测试多个插件的 on_quote 钩子链式调用"""
        class Plugin1(StrategyPlugin):
            def on_init(self, api):
                pass
            
            def on_quote(self, quote):
                quote.LastPrice = quote.LastPrice + 10.0
                return quote
        
        class Plugin2(StrategyPlugin):
            def on_init(self, api):
                pass
            
            def on_quote(self, quote):
                quote.LastPrice = quote.LastPrice * 2.0
                return quote
        
        manager = PluginManager()
        mock_api = Mock()
        
        plugin1 = Plugin1()
        plugin2 = Plugin2()
        
        manager.register(plugin1, mock_api)
        manager.register(plugin2, mock_api)
        
        quote = Quote(InstrumentID="rb2505", LastPrice=3500.0)
        result = manager.call_on_quote(quote)
        
        # (3500 + 10) * 2 = 7020
        assert result.LastPrice == 7020.0

    def test_call_on_quote_exception_handling(self):
        """测试 on_quote 钩子异常处理"""
        class BrokenPlugin(StrategyPlugin):
            def on_init(self, api):
                pass
            
            def on_quote(self, quote):
                raise Exception("插件错误")
        
        manager = PluginManager()
        plugin = BrokenPlugin()
        mock_api = Mock()
        
        manager.register(plugin, mock_api)
        
        quote = Quote(InstrumentID="rb2505", LastPrice=3500.0)
        
        # 应该捕获异常并返回原始数据
        result = manager.call_on_quote(quote)
        assert result == quote

    def test_call_on_trade(self):
        """测试调用 on_trade 钩子"""
        class TestPlugin(StrategyPlugin):
            def on_init(self, api):
                pass
            
            def on_trade(self, trade_data):
                trade_data['processed'] = True
                return trade_data
        
        manager = PluginManager()
        plugin = TestPlugin()
        mock_api = Mock()
        
        manager.register(plugin, mock_api)
        
        trade_data = {"order_id": "123", "price": 3500.0}
        result = manager.call_on_trade(trade_data)
        
        assert result is not None
        assert result['processed'] is True

    def test_call_on_trade_filter(self):
        """测试 on_trade 钩子过滤交易数据"""
        class FilterPlugin(StrategyPlugin):
            def on_init(self, api):
                pass
            
            def on_trade(self, trade_data):
                # 过滤掉价格低于 3500 的交易
                if trade_data.get('price', 0) < 3500.0:
                    return None
                return trade_data
        
        manager = PluginManager()
        plugin = FilterPlugin()
        mock_api = Mock()
        
        manager.register(plugin, mock_api)
        
        # 价格高于 3500，应该通过
        trade1 = {"order_id": "123", "price": 3600.0}
        result1 = manager.call_on_trade(trade1)
        assert result1 is not None
        
        # 价格低于 3500，应该被过滤
        trade2 = {"order_id": "124", "price": 3400.0}
        result2 = manager.call_on_trade(trade2)
        assert result2 is None

    def test_stop_all(self):
        """测试停止所有插件"""
        class TestPlugin(StrategyPlugin):
            def __init__(self):
                self.stopped = False
            
            def on_init(self, api):
                pass
            
            def on_stop(self):
                self.stopped = True
        
        manager = PluginManager()
        mock_api = Mock()
        
        plugin1 = TestPlugin()
        plugin2 = TestPlugin()
        plugin3 = TestPlugin()
        
        manager.register(plugin1, mock_api)
        manager.register(plugin2, mock_api)
        manager.register(plugin3, mock_api)
        
        manager.stop_all()
        
        assert len(manager._plugins) == 0
        assert plugin1.stopped is True
        assert plugin2.stopped is True
        assert plugin3.stopped is True

    def test_plugin_init_exception_handling(self):
        """测试插件初始化异常处理"""
        class BrokenPlugin(StrategyPlugin):
            def on_init(self, api):
                raise Exception("初始化失败")
        
        manager = PluginManager()
        plugin = BrokenPlugin()
        mock_api = Mock()
        
        # 应该捕获异常，插件仍然被注册
        manager.register(plugin, mock_api)
        
        assert len(manager._plugins) == 1

    def test_plugin_stop_exception_handling(self):
        """测试插件停止异常处理"""
        class BrokenPlugin(StrategyPlugin):
            def on_init(self, api):
                pass
            
            def on_stop(self):
                raise Exception("停止失败")
        
        manager = PluginManager()
        plugin = BrokenPlugin()
        mock_api = Mock()
        
        manager.register(plugin, mock_api)
        
        # 应该捕获异常，不抛出
        manager.unregister(plugin)
        
        assert len(manager._plugins) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
