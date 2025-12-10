#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : config.py
@Date       : 2025/12/3 14:55
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: config
"""
import os
import yaml
from pathlib import Path

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
        """
        with open(config_file_path) as f:
            config = yaml.safe_load(f)
            cls.TdFrontAddress = config.get("TdFrontAddress", "")
            cls.MdFrontAddress = config.get("MdFrontAddress", "")
            cls.BrokerID = config.get("BrokerID", "")
            cls.AuthCode = config.get("AuthCode", "")
            cls.AppID = config.get("AppID", "")
            cls.Host = config.get("Host", "0.0.0.0")
            cls.Port = config.get("Port", 8080)
            cls.LogLevel = config.get("LogLevel", "INFO")
            cls.ConFilePath = config.get("ConFilePath", "./con_file/")

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
