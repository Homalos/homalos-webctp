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
    socket_timeout: float = 2.0  # 优化：本地部署推荐 2.0 秒
    socket_connect_timeout: float = 2.0  # 优化：本地部署推荐 2.0 秒

    # TTL 配置
    market_snapshot_ttl: int = 30  # 优化：行情快照 TTL 30 秒，减少过期数据
    market_tick_ttl: int = 5  # 实时 tick TTL（秒）
    order_ttl: int = 86400  # 订单 TTL（秒）

    def validate(self) -> None:
        """
        验证配置参数的合理性
        
        Raises:
            ValueError: 配置参数不合理时抛出
        """
        if self.socket_timeout <= 0:
            raise ValueError(f"socket_timeout 必须大于 0，当前值: {self.socket_timeout}")
        
        if self.socket_connect_timeout <= 0:
            raise ValueError(f"socket_connect_timeout 必须大于 0，当前值: {self.socket_connect_timeout}")
        
        if self.max_connections <= 0:
            raise ValueError(f"max_connections 必须大于 0，当前值: {self.max_connections}")
        
        # 性能优化建议
        if self.socket_timeout > 3.0:
            from loguru import logger
            logger.warning(
                f"Redis socket_timeout 设置为 {self.socket_timeout} 秒，"
                f"对于本地部署建议设置为 1-2 秒以加快降级响应"
            )
        
        if self.market_snapshot_ttl > 60:
            from loguru import logger
            logger.warning(
                f"行情快照 TTL 设置为 {self.market_snapshot_ttl} 秒，"
                f"对于高频交易建议设置为 30 秒以减少过期数据"
            )


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


@dataclass
class AlertsConfig:
    """告警配置"""

    # 延迟告警阈值（毫秒）
    order_p95_threshold: float = 150.0  # 订单延迟 P95 阈值
    market_p95_threshold: float = 80.0  # 行情延迟 P95 阈值

    # Redis 告警阈值
    redis_hit_rate_threshold: float = 0.65  # Redis 命中率阈值（65%）

    # 系统资源告警阈值
    cpu_threshold: float = 70.0  # CPU 使用率阈值（70%）
    memory_threshold: float = 80.0  # 内存使用率阈值（80%）

    # 告警频率控制
    min_interval: int = 300  # 同类告警最小间隔（秒）


