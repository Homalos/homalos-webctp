#!/usr/bin/env python
"""
@ProjectName: homalos-webctp
@FileName   : order_tracking.py
@Date       : 2026/02/01
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: 订单状态跟踪模块 - 管理订单完整生命周期
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class OrderStatus(Enum):
    """
    订单状态枚举
    
    对应 CTP OrderStatus 字段的各种状态
    """
    # 初始状态
    PENDING = "pending"  # 等待提交
    
    # CTP 返回的状态
    ALL_TRADED = "0"  # 全部成交
    PART_TRADED_QUEUEING = "1"  # 部分成交还在队列中
    PART_TRADED_NOT_QUEUEING = "2"  # 部分成交不在队列中
    NO_TRADE_QUEUEING = "3"  # 未成交还在队列中
    NO_TRADE_NOT_QUEUEING = "4"  # 未成交不在队列中
    CANCELLED = "5"  # 撤单
    UNKNOWN = "a"  # 未知状态（通常是刚提交）
    NOT_TOUCHED = "b"  # 尚未触发
    TOUCHED = "c"  # 已触发
    
    # 错误状态
    ERROR = "error"  # 录入错误
    REJECTED = "rejected"  # 被拒绝
    
    @classmethod
    def from_ctp_status(cls, ctp_status: str) -> "OrderStatus":
        """
        从 CTP OrderStatus 字段转换为 OrderStatus 枚举
        
        Args:
            ctp_status: CTP 返回的 OrderStatus 字段值
            
        Returns:
            OrderStatus 枚举值
        """
        try:
            return cls(ctp_status)
        except ValueError:
            return cls.UNKNOWN
    
    def is_final(self) -> bool:
        """
        判断是否为最终状态（订单已完成，不会再有状态变更）
        
        Returns:
            True 如果是最终状态，False 否则
        """
        return self in [
            OrderStatus.ALL_TRADED,  # 全部成交
            OrderStatus.CANCELLED,  # 已撤销
            OrderStatus.ERROR,  # 录入错误
            OrderStatus.REJECTED,  # 被拒绝
            OrderStatus.PART_TRADED_NOT_QUEUEING,  # 部分成交不在队列中（视为最终状态）
            OrderStatus.NO_TRADE_NOT_QUEUEING,  # 未成交不在队列中（视为最终状态）
        ]
    
    def is_active(self) -> bool:
        """
        判断订单是否处于活跃状态（还在队列中等待成交）
        
        Returns:
            True 如果订单活跃，False 否则
        """
        return self in [
            OrderStatus.PENDING,
            OrderStatus.PART_TRADED_QUEUEING,
            OrderStatus.NO_TRADE_QUEUEING,
            OrderStatus.UNKNOWN,
            OrderStatus.NOT_TOUCHED,
            OrderStatus.TOUCHED,
        ]
    
    def get_description(self) -> str:
        """
        获取状态的中文描述
        
        Returns:
            状态描述字符串
        """
        descriptions = {
            OrderStatus.PENDING: "等待提交",
            OrderStatus.ALL_TRADED: "全部成交",
            OrderStatus.PART_TRADED_QUEUEING: "部分成交还在队列中",
            OrderStatus.PART_TRADED_NOT_QUEUEING: "部分成交不在队列中",
            OrderStatus.NO_TRADE_QUEUEING: "未成交还在队列中",
            OrderStatus.NO_TRADE_NOT_QUEUEING: "未成交不在队列中",
            OrderStatus.CANCELLED: "已撤销",
            OrderStatus.UNKNOWN: "已提交",
            OrderStatus.NOT_TOUCHED: "尚未触发",
            OrderStatus.TOUCHED: "已触发",
            OrderStatus.ERROR: "录入错误",
            OrderStatus.REJECTED: "被拒绝",
        }
        return descriptions.get(self, "未知状态")


@dataclass
class OrderStatusChange:
    """
    订单状态变更记录
    """
    timestamp: float  # 变更时间戳
    old_status: OrderStatus  # 旧状态
    new_status: OrderStatus  # 新状态
    status_msg: str = ""  # CTP 返回的状态消息
    volume_traded: int = 0  # 已成交数量
    volume_total: int = 0  # 剩余数量
    
    def __str__(self) -> str:
        time_str = time.strftime("%H:%M:%S", time.localtime(self.timestamp))
        return (
            f"[{time_str}] {self.old_status.get_description()} -> "
            f"{self.new_status.get_description()} "
            f"(已成交: {self.volume_traded}, 剩余: {self.volume_total})"
        )


@dataclass
class OrderInfo:
    """
    订单完整信息
    
    跟踪订单的完整生命周期，包括所有状态变更和响应记录
    """
    # 基本信息
    unique_id: str  # 订单唯一标识符 (FrontID_SessionID_OrderRef)
    instrument_id: str  # 合约代码
    action: str  # 交易动作 (kaiduo, kaikong, pingduo, pingkong)
    volume: int  # 订单数量
    price: float  # 订单价格
    direction: str  # CTP 方向字段
    offset_flag: str  # CTP 开平标志
    
    # 状态信息
    status: OrderStatus = OrderStatus.PENDING  # 当前状态
    status_history: list[OrderStatusChange] = field(default_factory=list)  # 状态变更历史
    
    # 时间信息
    submit_time: float = field(default_factory=time.time)  # 提交时间
    last_update_time: float = field(default_factory=time.time)  # 最后更新时间
    
    # 成交信息
    volume_traded: int = 0  # 已成交数量
    volume_total: int = 0  # 剩余数量（初始等于订单数量）
    
    # 响应记录
    order_responses: list[dict[str, Any]] = field(default_factory=list)  # 所有 CTP 响应
    
    # 错误信息
    error_id: int = 0  # 错误代码
    error_msg: str = ""  # 错误消息
    
    def __post_init__(self):
        """初始化后处理"""
        if self.volume_total == 0:
            self.volume_total = self.volume
    
    def update_status(
        self,
        new_status: OrderStatus,
        status_msg: str = "",
        volume_traded: int = 0,
        volume_total: int = 0,
    ) -> None:
        """
        更新订单状态
        
        Args:
            new_status: 新状态
            status_msg: 状态消息
            volume_traded: 已成交数量
            volume_total: 剩余数量
        """
        # 记录状态变更
        change = OrderStatusChange(
            timestamp=time.time(),
            old_status=self.status,
            new_status=new_status,
            status_msg=status_msg,
            volume_traded=volume_traded,
            volume_total=volume_total,
        )
        self.status_history.append(change)
        
        # 更新当前状态
        self.status = new_status
        self.last_update_time = time.time()
        self.volume_traded = volume_traded
        self.volume_total = volume_total
    
    def add_response(self, response: dict[str, Any]) -> None:
        """
        添加 CTP 响应记录
        
        Args:
            response: CTP 响应字典
        """
        self.order_responses.append({
            "timestamp": time.time(),
            "response": response,
        })
        self.last_update_time = time.time()
    
    def set_error(self, error_id: int, error_msg: str) -> None:
        """
        设置错误信息
        
        Args:
            error_id: 错误代码
            error_msg: 错误消息
        """
        self.error_id = error_id
        self.error_msg = error_msg
        self.status = OrderStatus.ERROR
        self.last_update_time = time.time()
    
    def is_final(self) -> bool:
        """
        判断订单是否已达到最终状态
        
        Returns:
            True 如果订单已完成，False 否则
        """
        return self.status.is_final()
    
    def is_active(self) -> bool:
        """
        判断订单是否处于活跃状态
        
        Returns:
            True 如果订单活跃，False 否则
        """
        return self.status.is_active()
    
    def get_status_summary(self) -> str:
        """
        获取订单状态摘要
        
        Returns:
            状态摘要字符串
        """
        return (
            f"订单 {self.unique_id}: {self.instrument_id} {self.action} "
            f"{self.volume}手@{self.price} - "
            f"状态: {self.status.get_description()} "
            f"(已成交: {self.volume_traded}/{self.volume})"
        )
    
    def get_status_history_str(self) -> str:
        """
        获取状态变更历史的字符串表示
        
        Returns:
            状态历史字符串
        """
        if not self.status_history:
            return "无状态变更记录"
        
        lines = ["订单状态变更历史:"]
        for i, change in enumerate(self.status_history, 1):
            lines.append(f"  {i}. {change}")
        
        return "\n".join(lines)

