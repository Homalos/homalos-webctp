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
from typing import Dict, List, Optional, Any

try:
    from .log import logger
    from .config import MetricsConfig, GlobalConfig, AlertsConfig
except ImportError:
    from log import logger
    from config import MetricsConfig, GlobalConfig, AlertsConfig


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
    
    def __init__(self, config: Optional[MetricsConfig] = None, alerts_config: Optional[AlertsConfig] = None):
        """初始化性能指标收集器
        
        Args:
            config: 指标配置，如果为 None 则使用 GlobalConfig.Metrics
            alerts_config: 告警配置，如果为 None 则使用 GlobalConfig.Alerts
        """
        # 使用提供的配置或全局配置
        self.config = config if config is not None else GlobalConfig.Metrics
        self.alerts_config = alerts_config if alerts_config is not None else GlobalConfig.Alerts
        
        # 告警频率控制：记录上次告警时间
        self._last_alert_time: Dict[str, float] = {}
        
        # 延迟指标：{metric_name: deque([(timestamp, latency_ms), ...])}
        self._latencies: Dict[str, deque] = defaultdict(lambda: deque())
        
        # 计数器：{metric_name: count}
        self._counters: Dict[str, int] = defaultdict(int)
        
        # 瞬时值：{metric_name: value}
        self._gauges: Dict[str, float] = {}
        
        # 上次报告时的计数器快照（用于计算吞吐量）
        self._last_counter_snapshot: Dict[str, int] = {}
        self._last_report_time: Optional[float] = None
        
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
        current_time = time.time()
        
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
                    p95_value = percentiles[0.95]
                    report_lines.append(f"    P95: {p95_value:.2f} ms")
                    
                    # 延迟告警检查：P95 超过阈值
                    threshold = self.alerts_config.order_p95_threshold if "order" in metric_name.lower() else self.alerts_config.market_p95_threshold
                    if p95_value > threshold:
                        self._trigger_alert(
                            f"latency_{metric_name}",
                            f"⚠️ 延迟告警: {metric_name} P95 延迟 ({p95_value:.2f} ms) "
                            f"超过阈值 ({threshold:.2f} ms)"
                        )
                
                if 0.99 in percentiles:
                    report_lines.append(f"    P99: {percentiles[0.99]:.2f} ms")
        
        # 计数器和吞吐量
        if summary["counters"]:
            report_lines.append("\n【计数器】")
            for metric_name, value in summary["counters"].items():
                report_lines.append(f"  {metric_name}: {value}")
            
            # 计算 Redis 命中率
            cache_hit = summary["counters"].get("cache_hit", 0)
            cache_miss = summary["counters"].get("cache_miss", 0)
            total_cache_requests = cache_hit + cache_miss
            if total_cache_requests > 0:
                hit_rate = (cache_hit / total_cache_requests) * 100
                report_lines.append("\n【Redis 命中率】")
                report_lines.append(f"  命中: {cache_hit}, 未命中: {cache_miss}")
                report_lines.append(f"  命中率: {hit_rate:.2f}%")
                
                # Redis 命中率告警检查：命中率低于阈值
                threshold_percent = self.alerts_config.redis_hit_rate_threshold * 100
                if hit_rate < threshold_percent:
                    self._trigger_alert(
                        "redis_hit_rate",
                        f"⚠️ Redis 命中率告警: 当前命中率 ({hit_rate:.2f}%) "
                        f"低于阈值 ({threshold_percent:.2f}%)"
                    )
            
            # 计算吞吐量（如果有上次快照）
            if self._last_counter_snapshot and self._last_report_time:
                time_delta = current_time - self._last_report_time
                if time_delta > 0:
                    report_lines.append("\n【吞吐量】")
                    for metric_name, current_value in summary["counters"].items():
                        last_value = self._last_counter_snapshot.get(metric_name, 0)
                        delta = current_value - last_value
                        throughput_per_sec = delta / time_delta
                        throughput_per_min = throughput_per_sec * 60
                        report_lines.append(
                            f"  {metric_name}: {throughput_per_sec:.2f} /秒, "
                            f"{throughput_per_min:.2f} /分钟"
                        )
        
        # 瞬时值
        if summary["gauges"]:
            report_lines.append("\n【瞬时值】")
            for metric_name, value in summary["gauges"].items():
                report_lines.append(f"  {metric_name}: {value:.2f}")
        
        # 收集系统资源指标
        system_metrics = self._collect_system_metrics()
        if system_metrics:
            report_lines.append("\n【系统资源】")
            
            # CPU 使用率
            if "cpu_percent" in system_metrics:
                cpu_percent = system_metrics['cpu_percent']
                report_lines.append(f"  CPU 使用率: {cpu_percent:.1f}%")
                
                # CPU 使用率告警检查
                if cpu_percent > self.alerts_config.cpu_threshold:
                    self._trigger_alert(
                        "cpu_usage",
                        f"⚠️ CPU 使用率告警: 当前 CPU 使用率 ({cpu_percent:.1f}%) "
                        f"超过阈值 ({self.alerts_config.cpu_threshold:.1f}%)"
                    )
            
            # 内存使用率
            if "memory_percent" in system_metrics:
                memory_percent = system_metrics['memory_percent']
                report_lines.append(f"  内存使用率: {memory_percent:.1f}%")
                
                # 内存使用率告警检查
                if memory_percent > self.alerts_config.memory_threshold:
                    self._trigger_alert(
                        "memory_usage",
                        f"⚠️ 内存使用率告警: 当前内存使用率 ({memory_percent:.1f}%) "
                        f"超过阈值 ({self.alerts_config.memory_threshold:.1f}%)"
                    )
            
            if "memory_used_mb" in system_metrics:
                report_lines.append(f"  内存使用量: {system_metrics['memory_used_mb']:.1f} MB")
            if "network_sent_mb" in system_metrics and "network_recv_mb" in system_metrics:
                report_lines.append(
                    f"  网络 I/O: 发送 {system_metrics['network_sent_mb']:.2f} MB, "
                    f"接收 {system_metrics['network_recv_mb']:.2f} MB"
                )
        
        report_lines.append("=" * 30)
        
        # 输出到日志
        report_message = "\n".join(report_lines)
        logger.info(report_message, tag="metrics")
        
        # 更新快照
        self._last_counter_snapshot = dict(self._counters)
        self._last_report_time = current_time
    
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
    
    def _trigger_alert(self, alert_type: str, message: str) -> None:
        """触发告警（带频率控制）
        
        Args:
            alert_type: 告警类型（用于频率控制）
            message: 告警消息
        """
        current_time = time.time()
        last_time = self._last_alert_time.get(alert_type, 0)
        
        # 检查是否在最小间隔内
        if current_time - last_time < self.alerts_config.min_interval:
            return  # 跳过此次告警
        
        # 记录告警时间并输出
        self._last_alert_time[alert_type] = current_time
        logger.warning(message, tag="metrics_alert")
    
    def _collect_system_metrics(self) -> Dict[str, float]:
        """
        收集系统资源使用情况
        
        Returns:
            Dict[str, float]: 系统资源指标字典，包含：
            - cpu_percent: CPU 使用率（百分比）
            - memory_percent: 内存使用率（百分比）
            - memory_used_mb: 内存使用量（MB）
            - network_sent_mb: 网络发送量（MB）
            - network_recv_mb: 网络接收量（MB）
        """
        metrics = {}
        
        try:
            import psutil
            
            # CPU 使用率
            cpu_percent = psutil.cpu_percent(interval=0.1)
            metrics["cpu_percent"] = cpu_percent
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            metrics["memory_percent"] = memory.percent
            metrics["memory_used_mb"] = memory.used / (1024 * 1024)
            
            # 网络 I/O（累计值）
            net_io = psutil.net_io_counters()
            metrics["network_sent_mb"] = net_io.bytes_sent / (1024 * 1024)
            metrics["network_recv_mb"] = net_io.bytes_recv / (1024 * 1024)
            
        except ImportError:
            logger.warning(
                "psutil 库未安装，无法收集系统资源指标。"
                "请运行: uv add psutil",
                tag="metrics"
            )
        except Exception as e:
            logger.warning(f"收集系统资源指标失败: {e}", tag="metrics")
        
        return metrics
    
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
