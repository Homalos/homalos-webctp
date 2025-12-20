#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : instrument_helper.py
@Date       : 2025/12/20
@Author     : Kiro AI Assistant
@Email      : -
@Software   : PyCharm
@Description: 合约信息处理辅助模块 - 处理合约查询、缓存等逻辑
"""

import threading
from typing import Dict, Optional
from loguru import logger


class _InstrumentHelper:
    """
    合约信息处理辅助类
    
    负责处理合约相关的业务逻辑，包括：
    - 合约信息缓存管理
    - 合约信息查询
    - 合约乘数获取
    """
    
    def __init__(self):
        """初始化合约信息辅助类"""
        self._instrument_cache: Dict[str, dict] = {}
        self._instrument_cache_lock = threading.RLock()
    
    def get_cached_instrument(self, instrument_id: str) -> Optional[dict]:
        """
        从缓存获取合约信息
        
        Args:
            instrument_id: 合约代码
            
        Returns:
            合约信息字典，如果不存在则返回 None
        """
        with self._instrument_cache_lock:
            return self._instrument_cache.get(instrument_id)
    
    def cache_instrument(self, instrument_id: str, instrument_info: dict) -> None:
        """
        缓存合约信息
        
        Args:
            instrument_id: 合约代码
            instrument_info: 合约信息字典
        """
        with self._instrument_cache_lock:
            self._instrument_cache[instrument_id] = instrument_info
            logger.debug(f"合约信息已缓存: {instrument_id}")
    
    def cache_instruments_batch(self, instruments_info: Dict[str, dict]) -> None:
        """
        批量缓存合约信息
        
        Args:
            instruments_info: 合约信息字典，键为合约代码，值为合约信息
        """
        with self._instrument_cache_lock:
            self._instrument_cache.update(instruments_info)
            logger.info(f"批量缓存合约信息: {len(instruments_info)} 个合约")
    
    def get_volume_multiple(self, instrument_id: str, default: int = 1) -> int:
        """
        获取合约乘数
        
        Args:
            instrument_id: 合约代码
            default: 默认乘数（如果查询失败）
            
        Returns:
            合约乘数
        """
        instrument_info = self.get_cached_instrument(instrument_id)
        if instrument_info:
            multiplier = instrument_info.get('VolumeMultiple', default)
            logger.debug(f"从缓存获取合约乘数: {instrument_id}, 乘数: {multiplier}")
            return multiplier
        
        logger.debug(f"合约乘数缓存未命中: {instrument_id}，使用默认值: {default}")
        return default
    
    def clear_cache(self) -> None:
        """清空合约信息缓存"""
        with self._instrument_cache_lock:
            self._instrument_cache.clear()
            logger.debug("合约信息缓存已清空")
