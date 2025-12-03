#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : main.py
@Date       : 2025/12/3 14:57
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: run
"""
import logging
import sys

import uvicorn

# 支持两种导入方式：相对导入（作为模块）和绝对导入（直接运行）
try:
    from .utils import GlobalConfig
except ImportError:
    from src.utils import GlobalConfig


def init_log():
    root = logging.getLogger()
    root.setLevel(GlobalConfig.LogLevel)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(GlobalConfig.LogLevel)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)


async def run(config_file_path: str, app_type: str):
    GlobalConfig.load_config(config_file_path)
    init_log()

    app: str = ""
    if app_type == "td":
        logging.info("start td app")
        app = "src.apps:td_app"
    elif app_type == "md":
        logging.info("start md app")
        app = "src.apps:md_app"
    elif app_type == "dev":
        logging.info("start dev app")
        app = "src.apps:dev_app"
    else:
        logging.error("error app type: %s", app_type)
        exit(1)

    server_config = uvicorn.Config(app, host=GlobalConfig.Host, port=GlobalConfig.Port, log_level="info")
    server = uvicorn.Server(server_config)
    await server.serve()
