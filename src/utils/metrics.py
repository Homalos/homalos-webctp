#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : metrics.py
@Date       : 2025/12/13 00:00
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: 性能指标收集器，用于收集和报告系统性能指标
"""

import time
import asyncio
import random
from collections import deque, defaultdict
from typing import Dict, List, Optional, Any, Tuple
from statistics import quantiles

try:
    from .log import logger
    from .config import MetricsConfig, GlobalConfig
except ImportError:
    from log import logger
    from config import MetricsConfig, GlobalConfig


class MetricsCollector:
    """性能指标收集器
    
    功能：
    - 收集延迟、计数器、瞬时值三种类型的指标
    - 使用滑动窗口存储延迟数据（最近 10 分钟）
    - 计算百分位数（P50, P95, P99）
    - 定期输出指标报告到日志
    - 支持采样率控制
    
    使用示例：
        # 创建收集器
        collector = MetricsCollector()
        
        # 记录延迟
        collector.record_latency("order_latency", 45.2)
        
        # 记录计数器
        collector.record_counter("order_count", 1)
        
        # 记录瞬时值
        collector.record_gauge("active_connections", 10)
        
        # 获取百分位数
        percentiles = collector.get_percentiles("order_latency")
        print(f"P95: {percentiles.get(0.95)}")
        
        # 启动定期报告
        await collector.start_reporting(interval_seconds=60)
        
        # 停止报告
        await collector.stop_reporting()
    """
    
    # 滑动窗口时间（秒）
    WINDOW_SIZE_SECONDS = 600  # 10 分钟
    
    def __init__(self, config: Optional[MetricsConfig] = None):
        """初始化性能指标收集器
        
        Args:
            config: 指标配置，如果为 None 则使用 GlobalConfig.Metrics
        """
        # 使用提供的配置或全局配置
        self.config = config if config is not None else GlobalConfig.Metrics
        
        # 延迟指标：{metric_name: deque([(timestamp, latency_ms), ...])}
        self._latencies: Dict[str, deque] = defaultdict(lambda: deque())
        
        # 计数器：{metric_name: count}
        self._counters: Dict[str, int] = defaultdict(int)
        
        # 瞬时值：{metric_name: value}
        self._gauges: Dict[str, float] = {}
        
        # 报告任务
        self._report_task: Optional[asyncio.Task] = None
        self._report_interval: int = self.config.report_interval
    
    def record_latency(self, metric_name: str, latency_ms: float) -> None:
        """记录延迟指标
        
        Args:
            metric_name: 指标名称（如 "order_latency", "market_latency"）
            latency_ms: 延迟时间（毫秒）
        """
        # 检查是否启用
        if not self.config.enabled:
            return
        
        # 采样率检查
        if random.random() > self.config.sample_rate:
            return
        
        # 记录延迟数据
        current_time = time.time()
        self._latencies[metric_name].append((current_time, latency_ms))
        
        # 清理旧数据
        self._cleanup_old_data(metric_name)
    
    def record_counter(self, metric_name: str, value: int = 1) -> None:
        """记录计数器指标
        
        Args:
            metric_name: 指标名称（如 "order_count", "error_count"）
            value: 计数值，默认为 1
        """
        # 检查是否启用
        if not self.config.enabled:
            return
        
        # 累加计数器
        self._counters[metric_name] += value
    
    def record_gauge(self, metric_name: str, value: float) -> None:
        """记录瞬时值指标
        
        Args:
            metric_name: 指标名称（如 "active_connections", "memory_usage"）
            value: 瞬时值
        """
        # 检查是否启用
        if not self.config.enabled:
            return
        
        # 更新瞬时值
        self._gauges[metric_name] = value
    
    def _cleanup_old_data(self, metric_name: str) -> None:
        """清理指定指标中超过滑动窗口时间的旧数据
        
        Args:
            metric_name: 指标名称
        """
        if metric_name not in self._latencies:
            return
        
        current_time = time.time()
        cutoff_time = current_time - self.WINDOW_SIZE_SECONDS
        
        # 从左侧移除过期数据
        latency_deque = self._latencies[metric_name]
        while latency_deque and latency_deque[0][0] < cutoff_time:
            latency_deque.popleft()
    
    def get_percentiles(
        self, 
        metric_name: str, 
        percentiles: List[float] = None
    ) -> Dict[float, float]:
        """获取指定延迟指标的百分位数
        
        Args:
            metric_name: 指标名称
            percentiles: 百分位数列表，默认为 [0.5, 0.95, 0.99]
        
        Returns:
            百分位数字典，如 {0.5: 50.0, 0.95: 95.0, 0.99: 99.0}
            如果数据不足，返回空字典
        """
        if percentiles is None:
            percentiles = [0.5, 0.95, 0.99]
        
        # 检查指标是否存在
        if metric_name not in self._latencies:
            return {}
        
        # 清理旧数据
        self._cleanup_old_data(metric_name)
        
        # 获取延迟值列表
        latency_values = [latency for _, latency in self._latencies[metric_name]]
        
        # 数据不足，无法计算百分位数（至少需要 2 个数据点）
        if len(latency_values) < 2:
            return {}
        
        try:
            # 使用 statistics.quantiles 计算百分位数
            # n 参数表示分位数，例如 n=100 表示百分位数
            result = {}
            sorted_values = sorted(latency_values)
            
            for p in percentiles:
                # 计算索引位置
                if p == 0.0:
                    result[p] = sorted_values[0]
                elif p == 1.0:
                    result[p] = sorted_values[-1]
                else:
                    # 使用线性插值
                    index = p * (len(sorted_values) - 1)
                    lower_index = int(index)
                    upper_index = min(lower_index + 1, len(sorted_values) - 1)
                    fraction = index - lower_index
                    
                    result[p] = (
                        sorted_values[lower_index] * (1 - fraction) +
                        sorted_values[upper_index] * fraction
                    )
            
            return result
        except Exception as e:
            logger.warning(f"计算百分位数失败: {e}", tag="metrics")
            return {}
    
    def get_summary(self) -> Dict[str, Any]:
        """获取所有指标的摘要
        
        Returns:
            指标摘要字典，包含：
            - latencies: 延迟指标的百分位数
            - counters: 计数器值
            - gauges: 瞬时值
        """
        summary = {
            "latencies": {},
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "timestamp": time.time()
        }
        
        # 计算所有延迟指标的百分位数
        for metric_name in self._latencies.keys():
            percentiles = self.get_percentiles(metric_name)
            if percentiles:
                # 同时记录数据点数量
                summary["latencies"][metric_name] = {
                    "percentiles": percentiles,
                    "count": len(self._latencies[metric_name])
                }
        
        return summary
    
    async def _report(self) -> None:
        """生成并输出指标报告（私有方法）"""
        summary = self.get_summary()
        
        # 构建报告消息
        report_lines = ["=== 性能指标报告 ==="]
        
        # 延迟指标
        if summary["latencies"]:
            report_lines.append("\n【延迟指标】")
            for metric_name, data in summary["latencies"].items():
                percentiles = data["percentiles"]
                count = data["count"]
                report_lines.append(f"  {metric_name} (样本数: {count}):")
                
                if 0.5 in percentiles:
                    report_lines.append(f"    P50: {percentiles[0.5]:.2f} ms")
                if 0.95 in percentiles:
                    report_lines.append(f"    P95: {percentiles[0.95]:.2f} ms")
                if 0.99 in percentiles:
                    report_lines.append(f"    P99: {percentiles[0.99]:.2f} ms")
        
        # 计数器
        if summary["counters"]:
            report_lines.append("\n【计数器】")
            for metric_name, value in summary["counters"].items():
                report_lines.append(f"  {metric_name}: {value}")
        
        # 瞬时值
        if summary["gauges"]:
            report_lines.append("\n【瞬时值】")
            for metric_name, value in summary["gauges"].items():
                report_lines.append(f"  {metric_name}: {value:.2f}")
        
        report_lines.append("=" * 30)
        
        # 输出到日志
        report_message = "\n".join(report_lines)
        logger.info(report_message, tag="metrics")
    
    async def start_reporting(self, interval_seconds: Optional[int] = None) -> None:
        """启动定期指标报告
        
        Args:
            interval_seconds: 报告间隔（秒），如果为 None 则使用配置中的值
        """
        # 检查是否启用
        if not self.config.enabled:
            logger.warning("指标收集未启用，跳过启动报告", tag="metrics")
            return
        
        # 如果已经在运行，先停止
        if self._report_task is not None and not self._report_task.done():
            await self.stop_reporting()
        
        # 设置报告间隔
        if interval_seconds is not None:
            self._report_interval = interval_seconds
        
        # 创建报告任务
        async def report_loop():
            """报告循环"""
            logger.info(
                f"启动性能指标报告，间隔: {self._report_interval} 秒", 
                tag="metrics"
            )
            
            while True:
                try:
                    await asyncio.sleep(self._report_interval)
                    await self._report()
                except asyncio.CancelledError:
                    logger.info("性能指标报告已停止", tag="metrics")
                    break
                except Exception as e:
                    logger.error(f"生成指标报告时出错: {e}", tag="metrics")
        
        self._report_task = asyncio.create_task(report_loop())
    
    async def stop_reporting(self) -> None:
        """停止定期指标报告"""
        if self._report_task is not None and not self._report_task.done():
            self._report_task.cancel()
            try:
                await self._report_task
            except asyncio.CancelledError:
                pass
            self._report_task = None
            logger.info("已停止性能指标报告", tag="metrics")
