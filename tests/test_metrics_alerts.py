#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : test_metrics_alerts.py
@Date       : 2025/12/15 00:00
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: 测试性能告警功能
"""

import pytest
from unittest.mock import patch, MagicMock
from src.utils.metrics import MetricsCollector
from src.utils.config import MetricsConfig


@pytest.fixture
def metrics_config():
    """创建测试用的指标配置"""
    return MetricsConfig(
        enabled=True,
        report_interval=60,
        sample_rate=1.0,
        latency_warning_threshold_ms=100.0,
        cache_hit_rate_warning_threshold=50.0,
        cpu_warning_threshold=80.0,
        memory_warning_threshold=80.0,
    )


@pytest.fixture
def collector(metrics_config):
    """创建 MetricsCollector 实例"""
    return MetricsCollector(config=metrics_config)


class TestMetricsAlerts:
    """测试性能告警功能"""

    @pytest.mark.asyncio
    async def test_latency_alert_triggered(self, collector):
        """测试延迟超过阈值时触发告警"""
        # 记录多个超过阈值的延迟值
        for _ in range(10):
            collector.record_latency("test_latency", 150.0)  # 超过 100ms 阈值
        
        # 使用 patch 捕获 logger.warning 调用
        with patch('src.utils.metrics.logger') as mock_logger:
            await collector._report()
            
            # 验证告警被触发
            warning_calls = [
                call for call in mock_logger.warning.call_args_list
                if '延迟告警' in str(call)
            ]
            assert len(warning_calls) > 0, "延迟告警应该被触发"

    @pytest.mark.asyncio
    async def test_latency_alert_not_triggered(self, collector):
        """测试延迟未超过阈值时不触发告警"""
        # 记录多个未超过阈值的延迟值
        for _ in range(10):
            collector.record_latency("test_latency", 50.0)  # 未超过 100ms 阈值
        
        # 使用 patch 捕获 logger.warning 调用
        with patch('src.utils.metrics.logger') as mock_logger:
            await collector._report()
            
            # 验证告警未被触发
            warning_calls = [
                call for call in mock_logger.warning.call_args_list
                if '延迟告警' in str(call)
            ]
            assert len(warning_calls) == 0, "延迟告警不应该被触发"

    @pytest.mark.asyncio
    async def test_cache_hit_rate_alert_triggered(self, collector):
        """测试 Redis 命中率低于阈值时触发告警"""
        # 记录低命中率：30% (3 命中, 7 未命中)
        collector.record_counter("cache_hit", 3)
        collector.record_counter("cache_miss", 7)
        
        # 使用 patch 捕获 logger.warning 调用
        with patch('src.utils.metrics.logger') as mock_logger:
            await collector._report()
            
            # 验证告警被触发
            warning_calls = [
                call for call in mock_logger.warning.call_args_list
                if 'Redis 命中率告警' in str(call)
            ]
            assert len(warning_calls) > 0, "Redis 命中率告警应该被触发"

    @pytest.mark.asyncio
    async def test_cache_hit_rate_alert_not_triggered(self, collector):
        """测试 Redis 命中率高于阈值时不触发告警"""
        # 记录高命中率：80% (8 命中, 2 未命中)
        collector.record_counter("cache_hit", 8)
        collector.record_counter("cache_miss", 2)
        
        # 使用 patch 捕获 logger.warning 调用
        with patch('src.utils.metrics.logger') as mock_logger:
            await collector._report()
            
            # 验证告警未被触发
            warning_calls = [
                call for call in mock_logger.warning.call_args_list
                if 'Redis 命中率告警' in str(call)
            ]
            assert len(warning_calls) == 0, "Redis 命中率告警不应该被触发"

    @pytest.mark.asyncio
    async def test_cpu_alert_triggered(self, collector):
        """测试 CPU 使用率超过阈值时触发告警"""
        # Mock psutil 返回高 CPU 使用率
        mock_cpu_percent = MagicMock(return_value=90.0)  # 超过 80% 阈值
        
        with patch('psutil.cpu_percent', mock_cpu_percent):
            with patch('psutil.virtual_memory') as mock_memory:
                mock_memory.return_value = MagicMock(percent=50.0, used=1024*1024*1024)
                
                with patch('psutil.net_io_counters') as mock_net:
                    mock_net.return_value = MagicMock(bytes_sent=0, bytes_recv=0)
                    
                    with patch('src.utils.metrics.logger') as mock_logger:
                        await collector._report()
                        
                        # 验证告警被触发
                        warning_calls = [
                            call for call in mock_logger.warning.call_args_list
                            if 'CPU 使用率告警' in str(call)
                        ]
                        assert len(warning_calls) > 0, "CPU 使用率告警应该被触发"

    @pytest.mark.asyncio
    async def test_memory_alert_triggered(self, collector):
        """测试内存使用率超过阈值时触发告警"""
        # Mock psutil 返回高内存使用率
        mock_memory = MagicMock(percent=90.0, used=1024*1024*1024)  # 超过 80% 阈值
        
        with patch('psutil.cpu_percent', return_value=50.0):
            with patch('psutil.virtual_memory', return_value=mock_memory):
                with patch('psutil.net_io_counters') as mock_net:
                    mock_net.return_value = MagicMock(bytes_sent=0, bytes_recv=0)
                    
                    with patch('src.utils.metrics.logger') as mock_logger:
                        await collector._report()
                        
                        # 验证告警被触发
                        warning_calls = [
                            call for call in mock_logger.warning.call_args_list
                            if '内存使用率告警' in str(call)
                        ]
                        assert len(warning_calls) > 0, "内存使用率告警应该被触发"

    @pytest.mark.asyncio
    async def test_multiple_alerts_triggered(self, collector):
        """测试多个告警同时触发"""
        # 记录超过阈值的延迟
        for _ in range(10):
            collector.record_latency("test_latency", 150.0)
        
        # 记录低命中率
        collector.record_counter("cache_hit", 3)
        collector.record_counter("cache_miss", 7)
        
        # Mock 高 CPU 和内存使用率
        mock_memory = MagicMock(percent=90.0, used=1024*1024*1024)
        
        with patch('psutil.cpu_percent', return_value=90.0):
            with patch('psutil.virtual_memory', return_value=mock_memory):
                with patch('psutil.net_io_counters') as mock_net:
                    mock_net.return_value = MagicMock(bytes_sent=0, bytes_recv=0)
                    
                    with patch('src.utils.metrics.logger') as mock_logger:
                        await collector._report()
                        
                        # 验证所有告警都被触发
                        all_warnings = [str(call) for call in mock_logger.warning.call_args_list]
                        
                        assert any('延迟告警' in w for w in all_warnings), "延迟告警应该被触发"
                        assert any('Redis 命中率告警' in w for w in all_warnings), "Redis 命中率告警应该被触发"
                        assert any('CPU 使用率告警' in w for w in all_warnings), "CPU 使用率告警应该被触发"
                        assert any('内存使用率告警' in w for w in all_warnings), "内存使用率告警应该被触发"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
