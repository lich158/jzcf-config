#!/usr/bin/env python3
"""
游戏配置核心模块
资深博彩设计师设计：基于心理学和数学模型的赔率系统
"""
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import json


class DifficultyLevel(Enum):
    """难度等级枚举"""
    EASY = 1      # 新手友好，高返奖率
    NORMAL = 2
    MEDIUM = 3
    HARD = 4
    EXPERT = 5
    MASTER = 6
    LEGEND = 7
    MYTHIC = 8
    HELL = 9      # 最高难度，庄家优势最大


@dataclass
class PrizeConfig:
    """开奖奖项配置"""
    name: str
    multiplier: int
    base_probability: float  # 基础概率（每10000把）
    min_probability: float   # 最小概率
    max_probability: float   # 最大概率


@dataclass
class BonusConfig:
    """加奖配置"""
    name: str
    multiplier_range: Tuple[int, int]  # 倍数范围
    base_probability: float
    min_probability: float
    max_probability: float


@dataclass
class DifficultyConfig:
    """难度配置"""
    difficulty: int
    # 基础参数
    double_difficulty: int      # 比倍难度 (%)
    eat_max: int                # 吃分最大值
    eat_min: int                # 吃分最小值
    return_rate: float           # 吃分返奖率 (%)
    business_return_rate: float # 营业返奖率 (%)
    # 开奖分布（每10000把出现的次数）
    prize_distribution: Dict[str, int]
    # 加奖分布（每10000把出现的次数）
    bonus_distribution: Dict[str, int]


