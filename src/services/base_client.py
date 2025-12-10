#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : base_client.py
@Date       : 2025/12/3 14:18
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: 客户端基类 (抽象类)
"""
import logging
import uuid
from abc import ABC, abstractmethod
from queue import Queue, Empty
from typing import Callable, Any, Awaitable

import anyio
from anyio.abc import TaskGroup


class BaseClient(ABC):
    """
    BaseClient 是 websocket 和客户端的边界，也是异步代码和同步代码的边界。它负责控制 CTP 客户端的状态。
    """

    def __init__(self) -> None:
        self._rsp_callback: Callable[[dict[str, Any]], Awaitable[None]] | None = None
        self._task_group: TaskGroup | None = None
        self._running: bool = False
        self._queue: Queue = Queue()
        self._client: Any = None
        self._client_lock: anyio.Lock = anyio.Lock()
        self._stop_event: anyio.Event | None = None
        self._call_map: dict[str, Callable[[dict[str, Any]], int]] = {}

    @property
    def rsp_callback(self) -> Callable[[dict[str, Any]], Awaitable[None]] | None:
        """
        获取响应回调函数

        Returns:
            Callable[[dict[str, Any]], Awaitable[None]] | None: 响应回调函数，接收一个字典参数并返回None
        """
        return self._rsp_callback

    @rsp_callback.setter
    def rsp_callback(self, callback: Callable[[dict[str, Any]], Awaitable[None]] | None) -> None:
        """
        设置响应回调函数

        Args:
            callback: 响应回调函数，接收一个字典参数并返回None
        """
        self._rsp_callback = callback

    @property
    def task_group(self) -> TaskGroup | None:
        """获取异步任务组实例

        Returns:
            TaskGroup | None: 用于管理异步任务的TaskGroup对象
        """
        return self._task_group

    @task_group.setter
    def task_group(self, task_group: TaskGroup | None) -> None:
        """设置异步任务组实例

        Args:
            task_group (TaskGroup): 用于管理异步任务的TaskGroup对象
        """
        self._task_group = task_group

    def on_rsp_or_rtn(self, data: dict[str, Any]) -> None:
        """处理来自CTP客户端的响应或返回数据

        Args:
            data: 包含响应或返回数据的字典，格式为{字段名: 字段值}

        Returns:
            None: 该方法无返回值
        """
        self._queue.put_nowait(data)

    async def start(self, user_id: str, password: str) -> None:
        """
        启动CTP客户端并使用用户凭据进行认证

        该方法负责初始化CTP客户端并建立连接。通过锁机制确保客户端只被创建一次，
        避免重复启动导致的竞态条件。

        NOTE: 这个if条件语句避免以下场景：
        1. 启动后台协程
        2. 开始登录
        3. 登录失败
        4. 再次尝试登录

        Args:
            user_id: 用户ID，用于CTP系统认证
            password: 用户密码，用于CTP系统认证

        Returns:
            None: 该方法没有返回值，但会异步建立客户端连接
        """
        async with self._client_lock:
            if not self._client:
                self._client = await anyio.to_thread.run_sync(
                    self._create_ctp_client, user_id, password
                )
                self._client.rsp_callback = self.on_rsp_or_rtn
                self._init_call_map()
                if not self._task_group:
                    raise RuntimeError("Task group is not set")
                # Use UUID to generate unique task name for better tracking and security
                task_name = f"{uuid.uuid4().hex[:8]}-{self._get_client_type()}-bg-task"
                self._task_group.start_soon(self.run, name=task_name)
            assert self._client is not None
            await anyio.to_thread.run_sync(self._client.connect)

    async def stop(self) -> None:
        """
        停止客户端运行

        异步停止客户端的所有活动，包括：
        - 设置运行状态为False
        - 等待停止事件完成（如果存在）
        - 释放客户端资源

        该方法会确保客户端优雅关闭，不会立即中断正在进行的操作。
        """
        logging.debug(f"stopping {self._get_client_type()} client")
        self._running = False
        if self._stop_event:
            await self._stop_event.wait()
            self._stop_event = None

        if self._client:
            await anyio.to_thread.run_sync(self._client.release)
        logging.debug(f"{self._get_client_type()} client stopped")

    async def run(self) -> None:
        """
        运行客户端协程的主循环

        该方法启动客户端的消息处理循环，持续从队列中获取并处理消息，直到客户端被停止。
        运行期间会设置停止事件和运行状态标志，确保优雅的启动和停止过程。

        Returns:
            None: 此方法不返回值
        """
        logging.info(f"start to run new {self._get_client_type()} coroutine")
        self._stop_event = anyio.Event()
        self._running = True
        while self._running:
            await self._process_a_message(1.0)
        logging.info(f"stop running {self._get_client_type()} coroutine")
        self._stop_event.set()

    async def _process_a_message(self, wait_time: float):
        """
        处理队列中的消息

        从消息队列中获取消息并调用响应回调函数进行处理。支持超时和取消操作。

        Args:
            wait_time: 等待消息的超时时间（秒）

        Raises:
            Exception: 处理消息过程中出现异常时记录日志，但不向上抛出
        """
        try:
            rsp = await anyio.to_thread.run_sync(
                self._queue.get, True, wait_time, cancellable=True
            )
            if self.rsp_callback:
                await self.rsp_callback(rsp)
        except Empty:
            pass
        except Exception as e:
            logging.exception(f"Exception in {self._get_client_type()} client: {e}")

    @abstractmethod
    def _create_ctp_client(self, user_id: str, password: str) -> Any:
        """创建特定的CTP客户端实例(Td或Md)

        Args:
            user_id: 用户ID，用于CTP登录
            password: 用户密码，用于CTP登录

        Returns:
            返回创建的CTP客户端实例(Td或Md)
        """
        pass

    @abstractmethod
    def _init_call_map(self):
        """
        初始化调用映射字典

        该方法应在子类中实现，用于初始化_call_map字典，将特定的请求类型字符串
        映射到对应的CTP客户端方法。

        注意：
        - 该方法在客户端启动时自动调用
        - 需要在具体的客户端子类（如MdClient、TdClient）中实现具体的映射逻辑
        """
        pass

    @abstractmethod
    def _get_client_type(self) -> str:
        """
        获取客户端类型标识字符串

        此抽象方法需要由具体子类实现，返回代表客户端类型的简短字符串标识。
        主要用于日志记录、任务命名和调试信息中区分不同类型的客户端。

        Returns:
            str: 客户端类型标识字符串，如 "md" 表示行情客户端，"td" 表示交易客户端
        """
        pass
