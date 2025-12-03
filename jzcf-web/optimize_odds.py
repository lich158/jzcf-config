#!/usr/bin/env python3
"""
赔率优化器
基于玩家心理和博彩理论，优化难度1-9的赔率设计
"""
import random
import json
from typing import Dict, List, Tuple
from collections import defaultdict

def calculate_expected_return(prize_dist: Dict, bonus_dist: Dict, 
                             prize_multipliers: Dict, 
                             bonus_multipliers: Dict = None) -> float:
    """
    计算期望返奖率
    返奖率 = 总期望奖金 / 总押注
    """
    if bonus_multipliers is None:
        bonus_multipliers = {}
    
    total_ev = 0
    
    # 开奖奖项期望值
    for prize, count in prize_dist.items():
        prob = count / 10000
        multiplier = prize_multipliers.get(prize, 0)
        total_ev += prob * multiplier
    
    # 加奖期望值
    for bonus, count in bonus_dist.items():
        prob = count / 10000
        if bonus == '小猫变身':
            # 小猫变身：10-30倍随机
            multiplier = 20  # 平均值
        else:
            # 其他加奖：假设平均8倍
            multiplier = bonus_multipliers.get(bonus, 8)
        total_ev += prob * multiplier
    
    return total_ev

def simulate_player_behavior(prize_dist: Dict, bonus_dist: Dict,
                             prize_multipliers: Dict, rounds: int = 10000) -> Dict:
    """
    模拟玩家行为和心理
    基于心理学原理：
    1. 可变奖励：玩家无法预测奖励，保持期待
    2. 近失效应：差一点中大奖，增加继续动力
    3. 追输心理：输钱后更愿意继续
    4. 大奖记忆：偶尔大奖印象深刻
    5. 频繁小奖：感觉"在赢"，保持参与
    """
    results = {
        'total_bet': 0,
        'total_win': 0,
        'prize_wins': 0,
        'bonus_wins': 0,
        'big_wins': 0,  # 30倍以上
        'huge_wins': 0,  # 60倍以上
        'win_streaks': [],
        'lose_streaks': [],
        'near_misses': 0,  # 近失次数
        'player_balance': 0,  # 玩家余额变化
        'engagement_score': 0  # 参与度评分
    }
    
    # 构建概率分布
    prize_probs = {k: v/10000 for k, v in prize_dist.items()}
    bonus_probs = {k: v/10000 for k, v in bonus_dist.items()}
    
    current_streak = 0
    is_winning = False
    balance = 10000  # 初始余额
    
    for i in range(rounds):
        bet_amount = 100
        results['total_bet'] += bet_amount
        balance -= bet_amount
        
        # 开奖
        rand = random.random()
        cumulative = 0
        prize = None
        for p, prob in prize_probs.items():
            cumulative += prob
            if rand <= cumulative:
                prize = p
                break
        
        win_amount = 0
        if prize:
            multiplier = prize_multipliers.get(prize, 0)
            win_amount = bet_amount * multiplier
            results['prize_wins'] += 1
            if multiplier >= 30:
                results['big_wins'] += 1
            if multiplier >= 60:
                results['huge_wins'] += 1
        
        # 加奖判定
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
        
        balance += win_amount
        results['total_win'] += win_amount
        results['player_balance'] = balance
        
        # 记录连胜/连败
        if win_amount > 0:
            if not is_winning:
                if current_streak < 0:
                    results['lose_streaks'].append(abs(current_streak))
                current_streak = 1
                is_winning = True
            else:
                current_streak += 1
        else:
            if is_winning:
                if current_streak > 0:
                    results['win_streaks'].append(current_streak)
                current_streak = -1
                is_winning = False
            else:
                current_streak -= 1
        
        # 近失效应：中奖但倍数较低（3-10倍），玩家感觉"差一点"
        if prize and prize_multipliers.get(prize, 0) <= 10:
            results['near_misses'] += 1
    
    # 计算参与度评分
    # 参与度 = 中奖率 * 0.3 + 大奖频率 * 0.3 + 加奖频率 * 0.2 + 近失频率 * 0.2
    win_rate = (results['prize_wins'] + results['bonus_wins']) / rounds
    big_win_rate = results['big_wins'] / rounds
    bonus_rate = results['bonus_wins'] / rounds
    near_miss_rate = results['near_misses'] / rounds
    
    results['engagement_score'] = (
        win_rate * 0.3 + 
        big_win_rate * 0.3 + 
        bonus_rate * 0.2 + 
        near_miss_rate * 0.2
    ) * 100
    
    return results

