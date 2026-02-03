#!/usr/bin/env python
"""
@ProjectName: homalos-webctp
@FileName   : data_models.py
@Date       : 2025/12/19
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description:

    SyncStrategyApi 数据模型定义

    模块概述

    本模块定义了 SyncStrategyApi 使用的核心数据类，包括行情快照（Quote）和持仓信息（Position）。
    这些数据类使用 Python 的 @dataclass 装饰器，提供简洁的数据结构定义和自动生成的方法。

    数据类特性

    1. **自动生成方法**
       - __init__: 自动生成初始化方法
       - __repr__: 自动生成字符串表示
       - __eq__: 自动生成相等性比较

    2. **类型注解**
       - 所有字段都有明确的类型注解
       - 支持 IDE 的类型检查和自动补全

    3. **默认值**
       - 所有字段都有合理的默认值
       - 无效价格使用 float('nan') 表示

    使用示例

    创建 Quote 对象::

        # 方式1：使用关键字参数
        quote = Quote(
            InstrumentID="rb2605",
            LastPrice=3500.0,
            BidPrice1=3499.0,
            AskPrice1=3501.0
        )

        # 方式2：使用默认值
        quote = Quote(InstrumentID="rb2605")
        print(quote.LastPrice)  # nan

    访问 Quote 字段::

        # 属性访问
        price = quote.LastPrice

        # 字典访问
        price = quote["LastPrice"]

        # 检查价格是否有效
        if not math.isnan(quote.LastPrice):
            print(f"有效价格: {quote.LastPrice}")

    创建 Position 对象::

        position = Position(
            pos_long=10,
            pos_long_today=5,
            pos_long_his=5,
            open_price_long=3500.0
        )

        # 计算净持仓
        net_position = position.pos_long - position.pos_short
        print(f"净持仓: {net_position}")

    最佳实践

    1. **使用类型注解**
       - 在函数签名中使用 Quote 和 Position 类型
       - 利用 IDE 的类型检查功能

    2. **检查无效值**
       - 使用 math.isnan() 检查价格是否有效
       - 不要直接比较 float('nan')

    3. **不可变性**
       - 数据类默认是可变的，如果需要不可变，使用 frozen=True
       - 在多线程环境中，考虑使用副本而不是共享对象

    4. **序列化**
       - 可以使用 dataclasses.asdict() 转换为字典
       - 便于 JSON 序列化和日志记录

    示例代码:

        from dataclasses import asdict
        import json

        quote = Quote(InstrumentID="rb2605", LastPrice=3500.0)

        # 转换为字典
        quote_dict = asdict(quote)

        # JSON 序列化
        json_str = json.dumps(quote_dict, default=str)
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class Quote:
    """
    行情快照数据类

    支持属性访问和字典访问两种方式：
    - 属性访问：quote.LastPrice
    - 字典访问：quote["LastPrice"]

    无效价格使用 float('nan') 表示

    Attributes:
        InstrumentID: 合约代码
        LastPrice: 最新价
        BidPrice1: 买一价
        BidVolume1: 买一量
        AskPrice1: 卖一价
        AskVolume1: 卖一量
        Volume: 成交量
        OpenInterest: 持仓量
        UpperLimitPrice: 涨停价
        LowerLimitPrice: 跌停价
        UpdateTime: 更新时间
        UpdateMillisec: 更新毫秒
        ctp_datetime: CTP 时间戳对象
    """

    InstrumentID: str = ""
    LastPrice: float = float("nan")
    BidPrice1: float = float("nan")
    BidVolume1: int = 0
    AskPrice1: float = float("nan")
    AskVolume1: int = 0
    Volume: int = 0
    OpenInterest: float = 0
    UpperLimitPrice: float = float("nan")  # 涨停价
    LowerLimitPrice: float = float("nan")  # 跌停价
    UpdateTime: str = ""
    UpdateMillisec: int = 0
    ctp_datetime: Any = None

    def __getitem__(self, key: str) -> Any:
        """
        支持字典式访问

        Args:
            key: 字段名

        Returns:
            字段值

        Raises:
            AttributeError: 字段不存在时抛出

        Example:
            quote = Quote(InstrumentID="rb2605", LastPrice=3500.0)
            quote["LastPrice"]  # 字典访问
            3500.0
            quote.LastPrice  # 属性访问
            3500.0
        """
        return getattr(self, key)


@dataclass
class Position:
    """
    持仓信息数据类

    包含多空持仓的详细信息，区分今仓和昨仓

    Attributes:
        pos_long: 多头持仓总量
        pos_long_today: 多头今仓
        pos_long_his: 多头昨仓
        open_price_long: 多头开仓均价
        pos_short: 空头持仓总量
        pos_short_today: 空头今仓
        pos_short_his: 空头昨仓
        open_price_short: 空头开仓均价
    """

    pos_long: int = 0  # 多头持仓总量
    pos_long_today: int = 0  # 多头今仓
    pos_long_his: int = 0  # 多头昨仓
    open_price_long: float = float("nan")  # 多头开仓均价
    pos_short: int = 0  # 空头持仓总量
    pos_short_today: int = 0  # 空头今仓
    pos_short_his: int = 0  # 空头昨仓
    open_price_short: float = float("nan")  # 空头开仓均价
