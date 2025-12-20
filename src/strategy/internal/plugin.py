#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : plugin.py
@Date       : 2025/12/20
@Author     : Kiro AI Assistant
@Email      : -
@Software   : PyCharm
@Description: 策略插件系统 - 提供可扩展的插件架构

模块概述
========

本模块提供可扩展的插件系统，允许在不修改核心代码的情况下扩展 SyncStrategyApi 的功能。
插件系统基于钩子（Hook）机制，在特定事件发生时调用插件的回调方法。

插件系统的作用
==============

插件系统解决了以下问题：

1. **功能扩展**
   - 在不修改核心代码的情况下添加新功能
   - 遵循开闭原则（对扩展开放，对修改封闭）

2. **代码解耦**
   - 将特定功能从核心代码中分离
   - 提高代码的可维护性

3. **灵活配置**
   - 可以动态注册和注销插件
   - 支持插件的热插拔

4. **功能组合**
   - 多个插件可以链式调用
   - 实现复杂的数据处理流程

插件钩子
========

StrategyPlugin 定义了以下钩子方法：

1. **on_init(api)**
   - 插件初始化时调用
   - 可以保存 API 引用或初始化插件状态
   - 参数：SyncStrategyApi 实例

2. **on_quote(quote)**
   - 行情数据更新时调用
   - 可以修改或过滤行情数据
   - 参数：Quote 对象
   - 返回：处理后的 Quote 对象，或 None（过滤）

3. **on_trade(trade_data)**
   - 交易数据更新时调用
   - 可以修改或过滤交易数据
   - 参数：交易数据字典
   - 返回：处理后的字典，或 None（过滤）

4. **on_stop()**
   - API 停止时调用
   - 可以清理插件资源

使用示例
========

创建简单插件::

    from src.strategy.sync_api import StrategyPlugin
    
    class LoggingPlugin(StrategyPlugin):
        def on_init(self, api):
            self.api = api
            print("日志插件初始化")
        
        def on_quote(self, quote):
            print(f"[行情] {quote.InstrumentID} @ {quote.LastPrice}")
            return quote
        
        def on_trade(self, trade_data):
            msg_type = trade_data.get('MsgType', '')
            print(f"[交易] {msg_type}")
            return trade_data
        
        def on_stop(self):
            print("日志插件停止")

注册插件::

    api = SyncStrategyApi("user_id", "password")
    api.register_plugin(LoggingPlugin())

创建过滤插件::

    class PriceFilterPlugin(StrategyPlugin):
        def __init__(self, min_price, max_price):
            self.min_price = min_price
            self.max_price = max_price
        
        def on_init(self, api):
            print(f"价格过滤插件: {self.min_price} - {self.max_price}")
        
        def on_quote(self, quote):
            # 过滤异常价格
            if quote.LastPrice < self.min_price or quote.LastPrice > self.max_price:
                print(f"过滤异常价格: {quote.LastPrice}")
                return None  # 返回 None 表示过滤
            return quote
    
    # 使用插件
    api.register_plugin(PriceFilterPlugin(min_price=3000, max_price=4000))

创建风控插件::

    class RiskControlPlugin(StrategyPlugin):
        def __init__(self, max_position):
            self.max_position = max_position
            self.current_position = 0
        
        def on_init(self, api):
            self.api = api
            print(f"风控插件: 最大持仓 {self.max_position}")
        
        def on_trade(self, trade_data):
            # 检查成交回报
            if 'RtnTrade' in trade_data.get('MsgType', ''):
                trade = trade_data.get('Trade', {})
                direction = trade.get('Direction')
                volume = trade.get('Volume', 0)
                
                # 更新持仓
                if direction == '0':  # 买入
                    self.current_position += volume
                elif direction == '1':  # 卖出
                    self.current_position -= volume
                
                # 检查持仓限制
                if abs(self.current_position) > self.max_position:
                    print(f"警告：持仓超限 {self.current_position}")
            
            return trade_data
    
    api.register_plugin(RiskControlPlugin(max_position=100))

插件链式调用::

    # 注册多个插件
    api.register_plugin(LoggingPlugin())
    api.register_plugin(PriceFilterPlugin(3000, 4000))
    api.register_plugin(RiskControlPlugin(100))
    
    # 行情数据会依次经过所有插件
    # LoggingPlugin -> PriceFilterPlugin -> RiskControlPlugin

最佳实践
========

