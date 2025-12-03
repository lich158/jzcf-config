#!/usr/bin/env python3
"""
博彩水果机赔率模拟器
模拟玩家押注心理和开奖结果，优化赔率设计
"""
import random
import json
from collections import defaultdict
from typing import Dict, List, Tuple

class SlotMachineSimulator:
    """水果机模拟器"""
    
    def __init__(self):
        # 8个押注选项（对应图片中的8个按钮）
        self.bet_options = ['BAR', '99', '双星', '西瓜', '金钟', '柠檬', '橘子', '苹果']
        
        # 开奖奖项及其倍数
        self.prize_multipliers = {
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
        
        # 加奖倍数（10-30倍随机）
        self.bonus_multiplier_range = (10, 30)
    
    def simulate_player_psychology(self, rounds: int = 10000) -> Dict:
        """
        模拟玩家押注心理
        玩家心理特征：
        1. 初期保守，押注低倍数选项
        2. 中奖后更激进，押注高倍数
        3. 连续输后可能加倍押注（追输心理）
        4. 看到别人中大奖后，会模仿押注
        5. 倾向于押注最近中奖的选项（热号心理）
        """
        player_stats = {
            'total_bet': 0,
            'total_win': 0,
            'win_rounds': 0,
            'lose_rounds': 0,
            'big_wins': 0,  # 中大奖次数
            'bonus_triggers': 0,  # 触发加奖次数
            'max_win_streak': 0,
            'max_lose_streak': 0,
            'bet_patterns': defaultdict(int)
        }
        
        current_streak = 0
        is_winning = False
        
        for i in range(rounds):
            # 模拟玩家押注选择（基于心理状态）
            if i == 0:
                # 初期保守，主要押注低倍数
                bet_option = random.choice(['苹果', '橘子', '柠檬'])
            elif player_stats['total_win'] > player_stats['total_bet']:
                # 盈利时更激进，押注高倍数
                bet_option = random.choice(['99', '大bar', '中bar', '双星'])
            elif current_streak < -3:
                # 连续输后，可能加倍押注高倍数（追输心理）
                bet_option = random.choice(['99', '大bar', '金猪奖'])
            else:
                # 正常情况，随机选择
                bet_option = random.choice(self.bet_options)
            
            player_stats['bet_patterns'][bet_option] += 1
            bet_amount = 100  # 假设每次押注100分
            player_stats['total_bet'] += bet_amount
            
            # 模拟开奖（这里简化，实际应该根据配置的概率）
            # 这里只是演示心理模拟，实际开奖在优化赔率时使用
            
        return player_stats
    
    def calculate_expected_value(self, prize_dist: Dict, bonus_dist: Dict, 
                                 difficulty: int) -> Dict:
        """
        计算期望值（EV）
        用于评估赔率设计的合理性
        """
        # 开奖奖项期望值
        prize_ev = 0
        for prize, count in prize_dist.items():
            multiplier = self.prize_multipliers.get(prize, 0)
            probability = count / 10000
            prize_ev += multiplier * probability
        
        # 加奖期望值（小猫变身等）
        bonus_ev = 0
        avg_bonus_multiplier = (self.bonus_multiplier_range[0] + 
                                self.bonus_multiplier_range[1]) / 2
        for bonus, count in bonus_dist.items():
            probability = count / 10000
            if bonus == '小猫变身':
                bonus_ev += avg_bonus_multiplier * probability
            else:
                # 其他加奖假设平均5倍
                bonus_ev += 5 * probability
        
        total_ev = prize_ev + bonus_ev
        
        return {
            'difficulty': difficulty,
            'prize_ev': prize_ev,
            'bonus_ev': bonus_ev,
            'total_ev': total_ev,
            'house_edge': 100 - total_ev  # 庄家优势
        }
    
    def optimize_distributions(self, target_return_rate: float, 
                              difficulty: int) -> Tuple[Dict, Dict]:
        """
        优化开奖和加奖分布
        目标：在满足返奖率的前提下，最大化玩家刺激感
        """
        # 这里可以加入优化算法
        # 暂时返回当前分布
        pass

def analyze_player_addiction_factors():
    """
    分析让玩家上瘾的关键因素
    基于行为心理学和博彩设计理论
    """
    factors = {
        'variable_reward': {
            'description': '可变奖励机制',
            'strategy': '让玩家无法预测奖励，保持期待感',
            'implementation': '三倍小奖占大部分，偶尔出现大奖'
        },
        'near_miss': {
            'description': '近失效应',
            'strategy': '让玩家感觉"差一点就中大奖"，增加继续游戏的动力',
            'implementation': '高倍数奖项概率适中，让玩家经常"擦肩而过"'
        },
        'loss_chasing': {
            'description': '追输心理',
            'strategy': '玩家输钱后更愿意继续游戏以挽回损失',
            'implementation': '设计合理的返奖率，让玩家有输有赢'
        },
        'big_win_memory': {
            'description': '大奖记忆',
            'strategy': '偶尔的大奖会让玩家印象深刻，持续吸引',
            'implementation': '保持一定的大奖概率，但不要太高'
        },
        'frequent_small_wins': {
            'description': '频繁小奖',
            'strategy': '频繁的小奖让玩家感觉"在赢"，保持参与感',
            'implementation': '三倍小奖占60-70%，让玩家经常中奖'
        },
        'bonus_excitement': {
            'description': '加奖刺激',
            'strategy': '加奖机制增加意外惊喜，提高游戏趣味性',
            'implementation': '小猫变身次数最多，频繁触发高倍数奖励'
        }
    }
    return factors

def simulate_game_session(difficulty: int, prize_dist: Dict, bonus_dist: Dict,
                          rounds: int = 1000) -> Dict:
    """
    模拟游戏会话
    模拟玩家押注和开奖的完整过程
    """
    results = {
        'rounds': rounds,
        'total_bet': 0,
        'total_win': 0,
        'prize_wins': 0,
        'bonus_wins': 0,
        'big_wins': 0,
        'win_rate': 0,
        'return_rate': 0,
        'max_win': 0,
        'win_history': []
    }
    
    # 构建概率分布
    prize_probs = {k: v/10000 for k, v in prize_dist.items()}
    bonus_probs = {k: v/10000 for k, v in bonus_dist.items()}
    
    prize_multipliers = {
        '三倍小奖': 3, '苹果': 5, '橘子': 10, '柠檬': 15, '金钟': 20,
        '西瓜': 20, '双星': 30, '99': 40, '小bar': 30, '中bar': 60,
        '大bar': 120, '金猪奖': 100
    }
    
    for i in range(rounds):
        # 玩家押注（简化：随机选择一个选项，押注100分）
        bet_option = random.choice(['BAR', '99', '双星', '西瓜', '金钟', '柠檬', '橘子', '苹果'])
        bet_amount = 100
        results['total_bet'] += bet_amount
        
        # 开奖：根据概率分布随机选择
        rand = random.random()
        cumulative = 0
        prize = None
        for p, prob in prize_probs.items():
            cumulative += prob
            if rand <= cumulative:
                prize = p
                break
        
        # 计算奖金
        win_amount = 0
        if prize:
            multiplier = prize_multipliers.get(prize, 0)
            win_amount = bet_amount * multiplier
            results['prize_wins'] += 1
            if multiplier >= 30:
                results['big_wins'] += 1
        
        # 加奖判定（独立概率）
        bonus_rand = random.random()
        bonus_cumulative = 0
        bonus = None
        for b, prob in bonus_probs.items():
            bonus_cumulative += prob
            if bonus_rand <= bonus_cumulative:
                bonus = b
                break
        
        if bonus:
            if bonus == '小猫变身':
                bonus_multiplier = random.randint(10, 30)
            else:
                bonus_multiplier = random.randint(5, 15)
            bonus_win = bet_amount * bonus_multiplier
            win_amount += bonus_win
            results['bonus_wins'] += 1
        
        results['total_win'] += win_amount
        results['max_win'] = max(results['max_win'], win_amount)
        results['win_history'].append({
            'round': i + 1,
            'bet': bet_amount,
            'win': win_amount,
            'prize': prize,
            'bonus': bonus
        })
    
    results['win_rate'] = (results['prize_wins'] + results['bonus_wins']) / rounds * 100
    results['return_rate'] = results['total_win'] / results['total_bet'] * 100 if results['total_bet'] > 0 else 0
    
    return results

if __name__ == "__main__":
    # 测试模拟器
    simulator = SlotMachineSimulator()
    
    # 分析上瘾因素
    print("=" * 60)
    print("玩家上瘾因素分析")
    print("=" * 60)
    factors = analyze_player_addiction_factors()
    for key, value in factors.items():
        print(f"\n{value['description']}:")
        print(f"  策略: {value['strategy']}")
        print(f"  实现: {value['implementation']}")
    
    print("\n" + "=" * 60)
    print("模拟游戏会话（难度1，1000局）")
    print("=" * 60)
    
    # 测试难度1的配置
    prize_dist_1 = {
        '三倍小奖': 6300, '苹果': 800, '橘子': 600, '柠檬': 460, '金钟': 370,
        '西瓜': 370, '双星': 320, '99': 260, '小bar': 185, '中bar': 140,
        '大bar': 95, '金猪奖': 100
    }
    bonus_dist_1 = {
        '小猫变身': 2600, '双响炮': 1100, '大四喜': 1000, '小三元': 900,
        '大三元': 800, '彩金': 700, '开火车': 600, '统统有奖': 500,
        '大满贯': 400, '仙女散花': 400
    }
    
    results = simulate_game_session(1, prize_dist_1, bonus_dist_1, rounds=1000)
    print(f"总押注: {results['total_bet']}")
    print(f"总奖金: {results['total_win']}")
    print(f"返奖率: {results['return_rate']:.2f}%")
    print(f"中奖率: {results['win_rate']:.2f}%")
    print(f"大奖次数: {results['big_wins']}")
    print(f"加奖次数: {results['bonus_wins']}")
    print(f"最大单次奖金: {results['max_win']}")

