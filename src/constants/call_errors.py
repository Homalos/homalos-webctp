#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : call_errors.py
@Date       : 2025/12/3 13:58
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: 错误码定义
"""
from typing import Any


class CallError(object):

    _errors: dict[int, Any] = {}

    def __init__(self, ret: int, error_id: int, error_message: str):
        self._ret = ret
        self._error_id = error_id
        self._error_message = error_message

    def to_rsp_info(self) -> dict[str, Any]:
        """
        将错误信息转换为CTP响应信息格式

        Returns:
            dict[str, Any]: 包含错误ID和错误消息的字典，格式为:
                - ErrorID: 错误代码
                - ErrorMsg: 错误描述信息
        """
        return {
            "ErrorID": self._error_id,
            "ErrorMsg": self._error_message
        }

    @classmethod
    def register_error(cls, ret: int, error_id: int, error_message: str):
        """
        注册错误映射关系

        将CTP返回码映射到对应的错误ID和错误消息

        Args:
            ret: CTP原始返回码
            error_id: 自定义错误代码
            error_message: 错误描述信息
        """
        cls._errors[ret] = CallError(ret, error_id, error_message)

    @classmethod
    def get_error(cls, ret: int) -> Any:
        """
        根据CTP原始返回码获取对应的错误信息对象

        Args:
            ret: CTP原始返回码

        Returns:
            CallError: 对应的错误信息对象，包含错误代码和描述信息
        """
        return cls._errors[ret]

    @classmethod
    def get_rsp_info(cls, ret: int) -> dict[str, Any]:
        """
        根据CTP原始返回码获取响应信息格式的错误信息

        Args:
            ret: CTP原始返回码

        Returns:
            dict[str, Any]: 包含错误ID和错误消息的字典，格式为:
                - ErrorID: 错误代码
                - ErrorMsg: 错误描述信息
        """
        return cls._errors[ret].to_rsp_info()


CallError.register_error(0, 0, "成功")
CallError.register_error(-1, -1, "CTP:请求失败")
CallError.register_error(-2, -2, "CTP:未处理请求超过许可数")
CallError.register_error(-3, -3, "CTP:每秒发送请求数超过许可数")
CallError.register_error(404, -404, "Not implemented")
CallError.register_error(401, -401, "未登录")
CallError.register_error(400, -400, "参数有误")
CallError.register_error(500, -500, "内部错误")
