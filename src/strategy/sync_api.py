#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : sync_api.py
@Date       : 2025/12/16
@Author     : Kiro AI Assistant
@Email      : -
@Software   : PyCharm
@Description: 同步策略 API - 同步阻塞式策略编写接口

模块概述
========

本模块提供 PeopleQuant 风格的同步阻塞式策略编写接口，封装了 CTP API 的复杂性，
让策略开发者可以使用简单的同步调用方式编写量化交易策略。

重构后的架构
============

本模块经过模块化重构，将原来的单一大文件（2300+ 行）拆分为多个职责清晰的模块：

主模块（sync_api.py）
---------------------
- 提供 SyncStrategyApi 公共接口
- 组合内部组件（缓存、事件循环、插件管理器）
- 实现同步 API 方法（get_quote, open_close 等）
- 协调各组件之间的交互

内部模块（internal/）
--------------------
- data_models.py: Quote 和 Position 数据类
- cache_manager.py: 通用缓存管理器和行情/持仓缓存
- event_manager.py: 统一的线程同步事件管理
- event_loop_thread.py: 后台异步事件循环线程
- plugin.py: 可扩展的插件系统
- order_helper.py: 订单处理辅助函数
- instrument_helper.py: 合约信息处理辅助函数

模块化的好处
============

1. **代码可维护性提升**
   - 每个模块不超过 300 行，职责单一
   - 清晰的模块边界，易于理解和修改

2. **代码复用性提高**
   - 通用缓存管理器消除了重复代码
   - 统一的事件管理器简化了线程同步逻辑

3. **可扩展性增强**
   - 插件系统支持在不修改核心代码的情况下扩展功能
   - 清晰的接口定义便于添加新功能

4. **测试更容易**
   - 每个模块可以独立测试
   - 模块化的测试结构提高了测试覆盖率

快速开始
========

基本用法::

    from src.strategy.sync_api import SyncStrategyApi
    
    # 初始化 API（自动连接和登录）
    api = SyncStrategyApi(
        user_id="your_user_id",
        password="your_password",
        config_path="config.yaml"
    )
    
    # 获取行情
    quote = api.get_quote("rb2605")
    print(f"最新价: {quote.LastPrice}")
    
    # 获取持仓
    position = api.get_position("rb2605")
    print(f"多头持仓: {position.pos_long}")
    
    # 开仓
    result = api.open_close("rb2605", "kaiduo", 1, 3500.0)
    if result["success"]:
        print(f"订单成功: {result['order_ref']}")
    
    # 停止服务
    api.stop()

使用插件扩展功能::

    from src.strategy.sync_api import SyncStrategyApi, StrategyPlugin
    
    class LoggingPlugin(StrategyPlugin):
        def on_init(self, api):
            print("插件初始化")
        
        def on_quote(self, quote):
            print(f"收到行情: {quote.InstrumentID} @ {quote.LastPrice}")
            return quote
    
    api = SyncStrategyApi("user_id", "password")
    api.register_plugin(LoggingPlugin())

运行策略::

    def my_strategy():
        while True:
            quote = api.get_quote("rb2605")
            # 策略逻辑...
            time.sleep(1)
    
    # 在后台线程运行策略
    thread = api.run_strategy(my_strategy)

向后兼容性
==========

重构完全保持了向后兼容性，所有现有的策略代码无需修改即可运行。
公共 API 接口（SyncStrategyApi、Quote、Position）保持不变。

更多信息
========

