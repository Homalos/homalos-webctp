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
