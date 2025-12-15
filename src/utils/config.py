#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : config.py
@Date       : 2025/12/3 14:55
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: 配置管理
"""

import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class CacheConfig:
    """Redis 缓存配置"""

    enabled: bool = False
    host: str = "localhost"
    port: int = 6379
    password: Optional[str] = None
    db: int = 0
    max_connections: int = 50
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0

    # TTL 配置
    market_snapshot_ttl: int = 60  # 行情快照 TTL（秒）
    market_tick_ttl: int = 5  # 实时 tick TTL（秒）
    order_ttl: int = 86400  # 订单 TTL（秒）


@dataclass
class MetricsConfig:
    """性能指标配置"""

    enabled: bool = True
    report_interval: int = 60  # 报告间隔（秒）
    latency_buckets: List[float] = field(
        default_factory=lambda: [10, 50, 100, 200, 500, 1000]
    )  # 延迟桶（毫秒）
    sample_rate: float = 1.0  # 采样率（0.0-1.0）
    
    # 告警阈值配置
    latency_warning_threshold_ms: float = 100.0  # 延迟告警阈值（毫秒）
    cache_hit_rate_warning_threshold: float = 50.0  # Redis 命中率告警阈值（百分比）
    cpu_warning_threshold: float = 80.0  # CPU 使用率告警阈值（百分比）
    memory_warning_threshold: float = 80.0  # 内存使用率告警阈值（百分比）


@dataclass
class StrategyConfig:
    """策略管理配置"""

    max_strategies: int = 10  # 最大策略数量
    default_max_memory_mb: int = 512  # 默认单策略最大内存（MB）
    default_max_cpu_percent: float = 50.0  # 默认单策略最大CPU使用率（%）


class GlobalConfig(object):
    TdFrontAddress: str
    MdFrontAddress: str
    BrokerID: str
    AuthCode: str
    AppID: str
    Host: str
    Port: int
    LogLevel: str
    ConFilePath: str
    Token: str
    HeartbeatInterval: float
    HeartbeatTimeout: float

    # 新增配置对象
    Cache: CacheConfig
    Metrics: MetricsConfig
    Strategy: StrategyConfig

    @classmethod
    def load_config(cls, config_file_path: str):
        """
        加载并解析 YAML 配置文件，设置类属性

        从指定路径读取 YAML 配置文件，解析后将配置值赋给类属性。如果某些配置项不存在，
        会使用默认值。同时确保连接文件路径(ConFilePath)以斜杠结尾且目录存在。

        Args:
            config_file_path (str): YAML 配置文件的路径

        设置以下类属性:
            TdFrontAddress: 交易前置地址
            MdFrontAddress: 行情前置地址
            BrokerID: 经纪商代码
            AuthCode: 认证码
            AppID: 应用ID
            Host: 服务主机地址，默认'0.0.0.0'
            Port: 服务端口，默认8080
            LogLevel: 日志级别，默认'INFO'
            ConFilePath: 连接文件路径，默认'./con_file/'
            Cache: Redis 缓存配置
            Metrics: 性能监控配置
            Strategy: 策略管理配置
        """
        with open(config_file_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)
            cls.TdFrontAddress = os.environ.get(
                "WEBCTP_TD_ADDRESS", config.get("TdFrontAddress", "")
            )
            cls.MdFrontAddress = os.environ.get(
                "WEBCTP_MD_ADDRESS", config.get("MdFrontAddress", "")
            )
            cls.BrokerID = os.environ.get(
                "WEBCTP_BROKER_ID", config.get("BrokerID", "")
            )
            cls.AuthCode = os.environ.get(
                "WEBCTP_AUTH_CODE", config.get("AuthCode", "")
            )
            cls.AppID = os.environ.get("WEBCTP_APP_ID", config.get("AppID", ""))
            cls.Host = os.environ.get("WEBCTP_HOST", config.get("Host", "0.0.0.0"))

            cls.Port = config.get("Port", 8080)
            cls.LogLevel = config.get("LogLevel", "INFO")
            cls.ConFilePath = config.get("ConFilePath", "./con_file/")
            # 优先从环境变量获取 Token，其次从配置文件获取，如果都没有则为空字符串（意味着无鉴权或默认行为，但在生产环境应强制）
            cls.Token = os.environ.get("WEBCTP_TOKEN", config.get("Token", ""))
            # Heartbeat configuration
            cls.HeartbeatInterval = float(
                os.environ.get(
                    "WEBCTP_HEARTBEAT_INTERVAL", config.get("HeartbeatInterval", 30.0)
                )
            )
            cls.HeartbeatTimeout = float(
                os.environ.get(
                    "WEBCTP_HEARTBEAT_TIMEOUT", config.get("HeartbeatTimeout", 60.0)
                )
            )

            # 加载 Redis 缓存配置（可选）
            redis_config = config.get("Redis", {})
            cls.Cache = CacheConfig(
                enabled=bool(
                    os.environ.get(
                        "WEBCTP_REDIS_ENABLED", redis_config.get("Enabled", False)
                    )
                ),
                host=os.environ.get(
                    "WEBCTP_REDIS_HOST", redis_config.get("Host", "localhost")
                ),
                port=int(
                    os.environ.get("WEBCTP_REDIS_PORT", redis_config.get("Port", 6379))
                ),
                password=os.environ.get(
                    "WEBCTP_REDIS_PASSWORD", redis_config.get("Password")
                ),
                db=int(os.environ.get("WEBCTP_REDIS_DB", redis_config.get("DB", 0))),
                max_connections=int(redis_config.get("MaxConnections", 50)),
                socket_timeout=float(redis_config.get("SocketTimeout", 5.0)),
                socket_connect_timeout=float(
                    redis_config.get("SocketConnectTimeout", 5.0)
                ),
                market_snapshot_ttl=int(redis_config.get("MarketSnapshotTTL", 60)),
                market_tick_ttl=int(redis_config.get("MarketTickTTL", 5)),
                order_ttl=int(redis_config.get("OrderTTL", 86400)),
            )

            # 加载性能监控配置（可选）
            metrics_config = config.get("Metrics", {})
            cls.Metrics = MetricsConfig(
                enabled=bool(
                    os.environ.get(
                        "WEBCTP_METRICS_ENABLED", metrics_config.get("Enabled", True)
                    )
                ),
                report_interval=int(
                    os.environ.get(
                        "WEBCTP_METRICS_INTERVAL",
                        metrics_config.get("ReportInterval", 60),
                    )
                ),
                sample_rate=float(metrics_config.get("SampleRate", 1.0)),
                latency_warning_threshold_ms=float(
                    os.environ.get(
                        "WEBCTP_METRICS_LATENCY_WARNING_THRESHOLD",
                        metrics_config.get("LatencyWarningThresholdMs", 100.0),
                    )
                ),
                cache_hit_rate_warning_threshold=float(
                    os.environ.get(
                        "WEBCTP_METRICS_CACHE_HIT_RATE_WARNING_THRESHOLD",
                        metrics_config.get("CacheHitRateWarningThreshold", 50.0),
                    )
                ),
                cpu_warning_threshold=float(
                    os.environ.get(
                        "WEBCTP_METRICS_CPU_WARNING_THRESHOLD",
                        metrics_config.get("CpuWarningThreshold", 80.0),
                    )
                ),
                memory_warning_threshold=float(
                    os.environ.get(
                        "WEBCTP_METRICS_MEMORY_WARNING_THRESHOLD",
                        metrics_config.get("MemoryWarningThreshold", 80.0),
                    )
                ),
            )

            # 加载策略管理配置（可选）
            strategy_config = config.get("Strategy", {})
            cls.Strategy = StrategyConfig(
                max_strategies=int(strategy_config.get("MaxStrategies", 10)),
                default_max_memory_mb=int(
                    strategy_config.get("DefaultMaxMemoryMB", 512)
                ),
                default_max_cpu_percent=float(
                    strategy_config.get("DefaultMaxCPUPercent", 50.0)
                ),
            )

        if not cls.ConFilePath.endswith("/"):
            cls.ConFilePath = cls.ConFilePath + "/"

        if not os.path.exists(cls.ConFilePath):
            os.makedirs(cls.ConFilePath)

    @classmethod
    def get_con_file_path(cls, name: str) -> str:
        """
        获取连接文件的完整路径

        Args:
            name: 连接文件名

        Returns:
            str: 连接文件的完整路径
        """
        path = os.path.join(cls.ConFilePath, name)
        return path


if __name__ == "__main__":
    config_path = Path(__file__).parent.parent.parent / "config" / "config.sample.yaml"
    GlobalConfig.load_config(str(config_path))
    print(GlobalConfig.TdFrontAddress, type(GlobalConfig.TdFrontAddress))
    print(GlobalConfig.MdFrontAddress, type(GlobalConfig.MdFrontAddress))
    print(GlobalConfig.BrokerID, type(GlobalConfig.BrokerID))
    print(GlobalConfig.AuthCode, type(GlobalConfig.AuthCode))
    print(GlobalConfig.AppID, type(GlobalConfig.AppID))
    print(GlobalConfig.Host, type(GlobalConfig.Host))
    print(GlobalConfig.Port, type(GlobalConfig.Port))
    print(GlobalConfig.LogLevel, type(GlobalConfig.LogLevel))
    print(GlobalConfig.ConFilePath, type(GlobalConfig.ConFilePath))
