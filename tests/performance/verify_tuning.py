#!/usr/bin/env python
"""
@ProjectName: homalos-webctp
@FileName   : verify_tuning.py
@Date       : 2025/12/15 00:00
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: 性能调优配置验证脚本
"""

import argparse
import sys
from pathlib import Path

import yaml


class ConfigValidator:
    """配置验证器"""

    def __init__(self, config_path: str):
        """
        初始化配置验证器

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.issues: list[tuple[str, str, str]] = []  # (级别, 参数, 建议)
        self.optimizations: list[tuple[str, str, str]] = []  # (参数, 当前值, 推荐值)

    def _load_config(self) -> dict:
        """加载配置文件"""
        try:
            with open(self.config_path, encoding="utf-8") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"❌ 错误: 配置文件不存在: {self.config_path}")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"❌ 错误: 配置文件格式错误: {e}")
            sys.exit(1)

    def validate_redis_config(self) -> None:
        """验证 Redis 配置"""
        redis_config = self.config.get("Redis", {})

        if not redis_config:
            self.issues.append(
                ("INFO", "Redis", "Redis 未配置，系统将在无缓存模式下运行")
            )
            return

        enabled = redis_config.get("Enabled", False)
        if not enabled:
            self.issues.append(
                ("INFO", "Redis.Enabled", "Redis 已禁用，系统将在无缓存模式下运行")
            )
            return

        # 验证超时配置
        socket_timeout = redis_config.get("SocketTimeout", 5.0)
        if socket_timeout > 3.0:
            self.issues.append(
                (
                    "WARNING",
                    "Redis.SocketTimeout",
                    f"当前值 {socket_timeout}s 较大，本地部署建议设置为 2.0s",
                )
            )
            self.optimizations.append(
                ("Redis.SocketTimeout", f"{socket_timeout}s", "2.0s")
            )
        elif socket_timeout < 1.0:
            self.issues.append(
                (
                    "WARNING",
                    "Redis.SocketTimeout",
                    f"当前值 {socket_timeout}s 过小，可能导致频繁超时",
                )
            )

        socket_connect_timeout = redis_config.get("SocketConnectTimeout", 5.0)
        if socket_connect_timeout > 3.0:
            self.issues.append(
                (
                    "WARNING",
                    "Redis.SocketConnectTimeout",
                    f"当前值 {socket_connect_timeout}s 较大，本地部署建议设置为 2.0s",
                )
            )
            self.optimizations.append(
                ("Redis.SocketConnectTimeout", f"{socket_connect_timeout}s", "2.0s")
            )

        # 验证 TTL 配置
        market_snapshot_ttl = redis_config.get("MarketSnapshotTTL", 60)
        if market_snapshot_ttl > 60:
            self.issues.append(
                (
                    "WARNING",
                    "Redis.MarketSnapshotTTL",
                    f"当前值 {market_snapshot_ttl}s 较大，高频交易建议设置为 30s",
                )
            )
            self.optimizations.append(
                ("Redis.MarketSnapshotTTL", f"{market_snapshot_ttl}s", "30s")
            )
        elif market_snapshot_ttl < 10:
            self.issues.append(
                (
                    "WARNING",
                    "Redis.MarketSnapshotTTL",
                    f"当前值 {market_snapshot_ttl}s 过小，可能导致缓存命中率低",
                )
            )

        # 验证连接池配置
        max_connections = redis_config.get("MaxConnections", 50)
        if max_connections < 10:
            self.issues.append(
                (
                    "WARNING",
                    "Redis.MaxConnections",
                    f"当前值 {max_connections} 较小，可能导致连接等待",
                )
            )
        elif max_connections > 200:
            self.issues.append(
                (
                    "WARNING",
                    "Redis.MaxConnections",
                    f"当前值 {max_connections} 较大，可能造成资源浪费",
                )
            )

    def validate_metrics_config(self) -> None:
        """验证性能监控配置"""
        metrics_config = self.config.get("Metrics", {})

        if not metrics_config:
            self.issues.append(("INFO", "Metrics", "性能监控未配置，将使用默认值"))
            return

        enabled = metrics_config.get("Enabled", True)
        if not enabled:
            self.issues.append(("INFO", "Metrics.Enabled", "性能监控已禁用"))
            return

        # 验证采样率
        sample_rate = metrics_config.get("SampleRate", 1.0)
        if sample_rate > 0.7:
            self.issues.append(
                (
                    "WARNING",
                    "Metrics.SampleRate",
                    f"当前值 {sample_rate} 较高，生产环境建议设置为 0.5",
                )
            )
            self.optimizations.append(("Metrics.SampleRate", f"{sample_rate}", "0.5"))
        elif sample_rate < 0.1:
            self.issues.append(
                (
                    "WARNING",
                    "Metrics.SampleRate",
                    f"当前值 {sample_rate} 过低，可能遗漏性能问题",
                )
            )

        # 验证报告间隔
        report_interval = metrics_config.get("ReportInterval", 60)
        if report_interval < 30:
            self.issues.append(
                (
                    "WARNING",
                    "Metrics.ReportInterval",
                    f"当前值 {report_interval}s 过短，可能增加日志开销",
                )
            )
        elif report_interval > 300:
            self.issues.append(
                (
                    "INFO",
                    "Metrics.ReportInterval",
                    f"当前值 {report_interval}s 较长，可能延迟问题发现",
                )
            )

    def validate_strategy_config(self) -> None:
        """验证策略管理配置"""
        strategy_config = self.config.get("Strategy", {})

        if not strategy_config:
            self.issues.append(("INFO", "Strategy", "策略管理未配置，将使用默认值"))
            return

        # 验证最大策略数量
        max_strategies = strategy_config.get("MaxStrategies", 10)
        if max_strategies > 20:
            self.issues.append(
                (
                    "WARNING",
                    "Strategy.MaxStrategies",
                    f"当前值 {max_strategies} 较大，请确保服务器资源充足",
                )
            )
        elif max_strategies < 1:
            self.issues.append(
                (
                    "ERROR",
                    "Strategy.MaxStrategies",
                    f"当前值 {max_strategies} 无效，必须至少为 1",
                )
            )

        # 验证资源配额
        default_max_memory_mb = strategy_config.get("DefaultMaxMemoryMB", 512)
        if default_max_memory_mb < 128:
            self.issues.append(
                (
                    "WARNING",
                    "Strategy.DefaultMaxMemoryMB",
                    f"当前值 {default_max_memory_mb}MB 较小，策略可能内存不足",
                )
            )

    def validate(self) -> bool:
        """
        执行完整验证

        Returns:
            bool: 验证通过返回 True，否则返回 False
        """
        print(f"\n🔍 正在验证配置文件: {self.config_path}\n")

        self.validate_redis_config()
        self.validate_metrics_config()
        self.validate_strategy_config()

        # 输出验证结果
        has_errors = False
        has_warnings = False

        if self.issues:
            print("📋 配置检查结果:\n")
            for level, param, message in self.issues:
                if level == "ERROR":
                    print(f"  ❌ 错误 [{param}]: {message}")
                    has_errors = True
                elif level == "WARNING":
                    print(f"  ⚠️  警告 [{param}]: {message}")
                    has_warnings = True
                else:  # INFO
                    print(f"  ℹ️  信息 [{param}]: {message}")
        else:
            print("✅ 配置检查通过，未发现问题\n")

        # 输出优化建议
        if self.optimizations:
            print("\n💡 优化建议:\n")
            for param, current, recommended in self.optimizations:
                print(f"  • {param}:")
                print(f"    当前值: {current}")
                print(f"    推荐值: {recommended}")

        # 输出总结
        print("\n" + "=" * 60)
        if has_errors:
            print("❌ 验证失败: 发现配置错误，请修复后重试")
            return False
        if has_warnings:
            print("⚠️  验证通过: 发现配置警告，建议优化")
            return True
        print("✅ 验证通过: 配置符合最佳实践")
        return True

    def print_summary(self) -> None:
        """打印配置摘要"""
        print("\n" + "=" * 60)
        print("📊 配置摘要")
        print("=" * 60)

        # Redis 配置
        redis_config = self.config.get("Redis", {})
        if redis_config and redis_config.get("Enabled", False):
            print("\n🔴 Redis 缓存:")
            print("  • 状态: 已启用")
            print(f"  • 主机: {redis_config.get('Host', 'localhost')}")
            print(f"  • 端口: {redis_config.get('Port', 6379)}")
            print(f"  • 连接池: {redis_config.get('MaxConnections', 50)}")
            print(f"  • 操作超时: {redis_config.get('SocketTimeout', 5.0)}s")
            print(f"  • 连接超时: {redis_config.get('SocketConnectTimeout', 5.0)}s")
            print(f"  • 快照 TTL: {redis_config.get('MarketSnapshotTTL', 60)}s")
            print(f"  • Tick TTL: {redis_config.get('MarketTickTTL', 5)}s")
        else:
            print("\n🔴 Redis 缓存: 未启用")

        # 性能监控配置
        metrics_config = self.config.get("Metrics", {})
        if metrics_config and metrics_config.get("Enabled", True):
            print("\n📊 性能监控:")
            print("  • 状态: 已启用")
            print(f"  • 采样率: {metrics_config.get('SampleRate', 1.0)}")
            print(f"  • 报告间隔: {metrics_config.get('ReportInterval', 60)}s")
        else:
            print("\n📊 性能监控: 未启用")

        # 策略管理配置
        strategy_config = self.config.get("Strategy", {})
        if strategy_config:
            print("\n🎯 策略管理:")
            print(f"  • 最大策略数: {strategy_config.get('MaxStrategies', 10)}")
            print(f"  • 单策略内存: {strategy_config.get('DefaultMaxMemoryMB', 512)}MB")
            print(
                f"  • 单策略 CPU: {strategy_config.get('DefaultMaxCPUPercent', 50.0)}%"
            )
        else:
            print("\n🎯 策略管理: 使用默认配置")

        print("\n" + "=" * 60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="homalos-webctp 性能调优配置验证工具")
    parser.add_argument(
        "--config",
        type=str,
        default="config/config.sample.yaml",
        help="配置文件路径（默认: config/config.sample.yaml）",
    )
    parser.add_argument("--summary", action="store_true", help="显示配置摘要")

    args = parser.parse_args()

    # 验证配置文件路径
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"❌ 错误: 配置文件不存在: {config_path}")
        sys.exit(1)

    # 创建验证器并执行验证
    validator = ConfigValidator(str(config_path))
    success = validator.validate()

    # 显示配置摘要
    if args.summary:
        validator.print_summary()

    # 返回退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
