#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : test_metrics.py
@Date       : 2025/12/13 00:00
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: MetricsCollector 单元测试
"""

import pytest
import asyncio
import time
from unittest.mock import patch

from src.utils.metrics import MetricsCollector
from src.utils.config import MetricsConfig


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def metrics_config():
    """创建测试用的指标配置"""
    return MetricsConfig(
        enabled=True,
        report_interval=60,
        latency_buckets=[10, 50, 100, 200, 500, 1000],
        sample_rate=1.0,
    )


@pytest.fixture
def metrics_collector(metrics_config):
    """创建 MetricsCollector 实例"""
    return MetricsCollector(config=metrics_config)


@pytest.fixture
def disabled_metrics_config():
    """创建禁用的指标配置"""
    return MetricsConfig(
        enabled=False,
        report_interval=60,
        sample_rate=1.0,
    )


@pytest.fixture
def disabled_metrics_collector(disabled_metrics_config):
    """创建禁用的 MetricsCollector 实例"""
    return MetricsCollector(config=disabled_metrics_config)


# ============================================================================
# TestMetricsCollectorLatency - 延迟指标测试
# ============================================================================


class TestMetricsCollectorLatency:
    """MetricsCollector 延迟指标测试"""

    def test_record_latency_basic(self, metrics_collector):
        """测试基本延迟记录"""
        collector = metrics_collector
        
        # 记录延迟
        collector.record_latency("test_latency", 50.0)
        collector.record_latency("test_latency", 100.0)
        collector.record_latency("test_latency", 150.0)
        
        # 验证数据已记录
        assert "test_latency" in collector._latencies
        assert len(collector._latencies["test_latency"]) == 3
        
        # 验证数据内容
        latencies = [lat for _, lat in collector._latencies["test_latency"]]
        assert 50.0 in latencies
        assert 100.0 in latencies
        assert 150.0 in latencies

    def test_record_latency_with_sampling(self):
        """测试采样率控制"""
        # 创建采样率为 0 的配置
        config = MetricsConfig(enabled=True, sample_rate=0.0)
        collector = MetricsCollector(config=config)
        
        # 记录延迟（应该被采样率过滤）
        for i in range(100):
            collector.record_latency("test_latency", float(i))
        
        # 验证没有数据被记录（采样率为 0）
        assert len(collector._latencies.get("test_latency", [])) == 0
        
        # 创建采样率为 1.0 的配置
        config_full = MetricsConfig(enabled=True, sample_rate=1.0)
        collector_full = MetricsCollector(config=config_full)
        
        # 记录延迟（应该全部记录）
        for i in range(10):
            collector_full.record_latency("test_latency", float(i))
        
        # 验证所有数据都被记录
        assert len(collector_full._latencies["test_latency"]) == 10

    def test_record_latency_when_disabled(self, disabled_metrics_collector):
        """测试禁用时不记录"""
        collector = disabled_metrics_collector
        
        # 记录延迟
        collector.record_latency("test_latency", 50.0)
        
        # 验证没有数据被记录
        assert "test_latency" not in collector._latencies or len(collector._latencies["test_latency"]) == 0

    def test_get_percentiles_basic(self, metrics_collector):
        """测试基本百分位数计算"""
        collector = metrics_collector
        
        # 记录一系列延迟数据
        latencies = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
        for lat in latencies:
            collector.record_latency("test_latency", lat)
        
        # 获取百分位数
        percentiles = collector.get_percentiles("test_latency")
        
        # 验证返回了正确的百分位数
        assert 0.5 in percentiles  # P50
        assert 0.95 in percentiles  # P95
        assert 0.99 in percentiles  # P99
        
        # 验证 P50 大约是中位数
        assert 50.0 <= percentiles[0.5] <= 60.0
        
        # 验证 P95 接近高值
        assert percentiles[0.95] >= 90.0
        
        # 验证 P99 接近最大值
        assert percentiles[0.99] >= 95.0

    def test_get_percentiles_insufficient_data(self, metrics_collector):
        """测试数据不足时返回空字典"""
        collector = metrics_collector
        
        # 只记录一个数据点
        collector.record_latency("test_latency", 50.0)
        
        # 获取百分位数（数据不足，应返回空字典）
        percentiles = collector.get_percentiles("test_latency")
        
        # 验证返回空字典
        assert percentiles == {}

    def test_get_percentiles_custom_percentiles(self, metrics_collector):
        """测试自定义百分位数"""
        collector = metrics_collector
        
        # 记录数据
        for i in range(100):
            collector.record_latency("test_latency", float(i))
        
        # 获取自定义百分位数
        custom_percentiles = [0.25, 0.5, 0.75, 0.9]
        percentiles = collector.get_percentiles("test_latency", custom_percentiles)
        
        # 验证返回了所有请求的百分位数
        assert 0.25 in percentiles
        assert 0.5 in percentiles
        assert 0.75 in percentiles
        assert 0.9 in percentiles
        
        # 验证百分位数的相对大小关系
        assert percentiles[0.25] < percentiles[0.5]
        assert percentiles[0.5] < percentiles[0.75]
        assert percentiles[0.75] < percentiles[0.9]

    def test_get_percentiles_nonexistent_metric(self, metrics_collector):
        """测试不存在的指标"""
        collector = metrics_collector
        
        # 获取不存在的指标的百分位数
        percentiles = collector.get_percentiles("nonexistent_metric")
        
        # 验证返回空字典
        assert percentiles == {}


# ============================================================================
# TestMetricsCollectorCounter - 计数器测试
# ============================================================================


class TestMetricsCollectorCounter:
    """MetricsCollector 计数器测试"""

    def test_record_counter_basic(self, metrics_collector):
        """测试基本计数器累加"""
        collector = metrics_collector
        
        # 记录计数器
        collector.record_counter("test_counter")
        collector.record_counter("test_counter")
        collector.record_counter("test_counter")
        
        # 验证计数器值
        assert collector._counters["test_counter"] == 3

    def test_record_counter_custom_value(self, metrics_collector):
        """测试自定义计数值"""
        collector = metrics_collector
        
        # 记录自定义计数值
        collector.record_counter("test_counter", 5)
        collector.record_counter("test_counter", 10)
        collector.record_counter("test_counter", 3)
        
        # 验证计数器累加
        assert collector._counters["test_counter"] == 18

    def test_record_counter_multiple_increments(self, metrics_collector):
        """测试多次累加"""
        collector = metrics_collector
        
        # 多次累加
        for i in range(100):
            collector.record_counter("test_counter", 1)
        
        # 验证累加结果
        assert collector._counters["test_counter"] == 100

    def test_record_counter_when_disabled(self, disabled_metrics_collector):
        """测试禁用时不记录"""
        collector = disabled_metrics_collector
        
        # 记录计数器
        collector.record_counter("test_counter", 10)
        
        # 验证没有记录
        assert collector._counters.get("test_counter", 0) == 0


# ============================================================================
# TestMetricsCollectorGauge - 瞬时值测试
# ============================================================================


class TestMetricsCollectorGauge:
    """MetricsCollector 瞬时值测试"""

    def test_record_gauge_basic(self, metrics_collector):
        """测试基本瞬时值记录"""
        collector = metrics_collector
        
        # 记录瞬时值
        collector.record_gauge("test_gauge", 42.5)
        
        # 验证瞬时值
        assert collector._gauges["test_gauge"] == 42.5

    def test_record_gauge_update(self, metrics_collector):
        """测试瞬时值更新"""
        collector = metrics_collector
        
        # 记录初始值
        collector.record_gauge("test_gauge", 10.0)
        assert collector._gauges["test_gauge"] == 10.0
        
        # 更新值
        collector.record_gauge("test_gauge", 20.0)
        assert collector._gauges["test_gauge"] == 20.0
        
        # 再次更新
        collector.record_gauge("test_gauge", 30.0)
        assert collector._gauges["test_gauge"] == 30.0

    def test_record_gauge_when_disabled(self, disabled_metrics_collector):
        """测试禁用时不记录"""
        collector = disabled_metrics_collector
        
        # 记录瞬时值
        collector.record_gauge("test_gauge", 42.5)
        
        # 验证没有记录
        assert "test_gauge" not in collector._gauges


# ============================================================================
# TestMetricsCollectorSlidingWindow - 滑动窗口测试
# ============================================================================


class TestMetricsCollectorSlidingWindow:
    """MetricsCollector 滑动窗口测试"""

    def test_sliding_window_cleanup(self, metrics_collector):
        """测试旧数据自动清理"""
        collector = metrics_collector
        
        # 模拟时间推进
        with patch('time.time') as mock_time:
            # 当前时间
            current_time = 1000.0
            mock_time.return_value = current_time
            
            # 记录一些数据
            collector.record_latency("test_latency", 50.0)
            collector.record_latency("test_latency", 60.0)
            
            # 验证数据已记录
            assert len(collector._latencies["test_latency"]) == 2
            
            # 时间推进到窗口边界之外（超过 600 秒）
            mock_time.return_value = current_time + 601
            
            # 记录新数据，触发清理
            collector.record_latency("test_latency", 70.0)
            
            # 验证旧数据已被清理
            assert len(collector._latencies["test_latency"]) == 1
            
            # 验证保留的是新数据
            latencies = [lat for _, lat in collector._latencies["test_latency"]]
            assert 70.0 in latencies
            assert 50.0 not in latencies
            assert 60.0 not in latencies

    def test_sliding_window_boundary(self, metrics_collector):
        """测试窗口边界情况"""
        collector = metrics_collector
        
        with patch('time.time') as mock_time:
            current_time = 1000.0
            mock_time.return_value = current_time
            
            # 记录数据
            collector.record_latency("test_latency", 50.0)
            
            # 时间推进到刚好在窗口内（599 秒）
            mock_time.return_value = current_time + 599
            collector.record_latency("test_latency", 60.0)
            
            # 验证旧数据仍然保留
            assert len(collector._latencies["test_latency"]) == 2
            
            # 时间推进到刚好超出窗口（601 秒）
            mock_time.return_value = current_time + 601
            collector.record_latency("test_latency", 70.0)
            
            # 验证旧数据被清理
            assert len(collector._latencies["test_latency"]) == 2  # 60.0 和 70.0
            latencies = [lat for _, lat in collector._latencies["test_latency"]]
            assert 50.0 not in latencies

    def test_sliding_window_multiple_metrics(self, metrics_collector):
        """测试多个指标的独立窗口"""
        collector = metrics_collector
        
        with patch('time.time') as mock_time:
            current_time = 1000.0
            mock_time.return_value = current_time
            
            # 记录两个不同指标的数据
            collector.record_latency("metric1", 50.0)
            collector.record_latency("metric2", 100.0)
            
            # 时间推进
            mock_time.return_value = current_time + 601
            
            # 只记录 metric1 的新数据
            collector.record_latency("metric1", 60.0)
            
            # 验证 metric1 的旧数据被清理
            assert len(collector._latencies["metric1"]) == 1
            latencies1 = [lat for _, lat in collector._latencies["metric1"]]
            assert 60.0 in latencies1
            assert 50.0 not in latencies1
            
            # 验证 metric2 的数据仍然保留（没有触发清理）
            assert len(collector._latencies["metric2"]) == 1
            latencies2 = [lat for _, lat in collector._latencies["metric2"]]
            assert 100.0 in latencies2


# ============================================================================
# TestMetricsCollectorSummary - 摘要测试
# ============================================================================


class TestMetricsCollectorSummary:
    """MetricsCollector 摘要测试"""

    def test_get_summary_empty(self, metrics_collector):
        """测试空摘要"""
        collector = metrics_collector
        
        # 获取摘要
        summary = collector.get_summary()
        
        # 验证摘要结构
        assert "latencies" in summary
        assert "counters" in summary
        assert "gauges" in summary
        assert "timestamp" in summary
        
        # 验证所有部分都是空的
        assert summary["latencies"] == {}
        assert summary["counters"] == {}
        assert summary["gauges"] == {}

    def test_get_summary_with_data(self, metrics_collector):
        """测试包含数据的摘要"""
        collector = metrics_collector
        
        # 记录各种类型的数据
        for i in range(10):
            collector.record_latency("test_latency", float(i * 10))
        
        collector.record_counter("test_counter", 5)
        collector.record_counter("test_counter", 3)
        
        collector.record_gauge("test_gauge", 42.5)
        
        # 获取摘要
        summary = collector.get_summary()
        
        # 验证延迟数据
        assert "test_latency" in summary["latencies"]
        assert "percentiles" in summary["latencies"]["test_latency"]
        assert "count" in summary["latencies"]["test_latency"]
        assert summary["latencies"]["test_latency"]["count"] == 10
        
        # 验证计数器数据
        assert "test_counter" in summary["counters"]
        assert summary["counters"]["test_counter"] == 8
        
        # 验证瞬时值数据
        assert "test_gauge" in summary["gauges"]
        assert summary["gauges"]["test_gauge"] == 42.5

    def test_get_summary_structure(self, metrics_collector):
        """测试摘要结构完整性"""
        collector = metrics_collector
        
        # 记录数据
        collector.record_latency("latency1", 50.0)
        collector.record_latency("latency1", 60.0)
        collector.record_latency("latency2", 100.0)
        collector.record_latency("latency2", 110.0)
        
        collector.record_counter("counter1", 1)
        collector.record_counter("counter2", 2)
        
        collector.record_gauge("gauge1", 10.0)
        collector.record_gauge("gauge2", 20.0)
        
        # 获取摘要
        summary = collector.get_summary()
        
        # 验证延迟指标数量
        assert len(summary["latencies"]) == 2
        
        # 验证计数器数量
        assert len(summary["counters"]) == 2
        
        # 验证瞬时值数量
        assert len(summary["gauges"]) == 2
        
        # 验证时间戳是合理的
        assert summary["timestamp"] > 0
        assert summary["timestamp"] <= time.time()


# ============================================================================
# TestMetricsCollectorReporting - 报告测试
# ============================================================================


class TestMetricsCollectorReporting:
    """MetricsCollector 报告测试"""

    @pytest.mark.asyncio
    async def test_start_reporting(self, metrics_collector):
        """测试启动报告"""
        collector = metrics_collector
        
        # 启动报告
        await collector.start_reporting(interval_seconds=1)
        
        # 验证报告任务已创建
        assert collector._report_task is not None
        assert not collector._report_task.done()
        
        # 停止报告
        await collector.stop_reporting()

    @pytest.mark.asyncio
    async def test_stop_reporting(self, metrics_collector):
        """测试停止报告"""
        collector = metrics_collector
        
        # 启动报告
        await collector.start_reporting(interval_seconds=1)
        
        # 验证任务正在运行
        assert collector._report_task is not None
        assert not collector._report_task.done()
        
        # 停止报告
        await collector.stop_reporting()
        
        # 验证任务已停止
        assert collector._report_task is None or collector._report_task.done()

    @pytest.mark.asyncio
    async def test_reporting_when_disabled(self, disabled_metrics_collector):
        """测试禁用时不启动报告"""
        collector = disabled_metrics_collector
        
        # 尝试启动报告
        await collector.start_reporting(interval_seconds=1)
        
        # 验证报告任务未创建
        assert collector._report_task is None

    @pytest.mark.asyncio
    async def test_reporting_interval(self, metrics_collector):
        """测试报告间隔"""
        collector = metrics_collector
        
        # 记录一些数据
        collector.record_latency("test_latency", 50.0)
        collector.record_counter("test_counter", 1)
        
        # 使用短间隔启动报告
        report_count = 0
        
        # Mock _report 方法来计数
        original_report = collector._report
        
        async def mock_report():
            nonlocal report_count
            report_count += 1
            await original_report()
        
        with patch.object(collector, '_report', side_effect=mock_report):
            await collector.start_reporting(interval_seconds=0.1)
            
            # 等待足够时间让报告执行几次
            try:
                await asyncio.wait_for(asyncio.sleep(0.3), timeout=1.0)
            except asyncio.TimeoutError:
                pass
            
            # 停止报告
            await collector.stop_reporting()
        
        # 验证报告被调用了至少 1 次（时序可能不稳定）
        assert report_count >= 1, f"期望至少 1 次报告，实际 {report_count} 次"

    @pytest.mark.asyncio
    async def test_restart_reporting(self, metrics_collector):
        """测试重启报告"""
        collector = metrics_collector
        
        # 第一次启动
        await collector.start_reporting(interval_seconds=1)
        first_task = collector._report_task
        
        # 第二次启动（应该先停止旧任务）
        await collector.start_reporting(interval_seconds=1)
        second_task = collector._report_task
        
        # 验证任务已更换
        assert first_task is not second_task
        assert first_task.done() or first_task.cancelled()
        assert not second_task.done()
        
        # 清理
        await collector.stop_reporting()




if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
