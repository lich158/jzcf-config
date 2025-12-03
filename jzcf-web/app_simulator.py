#!/usr/bin/env python3
"""
App模拟器 - 模拟Android App连接并接收配置
功能：
1. 连接到WebSocket服务器
2. 接收页面发送的配置更新
3. 格式化显示配置数据
4. 验证数据完整性（总和检查）
5. 检测异常值（如负数）
"""
import asyncio
import websockets
import json
import sys
from datetime import datetime
from typing import Dict, Any
from collections import defaultdict

class AppSimulator:
    """App模拟器类"""
    
    def __init__(self, uri: str = "ws://localhost:9091/ws/app"):
        self.uri = uri
        self.received_configs = {}
        self.message_count = 0
    
    def validate_config(self, difficulty_key: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证配置数据
        返回验证结果和问题列表
        """
        issues = []
        warnings = []
        
        # 开奖奖项字段
        prize_fields = ['三倍小奖', '苹果', '橘子', '柠檬', '金钟', '西瓜', 
                        '双星', '99', '小bar', '中bar', '大bar', '金猪奖']
        
        # 加奖奖项字段
        bonus_fields = ['双响炮', '大四喜', '小三元', '大三元', '彩金', 
                        '开火车', '统统有奖', '大满贯', '仙女散花', '小猫变身']
        
        # 检查开奖总和
        prize_total = sum(config.get(field, 0) for field in prize_fields)
        if prize_total != 10000:
            issues.append(f"开奖总和错误: {prize_total} (应为10000)")
        
        # 检查加奖总和
        bonus_total = sum(config.get(field, 0) for field in bonus_fields)
        if bonus_total != 10000:
            issues.append(f"加奖总和错误: {bonus_total} (应为10000)")
        
        # 检查负数
        for field in prize_fields + bonus_fields:
            value = config.get(field, 0)
            if value < 0:
                issues.append(f"{field} 为负数: {value}")
            elif value == 0 and field != '金猪奖':  # 金猪奖可以为0（加奖入口）
                warnings.append(f"{field} 为0，可能配置错误")
        
        # 检查金猪奖（特殊处理：加奖入口，不应该有倍数）
        jinzhu_value = config.get('金猪奖', 0)
        if jinzhu_value < 0:
            issues.append(f"金猪奖为负数: {jinzhu_value} (金猪奖是加奖入口，不应为负)")
        
        # 检查基础参数
        if config.get('吃分最小值', 0) >= config.get('吃分最大值', 0):
            issues.append(f"吃分最小值({config.get('吃分最小值')}) >= 吃分最大值({config.get('吃分最大值')})")
        
        if not (0 <= config.get('比倍难度', 0) <= 100):
            issues.append(f"比倍难度超出范围: {config.get('比倍难度')}")
        
        if not (0 <= config.get('吃分返奖率', 0) <= 100):
            issues.append(f"吃分返奖率超出范围: {config.get('吃分返奖率')}")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'prize_total': prize_total,
            'bonus_total': bonus_total
        }
    
    def format_config_display(self, difficulty_key: str, config: Dict[str, Any]) -> str:
        """格式化配置显示"""
        lines = []
        lines.append(f"\n{'='*80}")
        lines.append(f"【{difficulty_key}】配置详情")
        lines.append(f"{'='*80}")
        
        # 基础配置
        lines.append("\n【基础配置】")
        lines.append(f"  比倍难度: {config.get('比倍难度', 0)}%")
        lines.append(f"  吃分最大值: {config.get('吃分最大值', 0):,}")
        lines.append(f"  吃分最小值: {config.get('吃分最小值', 0):,}")
        lines.append(f"  吃分返奖率: {config.get('吃分返奖率', 0)}%")
        lines.append(f"  营业返奖率: {config.get('营业返奖率', 0)}%")
        
        # 开奖奖项
        lines.append("\n【开奖奖项】（每10000把出现的次数，总和应为10000）")
        prize_fields = ['三倍小奖', '苹果', '橘子', '柠檬', '金钟', '西瓜', 
                        '双星', '99', '小bar', '中bar', '大bar', '金猪奖']
        
        prize_multipliers = {
            '三倍小奖': 3, '苹果': 5, '橘子': 10, '柠檬': 15, '金钟': 20,
            '西瓜': 20, '双星': 30, '99': 40, '小bar': 30, '中bar': 60,
            '大bar': 120, '金猪奖': None  # 金猪奖是加奖入口，没有倍数
        }
        
        prize_total = 0
        for field in prize_fields:
            value = config.get(field, 0)
            prize_total += value
            multiplier = prize_multipliers.get(field)
            if multiplier:
                lines.append(f"  {field:8s}: {value:5d}  (倍数: {multiplier:3d})")
            else:
                lines.append(f"  {field:8s}: {value:5d}  (加奖入口，无倍数)")
        
        lines.append(f"  开奖总和: {prize_total:,} {'✓' if prize_total == 10000 else '✗'}")
        
        # 加奖奖项
        lines.append("\n【加奖奖项】（每10000把出现的次数，总和应为10000）")
        bonus_fields = ['双响炮', '大四喜', '小三元', '大三元', '彩金', 
                        '开火车', '统统有奖', '大满贯', '仙女散花', '小猫变身']
        
        bonus_total = 0
        for field in bonus_fields:
            value = config.get(field, 0)
            bonus_total += value
            lines.append(f"  {field:8s}: {value:5d}")
        
        lines.append(f"  加奖总和: {bonus_total:,} {'✓' if bonus_total == 10000 else '✗'}")
        
        # 验证结果
        validation = self.validate_config(difficulty_key, config)
        if validation['issues']:
            lines.append(f"\n【验证结果】✗ 发现 {len(validation['issues'])} 个问题:")
            for issue in validation['issues']:
                lines.append(f"  ⚠ {issue}")
        else:
            lines.append(f"\n【验证结果】✓ 配置有效")
        
        if validation['warnings']:
            lines.append(f"\n【警告】发现 {len(validation['warnings'])} 个警告:")
            for warning in validation['warnings']:
                lines.append(f"  ⚠ {warning}")
        
        lines.append(f"{'='*80}\n")
        
        return "\n".join(lines)
    
    async def connect_and_listen(self):
        """连接服务器并监听配置更新"""
        try:
            print(f"{'='*80}")
            print(f"App模拟器启动")
            print(f"{'='*80}")
            print(f"目标服务器: {self.uri}")
            print(f"等待连接...\n")
            
            async with websockets.connect(self.uri) as websocket:
                print("✓ 已成功连接到服务器")
                print("等待接收配置数据...\n")
                
                # 持续接收消息
                async for message in websocket:
                    try:
                        self.message_count += 1
                        data = json.loads(message)
                        
                        print(f"\n{'#'*80}")
                        print(f"收到消息 #{self.message_count}")
                        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        print(f"类型: {data.get('type', 'unknown')}")
                        print(f"时间戳: {data.get('timestamp', 'N/A')}")
                        print(f"{'#'*80}")
                        
                        if 'data' in data:
                            config_data = data['data']
                            
                            # 处理新格式：{"难度1": {...}, "难度2": {...}}
                            if isinstance(config_data, dict):
                                print(f"\n共收到 {len(config_data)} 个难度的配置:\n")
                                
                                for difficulty_key, config in sorted(config_data.items()):
                                    # 显示配置详情
                                    print(self.format_config_display(difficulty_key, config))
                                    
                                    # 保存配置
                                    self.received_configs[difficulty_key] = config
                                
                                # 总结
                                print(f"\n{'='*80}")
                                print("配置接收完成")
                                print(f"{'='*80}")
                                print(f"共接收 {len(config_data)} 个难度配置")
                                
                                # 检查是否有问题
                                total_issues = 0
                                for difficulty_key, config in config_data.items():
                                    validation = self.validate_config(difficulty_key, config)
                                    total_issues += len(validation['issues'])
                                
                                if total_issues > 0:
                                    print(f"\n⚠ 发现 {total_issues} 个配置问题，请检查上述输出")
                                else:
                                    print("✓ 所有配置验证通过")
                                print()
                            
                            # 兼容旧格式：数组格式
                            elif isinstance(config_data, list):
                                print(f"\n共收到 {len(config_data)} 个难度的配置（旧格式）:\n")
                                for item in config_data:
                                    difficulty = item.get('难度') or item.get('difficulty', '?')
                                    difficulty_key = f"难度{difficulty}"
                                    print(self.format_config_display(difficulty_key, item))
                                    self.received_configs[difficulty_key] = item
                        
                    except json.JSONDecodeError as e:
                        print(f"\n✗ 解析JSON失败: {e}")
                        print(f"原始消息: {message[:200]}...")
                    except Exception as e:
                        print(f"\n✗ 处理消息时出错: {e}")
                        import traceback
                        traceback.print_exc()
                        
        except websockets.exceptions.ConnectionRefused:
            print(f"\n✗ 连接被拒绝")
            print(f"请确保服务器正在运行:")
            print(f"  python3 web.py")
            print(f"  或")
            print(f"  python3 web_v2.py")
            sys.exit(1)
        except KeyboardInterrupt:
            print(f"\n\n{'='*80}")
            print("模拟器已断开连接")
            print(f"共接收 {self.message_count} 条消息")
            print(f"共保存 {len(self.received_configs)} 个难度配置")
            print(f"{'='*80}")
        except Exception as e:
            print(f"\n✗ 连接失败: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='App模拟器 - 模拟Android App连接并接收配置')
    parser.add_argument('--uri', type=str, default='ws://localhost:9091/ws/app',
                       help='WebSocket服务器地址（默认: ws://localhost:9091/ws/app）')
    parser.add_argument('--host', type=str, default='localhost',
                       help='服务器主机（默认: localhost）')
    parser.add_argument('--port', type=int, default=9091,
                       help='服务器端口（默认: 9091）')
    
    args = parser.parse_args()
    
    # 如果指定了host或port，构建URI
    if args.host != 'localhost' or args.port != 9091:
        uri = f"ws://{args.host}:{args.port}/ws/app"
    else:
        uri = args.uri
    
    simulator = AppSimulator(uri)
    
    try:
        asyncio.run(simulator.connect_and_listen())
    except KeyboardInterrupt:
        print("\n模拟器已停止")

if __name__ == "__main__":
    main()

