#!/usr/bin/env python
"""
@ProjectName: homalos-webctp
@FileName   : example_test_single_order.py
@Date       : 2025/02/01
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: 测试单笔订单 - 验证订单响应匹配机制

本示例用于测试任务 1.1 的修复效果：
1. 验证 FrontID 和 SessionID 是否正确缓存
2. 测试单笔订单提交和响应匹配
3. 验证订单唯一标识符生成
4. 测试订单成功和失败场景
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config_example import CONFIG, INSTRUMENT_INFO, STRATEGY_PARAMS
from loguru import logger

from src.strategy.sync_api import SyncStrategyApi


def test_session_info(api: SyncStrategyApi):
    """测试会话信息缓存"""
    logger.info("=" * 80)
    logger.info("测试 1: 验证会话信息缓存")
    logger.info("=" * 80)

    try:
        # 尝试获取会话信息
        front_id, session_id = api._get_session_info()
        logger.info(f"会话信息已缓存: FrontID={front_id}, SessionID={session_id}")
        return True
    except RuntimeError as e:
        logger.error(f"获取会话信息失败: {e}")
        return False


def test_single_order_success(api: SyncStrategyApi, symbol: str):
    """测试单笔订单（预期成功）"""
    logger.info("=" * 80)
    logger.info("测试 2: 提交单笔订单（开仓）")
    logger.info("=" * 80)

    # 获取当前行情
    quote = api.get_quote(symbol, timeout=10.0)
    logger.info(f"当前行情: 最新价={quote.LastPrice:.2f}, 买一={quote.BidPrice1:.2f}, 卖一={quote.AskPrice1:.2f}")

    # 计算一个合理的价格（低于当前价，预期不会立即成交）
    order_price = quote.BidPrice1 - 10.0

    logger.info(f"准备开多仓: 合约={symbol}, 数量=1手, 价格={order_price:.2f}")

    try:
        # 提交订单
        result = api.open_close(
            instrument_id=symbol,
            action="kaiduo",  # 开多
            volume=1,
            price=order_price,
            block=True,  # 阻塞等待响应
            timeout=10.0
        )

        # 检查结果
        if result["success"]:
            logger.info("订单提交成功!")
            logger.info(f"  订单引用: {result.get('order_ref', 'N/A')}")
            logger.info(f"  唯一标识符: {result.get('unique_id', 'N/A')}")
            logger.info(f"  FrontID: {result.get('front_id', 'N/A')}")
            logger.info(f"  SessionID: {result.get('session_id', 'N/A')}")
            logger.info(f"  合约: {result.get('instrument_id', 'N/A')}")
            logger.info(f"  动作: {result.get('action', 'N/A')}")
            logger.info(f"  数量: {result.get('volume', 'N/A')}")
            logger.info(f"  价格: {result.get('price', 'N/A')}")
            return True, result
        else:
            logger.warning("订单提交失败（这可能是预期的）")
            logger.warning(f"  错误代码: {result.get('error_id', 'N/A')}")
            logger.warning(f"  错误信息: {result.get('error_msg', 'N/A')}")
            return False, result

    except Exception as e:
        logger.error(f"订单提交异常: {e}", exc_info=True)
        return False, None


def test_single_order_fail(api: SyncStrategyApi, symbol: str):
    """测试单笔订单（预期失败 - 价格超出涨跌停）"""
    logger.info("=" * 80)
    logger.info("测试 3: 提交单笔订单（预期失败 - 测试错误响应匹配）")
    logger.info("=" * 80)

    # 获取当前行情
    quote = api.get_quote(symbol, timeout=10.0)
    logger.info(f"当前行情: 涨停价={quote.UpperLimitPrice:.2f}, 跌停价={quote.LowerLimitPrice:.2f}")

    # 使用超出涨停价的价格（预期会被拒绝）
    invalid_price = quote.UpperLimitPrice + 100.0

    logger.info(f"准备提交无效订单: 合约={symbol}, 数量=1手, 价格={invalid_price:.2f} (超出涨停价)")

    try:
        # 提交订单
        result = api.open_close(
            instrument_id=symbol,
            action="kaiduo",  # 开多
            volume=1,
            price=invalid_price,
            block=True,  # 阻塞等待响应
            timeout=10.0
        )

        # 检查结果
        if not result["success"]:
            logger.info("订单被正确拒绝（符合预期）")
            logger.info(f"  错误代码: {result.get('error_id', 'N/A')}")
            logger.info(f"  错误信息: {result.get('error_msg', 'N/A')}")
            logger.info("错误响应匹配机制工作正常")
            return True, result
        else:
            logger.warning("订单意外成功（不符合预期）")
            logger.warning(f"  订单引用: {result.get('order_ref', 'N/A')}")
            return False, result

    except Exception as e:
        logger.error(f"订单提交异常: {e}", exc_info=True)
        return False, None


def test_concurrent_orders(api: SyncStrategyApi, symbol: str):
    """测试并发订单（简单版本 - 顺序提交多笔）"""
    logger.info("=" * 80)
    logger.info("测试 4: 顺序提交多笔订单（验证唯一标识符不冲突）")
    logger.info("=" * 80)

    # 获取当前行情
    quote = api.get_quote(symbol, timeout=10.0)
    base_price = quote.BidPrice1 - 10.0

    results = []
    order_count = 3

    logger.info(f"准备提交 {order_count} 笔订单...")

    for i in range(order_count):
        order_price = base_price - i * 1.0  # 每笔订单价格递减
        logger.info(f"提交第 {i+1} 笔订单: 价格={order_price:.2f}")

        try:
            result = api.open_close(
                instrument_id=symbol,
                action="kaiduo",
                volume=1,
                price=order_price,
                block=True,
                timeout=10.0
            )

            results.append(result)

            if result["success"]:
                logger.info(f"  第 {i+1} 笔订单成功: unique_id={result.get('unique_id', 'N/A')}")
            else:
                logger.warning(f"  第 {i+1} 笔订单失败: {result.get('error_msg', 'N/A')}")

            # 短暂延迟，避免频繁请求
            time.sleep(0.5)

        except Exception as e:
            logger.error(f"  第 {i+1} 笔订单异常: {e}")
            results.append(None)

    # 检查唯一标识符是否都不同
    unique_ids = [r.get('unique_id') for r in results if r and r.get('success')]
    if len(unique_ids) == len(set(unique_ids)):
        logger.info(f"所有订单的唯一标识符都不同（共 {len(unique_ids)} 个）")
        return True
    else:
        logger.error(f"发现重复的唯一标识符！")
        return False


def main():
    """主测试流程"""
    logger.info("=" * 80)
    logger.info("单笔订单测试 - 验证任务 1.1 修复效果")
    logger.info("=" * 80)


    # 创建 API 实例并连接
    api = SyncStrategyApi(
        user_id=CONFIG["user_id"],
        password=CONFIG["password"],
        config_path=CONFIG["config_path"],
        timeout=30.0,
        instrument_info=INSTRUMENT_INFO,
    )

    try:
        symbol = STRATEGY_PARAMS["symbol"]

        # 等待一下，确保登录完成
        logger.info("等待登录完成...")
        time.sleep(2)

        # 测试结果统计
        test_results = {}

        # 测试 1: 会话信息缓存
        test_results["session_info"] = test_session_info(api)
        time.sleep(1)

        # 测试 2: 单笔订单（成功场景）
        success, result = test_single_order_success(api, symbol)
        test_results["single_order_success"] = success
        time.sleep(2)

        # 测试 3: 单笔订单（失败场景）
        success, result = test_single_order_fail(api, symbol)
        test_results["single_order_fail"] = success
        time.sleep(2)

        # 测试 4: 并发订单
        test_results["concurrent_orders"] = test_concurrent_orders(api, symbol)

        # 输出测试总结
        logger.info("=" * 80)
        logger.info("测试总结")
        logger.info("=" * 80)

        for test_name, result in test_results.items():
            status = "通过" if result else "❌ 失败"
            logger.info(f"{test_name}: {status}")

        # 计算通过率
        passed = sum(1 for r in test_results.values() if r)
        total = len(test_results)
        pass_rate = (passed / total) * 100 if total > 0 else 0

        logger.info("=" * 80)
        logger.info(f"测试通过率: {passed}/{total} ({pass_rate:.1f}%)")
        logger.info("=" * 80)

        if pass_rate == 100:
            logger.info("🎉 所有测试通过！任务 1.1 修复成功！")
        else:
            logger.warning("部分测试失败，请检查日志")

    except Exception as e:
        logger.error(f"测试过程中发生异常: {e}", exc_info=True)

    finally:
        # 停止服务
        logger.info("停止 API 服务...")
        api.stop()
        logger.info("API 服务已停止")


if __name__ == "__main__":
    main()