class GameConfigManager:
    """
    游戏配置管理器
    核心设计理念：
    1. 可变奖励机制（Variable Reward Schedule）
    2. 近失效应（Near Miss Effect）
    3. 损失厌恶与追输心理（Loss Aversion & Chasing Losses）
    4. 间歇性强化（Intermittent Reinforcement）
    5. 沉没成本效应（Sunk Cost Fallacy）
    """
    
    # 开奖奖项定义（倍数配置）
    PRIZE_MULTIPLIERS = {
        '三倍小奖': 3,
        '苹果': 5,
        '橘子': 10,
        '柠檬': 15,
        '金钟': 20,
        '西瓜': 20,
        '双星': 30,
        '99': 40,
        '小bar': 30,
        '中bar': 60,
        '大bar': 120,
        '金猪奖': 100
    }
    
    # 加奖倍数范围
    BONUS_MULTIPLIERS = {
        '小猫变身': (10, 30),
        '双响炮': (5, 12),
        '大四喜': (5, 12),
        '小三元': (5, 10),
        '大三元': (5, 10),
        '彩金': (5, 10),
        '开火车': (5, 10),
        '统统有奖': (5, 10),
        '大满贯': (5, 10),
        '仙女散花': (5, 10)
    }
    
    # 目标返奖率（基于难度）
    TARGET_RETURN_RATES = {
        1: 80.0,  # 新手友好，让玩家感觉"容易赢"
        2: 75.0,
        3: 70.0,
        4: 65.0,
        5: 60.0,
        6: 55.0,
        7: 50.0,
        8: 45.0,
        9: 40.0  # 最高难度，庄家优势60%
    }
    
    def __init__(self):
        self._configs: Dict[int, DifficultyConfig] = {}
        self._initialize_default_configs()
    
    def _initialize_default_configs(self):
        """初始化默认配置（基于资深博彩设计原理）"""
        for difficulty in range(1, 10):
            config = self._create_optimized_config(difficulty)
            self._configs[difficulty] = config
    
    def _create_optimized_config(self, difficulty: int) -> DifficultyConfig:
        """
        创建优化的难度配置
        设计原则：
        1. 难度1：高返奖率(80%)，高参与度，让玩家建立信心
        2. 难度递增：返奖率递减，但保持刺激感
        3. 难度9：低返奖率(40%)，但仍保持一定的大奖概率以维持期待
        """
        # 基础参数
        base_params = {
            1: {'double': 20, 'eat_max': 2000, 'eat_min': 300, 'return': 80, 'business': 83},
            2: {'double': 25, 'eat_max': 2400, 'eat_min': 400, 'return': 75, 'business': 78},
            3: {'double': 30, 'eat_max': 2800, 'eat_min': 500, 'return': 70, 'business': 73},
            4: {'double': 35, 'eat_max': 3200, 'eat_min': 600, 'return': 65, 'business': 68},
            5: {'double': 40, 'eat_max': 3600, 'eat_min': 700, 'return': 60, 'business': 63},
            6: {'double': 45, 'eat_max': 4000, 'eat_min': 800, 'return': 55, 'business': 58},
            7: {'double': 50, 'eat_max': 4400, 'eat_min': 900, 'return': 50, 'business': 53},
            8: {'double': 55, 'eat_max': 4800, 'eat_min': 1000, 'return': 45, 'business': 48},
            9: {'double': 60, 'eat_max': 5200, 'eat_min': 1100, 'return': 40, 'business': 43}
        }
        
        params = base_params[difficulty]
        
        # 开奖分布（基于心理学原理优化）
        prize_dist = self._calculate_prize_distribution(difficulty)
        
        # 加奖分布（最大化刺激感）
        bonus_dist = self._calculate_bonus_distribution(difficulty)
        
        return DifficultyConfig(
            difficulty=difficulty,
            double_difficulty=params['double'],
            eat_max=params['eat_max'],
            eat_min=params['eat_min'],
            return_rate=params['return'],
            business_return_rate=params['business'],
            prize_distribution=prize_dist,
            bonus_distribution=bonus_dist
        )
    
    def _calculate_prize_distribution(self, difficulty: int) -> Dict[str, int]:
        """
        计算开奖分布
        核心策略：
        1. 三倍小奖：难度1=63%，难度9=47%（逐渐降低，但保持高频）
        2. 中等奖项：保持一定概率，维持刺激
        3. 大奖：保持稀有但可触及，维持期待
        """
        # 优化后的分布模板：减少三倍小奖，增加金猪奖（加奖入口），提高玩家兴趣
        # 策略：三倍小奖降低到47-51.5%，金猪奖增加到300-550，让玩家有更多机会触发加奖
        base_distributions = {
            1: {'三倍小奖': 5150, '苹果': 900, '橘子': 700, '柠檬': 600, '金钟': 500, '西瓜': 500,
                '双星': 400, '99': 350, '小bar': 250, '中bar': 200, '大bar': 150, '金猪奖': 300},
            2: {'三倍小奖': 5120, '苹果': 900, '橘子': 700, '柠檬': 600, '金钟': 500, '西瓜': 500,
                '双星': 400, '99': 350, '小bar': 250, '中bar': 200, '大bar': 150, '金猪奖': 330},
            3: {'三倍小奖': 5090, '苹果': 900, '橘子': 700, '柠檬': 600, '金钟': 500, '西瓜': 500,
                '双星': 400, '99': 350, '小bar': 250, '中bar': 200, '大bar': 150, '金猪奖': 360},
            4: {'三倍小奖': 5060, '苹果': 900, '橘子': 700, '柠檬': 600, '金钟': 500, '西瓜': 500,
                '双星': 400, '99': 350, '小bar': 250, '中bar': 200, '大bar': 150, '金猪奖': 390},
            5: {'三倍小奖': 5030, '苹果': 900, '橘子': 700, '柠檬': 600, '金钟': 500, '西瓜': 500,
                '双星': 400, '99': 350, '小bar': 250, '中bar': 200, '大bar': 150, '金猪奖': 420},
            6: {'三倍小奖': 5000, '苹果': 900, '橘子': 700, '柠檬': 600, '金钟': 500, '西瓜': 500,
                '双星': 400, '99': 350, '小bar': 250, '中bar': 200, '大bar': 150, '金猪奖': 450},
            7: {'三倍小奖': 4900, '苹果': 900, '橘子': 700, '柠檬': 600, '金钟': 500, '西瓜': 500,
                '双星': 400, '99': 350, '小bar': 250, '中bar': 200, '大bar': 150, '金猪奖': 550},
            8: {'三倍小奖': 4800, '苹果': 900, '橘子': 700, '柠檬': 600, '金钟': 500, '西瓜': 500,
                '双星': 400, '99': 350, '小bar': 250, '中bar': 200, '大bar': 150, '金猪奖': 650},
            9: {'三倍小奖': 4700, '苹果': 900, '橘子': 700, '柠檬': 600, '金钟': 500, '西瓜': 500,
                '双星': 400, '99': 350, '小bar': 250, '中bar': 200, '大bar': 150, '金猪奖': 750}
        }
        
        dist = base_distributions[difficulty].copy()
        
        # 确保总和为10000
        # 注意：金猪奖是加奖入口，不应该有倍数，但需要确保总和正确
        # 如果总和不对，优先调整其他奖项，确保金猪奖不为负数
        total = sum(dist.values())
        if total != 10000:
            diff = 10000 - total
            # 如果diff为负（总和超过10000），需要从其他奖项扣除
            if diff < 0:
                # 从三倍小奖扣除（因为它占比最大）
                dist['三倍小奖'] = max(0, dist['三倍小奖'] + diff)
            else:
                # 如果diff为正，加到金猪奖
                dist['金猪奖'] += diff
        
        # 再次检查，确保金猪奖不为负数
        if dist['金猪奖'] < 0:
            # 如果金猪奖为负，从三倍小奖补偿
            compensation = abs(dist['金猪奖'])
            dist['三倍小奖'] = max(0, dist['三倍小奖'] - compensation)
            dist['金猪奖'] = 0  # 金猪奖最小为0
        
        # 最终验证总和
        final_total = sum(dist.values())
        if final_total != 10000:
            # 如果还是不对，调整三倍小奖（最后手段）
            dist['三倍小奖'] += (10000 - final_total)
        
        return dist
    
    def _calculate_bonus_distribution(self, difficulty: int) -> Dict[str, int]:
        """
        计算加奖分布
        核心策略：小猫变身占最大比例，最大化刺激感
        """
        base_distributions = {
            1: {'小猫变身': 2600, '双响炮': 1100, '大四喜': 1000, '小三元': 900, '大三元': 800,
                '彩金': 700, '开火车': 600, '统统有奖': 500, '大满贯': 400, '仙女散花': 400},
            2: {'小猫变身': 2500, '双响炮': 1050, '大四喜': 950, '小三元': 850, '大三元': 750,
                '彩金': 650, '开火车': 550, '统统有奖': 450, '大满贯': 350, '仙女散花': 350},
            3: {'小猫变身': 2400, '双响炮': 1000, '大四喜': 900, '小三元': 800, '大三元': 700,
                '彩金': 600, '开火车': 500, '统统有奖': 400, '大满贯': 300, '仙女散花': 300},
            4: {'小猫变身': 2300, '双响炮': 950, '大四喜': 850, '小三元': 750, '大三元': 650,
                '彩金': 550, '开火车': 450, '统统有奖': 350, '大满贯': 250, '仙女散花': 250},
            5: {'小猫变身': 3200, '双响炮': 1200, '大四喜': 1100, '小三元': 1000, '大三元': 900,
                '彩金': 800, '开火车': 700, '统统有奖': 600, '大满贯': 300, '仙女散花': 200},
            6: {'小猫变身': 3000, '双响炮': 1150, '大四喜': 1050, '小三元': 950, '大三元': 850,
                '彩金': 750, '开火车': 650, '统统有奖': 550, '大满贯': 250, '仙女散花': 150},
            7: {'小猫变身': 2800, '双响炮': 1100, '大四喜': 1000, '小三元': 900, '大三元': 800,
                '彩金': 700, '开火车': 600, '统统有奖': 500, '大满贯': 200, '仙女散花': 100},
            8: {'小猫变身': 2600, '双响炮': 1050, '大四喜': 950, '小三元': 850, '大三元': 750,
                '彩金': 650, '开火车': 550, '统统有奖': 450, '大满贯': 150, '仙女散花': 50},
            9: {'小猫变身': 3000, '双响炮': 1200, '大四喜': 1100, '小三元': 1000, '大三元': 900,
                '彩金': 800, '开火车': 700, '统统有奖': 600, '大满贯': 300, '仙女散花': 200}
        }
        
        dist = base_distributions[difficulty].copy()
        
        # 确保总和为10000
        total = sum(dist.values())
        if total != 10000:
            diff = 10000 - total
            dist['小猫变身'] += diff
        
        return dist
    
    def get_config(self, difficulty: int) -> Optional[DifficultyConfig]:
        """获取指定难度的配置"""
        return self._configs.get(difficulty)
    
    def get_all_configs(self) -> Dict[int, DifficultyConfig]:
        """获取所有难度配置"""
        return self._configs.copy()
    
    def update_config(self, difficulty: int, config_data: Dict) -> bool:
        """
        更新配置
        包含数据验证
        """
        if difficulty not in range(1, 10):
            return False
        
        config = self._configs.get(difficulty)
        if not config:
            return False
        
        # 更新基础参数
        if '比倍难度' in config_data:
            config.double_difficulty = int(config_data['比倍难度'])
        if '吃分最大值' in config_data:
            config.eat_max = int(config_data['吃分最大值'])
        if '吃分最小值' in config_data:
            config.eat_min = int(config_data['吃分最小值'])
        if '吃分返奖率' in config_data:
            config.return_rate = float(config_data['吃分返奖率'])
        if '营业返奖率' in config_data:
            config.business_return_rate = float(config_data['营业返奖率'])
        
        # 更新开奖分布
        prize_fields = list(self.PRIZE_MULTIPLIERS.keys())
        for field in prize_fields:
            if field in config_data:
                config.prize_distribution[field] = int(config_data[field])
        
        # 更新加奖分布
        bonus_fields = list(self.BONUS_MULTIPLIERS.keys())
        for field in bonus_fields:
            if field in config_data:
                config.bonus_distribution[field] = int(config_data[field])
        
        # 验证数据
        return self._validate_config(config)
    
    def _validate_config(self, config: DifficultyConfig) -> bool:
        """验证配置数据"""
        # 验证开奖总和
        prize_total = sum(config.prize_distribution.values())
        if prize_total != 10000:
            return False
        
        # 验证加奖总和
        bonus_total = sum(config.bonus_distribution.values())
        if bonus_total != 10000:
            return False
        
        # 验证基础参数范围
        if not (0 <= config.double_difficulty <= 100):
            return False
        if config.eat_min >= config.eat_max:
            return False
        if not (0 <= config.return_rate <= 100):
            return False
        
        return True
    
    def calculate_expected_return_rate(self, difficulty: int) -> float:
        """
        计算期望返奖率
        基于概率和倍数的数学期望
        """
        config = self.get_config(difficulty)
        if not config:
            return 0.0
        
        total_ev = 0.0
        
        # 开奖期望值
        for prize, count in config.prize_distribution.items():
            prob = count / 10000.0
            multiplier = self.PRIZE_MULTIPLIERS.get(prize, 0)
            total_ev += prob * multiplier
        
        # 加奖期望值
        for bonus, count in config.bonus_distribution.items():
            prob = count / 10000.0
            multiplier_range = self.BONUS_MULTIPLIERS.get(bonus, (5, 10))
            avg_multiplier = (multiplier_range[0] + multiplier_range[1]) / 2.0
            total_ev += prob * avg_multiplier
        
        return total_ev
    
    def to_dict(self, difficulty: int) -> Dict:
        """转换为字典格式（用于API）"""
        config = self.get_config(difficulty)
        if not config:
            return {}
        
        result = {
            '比倍难度': config.double_difficulty,
            '吃分最大值': config.eat_max,
            '吃分最小值': config.eat_min,
            '吃分返奖率': config.return_rate,
            '营业返奖率': config.business_return_rate
        }
        
        # 添加开奖分布
        result.update(config.prize_distribution)
        
        # 添加加奖分布
        result.update(config.bonus_distribution)
        
        return result
    
    def to_dict_all(self) -> Dict[str, Dict]:
        """获取所有难度的字典格式"""
        result = {}
        for difficulty in range(1, 10):
            result[f"难度{difficulty}"] = self.to_dict(difficulty)
        return result

