#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : config_example.py
@Date       : 2025/12/18
@Author     : Kiro AI Assistant
@Email      : -
@Software   : PyCharm
@Description: 示例脚本的共享配置
"""

# SimNow 7x24 环境配置
CONFIG = {
    "user_id": "",
    "password": "",
    "config_path": "./config/config_td.yaml"
}

# 策略参数
STRATEGY_PARAMS = {
    "symbol": "rb2605",           # 交易合约
    "fast_period": 5,             # 快速均线周期
    "slow_period": 20,            # 慢速均线周期
    "volume": 1,                  # 每次交易手数
    "check_interval": 1.0,        # 行情检查间隔（秒）
}

# 合约信息（推荐方式，避免 CTP 查询可能失败）
INSTRUMENT_INFO = {
    "rb2605": {"VolumeMultiple": 10},  # rb 螺纹钢的合约乘数是 10
}
