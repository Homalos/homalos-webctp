#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : logging_plugin.py
@Date       : 2025/12/20
@Author     : Kiro AI Assistant
@Email      : -
@Software   : PyCharm
@Description: 日志记录插件示例 - 记录所有行情和交易数据
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.strategy.sync_api import StrategyPlugin, Quote
from loguru import logger


class LoggingPlugin(StrategyPlugin):
    """
    日志记录插件
    
    记录所有行情和交易数据到日志文件,用于调试和监控。
    
    特性:
    - 记录行情更新
    - 记录交易数据
    - 可配置日志级别
    """
    
    def __init__(self, log_quotes: bool = True, log_trades: bool = True):
        """
        初始化日志记录插件
        
        Args:
            log_quotes: 是否记录行情数据
            log_trades: 是否记录交易数据
        """
        self.log_quotes = log_quotes
        self.log_trades = log_trades
        self.api = None
    
    def on_init(self, api) -> None:
        """插件初始化"""
        self.api = api
        logger.info("日志记录插件已初始化")
        logger.info(f"配置: log_quotes={self.log_quotes}, log_trades={self.log_trades}")
    
    def on_quote(self, quote: Quote) -> Quote:
        """记录行情数据"""
        if self.log_quotes:
            logger.info(
                f"[行情] {quote.InstrumentID}: "
                f"最新价={quote.LastPrice:.2f}, "
                f"买价={quote.BidPrice1:.2f}, "
                f"卖价={quote.AskPrice1:.2f}, "
                f"成交量={quote.Volume}"
            )
        return quote
    
    def on_trade(self, trade_data: dict) -> dict:
        """记录交易数据"""
        if self.log_trades:
            msg_type = trade_data.get('MsgType', '')
            logger.info(f"[交易] 消息类型: {msg_type}")
        return trade_data
    
    def on_stop(self) -> None:
        """插件停止"""
        logger.info("日志记录插件已停止")


if __name__ == "__main__":
    # 使用示例
    from src.strategy.sync_api import SyncStrategyApi
    
    # 创建 API 实例
    api = SyncStrategyApi(
        user_id="your_user_id",
        password="your_password",
        config_path="./config/config_td.yaml"
    )
    
    # 注册日志记录插件
    plugin = LoggingPlugin(log_quotes=True, log_trades=True)
    api.register_plugin(plugin)
    
    # 订阅行情
    api.subscribe(["rb2605"])
    
    # 运行策略
    def my_strategy():
        while True:
            quote = api.get_quote("rb2605")
            if quote:
                print(f"当前价格: {quote.LastPrice}")
    
    api.run_strategy("my_strategy", my_strategy)
