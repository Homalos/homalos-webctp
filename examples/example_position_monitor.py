#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : example_position_monitor.py
@Date       : 2025/12/18
@Author     : Kiro AI Assistant
@Email      : -
@Software   : PyCharm
@Description: 持仓监控策略示例

本示例展示如何使用 SyncStrategyApi 监控持仓信息：
- 使用 get_position() 查询持仓
- 定期打印持仓数据
"""

import time
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.strategy.sync_api import SyncStrategyApi
from loguru import logger
from config_example import CONFIG, STRATEGY_PARAMS, INSTRUMENT_INFO


def position_monitor_strategy(api: SyncStrategyApi, symbol: str):
    """
    持仓监控策略
    
    定期查询并打印持仓信息，展示 get_position() 的使用。
    
    Args:
        api: SyncStrategyApi 实例
        symbol: 监控的合约代码
    """
    logger.info(f"启动持仓监控策略: {symbol}")
    
    try:
        while True:
            # 获取持仓信息
            position = api.get_position(symbol)
            
            logger.info(
                f"[{symbol}] 持仓信息 - "
                f"多头: {position.pos_long}手(今:{position.pos_long_today}, 昨:{position.pos_long_his}), "
                f"多头均价: {position.open_price_long:.2f}, "
                f"空头: {position.pos_short}手(今:{position.pos_short_today}, 昨:{position.pos_short_his}), "
                f"空头均价: {position.open_price_short:.2f}"
            )
            
            # 每 5 秒查询一次
            time.sleep(5.0)
            
    except KeyboardInterrupt:
        logger.info("持仓监控策略被用户中断")
    except Exception as e:
        logger.error(f"持仓监控策略异常: {e}", exc_info=True)


def main():
    """运行持仓监控策略"""
    logger.info("=" * 80)
    logger.info("持仓监控策略示例")
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
        # 运行持仓监控策略
        position_monitor_strategy(
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