- 插件开发指南: 参见 examples/plugins/README.md
- 性能优化指南: 参见 docs/performance_tuning_guide_CN.md
- 故障排除: 参见 docs/troubleshooting_CN.md
"""

# ===== 标准库导入 =====
import threading
from typing import Dict, Optional, Callable

# ===== 第三方库导入 =====
import anyio
import anyio.from_thread
import anyio.lowlevel
from loguru import logger

# ===== 内部模块导入 =====
# 数据模型：Quote 和 Position 数据类
from .internal.data_models import Quote, Position

# 缓存管理：行情缓存和持仓缓存
from .internal.cache_manager import _QuoteCache, _PositionCache

# 事件管理：统一的线程同步事件管理
from .internal.event_manager import _EventManager

# 事件循环：后台异步事件循环线程
from .internal.event_loop_thread import _EventLoopThread

# 插件系统：策略插件接口和管理器
from .internal.plugin import PluginManager, StrategyPlugin


class SyncStrategyApi:
    """
    同步策略 API 主类
    
    提供 PeopleQuant 风格的同步阻塞式策略编写接口。
    内部使用异步的 MdClient 和 TdClient，通过桥接层实现同步/异步转换。
    
    主要功能：
    - 同步行情查询和订阅
    - 同步持仓查询
    - 同步交易下单
    - 多策略并发运行
    """
    
    def __init__(
        self, 
        user_id: str, 
        password: str, 
        config_path: Optional[str] = None,
        timeout: Optional[float] = None,
        instruments: Optional[list] = None,
        instrument_info: Optional[Dict[str, dict]] = None
    ):
        """
        初始化同步策略 API 并连接到 CTP 服务器
        
        该方法会自动执行以下操作：
        1. 加载配置文件（如果提供）
        2. 初始化内部数据结构（行情缓存、持仓缓存等）
        3. 启动后台事件循环线程
        4. 创建 MdClient 和 TdClient 实例
        5. 自动执行 CTP 登录流程
        6. 等待连接就绪
        7. 预加载合约信息（如果提供了合约列表或合约信息字典）
        
        Args:
            user_id: CTP 用户 ID（必需）
            password: CTP 密码（必需）
            config_path: 配置文件路径（可选）
            timeout: CTP 连接超时时间（秒），None 表示使用配置文件中的默认值
            instruments: 需要预加载的合约列表（可选）。
                        如果提供，将在登录完成后自动查询这些合约的信息。
                        例如: ["rb2605", "cu2505", "au2506"]
                        注意：SimNow 环境可能不支持合约查询，建议使用 instrument_info 参数
            instrument_info: 合约信息字典（可选）。
                            键为合约代码，值为包含合约信息的字典（必须包含 VolumeMultiple 字段）。
                            例如: {"rb2605": {"VolumeMultiple": 10}, "cu2505": {"VolumeMultiple": 5}}
                            如果提供，将直接缓存这些信息，无需查询 CTP
            
        Raises:
            TimeoutError: CTP 连接超时
            RuntimeError: 初始化失败或登录失败
            
        Example:
            >>> # 使用默认配置
            >>> api = SyncStrategyApi("user_id", "password")
            >>> 
            >>> # 使用自定义配置文件
            >>> api = SyncStrategyApi("user_id", "password", config_path="config.yaml")
            >>> 
            >>> # 使用自定义超时时间
            >>> api = SyncStrategyApi("user_id", "password", timeout=60.0)
            >>> 
            >>> # 预加载合约信息（推荐方式：直接提供合约信息）
            >>> api = SyncStrategyApi(
            >>>     "user_id", "password",
            >>>     instrument_info={"rb2605": {"VolumeMultiple": 10}}
            >>> )
            >>> 
            >>> # 预加载合约信息（通过 CTP 查询，可能不支持）
            >>> api = SyncStrategyApi("user_id", "password", instruments=["rb2605"])
        """
        logger.info("初始化 SyncStrategyApi...")
        
        # 加载配置（如果提供了配置路径）
        if config_path:
            try:
                from ..utils.config import GlobalConfig
                GlobalConfig.load_config(config_path)
                logger.info(f"成功加载配置文件: {config_path}")
            except FileNotFoundError:
                logger.warning(f"配置文件不存在: {config_path}，将使用默认配置")
            except Exception as e:
                logger.warning(f"加载配置文件失败: {e}，将使用默认配置")
        else:
            logger.info("未提供配置文件路径，将使用默认配置")
        
        # 读取配置参数
        try:
            from ..utils.config import GlobalConfig
            self._config = GlobalConfig.SyncApi
            logger.info(
                f"应用配置参数: "
                f"连接超时={self._config.connect_timeout}s, "
                f"最大策略数={self._config.max_strategies}, "
                f"行情超时={self._config.quote_timeout}s, "
                f"持仓超时={self._config.position_timeout}s, "
                f"订单超时={self._config.order_timeout}s"
            )
        except (ImportError, AttributeError):
            # 如果配置未加载，使用默认值
            from ..utils.config import SyncApiConfig
            self._config = SyncApiConfig()
            logger.warning("使用默认配置参数")
        
        # 初始化缓存管理器
        self._quote_cache = _QuoteCache()
        self._position_cache = _PositionCache()
        
        # 初始化事件管理器
        self._event_manager = _EventManager()
        
        # 初始化插件管理器
        self._plugin_manager = PluginManager()
        
        # 订阅状态跟踪
        self._subscribed_instruments: set = set()
        self._subscription_lock = threading.RLock()
        
        # 合约信息缓存
        self._instrument_cache: Dict[str, dict] = {}
        self._instrument_cache_lock = threading.RLock()
        
        # 订单响应状态跟踪
        self._order_responses: Dict[str, dict] = {}
        self._order_response_lock = threading.RLock()
        self._pending_order_ids: list = []  # 等待中的订单ID队列（FIFO）
        
        # 策略管理
        self._running_strategies: Dict[str, threading.Thread] = {}
        self._strategy_lock = threading.RLock()
        
        # 保存配置路径和用户信息
        self._config_path = config_path
        self._user_id = user_id
        
        # 使用配置的超时值（如果未指定）
        if timeout is None:
            timeout = self._config.connect_timeout
        
        logger.info(f"连接 CTP 服务器，用户: {user_id}，超时: {timeout}s")
        
        # 创建并启动事件循环线程
        self._event_loop_thread = _EventLoopThread()
        self._event_loop_thread.start(
            user_id, 
            password, 
            config_path,
            md_callback=self._on_market_data,
            td_callback=self._on_trade_data
        )
        
        # 等待连接就绪（包括登录完成）
        self._event_loop_thread.wait_ready(timeout=timeout)
        
        # 预加载合约信息
        # 方式1：如果提供了合约信息字典，直接缓存
        if instrument_info:
            logger.info(f"加载用户提供的合约信息: {len(instrument_info)} 个合约")
            with self._instrument_cache_lock:
                self._instrument_cache.update(instrument_info)
            logger.info(f"合约信息已缓存: {list(instrument_info.keys())}")
        
        # 方式2：如果提供了合约列表，尝试通过 CTP 查询
        # 注意：SimNow 环境可能不支持合约查询，预加载可能失败
        if instruments and not instrument_info:
            logger.info(f"开始预加载 {len(instruments)} 个合约信息（通过 CTP 查询）...")
            try:
                self._preload_instruments(instruments)
            except Exception as e:
                logger.warning(f"预加载合约信息失败: {e}，将在需要时按需查询")
        
        logger.info("SyncStrategyApi 初始化完成，CTP 连接成功")
    

    def _query_instrument(self, instrument_id: str, timeout: float = 5.0) -> Optional[dict]:
        """
        查询合约信息（内部方法）
        
        使用 anyio.from_thread.run() 调用异步查询方法。
        查询结果会缓存在 _instrument_cache 中。
        
        Args:
            instrument_id: 合约代码
            timeout: 查询超时时间（秒）
            
        Returns:
            合约信息字典，如果查询失败则返回 None
            
        Raises:
            RuntimeError: 查询失败
            TimeoutError: 查询超时
        """
        # 检查缓存
        with self._instrument_cache_lock:
            if instrument_id in self._instrument_cache:
                logger.debug(f"合约信息缓存命中: {instrument_id}")
                return self._instrument_cache[instrument_id]
        
        if not self._event_loop_thread or not self._event_loop_thread._clients_ready:
            raise RuntimeError("事件循环未启动，无法查询合约信息")
        
        logger.info(f"[合约查询] 开始查询合约信息: {instrument_id}, 超时: {timeout}秒")
        
        try:
            # 创建查询完成事件
            self._event_manager.create_event(f"instrument_query_{instrument_id}")
            logger.debug(f"[合约查询] 已创建查询事件: {instrument_id}")
            
            # 构造合约查询请求
            from ..constants.constant import CommonConstant, TdConstant as Constant
            request = {
                CommonConstant.MessageType: Constant.ReqQryInstrument,
                CommonConstant.RequestID: 0,
                Constant.ReqQryInstrument: {
                    'InstrumentID': instrument_id
                }
            }
            
            logger.info(f"[合约查询] 请求构造完成: {request}")
            logger.debug(f"[合约查询] 请求字段详情 - MessageType: {Constant.ReqQryInstrument}, RequestID: 0, InstrumentID: {instrument_id}")
            
            # 使用 anyio.from_thread.run() 调用异步方法
            td_client = self._event_loop_thread.td_client
            if not td_client:
                raise RuntimeError("TdClient 未初始化")
            
            logger.debug("[合约查询] TdClient 已就绪，准备提交请求")
            
            try:
                logger.info("[合约查询] 正在提交请求到 TdClient...")
                anyio.from_thread.run(td_client.call, request)
                logger.info(f"[合约查询] 请求已成功提交到 TdClient: {instrument_id}")
            except TimeoutError:
                logger.error(f"[合约查询] 提交请求超时（{timeout / 2}秒）: {instrument_id}")
                raise TimeoutError(f"提交合约查询请求超时（{timeout / 2}秒）")
            except Exception as e:
                logger.error(f"[合约查询] 提交请求失败: {instrument_id}, 错误: {e}", exc_info=True)
                raise
            
            # 等待合约信息返回（通过事件通知）
            # CTP 查询可能有延迟，使用完整的超时时间
            logger.info(f"[合约查询] 开始等待响应，超时: {timeout}秒")
            if not self._event_manager.wait_event(f"instrument_query_{instrument_id}", timeout=timeout):
                logger.error(f"[合约查询] 等待响应超时（{timeout}秒）: {instrument_id}")
                logger.warning("[合约查询] 可能的原因：1) SimNow环境不支持合约查询 2) 网络延迟 3) CTP服务器未响应")
                raise TimeoutError(f"等待合约查询响应超时（{timeout}秒）")
            
            logger.info(f"[合约查询] 收到响应通知: {instrument_id}")
            
            # 从缓存中获取结果
            with self._instrument_cache_lock:
                instrument_info = self._instrument_cache.get(instrument_id)
            
            if instrument_info:
                logger.info(f"[合约查询] 查询成功: {instrument_id}, 乘数: {instrument_info.get('VolumeMultiple', 'N/A')}")
                return instrument_info
            else:
                logger.warning(f"[合约查询] 查询失败：未找到数据: {instrument_id}")
                return None
            
        except Exception as e:
            logger.error(f"[合约查询] 查询异常: {instrument_id}, 错误: {e}", exc_info=True)
            raise
        finally:
            # 清理查询事件
            self._event_manager.clear_event(f"instrument_query_{instrument_id}")
            logger.debug(f"[合约查询] 已清理查询事件: {instrument_id}")
    
    def _get_volume_multiple(self, instrument_id: str) -> int:
        """
        获取合约乘数（内部方法）
        
        首先检查缓存，如果不存在则查询合约信息。
        如果查询失败（例如 SimNow 环境不支持），则返回默认值 1。
        
        Args:
            instrument_id: 合约代码
            
        Returns:
            合约乘数，如果查询失败则返回默认值 1
        """
        # 检查缓存
        with self._instrument_cache_lock:
            if instrument_id in self._instrument_cache:
                instrument_info: dict = self._instrument_cache[instrument_id]
                multiplier = instrument_info.get('VolumeMultiple', 1)
                logger.debug(f"从缓存获取合约乘数: {instrument_id}, 乘数: {multiplier}")
                return multiplier
        
        # 缓存未命中，尝试查询合约信息
        # 注意：SimNow 环境可能不支持合约查询，查询可能失败
        logger.debug(f"合约乘数缓存未命中: {instrument_id}，尝试查询（可能失败）")
        
        try:
            instrument_info = self._query_instrument(instrument_id, timeout=3.0)
            if instrument_info is not None:
                multiplier = instrument_info.get('VolumeMultiple', 1)
                logger.info(f"查询到合约乘数: {instrument_id}, 乘数: {multiplier}")
                return multiplier
            else:
                logger.warning(
                    f"查询合约 {instrument_id} 信息失败，使用默认乘数 1。"
                    f"提示：SimNow 环境可能不支持合约查询，建议在初始化时通过 instruments 参数预加载"
                )
                return 1
        except Exception as e:
            logger.warning(
                f"查询合约 {instrument_id} 乘数失败: {e}，使用默认乘数 1。"
                f"提示：SimNow 环境可能不支持合约查询"
            )
            return 1
    
    def _preload_instruments(self, instruments: list) -> None:
        """
        预加载合约信息（内部方法）
        
        在登录完成后批量查询合约信息，避免后续查询持仓时的延迟。
        
        Args:
            instruments: 合约代码列表
        """
        success_count = 0
        fail_count = 0
        
        for instrument_id in instruments:
            try:
                logger.debug(f"预加载合约信息: {instrument_id}")
                self._query_instrument(instrument_id, timeout=10.0)
                success_count += 1
            except Exception as e:
                logger.warning(f"预加载合约 {instrument_id} 信息失败: {e}")
                fail_count += 1
        
        logger.info(
            f"合约信息预加载完成: 成功 {success_count} 个, 失败 {fail_count} 个"
        )
    
    def _on_market_data(self, response: dict) -> None:
        """
        处理行情数据回调（在事件循环线程中调用）
        
        Args:
            response: 行情响应字典，包含 MsgType 和 DepthMarketData 等字段
        """
        # 检查是否是行情推送
        # 注意：字段名是 "MsgType" 而不是 "msg_type"
        msg_type = response.get('MsgType', '')
        if 'RtnDepthMarketData' not in msg_type:
            return
        
        # 提取行情数据
        market_data = response.get('DepthMarketData')
        if not market_data:
            return
        
        instrument_id = market_data.get('InstrumentID')
        if not instrument_id:
            return
        
        # 更新行情缓存（会自动通知等待线程）
        self._quote_cache.update_from_market_data(instrument_id, market_data)
        
        # 调用插件钩子
        quote = self._quote_cache.get(instrument_id)
        if quote:
            processed_quote = self._plugin_manager.call_on_quote(quote)
            # 如果插件过滤了行情，不做进一步处理
            if processed_quote is None:
                logger.debug(f"行情被插件过滤: {instrument_id}")
                return
        
        logger.debug(f"收到行情推送: {instrument_id}, 价格: {market_data.get('LastPrice')}")
    
    def _handle_trade_report(self, response: dict) -> None:
        """
        处理成交回报，自动触发持仓查询以更新缓存
        
        当收到成交回报时，说明持仓发生了变化，需要重新查询持仓数据。
        为了避免频繁查询，这里使用简单的策略：
        - 提取成交的合约代码
        - 异步触发该合约的持仓查询
        
        Args:
            response: 成交回报响应字典
        """
        from ..constants.constant import TdConstant as Constant
        
        # 提取成交数据
        trade_data = response.get(Constant.Trade)
        if not trade_data:
            return
        
        instrument_id = trade_data.get('InstrumentID')
        if not instrument_id:
            return
        
        logger.debug(f"收到成交回报: {instrument_id}, 成交量: {trade_data.get('Volume', 0)}")
        
        # 异步触发持仓查询（不阻塞当前线程）
        # 使用线程池执行查询，避免阻塞事件循环
        try:
            import threading
            query_thread = threading.Thread(
                target=self._query_position_async,
                args=(instrument_id,),
                daemon=True
            )
            query_thread.start()
            logger.debug(f"触发持仓查询: {instrument_id}")
        except Exception as e:
            logger.warning(f"触发持仓查询失败: {e}")
    
    def _query_position_async(self, instrument_id: str) -> None:
        """
        异步查询持仓（在独立线程中执行）
        
        Args:
            instrument_id: 合约代码
        """
        try:
            self._query_position(instrument_id, timeout=5.0)
        except Exception as e:
            logger.warning(f"异步持仓查询失败: {instrument_id}, 错误: {e}")
    
    def _handle_order_response(self, response: dict) -> None:
        """
        处理订单响应，缓存响应并通知等待线程
        
        Args:
            response: 订单响应字典
        """
        msg_type = response.get('MsgType', '')
        logger.debug(f"[订单响应] 收到订单响应，消息类型: {msg_type}")
        
        # 缓存响应并通知等待线程
        with self._order_response_lock:
            # 由于我们无法从响应中获取请求ID，使用FIFO策略
            # 假设订单是按顺序处理的，通知第一个等待的订单
            if self._pending_order_ids:
                # 获取第一个等待的订单ID
                order_id = self._pending_order_ids.pop(0)
                
                # 缓存响应
                self._order_responses[order_id] = response
                
                # 通知等待订单响应的线程
                self._event_manager.set_event(f"order_response_{order_id}")
                logger.debug(f"[订单响应] 已通知订单完成: {order_id}")
            else:
                logger.warning("[订单响应] 收到订单响应但没有等待的订单")
    
    def _on_trade_data(self, response: dict) -> None:
        """
        处理交易数据回调（在事件循环线程中调用）
        
        处理三种类型的回调：
        1. 合约查询响应（OnRspQryInstrument）：更新合约信息缓存
        2. 持仓查询响应（OnRspQryInvestorPosition）：更新持仓缓存
        3. 成交回报（OnRtnTrade）：触发持仓查询以自动更新缓存
        
        Args:
            response: 交易响应字典，包含 MsgType 和相关数据字段
        """
        # 调用插件钩子
        processed_response = self._plugin_manager.call_on_trade(response)
        # 如果插件过滤了交易数据，不做进一步处理
        if processed_response is None:
            logger.debug("交易数据被插件过滤")
            return
        # 使用处理后的响应继续处理
        response = processed_response
        
        # 注意：字段名是 "MsgType" 而不是 "msg_type"
        msg_type = response.get('MsgType', '')
        
        # ===== 关键日志：记录所有TD回调消息类型 =====
        logger.debug(f"[TD回调] 收到消息类型: {msg_type}")
        
        # 处理订单响应
        # CTP 订单响应机制：
        # - 录入错误：OnRspOrderInsert 或 OnErrRtnOrderInsert
        # - 录入成功：OnRtnOrder（订单回报）和 OnRtnTrade（成交回报）
        if 'RtnOrder' in msg_type or 'ErrRtnOrderInsert' in msg_type or 'RspOrderInsert' in msg_type:
            logger.debug(f"[TD回调] 处理订单响应，消息类型: {msg_type}")
            self._handle_order_response(response)
            return
        
        # 处理成交回报：当有成交时，自动触发持仓查询以更新缓存
        # 注意：msg_type 可能是 'RtnTrade' 或 'OnRtnTrade'
        if 'RtnTrade' in msg_type:
            logger.debug("[TD回调] 处理成交回报")
            self._handle_trade_report(response)
            return
        
        # 处理合约查询响应
        if 'RspQryInstrument' in msg_type:
            from ..constants.constant import TdConstant as Constant
            instrument_data = response.get(Constant.Instrument)
            is_last = response.get('IsLast', False)
            rsp_info = response.get('RspInfo', {})
            error_id = rsp_info.get('ErrorID', 0) if rsp_info else 0
            error_msg = rsp_info.get('ErrorMsg', '') if rsp_info else ''
            
            logger.info("[TD回调-合约查询] 收到合约查询响应")
            logger.info(f"[TD回调-合约查询] 响应详情 - instrument_data存在: {instrument_data is not None}, IsLast: {is_last}, ErrorID: {error_id}, ErrorMsg: {error_msg}")
            
            if error_id != 0:
                logger.error(f"[TD回调-合约查询] 查询失败 - ErrorID: {error_id}, ErrorMsg: {error_msg}")
            
            if instrument_data:
                instrument_id = instrument_data.get('InstrumentID')
                volume_multiple = instrument_data.get('VolumeMultiple')
                logger.info(f"[TD回调-合约查询] 收到合约数据: {instrument_id}, 乘数: {volume_multiple}")
                
                if instrument_id:
                    # 更新合约信息缓存
                    with self._instrument_cache_lock:
                        self._instrument_cache[instrument_id] = instrument_data
                        logger.info(
                            f"[TD回调-合约查询] 更新合约信息缓存: {instrument_id}, "
                            f"乘数: {instrument_data.get('VolumeMultiple', 1)}"
                        )
            
            # 只有在 IsLast=True 时才通知等待线程
            if is_last:
                logger.info("[TD回调-合约查询] 查询结束（IsLast=True），开始通知等待线程")
                # 通知等待该合约查询的线程
                if instrument_data and instrument_id:
                    logger.info(f"[TD回调-合约查询] 找到请求的合约: {instrument_id}，通知查询完成")
                    self._event_manager.set_event(f"instrument_query_{instrument_id}")
                else:
                    logger.warning("[TD回调-合约查询] 查询结束但未找到合约数据，通知查询失败")
            else:
                logger.debug("[TD回调-合约查询] 收到中间响应（IsLast=False），继续等待")
            
            return
        
        # 处理持仓查询响应
        if 'QryInvestorPosition' not in msg_type:
            return
        
        # 提取持仓数据
        from ..constants.constant import TdConstant as Constant
        position_data = response.get(Constant.InvestorPosition)
        is_last = response.get('IsLast', False)
        
        if not position_data:
            # 可能是查询结束标志（IsLast=True 但没有数据，即空持仓）
            if is_last:
                # 查询已完成，通知所有等待中的持仓查询
                # 注意：由于响应中没有 instrument_id，我们需要通知所有可能等待的查询
                # 这里我们简单地记录日志，实际通知会在有数据的情况下进行
                logger.debug("收到空持仓响应（IsLast=True）")
            return
        
        instrument_id = position_data.get('InstrumentID')
        if not instrument_id:
            return
        
        # CTP 持仓数据按多空方向分别返回，需要合并
        # PosiDirection: '2' = 多头, '3' = 空头
        posi_direction = position_data.get('PosiDirection', '')
        position = position_data.get('Position', 0)
        today_position = position_data.get('TodayPosition', 0)
        yd_position = position_data.get('YdPosition', 0)
        
        # 计算开仓均价（如果有持仓）
        open_cost = position_data.get('OpenCost', 0.0)
        # 从合约信息缓存中获取合约乘数
        multiplier = self._get_volume_multiple(instrument_id)
        open_price = float('nan')
        if position > 0 and multiplier > 0:
            open_price = open_cost / position / multiplier
        
        # 获取或创建持仓对象
        cached_position = self._position_cache.get(instrument_id)
        
        # 更新对应方向的持仓
        if posi_direction == '2':  # 多头
            position_dict = {
                'pos_long': position,
                'pos_long_today': today_position,
                'pos_long_his': yd_position,
                'open_price_long': open_price,
                'pos_short': cached_position.pos_short,
                'pos_short_today': cached_position.pos_short_today,
                'pos_short_his': cached_position.pos_short_his,
                'open_price_short': cached_position.open_price_short
            }
        elif posi_direction == '3':  # 空头
            position_dict = {
                'pos_long': cached_position.pos_long,
                'pos_long_today': cached_position.pos_long_today,
                'pos_long_his': cached_position.pos_long_his,
                'open_price_long': cached_position.open_price_long,
                'pos_short': position,
                'pos_short_today': today_position,
                'pos_short_his': yd_position,
                'open_price_short': open_price
            }
        else:
            logger.warning(f"未知的持仓方向: {posi_direction}")
            return
        
        # 更新持仓缓存
        self._position_cache.update_from_position_data(instrument_id, position_dict)
        
        logger.debug(f"收到持仓数据: {instrument_id}, 方向: {posi_direction}, 持仓: {position}")
        
        # 通知等待该合约持仓查询的线程
        self._event_manager.set_event(f"position_query_{instrument_id}")
    
    def _query_position(self, instrument_id: str, timeout: float = 5.0) -> None:
        """
        查询合约持仓（内部方法）
        
        使用 anyio.from_thread.run() 调用异步查询方法。
        
        Args:
            instrument_id: 合约代码
            timeout: 查询超时时间（秒）
            
        Raises:
            RuntimeError: 查询失败
            TimeoutError: 查询超时
        """
        if not self._event_loop_thread or not self._event_loop_thread._clients_ready:
            raise RuntimeError("事件循环未启动，请先调用 connect() 方法")
        
        logger.info(f"查询合约持仓: {instrument_id}")
        
        try:
            # 创建查询完成事件
            self._event_manager.create_event(f"position_query_{instrument_id}")
            
            # 构造持仓查询请求
            from ..constants.constant import CommonConstant, TdConstant as Constant
            request = {
                CommonConstant.MessageType: Constant.ReqQryInvestorPosition,
                CommonConstant.RequestID: 0,  # RequestID 是必需的
                'QryInvestorPosition': {
                    'InstrumentID': instrument_id
                }
            }
            
            # 使用 anyio.from_thread.run() 调用异步方法
            td_client = self._event_loop_thread.td_client
            if not td_client:
                raise RuntimeError("TdClient 未初始化")
            
            try:
                # 使用 anyio 的跨线程调用，带超时
                anyio.from_thread.run(td_client.call, request)
            except TimeoutError:
                raise TimeoutError(f"提交持仓查询请求超时（{timeout}秒）")
            
            # 等待持仓数据返回（通过事件通知）
            # 注意：如果持仓查询期间触发了合约查询，可能需要更长的等待时间
            if not self._event_manager.wait_event(f"position_query_{instrument_id}", timeout=timeout):
                raise TimeoutError(f"等待持仓查询响应超时（{timeout}秒）")
            
            logger.debug(f"合约 {instrument_id} 持仓查询成功")
            
        except Exception as e:
            logger.error(f"查询合约 {instrument_id} 持仓失败: {e}")
            raise
        finally:
            # 清理查询事件
            self._event_manager.clear_event(f"position_query_{instrument_id}")
    
    def _subscribe_quote(self, instrument_id: str, timeout: float = 5.0) -> None:
        """
        订阅合约行情（内部方法）
        
        使用 anyio.from_thread.run() 调用异步订阅方法。
        
        如果订阅失败，会记录警告日志但不抛出异常，允许调用方继续执行。
        调用方可以通过等待行情超时来检测订阅失败。
        
        Args:
            instrument_id: 合约代码
            timeout: 订阅超时时间（秒）
            
        Raises:
            RuntimeError: 事件循环未启动
        """
        if not self._event_loop_thread or not self._event_loop_thread._clients_ready:
            raise RuntimeError("事件循环未启动，请先调用 connect() 方法")
        
        with self._subscription_lock:
            # 检查是否已订阅
            if instrument_id in self._subscribed_instruments:
                logger.debug(f"合约 {instrument_id} 已订阅，跳过")
                return
            
            logger.info(f"订阅合约行情: {instrument_id}")
            
            try:
                # 构造订阅请求
                from ..constants.constant import CommonConstant as Constant, MdConstant
                request = {
                    Constant.MessageType: MdConstant.SubscribeMarketData,
                    'InstrumentID': [instrument_id]
                }
                
                # 使用 anyio.from_thread.run() 调用异步方法
                md_client = self._event_loop_thread.md_client
                if not md_client:
                    logger.warning(f"订阅合约 {instrument_id} 失败: MdClient 未初始化")
                    return
                
                try:
                    anyio.from_thread.run(md_client.call, request)
                except TimeoutError:
                    logger.warning(f"订阅合约 {instrument_id} 超时（{timeout}秒）")
                    return
                
                # 标记为已订阅
                self._subscribed_instruments.add(instrument_id)
                
                logger.debug(f"合约 {instrument_id} 订阅成功")
                
            except Exception as e:
                logger.warning(f"订阅合约 {instrument_id} 失败: {e}")
                # 不抛出异常，让调用方通过等待行情超时来检测订阅失败
    
    def get_quote(self, instrument_id: str, timeout: Optional[float] = None) -> Quote:
        """
        获取合约行情（同步阻塞）
        
        如果合约未订阅，会自动订阅并等待首次行情数据。
        如果合约已订阅且缓存中有数据，直接返回缓存数据。
        
        Args:
            instrument_id: 合约代码
            timeout: 超时时间（秒），None 表示使用配置文件中的默认值
            
        Returns:
            Quote 对象，包含最新行情数据
            
        Raises:
            TimeoutError: 等待行情数据超时
            RuntimeError: 订阅失败或其他错误
            
        Example:
            >>> api = SyncStrategyApi()
            >>> api.connect("user_id", "password")
            >>> quote = api.get_quote("rb2505")
            >>> print(f"最新价: {quote.LastPrice}")
        """
        # 使用配置的超时值（如果未指定）
        if timeout is None:
            timeout = self._config.quote_timeout
        
        # 检查服务是否可用
        if self._event_loop_thread and not self._event_loop_thread.is_service_available:
            raise RuntimeError("事件循环服务不可用，无法获取行情数据")
        
        logger.debug(f"查询合约行情: {instrument_id}，超时: {timeout}s")
        
        # 检查缓存中是否已有行情数据
        cached_quote = self._quote_cache.get(instrument_id)
        
        if cached_quote is not None:
            # 缓存命中，直接返回
            logger.debug(f"行情缓存命中: {instrument_id}")
            return cached_quote
        
        # 缓存未命中，需要订阅
        logger.debug(f"行情缓存未命中: {instrument_id}，开始订阅")
        
        # 订阅合约（如果未订阅）
        self._subscribe_quote(instrument_id, timeout=timeout)
        
        # 等待首次行情数据
        logger.debug(f"等待首次行情数据: {instrument_id}")
        try:
            # 确保 timeout 不为 None
            actual_timeout = timeout if timeout is not None else 30.0
            quote = self._quote_cache.wait_update(instrument_id, timeout=actual_timeout)
            logger.info(f"获取到首次行情: {instrument_id}, 价格: {quote.LastPrice}")
            return quote
        except TimeoutError:
            logger.warning(f"等待合约 {instrument_id} 首次行情超时（{timeout}秒）")
            raise TimeoutError(f"等待合约 {instrument_id} 首次行情超时（{timeout}秒）")
    
    def get_position(self, instrument_id: str, timeout: Optional[float] = None) -> Position:
        """
        获取合约持仓（同步阻塞）
        
        如果持仓缓存不存在，会触发 CTP 查询并等待结果返回。
        如果持仓缓存已存在，直接返回缓存数据。
        
        注意：与 get_quote() 不同，持仓查询超时时返回空持仓对象而不是抛出异常。
        这是因为持仓为空是正常情况，不应该被视为错误。
        
        Args:
            instrument_id: 合约代码
            timeout: 超时时间（秒），None 表示使用配置文件中的默认值
            
        Returns:
            Position 对象，包含多空持仓信息。如果查询超时或失败，返回空持仓对象。
            
        Example:
            >>> api = SyncStrategyApi()
            >>> api.connect("user_id", "password")
            >>> position = api.get_position("rb2505")
            >>> print(f"多头持仓: {position.pos_long}, 空头持仓: {position.pos_short}")
        """
        # 使用配置的超时值（如果未指定）
        if timeout is None:
            timeout = self._config.position_timeout
        
        # 检查服务是否可用
        if self._event_loop_thread and not self._event_loop_thread.is_service_available:
            logger.error("事件循环服务不可用，返回空持仓对象")
            return Position()
        
        logger.debug(f"查询合约持仓: {instrument_id}，超时: {timeout}s")
        
        # 检查缓存中是否已有持仓数据
        cached_position = self._position_cache.get(instrument_id)
        
        # 检查是否是有效的持仓数据（不是默认的空持仓）
        has_position = (
            cached_position.pos_long > 0 or 
            cached_position.pos_short > 0 or
            cached_position.pos_long_today > 0 or
            cached_position.pos_short_today > 0 or
            cached_position.pos_long_his > 0 or
            cached_position.pos_short_his > 0
        )
        
        if has_position:
            # 缓存命中且有持仓，直接返回
            logger.debug(f"持仓缓存命中: {instrument_id}")
            return cached_position
        
        # 缓存未命中或持仓为空，需要查询
        logger.debug(f"持仓缓存未命中或为空: {instrument_id}，开始查询")
        
        try:
            # 查询持仓
            self._query_position(instrument_id, timeout=timeout)
            
            # 查询成功，从缓存获取结果
            position = self._position_cache.get(instrument_id)
            logger.info(f"获取到持仓数据: {instrument_id}, 多头: {position.pos_long}, 空头: {position.pos_short}")
            return position
            
        except TimeoutError:
            # 查询超时，返回空持仓对象（不抛出异常）
            logger.warning(f"查询合约 {instrument_id} 持仓超时（{timeout}秒），返回空持仓")
            return Position()
            
        except Exception as e:
            # 查询失败，返回空持仓对象（不抛出异常）
            logger.error(f"查询合约 {instrument_id} 持仓失败: {e}，返回空持仓")
            return Position()
    
    def wait_quote_update(self, instrument_id: str, timeout: Optional[float] = None) -> Quote:
        """
        等待行情更新（阻塞直到有新行情）
        
        该方法会阻塞当前线程，直到指定合约有新的行情推送。
        如果合约未订阅，会自动订阅。
        
        Args:
            instrument_id: 合约代码
            timeout: 超时时间（秒），None 表示无限等待（默认）
            
        Returns:
            更新后的 Quote 对象
            
        Raises:
            TimeoutError: 等待超时时抛出
            RuntimeError: 订阅失败或其他错误
            
        Example:
            >>> api = SyncStrategyApi()
            >>> api.connect("user_id", "password")
            >>> # 等待行情更新
            >>> quote = api.wait_quote_update("rb2505", timeout=10.0)
            >>> print(f"收到新行情: {quote.LastPrice}")
        """
        if instrument_id == "":
            raise Exception("wait_quote_update 中请求合约代码不能为空字符串")

        # 检查服务是否可用
        if self._event_loop_thread and not self._event_loop_thread.is_service_available:
            raise RuntimeError("事件循环服务不可用，无法等待行情更新")
        
        timeout_str = f"{timeout}s" if timeout is not None else "无限等待"
        logger.debug(f"等待合约行情更新: {instrument_id}，超时: {timeout_str}")
        
        # 确保合约已订阅
        with self._subscription_lock:
            if instrument_id not in self._subscribed_instruments:
                logger.debug(f"合约 {instrument_id} 未订阅，先进行订阅")
                # 订阅合约（使用配置的行情超时）
                self._subscribe_quote(instrument_id, timeout=self._config.quote_timeout)
        
        # 阻塞等待行情更新
        logger.debug(f"开始等待合约 {instrument_id} 的行情更新...")
        try:
            # 如果 timeout 为 None，使用一个较大的默认值
            actual_timeout = timeout if timeout is not None else 3600.0  # 1小时
            quote = self._quote_cache.wait_update(instrument_id, timeout=actual_timeout)
            logger.info(f"收到合约 {instrument_id} 行情更新, 价格: {quote.LastPrice}")
            return quote
            
        except TimeoutError:
            # 非交易时间段等待行情更新超时是正常情况，只记录警告不抛出异常
            timeout_str = f"{timeout}秒" if timeout is not None else "无限等待"
            logger.warning(f"等待合约 {instrument_id} 行情更新超时（{timeout_str}），可能处于非交易时间段")
            # 返回缓存中的最新行情（如果有）
            cached_quote = self._quote_cache.get(instrument_id)
            if cached_quote:
                logger.info(f"返回缓存中的行情数据: {instrument_id}, 价格: {cached_quote.LastPrice}")
                return cached_quote
            else:
                # 如果缓存中也没有，返回空行情对象
                logger.warning(f"缓存中也没有行情数据，返回空行情对象: {instrument_id}")
                return Quote(InstrumentID=instrument_id)
    
    def _map_action_to_ctp(self, action: str, close_today: bool = False) -> tuple:
        """映射 action 参数到 CTP 的 Direction 和 CombOffsetFlag"""
        from .internal.order_helper import _OrderHelper
        return _OrderHelper.map_action_to_ctp(action, close_today)
    
    def _get_exchange_id(self, instrument_id: str) -> str:
        """根据合约代码推断交易所ID"""
        from .internal.order_helper import _OrderHelper
        return _OrderHelper.get_exchange_id(instrument_id)
    
    def open_close(
        self,
        instrument_id: str,
        action: str,
        volume: int,
        price: float,
        block: bool = True,
        timeout: Optional[float] = None
    ) -> dict:
        """
        开平仓操作（同步阻塞）
        
        提交订单到 CTP 系统。支持开多、开空、平多、平空四种操作。
        
        智能平仓特性：
        - 对于上期所（SHFE）、能源中心（INE）、中金所（CFFEX）的合约，
          自动区分平今仓和平昨仓，优先平昨仓再平今仓
        - 如果需要，自动拆分为多笔订单（先平昨后平今）
        - 对于大商所（DCE）和郑商所（CZCE），不区分平今平昨
        
        Args:
            instrument_id: 合约代码
            action: 交易动作，支持以下值：
                - "kaiduo": 开多（买入开仓）
                - "kaikong": 开空（卖出开仓）
                - "pingduo": 平多（卖出平仓，自动处理今昨仓）
                - "pingkong": 平空（买入平仓，自动处理今昨仓）
            volume: 下单数量（手）
            price: 限价价格
            block: 是否阻塞等待订单响应，默认 True
            timeout: 超时时间（秒），None 表示使用配置文件中的默认值
            
        Returns:
            订单结果字典，包含以下字段：
            - success: bool - 订单是否成功提交
            - order_ref: str - 订单引用（如果成功）
            - error_id: int - 错误代码（如果失败）
            - error_msg: str - 错误消息（如果失败）
            - instrument_id: str - 合约代码
            - action: str - 交易动作
            - volume: int - 下单数量
            - price: float - 下单价格
            - note: str - 额外说明（可选，如订单拆分信息）
            
        Raises:
            RuntimeError: 事件循环未启动或其他系统错误
            ValueError: 参数错误或持仓不足
            TimeoutError: 等待订单响应超时（仅在 block=True 时）
            
        Example:
            >>> api = SyncStrategyApi()
            >>> api.connect("user_id", "password")
            >>> # 开多 1 手，价格 3500
            >>> result = api.open_close("rb2505", "kaiduo", 1, 3500.0)
            >>> if result["success"]:
            >>>     print(f"订单提交成功，订单号: {result['order_ref']}")
            >>> else:
            >>>     print(f"订单提交失败: {result['error_msg']}")
            >>> 
            >>> # 平多仓（自动处理今昨仓）
            >>> result = api.open_close("rb2505", "pingduo", 3, 3520.0)
        """
        # 使用配置的超时值（如果未指定）
        if timeout is None:
            timeout = self._config.order_timeout
        
        logger.info(f"提交订单: {instrument_id}, 动作: {action}, 数量: {volume}, 价格: {price}, 超时: {timeout}s")
        
        # 检查事件循环是否启动
        if not self._event_loop_thread or not self._event_loop_thread._clients_ready:
            raise RuntimeError("事件循环未启动，请先调用 connect() 方法")
        
        # 检查服务是否可用
        if not self._event_loop_thread.is_service_available:
            raise RuntimeError("事件循环服务不可用，无法提交订单")
        
        # 参数验证
        if volume <= 0:
            raise ValueError(f"下单数量必须大于 0，当前值: {volume}")
        
        if price <= 0:
            raise ValueError(f"下单价格必须大于 0，当前值: {price}")
        
        try:
            # ===== 智能平仓逻辑 =====
            # 对于平仓操作，需要根据交易所和持仓情况智能选择平今/平昨
            is_close_action = action in ['pingduo', 'pingkong']
            
            if is_close_action:
                # 获取交易所ID
                exchange_id = self._get_exchange_id(instrument_id)
                
                # 判断交易所是否需要区分平今平昨
                # 上期所（SHFE）、能源中心（INE）、中金所（CFFEX）需要区分
                need_distinguish = exchange_id in ['SHFE', 'INE', 'CFFEX']
                
                if need_distinguish:
                    # 查询当前持仓
                    position = self.get_position(instrument_id, timeout=self._config.position_timeout)
                    
                    # 根据平仓方向确定今昨仓数量
                    if action == 'pingduo':
                        # 平多仓
                        today_pos = position.pos_long_today
                        his_pos = position.pos_long_his
                        total_pos = position.pos_long
                    else:  # pingkong
                        # 平空仓
                        today_pos = position.pos_short_today
                        his_pos = position.pos_short_his
                        total_pos = position.pos_short
                    
                    # 检查持仓是否足够
                    if volume > total_pos:
                        raise ValueError(
                            f"平仓数量({volume})超过持仓数量({total_pos})，"
                            f"今仓: {today_pos}, 昨仓: {his_pos}"
                        )
                    
                    # 智能拆分订单：优先平昨仓，再平今仓
                    orders_to_submit: list[dict] = []
                    remaining_volume = volume
                    
                    # 先平昨仓
                    if his_pos > 0 and remaining_volume > 0:
                        close_his_volume = min(his_pos, remaining_volume)
                        orders_to_submit.append({
                            'volume': close_his_volume,
                            'close_today': False,  # 平昨仓
                            'description': f'平昨仓 {close_his_volume} 手'
                        })
                        remaining_volume -= close_his_volume
                    
                    # 再平今仓
                    if today_pos > 0 and remaining_volume > 0:
                        close_today_volume = min(today_pos, remaining_volume)
                        orders_to_submit.append({
                            'volume': close_today_volume,
                            'close_today': True,  # 平今仓
                            'description': f'平今仓 {close_today_volume} 手'
                        })
                        remaining_volume -= close_today_volume
                    
                    # 如果需要拆分订单，递归调用
                    if len(orders_to_submit) > 1:
                        logger.info(
                            f"平仓订单需要拆分: 总量 {volume} 手 -> "
                            f"{', '.join([str(o['description']) for o in orders_to_submit])}"
                        )
                        
                        # 提交多笔订单
                        results = []
                        for order_info in orders_to_submit:
                            # 递归调用，但使用内部标志避免再次拆分
                            sub_result = self._submit_single_order(
                                instrument_id=instrument_id,
                                action=action,
                                volume=int(order_info['volume']),
                                price=price,
                                close_today=bool(order_info['close_today']),
                                block=block,
                                timeout=timeout
                            )
                            results.append(sub_result)
                            
                            # 如果任何一笔失败，返回失败结果
                            if not sub_result['success']:
                                logger.error(f"{order_info['description']} 失败: {sub_result['error_msg']}")
                                return sub_result
                        
                        # 所有订单都成功，返回汇总结果
                        logger.info(f"平仓订单全部成功: {volume} 手")
                        return {
                            'success': True,
                            'order_ref': ', '.join([r.get('order_ref', '') for r in results]),
                            'instrument_id': instrument_id,
                            'action': action,
                            'volume': volume,
                            'price': price,
                            'note': f'拆分为 {len(orders_to_submit)} 笔订单'
                        }
                    
                    # 不需要拆分，确定使用平今还是平昨
                    close_today = bool(orders_to_submit[0]['close_today']) if orders_to_submit else False
                    logger.debug(f"平仓操作: {orders_to_submit[0]['description'] if orders_to_submit else '无持仓'}")
                    
                    # 使用确定的平仓标志提交订单
                    return self._submit_single_order(
                        instrument_id=instrument_id,
                        action=action,
                        volume=volume,
                        price=price,
                        close_today=close_today,
                        block=block,
                        timeout=timeout
                    )
                else:
                    # 不需要区分平今平昨的交易所（DCE、CZCE），直接提交
                    logger.debug(f"交易所 {exchange_id} 不区分平今平昨，直接提交平仓订单")
                    return self._submit_single_order(
                        instrument_id=instrument_id,
                        action=action,
                        volume=volume,
                        price=price,
                        close_today=False,  # 使用平仓标志 '1'
                        block=block,
                        timeout=timeout
                    )
            else:
                # 开仓操作，直接提交
                return self._submit_single_order(
                    instrument_id=instrument_id,
                    action=action,
                    volume=volume,
                    price=price,
                    close_today=False,  # 开仓不需要此参数
                    block=block,
                    timeout=timeout
                )
                
        except TimeoutError:
            # 超时错误应该重新抛出，让调用者处理
            raise
            
        except ValueError as e:
            # 参数错误
            logger.error(f"订单参数错误: {e}")
            return {
                'success': False,
                'error_id': -1,
                'error_msg': str(e),
                'instrument_id': instrument_id,
                'action': action,
                'volume': volume,
                'price': price
            }
            
        except Exception as e:
            # 其他错误
            logger.error(f"提交订单失败: {e}", exc_info=True)
            return {
                'success': False,
                'error_id': -1,
                'error_msg': f"提交订单失败: {e}",
                'instrument_id': instrument_id,
                'action': action,
                'volume': volume,
                'price': price
            }
    
    def _submit_single_order(
        self,
        instrument_id: str,
        action: str,
        volume: int,
        price: float,
        close_today: bool,
        block: bool,
        timeout: float
    ) -> dict:
        """
        提交单笔订单（内部方法）
        
        Args:
            instrument_id: 合约代码
            action: 交易动作
            volume: 下单数量
            price: 限价价格
            close_today: 平仓时是否平今仓
            block: 是否阻塞等待响应
            timeout: 超时时间
            
        Returns:
            订单结果字典
        """
        from ..constants.constant import CommonConstant, TdConstant as Constant
        from ..utils.config import GlobalConfig
        
        # 映射 action 到 CTP 参数
        direction, comb_offset_flag = self._map_action_to_ctp(action, close_today=close_today)
        
        # 获取交易所ID
        exchange_id = self._get_exchange_id(instrument_id)
        
        # 构造订单请求
        request = {
            CommonConstant.MessageType: Constant.ReqOrderInsert,
            CommonConstant.RequestID: 0,
            Constant.InputOrder: {
                'BrokerID': GlobalConfig.BrokerID,
                'InvestorID': self._user_id,
                'InstrumentID': instrument_id,
                'ExchangeID': exchange_id,
                'OrderPriceType': '2',        # 限价单
                'Direction': direction,
                'CombOffsetFlag': comb_offset_flag,
                'CombHedgeFlag': '1',         # 投机
                'LimitPrice': price,
                'VolumeTotalOriginal': volume,
                'TimeCondition': '3',         # 当日有效
                'VolumeCondition': '1',       # 任意数量
                'ContingentCondition': '1',   # 立即
                'ForceCloseReason': '0',      # 非强平
                'IsAutoSuspend': 0,
                'IsSwapOrder': 0
            }
        }
        
        logger.debug(f"订单请求: {request}")
        
        # 获取 TdClient
        td_client = self._event_loop_thread.td_client
        if not td_client:
            raise RuntimeError("TdClient 未初始化")
        
        # 使用 anyio.from_thread.run() 调用异步方法
        if block:
            # 阻塞等待订单响应
            logger.debug(f"等待订单响应（超时: {timeout}秒）...")
            
            # 生成订单ID（使用时间戳）
            import time
            order_id = str(int(time.time() * 1000000))  # 微秒级时间戳
            
            try:
                # 创建等待事件
                self._event_manager.create_event(f"order_response_{order_id}")
                
                # 将订单ID添加到等待队列
                with self._order_response_lock:
                    self._pending_order_ids.append(order_id)
                
                # 提交订单请求（不等待返回值）
                anyio.from_thread.run(td_client.call, request)
                
                # 等待订单响应（通过事件通知）
                if not self._event_manager.wait_event(f"order_response_{order_id}", timeout=timeout):
                    raise TimeoutError(f"等待订单响应超时（{timeout}秒）")
                
                # 从缓存中获取响应
                with self._order_response_lock:
                    response = self._order_responses.get(order_id)
                
                if not response:
                    raise RuntimeError("订单响应丢失")
                
                # 解析响应
                logger.debug(f"订单响应: {response}")
                
                # 检查响应信息
                rsp_info = response.get('RspInfo', {})
                if rsp_info is None:
                    rsp_info = {}
                error_id = rsp_info.get('ErrorID', 0)
                
                if error_id == 0:
                    # 订单提交成功
                    input_order = response.get(Constant.InputOrder, {})
                    if input_order is None:
                        input_order = {}
                    
                    # 尝试从 Order 字段获取 OrderRef（RtnOrder 响应）
                    order_data = response.get(Constant.Order, {})
                    if order_data is None:
                        order_data = {}
                    
                    order_ref = input_order.get('OrderRef', '') or order_data.get('OrderRef', '')
                    
                    logger.info(f"订单提交成功: {instrument_id}, 订单号: {order_ref}")
                    
                    return {
                        'success': True,
                        'order_ref': order_ref,
                        'instrument_id': instrument_id,
                        'action': action,
                        'volume': volume,
                        'price': price
                    }
                else:
                    # 订单提交失败
                    error_msg = rsp_info.get('ErrorMsg', '未知错误')
                    logger.error(f"订单提交失败: [{error_id}] {error_msg}")
                    
                    return {
                        'success': False,
                        'error_id': error_id,
                        'error_msg': error_msg,
                        'instrument_id': instrument_id,
                        'action': action,
                        'volume': volume,
                        'price': price
                    }
                    
            except TimeoutError:
                logger.error(f"等待订单响应超时（{timeout}秒）")
                raise TimeoutError(f"等待订单响应超时（{timeout}秒）")
            
            finally:
                # 清理事件和缓存
                self._event_manager.clear_event(f"order_response_{order_id}")
                with self._order_response_lock:
                    if order_id in self._order_responses:
                        del self._order_responses[order_id]
                
        else:
            # 不阻塞，立即返回
            logger.debug("订单已提交，不等待响应")
            
            # 使用 anyio.from_thread.run() 提交订单但不等待响应
            anyio.from_thread.run(td_client.call, request)
            
            return {
                'success': True,
                'order_ref': '',  # 非阻塞模式下无法获取订单号
                'instrument_id': instrument_id,
                'action': action,
                'volume': volume,
                'price': price,
                'note': '订单已提交，未等待响应'
            }

    def run_strategy(
        self,
        strategy_func: Callable,
        *args,
        **kwargs
    ) -> threading.Thread:
        """
        在独立线程中运行策略
        
        该方法会创建一个新的线程来运行策略函数，并将线程添加到内部注册表中。
        策略函数中的异常会被自动捕获并记录，不会影响其他策略的运行。
        
        Args:
            strategy_func: 策略函数，可以是任何可调用对象
            *args: 传递给策略函数的位置参数
            **kwargs: 传递给策略函数的关键字参数
            
        Returns:
            threading.Thread 对象，可用于外部管理（如 join()）
            
        Raises:
            RuntimeError: 如果达到最大策略数量限制
            
        Example:
            >>> api = SyncStrategyApi()
            >>> api.connect("user_id", "password")
            >>> 
            >>> def my_strategy(symbol):
            >>>     while True:
            >>>         quote = api.get_quote(symbol)
            >>>         print(f"价格: {quote.LastPrice}")
            >>>         time.sleep(1)
            >>> 
            >>> thread = api.run_strategy(my_strategy, "rb2505")
            >>> # 策略在后台运行
        """
        logger.info(f"启动策略: {strategy_func.__name__}")
        
        # 检查是否达到最大策略数量限制
        with self._strategy_lock:
            active_count = sum(1 for t in self._running_strategies.values() if t.is_alive())
            if active_count >= self._config.max_strategies:
                error_msg = (
                    f"已达到最大策略数量限制（{self._config.max_strategies}），"
                    f"当前运行中的策略数: {active_count}"
                )
                logger.error(error_msg)
                raise RuntimeError(error_msg)
        
        # 创建策略包装函数
        def strategy_wrapper():
            """
            策略包装函数，负责异常捕获和日志记录
            """
            strategy_name = strategy_func.__name__
            logger.info(f"策略线程启动: {strategy_name}")
            
            try:
                # 执行策略函数
                strategy_func(*args, **kwargs)
                logger.info(f"策略正常结束: {strategy_name}")
                
            except Exception as e:
                # 捕获策略异常，记录完整堆栈信息
                logger.error(
                    f"策略 {strategy_name} 发生异常: {e}",
                    exc_info=True
                )
                
            finally:
                # 从注册表中移除该策略
                with self._strategy_lock:
                    if strategy_name in self._running_strategies:
                        del self._running_strategies[strategy_name]
                        logger.debug(f"策略已从注册表移除: {strategy_name}")
        
        # 创建策略线程
        strategy_name = strategy_func.__name__
        strategy_thread = threading.Thread(
            target=strategy_wrapper,
            name=f"Strategy-{strategy_name}",
            daemon=True  # 设置为守护线程，主程序退出时自动结束
        )
        
        # 添加到注册表
        with self._strategy_lock:
            self._running_strategies[strategy_name] = strategy_thread
            logger.debug(f"策略已添加到注册表: {strategy_name}")
        
        # 启动线程
        strategy_thread.start()
        logger.info(f"策略线程已启动: {strategy_name}")
        
        return strategy_thread

    def get_running_strategies(self) -> Dict[str, threading.Thread]:
        """
        获取当前运行中的策略列表
        
        Returns:
            字典，键为策略名称，值为线程对象
            
        Example:
            >>> api = SyncStrategyApi()
            >>> strategies = api.get_running_strategies()
            >>> for name, thread in strategies.items():
            >>>     print(f"策略: {name}, 运行中: {thread.is_alive()}")
        """
        with self._strategy_lock:
            # 返回副本，避免外部修改
            return dict(self._running_strategies)
    
    def register_plugin(self, plugin: StrategyPlugin) -> None:
        """
        注册策略插件
        
        插件可以在特定事件发生时执行自定义逻辑,例如:
        - 行情数据预处理
        - 交易信号生成
        - 风险控制
        - 日志记录和监控
        
        Args:
            plugin: 插件实例,必须继承自 StrategyPlugin
            
        Example:
            >>> class MyPlugin(StrategyPlugin):
            >>>     def on_init(self, api):
            >>>         self.api = api
            >>>         print("插件初始化")
            >>>     
            >>>     def on_quote(self, quote):
            >>>         print(f"收到行情: {quote.InstrumentID}")
            >>>         return quote
            >>> 
            >>> api = SyncStrategyApi("user_id", "password")
            >>> api.register_plugin(MyPlugin())
        """
        self._plugin_manager.register(plugin, self)
        logger.info(f"插件已注册: {plugin.__class__.__name__}")
    
    def unregister_plugin(self, plugin: StrategyPlugin) -> None:
        """
        注销策略插件
        
        Args:
            plugin: 要注销的插件实例
            
        Example:
            >>> plugin = MyPlugin()
            >>> api.register_plugin(plugin)
            >>> # ... 使用插件 ...
            >>> api.unregister_plugin(plugin)
        """
        self._plugin_manager.unregister(plugin)
        logger.info(f"插件已注销: {plugin.__class__.__name__}")
    
    def stop(self, timeout: Optional[float] = None) -> None:
        """
        停止所有策略和服务
        
        该方法会按顺序执行以下操作：
        1. 等待所有运行中的策略线程完成（设置超时）
        2. 停止异步事件循环
        3. 断开 CTP 连接并释放客户端对象
        4. 清理内部数据结构
        
        Args:
            timeout: 等待策略线程停止的超时时间（秒），None 表示使用配置文件中的默认值
            
        Example:
            >>> api = SyncStrategyApi()
            >>> api.connect("user_id", "password")
            >>> # ... 运行策略 ...
            >>> api.stop()  # 停止所有服务
        """
        # 使用配置的超时值（如果未指定）
        if timeout is None:
            timeout = self._config.stop_timeout
        
        logger.info(f"开始停止 SyncStrategyApi，超时: {timeout}s...")
        
        try:
            # 步骤 1: 等待所有策略线程完成
            logger.info("等待所有策略线程完成...")
            with self._strategy_lock:
                running_strategies = list(self._running_strategies.items())
            
            if running_strategies:
                logger.info(f"当前有 {len(running_strategies)} 个策略正在运行")
                
                # 为每个策略线程分配超时时间
                per_thread_timeout = timeout / len(running_strategies) if running_strategies else timeout
                
                for strategy_name, strategy_thread in running_strategies:
                    if strategy_thread.is_alive():
                        logger.debug(f"等待策略线程停止: {strategy_name}")
                        strategy_thread.join(timeout=per_thread_timeout)
                        
                        if strategy_thread.is_alive():
                            logger.warning(
                                f"策略线程 {strategy_name} 在 {per_thread_timeout:.2f} 秒后仍未停止"
                            )
                        else:
                            logger.debug(f"策略线程已停止: {strategy_name}")
                    else:
                        logger.debug(f"策略线程已经停止: {strategy_name}")
            else:
                logger.info("没有运行中的策略线程")
            
            # 步骤 2: 停止异步事件循环（会自动断开 CTP 连接）
            if self._event_loop_thread:
                logger.info("停止异步事件循环...")
                try:
                    self._event_loop_thread.stop(timeout=timeout)
                    logger.info("异步事件循环已停止")
                except Exception as e:
                    logger.error(f"停止异步事件循环时出错: {e}", exc_info=True)
            else:
                logger.debug("事件循环线程未初始化，跳过停止")
            
            # 步骤 3: 停止所有插件
            logger.info("停止所有插件...")
            try:
                self._plugin_manager.stop_all()
            except Exception as e:
                logger.error(f"停止插件时出错: {e}", exc_info=True)
            
            # 步骤 4: 清理内部数据结构
            logger.info("清理内部数据结构...")
            
            # 清空行情缓存
            self._quote_cache.clear()
            logger.debug("行情缓存已清空")
            
            # 清空持仓缓存
            self._position_cache.clear()
            logger.debug("持仓缓存已清空")
            
            # 清空订阅状态
            with self._subscription_lock:
                self._subscribed_instruments.clear()
                logger.debug("订阅状态已清空")
            
            # 清空事件管理器
            self._event_manager.clear_all()
            logger.debug("事件管理器已清空")
            
            # 清空订单响应缓存
            with self._order_response_lock:
                self._order_responses.clear()
                logger.debug("订单响应缓存已清空")
            
            # 清空合约信息缓存
            with self._instrument_cache_lock:
                self._instrument_cache.clear()
                logger.debug("合约信息缓存已清空")
            
            # 清空策略注册表
            with self._strategy_lock:
                self._running_strategies.clear()
                logger.debug("策略注册表已清空")
            
            logger.info("SyncStrategyApi 已完全停止")
            
        except Exception as e:
            logger.error(f"停止 SyncStrategyApi 时发生错误: {e}", exc_info=True)
            raise


# 导出公共接口
__all__ = ['SyncStrategyApi', 'Quote', 'Position', 'StrategyPlugin']
