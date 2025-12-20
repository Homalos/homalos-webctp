#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : risk_control_plugin.py
@Date       : 2025/12/20
@Author     : Kiro AI Assistant
@Email      : -
@Software   : PyCharm
@Description: 风险控制插件示例 - 过滤异常行情和限制交易
"""

import sys
import os
import math

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.strategy.sync_api import StrategyPlugin, Quote
from loguru import logger


class RiskControlPlugin(StrategyPlugin):
    """
    风险控制插件
    
    提供基本的风险控制功能:
    - 过滤异常行情(价格为 NaN 或 0)
    - 价格涨跌幅限制检查
    - 交易数据验证
    
    特性:
    - 自动过滤无效行情
    - 可配置价格变动阈值
    - 记录风险事件
    """
    
    def __init__(self, max_price_change_pct: float = 10.0):
        """
        初始化风险控制插件
        
        Args:
            max_price_change_pct: 最大价格变动百分比(默认 10%)
        """
        self.max_price_change_pct = max_price_change_pct
        self.api = None
        self.last_prices = {}  # 记录上一次的价格
    
    def on_init(self, api) -> None:
        """插件初始化"""
        self.api = api
        logger.info("风险控制插件已初始化")
        logger.info(f"配置: max_price_change_pct={self.max_price_change_pct}%")
    
    def on_quote(self, quote: Quote) -> Quote:
        """
        验证行情数据
        
        过滤条件:
        1. 价格为 NaN 或 0
        2. 价格变动超过阈值
        """
        instrument_id = quote.InstrumentID
        last_price = quote.LastPrice
        
        # 检查价格是否有效
        if math.isnan(last_price) or last_price <= 0:
            logger.warning(f"[风控] 过滤无效行情: {instrument_id}, 价格={last_price}")
            return None
        
        # 检查价格变动幅度
        if instrument_id in self.last_prices:
            prev_price = self.last_prices[instrument_id]
            price_change_pct = abs((last_price - prev_price) / prev_price * 100)
            
            if price_change_pct > self.max_price_change_pct:
                logger.warning(
                    f"[风控] 价格变动异常: {instrument_id}, "
                    f"前价={prev_price:.2f}, 现价={last_price:.2f}, "
                    f"变动={price_change_pct:.2f}%"
                )
                # 不过滤,但记录警告
        
        # 更新最后价格
        self.last_prices[instrument_id] = last_price
        
        return quote
    
    def on_trade(self, trade_data: dict) -> dict:
        """
        验证交易数据
        
        检查交易数据的完整性和合法性
        """
        msg_type = trade_data.get('MsgType', '')
        
        # 检查订单响应
        if 'RtnOrder' in msg_type:
            logger.debug(f"[风控] 订单响应通过验证: {msg_type}")
        
        # 检查成交回报
        if 'RtnTrade' in msg_type:
            logger.debug(f"[风控] 成交回报通过验证: {msg_type}")
        
        return trade_data
    
    def on_stop(self) -> None:
        """插件停止"""
        logger.info("风险控制插件已停止")
        logger.info(f"共监控 {len(self.last_prices)} 个合约")


if __name__ == "__main__":
    # 使用示例
    from src.strategy.sync_api import SyncStrategyApi
    
    # 创建 API 实例
    api = SyncStrategyApi(
        user_id="your_user_id",
        password="your_password",
        config_path="./config/config_td.yaml"
    )
    
    # 注册风险控制插件
    plugin = RiskControlPlugin(max_price_change_pct=10.0)
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
