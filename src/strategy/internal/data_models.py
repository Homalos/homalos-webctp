#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : data_models.py
@Date       : 2025/12/19
@Author     : Kiro AI Assistant
@Email      : -
@Software   : PyCharm
@Description: SyncStrategyApi 数据模型定义
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class Quote:
    """
    行情快照数据类
    
    支持属性访问和字典访问两种方式：
    - 属性访问：quote.LastPrice
    - 字典访问：quote["LastPrice"]
    
    无效价格使用 float('nan') 表示
    
    Attributes:
        InstrumentID: 合约代码
        LastPrice: 最新价
        BidPrice1: 买一价
        BidVolume1: 买一量
        AskPrice1: 卖一价
        AskVolume1: 卖一量
        Volume: 成交量
        OpenInterest: 持仓量
        UpdateTime: 更新时间
        UpdateMillisec: 更新毫秒
        ctp_datetime: CTP 时间戳对象
    """
    InstrumentID: str = ""
    LastPrice: float = float('nan')
    BidPrice1: float = float('nan')
    BidVolume1: int = 0
    AskPrice1: float = float('nan')
    AskVolume1: int = 0
    Volume: int = 0
    OpenInterest: float = 0
    UpdateTime: str = ""
    UpdateMillisec: int = 0
    ctp_datetime: Any = None
    
    def __getitem__(self, key: str) -> Any:
        """
        支持字典式访问
        
        Args:
            key: 字段名
            
        Returns:
            字段值
            
        Raises:
            AttributeError: 字段不存在时抛出
            
        Example:
            >>> quote = Quote(InstrumentID="rb2605", LastPrice=3500.0)
            >>> quote["LastPrice"]  # 字典访问
            3500.0
            >>> quote.LastPrice  # 属性访问
            3500.0
        """
        return getattr(self, key)


@dataclass
class Position:
    """
    持仓信息数据类
    
    包含多空持仓的详细信息，区分今仓和昨仓
    
    Attributes:
        pos_long: 多头持仓总量
        pos_long_today: 多头今仓
        pos_long_his: 多头昨仓
        open_price_long: 多头开仓均价
        pos_short: 空头持仓总量
        pos_short_today: 空头今仓
        pos_short_his: 空头昨仓
        open_price_short: 空头开仓均价
    """
    pos_long: int = 0                      # 多头持仓总量
    pos_long_today: int = 0                # 多头今仓
    pos_long_his: int = 0                  # 多头昨仓
    open_price_long: float = float('nan')  # 多头开仓均价
    pos_short: int = 0                     # 空头持仓总量
    pos_short_today: int = 0               # 空头今仓
    pos_short_his: int = 0                 # 空头昨仓
    open_price_short: float = float('nan') # 空头开仓均价
