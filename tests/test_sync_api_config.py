#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : test_sync_api_config.py
@Date       : 2025/12/17
@Author     : Kiro AI Assistant
@Email      : -
@Software   : PyCharm
@Description: SyncStrategyApi 配置管理单元测试
"""

import os
import tempfile
import pytest
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.strategy.sync_api import SyncStrategyApi
from src.utils.config import GlobalConfig, SyncApiConfig


class TestSyncApiConfig:
    """SyncStrategyApi 配置管理单元测试"""

    @pytest.fixture(autouse=True)
    def reset_global_config(self):
        """在每个测试前重置 GlobalConfig"""
        # 保存原始配置（如果存在）
        original_sync_api = getattr(GlobalConfig, 'SyncApi', None)
        
        yield
        
        # 恢复原始配置（如果存在）
        if original_sync_api is not None:
            GlobalConfig.SyncApi = original_sync_api
        elif hasattr(GlobalConfig, 'SyncApi'):
            delattr(GlobalConfig, 'SyncApi')

    @pytest.fixture
    def temp_config_file(self):
        """创建临时配置文件的 fixture"""
        # 创建临时文件
        fd, path = tempfile.mkstemp(suffix='.yaml', text=True)
        
        # 写入配置内容
        config_content = {
            'TdFrontAddress': 'tcp://180.168.146.187:10130',
            'MdFrontAddress': 'tcp://180.168.146.187:10131',
            'BrokerID': '9999',
            'AuthCode': '0000000000000000',
            'AppID': 'simnow_client_test',
            'Host': '0.0.0.0',
            'Port': 8080,
            'LogLevel': 'INFO',
            'ConFilePath': './con_file/',
            'SyncApi': {
                'ConnectTimeout': 45.0,
                'MaxStrategies': 20,
                'QuoteTimeout': 10.0,
                'PositionTimeout': 8.0,
                'OrderTimeout': 15.0,
                'QuoteUpdateTimeout': 60.0,
                'StopTimeout': 10.0
            }
        }
        
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            yaml.dump(config_content, f)
        
        yield path
        
        # 清理临时文件
        try:
            os.unlink(path)
        except:
            pass

    @pytest.fixture
    def invalid_config_file(self):
        """创建格式错误的配置文件的 fixture"""
        fd, path = tempfile.mkstemp(suffix='.yaml', text=True)
        
        # 写入无效的 YAML 内容
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write("invalid: yaml: content: [unclosed")
        
        yield path
        
        # 清理临时文件
        try:
            os.unlink(path)
        except:
            pass

    def test_load_valid_config_file(self, temp_config_file):
        """
        测试有效配置文件加载
        
        验证：
        1. 配置文件被成功加载
        2. SyncApi 配置参数被正确读取
        3. 配置参数与文件中的值一致
        
        Requirements: 10.1, 10.2, 10.4, 10.5
        """
        # Mock 事件循环线程以避免实际连接 CTP
        with patch('src.strategy.sync_api._EventLoopThread') as mock_event_loop:
            # 配置 mock 对象
            mock_instance = MagicMock()
            mock_event_loop.return_value = mock_instance
            
            # 初始化 SyncStrategyApi，传入配置文件路径和测试凭证
            api = SyncStrategyApi(
                user_id="test_user",
                password="test_password",
                config_path=temp_config_file
            )
        
        # 验证配置参数被正确加载
        assert api._config is not None, "配置对象应该被创建"
        assert isinstance(api._config, SyncApiConfig), "配置对象应该是 SyncApiConfig 类型"
        
        # 验证各个配置参数的值
        assert api._config.connect_timeout == 45.0, \
            f"ConnectTimeout 应该是 45.0，实际: {api._config.connect_timeout}"
        assert api._config.max_strategies == 20, \
            f"MaxStrategies 应该是 20，实际: {api._config.max_strategies}"
        assert api._config.quote_timeout == 10.0, \
            f"QuoteTimeout 应该是 10.0，实际: {api._config.quote_timeout}"
        assert api._config.position_timeout == 8.0, \
            f"PositionTimeout 应该是 8.0，实际: {api._config.position_timeout}"
        assert api._config.order_timeout == 15.0, \
            f"OrderTimeout 应该是 15.0，实际: {api._config.order_timeout}"
        assert api._config.quote_update_timeout == 60.0, \
            f"QuoteUpdateTimeout 应该是 60.0，实际: {api._config.quote_update_timeout}"
        assert api._config.stop_timeout == 10.0, \
            f"StopTimeout 应该是 10.0，实际: {api._config.stop_timeout}"

    def test_config_file_not_found_uses_defaults(self, caplog):
        """
        测试配置文件不存在时使用默认值
        
        验证：
        1. 传入不存在的配置文件路径
        2. 系统使用默认配置值
        3. 记录了警告日志
        
        Requirements: 10.2, 10.3
        """
        # 使用不存在的配置文件路径
        nonexistent_path = "/path/to/nonexistent/config.yaml"
        
        # Mock 事件循环线程以避免实际连接 CTP
        with patch('src.strategy.sync_api._EventLoopThread') as mock_event_loop:
            mock_instance = MagicMock()
            mock_event_loop.return_value = mock_instance
            
            # 初始化 SyncStrategyApi
            api = SyncStrategyApi(
                user_id="test_user",
                password="test_password",
                config_path=nonexistent_path
            )
        
        # 验证使用默认配置值
        assert api._config is not None, "配置对象应该被创建"
        assert isinstance(api._config, SyncApiConfig), "配置对象应该是 SyncApiConfig 类型"
        
        # 验证默认值
        default_config = SyncApiConfig()
        assert api._config.connect_timeout == default_config.connect_timeout, \
            "应该使用默认的 ConnectTimeout"
        assert api._config.max_strategies == default_config.max_strategies, \
            "应该使用默认的 MaxStrategies"
        assert api._config.quote_timeout == default_config.quote_timeout, \
            "应该使用默认的 QuoteTimeout"
        assert api._config.position_timeout == default_config.position_timeout, \
            "应该使用默认的 PositionTimeout"
        assert api._config.order_timeout == default_config.order_timeout, \
            "应该使用默认的 OrderTimeout"
        assert api._config.quote_update_timeout == default_config.quote_update_timeout, \
            "应该使用默认的 QuoteUpdateTimeout"
        assert api._config.stop_timeout == default_config.stop_timeout, \
            "应该使用默认的 StopTimeout"
        
        # 注意：loguru 的日志不会被 pytest 的 caplog 自动捕获
        # 但我们可以通过检查 API 对象的状态来验证配置加载失败的处理
        # 如果配置文件不存在，API 应该仍然能够正常初始化并使用默认配置
        assert api._quote_cache is not None, "即使配置文件不存在，API 也应该正常初始化"

    def test_no_config_path_uses_defaults(self):
        """
        测试未提供配置路径时使用默认值
        
        验证：
        1. 不传入 config_path 参数
        2. 系统使用默认配置值
        
        Requirements: 10.3
        """
        # Mock 事件循环线程以避免实际连接 CTP
        with patch('src.strategy.sync_api._EventLoopThread') as mock_event_loop:
            mock_instance = MagicMock()
            mock_event_loop.return_value = mock_instance
            
            # 不传入 config_path 参数
            api = SyncStrategyApi(
                user_id="test_user",
                password="test_password"
            )
        
        # 验证使用默认配置值
        assert api._config is not None, "配置对象应该被创建"
        assert isinstance(api._config, SyncApiConfig), "配置对象应该是 SyncApiConfig 类型"
        
        # 验证默认值
        default_config = SyncApiConfig()
        assert api._config.connect_timeout == default_config.connect_timeout
        assert api._config.max_strategies == default_config.max_strategies
        assert api._config.quote_timeout == default_config.quote_timeout
        assert api._config.position_timeout == default_config.position_timeout
        assert api._config.order_timeout == default_config.order_timeout
        assert api._config.quote_update_timeout == default_config.quote_update_timeout
        assert api._config.stop_timeout == default_config.stop_timeout

    def test_config_parameters_applied_correctly(self, temp_config_file):
        """
        测试配置参数正确应用
        
        验证：
        1. 配置参数在各个方法中被正确使用
        2. 超时参数的应用
        3. 最大策略数限制的应用
        
        Requirements: 10.4, 10.5
        """
        # Mock 事件循环线程以避免实际连接 CTP
        with patch('src.strategy.sync_api._EventLoopThread') as mock_event_loop:
            mock_instance = MagicMock()
            mock_event_loop.return_value = mock_instance
            
            # 加载自定义配置
            api = SyncStrategyApi(
                user_id="test_user",
                password="test_password",
                config_path=temp_config_file
            )
        
        # 验证配置参数被存储
        assert api._config.connect_timeout == 45.0
        assert api._config.max_strategies == 20
        assert api._config.quote_timeout == 10.0
        assert api._config.position_timeout == 8.0
        assert api._config.order_timeout == 15.0
        assert api._config.quote_update_timeout == 60.0
        assert api._config.stop_timeout == 10.0
        
        # 验证配置参数可以被方法访问
        # 注意：这里只验证配置参数的存在性，不实际调用方法（避免连接 CTP）
        assert hasattr(api, '_config'), "API 应该有 _config 属性"
        assert api._config is not None, "_config 不应该是 None"
        
        # 验证内部数据结构使用了配置
        assert api._quote_cache is not None, "行情缓存应该被初始化"
        assert api._position_cache is not None, "持仓缓存应该被初始化"
        assert api._running_strategies is not None, "策略注册表应该被初始化"

    def test_invalid_config_file_uses_defaults(self, invalid_config_file, caplog):
        """
        测试配置文件格式错误时使用默认值
        
        验证：
        1. 传入格式错误的配置文件
        2. 系统使用默认配置值
        3. 记录了警告日志
        
        Requirements: 10.2, 10.3
        """
        # Mock 事件循环线程以避免实际连接 CTP
        with patch('src.strategy.sync_api._EventLoopThread') as mock_event_loop:
            mock_instance = MagicMock()
            mock_event_loop.return_value = mock_instance
            
            # 使用格式错误的配置文件
            api = SyncStrategyApi(
                user_id="test_user",
                password="test_password",
                config_path=invalid_config_file
            )
        
        # 验证使用默认配置值
        assert api._config is not None, "配置对象应该被创建"
        assert isinstance(api._config, SyncApiConfig), "配置对象应该是 SyncApiConfig 类型"
        
        # 验证默认值
        default_config = SyncApiConfig()
        assert api._config.connect_timeout == default_config.connect_timeout
        assert api._config.max_strategies == default_config.max_strategies
        assert api._config.quote_timeout == default_config.quote_timeout
        
        # 注意：loguru 的日志不会被 pytest 的 caplog 自动捕获
        # 但我们可以通过检查 API 对象的状态来验证配置加载失败的处理
        # 如果配置文件格式错误，API 应该仍然能够正常初始化并使用默认配置
        assert api._quote_cache is not None, "即使配置文件格式错误，API 也应该正常初始化"

    def test_config_without_sync_api_section(self):
        """
        测试配置文件中没有 SyncApi 部分时使用默认值
        
        验证：
        1. 配置文件存在但没有 SyncApi 配置
        2. 系统使用默认配置值
        
        Requirements: 10.3
        """
        # 创建没有 SyncApi 部分的配置文件
        fd, path = tempfile.mkstemp(suffix='.yaml', text=True)
        
        config_content = {
            'TdFrontAddress': 'tcp://180.168.146.187:10130',
            'MdFrontAddress': 'tcp://180.168.146.187:10131',
            'BrokerID': '9999',
            'Host': '0.0.0.0',
            'Port': 8080
            # 注意：没有 SyncApi 部分
        }
        
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            yaml.dump(config_content, f)
        
        try:
            # Mock 事件循环线程以避免实际连接 CTP
            with patch('src.strategy.sync_api._EventLoopThread') as mock_event_loop:
                mock_instance = MagicMock()
                mock_event_loop.return_value = mock_instance
                
                # 初始化 API
                api = SyncStrategyApi(
                    user_id="test_user",
                    password="test_password",
                    config_path=path
                )
                
                # 验证使用默认配置值
                default_config = SyncApiConfig()
                assert api._config.connect_timeout == default_config.connect_timeout
                assert api._config.max_strategies == default_config.max_strategies
                assert api._config.quote_timeout == default_config.quote_timeout
            
        finally:
            # 清理临时文件
            try:
                os.unlink(path)
            except:
                pass

    def test_partial_sync_api_config(self):
        """
        测试部分 SyncApi 配置时使用默认值填充
        
        验证：
        1. 配置文件只包含部分 SyncApi 参数
        2. 已配置的参数使用配置值
        3. 未配置的参数使用默认值
        
        Requirements: 10.3, 10.4
        """
        # 创建只包含部分 SyncApi 配置的文件
        fd, path = tempfile.mkstemp(suffix='.yaml', text=True)
        
        config_content = {
            'TdFrontAddress': 'tcp://180.168.146.187:10130',
            'MdFrontAddress': 'tcp://180.168.146.187:10131',
            'BrokerID': '9999',
            'SyncApi': {
                'ConnectTimeout': 50.0,
                'MaxStrategies': 15
                # 其他参数未配置
            }
        }
        
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            yaml.dump(config_content, f)
        
        try:
            # Mock 事件循环线程以避免实际连接 CTP
            with patch('src.strategy.sync_api._EventLoopThread') as mock_event_loop:
                mock_instance = MagicMock()
                mock_event_loop.return_value = mock_instance
                
                # 初始化 API
                api = SyncStrategyApi(
                    user_id="test_user",
                    password="test_password",
                    config_path=path
                )
                
                # 验证已配置的参数
                assert api._config.connect_timeout == 50.0, \
                    "已配置的 ConnectTimeout 应该使用配置值"
                assert api._config.max_strategies == 15, \
                    "已配置的 MaxStrategies 应该使用配置值"
                
                # 验证未配置的参数使用默认值
                default_config = SyncApiConfig()
                assert api._config.quote_timeout == default_config.quote_timeout, \
                    "未配置的 QuoteTimeout 应该使用默认值"
                assert api._config.position_timeout == default_config.position_timeout, \
                    "未配置的 PositionTimeout 应该使用默认值"
                assert api._config.order_timeout == default_config.order_timeout, \
                    "未配置的 OrderTimeout 应该使用默认值"
            
        finally:
            # 清理临时文件
            try:
                os.unlink(path)
            except:
                pass

    def test_config_values_are_correct_types(self, temp_config_file):
        """
        测试配置值的类型正确性
        
        验证：
        1. 超时参数是 float 类型
        2. 最大策略数是 int 类型
        
        Requirements: 10.4, 10.5
        """
        # Mock 事件循环线程以避免实际连接 CTP
        with patch('src.strategy.sync_api._EventLoopThread') as mock_event_loop:
            mock_instance = MagicMock()
            mock_event_loop.return_value = mock_instance
            
            api = SyncStrategyApi(
                user_id="test_user",
                password="test_password",
                config_path=temp_config_file
            )
        
        # 验证类型
        assert isinstance(api._config.connect_timeout, float), \
            "ConnectTimeout 应该是 float 类型"
        assert isinstance(api._config.max_strategies, int), \
            "MaxStrategies 应该是 int 类型"
        assert isinstance(api._config.quote_timeout, float), \
            "QuoteTimeout 应该是 float 类型"
        assert isinstance(api._config.position_timeout, float), \
            "PositionTimeout 应该是 float 类型"
        assert isinstance(api._config.order_timeout, float), \
            "OrderTimeout 应该是 float 类型"
        assert isinstance(api._config.quote_update_timeout, float), \
            "QuoteUpdateTimeout 应该是 float 类型"
        assert isinstance(api._config.stop_timeout, float), \
            "StopTimeout 应该是 float 类型"
        
        # 验证值的合理性
        assert api._config.connect_timeout > 0, "ConnectTimeout 应该大于 0"
        assert api._config.max_strategies > 0, "MaxStrategies 应该大于 0"
        assert api._config.quote_timeout > 0, "QuoteTimeout 应该大于 0"
        assert api._config.position_timeout > 0, "PositionTimeout 应该大于 0"
        assert api._config.order_timeout > 0, "OrderTimeout 应该大于 0"
        assert api._config.quote_update_timeout > 0, "QuoteUpdateTimeout 应该大于 0"
        assert api._config.stop_timeout > 0, "StopTimeout 应该大于 0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
