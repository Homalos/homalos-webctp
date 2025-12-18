#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : example_simple_demo.py
@Date       : 2025/12/18
@Author     : Kiro AI Assistant
@Email      : -
@Software   : PyCharm
@Description: 简单演示 - 获取行情和持仓（推荐新手）

本示例展示 SyncStrategyApi 的基本用法：
1. 获取行情快照
2. 查询持仓信息
3. 等待行情更新
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.strategy.sync_api import SyncStrategyApi
from loguru import logger
from config_example import CONFIG, STRATEGY_PARAMS, INSTRUMENT_INFO


def main():
    """简单演示：获取行情和持仓"""
    logger.info("=" * 80)
    logger.info("简单演示 - 获取行情和持仓")
    logger.info("=" * 80)
    
    # 创建 API 实例并连接
    # 直接提供合约信息（推荐方式，避免 CTP 查询可能失败的问题）
    api = SyncStrategyApi(
        user_id=CONFIG["user_id"],
        password=CONFIG["password"],
        config_path=CONFIG["config_path"],
        timeout=30.0,
        instrument_info=INSTRUMENT_INFO
    )
    
    try:
        symbol = STRATEGY_PARAMS["symbol"]
        
        # 1. 获取行情
        logger.info(f"获取 {symbol} 行情...")
        quote = api.get_quote(symbol, timeout=10.0)
        logger.info(
            f"行情数据: "
            f"合约={quote.InstrumentID}, "
            f"最新价={quote.LastPrice:.2f}, "
            f"买一价={quote.BidPrice1:.2f}, "
            f"卖一价={quote.AskPrice1:.2f}, "
            f"成交量={quote.Volume}, "
            f"时间={quote.UpdateTime}"
        )
        
        # 2. 获取持仓
        logger.info(f"获取 {symbol} 持仓...")
        position = api.get_position(symbol)
        logger.info(
            f"持仓数据: "
            f"多头={position.pos_long}手, "
            f"多头均价={position.open_price_long:.2f}, "
            f"空头={position.pos_short}手, "
            f"空头均价={position.open_price_short:.2f}"
        )
        
        # 3. 演示字典访问方式
        logger.info("演示 Quote 对象的字典访问方式:")
        logger.info(f"  quote['LastPrice'] = {quote['LastPrice']:.2f}")
        logger.info(f"  quote['BidPrice1'] = {quote['BidPrice1']:.2f}")
        logger.info(f"  quote['AskPrice1'] = {quote['AskPrice1']:.2f}")

        # 4. 等待行情更新（无限等待，直到有新行情推送）
        logger.info(f"等待 {symbol} 行情更新...")
        quote = api.wait_quote_update(symbol)  # 默认无限等待
        logger.info(
            f"收到行情更新: 最新价={quote.LastPrice:.2f}, "
            f"时间={quote.UpdateTime}"
        )
        
        # # 4. 等待几次行情更新
        # logger.info(f"等待 {symbol} 行情更新（3次）...")
        # for i in range(3):
        #     quote = api.wait_quote_update(symbol, timeout=30.0)
        #     logger.info(
        #         f"  第 {i+1} 次更新: "
        #         f"最新价={quote.LastPrice:.2f}, "
        #         f"时间={quote.UpdateTime}"
        #     )
        
        # logger.info("简单演示完成！")
        
    finally:
        # 停止服务
        logger.info("停止 API 服务...")
        api.stop()
        logger.info("API 服务已停止")


if __name__ == "__main__":
    main()
