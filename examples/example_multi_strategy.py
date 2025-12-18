#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : example_multi_strategy.py
@Date       : 2025/12/18
@Author     : Kiro AI Assistant
@Email      : -
@Software   : PyCharm
@Description: 多策略并发运行示例

本示例展示如何使用 SyncStrategyApi 同时运行多个策略：
- 使用 run_strategy() 在独立线程中运行策略
- 多个策略并发执行，互不干扰
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.strategy.sync_api import SyncStrategyApi
from loguru import logger
from config_example import CONFIG, STRATEGY_PARAMS, INSTRUMENT_INFO

# 导入策略函数
from example_dual_ma_strategy import dual_moving_average_strategy
from example_quote_monitor import quote_monitor_strategy
from example_position_monitor import position_monitor_strategy


def main():
    """运行多个策略并发示例"""
    logger.info("=" * 80)
    logger.info("多策略并发运行示例")
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
        # 启动多个策略
        logger.info("启动策略 1: 双均线策略")
        thread1 = api.run_strategy(
            dual_moving_average_strategy,
            api,
            STRATEGY_PARAMS["symbol"],
            STRATEGY_PARAMS["fast_period"],
            STRATEGY_PARAMS["slow_period"],
            STRATEGY_PARAMS["volume"]
        )
        
        logger.info("启动策略 2: 行情监控策略")
        thread2 = api.run_strategy(
            quote_monitor_strategy,
            api,
            STRATEGY_PARAMS["symbol"]
        )
        
        logger.info("启动策略 3: 持仓监控策略")
        thread3 = api.run_strategy(
            position_monitor_strategy,
            api,
            STRATEGY_PARAMS["symbol"]
        )
        
        logger.info("所有策略已启动，按 Ctrl+C 停止...")
        
        # 等待所有策略线程
        thread1.join()
        thread2.join()
        thread3.join()
        
    except KeyboardInterrupt:
        logger.info("收到停止信号，正在停止所有策略...")
    finally:
        # 停止服务
        logger.info("停止 API 服务...")
        api.stop()
        logger.info("API 服务已停止")


if __name__ == "__main__":
    main()