1. **插件设计原则**
   - 单一职责：每个插件只做一件事
   - 最小依赖：尽量不依赖其他插件
   - 快速返回：避免在钩子中执行耗时操作

2. **错误处理**
   - 插件异常会被自动捕获
   - 不会影响核心功能和其他插件
   - 异常会记录到日志

3. **状态管理**
   - 在 on_init() 中初始化状态
   - 在 on_stop() 中清理资源
   - 使用实例变量保存状态

4. **数据修改**
   - 可以修改数据但要谨慎
   - 返回 None 表示过滤数据
   - 不要修改原始对象，创建副本

5. **性能考虑**
   - 插件会在关键路径上执行
   - 避免复杂计算和 I/O 操作
   - 使用异步任务处理耗时操作

插件开发指南
============

1. **继承 StrategyPlugin**
   - 必须实现 on_init() 方法
   - 其他钩子方法可选

2. **保存 API 引用**
   - 在 on_init() 中保存 api 参数
   - 可以调用 API 的公共方法

3. **返回值规范**
   - on_quote(): 返回 Quote 对象或 None
   - on_trade(): 返回字典或 None
   - None 表示过滤该数据

4. **异常处理**
   - 插件内部应该处理异常
   - 未捕获的异常会被记录但不会中断

5. **线程安全**
   - 钩子方法在事件循环线程调用
   - 如果需要访问共享状态，使用锁

插件示例
========

完整的插件示例请参见：
- examples/plugins/logging_plugin.py - 日志记录插件
- examples/plugins/risk_control_plugin.py - 风控插件

更多插件开发指南请参见：
- examples/plugins/README.md - 插件开发详细文档

技术细节
========

1. **插件管理器**
   - PluginManager 负责插件的注册和调用
   - 使用 RLock 保证线程安全
   - 自动捕获插件异常

2. **钩子调用顺序**
   - 按注册顺序依次调用
   - 前一个插件的输出是下一个插件的输入
   - 任何插件返回 None 会中断链

3. **生命周期**
   - 注册时调用 on_init()
   - 运行时调用 on_quote() 和 on_trade()
   - 停止时调用 on_stop()
   - 注销时自动调用 on_stop()

4. **异常隔离**
   - 每个插件的异常独立处理
   - 不会影响其他插件
   - 不会影响核心功能

性能影响
========

插件会在关键路径上执行，对性能有一定影响：

1. **行情处理**
   - 每次行情更新都会调用 on_quote()
   - 插件数量和复杂度影响延迟

2. **交易处理**
   - 每次交易回调都会调用 on_trade()
   - 频繁的交易会增加开销

3. **优化建议**
   - 保持插件简单快速
   - 使用异步任务处理复杂逻辑
   - 避免在钩子中执行 I/O 操作

与传统方法的对比
================

传统方法（修改核心代码）::

    class SyncStrategyApi:
        def _on_market_data(self, response):
            # 处理行情
            quote = create_quote(response)
            
            # 添加日志（修改核心代码）
            print(f"收到行情: {quote.InstrumentID}")
            
            # 添加过滤（修改核心代码）
            if quote.LastPrice < 3000:
                return
            
            # 更新缓存
            self._quote_cache.update(quote)

使用插件系统::

    class SyncStrategyApi:
        def _on_market_data(self, response):
            # 处理行情
            quote = create_quote(response)
            
            # 调用插件（不修改核心代码）
            quote = self._plugin_manager.call_on_quote(quote)
            if quote is None:
                return
            
            # 更新缓存
            self._quote_cache.update(quote)
    
    # 功能通过插件实现
    api.register_plugin(LoggingPlugin())
    api.register_plugin(PriceFilterPlugin(3000, 4000))

