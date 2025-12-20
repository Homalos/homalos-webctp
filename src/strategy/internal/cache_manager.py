#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : cache_manager.py
@Date       : 2025/12/19
@Author     : Kiro AI Assistant
@Email      : -
@Software   : PyCharm
@Description: 缓存管理器 - 提供线程安全的缓存管理功能

模块概述
========

本模块提供通用的缓存管理功能，包括基类 _CacheManager 和两个具体实现：
_QuoteCache（行情缓存）和 _PositionCache（持仓缓存）。

设计模式
========

本模块使用了以下设计模式：

1. **模板方法模式**
   - _CacheManager 定义了缓存管理的通用方法
   - 子类可以重写或扩展这些方法

2. **泛型编程**
   - 使用 Generic[T] 支持不同类型的缓存值
   - 提供类型安全的缓存操作

3. **线程安全**
   - 使用 threading.RLock 保护共享数据
   - 所有公共方法都是线程安全的

缓存管理器层次结构
==================

_CacheManager[T] (基类)
    ├── _QuoteCache (行情缓存)
    │   └── 添加行情更新通知机制
    └── _PositionCache (持仓缓存)
        └── 提供持仓数据缓存

使用示例
========

使用 _QuoteCache::

    cache = _QuoteCache()
    
    # 更新行情
    market_data = {'LastPrice': 3500.0, 'Volume': 1000}
    cache.update_from_market_data('rb2605', market_data)
    
    # 获取行情（非阻塞）
    quote = cache.get('rb2605')
    if quote:
        print(f"最新价: {quote.LastPrice}")
    
    # 等待行情更新（阻塞）
    try:
        quote = cache.wait_update('rb2605', timeout=5.0)
        print(f"收到新行情: {quote.LastPrice}")
    except TimeoutError:
        print("等待超时")

使用 _PositionCache::

    cache = _PositionCache()
    
    # 更新持仓
    position_data = {
        'pos_long': 10,
        'pos_long_today': 5,
        'open_price_long': 3500.0
    }
    cache.update_from_position_data('rb2605', position_data)
    
    # 获取持仓
    position = cache.get('rb2605')
    print(f"多头持仓: {position.pos_long}")

最佳实践
========

1. **缓存更新策略**
   - 行情缓存：每次收到行情推送时更新
   - 持仓缓存：成交回报后查询更新

2. **线程安全**
   - 所有缓存操作都是线程安全的
   - 不需要在外部加锁

3. **内存管理**
   - 定期清理不再使用的缓存
   - 使用 clear() 方法清空所有缓存

4. **性能优化**
   - get() 方法返回副本，避免并发修改
   - 锁持有时间最小化，提高并发性能

性能考虑
========

1. **锁竞争**
   - 使用 RLock 支持可重入
   - 在锁外创建对象副本，减少锁持有时间

2. **通知机制**
   - _QuoteCache 使用队列广播机制
   - 每个等待线程有独立的队列，避免竞争

3. **缓存大小**
   - 当前实现没有大小限制
   - 如果需要，可以添加 LRU 淘汰策略

线程安全保证
============

