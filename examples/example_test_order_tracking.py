#!/usr/bin/env python
"""
@ProjectName: homalos-webctp
@FileName   : example_test_order_tracking.py
@Date       : 2026/02/01
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: 测试订单状态跟踪功能

本示例用于测试增强的订单状态跟踪系统：
1. 验证订单生命周期管理
2. 测试订单状态变更记录
3. 验证多次回调处理
4. 测试订单查询功能
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


def test_order_lifecycle(api: SyncStrategyApi, symbol: str):
    """测试订单生命周期跟踪"""
    logger.info("=" * 80)
    logger.info("测试 1: 订单生命周期跟踪")
    logger.info("=" * 80)

    # 获取当前行情
    quote = api.get_quote(symbol, timeout=10.0)
    logger.info(f"当前行情: 最新价={quote.LastPrice:.2f}")

    # 提交订单（价格低于市价，不会立即成交）
    order_price = quote.BidPrice1 - 10.0
    logger.info(f"提交订单: 合约={symbol}, 数量=1手, 价格={order_price:.2f}")

    try:
        result = api.open_close(
            instrument_id=symbol,
            action="kaiduo",
            volume=1,
            price=order_price,
            block=True,
            timeout=10.0
        )

        if not result["success"]:
            logger.error(f"订单提交失败: {result.get('error_msg')}")
            return False, None

        unique_id = result.get("unique_id")
        logger.info(f"订单提交成功: {unique_id}")

        # 立即查询订单信息
        order_info = api.get_order_info(unique_id)
        if order_info:
            logger.info(f"订单状态: {order_info.get_status_summary()}")
            logger.info(f"状态历史:\n{order_info.get_status_history_str()}")

            # 等待一段时间，看是否有状态更新
            logger.info("等待 3 秒，观察订单状态变化...")
            time.sleep(3)

            # 再次查询
            order_info = api.get_order_info(unique_id)
            if order_info:
                logger.info(f"更新后状态: {order_info.get_status_summary()}")
                logger.info(f"状态历史:\n{order_info.get_status_history_str()}")
                logger.info(f"响应次数: {len(order_info.order_responses)}")

                return True, unique_id
        else:
            logger.error("无法获取订单信息")
            return False, None

    except Exception as e:
        logger.error(f"测试异常: {e}", exc_info=True)
        return False, None


def test_active_orders(api: SyncStrategyApi, symbol: str):
    """测试活跃订单查询"""
    logger.info("=" * 80)
    logger.info("测试 2: 活跃订单查询")
    logger.info("=" * 80)

    # 提交多笔订单
    quote = api.get_quote(symbol, timeout=10.0)
    base_price = quote.BidPrice1 - 10.0

    order_ids = []
    for i in range(3):
        order_price = base_price - i * 1.0
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

            if result["success"]:
                order_ids.append(result["unique_id"])
                logger.info(f"  ✅ 订单 {i+1} 提交成功")

            time.sleep(0.5)

        except Exception as e:
            logger.error(f"  ❌ 订单 {i+1} 提交失败: {e}")

    # 查询所有活跃订单
    logger.info("\n查询所有活跃订单:")
    active_orders = api.get_active_orders()
    logger.info(f"当前活跃订单数: {len(active_orders)}")

    for unique_id, order_info in active_orders.items():
        logger.info(f"  - {order_info.get_status_summary()}")

    return len(active_orders) > 0


def test_completed_orders(api: SyncStrategyApi):
    """测试已完成订单查询"""
    logger.info("=" * 80)
    logger.info("测试 3: 已完成订单查询")
    logger.info("=" * 80)

    # 等待一段时间，让订单可能达到最终状态
    logger.info("等待 5 秒，让订单可能达到最终状态...")
    time.sleep(5)

    # 查询已完成订单
    completed_orders = api.get_completed_orders(limit=10)
    logger.info(f"已完成订单数: {len(completed_orders)}")

    if completed_orders:
        logger.info("\n已完成订单列表:")
        for unique_id, order_info in completed_orders.items():
            logger.info(f"  - {order_info.get_status_summary()}")
            logger.info(f"    最终状态: {order_info.status.get_description()}")
            logger.info(f"    响应次数: {len(order_info.order_responses)}")

    return True


def test_order_cleanup(api: SyncStrategyApi):
    """测试订单清理功能"""
    logger.info("=" * 80)
    logger.info("测试 4: 订单清理功能")
    logger.info("=" * 80)

    # 查询当前已完成订单数
    completed_before = api.get_completed_orders()
    logger.info(f"清理前已完成订单数: {len(completed_before)}")

    # 清理订单，只保留最近 5 个
    cleared_count = api.clear_completed_orders(keep_recent=5)
    logger.info(f"清理了 {cleared_count} 个订单")

    # 再次查询
    completed_after = api.get_completed_orders()
    logger.info(f"清理后已完成订单数: {len(completed_after)}")

    return True


def test_order_status_details(api: SyncStrategyApi, symbol: str):
    """测试订单状态详细信息"""
    logger.info("=" * 80)
    logger.info("测试 5: 订单状态详细信息")
    logger.info("=" * 80)

    # 提交一笔订单
    quote = api.get_quote(symbol, timeout=10.0)
    order_price = quote.BidPrice1 - 10.0

    logger.info(f"提交订单: 价格={order_price:.2f}")

    try:
        result = api.open_close(
            instrument_id=symbol,
            action="kaiduo",
            volume=1,
            price=order_price,
            block=True,
            timeout=10.0
        )

        if not result["success"]:
            logger.error(f"订单提交失败: {result.get('error_msg')}")
            return False

        unique_id = result["unique_id"]
        logger.info(f"✅ 订单提交成功: {unique_id}")

        # 等待一段时间，收集多次回调
        logger.info("等待 5 秒，收集订单状态更新...")
        time.sleep(5)

        # 获取订单详细信息
        order_info = api.get_order_info(unique_id)
        if order_info:
            logger.info("\n订单详细信息:")
            logger.info(f"  唯一标识符: {order_info.unique_id}")
            logger.info(f"  合约: {order_info.instrument_id}")
            logger.info(f"  动作: {order_info.action}")
            logger.info(f"  数量: {order_info.volume}")
            logger.info(f"  价格: {order_info.price}")
            logger.info(f"  当前状态: {order_info.status.get_description()}")
            logger.info(f"  已成交: {order_info.volume_traded}/{order_info.volume}")
            logger.info(f"  剩余: {order_info.volume_total}")
            logger.info(f"  是否活跃: {order_info.is_active()}")
            logger.info(f"  是否最终状态: {order_info.is_final()}")
            logger.info(f"  响应次数: {len(order_info.order_responses)}")
            logger.info(f"\n{order_info.get_status_history_str()}")

            return True
        else:
            logger.error("无法获取订单信息")
            return False

    except Exception as e:
        logger.error(f"测试异常: {e}", exc_info=True)
        return False


def main():
    """主测试流程"""
    logger.info("=" * 80)
    logger.info("订单状态跟踪功能测试")
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

        # 等待登录完成
        logger.info("等待登录完成...")
        time.sleep(2)

        # 测试结果统计
        test_results = {}

        # 测试 1: 订单生命周期
        success, order_id = test_order_lifecycle(api, symbol)
        test_results["order_lifecycle"] = success
        time.sleep(2)

        # 测试 2: 活跃订单查询
        test_results["active_orders"] = test_active_orders(api, symbol)
        time.sleep(2)

        # 测试 3: 已完成订单查询
        test_results["completed_orders"] = test_completed_orders(api)
        time.sleep(2)

        # 测试 4: 订单清理
        test_results["order_cleanup"] = test_order_cleanup(api)
        time.sleep(2)

        # 测试 5: 订单状态详细信息
        test_results["order_details"] = test_order_status_details(api, symbol)

        # 输出测试总结
        logger.info("=" * 80)
        logger.info("测试总结")
        logger.info("=" * 80)

        for test_name, result in test_results.items():
            status = "✅ 通过" if result else "❌ 失败"
            logger.info(f"{test_name}: {status}")

        # 计算通过率
        passed = sum(1 for r in test_results.values() if r)
        total = len(test_results)
        pass_rate = (passed / total) * 100 if total > 0 else 0

        logger.info("=" * 80)
        logger.info(f"测试通过率: {passed}/{total} ({pass_rate:.1f}%)")
        logger.info("=" * 80)

        if pass_rate == 100:
            logger.info("🎉 所有测试通过！订单状态跟踪功能正常！")
        else:
            logger.warning("⚠️ 部分测试失败，请检查日志")

    except Exception as e:
        logger.error(f"测试过程中发生异常: {e}", exc_info=True)

    finally:
        # 停止服务
        logger.info("停止 API 服务...")
        api.stop()
        logger.info("API 服务已停止")


if __name__ == "__main__":
    main()