def optimize_odds_for_difficulty(difficulty: int, target_return_rate: float) -> Tuple[Dict, Dict]:
    """
    为特定难度优化赔率
    目标：在满足返奖率的前提下，最大化玩家参与度
    """
    prize_multipliers = {
        '三倍小奖': 3, '苹果': 5, '橘子': 10, '柠檬': 15, '金钟': 20,
        '西瓜': 20, '双星': 30, '99': 40, '小bar': 30, '中bar': 60,
        '大bar': 120, '金猪奖': 100
    }
    
    # 基于难度调整策略
    # 难度1：高返奖率，高参与度，让玩家感觉"容易赢"
    # 难度9：低返奖率，但仍保持一定刺激感
    
    # 核心策略：
    # 1. 三倍小奖占比：难度1=65%, 难度9=47%（逐渐降低）
    # 2. 中高倍数奖项：保持一定概率，维持刺激
    # 3. 小猫变身：难度1=26%, 难度9=30%（高难度时增加刺激）
    
    # 优化后的分布（基于心理学原理）
    optimized_prize = {
        1: {'三倍小奖': 6500, '苹果': 850, '橘子': 650, '柠檬': 500, '金钟': 400, '西瓜': 400,
            '双星': 350, '99': 280, '小bar': 200, '中bar': 150, '大bar': 100, '金猪奖': 120},
        2: {'三倍小奖': 6400, '苹果': 880, '橘子': 680, '柠檬': 530, '金钟': 430, '西瓜': 430,
            '双星': 370, '99': 290, '小bar': 210, '中bar': 160, '大bar': 105, '金猪奖': 115},
        3: {'三倍小奖': 6300, '苹果': 910, '橘子': 710, '柠檬': 560, '金钟': 460, '西瓜': 460,
            '双星': 390, '99': 300, '小bar': 220, '中bar': 170, '大bar': 110, '金猪奖': 110},
        4: {'三倍小奖': 6200, '苹果': 940, '橘子': 740, '柠檬': 590, '金钟': 490, '西瓜': 490,
            '双星': 410, '99': 310, '小bar': 230, '中bar': 180, '大bar': 115, '金猪奖': 105},
        5: {'三倍小奖': 5800, '苹果': 950, '橘子': 750, '柠檬': 610, '金钟': 530, '西瓜': 530,
            '双星': 420, '99': 320, '小bar': 250, '中bar': 190, '大bar': 125, '金猪奖': 100},
        6: {'三倍小奖': 5700, '苹果': 980, '橘子': 790, '柠檬': 650, '金钟': 570, '西瓜': 570,
            '双星': 440, '99': 330, '小bar': 270, '中bar': 200, '大bar': 130, '金猪奖': 90},
        7: {'三倍小奖': 5600, '苹果': 1010, '橘子': 830, '柠檬': 690, '金钟': 610, '西瓜': 610,
            '双星': 460, '99': 350, '小bar': 290, '中bar': 210, '大bar': 140, '金猪奖': 90},
        8: {'三倍小奖': 5500, '苹果': 1050, '橘子': 880, '柠檬': 750, '金钟': 670, '西瓜': 670,
            '双星': 490, '99': 370, '小bar': 310, '中bar': 230, '大bar': 150, '金猪奖': 90},
        9: {'三倍小奖': 4700, '苹果': 1020, '橘子': 870, '柠檬': 750, '金钟': 670, '西瓜': 670,
            '双星': 480, '99': 360, '小bar': 300, '中bar': 230, '大bar': 160, '金猪奖': 100}
    }
    
    optimized_bonus = {
        1: {'小猫变身': 2600, '双响炮': 1200, '大四喜': 1100, '小三元': 1000, '大三元': 900,
            '彩金': 800, '开火车': 700, '统统有奖': 600, '大满贯': 500, '仙女散花': 400},
        2: {'小猫变身': 2500, '双响炮': 1150, '大四喜': 1050, '小三元': 950, '大三元': 850,
            '彩金': 750, '开火车': 650, '统统有奖': 550, '大满贯': 450, '仙女散花': 350},
        3: {'小猫变身': 2400, '双响炮': 1100, '大四喜': 1000, '小三元': 900, '大三元': 800,
            '彩金': 700, '开火车': 600, '统统有奖': 500, '大满贯': 400, '仙女散花': 300},
        4: {'小猫变身': 2300, '双响炮': 1050, '大四喜': 950, '小三元': 850, '大三元': 750,
            '彩金': 650, '开火车': 550, '统统有奖': 450, '大满贯': 350, '仙女散花': 250},
        5: {'小猫变身': 3000, '双响炮': 1300, '大四喜': 1200, '小三元': 1100, '大三元': 1000,
            '彩金': 900, '开火车': 800, '统统有奖': 700, '大满贯': 400, '仙女散花': 200},
        6: {'小猫变身': 2900, '双响炮': 1250, '大四喜': 1150, '小三元': 1050, '大三元': 950,
            '彩金': 850, '开火车': 750, '统统有奖': 650, '大满贯': 300, '仙女散花': 150},
        7: {'小猫变身': 2800, '双响炮': 1200, '大四喜': 1100, '小三元': 1000, '大三元': 900,
            '彩金': 800, '开火车': 700, '统统有奖': 600, '大满贯': 250, '仙女散花': 100},
        8: {'小猫变身': 2700, '双响炮': 1150, '大四喜': 1050, '小三元': 950, '大三元': 850,
            '彩金': 750, '开火车': 650, '统统有奖': 550, '大满贯': 200, '仙女散花': 50},
        9: {'小猫变身': 3000, '双响炮': 1300, '大四喜': 1200, '小三元': 1100, '大三元': 1000,
            '彩金': 900, '开火车': 800, '统统有奖': 700, '大满贯': 300, '仙女散花': 200}
    }
    
    # 确保总和为10000
    prize = optimized_prize[difficulty].copy()
    bonus = optimized_bonus[difficulty].copy()
    
    # 调整到总和10000
    prize_sum = sum(prize.values())
    if prize_sum != 10000:
        diff = 10000 - prize_sum
        prize['金猪奖'] += diff
    
    bonus_sum = sum(bonus.values())
    if bonus_sum != 10000:
        diff = 10000 - bonus_sum
        bonus['小猫变身'] += diff
    
    return prize, bonus

