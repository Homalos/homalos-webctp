#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : event_manager.py
@Date       : 2025/12/20
@Author     : Kiro AI Assistant
@Email      : -
@Software   : PyCharm
@Description: 统一事件管理器 - 管理线程同步事件
"""

import threading
from typing import Dict, Optional

from loguru import logger


class _EventManager:
    """
    统一事件管理器（内部类）
    
    提供线程安全的事件管理功能，用于统一管理各种线程同步事件。
    消除了重复的事件管理代码模式。
    
    主要功能：
    - 事件创建和注册
    - 事件等待（带超时）
    - 事件设置和清理
    - 线程安全的事件字典管理
    
    使用场景：
    - 持仓查询事件管理
    - 合约查询事件管理
    - 订单响应事件管理
    - 其他需要线程同步的场景
    """
    
    def __init__(self):
        """初始化事件管理器"""
        self._events: Dict[str, threading.Event] = {}
        self._lock = threading.RLock()
        logger.debug("事件管理器已初始化")
    
    def create_event(self, event_id: str) -> threading.Event:
        """
        创建并注册事件
        
        如果事件已存在，返回现有事件对象。
        
        Args:
            event_id: 事件唯一标识符
            
        Returns:
            创建或已存在的事件对象
            
        Example:
            >>> event_manager = _EventManager()
            >>> event = event_manager.create_event("position_query_rb2605")
            >>> # 使用事件进行线程同步
        """
        with self._lock:
            if event_id in self._events:
                logger.debug(f"事件已存在，返回现有事件: {event_id}")
                return self._events[event_id]
            
            event = threading.Event()
            self._events[event_id] = event
            logger.debug(f"创建新事件: {event_id}")
            return event
    
    def wait_event(self, event_id: str, timeout: Optional[float] = None) -> bool:
        """
        等待事件触发
        
        该方法会阻塞当前线程，直到事件被设置或超时。
        
        Args:
            event_id: 事件唯一标识符
            timeout: 超时时间（秒），None 表示无限等待
            
        Returns:
            True 表示事件被触发，False 表示超时
            
        Raises:
            KeyError: 事件不存在时抛出
            
        Example:
            >>> event_manager = _EventManager()
            >>> event = event_manager.create_event("test_event")
            >>> # 在另一个线程中等待
            >>> if event_manager.wait_event("test_event", timeout=5.0):
            >>>     print("事件已触发")
            >>> else:
            >>>     print("等待超时")
        """
        with self._lock:
            if event_id not in self._events:
                raise KeyError(f"事件不存在: {event_id}")
            event = self._events[event_id]
        
        # 在锁外等待，避免阻塞其他线程
        timeout_str = f"{timeout}s" if timeout is not None else "无限等待"
        logger.debug(f"等待事件触发: {event_id}, 超时: {timeout_str}")
        
        result = event.wait(timeout=timeout)
        
        if result:
            logger.debug(f"事件已触发: {event_id}")
        else:
            logger.debug(f"等待事件超时: {event_id}")
        
        return result
    
    def set_event(self, event_id: str) -> None:
        """
        设置事件（触发等待线程）
        
        设置事件后，所有等待该事件的线程将被唤醒。
        如果事件不存在，该方法不会抛出异常，只记录警告日志。
        
        Args:
            event_id: 事件唯一标识符
            
        Example:
            >>> event_manager = _EventManager()
            >>> event = event_manager.create_event("test_event")
            >>> # 在另一个线程中触发事件
            >>> event_manager.set_event("test_event")
        """
        # 优化：使用 get() 代替 in 检查，减少字典查找次数
        with self._lock:
            event = self._events.get(event_id)
            if event is not None:
                event.set()
                logger.debug(f"事件已设置: {event_id}")
            else:
                logger.warning(f"尝试设置不存在的事件: {event_id}")
    
    def clear_event(self, event_id: str) -> None:
        """
        清除并删除事件
        
        该方法会从事件字典中删除事件对象。
        如果事件不存在，该方法不会抛出异常。
        
        Args:
            event_id: 事件唯一标识符
            
        Example:
            >>> event_manager = _EventManager()
            >>> event = event_manager.create_event("test_event")
            >>> # 使用完毕后清理
            >>> event_manager.clear_event("test_event")
        """
        # 优化：使用 pop() 代替 in + del，减少字典查找次数
        with self._lock:
            event = self._events.pop(event_id, None)
            if event is not None:
                logger.debug(f"事件已清除: {event_id}")
            else:
                logger.debug(f"尝试清除不存在的事件: {event_id}")
    
    def clear_all(self) -> None:
        """
        清除所有事件
        
        该方法通常在系统停止时调用，用于清理所有事件资源。
        
        Example:
            >>> event_manager = _EventManager()
            >>> # 创建多个事件
            >>> event_manager.create_event("event1")
            >>> event_manager.create_event("event2")
            >>> # 清理所有事件
            >>> event_manager.clear_all()
        """
        with self._lock:
            event_count = len(self._events)
            self._events.clear()
            logger.debug(f"已清除所有事件，共 {event_count} 个")
    
    def get_event_count(self) -> int:
        """
        获取当前事件数量
        
        Returns:
            当前注册的事件数量
        """
        with self._lock:
            return len(self._events)


# 导出公共接口
__all__ = ['_EventManager']
