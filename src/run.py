#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : main.py
@Date       : 2025/12/3 14:57
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: 运行CTP应用服务
"""
import uvicorn

from .utils.log import logger

# 支持两种导入方式：相对导入（作为模块）和绝对导入（直接运行）
try:
    from .utils import GlobalConfig
except ImportError:
    from src.utils import GlobalConfig


async def run(config_file_path: str, app_type: str):
    """
    运行CTP应用服务

    根据指定的应用类型启动对应的CTP交易或行情服务

    Args:
        config_file_path: 配置文件路径
        app_type: 应用类型，支持以下值：
            - "td": 交易服务
            - "md": 行情服务
            - "dev": 开发测试服务

    Returns:
        None

    Raises:
        SystemExit: 当应用类型不支持时退出程序
    """
    GlobalConfig.load_config(config_file_path)

    app: str = ""
    if app_type == "td":
        logger.info("start td app")
        app = "src.apps:td_app"
    elif app_type == "md":
        logger.info("start md app")
        app = "src.apps:md_app"
    elif app_type == "dev":
        logger.info("start dev app")
        app = "src.apps:dev_app"
    else:
        logger.error("error app type: %s", app_type)
        exit(1)

    server_config = uvicorn.Config(app, host=GlobalConfig.Host, port=GlobalConfig.Port, log_level="info")
    server = uvicorn.Server(server_config)
    await server.serve()