def main():
    """主函数：优化所有难度的赔率"""
    print("=" * 80)
    print("赔率优化器 - 基于玩家心理和博彩理论")
    print("=" * 80)
    
    prize_multipliers = {
        '三倍小奖': 3, '苹果': 5, '橘子': 10, '柠檬': 15, '金钟': 20,
        '西瓜': 20, '双星': 30, '99': 40, '小bar': 30, '中bar': 60,
        '大bar': 120, '金猪奖': 100
    }
    
    target_returns = {
        1: 80, 2: 75, 3: 70, 4: 65, 5: 60,
        6: 55, 7: 50, 8: 45, 9: 40
    }
    
    print("\n优化后的赔率分布：")
    print("-" * 80)
    
    for difficulty in range(1, 10):
        prize_dist, bonus_dist = optimize_odds_for_difficulty(difficulty, target_returns[difficulty])
        
        # 计算期望返奖率
        expected_return = calculate_expected_return(prize_dist, bonus_dist, prize_multipliers)
        
        # 模拟玩家行为
        sim_results = simulate_player_behavior(prize_dist, bonus_dist, prize_multipliers, rounds=10000)
        
        print(f"\n难度 {difficulty} (目标返奖率: {target_returns[difficulty]}%):")
        print(f"  实际期望返奖率: {expected_return:.2f}%")
        print(f"  中奖率: {sim_results['prize_wins']/10000*100:.1f}%")
        print(f"  加奖率: {sim_results['bonus_wins']/10000*100:.1f}%")
        print(f"  大奖率(30倍+): {sim_results['big_wins']/10000*100:.2f}%")
        print(f"  超大奖率(60倍+): {sim_results['huge_wins']/10000*100:.2f}%")
        print(f"  参与度评分: {sim_results['engagement_score']:.1f}/100")
        print(f"  三倍小奖占比: {prize_dist['三倍小奖']/100:.1f}%")
        print(f"  小猫变身占比: {bonus_dist['小猫变身']/100:.1f}%")
        
        # 验证总和
        prize_sum = sum(prize_dist.values())
        bonus_sum = sum(bonus_dist.values())
        print(f"  开奖总和: {prize_sum}, 加奖总和: {bonus_sum}")

if __name__ == "__main__":
    main()

