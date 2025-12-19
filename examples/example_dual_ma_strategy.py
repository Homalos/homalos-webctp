#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : example_dual_ma_strategy.py
@Date       : 2025/12/18
@Author     : Kiro AI Assistant
@Email      : -
@Software   : PyCharm
@Description: 双均线策略示例

本示例展示如何使用 SyncStrategyApi 实现双均线策略：
- 当快速均线上穿慢速均线时，开多仓
- 当快速均线下穿慢速均线时，平多仓并开空仓
- 当快速均线上穿慢速均线时，平空仓并开多仓
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


def dual_moving_average_strategy(api: SyncStrategyApi, symbol: str, fast_period: int, slow_period: int, volume: int):
    """
    双均线策略
    
    策略逻辑：
    - 当快速均线上穿慢速均线时，开多仓
    - 当快速均线下穿慢速均线时，平多仓并开空仓
    - 当快速均线上穿慢速均线时，平空仓并开多仓
    
    Args:
        api: SyncStrategyApi 实例
        symbol: 交易合约代码
        fast_period: 快速均线周期
        slow_period: 慢速均线周期
        volume: 每次交易手数
    """
    logger.info(f"启动双均线策略: {symbol}, 快线周期={fast_period}, 慢线周期={slow_period}")
    
    # 用于存储历史价格
    price_history = []
    
    # 上一次的信号状态
    last_signal = None  # 'long', 'short', None
    
    try:
        while True:
            # 获取最新行情
            quote = api.get_quote(symbol)
            
            if quote.LastPrice != quote.LastPrice:  # 检查是否为 NaN
                logger.warning(f"行情价格无效: {symbol}")
                time.sleep(STRATEGY_PARAMS["check_interval"])
                continue
            
            # 添加到历史价格
            price_history.append(quote.LastPrice)
            
            # 保持历史价格数量不超过慢速均线周期
            if len(price_history) > slow_period:
                price_history.pop(0)
            
            # 等待足够的数据
            if len(price_history) < slow_period:
                logger.debug(f"等待数据积累: {len(price_history)}/{slow_period}")
                time.sleep(STRATEGY_PARAMS["check_interval"])
                continue
            
            # 计算均线
            fast_ma = sum(price_history[-fast_period:]) / fast_period
            slow_ma = sum(price_history[-slow_period:]) / slow_period
            
            logger.info(
                f"[{symbol}] 价格: {quote.LastPrice:.2f}, "
                f"快线: {fast_ma:.2f}, 慢线: {slow_ma:.2f}"
            )
            
            # 获取当前持仓
            position = api.get_position(symbol)
            
            # 判断信号
            current_signal = None
            if fast_ma > slow_ma:
                current_signal = 'long'
            elif fast_ma < slow_ma:
                current_signal = 'short'
            
            # 执行交易逻辑
            if current_signal != last_signal and current_signal is not None:
                logger.info(f"信号变化: {last_signal} -> {current_signal}")
                
                if current_signal == 'long':
                    # 快线上穿慢线，做多
                    
                    # 如果有空仓，先平空
                    if position.pos_short > 0:
                        logger.info(f"平空仓: {position.pos_short} 手")
                        result = api.open_close(
                            symbol, 
                            "pingkong", 
                            position.pos_short, 
                            quote.AskPrice1,
                            block=True,
                            timeout=10.0
                        )
                        if result["success"]:
                            logger.info(f"平空成功: {result}")
                        else:
                            logger.error(f"平空失败: {result}")
                    
                    # 开多仓
                    logger.info(f"开多仓: {volume} 手")
                    result = api.open_close(
                        symbol, 
                        "kaiduo", 
                        volume, 
                        quote.AskPrice1,
                        block=True,
                        timeout=10.0
                    )
                    if result["success"]:
                        logger.info(f"开多成功: {result}")
                    else:
                        logger.error(f"开多失败: {result}")
                
                elif current_signal == 'short':
                    # 快线下穿慢线，做空
                    
                    # 如果有多仓，先平多
                    if position.pos_long > 0:
                        logger.info(f"平多仓: {position.pos_long} 手")
                        result = api.open_close(
                            symbol, 
                            "pingduo", 
                            position.pos_long, 
                            quote.BidPrice1,
                            block=True,
                            timeout=10.0
                        )
                        if result["success"]:
                            logger.info(f"平多成功: {result}")
                        else:
                            logger.error(f"平多失败: {result}")
                    
                    # 开空仓
                    logger.info(f"开空仓: {volume} 手")
                    result = api.open_close(
                        symbol, 
                        "kaikong", 
                        volume, 
                        quote.BidPrice1,
                        block=True,
                        timeout=10.0
                    )
                    if result["success"]:
                        logger.info(f"开空成功: {result}")
                    else:
                        logger.error(f"开空失败: {result}")
                
                last_signal = current_signal
            
            # 等待下一次检查
            time.sleep(STRATEGY_PARAMS["check_interval"])
            
    except KeyboardInterrupt:
        logger.info("策略被用户中断")
    except Exception as e:
        logger.error(f"策略异常: {e}", exc_info=True)


def main():
    """运行双均线策略"""
    logger.info("=" * 80)
    logger.info("双均线策略示例")
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
        # 运行双均线策略
        dual_moving_average_strategy(
            api,
            symbol=STRATEGY_PARAMS["symbol"],
            fast_period=STRATEGY_PARAMS["fast_period"],
            slow_period=STRATEGY_PARAMS["slow_period"],
            volume=STRATEGY_PARAMS["volume"]
        )
    finally:
        # 停止服务
        logger.info("停止 API 服务...")
        api.stop()
        logger.info("API 服务已停止")


if __name__ == "__main__":
    main()