所有公共方法都使用 RLock 保护：
- get(): 读取缓存时加锁
- update(): 更新缓存时加锁
- clear(): 清空缓存时加锁
- wait_update(): 等待时不持有锁，避免阻塞其他线程
"""

import queue
import threading
from typing import Dict, Generic, List, Optional, TypeVar

from .data_models import Quote, Position

T = TypeVar('T')


class _CacheManager(Generic[T]):
    """
    缓存管理器基类
    
    提供线程安全的缓存管理功能，包括：
    - 数据存储和检索
    - 锁保护
    - 缓存清理
    
    使用泛型支持不同类型的缓存值。
    
    Type Parameters:
        T: 缓存值的类型
    
    Attributes:
        _cache: 缓存字典，键为字符串，值为类型 T
        _lock: 可重入锁，保护缓存字典的并发访问
    """
    
    def __init__(self):
        """初始化缓存管理器"""
        self._cache: Dict[str, T] = {}
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[T]:
        """
        获取缓存数据（线程安全）
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在则返回 None
            
        Example:
            >>> cache = _CacheManager[str]()
            >>> cache.update("key1", "value1")
            >>> cache.get("key1")
            'value1'
            >>> cache.get("nonexistent")
            None
        """
        with self._lock:
            return self._cache.get(key)
    
    def update(self, key: str, value: T) -> None:
        """
        更新缓存数据（线程安全）
        
        Args:
            key: 缓存键
            value: 缓存值
            
        Example:
            >>> cache = _CacheManager[int]()
            >>> cache.update("count", 42)
            >>> cache.get("count")
            42
        """
        with self._lock:
            self._cache[key] = value
    
    def clear(self) -> None:
        """
        清空所有缓存（线程安全）
        
        Example:
            >>> cache = _CacheManager[str]()
            >>> cache.update("key1", "value1")
            >>> cache.clear()
            >>> cache.get("key1")
            None
        """
        with self._lock:
            self._cache.clear()
    
    def keys(self) -> List[str]:
        """
        获取所有缓存键（线程安全）
        
        Returns:
            缓存键列表
            
        Example:
            >>> cache = _CacheManager[str]()
            >>> cache.update("key1", "value1")
            >>> cache.update("key2", "value2")
            >>> sorted(cache.keys())
            ['key1', 'key2']
        """
        with self._lock:
            return list(self._cache.keys())
    
    def __contains__(self, key: str) -> bool:
        """
        检查键是否存在（线程安全）
        
        Args:
            key: 缓存键
            
        Returns:
            True 表示键存在，False 表示不存在
            
        Example:
            >>> cache = _CacheManager[str]()
            >>> cache.update("key1", "value1")
            >>> "key1" in cache
            True
            >>> "key2" in cache
            False
        """
        with self._lock:
            return key in self._cache
    
    def __len__(self) -> int:
        """
        获取缓存大小（线程安全）
        
        Returns:
            缓存中的键值对数量
            
        Example:
            >>> cache = _CacheManager[str]()
            >>> len(cache)
            0
            >>> cache.update("key1", "value1")
            >>> len(cache)
            1
        """
        with self._lock:
            return len(self._cache)


class _QuoteCache(_CacheManager[Quote]):
    """
    行情缓存管理器
    
    继承自 _CacheManager，添加行情特定的功能：
    - 行情更新通知队列
    - 阻塞等待行情更新
    
    Attributes:
        _quote_queues: 行情通知队列字典，每个合约维护一个队列列表
    """
    
    def __init__(self):
        """初始化行情缓存管理器"""
        super().__init__()
        self._quote_queues: Dict[str, list] = {}
    
    def update_from_market_data(self, instrument_id: str, market_data: dict) -> None:
        """
        从行情数据更新缓存并通知所有等待该合约行情的线程
        
        Args:
            instrument_id: 合约代码
            market_data: 行情数据字典，包含 CTP 行情字段
            
        Example:
            >>> cache = _QuoteCache()
            >>> market_data = {'LastPrice': 3500.0, 'Volume': 1000}
            >>> cache.update_from_market_data('rb2605', market_data)
        """
        with self._lock:
            # 创建 Quote 对象
            quote = Quote(
                InstrumentID=instrument_id,
                LastPrice=market_data.get('LastPrice', float('nan')),
                BidPrice1=market_data.get('BidPrice1', float('nan')),
                BidVolume1=market_data.get('BidVolume1', 0),
                AskPrice1=market_data.get('AskPrice1', float('nan')),
                AskVolume1=market_data.get('AskVolume1', 0),
                Volume=market_data.get('Volume', 0),
                OpenInterest=market_data.get('OpenInterest', 0),
                UpdateTime=market_data.get('UpdateTime', ''),
                UpdateMillisec=market_data.get('UpdateMillisec', 0),
                ctp_datetime=market_data.get('ctp_datetime')
            )
            
            # 调用父类方法更新缓存
            super().update(instrument_id, quote)
            
            # 通知所有等待该合约行情的线程（广播机制）
            self._notify_waiters(instrument_id, quote)
    
    def get(self, instrument_id: str) -> Optional[Quote]:
        """
        获取行情快照（非阻塞）
        
        重写父类方法以返回 Quote 对象的副本，避免并发修改。
        
        Args:
            instrument_id: 合约代码
            
        Returns:
            Quote 对象副本，如果不存在则返回 None
            
        Example:
            >>> cache = _QuoteCache()
            >>> cache.update('rb2605', {'LastPrice': 3500.0})
            >>> quote = cache.get('rb2605')
            >>> quote.LastPrice
            3500.0
        """
        # 优化：先在锁内获取引用，然后在锁外创建副本，减少锁持有时间
        with self._lock:
            quote = self._cache.get(instrument_id)
            if quote is None:
                return None
            
            # 在锁内快速提取所有字段值
            instrument_id_val = quote.InstrumentID
            last_price = quote.LastPrice
            bid_price1 = quote.BidPrice1
            bid_volume1 = quote.BidVolume1
            ask_price1 = quote.AskPrice1
            ask_volume1 = quote.AskVolume1
            volume = quote.Volume
            open_interest = quote.OpenInterest
            update_time = quote.UpdateTime
            update_millisec = quote.UpdateMillisec
            ctp_datetime = quote.ctp_datetime
        
        # 在锁外创建副本对象，减少锁持有时间
        return Quote(
            InstrumentID=instrument_id_val,
            LastPrice=last_price,
            BidPrice1=bid_price1,
            BidVolume1=bid_volume1,
            AskPrice1=ask_price1,
            AskVolume1=ask_volume1,
            Volume=volume,
            OpenInterest=open_interest,
            UpdateTime=update_time,
            UpdateMillisec=update_millisec,
            ctp_datetime=ctp_datetime
        )
    
    def wait_update(self, instrument_id: str, timeout: Optional[float]) -> Quote:
        """
        阻塞等待行情更新
        
        Args:
            instrument_id: 合约代码
            timeout: 超时时间（秒），None 表示无限等待
            
        Returns:
            更新后的 Quote 对象
            
        Raises:
            TimeoutError: 等待超时时抛出
            
        Example:
            >>> cache = _QuoteCache()
            >>> # 在另一个线程中更新行情
            >>> quote = cache.wait_update('rb2605', timeout=5.0)
        """
        # 为当前等待线程创建独立的队列
        notify_queue: queue.Queue[Quote] = queue.Queue(maxsize=1)
        
        with self._lock:
            # 为该合约创建队列列表（如果不存在）
            if instrument_id not in self._quote_queues:
                self._quote_queues[instrument_id] = []
            
            # 将当前队列添加到列表中
            self._quote_queues[instrument_id].append(notify_queue)
        
        # 在锁外等待，避免阻塞其他线程
        try:
            quote = notify_queue.get(timeout=timeout)
            return quote
        except queue.Empty:
            raise TimeoutError(f"等待合约 {instrument_id} 行情更新超时（{timeout}秒）")
        finally:
            # 清理：从队列列表中移除当前队列
            with self._lock:
                if instrument_id in self._quote_queues:
                    try:
                        self._quote_queues[instrument_id].remove(notify_queue)
                        # 如果列表为空，删除该合约的条目
                        if not self._quote_queues[instrument_id]:
                            del self._quote_queues[instrument_id]
                    except ValueError:
                        # 队列已被移除，忽略
                        pass
    
    def _notify_waiters(self, instrument_id: str, quote: Quote) -> None:
        """
        通知所有等待该合约行情的线程（内部方法）
        
        Args:
            instrument_id: 合约代码
            quote: 行情对象
        """
        if instrument_id in self._quote_queues:
            # 遍历该合约的所有等待队列
            queue_list = self._quote_queues[instrument_id]
            for q in queue_list:
                try:
                    # 向每个队列发送行情数据副本
                    quote_copy = Quote(
                        InstrumentID=quote.InstrumentID,
                        LastPrice=quote.LastPrice,
                        BidPrice1=quote.BidPrice1,
                        BidVolume1=quote.BidVolume1,
                        AskPrice1=quote.AskPrice1,
                        AskVolume1=quote.AskVolume1,
                        Volume=quote.Volume,
                        OpenInterest=quote.OpenInterest,
                        UpdateTime=quote.UpdateTime,
                        UpdateMillisec=quote.UpdateMillisec,
                        ctp_datetime=quote.ctp_datetime
                    )
                    q.put_nowait(quote_copy)
                except queue.Full:
                    # 队列满时忽略，等待线程会超时
                    pass



class _PositionCache(_CacheManager[Position]):
    """
    持仓缓存管理器
    
    继承自 _CacheManager，提供持仓数据的缓存管理。
    
    与 _QuoteCache 不同，持仓缓存不需要通知机制，
    因为持仓数据的更新频率较低，通常通过主动查询获取。
    """
    
    def __init__(self):
        """初始化持仓缓存管理器"""
        super().__init__()
    
    def update_from_position_data(self, instrument_id: str, position_data: dict) -> None:
        """
        从持仓数据更新缓存
        
        Args:
            instrument_id: 合约代码
            position_data: 持仓数据字典，包含多空持仓信息
            
        Example:
            >>> cache = _PositionCache()
            >>> position_data = {
            ...     'pos_long': 10,
            ...     'pos_long_today': 5,
            ...     'open_price_long': 3500.0
            ... }
            >>> cache.update_from_position_data('rb2605', position_data)
        """
        with self._lock:
            # 创建 Position 对象
            position = Position(
                pos_long=position_data.get('pos_long', 0),
                pos_long_today=position_data.get('pos_long_today', 0),
                pos_long_his=position_data.get('pos_long_his', 0),
                open_price_long=position_data.get('open_price_long', float('nan')),
                pos_short=position_data.get('pos_short', 0),
                pos_short_today=position_data.get('pos_short_today', 0),
                pos_short_his=position_data.get('pos_short_his', 0),
                open_price_short=position_data.get('open_price_short', float('nan'))
            )
            
            # 调用父类方法更新缓存
            super().update(instrument_id, position)
    
    def get(self, instrument_id: str) -> Position:
        """
        获取持仓信息（非阻塞）
        
        重写父类方法以返回 Position 对象的副本，避免并发修改。
        如果持仓不存在，返回空持仓对象。
        
        Args:
            instrument_id: 合约代码
            
        Returns:
            Position 对象副本，如果不存在则返回空持仓对象
            
        Example:
            >>> cache = _PositionCache()
            >>> cache.update('rb2605', {'pos_long': 10})
            >>> position = cache.get('rb2605')
            >>> position.pos_long
            10
            >>> # 不存在的合约返回空持仓
            >>> empty_pos = cache.get('nonexistent')
            >>> empty_pos.pos_long
            0
        """
        # 优化：先在锁内获取引用，然后在锁外创建副本，减少锁持有时间
        with self._lock:
            position = self._cache.get(instrument_id)
            
            # 如果不存在，返回空持仓对象
            if position is None:
                return Position()
            
            # 在锁内快速提取所有字段值
            pos_long = position.pos_long
            pos_long_today = position.pos_long_today
            pos_long_his = position.pos_long_his
            open_price_long = position.open_price_long
            pos_short = position.pos_short
            pos_short_today = position.pos_short_today
            pos_short_his = position.pos_short_his
            open_price_short = position.open_price_short
        
        # 在锁外创建副本对象，减少锁持有时间
        return Position(
            pos_long=pos_long,
            pos_long_today=pos_long_today,
            pos_long_his=pos_long_his,
            open_price_long=open_price_long,
            pos_short=pos_short,
            pos_short_today=pos_short_today,
            pos_short_his=pos_short_his,
            open_price_short=open_price_short
        )
