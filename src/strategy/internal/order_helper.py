#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@ProjectName: homalos-webctp
@FileName   : order_helper.py
@Date       : 2025/12/20
@Author     : Kiro AI Assistant
@Email      : -
@Software   : PyCharm
@Description: 订单处理辅助模块 - 处理订单提交、智能平仓等逻辑
"""


class _OrderHelper:
    """
    订单处理辅助类
    
    负责处理订单相关的业务逻辑，包括：
    - Action 参数映射到 CTP 参数
    - 交易所识别
    - 智能平仓（区分平今平昨）
    """
    
    @staticmethod
    def map_action_to_ctp(action: str, close_today: bool = False) -> tuple:
        """
        映射 action 参数到 CTP 的 Direction 和 CombOffsetFlag
        
        Args:
            action: 交易动作，支持 "kaiduo", "kaikong", "pingduo", "pingkong"
            close_today: 平仓时是否平今仓（仅对平仓操作有效）
            
        Returns:
            (Direction, CombOffsetFlag) 元组
            
        Raises:
            ValueError: 不支持的 action 参数
        """
        if action == 'kaiduo':
            return ('0', '0')
        elif action == 'kaikong':
            return ('1', '0')
        elif action == 'pingduo':
            offset_flag = '3' if close_today else '1'
            return ('1', offset_flag)
        elif action == 'pingkong':
            offset_flag = '3' if close_today else '1'
            return ('0', offset_flag)
        else:
            raise ValueError(
                f"不支持的 action 参数: {action}，"
                f"支持的值: kaiduo, kaikong, pingduo, pingkong"
            )
    
    @staticmethod
    def get_exchange_id(instrument_id: str) -> str:
        """
        根据合约代码推断交易所ID
        
        Args:
            instrument_id: 合约代码
            
        Returns:
            交易所ID字符串
        """
        import re
        product_code = re.match(r'([a-zA-Z]+)', instrument_id)
        if not product_code:
            return ""
        
        product = product_code.group(1).upper()
        
        shfe_products = ['CU', 'AL', 'ZN', 'PB', 'NI', 'SN', 'AU', 'AG', 'RB', 'WR', 'HC', 'FU', 'BU', 'RU', 'SP', 'SS', 'BC', 'LU']
        dce_products = ['A', 'B', 'M', 'Y', 'P', 'C', 'CS', 'JD', 'L', 'V', 'PP', 'J', 'JM', 'I', 'EG', 'EB', 'PG', 'RR', 'FB', 'BB', 'LH']
        czce_products = ['WH', 'PM', 'CF', 'SR', 'TA', 'OI', 'RI', 'MA', 'FG', 'RS', 'RM', 'ZC', 'JR', 'LR', 'SF', 'SM', 'CY', 'AP', 'CJ', 'UR', 'SA', 'PF', 'PK']
        cffex_products = ['IF', 'IC', 'IH', 'TS', 'TF', 'T', 'IM']
        ine_products = ['SC', 'NR', 'LU', 'BC']
        
        if product in shfe_products:
            return 'SHFE'
        elif product in dce_products:
            return 'DCE'
        elif product in czce_products:
            return 'CZCE'
        elif product in cffex_products:
            return 'CFFEX'
        elif product in ine_products:
            return 'INE'
        else:
            return ""
    
    @staticmethod
    def need_distinguish_close_type(exchange_id: str) -> bool:
        """
        判断交易所是否需要区分平今平昨
        
        Args:
            exchange_id: 交易所ID
            
        Returns:
            True 表示需要区分，False 表示不需要
        """
        return exchange_id in ['SHFE', 'INE', 'CFFEX']
    
    @staticmethod
    def split_close_orders(
        action: str,
        volume: int,
        today_pos: int,
        his_pos: int,
        total_pos: int
    ) -> list:
        """
        智能拆分平仓订单（优先平昨仓，再平今仓）
        
        Args:
            action: 交易动作（pingduo 或 pingkong）
            volume: 平仓数量
            today_pos: 今仓数量
            his_pos: 昨仓数量
            total_pos: 总持仓数量
            
        Returns:
            订单列表，每个订单包含 volume, close_today, description
            
        Raises:
            ValueError: 平仓数量超过持仓数量
        """
        if volume > total_pos:
            raise ValueError(
                f"平仓数量({volume})超过持仓数量({total_pos})，"
                f"今仓: {today_pos}, 昨仓: {his_pos}"
            )
        
        orders_to_submit = []
        remaining_volume = volume
        
        # 先平昨仓
        if his_pos > 0 and remaining_volume > 0:
            close_his_volume = min(his_pos, remaining_volume)
            orders_to_submit.append({
                'volume': close_his_volume,
                'close_today': False,
                'description': f'平昨仓 {close_his_volume} 手'
            })
            remaining_volume -= close_his_volume
        
        # 再平今仓
        if today_pos > 0 and remaining_volume > 0:
            close_today_volume = min(today_pos, remaining_volume)
            orders_to_submit.append({
                'volume': close_today_volume,
                'close_today': True,
                'description': f'平今仓 {close_today_volume} 手'
            })
            remaining_volume -= close_today_volume
        
        return orders_to_submit
