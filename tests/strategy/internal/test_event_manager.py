#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : test_event_manager.py
@Date       : 2025/12/20
@Author     : Kiro AI Assistant
@Email      : -
@Software   : PyCharm
@Description: _EventManager 类的单元测试
"""

import time
import threading
import pytest
from src.strategy.internal.event_manager import _EventManager


class TestEventManager:
    """_EventManager 类单元测试"""

    def test_initialization(self):
        """测试 _EventManager 初始化"""
        manager = _EventManager()
        
        assert manager._events == {}
        assert manager._lock is not None
        assert manager.get_event_count() == 0

    def test_create_event(self):
        """测试创建事件"""
        manager = _EventManager()
        
        event = manager.create_event("test_event")
        
        assert event is not None
        assert isinstance(event, threading.Event)
        assert manager.get_event_count() == 1

    def test_create_event_idempotent(self):
        """测试重复创建同一事件返回相同对象"""
        manager = _EventManager()
        
        event1 = manager.create_event("test_event")
        event2 = manager.create_event("test_event")
        
        assert event1 is event2
        assert manager.get_event_count() == 1

    def test_set_event(self):
        """测试设置事件"""
        manager = _EventManager()
        
        event = manager.create_event("test_event")
        assert not event.is_set()
        
        manager.set_event("test_event")
        assert event.is_set()

    def test_set_nonexistent_event(self):
        """测试设置不存在的事件不抛出异常"""
        manager = _EventManager()
        
        # 应该不会抛出异常，只记录警告
        manager.set_event("nonexistent_event")

    def test_wait_event_success(self):
        """测试等待事件成功"""
        manager = _EventManager()
        event = manager.create_event("test_event")
        
        def setter():
            time.sleep(0.1)
            manager.set_event("test_event")
        
        thread = threading.Thread(target=setter)
        thread.start()
        
        result = manager.wait_event("test_event", timeout=1.0)
        
        assert result is True
        thread.join()

    def test_wait_event_timeout(self):
        """测试等待事件超时"""
        manager = _EventManager()
        manager.create_event("test_event")
        
        result = manager.wait_event("test_event", timeout=0.1)
        
        assert result is False

    def test_wait_nonexistent_event(self):
        """测试等待不存在的事件抛出异常"""
        manager = _EventManager()
        
        with pytest.raises(KeyError, match="事件不存在"):
            manager.wait_event("nonexistent_event", timeout=0.1)

    def test_clear_event(self):
        """测试清除事件"""
        manager = _EventManager()
        
        manager.create_event("test_event")
        assert manager.get_event_count() == 1
        
        manager.clear_event("test_event")
        assert manager.get_event_count() == 0

    def test_clear_nonexistent_event(self):
        """测试清除不存在的事件不抛出异常"""
        manager = _EventManager()
        
        # 应该不会抛出异常
        manager.clear_event("nonexistent_event")

    def test_clear_all(self):
        """测试清除所有事件"""
        manager = _EventManager()
        
        manager.create_event("event1")
        manager.create_event("event2")
        manager.create_event("event3")
        
        assert manager.get_event_count() == 3
        
        manager.clear_all()
        
        assert manager.get_event_count() == 0

    def test_concurrent_event_creation(self):
        """测试并发创建事件"""
        manager = _EventManager()
        exceptions = []
        
        def worker(event_id: str):
            try:
                event = manager.create_event(event_id)
                assert event is not None
            except Exception as e:
                exceptions.append(e)
        
        threads = []
        for i in range(10):
            thread = threading.Thread(target=worker, args=(f"event_{i}",))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        assert len(exceptions) == 0
        assert manager.get_event_count() == 10

    def test_concurrent_wait_and_set(self):
        """测试并发等待和设置事件"""
        manager = _EventManager()
        event_id = "test_event"
        manager.create_event(event_id)
        
        wait_results = []
        
        def waiter():
            result = manager.wait_event(event_id, timeout=2.0)
            wait_results.append(result)
        
        def setter():
            time.sleep(0.2)
            manager.set_event(event_id)
        
        # 启动多个等待线程
        wait_threads = []
        for _ in range(5):
            thread = threading.Thread(target=waiter)
            wait_threads.append(thread)
            thread.start()
        
        # 启动设置线程
        set_thread = threading.Thread(target=setter)
        set_thread.start()
        
        # 等待所有线程完成
        for thread in wait_threads:
            thread.join()
        set_thread.join()
        
        # 所有等待线程都应该成功
        assert len(wait_results) == 5
        assert all(result is True for result in wait_results)

    def test_event_lifecycle(self):
        """测试事件的完整生命周期"""
        manager = _EventManager()
        event_id = "lifecycle_event"
        
        # 创建
        event = manager.create_event(event_id)
        assert not event.is_set()
        assert manager.get_event_count() == 1
        
        # 设置
        manager.set_event(event_id)
        assert event.is_set()
        
        # 等待（应该立即返回）
        result = manager.wait_event(event_id, timeout=0.1)
        assert result is True
        
        # 清除
        manager.clear_event(event_id)
        assert manager.get_event_count() == 0

    def test_multiple_events_independence(self):
        """测试多个事件的独立性"""
        manager = _EventManager()
        
        event1 = manager.create_event("event1")
        event2 = manager.create_event("event2")
        
        # 设置 event1
        manager.set_event("event1")
        
        # event1 应该被设置，event2 不应该
        assert event1.is_set()
        assert not event2.is_set()
        
        # 等待 event1 应该立即返回
        result1 = manager.wait_event("event1", timeout=0.1)
        assert result1 is True
        
        # 等待 event2 应该超时
        result2 = manager.wait_event("event2", timeout=0.1)
        assert result2 is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
