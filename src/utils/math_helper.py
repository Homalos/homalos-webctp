#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : math_helper.py
@Date       : 2025/12/3 14:40
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: 数学辅助函数
"""
import sys


class MathHelper(object):

    @staticmethod
    def adjust_price(price: float) -> float:
        """
        调整价格值，将最大浮点数值转换为0

        当价格值为系统的最大浮点数值时，将其转换为0。
        这通常用于处理CTP API中特殊的价格标记值。

        Args:
            price (float): 需要调整的价格值

        Returns:
            float: 调整后的价格值，最大浮点数值会被转换为0，其他值保持不变
        """
        if price == sys.float_info.max:
            price = 0
        return price
