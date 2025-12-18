#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : test_sync_api_open_close.py
@Date       : 2025/12/16
@Author     : Kiro AI Assistant
@Email      : -
@Software   : PyCharm
@Description: open_close 方法和订单提交映射的属性测试
"""

import pytest
import time
import threading
from unittest.mock import Mock, AsyncMock, patch
from hypothesis import given, strategies as st, settings
from src.strategy.sync_api import SyncStrategyApi
# Test credentials
TEST_USER_ID = "test_user"
TEST_PASSWORD = "test_pass"


class TestActionMapping:
    """订单动作映射单元测试"""

    def test_kaiduo_mapping(self):
        """测试开多动作映射"""
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        direction, offset_flag = api._map_action_to_ctp('kaiduo')
        
        assert direction == '0', "开多应该是买入方向 (Direction='0')"
        assert offset_flag == '0', "开多应该是开仓 (CombOffsetFlag='0')"

    def test_kaikong_mapping(self):
        """测试开空动作映射"""
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        direction, offset_flag = api._map_action_to_ctp('kaikong')
        
        assert direction == '1', "开空应该是卖出方向 (Direction='1')"
        assert offset_flag == '0', "开空应该是开仓 (CombOffsetFlag='0')"

    def test_pingduo_mapping(self):
        """测试平多动作映射"""
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        direction, offset_flag = api._map_action_to_ctp('pingduo')
        
        assert direction == '1', "平多应该是卖出方向 (Direction='1')"
        assert offset_flag == '1', "平多应该是平仓 (CombOffsetFlag='1')"

    def test_pingkong_mapping(self):
        """测试平空动作映射"""
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        direction, offset_flag = api._map_action_to_ctp('pingkong')
        
        assert direction == '0', "平空应该是买入方向 (Direction='0')"
        assert offset_flag == '1', "平空应该是平仓 (CombOffsetFlag='1')"

    def test_invalid_action_raises_error(self):
        """测试无效动作抛出 ValueError"""
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        with pytest.raises(ValueError) as exc_info:
            api._map_action_to_ctp('invalid_action')
        
        assert 'invalid_action' in str(exc_info.value)
        assert 'kaiduo' in str(exc_info.value)

    def test_empty_action_raises_error(self):
        """测试空字符串动作抛出 ValueError"""
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        with pytest.raises(ValueError):
            api._map_action_to_ctp('')

    def test_case_sensitive_action(self):
        """测试动作参数区分大小写"""
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 大写应该失败
        with pytest.raises(ValueError):
            api._map_action_to_ctp('KAIDUO')
        
        # 混合大小写应该失败
        with pytest.raises(ValueError):
            api._map_action_to_ctp('KaiDuo')


class TestOrderSubmissionMapping:
    """订单提交映射属性测试"""

    # Feature: sync-strategy-api, Property 8: 订单提交正确映射
    
    @settings(max_examples=100)
    @given(
        instrument_id=st.text(
            min_size=4,
            max_size=10,
            alphabet=st.characters(whitelist_categories=('Lu', 'Nd'))
        ),
        action=st.sampled_from(['kaiduo', 'kaikong', 'pingduo', 'pingkong']),
        volume=st.integers(min_value=1, max_value=100),
        price=st.floats(min_value=0.01, max_value=100000.0, allow_nan=False, allow_infinity=False)
    )
    def test_property_order_submission_correct_mapping(
        self,
        instrument_id: str,
        action: str,
        volume: int,
        price: float
    ):
        """
        **Feature: sync-strategy-api, Property 8: 订单提交正确映射**
        
        Property 8: 订单提交正确映射
        
        For any 有效的订单参数（instrument_id, action, volume, price），
        调用 open_close() 应该正确映射 action 参数到 CTP 的 Direction 和 CombOffsetFlag，
        并提交订单到 CTP 系统。
        
        **Validates: Requirements 3.1, 3.2-3.5**
        
        测试策略：
        1. 生成随机的订单参数（合约代码、动作、数量、价格）
        2. 验证 _map_action_to_ctp() 方法返回正确的映射
        3. 验证映射结果符合 CTP 协议规范：
           - kaiduo: Direction='0' (买), CombOffsetFlag='0' (开仓)
           - kaikong: Direction='1' (卖), CombOffsetFlag='0' (开仓)
           - pingduo: Direction='1' (卖), CombOffsetFlag='1' (平仓)
           - pingkong: Direction='0' (买), CombOffsetFlag='1' (平仓)
        """
        # 创建 API 实例（不需要连接 CTP）
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 调用映射方法
        direction, offset_flag = api._map_action_to_ctp(action)
        
        # 定义预期的映射关系
        expected_mappings = {
            'kaiduo': ('0', '0'),    # 买入开仓
            'kaikong': ('1', '0'),   # 卖出开仓
            'pingduo': ('1', '1'),   # 卖出平仓
            'pingkong': ('0', '1')   # 买入平仓
        }
        
        # 验证映射结果
        expected_direction, expected_offset = expected_mappings[action]
        
        assert direction == expected_direction, \
            f"动作 {action} 的 Direction 映射错误: 期望 {expected_direction}, 实际 {direction}"
        
        assert offset_flag == expected_offset, \
            f"动作 {action} 的 CombOffsetFlag 映射错误: 期望 {expected_offset}, 实际 {offset_flag}"
        
        # 验证映射的一致性：相同的 action 应该总是返回相同的映射
        direction2, offset_flag2 = api._map_action_to_ctp(action)
        assert direction == direction2, "相同 action 的映射应该一致"
        assert offset_flag == offset_flag2, "相同 action 的映射应该一致"
        
        # 验证 Direction 只能是 '0' 或 '1'
        assert direction in ['0', '1'], \
            f"Direction 必须是 '0' 或 '1'，实际: {direction}"
        
        # 验证 CombOffsetFlag 只能是 '0' 或 '1'
        assert offset_flag in ['0', '1'], \
            f"CombOffsetFlag 必须是 '0' 或 '1'，实际: {offset_flag}"

    @settings(max_examples=50)
    @given(
        action=st.sampled_from(['kaiduo', 'kaikong', 'pingduo', 'pingkong'])
    )
    def test_property_mapping_consistency(self, action: str):
        """
        属性测试：映射的一致性
        
        验证对于相同的 action，多次调用 _map_action_to_ctp() 应该返回相同的结果。
        """
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 多次调用，验证结果一致
        results = [api._map_action_to_ctp(action) for _ in range(10)]
        
        # 所有结果应该相同
        first_result = results[0]
        for result in results[1:]:
            assert result == first_result, \
                f"相同 action '{action}' 的映射结果应该一致，但得到不同结果: {results}"

    @settings(max_examples=50)
    @given(
        invalid_action=st.text(min_size=1, max_size=20).filter(
            lambda x: x not in ['kaiduo', 'kaikong', 'pingduo', 'pingkong']
        )
    )
    def test_property_invalid_action_raises_error(self, invalid_action: str):
        """
        属性测试：无效动作抛出错误
        
        验证对于任何不在支持列表中的 action，_map_action_to_ctp() 应该抛出 ValueError。
        """
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        with pytest.raises(ValueError) as exc_info:
            api._map_action_to_ctp(invalid_action)
        
        # 验证错误消息包含有用信息
        error_msg = str(exc_info.value)
        assert invalid_action in error_msg or '不支持' in error_msg or '无效' in error_msg, \
            f"错误消息应该包含无效的 action 或提示信息，实际: {error_msg}"

    def test_all_actions_have_unique_mappings(self):
        """测试所有动作都有唯一的映射组合"""
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        actions = ['kaiduo', 'kaikong', 'pingduo', 'pingkong']
        mappings = {}
        
        for action in actions:
            direction, offset_flag = api._map_action_to_ctp(action)
            mapping_tuple = (direction, offset_flag)
            
            # 验证这个映射组合是唯一的
            assert mapping_tuple not in mappings.values(), \
                f"映射冲突: {action} 的映射 {mapping_tuple} 与其他动作重复"
            
            mappings[action] = mapping_tuple
        
        # 验证所有四种动作都有映射
        assert len(mappings) == 4, "应该有 4 种不同的动作映射"

    def test_buy_sell_direction_correctness(self):
        """测试买卖方向的正确性"""
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 开多和平空应该是买入方向 ('0')
        buy_actions = ['kaiduo', 'pingkong']
        for action in buy_actions:
            direction, _ = api._map_action_to_ctp(action)
            assert direction == '0', \
                f"{action} 应该是买入方向 (Direction='0')，实际: {direction}"
        
        # 开空和平多应该是卖出方向 ('1')
        sell_actions = ['kaikong', 'pingduo']
        for action in sell_actions:
            direction, _ = api._map_action_to_ctp(action)
            assert direction == '1', \
                f"{action} 应该是卖出方向 (Direction='1')，实际: {direction}"

    def test_open_close_offset_correctness(self):
        """测试开平仓标志的正确性"""
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 开多和开空应该是开仓 ('0')
        open_actions = ['kaiduo', 'kaikong']
        for action in open_actions:
            _, offset_flag = api._map_action_to_ctp(action)
            assert offset_flag == '0', \
                f"{action} 应该是开仓 (CombOffsetFlag='0')，实际: {offset_flag}"
        
        # 平多和平空应该是平仓 ('1')
        close_actions = ['pingduo', 'pingkong']
        for action in close_actions:
            _, offset_flag = api._map_action_to_ctp(action)
            assert offset_flag == '1', \
                f"{action} 应该是平仓 (CombOffsetFlag='1')，实际: {offset_flag}"

    def test_mapping_returns_strings(self):
        """测试映射返回的是字符串类型"""
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        actions = ['kaiduo', 'kaikong', 'pingduo', 'pingkong']
        
        for action in actions:
            direction, offset_flag = api._map_action_to_ctp(action)
            
            assert isinstance(direction, str), \
                f"{action} 的 Direction 应该是字符串类型，实际: {type(direction)}"
            
            assert isinstance(offset_flag, str), \
                f"{action} 的 CombOffsetFlag 应该是字符串类型，实际: {type(offset_flag)}"


class TestBlockingBehavior:
    """阻塞等待成交的属性测试"""
    
    # Feature: sync-strategy-api, Property 9: 阻塞等待成交
    
    def test_property_blocking_vs_nonblocking_behavior(self):
        """
        **Feature: sync-strategy-api, Property 9: 阻塞等待成交**
        
        Property 9: 阻塞等待成交
        
        For any 订单，当 block=True 时，open_close() 应该阻塞当前线程直到订单成交或超时；
        当 block=False 时，应该立即返回而不等待成交。
        
        **Validates: Requirements 3.6, 3.7**
        
        测试策略：
        1. 测试 block=True 的行为：
           - 模拟延迟响应
           - 验证方法阻塞等待响应
           - 验证等待时间符合预期
        2. 测试 block=False 的行为：
           - 验证方法立即返回
           - 验证返回时间很短
        """
        import asyncio
        import concurrent.futures
        
        # 创建 API 实例
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 模拟事件循环和客户端
        api._event_loop_thread = Mock()
        api._event_loop_thread.loop = Mock()
        api._event_loop_thread.td_client = Mock()
        
        # 测试 block=True 的行为
        # 创建一个会延迟返回的 Future
        def create_delayed_future(delay_seconds, result_value):
            """创建一个延迟返回的 Future"""
            future = concurrent.futures.Future()
            
            def set_result_after_delay():
                time.sleep(delay_seconds)
                future.set_result(result_value)
            
            thread = threading.Thread(target=set_result_after_delay, daemon=True)
            thread.start()
            
            return future
        
        # Mock run_coroutine_threadsafe 返回延迟的 Future
        with patch('asyncio.run_coroutine_threadsafe') as mock_run:
            # 设置延迟 0.5 秒的成功响应
            success_response = {
                'RspInfo': {'ErrorID': 0, 'ErrorMsg': ''},
                'InputOrder': {'OrderRef': '123456'}
            }
            mock_run.return_value = create_delayed_future(0.5, success_response)
            
            # 测试 block=True：应该阻塞等待
            start_time = time.time()
            result = api.open_close(
                instrument_id="TEST",
                action="kaiduo",
                volume=1,
                price=3500.0,
                block=True,
                timeout=2.0
            )
            elapsed_time = time.time() - start_time
            
            # 验证：应该阻塞至少 0.4 秒
            assert elapsed_time >= 0.4, \
                f"block=True 时应该阻塞等待响应，但只用了 {elapsed_time:.2f} 秒"
            
            # 验证：返回成功
            assert result['success'] is True, \
                f"block=True 时应该返回成功，实际: {result}"
            
            # 验证：包含订单号
            assert 'order_ref' in result, \
                f"返回结果应该包含 order_ref，实际: {result}"
        
        # 测试 block=False 的行为
        with patch('asyncio.run_coroutine_threadsafe') as mock_run:
            # 即使设置延迟，block=False 也应该立即返回
            mock_run.return_value = create_delayed_future(0.5, success_response)
            
            # 测试 block=False：应该立即返回
            start_time = time.time()
            result = api.open_close(
                instrument_id="TEST",
                action="kaiduo",
                volume=1,
                price=3500.0,
                block=False,
                timeout=2.0
            )
            elapsed_time = time.time() - start_time
            
            # 验证：应该立即返回（< 0.1 秒）
            assert elapsed_time < 0.1, \
                f"block=False 时应该立即返回，但用了 {elapsed_time:.2f} 秒"
            
            # 验证：返回成功
            assert result['success'] is True, \
                f"block=False 时应该返回成功，实际: {result}"

    def test_property_blocking_timeout_behavior(self):
        """
        属性测试：阻塞超时行为
        
        验证当 block=True 且响应超时时，open_close() 应该抛出 TimeoutError。
        
        测试策略：
        1. 模拟一个永远不返回的 Future
        2. 设置较短的超时时间（0.5 秒）
        3. 验证方法抛出 TimeoutError
        4. 验证超时时间符合预期
        """
        import concurrent.futures
        
        # 创建 API 实例
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 模拟事件循环和客户端
        api._event_loop_thread = Mock()
        api._event_loop_thread.loop = Mock()
        api._event_loop_thread.td_client = Mock()
        
        # 创建一个永远不会完成的 Future
        def create_never_completing_future():
            """创建一个永远不会完成的 Future"""
            future = concurrent.futures.Future()
            # 不设置结果，Future 永远不会完成
            return future
        
        with patch('asyncio.run_coroutine_threadsafe') as mock_run:
            mock_run.return_value = create_never_completing_future()
            
            # 测试超时行为
            start_time = time.time()
            
            with pytest.raises(TimeoutError) as exc_info:
                api.open_close(
                    instrument_id="TEST",
                    action="kaiduo",
                    volume=1,
                    price=3500.0,
                    block=True,
                    timeout=0.5  # 设置较短的超时时间
                )
            
            elapsed_time = time.time() - start_time
            
            # 验证：应该在超时时间附近抛出异常（允许 ±0.2 秒的误差）
            assert 0.3 <= elapsed_time <= 0.7, \
                f"超时应该在 0.5 秒左右发生，实际: {elapsed_time:.2f} 秒"
            
            # 验证：异常消息应该包含超时信息
            assert '超时' in str(exc_info.value) or 'timeout' in str(exc_info.value).lower(), \
                f"超时异常消息应该包含超时信息，实际: {exc_info.value}"

    def test_block_parameter_type_validation(self):
        """测试 block 参数的类型验证"""
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 模拟事件循环
        api._event_loop_thread = Mock()
        api._event_loop_thread.loop = Mock()
        api._event_loop_thread.td_client = Mock()
        
        # block 参数应该接受布尔值
        # 这里只测试参数传递，不实际执行（因为没有真实的 CTP 连接）
        
        # 测试 block=True
        try:
            # 这会失败，因为没有真实的 TdClient，但不应该因为 block 参数类型而失败
            api.open_close("TEST", "kaiduo", 1, 3500.0, block=True, timeout=0.1)
        except (RuntimeError, TimeoutError, AttributeError):
            # 预期的错误（因为没有真实连接）
            pass
        
        # 测试 block=False
        try:
            api.open_close("TEST", "kaiduo", 1, 3500.0, block=False, timeout=0.1)
        except (RuntimeError, TimeoutError, AttributeError):
            # 预期的错误
            pass

    def test_block_true_waits_for_error_response(self):
        """测试 block=True 时等待错误响应"""
        import concurrent.futures
        
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 模拟事件循环和客户端
        api._event_loop_thread = Mock()
        api._event_loop_thread.loop = Mock()
        api._event_loop_thread.td_client = Mock()
        
        # 创建延迟返回错误响应的 Future
        def create_delayed_error_future():
            future = concurrent.futures.Future()
            
            def set_error_after_delay():
                time.sleep(0.3)
                future.set_result({
                    'RspInfo': {
                        'ErrorID': 1,
                        'ErrorMsg': '资金不足'
                    },
                    'InputOrder': {'OrderRef': '123456'}
                })
            
            thread = threading.Thread(target=set_error_after_delay, daemon=True)
            thread.start()
            
            return future
        
        with patch('asyncio.run_coroutine_threadsafe') as mock_run:
            mock_run.return_value = create_delayed_error_future()
            
            start_time = time.time()
            result = api.open_close(
                instrument_id="TEST",
                action="kaiduo",
                volume=1,
                price=3500.0,
                block=True,
                timeout=2.0
            )
            elapsed_time = time.time() - start_time
            
            # 验证：应该阻塞等待响应
            assert elapsed_time >= 0.2, \
                f"block=True 时应该阻塞等待响应，但只用了 {elapsed_time:.2f} 秒"
            
            # 验证：返回结果应该标记为失败
            assert result['success'] is False, \
                f"错误响应应该标记为失败，实际: {result}"
            
            # 验证：返回结果应该包含错误信息
            assert 'error_id' in result and result['error_id'] == 1, \
                f"返回结果应该包含错误代码，实际: {result}"
            
            assert 'error_msg' in result and '资金不足' in result['error_msg'], \
                f"返回结果应该包含错误消息，实际: {result}"


class TestOrderFailureMarking:
    """订单失败标记的属性测试"""
    
    # Feature: sync-strategy-api, Property 10: 订单失败标记
    
    @settings(max_examples=100)
    @given(
        instrument_id=st.text(
            min_size=4,
            max_size=10,
            alphabet=st.characters(whitelist_categories=('Lu', 'Nd'))
        ),
        action=st.sampled_from(['kaiduo', 'kaikong', 'pingduo', 'pingkong']),
        volume=st.integers(min_value=1, max_value=100),
        price=st.floats(min_value=0.01, max_value=100000.0, allow_nan=False, allow_infinity=False),
        error_id=st.integers(min_value=1, max_value=999),
        error_msg=st.text(min_size=1, max_size=50)
    )
    def test_property_order_failure_marking(
        self,
        instrument_id: str,
        action: str,
        volume: int,
        price: float,
        error_id: int,
        error_msg: str
    ):
        """
        **Feature: sync-strategy-api, Property 10: 订单失败标记**
        
        Property 10: 订单失败标记
        
        For any 提交失败的订单，open_close() 的返回结果应该包含 success=False 标记，
        并包含错误详情（error_id 和 error_msg）。
        
        **Validates: Requirements 3.8, 7.3**
        
        测试策略：
        1. 生成随机的订单参数和错误响应
        2. Mock CTP 返回错误响应（ErrorID != 0）
        3. 验证返回结果包含 success=False
        4. 验证返回结果包含 error_id 和 error_msg
        5. 验证错误信息与 CTP 响应一致
        """
        import concurrent.futures
        
        # 创建 API 实例
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 模拟事件循环和客户端
        api._event_loop_thread = Mock()
        api._event_loop_thread.loop = Mock()
        api._event_loop_thread.td_client = Mock()
        
        # 创建错误响应
        error_response = {
            'RspInfo': {
                'ErrorID': error_id,
                'ErrorMsg': error_msg
            },
            'InputOrder': {
                'OrderRef': '123456'
            }
        }
        
        # 创建立即返回错误响应的 Future
        def create_error_future():
            future = concurrent.futures.Future()
            future.set_result(error_response)
            return future
        
        with patch('asyncio.run_coroutine_threadsafe') as mock_run:
            mock_run.return_value = create_error_future()
            
            # 调用 open_close（block=True）
            result = api.open_close(
                instrument_id=instrument_id,
                action=action,
                volume=volume,
                price=price,
                block=True,
                timeout=2.0
            )
            
            # 验证：返回结果应该标记为失败
            assert result['success'] is False, \
                f"订单失败时应该返回 success=False，实际: {result}"
            
            # 验证：返回结果应该包含错误代码
            assert 'error_id' in result, \
                f"返回结果应该包含 error_id 字段，实际: {result}"
            
            assert result['error_id'] == error_id, \
                f"error_id 应该与 CTP 响应一致，期望: {error_id}, 实际: {result['error_id']}"
            
            # 验证：返回结果应该包含错误消息
            assert 'error_msg' in result, \
                f"返回结果应该包含 error_msg 字段，实际: {result}"
            
            assert result['error_msg'] == error_msg, \
                f"error_msg 应该与 CTP 响应一致，期望: {error_msg}, 实际: {result['error_msg']}"
            
            # 验证：返回结果应该包含订单参数（用于调试）
            assert result['instrument_id'] == instrument_id, \
                f"返回结果应该包含 instrument_id，实际: {result}"
            
            assert result['action'] == action, \
                f"返回结果应该包含 action，实际: {result}"
            
            assert result['volume'] == volume, \
                f"返回结果应该包含 volume，实际: {result}"
            
            assert result['price'] == price, \
                f"返回结果应该包含 price，实际: {result}"

    @settings(max_examples=50)
    @given(
        instrument_id=st.text(
            min_size=4,
            max_size=10,
            alphabet=st.characters(whitelist_categories=('Lu', 'Nd'))
        ),
        invalid_action=st.text(min_size=1, max_size=20).filter(
            lambda x: x not in ['kaiduo', 'kaikong', 'pingduo', 'pingkong']
        ),
        volume=st.integers(min_value=1, max_value=100),
        price=st.floats(min_value=0.01, max_value=100000.0, allow_nan=False, allow_infinity=False)
    )
    def test_property_invalid_action_failure_marking(
        self,
        instrument_id: str,
        invalid_action: str,
        volume: int,
        price: float
    ):
        """
        属性测试：无效 action 参数的失败标记
        
        验证当 action 参数无效时，open_close() 应该返回 success=False，
        并包含错误信息，而不是抛出异常。
        
        **Validates: Requirements 3.8, 7.3**
        """
        # 创建 API 实例
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 模拟事件循环和客户端
        api._event_loop_thread = Mock()
        api._event_loop_thread.loop = Mock()
        api._event_loop_thread.td_client = Mock()
        
        # 调用 open_close（不应该抛出异常）
        result = api.open_close(
            instrument_id=instrument_id,
            action=invalid_action,
            volume=volume,
            price=price,
            block=True,
            timeout=2.0
        )
        
        # 验证：返回结果应该标记为失败
        assert result['success'] is False, \
            f"无效 action 时应该返回 success=False，实际: {result}"
        
        # 验证：返回结果应该包含错误信息
        assert 'error_id' in result, \
            f"返回结果应该包含 error_id 字段，实际: {result}"
        
        assert 'error_msg' in result, \
            f"返回结果应该包含 error_msg 字段，实际: {result}"
        
        # 验证：错误消息应该提示 action 无效
        error_msg = result['error_msg']
        assert invalid_action in error_msg or '无效' in error_msg or '不支持' in error_msg, \
            f"错误消息应该包含无效的 action 或提示信息，实际: {error_msg}"
        
        # 验证：返回结果应该包含订单参数
        assert result['instrument_id'] == instrument_id
        assert result['action'] == invalid_action
        assert result['volume'] == volume
        assert result['price'] == price

    def test_property_system_error_failure_marking(self):
        """
        属性测试：系统错误的失败标记
        
        验证当系统错误（如事件循环未启动）时，open_close() 应该返回 success=False
        或抛出 RuntimeError（取决于错误类型）。
        
        **Validates: Requirements 7.3**
        """
        # 创建 API 实例（未连接 CTP）
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 不设置事件循环，模拟未连接状态
        api._event_loop_thread = None
        
        # 调用 open_close 应该抛出 RuntimeError
        with pytest.raises(RuntimeError) as exc_info:
            api.open_close(
                instrument_id="TEST",
                action="kaiduo",
                volume=1,
                price=3500.0,
                block=True,
                timeout=2.0
            )
        
        # 验证：错误消息应该提示事件循环未启动
        error_msg = str(exc_info.value)
        assert '事件循环' in error_msg or 'connect' in error_msg, \
            f"错误消息应该提示事件循环未启动，实际: {error_msg}"

    @settings(max_examples=50)
    @given(
        instrument_id=st.text(
            min_size=4,
            max_size=10,
            alphabet=st.characters(whitelist_categories=('Lu', 'Nd'))
        ),
        action=st.sampled_from(['kaiduo', 'kaikong', 'pingduo', 'pingkong']),
        volume=st.integers(min_value=1, max_value=100),
        price=st.floats(min_value=0.01, max_value=100000.0, allow_nan=False, allow_infinity=False)
    )
    def test_failure_result_structure(
        self,
        instrument_id: str,
        action: str,
        volume: int,
        price: float
    ):
        """
        属性测试：失败结果的结构完整性
        
        验证失败的订单结果包含所有必需的字段，且字段类型正确。
        
        **Validates: Requirements 3.8, 7.3**
        """
        import concurrent.futures
        
        # 创建 API 实例
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 模拟事件循环和客户端
        api._event_loop_thread = Mock()
        api._event_loop_thread.loop = Mock()
        api._event_loop_thread.td_client = Mock()
        
        # 创建错误响应
        error_response = {
            'RspInfo': {
                'ErrorID': 42,
                'ErrorMsg': '测试错误'
            },
            'InputOrder': {
                'OrderRef': '123456'
            }
        }
        
        def create_error_future():
            future = concurrent.futures.Future()
            future.set_result(error_response)
            return future
        
        with patch('asyncio.run_coroutine_threadsafe') as mock_run:
            mock_run.return_value = create_error_future()
            
            result = api.open_close(
                instrument_id=instrument_id,
                action=action,
                volume=volume,
                price=price,
                block=True,
                timeout=2.0
            )
            
            # 验证：返回结果是字典类型
            assert isinstance(result, dict), \
                f"返回结果应该是字典类型，实际: {type(result)}"
            
            # 验证：必需字段存在
            required_fields = ['success', 'error_id', 'error_msg', 
                             'instrument_id', 'action', 'volume', 'price']
            
            for field in required_fields:
                assert field in result, \
                    f"返回结果应该包含字段 '{field}'，实际字段: {list(result.keys())}"
            
            # 验证：字段类型正确
            assert isinstance(result['success'], bool), \
                f"success 应该是布尔类型，实际: {type(result['success'])}"
            
            assert isinstance(result['error_id'], int), \
                f"error_id 应该是整数类型，实际: {type(result['error_id'])}"
            
            assert isinstance(result['error_msg'], str), \
                f"error_msg 应该是字符串类型，实际: {type(result['error_msg'])}"
            
            assert isinstance(result['instrument_id'], str), \
                f"instrument_id 应该是字符串类型，实际: {type(result['instrument_id'])}"
            
            assert isinstance(result['action'], str), \
                f"action 应该是字符串类型，实际: {type(result['action'])}"
            
            assert isinstance(result['volume'], int), \
                f"volume 应该是整数类型，实际: {type(result['volume'])}"
            
            assert isinstance(result['price'], float), \
                f"price 应该是浮点数类型，实际: {type(result['price'])}"
            
            # 验证：success 为 False
            assert result['success'] is False, \
                f"失败的订单 success 应该为 False，实际: {result['success']}"
            
            # 验证：error_id 不为 0
            assert result['error_id'] != 0, \
                f"失败的订单 error_id 应该不为 0，实际: {result['error_id']}"
            
            # 验证：error_msg 不为空
            assert len(result['error_msg']) > 0, \
                f"失败的订单 error_msg 应该不为空，实际: '{result['error_msg']}'"

    def test_exception_during_submission_failure_marking(self):
        """
        单元测试：提交过程中发生异常的失败标记
        
        验证当提交订单过程中发生异常时，open_close() 应该返回 success=False
        并包含异常信息。
        
        **Validates: Requirements 7.3**
        """
        import concurrent.futures
        
        # 创建 API 实例
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 模拟事件循环和客户端
        api._event_loop_thread = Mock()
        api._event_loop_thread.loop = Mock()
        api._event_loop_thread.td_client = Mock()
        
        # Mock run_coroutine_threadsafe 抛出异常
        with patch('asyncio.run_coroutine_threadsafe') as mock_run:
            mock_run.side_effect = RuntimeError("模拟的提交异常")
            
            # 调用 open_close（不应该抛出异常）
            result = api.open_close(
                instrument_id="TEST",
                action="kaiduo",
                volume=1,
                price=3500.0,
                block=True,
                timeout=2.0
            )
            
            # 验证：返回结果应该标记为失败
            assert result['success'] is False, \
                f"异常时应该返回 success=False，实际: {result}"
            
            # 验证：返回结果应该包含错误信息
            assert 'error_id' in result
            assert 'error_msg' in result
            
            # 验证：错误消息应该包含异常信息
            assert '模拟的提交异常' in result['error_msg'] or '提交订单失败' in result['error_msg'], \
                f"错误消息应该包含异常信息，实际: {result['error_msg']}"

    def test_success_vs_failure_result_consistency(self):
        """
        单元测试：成功和失败结果的一致性
        
        验证成功和失败的订单结果都包含相同的基本字段，
        只是 success 标志和错误信息不同。
        
        **Validates: Requirements 3.8**
        """
        import concurrent.futures
        
        # 创建 API 实例
        api = SyncStrategyApi(user_id=TEST_USER_ID, password=TEST_PASSWORD)
        
        # 模拟事件循环和客户端
        api._event_loop_thread = Mock()
        api._event_loop_thread.loop = Mock()
        api._event_loop_thread.td_client = Mock()
        
        # 测试成功响应
        success_response = {
            'RspInfo': {
                'ErrorID': 0,
                'ErrorMsg': ''
            },
            'InputOrder': {
                'OrderRef': '123456'
            }
        }
        
        def create_success_future():
            future = concurrent.futures.Future()
            future.set_result(success_response)
            return future
        
        with patch('asyncio.run_coroutine_threadsafe') as mock_run:
            mock_run.return_value = create_success_future()
            
            success_result = api.open_close(
                instrument_id="TEST",
                action="kaiduo",
                volume=1,
                price=3500.0,
                block=True,
                timeout=2.0
            )
        
        # 测试失败响应
        error_response = {
            'RspInfo': {
                'ErrorID': 1,
                'ErrorMsg': '资金不足'
            },
            'InputOrder': {
                'OrderRef': '123456'
            }
        }
        
        def create_error_future():
            future = concurrent.futures.Future()
            future.set_result(error_response)
            return future
        
        with patch('asyncio.run_coroutine_threadsafe') as mock_run:
            mock_run.return_value = create_error_future()
            
            failure_result = api.open_close(
                instrument_id="TEST",
                action="kaiduo",
                volume=1,
                price=3500.0,
                block=True,
                timeout=2.0
            )
        
        # 验证：两个结果都包含基本字段
        common_fields = ['success', 'instrument_id', 'action', 'volume', 'price']
        
        for field in common_fields:
            assert field in success_result, \
                f"成功结果应该包含字段 '{field}'"
            assert field in failure_result, \
                f"失败结果应该包含字段 '{field}'"
        
        # 验证：success 标志不同
        assert success_result['success'] is True
        assert failure_result['success'] is False
        
        # 验证：失败结果包含错误信息
        assert 'error_id' in failure_result
        assert 'error_msg' in failure_result
        assert failure_result['error_id'] == 1
        assert failure_result['error_msg'] == '资金不足'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
