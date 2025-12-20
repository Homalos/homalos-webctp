#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : event_loop_thread.py
@Date       : 2025/12/20
@Author     : Kiro AI Assistant
@Email      : -
@Software   : PyCharm
@Description: 事件循环线程模块 - 管理后台异步事件循环
"""

import threading
from typing import Any, Optional, Callable

import anyio
import anyio.from_thread
import anyio.lowlevel
from loguru import logger


class _EventLoopThread:
    """
    后台事件循环线程（内部类）
    
    在独立线程中运行 asyncio 事件循环，负责管理异步的 MdClient 和 TdClient。
    提供同步/异步边界的桥接功能。
    
    Attributes:
        _anyio_token: anyio 跨线程调用 token
        _thread: 事件循环线程对象
        _md_client: MdClient 实例
        _td_client: TdClient 实例
        _running: 线程运行状态标志
        _clients_ready: 客户端是否已就绪
        _ready_event: 就绪事件，用于通知客户端初始化完成
        _init_error: 初始化错误（如果有）
        _service_available: 服务可用性标记
        _login_event: 登录完成事件
        _login_error: 登录错误（如果有）
        _md_logged_in: MdClient 登录状态
        _td_logged_in: TdClient 登录状态
        _md_callback: 行情数据回调函数
        _td_callback: 交易数据回调函数
        _client_stop_event: 客户端停止事件
    """
    
    def __init__(self) -> None:
        """初始化事件循环线程"""
        self._anyio_token: Optional[Any] = None  # anyio 跨线程调用 token
        self._thread: Optional[threading.Thread] = None
        self._md_client: Optional[Any] = None  # MdClient 实例
        self._td_client: Optional[Any] = None  # TdClient 实例
        self._running: bool = False
        self._clients_ready: bool = False  # 客户端是否已就绪
        self._ready_event: threading.Event = threading.Event()
        self._init_error: Optional[Exception] = None  # 初始化错误
        self._service_available: bool = True  # 服务可用性标记
        # 登录状态跟踪
        self._login_event: threading.Event = threading.Event()
        self._login_error: Optional[Exception] = None
        self._md_logged_in: bool = False
        self._td_logged_in: bool = False
        
    def start(
        self, 
        user_id: str, 
        password: str, 
        config_path: Optional[str] = None,
        md_callback: Optional[Callable] = None,
        td_callback: Optional[Callable] = None
    ) -> None:
        """
        启动事件循环线程并初始化 CTP 客户端
        
        Args:
            user_id: CTP 用户 ID
            password: CTP 密码
            config_path: 配置文件路径（可选）
            md_callback: 行情数据回调函数（可选）
            td_callback: 交易数据回调函数（可选）
            
        Raises:
            RuntimeError: 如果线程已经在运行
        """
        if self._running:
            raise RuntimeError("事件循环线程已经在运行")
        
        logger.info("启动后台事件循环线程...")
        
        # 保存回调函数
        self._md_callback = md_callback
        self._td_callback = td_callback
        
        # 创建并启动事件循环线程
        self._thread = threading.Thread(
            target=self._run_event_loop,
            args=(user_id, password, config_path),
            daemon=True,
            name="EventLoopThread"
        )
        self._running = True
        self._thread.start()
        
        logger.info("后台事件循环线程已启动")
    
    def _run_event_loop(self, user_id: str, password: str, config_path: Optional[str]) -> None:
        """
        在独立线程中运行事件循环（内部方法）
        
        使用 anyio 运行事件循环，以支持 task group。
        
        Args:
            user_id: CTP 用户 ID
            password: CTP 密码
            config_path: 配置文件路径
        """
        try:
            logger.debug("使用 anyio 创建事件循环，开始初始化 CTP 客户端...")
            
            # 使用 anyio.run() 运行异步代码
            # 这会创建一个新的事件循环并运行直到完成
            anyio.run(
                self._initialize_clients_with_taskgroup,
                user_id,
                password,
                config_path,
                backend="asyncio"  # 使用 asyncio 后端
            )
            
            logger.info("事件循环正常退出")
            
        except Exception as e:
            logger.error(f"事件循环线程异常: {e}", exc_info=True)
            self._init_error = e  # 保存错误
            self._service_available = False  # 标记服务不可用
            self._ready_event.set()  # 设置事件，让 wait_ready 可以检查错误
            logger.error("事件循环异常，服务已标记为不可用")
        finally:
            logger.info("事件循环线程已退出")
    
    def _on_login_response(self, response: dict) -> None:
        """
        处理登录响应（在事件循环线程中调用）
        
        监听 MdClient 和 TdClient 的登录响应，当两个客户端都登录成功后
        设置 _login_event 事件，通知 wait_ready() 方法可以继续。
        
        Args:
            response: 登录响应字典，包含 MsgType、RspInfo 和 _ClientType 等字段
        """
        # 注意：字段名是 "MsgType" 而不是 "msg_type"
        msg_type = response.get('MsgType', '')
        
        logger.debug(f"收到响应，MsgType: {msg_type}")
        
        # 检查是否是登录响应（修复：使用 'RspUserLogin' 而不是 'OnRspUserLogin'）
        if 'RspUserLogin' not in msg_type:
            return
        
        logger.info(f"检测到登录响应: {msg_type}")
        
        # 检查响应信息
        rsp_info = response.get('RspInfo', {})
        if rsp_info is None:
            rsp_info = {}
        error_id = rsp_info.get('ErrorID', 0)
        
        if error_id != 0:
            # 登录失败
            error_msg = rsp_info.get('ErrorMsg', '未知错误')
            self._login_error = RuntimeError(f"CTP 登录失败: [{error_id}] {error_msg}")
            logger.error(f"登录失败: {error_msg}")
            self._login_event.set()
        else:
            # 登录成功
            # 使用 _ClientType 字段判断是哪个客户端登录成功
            client_type = response.get('_ClientType', '')
            if client_type == 'Md':
                self._md_logged_in = True
                logger.info(f"MdClient 登录成功，已登录状态: Md={self._md_logged_in}, Td={self._td_logged_in}")
            elif client_type == 'Td':
                self._td_logged_in = True
                logger.info(f"TdClient 登录成功，已登录状态: Md={self._md_logged_in}, Td={self._td_logged_in}")
            
            # 两个客户端都登录成功后设置事件
            if self._md_logged_in and self._td_logged_in:
                logger.info("所有 CTP 客户端登录完成，设置登录事件")
                self._login_event.set()
    
    async def _initialize_clients_with_taskgroup(
        self, 
        user_id: str, 
        password: str, 
        config_path: Optional[str]
    ) -> None:
        """
        在 task group 上下文中初始化并运行 MdClient 和 TdClient（异步方法）
        
        这个方法会一直运行，直到收到停止信号。
        
        Args:
            user_id: CTP 用户 ID
            password: CTP 密码
            config_path: 配置文件路径
        """
        try:
            # 导入服务层的客户端类
            from ...services.md_client import MdClient
            from ...services.td_client import TdClient
            
            # 获取 anyio token 用于跨线程调用
            self._anyio_token = anyio.lowlevel.current_token()
            logger.debug("已获取 anyio token")
            
            # 配置已在 SyncStrategyApi.__init__() 中加载，此处不需要重复加载
            
            # 创建 MdClient 实例
            logger.debug("创建 MdClient 实例...")
            self._md_client = MdClient()
            
            # 创建 TdClient 实例
            logger.debug("创建 TdClient 实例...")
            self._td_client = TdClient()
            
            # 创建包装回调函数，同时处理登录响应和其他响应
            async def md_callback_wrapper(response: dict) -> None:
                """MdClient 回调包装器"""
                # 添加客户端类型标识
                response['_ClientType'] = 'Md'
                # 处理登录响应
                self._on_login_response(response)
                # 如果有外部回调，调用它
                if self._md_callback:
                    logger.debug(f"调用 MD 回调，消息类型: {response.get('MsgType', 'unknown')}")
                    # 使用 anyio.to_thread.run_sync 调用同步回调
                    await anyio.to_thread.run_sync(self._md_callback, response)
            
            async def td_callback_wrapper(response: dict) -> None:
                """TdClient 回调包装器"""
                # 添加客户端类型标识
                response['_ClientType'] = 'Td'
                # 处理登录响应
                self._on_login_response(response)
                # 如果有外部回调，调用它
                if self._td_callback:
                    logger.debug(f"调用 TD 回调，消息类型: {response.get('MsgType', 'unknown')}")
                    # 使用 anyio.to_thread.run_sync 调用同步回调
                    await anyio.to_thread.run_sync(self._td_callback, response)
            
            # 设置回调函数
            self._md_client.rsp_callback = md_callback_wrapper
            self._td_client.rsp_callback = td_callback_wrapper
            
            # 创建停止事件
            self._client_stop_event = anyio.Event()
            
            # 在 task group 上下文中运行客户端
            async with anyio.create_task_group() as tg:
                # 设置 task group
                self._md_client.task_group = tg
                self._td_client.task_group = tg
                
                # 启动 MdClient（自动登录）
                logger.debug(f"启动 MdClient，用户: {user_id}")
                await self._md_client.start(user_id, password)
                logger.debug("MdClient.start() 调用完成")
                
                # 启动 TdClient（自动登录）
                logger.debug(f"启动 TdClient，用户: {user_id}")
                await self._td_client.start(user_id, password)
                logger.debug("TdClient.start() 调用完成")
                
                # 重新设置回调函数（因为 start() 方法会覆盖回调）
                self._md_client.rsp_callback = md_callback_wrapper
                self._td_client.rsp_callback = td_callback_wrapper
                
                logger.info("MdClient 和 TdClient 初始化成功，等待登录完成...")
                
                # 标记客户端已就绪
                self._clients_ready = True
                logger.debug("客户端已标记为就绪")
                
                # 标记为就绪
                self._ready_event.set()
                
                # 保持 task group 运行，直到收到停止信号
                await self._client_stop_event.wait()
            
            logger.info("客户端 task group 已退出")
            
        except Exception as e:
            logger.error(f"初始化 CTP 客户端失败: {e}", exc_info=True)
            self._init_error = e
            self._service_available = False
            self._ready_event.set()
            raise
    
    def stop(self, timeout: float = 5.0) -> None:
        """
        停止事件循环线程
        
        Args:
            timeout: 等待线程停止的超时时间（秒）
        """
        if not self._running:
            logger.warning("事件循环线程未运行")
            return
        
        logger.info("停止后台事件循环线程...")
        
        try:
            # 设置停止事件，这会导致 task group 退出
            if hasattr(self, '_client_stop_event') and self._client_stop_event:
                # 使用 anyio 的跨线程调用机制设置停止事件
                try:
                    if self._anyio_token:
                        anyio.from_thread.run_sync(self._client_stop_event.set)
                        logger.debug("已设置停止事件")
                    else:
                        logger.warning("anyio token 未设置，无法停止事件循环")
                except Exception as e:
                    logger.warning(f"设置停止事件失败: {e}")
            
            # 等待线程结束
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=timeout)
                if self._thread.is_alive():
                    logger.warning(f"事件循环线程在 {timeout} 秒后仍未停止")
            
            # 清理状态
            self._running = False
            self._clients_ready = False
            self._anyio_token = None
            logger.info("后台事件循环线程已停止")
            
        except Exception as e:
            logger.error(f"停止事件循环线程时出错: {e}", exc_info=True)
    
    def wait_ready(self, timeout: float = 30.0) -> None:
        """
        等待事件循环和客户端就绪（包括登录完成）
        
        该方法分两步等待：
        1. 等待客户端初始化完成（创建 MdClient 和 TdClient）
        2. 等待 CTP 登录完成（简单等待一段时间）
        
        Args:
            timeout: 超时时间（秒），会平均分配给两个等待步骤
            
        Raises:
            TimeoutError: 等待超时时抛出
            RuntimeError: 初始化或登录失败时抛出
        """
        # 第一步：等待客户端初始化完成
        if not self._ready_event.wait(timeout=timeout / 2):
            raise TimeoutError(f"等待 CTP 客户端初始化超时（{timeout / 2}秒）")
        
        # 检查是否有初始化错误
        if self._init_error is not None:
            raise RuntimeError(f"CTP 客户端初始化失败: {self._init_error}")
        
        logger.debug("CTP 客户端初始化完成，等待登录...")
        
        # 第二步：等待登录完成（使用事件机制）
        remaining_timeout = timeout / 2
        logger.debug(f"等待登录完成，超时: {remaining_timeout}s")
        
        if not self._login_event.wait(timeout=remaining_timeout):
            # 超时，检查部分登录状态
            status_msg = f"Md={'成功' if self._md_logged_in else '未完成'}, Td={'成功' if self._td_logged_in else '未完成'}"
            logger.error(f"等待 CTP 登录超时（{remaining_timeout}秒），当前状态: {status_msg}")
            raise TimeoutError(f"等待 CTP 登录超时（{remaining_timeout}秒），当前状态: {status_msg}")
        
        # 检查登录错误
        if self._login_error is not None:
            logger.error(f"CTP 登录失败: {self._login_error}")
            raise self._login_error
        
        # 确认两个客户端都登录成功
        if not (self._md_logged_in and self._td_logged_in):
            status_msg = f"Md={'成功' if self._md_logged_in else '失败'}, Td={'成功' if self._td_logged_in else '失败'}"
            logger.error(f"CTP 登录不完整: {status_msg}")
            raise RuntimeError(f"CTP 登录不完整: {status_msg}")
        
        logger.info(f"CTP 连接已就绪，登录成功: Md={self._md_logged_in}, Td={self._td_logged_in}")
    
    def set_md_callback(self, callback: Callable[[dict], None]) -> None:
        """
        设置行情数据回调函数
        
        Args:
            callback: 行情数据回调函数，接收行情数据字典
        """
        if self._md_client:
            self._md_client.rsp_callback = callback
            logger.debug("已设置行情数据回调函数")
    
    def set_td_callback(self, callback: Callable[[dict], None]) -> None:
        """
        设置交易数据回调函数
        
        Args:
            callback: 交易数据回调函数，接收交易数据字典
        """
        if self._td_client:
            self._td_client.rsp_callback = callback
            logger.debug("已设置交易数据回调函数")
    
    @property
    def md_client(self) -> Optional[Any]:
        """获取 MdClient 实例"""
        return self._md_client
    
    @property
    def td_client(self) -> Optional[Any]:
        """获取 TdClient 实例"""
        return self._td_client
    
    @property
    def is_service_available(self) -> bool:
        """
        检查服务是否可用
        
        Returns:
            bool: True 表示服务可用，False 表示服务不可用
        """
        return self._service_available