优势：
- 核心代码保持简洁
- 功能可以独立开发和测试
- 支持动态配置
- 更好的可维护性
"""

import threading
from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from ..sync_api import SyncStrategyApi
    from .data_models import Quote


class StrategyPlugin(ABC):
    """
    策略插件抽象基类
    
    插件可以在特定事件发生时执行自定义逻辑,例如:
    - 行情数据预处理
    - 交易信号生成
    - 风险控制
    - 日志记录和监控
    
    使用示例:
        >>> class MyPlugin(StrategyPlugin):
        >>>     def on_init(self, api):
        >>>         self.api = api
        >>>         print("插件初始化")
        >>>     
        >>>     def on_quote(self, quote):
        >>>         print(f"收到行情: {quote.InstrumentID}")
        >>>         return quote
        >>> 
        >>> api = SyncStrategyApi(...)
        >>> api.register_plugin(MyPlugin())
    """
    
    @abstractmethod
    def on_init(self, api: 'SyncStrategyApi') -> None:
        """
        插件初始化钩子
        
        在插件注册时调用,可以保存 API 引用或初始化插件状态。
        
        Args:
            api: SyncStrategyApi 实例
        """
        pass
    
    def on_quote(self, quote: 'Quote') -> Optional['Quote']:
        """
        行情数据钩子
        
        在行情数据更新时调用,可以修改或过滤行情数据。
        
        Args:
            quote: 原始行情数据
            
        Returns:
            处理后的行情数据,返回 None 表示过滤该行情
        """
        return quote
    
    def on_trade(self, trade_data: dict) -> Optional[dict]:
        """
        交易数据钩子
        
        在交易数据更新时调用,可以修改或过滤交易数据。
        
        Args:
            trade_data: 原始交易数据
            
        Returns:
            处理后的交易数据,返回 None 表示过滤该数据
        """
        return trade_data
    
    def on_stop(self) -> None:
        """
        插件停止钩子
        
        在 API 停止时调用,可以清理插件资源。
        """
        pass


class PluginManager:
    """
    插件管理器
    
    负责插件的注册、注销和调用。
    
    特性:
    - 线程安全的插件管理
    - 自动异常捕获和日志记录
    - 支持插件链式调用
    """
    
    def __init__(self):
        """初始化插件管理器"""
        self._plugins: List[StrategyPlugin] = []
        self._lock = threading.RLock()
    
    def register(self, plugin: StrategyPlugin, api: 'SyncStrategyApi') -> None:
        """
        注册插件
        
        Args:
            plugin: 插件实例
            api: SyncStrategyApi 实例
        """
        with self._lock:
            self._plugins.append(plugin)
            try:
                plugin.on_init(api)
                logger.info(f"插件注册成功: {plugin.__class__.__name__}")
            except Exception as e:
                logger.error(f"插件初始化失败: {plugin.__class__.__name__}, 错误: {e}", exc_info=True)
    
    def unregister(self, plugin: StrategyPlugin) -> None:
        """
        注销插件
        
        Args:
            plugin: 插件实例
        """
        with self._lock:
            if plugin in self._plugins:
                self._plugins.remove(plugin)
                try:
                    plugin.on_stop()
                    logger.info(f"插件注销成功: {plugin.__class__.__name__}")
                except Exception as e:
                    logger.error(f"插件停止失败: {plugin.__class__.__name__}, 错误: {e}", exc_info=True)
    
    def call_on_quote(self, quote: 'Quote') -> Optional['Quote']:
        """
        调用所有插件的 on_quote 钩子
        
        Args:
            quote: 原始行情数据
            
        Returns:
            处理后的行情数据,如果被过滤则返回 None
        """
        with self._lock:
            result: Optional['Quote'] = quote
            for plugin in self._plugins:
                try:
                    result = plugin.on_quote(result) if result is not None else None
                    if result is None:
                        logger.debug(f"行情被插件过滤: {plugin.__class__.__name__}")
                        return None
                except Exception as e:
                    logger.error(f"插件 on_quote 失败: {plugin.__class__.__name__}, 错误: {e}", exc_info=True)
            return result
    
    def call_on_trade(self, trade_data: dict) -> Optional[dict]:
        """
        调用所有插件的 on_trade 钩子
        
        Args:
            trade_data: 原始交易数据
            
        Returns:
            处理后的交易数据,如果被过滤则返回 None
        """
        with self._lock:
            result: Optional[dict] = trade_data
            for plugin in self._plugins:
                try:
                    result = plugin.on_trade(result) if result is not None else None
                    if result is None:
                        logger.debug(f"交易数据被插件过滤: {plugin.__class__.__name__}")
                        return None
                except Exception as e:
                    logger.error(f"插件 on_trade 失败: {plugin.__class__.__name__}, 错误: {e}", exc_info=True)
            return result
    
    def stop_all(self) -> None:
        """停止所有插件"""
        with self._lock:
            for plugin in self._plugins:
                try:
                    plugin.on_stop()
                    logger.debug(f"插件已停止: {plugin.__class__.__name__}")
                except Exception as e:
                    logger.error(f"插件停止失败: {plugin.__class__.__name__}, 错误: {e}", exc_info=True)
            self._plugins.clear()
            logger.info("所有插件已停止")
