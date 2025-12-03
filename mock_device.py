#!/usr/bin/env python3
"""
模拟设备 - 连接到web.py的WebSocket服务器
接收配置数据并打印出来
"""
import asyncio
import websockets
import json
import sys

async def connect_to_server(uri="ws://localhost:9091/ws/app"):
    """连接到WebSocket服务器"""
    try:
        print(f"正在连接到 {uri}...")
        async with websockets.connect(uri) as websocket:
            print("✓ 已成功连接到服务器")
            print("等待接收配置数据...\n")
            
            # 持续接收消息
            async for message in websocket:
                try:
                    data = json.loads(message)
                    print("=" * 60)
                    print("收到配置更新:")
                    print(f"类型: {data.get('type', 'unknown')}")
                    
                    if 'data' in data and isinstance(data['data'], list):
                        print(f"\n共收到 {len(data['data'])} 个难度的配置:")
                        print("-" * 60)
                        
                        for difficulty_data in data['data']:
                            difficulty = difficulty_data.get('difficulty', '?')
                            print(f"\n【难度 {difficulty}】")
                            
                            # 基础配置
                            print("  基础配置:")
                            print(f"    比倍难度: {difficulty_data.get('比倍难度', 0)}%")
                            print(f"    吃分最大值: {difficulty_data.get('吃分最大值', 0)}")
                            print(f"    吃分最小值: {difficulty_data.get('吃分最小值', 0)}")
                            print(f"    吃分返奖率: {difficulty_data.get('吃分返奖率', 0)}%")
                            print(f"    营业返奖率: {difficulty_data.get('营业返奖率', 0)}%")
                            
                            # 开奖奖项
                            print("  开奖奖项 (每10000把出现的次数):")
                            prize_fields = ['苹果', '橘子', '柠檬', '金钟', '西瓜', '双星', '99', 'bar']
                            total = 0
                            for field in prize_fields:
                                value = difficulty_data.get(field, 0)
                                total += value
                                print(f"    {field}: {value}")
                            print(f"    总计: {total}")
                    
                    print("=" * 60)
                    print()
                    
                except json.JSONDecodeError as e:
                    print(f"解析JSON失败: {e}")
                    print(f"原始消息: {message}")
                except Exception as e:
                    print(f"处理消息时出错: {e}")
                    
    except websockets.exceptions.ConnectionRefused:
        print(f"✗ 连接被拒绝，请确保服务器正在运行")
        print(f"  尝试运行: python web.py 或 uvicorn web:app")
        sys.exit(1)
    except Exception as e:
        print(f"✗ 连接失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # 可以从命令行参数获取URI
    uri = sys.argv[1] if len(sys.argv) > 1 else "ws://localhost:9091/ws/app"
    print("模拟设备启动")
    print(f"目标服务器: {uri}\n")
    
    try:
        asyncio.run(connect_to_server(uri))
    except KeyboardInterrupt:
        print("\n\n模拟设备已断开连接")

