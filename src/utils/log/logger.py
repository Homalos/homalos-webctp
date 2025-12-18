#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: webctp
@FileName   : logger.py
@Date       : 2025/12/3 13:55
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: 基于 loguru 的日志工具类，支持标签分类和 trace_id 追踪
"""

import contextvars
import sys
import uuid
from pathlib import Path
from typing import Optional

from loguru import logger as _logger

# 创建 trace_id 上下文变量，用于追踪请求
_trace_id_context: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    'trace_id', default=None
)

# 创建默认 tag 上下文变量，用于设置日志上下文
_default_tag_context: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    'default_tag', default=None
)


class Logger:
    """
    日志工具类，基于 loguru 库实现。
    
    特性：
    - 支持标签分类日志
    - 支持 trace_id 追踪
    - 支持控制台和文件输出
    - 支持自定义日志格式
    - 线程安全和异步安全
    
    使用示例：
        # 基础使用
        logger = Logger()
        logger.info("这是一条信息", tag="auth")
        logger.error("这是一条错误", tag="database")
        
        # 使用 trace_id
        logger.set_trace_id("req-123456")
        logger.info("处理请求", tag="request")
        logger.clear_trace_id()
        
        # 上下文管理器
        with logger.trace("req-789"):
            logger.info("在 trace 上下文中", tag="service")
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化日志工具"""
        if Logger._initialized:
            return
        
        # 移除默认的处理器
        _logger.remove()
        
        # 添加控制台处理器
        _logger.add(
            sys.stdout,
            format=self._get_console_format(),
            level="DEBUG",
            colorize=True,
            backtrace=True,
            diagnose=True,
        )
        
        # 添加文件处理器（日志文件）
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        _logger.add(
            log_dir / "webctp.log",
            format=self._get_file_format(),
            level="DEBUG",
            rotation="500 MB",
            retention="7 days",
            compression="zip",
            backtrace=True,
            diagnose=True,
        )
        
        # 添加错误日志文件
        _logger.add(
            log_dir / "webctp_error.log",
            format=self._get_file_format(),
            level="ERROR",
            rotation="500 MB",
            retention="30 days",
            compression="zip",
            backtrace=True,
            diagnose=True,
        )
        
        Logger._initialized = True
    
    @staticmethod
    def _get_console_format() -> str:
        """获取控制台日志格式"""
        return (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
    
    @staticmethod
    def _get_file_format() -> str:
        """获取文件日志格式"""
        return (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message}"
        )
    
    @staticmethod
    def _get_trace_id() -> Optional[str]:
        """获取当前的 trace_id"""
        return _trace_id_context.get()
    
    @staticmethod
    def generate_trace_id() -> str:
        """
        生成唯一的 trace_id
        
        Returns:
            生成的 trace_id（UUID 格式）
        """
        return str(uuid.uuid4())
    
    @staticmethod
    def set_trace_id(trace_id: Optional[str] = None) -> str:
        """
        设置 trace_id，用于追踪请求
        
        如果不指定 trace_id，将自动生成一个 UUID
        
        Args:
            trace_id: 追踪 ID，如果为 None 则自动生成
            
        Returns:
            设置的 trace_id
        """
        if trace_id is None:
            trace_id = Logger.generate_trace_id()
        _trace_id_context.set(trace_id)
        return trace_id
    
    @staticmethod
    def clear_trace_id() -> None:
        """清除 trace_id"""
        _trace_id_context.set(None)
    
    @staticmethod
    def get_trace_id() -> Optional[str]:
        """获取当前的 trace_id"""
        return Logger._get_trace_id()
    
    def _log_with_trace(self, message: str, tag: Optional[str], trace_id, log_func, **kwargs) -> None:
        """
        使用 trace_id 记录日志的辅助方法
        
        Args:
            message: 日志消息
            tag: 日志标签
            trace_id: 追踪 ID（True/str/None）
            log_func: 日志函数（_logger.debug/info/error 等）
            **kwargs: 其他参数
        """
        # 处理 trace_id 参数
        if trace_id is True:
            # 自动生成 UUID
            trace_id = self.generate_trace_id()
        
        # 如果指定了 trace_id，临时设置
        if trace_id:
            previous_trace_id = self._get_trace_id()
            self.set_trace_id(trace_id)
            try:
                formatted_message = self._format_message(message, tag)
                # 使用 opt(depth=2) 跳过 _log_with_trace 和 debug/info/error 的栈帧，指向实际调用者
                _logger.opt(depth=2).log(log_func.__name__.upper(), formatted_message, **kwargs)
            finally:
                # 恢复之前的 trace_id
                if previous_trace_id:
                    self.set_trace_id(previous_trace_id)
                else:
                    self.clear_trace_id()
        else:
            formatted_message = self._format_message(message, tag)
            # 使用 opt(depth=2) 跳过 _log_with_trace 和 debug/info/error 的栈帧，指向实际调用者
            _logger.opt(depth=2).log(log_func.__name__.upper(), formatted_message, **kwargs)
    
    def _format_message(self, message: str, tag: Optional[str] = None) -> str:
        """
        格式化日志消息，添加 trace_id 和标签
        
        Args:
            message: 原始消息
            tag: 日志标签（可选）
            
        Returns:
            格式化后的消息
        """
        parts = []
        
        # 添加 trace_id
        trace_id = self._get_trace_id()
        if trace_id:
            parts.append(f"[trace_id={trace_id}]")
        
        # 添加标签（如果指定）
        if tag:
            parts.append(f"[{tag}]")
        
        # 添加消息
        parts.append(message)
        
        return " ".join(parts)
    
    def debug(self, message: str, tag: Optional[str] = None, trace_id: Optional[str] = None, **kwargs) -> None:
        """
        记录 DEBUG 级别日志
        
        Args:
            message: 日志消息
            tag: 日志标签（可选）
            trace_id: 追踪 ID（可选）
                - True: 自动生成 UUID
                - str: 使用指定的 trace_id
                - None/False: 不添加 trace_id
            **kwargs: 其他参数
            
        示例：
            logger.debug("调试信息")
            logger.debug("调试信息", tag="database")
            logger.debug("调试信息", trace_id=True)  # 自动生成 trace_id
            logger.debug("调试信息", trace_id="req-123")  # 指定 trace_id
        """
        self._log_with_trace(message, tag, trace_id, _logger.debug, **kwargs)
    
    def info(self, message: str, tag: Optional[str] = None, trace_id: Optional[str] = None, **kwargs) -> None:
        """
        记录 INFO 级别日志
        
        Args:
            message: 日志消息
            tag: 日志标签（可选）
            trace_id: 追踪 ID（可选）
                - True: 自动生成 UUID
                - str: 使用指定的 trace_id
                - None/False: 不添加 trace_id
            **kwargs: 其他参数
            
        示例：
            logger.info("信息")
            logger.info("信息", tag="auth")
            logger.info("信息", trace_id=True)
        """
        self._log_with_trace(message, tag, trace_id, _logger.info, **kwargs)
    
    def success(self, message: str, tag: Optional[str] = None, trace_id: Optional[str] = None, **kwargs) -> None:
        """
        记录 SUCCESS 级别日志
        
        Args:
            message: 日志消息
            tag: 日志标签（可选）
            trace_id: 追踪 ID（可选）
            **kwargs: 其他参数
        """
        self._log_with_trace(message, tag, trace_id, _logger.success, **kwargs)
    
    def warning(self, message: str, tag: Optional[str] = None, trace_id: Optional[str] = None, **kwargs) -> None:
        """
        记录 WARNING 级别日志
        
        Args:
            message: 日志消息
            tag: 日志标签（可选）
            trace_id: 追踪 ID（可选）
            **kwargs: 其他参数
        """
        self._log_with_trace(message, tag, trace_id, _logger.warning, **kwargs)
    
    def error(self, message: str, tag: Optional[str] = None, trace_id: Optional[str] = None, **kwargs) -> None:
        """
        记录 ERROR 级别日志
        
        Args:
            message: 日志消息
            tag: 日志标签（可选）
            trace_id: 追踪 ID（可选）
            **kwargs: 其他参数
        """
        self._log_with_trace(message, tag, trace_id, _logger.error, **kwargs)
    
    def critical(self, message: str, tag: Optional[str] = None, trace_id: Optional[str] = None, **kwargs) -> None:
        """
        记录 CRITICAL 级别日志
        
        Args:
            message: 日志消息
            tag: 日志标签（可选）
            trace_id: 追踪 ID（可选）
            **kwargs: 其他参数
        """
        self._log_with_trace(message, tag, trace_id, _logger.critical, **kwargs)
    
    def exception(self, message: str, tag: Optional[str] = None, trace_id: Optional[str] = None, **kwargs) -> None:
        """
        记录异常日志（包含堆栈跟踪）
        
        Args:
            message: 日志消息
            tag: 日志标签（可选）
            trace_id: 追踪 ID（可选）
            **kwargs: 其他参数
        """
        self._log_with_trace(message, tag, trace_id, _logger.exception, **kwargs)


# 创建全局日志实例
logger = Logger()
