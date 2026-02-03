#!/usr/bin/env python
"""
@ProjectName: homalos-webctp
@FileName   : event_manager.py
@Date       : 2025/12/20
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description:

    统一事件管理器 - 管理线程同步事件

    模块概述

    本模块提供统一的事件管理功能，用于管理各种线程同步事件。
    通过集中管理事件，消除了重复的事件管理代码模式，提高了代码的可维护性。

    事件管理器的作用

    在多线程环境中，经常需要在不同线程之间进行同步和通信。
    _EventManager 提供了一个统一的接口来管理这些同步事件：

    1. **事件创建和注册**
       - 为每个异步操作创建唯一的事件
       - 自动管理事件的生命周期

    2. **事件等待**
       - 支持超时等待
       - 在锁外等待，避免阻塞其他线程

    3. **事件触发**
       - 通知等待线程继续执行
       - 支持一对多通知

    4. **事件清理**
       - 自动清理不再使用的事件
       - 防止内存泄漏

    使用场景

    _EventManager 主要用于以下场景：

    1. **持仓查询同步**
       - 主线程发起查询请求
       - 等待 CTP 回调返回结果
       - 通过事件通知主线程继续

    2. **合约查询同步**
       - 查询合约信息
       - 等待查询响应
       - 通过事件通知查询完成

    3. **订单响应同步**
       - 提交订单请求
       - 等待订单响应
       - 通过事件通知订单结果

    4. **其他异步操作**
       - 任何需要线程同步的场景
       - 替代传统的 Event + 字典管理模式

    使用示例

    基本用法::

        event_manager = _EventManager()

        # 线程1：等待事件
        def worker_thread():
            event_manager.create_event("task_complete")
            if event_manager.wait_event("task_complete", timeout=5.0):
                print("任务完成")
            else:
                print("等待超时")
            event_manager.clear_event("task_complete")

        # 线程2：触发事件
        def trigger_thread():
            time.sleep(2)
            event_manager.set_event("task_complete")

    持仓查询示例::

        # 创建查询事件
        instrument_id = "rb2605"
        event_id = f"position_query_{instrument_id}"
        event_manager.create_event(event_id)

        try:
            # 发起查询请求
            submit_query_request(instrument_id)

            # 等待查询响应
            if event_manager.wait_event(event_id, timeout=5.0):
                # 查询成功，从缓存获取结果
                position = get_position_from_cache(instrument_id)
            else:
                # 查询超时
                raise TimeoutError("持仓查询超时")
        finally:
            # 清理事件
            event_manager.clear_event(event_id)

    订单响应示例::

        # 创建订单响应事件
        order_id = generate_order_id()
        event_id = f"order_response_{order_id}"
        event_manager.create_event(event_id)

        try:
            # 提交订单
            submit_order(order_id, instrument_id, action, volume, price)

            # 等待订单响应
            if event_manager.wait_event(event_id, timeout=10.0):
                # 订单响应已收到
                response = get_order_response(order_id)
                return response
            else:
                raise TimeoutError("订单响应超时")
        finally:
            event_manager.clear_event(event_id)

    最佳实践

    1. **事件命名规范**
       - 使用描述性的事件ID
       - 包含操作类型和标识符
       - 例如：position_query_rb2605, order_response_12345

    2. **及时清理事件**
       - 使用 try-finally 确保事件被清理
       - 避免事件泄漏导致内存增长

    3. **合理设置超时**
       - 根据操作类型设置合适的超时时间
       - 持仓查询：5秒
       - 订单响应：10秒
       - 合约查询：3秒

    4. **错误处理**
       - 捕获 KeyError（事件不存在）
       - 处理超时情况
       - 记录详细的日志

    5. **避免死锁**
       - wait_event() 在锁外等待
       - 不要在持有其他锁时等待事件

    线程安全保证

    _EventManager 的所有公共方法都是线程安全的：

    - create_event(): 使用锁保护事件字典
    - wait_event(): 在锁外等待，避免阻塞
    - set_event(): 使用锁保护事件访问
    - clear_event(): 使用锁保护事件删除
    - clear_all(): 使用锁保护批量清理

    性能考虑

    1. **锁粒度**
       - 使用 RLock 支持可重入
       - 锁持有时间最小化

    2. **等待机制**
       - 使用 threading.Event 的高效等待
       - 不使用轮询，避免 CPU 浪费

    3. **内存管理**
       - 及时清理不再使用的事件
       - 使用 clear_all() 批量清理

    与传统方法的对比

    传统方法（重复代码）::

        # 每个查询都需要管理自己的事件
        self._position_events = {}
        self._position_lock = threading.RLock()

        # 创建事件
        with self._position_lock:
            event = threading.Event()
            self._position_events[instrument_id] = event

        # 等待事件
        if not event.wait(timeout=5.0):
            raise TimeoutError()

        # 清理事件
        with self._position_lock:
            del self._position_events[instrument_id]

    使用 _EventManager（统一管理）::

        # 所有查询共享同一个事件管理器
        event_manager.create_event(f"position_query_{instrument_id}")

        if not event_manager.wait_event(f"position_query_{instrument_id}", timeout=5.0):
            raise TimeoutError()

        event_manager.clear_event(f"position_query_{instrument_id}")

    优势：
    - 代码更简洁
    - 消除重复
    - 统一的错误处理
    - 更好的可维护性
"""

import threading

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
        self._events: dict[str, threading.Event] = {}
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
            event_manager = _EventManager()
            event = event_manager.create_event("position_query_rb2605")
            使用事件进行线程同步
        """
        with self._lock:
            if event_id in self._events:
                logger.debug(f"事件已存在，返回现有事件: {event_id}")
                return self._events[event_id]

            event = threading.Event()
            self._events[event_id] = event
            logger.debug(f"创建新事件: {event_id}")
            return event

    def wait_event(self, event_id: str, timeout: float | None = None) -> bool:
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
            event_manager = _EventManager()
            event = event_manager.create_event("test_event")
            在另一个线程中等待
            if event_manager.wait_event("test_event", timeout=5.0):
                print("事件已触发")
            else:
                print("等待超时")
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
            event_manager = _EventManager()
            event = event_manager.create_event("test_event")
            在另一个线程中触发事件
            event_manager.set_event("test_event")
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
            event_manager = _EventManager()
            event = event_manager.create_event("test_event")
            使用完毕后清理
            event_manager.clear_event("test_event")
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
            event_manager = _EventManager()
            创建多个事件
            event_manager.create_event("event1")
            event_manager.create_event("event2")
            清理所有事件
            event_manager.clear_all()
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
__all__ = ["_EventManager"]
