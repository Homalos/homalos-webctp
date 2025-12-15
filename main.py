#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : main.py
@Date       : 2025/12/3 15:40
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: 项目主入口
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.run import run
import anyio
import argparse


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser("webctp", description="WebCTP")
    arg_parser.add_argument("--config", type=str, default="./config/config_td.yaml", help="config file path")
    arg_parser.add_argument("--app_type", type=str, default="td", help="app type, td or md")
    parsed_args = arg_parser.parse_args(sys.argv[1:])
    
    try:
        anyio.run(run, parsed_args.config, parsed_args.app_type)
    except KeyboardInterrupt:
        print("\n服务已优雅关闭")
        sys.exit(0)
