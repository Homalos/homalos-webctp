#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : __init__.py
@Date       : 2025/12/19
@Author     : Kiro AI Assistant
@Email      : -
@Software   : PyCharm
@Description: SyncStrategyApi 内部模块包

包概述
======

本包包含 SyncStrategyApi 的所有内部组件，这些组件通过模块化重构从主文件中提取出来，
以提高代码的可维护性、可测试性和可扩展性。

内部模块说明
============

数据模型（data_models.py）
--------------------------
定义核心数据类：
- Quote: 行情快照数据类，包含最新价、买卖价、成交量等字段
- Position: 持仓信息数据类，包含多空持仓、今昨仓等信息

特点：
- 使用 @dataclass 装饰器，自动生成 __init__、__repr__ 等方法
- 支持属性访问和字典访问两种方式
- 无效价格使用 float('nan') 表示

缓存管理（cache_manager.py）
----------------------------
提供线程安全的缓存管理功能：
- _CacheManager: 通用缓存管理器基类，提供 get/update/clear 等方法
- _QuoteCache: 行情缓存，继承自 _CacheManager，添加行情更新通知机制
- _PositionCache: 持仓缓存，继承自 _CacheManager

特点：
- 使用 threading.RLock 保护共享数据
- 消除了重复的锁管理代码
- 支持泛型，类型安全

事件管理（event_manager.py）
----------------------------
统一管理线程同步事件：
- _EventManager: 事件管理器，提供事件创建、等待、设置、清理等功能

特点：
- 线程安全的事件字典管理
- 支持超时等待
- 自动清理不再使用的事件

事件循环（event_loop_thread.py）
--------------------------------
管理后台异步事件循环：
- _EventLoopThread: 在独立线程中运行 asyncio 事件循环
- 管理 MdClient 和 TdClient 的生命周期
- 提供同步/异步边界的桥接功能

特点：
- 使用 anyio 支持跨线程调用
- 自动处理 CTP 登录流程
- 监控服务可用性

插件系统（plugin.py）
---------------------
提供可扩展的插件架构：
- StrategyPlugin: 插件抽象基类，定义插件接口
- PluginManager: 插件管理器，负责插件注册、调用和生命周期管理

特点：
- 支持行情和交易数据钩子
- 自动异常捕获和日志记录
- 插件链式调用

辅助模块（order_helper.py, instrument_helper.py）
-------------------------------------------------
提供订单处理和合约信息处理的辅助函数：
- _OrderHelper: 订单参数映射、交易所识别等
- _InstrumentHelper: 合约信息查询、乘数获取等

模块依赖关系
============

依赖层次（从底层到顶层）::

    data_models.py (数据定义，无依赖)
         ↓
    cache_manager.py (依赖 data_models)
         ↓
    event_manager.py (独立模块，无依赖)
         ↓
    event_loop_thread.py (依赖 MdClient, TdClient)
         ↓
    plugin.py (依赖 data_models)
         ↓
    order_helper.py, instrument_helper.py (辅助模块)
         ↓
    sync_api.py (主模块，组合所有内部组件)

使用指南
========

内部模块仅供 SyncStrategyApi 内部使用，不应该被外部代码直接导入。
外部代码应该通过 SyncStrategyApi 的公共接口访问功能。

正确的使用方式::

    from src.strategy.sync_api import SyncStrategyApi, Quote, Position, StrategyPlugin
    
    # 使用公共接口
    api = SyncStrategyApi("user_id", "password")
    quote = api.get_quote("rb2605")

错误的使用方式::

    # 不要直接导入内部模块
    from src.strategy.internal.cache_manager import _QuoteCache  # 错误！
    from src.strategy.internal.event_manager import _EventManager  # 错误！

注意事项
========

1. 所有以下划线开头的类（如 _CacheManager、_EventManager）都是内部类，
   不应该被外部代码直接使用。

2. 内部模块的接口可能会在未来版本中变化，不保证向后兼容性。

3. 如果需要扩展功能，请使用插件系统（StrategyPlugin）而不是修改内部模块。

4. 内部模块的文档主要面向维护者和贡献者，策略开发者应该参考 SyncStrategyApi 的文档。
"""

# 导出数据模型
from .data_models import Quote, Position
# 导出缓存管理器（内部使用）
from .cache_manager import _CacheManager, _QuoteCache, _PositionCache
# 导出事件管理器（内部使用）
from .event_manager import _EventManager
# 导出事件循环线程（内部使用）
from .event_loop_thread import _EventLoopThread
# 导出插件系统
from .plugin import StrategyPlugin, PluginManager
# 导出辅助模块（内部使用）
from .order_helper import _OrderHelper
from .instrument_helper import _InstrumentHelper

__all__ = [
    'Quote', 
    'Position', 
    '_CacheManager', 
    '_QuoteCache', 
    '_PositionCache',
    '_EventManager',
    '_EventLoopThread',
    'StrategyPlugin',
    'PluginManager',
    '_OrderHelper',
    '_InstrumentHelper',
]