@dataclass
class SyncApiConfig:
    """同步策略 API 配置"""

    # 连接超时配置
    connect_timeout: float = 30.0  # CTP 连接超时时间（秒）
    
    # 策略管理配置
    max_strategies: int = 10  # 最大并发策略数量
    
    # 操作超时配置
    quote_timeout: float = 5.0  # 行情查询默认超时（秒）
    position_timeout: float = 5.0  # 持仓查询默认超时（秒）
    order_timeout: float = 10.0  # 订单提交默认超时（秒）
    quote_update_timeout: float = 30.0  # 行情更新等待默认超时（秒）
    stop_timeout: float = 5.0  # 停止服务默认超时（秒）


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
    Alerts: AlertsConfig
    SyncApi: SyncApiConfig

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
                socket_timeout=float(redis_config.get("SocketTimeout", 2.0)),  # 优化默认值
                socket_connect_timeout=float(
                    redis_config.get("SocketConnectTimeout", 2.0)  # 优化默认值
                ),
                market_snapshot_ttl=int(redis_config.get("MarketSnapshotTTL", 30)),  # 优化默认值
                market_tick_ttl=int(redis_config.get("MarketTickTTL", 5)),
                order_ttl=int(redis_config.get("OrderTTL", 86400)),
            )
            
            # 验证配置
            if cls.Cache.enabled:
                try:
                    cls.Cache.validate()
                except ValueError as e:
                    from loguru import logger
                    logger.error(f"Redis 配置验证失败: {e}")
                    raise

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

            # 加载告警配置（可选，从 alerts.yaml 或主配置文件）
            cls._load_alerts_config(config_file_path)

            # 加载同步策略 API 配置（可选）
            sync_api_config = config.get("SyncApi", {})
            cls.SyncApi = SyncApiConfig(
                connect_timeout=float(
                    os.environ.get(
                        "WEBCTP_SYNC_API_CONNECT_TIMEOUT",
                        sync_api_config.get("ConnectTimeout", 30.0),
                    )
                ),
                max_strategies=int(
                    os.environ.get(
                        "WEBCTP_SYNC_API_MAX_STRATEGIES",
                        sync_api_config.get("MaxStrategies", 10),
                    )
                ),
                quote_timeout=float(
                    os.environ.get(
                        "WEBCTP_SYNC_API_QUOTE_TIMEOUT",
                        sync_api_config.get("QuoteTimeout", 5.0),
                    )
                ),
                position_timeout=float(
                    os.environ.get(
                        "WEBCTP_SYNC_API_POSITION_TIMEOUT",
                        sync_api_config.get("PositionTimeout", 5.0),
                    )
                ),
                order_timeout=float(
                    os.environ.get(
                        "WEBCTP_SYNC_API_ORDER_TIMEOUT",
                        sync_api_config.get("OrderTimeout", 10.0),
                    )
                ),
                quote_update_timeout=float(
                    os.environ.get(
                        "WEBCTP_SYNC_API_QUOTE_UPDATE_TIMEOUT",
                        sync_api_config.get("QuoteUpdateTimeout", 30.0),
                    )
                ),
                stop_timeout=float(
                    os.environ.get(
                        "WEBCTP_SYNC_API_STOP_TIMEOUT",
                        sync_api_config.get("StopTimeout", 5.0),
                    )
                ),
            )

        if not cls.ConFilePath.endswith("/"):
            cls.ConFilePath = cls.ConFilePath + "/"

        if not os.path.exists(cls.ConFilePath):
            os.makedirs(cls.ConFilePath)

    @classmethod
    def _load_alerts_config(cls, config_file_path: str):
        """
        加载告警配置

        优先从 config/alerts.yaml 加载，如果不存在则使用默认值

        Args:
            config_file_path: 主配置文件路径
        """
        # 尝试从 alerts.yaml 加载
        config_dir = Path(config_file_path).parent
        alerts_file = config_dir / "alerts.yaml"

        if alerts_file.exists():
            try:
                with open(alerts_file, encoding="utf-8") as f:
                    alerts_config = yaml.safe_load(f).get("Alerts", {})
            except Exception:
                alerts_config = {}
        else:
            alerts_config = {}

        # 解析配置
        latency_config = alerts_config.get("Latency", {})
        redis_config = alerts_config.get("Redis", {})
        system_config = alerts_config.get("System", {})
        rate_limit_config = alerts_config.get("RateLimit", {})

        cls.Alerts = AlertsConfig(
            order_p95_threshold=float(
                os.environ.get(
                    "WEBCTP_ALERT_ORDER_P95_THRESHOLD",
                    latency_config.get("OrderP95Threshold", 150.0),
                )
            ),
            market_p95_threshold=float(
                os.environ.get(
                    "WEBCTP_ALERT_MARKET_P95_THRESHOLD",
                    latency_config.get("MarketP95Threshold", 80.0),
                )
            ),
            redis_hit_rate_threshold=float(
                os.environ.get(
                    "WEBCTP_ALERT_REDIS_HIT_RATE_THRESHOLD",
                    redis_config.get("HitRateThreshold", 0.65),
                )
            ),
            cpu_threshold=float(
                os.environ.get(
                    "WEBCTP_ALERT_CPU_THRESHOLD",
                    system_config.get("CPUThreshold", 70.0),
                )
            ),
            memory_threshold=float(
                os.environ.get(
                    "WEBCTP_ALERT_MEMORY_THRESHOLD",
                    system_config.get("MemoryThreshold", 80.0),
                )
            ),
            min_interval=int(
                os.environ.get(
                    "WEBCTP_ALERT_MIN_INTERVAL",
                    rate_limit_config.get("MinInterval", 300),
                )
            ),
        )

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
