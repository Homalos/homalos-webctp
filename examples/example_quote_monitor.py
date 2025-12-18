#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : example_quote_monitor.py
@Date       : 2025/12/18
@Author     : Kiro AI Assistant
@Email      : -
@Software   : PyCharm
@Description: 行情监控策略示例

本示例展示如何使用 SyncStrategyApi 监控行情数据：
- 使用 wait_quote_update() 阻塞等待行情更新
- 实时打印行情数据
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.strategy.sync_api import SyncStrategyApi
from loguru import logger
from config_example import CONFIG, STRATEGY_PARAMS, INSTRUMENT_INFO


def quote_monitor_strategy(api: SyncStrategyApi, symbol: str):
    """
    行情监控策略
    
    简单地监控并打印行情数据，展示 wait_quote_update() 的使用。
    
    Args:
        api: SyncStrategyApi 实例
        symbol: 监控的合约代码
    """
    logger.info(f"启动行情监控策略: {symbol}")
    
    try:
        while True:
            # 等待行情更新（阻塞直到有新行情）
            quote = api.wait_quote_update(symbol, timeout=30.0)
            
            logger.info(
                f"[{symbol}] 最新价: {quote.LastPrice:.2f}, "
                f"买一: {quote.BidPrice1:.2f}({quote.BidVolume1}), "
                f"卖一: {quote.AskPrice1:.2f}({quote.AskVolume1}), "
                f"成交量: {quote.Volume}, "
                f"时间: {quote.UpdateTime}"
            )
            
    except KeyboardInterrupt:
        logger.info("监控策略被用户中断")
    except Exception as e:
        logger.error(f"监控策略异常: {e}", exc_info=True)


def main():
    """运行行情监控策略"""
    logger.info("=" * 80)
    logger.info("行情监控策略示例")
    logger.info("=" * 80)
    
    # 创建 API 实例并连接
    api = SyncStrategyApi(
        user_id=CONFIG["user_id"],
        password=CONFIG["password"],
        config_path=CONFIG["config_path"],
        timeout=30.0,
        instrument_info=INSTRUMENT_INFO
    )
    
    try:
        # 运行行情监控策略
        quote_monitor_strategy(
            api,
            symbol=STRATEGY_PARAMS["symbol"]
        )
    finally:
        # 停止服务
        logger.info("停止 API 服务...")
        api.stop()
        logger.info("API 服务已停止")


if __name__ == "__main__":
    main()
