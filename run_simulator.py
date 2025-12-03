#!/usr/bin/env python3
"""
模拟器运行脚本
提供便捷的方式运行各种模拟和测试
"""
import sys
import argparse
from difficulty_config import DIFFICULTY_CONFIG, get_difficulty_config
from simulator import simulate_game_session, analyze_player_addiction_factors
from optimize_odds import calculate_expected_return, simulate_player_behavior

def run_basic_simulator():
    """运行基础模拟器"""
    print("=" * 80)
    print("运行基础模拟器")
    print("=" * 80)
    
    # 分析上瘾因素
    print("\n玩家上瘾因素分析:")
    factors = analyze_player_addiction_factors()
    for key, value in factors.items():
        print(f"\n{value['description']}:")
        print(f"  策略: {value['strategy']}")
        print(f"  实现: {value['implementation']}")
    
    # 模拟难度1
    print("\n" + "=" * 80)
    print("模拟游戏会话（难度1，10000局）")
    print("=" * 80)
    
    config = get_difficulty_config(1)
    prize_fields = ['三倍小奖', '苹果', '橘子', '柠檬', '金钟', '西瓜', 
                    '双星', '99', '小bar', '中bar', '大bar', '金猪奖']
    bonus_fields = ['双响炮', '大四喜', '小三元', '大三元', '彩金', 
                    '开火车', '统统有奖', '大满贯', '仙女散花', '小猫变身']
    
    prize_dist = {field: config[field] for field in prize_fields}
    bonus_dist = {field: config[field] for field in bonus_fields}
    
    results = simulate_game_session(1, prize_dist, bonus_dist, rounds=10000)
    
    print(f"\n结果统计:")
    print(f"  总押注: {results['total_bet']:,}")
    print(f"  总奖金: {results['total_win']:,}")
    print(f"  返奖率: {results['return_rate']:.2f}%")
    print(f"  中奖率: {results['win_rate']:.2f}%")
    print(f"  大奖次数(30倍+): {results['big_wins']}")
    print(f"  加奖次数: {results['bonus_wins']}")
    print(f"  最大单次奖金: {results['max_win']:,}")

def run_all_difficulties(rounds=10000):
    """测试所有难度"""
    print("=" * 80)
    print(f"批量测试所有难度（每个难度 {rounds:,} 局）")
    print("=" * 80)
    
    prize_fields = ['三倍小奖', '苹果', '橘子', '柠檬', '金钟', '西瓜', 
                    '双星', '99', '小bar', '中bar', '大bar', '金猪奖']
    bonus_fields = ['双响炮', '大四喜', '小三元', '大三元', '彩金', 
                    '开火车', '统统有奖', '大满贯', '仙女散花', '小猫变身']
    
    prize_multipliers = {
        '三倍小奖': 3, '苹果': 5, '橘子': 10, '柠檬': 15, '金钟': 20,
        '西瓜': 20, '双星': 30, '99': 40, '小bar': 30, '中bar': 60,
        '大bar': 120, '金猪奖': 100
    }
    
    for difficulty in range(1, 10):
        config = DIFFICULTY_CONFIG[difficulty - 1]
        prize_dist = {field: config[field] for field in prize_fields}
        bonus_dist = {field: config[field] for field in bonus_fields}
        
        # 计算期望返奖率
        expected_return = calculate_expected_return(
            prize_dist, bonus_dist, prize_multipliers
        )
        
        # 模拟游戏
        results = simulate_game_session(
            difficulty, prize_dist, bonus_dist, rounds=rounds
        )
        
        # 模拟玩家行为
        behavior = simulate_player_behavior(
            prize_dist, bonus_dist, prize_multipliers, rounds=rounds
        )
        
        print(f"\n难度 {difficulty}:")
        print(f"  期望返奖率: {expected_return:.2f}%")
        print(f"  实际返奖率: {results['return_rate']:.2f}%")
        print(f"  中奖率: {results['win_rate']:.2f}%")
        print(f"  大奖率: {results['big_wins']/rounds*100:.2f}%")
        print(f"  加奖率: {results['bonus_wins']/rounds*100:.2f}%")
        print(f"  参与度评分: {behavior['engagement_score']:.1f}/100")
        print(f"  三倍小奖占比: {prize_dist['三倍小奖']/100:.1f}%")
        print(f"  小猫变身占比: {bonus_dist['小猫变身']/100:.1f}%")

def main():
    parser = argparse.ArgumentParser(description='模拟器运行脚本')
    parser.add_argument('--mode', choices=['basic', 'all', 'single'], 
                       default='basic', help='运行模式')
    parser.add_argument('--difficulty', type=int, choices=range(1, 10),
                       help='指定难度（1-9），仅在single模式下使用')
    parser.add_argument('--rounds', type=int, default=10000,
                       help='模拟局数（默认10000）')
    
    args = parser.parse_args()
    
    if args.mode == 'basic':
        run_basic_simulator()
    elif args.mode == 'all':
        run_all_difficulties(rounds=args.rounds)
    elif args.mode == 'single':
        if not args.difficulty:
            print("错误: single模式需要指定--difficulty参数")
            sys.exit(1)
        
        config = get_difficulty_config(args.difficulty)
        prize_fields = ['三倍小奖', '苹果', '橘子', '柠檬', '金钟', '西瓜', 
                        '双星', '99', '小bar', '中bar', '大bar', '金猪奖']
        bonus_fields = ['双响炮', '大四喜', '小三元', '大三元', '彩金', 
                        '开火车', '统统有奖', '大满贯', '仙女散花', '小猫变身']
        
        prize_dist = {field: config[field] for field in prize_fields}
        bonus_dist = {field: config[field] for field in bonus_fields}
        
        print(f"模拟难度 {args.difficulty} ({args.rounds:,} 局)")
        results = simulate_game_session(
            args.difficulty, prize_dist, bonus_dist, rounds=args.rounds
        )
        
        print(f"\n结果:")
        print(f"  返奖率: {results['return_rate']:.2f}%")
        print(f"  中奖率: {results['win_rate']:.2f}%")
        print(f"  大奖次数: {results['big_wins']}")
        print(f"  加奖次数: {results['bonus_wins']}")

if __name__ == "__main__":
    main()

