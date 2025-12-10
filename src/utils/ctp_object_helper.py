#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : ctp_object_helper.py
@Date       : 2025/12/3 14:50
@Author     : Lumosylva
@Email      : donnymoving@gmail.com
@Software   : PyCharm
@Description: CTP 对象辅助函数
"""
class CTPObjectHelper(object):

    exclude_attrs = ["thisown"]

    @staticmethod
    def object_to_dict(obj: object, typ: any) -> dict[str, any]:
        """
        将对象转换为字典，过滤Python内置属性和exclude_attrs中的属性。

        该方法会遍历对象的所有属性，排除以下属性：
        - 以双下划线开头的方法（Python内置方法）
        - exclude_attrs列表中定义的排除属性

        Args:
            obj: 要转换的对象实例，如果为None则返回空字典
            typ: 对象类型，用于获取属性列表

        Returns:
            包含对象属性键值对的字典，键为属性名，值为属性值
        """
        data = {}
        if obj:
            # filter python built-in attributes
            attrs = list(filter(lambda x: not (x.startswith("__") or x in CTPObjectHelper.exclude_attrs), dir(typ)))
            for attr in attrs:
                data[attr] = obj.__getattribute__(attr)
        return data

    @staticmethod
    def dict_to_object(data: dict[str, any], obj: object) -> None:
        """
        将字典数据映射到对象的属性

        通过遍历字典的键值对，将每个键对应的值设置到对象的同名属性上

        Args:
            data: 包含属性名和对应值的字典
            obj: 要设置属性的目标对象

        Returns:
            None: 此方法直接修改传入的对象，不返回任何值
        """
        for attr, value in data.items():
            obj.__setattr__(attr, value)

    @staticmethod
    def build_response_dict(
            message_type: str,
            rsp_info: object = None,
            request_id: int = None,
            is_last: bool = None
    ) -> dict[str, any]:
        """
        构建标准的响应字典结构

        用于将CTP API的响应信息转换为统一的字典格式，便于后续处理和序列化。

        Args:
            message_type: 消息类型，标识响应消息的类别
            rsp_info: 响应信息对象，包含错误代码和错误消息，可选参数
            request_id: 请求ID，用于匹配请求和响应，可选参数
            is_last: 标识是否为最后一条响应，可选参数

        Returns:
            dict[str, any]: 标准化响应字典，包含以下字段：
                - MsgType: 消息类型
                - RspInfo: 响应信息字典（包含ErrorID和ErrorMsg），可为None
                - RequestID: 请求ID（如果提供了request_id）
                - IsLast: 是否最后一条标志（如果提供了is_last）
        """
        response = {
            "MsgType": message_type,
            "RspInfo": None,
        }
        if request_id:
            response["RequestID"] = request_id
        if is_last:
            response["IsLast"] = is_last
        if rsp_info:
            response["RspInfo"] = {
                "ErrorID": rsp_info.ErrorID,
                "ErrorMsg": rsp_info.ErrorMsg
            }
        return response

    @staticmethod
    def extract_request(request_dict: dict[str, any], request_field_name: str, request_type):
        """
        从请求字典中提取特定请求对象和请求ID

        Args:
            request_dict: 包含请求数据的字典
            request_field_name: 请求对象在字典中的字段名
            request_type: 请求对象的类型

        Returns:
            tuple: (请求对象实例, 请求ID)
        """
        req = request_type()
        CTPObjectHelper.dict_to_object(request_dict[request_field_name], req)
        return (req, request_dict["RequestID"])
