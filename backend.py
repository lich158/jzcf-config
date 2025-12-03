#!/usr/bin/env python3
"""
后端API服务
提供WebSocket和REST API接口
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import json
import os

app = FastAPI()
security = HTTPBasic()

# 认证信息
USERNAME = "lich"
PASSWORD = "123123"

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != USERNAME or credentials.password != PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# 保存所有连接的 App WebSocket
active_connections = set()

# 服务器端保存所有难度的默认值
server_default_values = {}

# 初始化服务器端默认值（用户提供的具体数值）
def init_server_default_values():
    # 基础配置字段
    base_fields = ['比倍难度', '吃分最大值', '吃分最小值', '吃分返奖率', '营业返奖率']
    # 开奖奖项字段（新的字段名）
    prize_fields = ['三倍小奖', '苹果', '橘子', '柠檬', '金钟', '西瓜', '双星', '99', 
                    '小bar', '中bar', '大bar', '金猪奖']
    # 加奖奖项字段（新的字段名和顺序）
    bonus_fields = ['双响炮', '大四喜', '小三元', '大三元', '彩金', '开火车', '统统有奖', '大满贯', '仙女散花', '小猫变身']
    
    # 资深博彩设计：最大化玩家刺激，确保庄家盈利
    # 吃分返奖率：吃了100分，返给玩家的分数（百分比）
    # 难度1：返奖率80%（庄家赢20%），难度9：返奖率40%（庄家赢60%）
    # 营业返奖率：整体营业返奖率（包含加奖），略高于吃分返奖率
    default_data = {
        1: {'比倍难度': 20, '吃分最大值': 2000, '吃分最小值': 300, '吃分返奖率': 80, '营业返奖率': 83},
        2: {'比倍难度': 25, '吃分最大值': 2400, '吃分最小值': 400, '吃分返奖率': 75, '营业返奖率': 78},
        3: {'比倍难度': 30, '吃分最大值': 2800, '吃分最小值': 500, '吃分返奖率': 70, '营业返奖率': 73},
        4: {'比倍难度': 35, '吃分最大值': 3200, '吃分最小值': 600, '吃分返奖率': 65, '营业返奖率': 68},
        5: {'比倍难度': 40, '吃分最大值': 3600, '吃分最小值': 700, '吃分返奖率': 60, '营业返奖率': 63},
        6: {'比倍难度': 45, '吃分最大值': 4000, '吃分最小值': 800, '吃分返奖率': 55, '营业返奖率': 58},
        7: {'比倍难度': 50, '吃分最大值': 4400, '吃分最小值': 900, '吃分返奖率': 50, '营业返奖率': 53},
        8: {'比倍难度': 55, '吃分最大值': 4800, '吃分最小值': 1000, '吃分返奖率': 45, '营业返奖率': 48},
        9: {'比倍难度': 60, '吃分最大值': 5200, '吃分最小值': 1100, '吃分返奖率': 40, '营业返奖率': 43}
    }
    
    # 资深博彩设计：最大化刺激感，让玩家有更多中大奖的机会
    # 核心策略：三倍小奖占60-68%，适当提高中高倍数奖项概率，增加刺激感
    # 难度越大，三倍小奖占比降低，但保持一定的高倍数概率以维持刺激
    prize_distributions = {
        1: {'三倍小奖': 6300, '苹果': 800, '橘子': 600, '柠檬': 460, '金钟': 370, '西瓜': 370, 
            '双星': 320, '99': 260, '小bar': 185, '中bar': 140, '大bar': 95, '金猪奖': 100},
        2: {'三倍小奖': 6200, '苹果': 850, '橘子': 650, '柠檬': 510, '金钟': 420, '西瓜': 420,
            '双星': 350, '99': 280, '小bar': 205, '中bar': 155, '大bar': 100, '金猪奖': 100},
        3: {'三倍小奖': 6100, '苹果': 900, '橘子': 700, '柠檬': 560, '金钟': 470, '西瓜': 470,
            '双星': 380, '99': 300, '小bar': 225, '中bar': 170, '大bar': 110, '金猪奖': 100},
        4: {'三倍小奖': 6000, '苹果': 950, '橘子': 750, '柠檬': 610, '金钟': 520, '西瓜': 520,
            '双星': 410, '99': 320, '小bar': 245, '中bar': 185, '大bar': 120, '金猪奖': 100},
        5: {'三倍小奖': 5400, '苹果': 920, '橘子': 730, '柠檬': 600, '金钟': 520, '西瓜': 520,
            '双星': 400, '99': 310, '小bar': 240, '中bar': 180, '大bar': 120, '金猪奖': 80},
        6: {'三倍小奖': 5350, '苹果': 960, '橘子': 780, '柠檬': 650, '金钟': 570, '西瓜': 570,
            '双星': 430, '99': 330, '小bar': 260, '中bar': 195, '大bar': 130, '金猪奖': 85},
        7: {'三倍小奖': 5300, '苹果': 1000, '橘子': 830, '柠檬': 700, '金钟': 620, '西瓜': 620,
            '双星': 460, '99': 350, '小bar': 280, '中bar': 210, '大bar': 140, '金猪奖': 90},
        8: {'三倍小奖': 5250, '苹果': 1050, '橘子': 880, '柠檬': 750, '金钟': 670, '西瓜': 670,
            '双星': 490, '99': 370, '小bar': 300, '中bar': 225, '大bar': 150, '金猪奖': 95},
        9: {'三倍小奖': 4700, '苹果': 1000, '橘子': 850, '柠檬': 730, '金钟': 650, '西瓜': 650,
            '双星': 470, '99': 350, '小bar': 290, '中bar': 220, '大bar': 150, '金猪奖': 90}
    }
    
    # 资深博彩设计：加奖奖项分布 - 小猫变身次数最多，最大化刺激感
    # 核心策略：小猫变身占最大比例（18-25%），让玩家经常触发高倍数奖励
    # 其他加奖奖项递减，难度越大整体加奖概率略降但仍保持刺激
    bonus_distributions = {
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
    
    for difficulty in range(1, 10):
        server_default_values[difficulty] = {}
        
        # 设置基础配置值
        if difficulty in default_data:
            for field, value in default_data[difficulty].items():
                server_default_values[difficulty][field] = value
        
        # 设置开奖奖项默认值（按难度分配，自动调整到总和10000）
        prize_total = sum(prize_distributions[difficulty].values())
        scale = 10000 / prize_total
        for field in prize_fields:
            server_default_values[difficulty][field] = int(prize_distributions[difficulty][field] * scale)
        # 调整最后一个字段确保总和为10000
        current_sum = sum(server_default_values[difficulty][field] for field in prize_fields)
        server_default_values[difficulty][prize_fields[-1]] += (10000 - current_sum)
        
        # 设置加奖奖项默认值（按难度分配，自动调整到总和10000）
        bonus_total = sum(bonus_distributions[difficulty].values())
        scale = 10000 / bonus_total
        for field in bonus_fields:
            server_default_values[difficulty][field] = int(bonus_distributions[difficulty][field] * scale)
        # 调整最后一个字段确保总和为10000
        current_sum = sum(server_default_values[difficulty][field] for field in bonus_fields)
        server_default_values[difficulty][bonus_fields[-1]] += (10000 - current_sum)

# 获取所有难度的数据（JSON数组格式）
def get_all_difficulties_data():
    base_fields = ['比倍难度', '吃分最大值', '吃分最小值', '吃分返奖率', '营业返奖率']
    prize_fields = ['三倍小奖', '苹果', '橘子', '柠檬', '金钟', '西瓜', '双星', '99', 
                    '小bar', '中bar', '大bar', '金猪奖']
    bonus_fields = ['双响炮', '大四喜', '小三元', '大三元', '彩金', '开火车', '统统有奖', '大满贯', '仙女散花', '小猫变身']
    all_fields = base_fields + prize_fields + bonus_fields
    
    all_data = {}
    for difficulty in range(1, 10):
        difficulty_data = {}
        for field in all_fields:
            difficulty_data[field] = server_default_values[difficulty][field]
        all_data[f"难度{difficulty}"] = difficulty_data
    return all_data

# 初始化服务器默认值
init_server_default_values()

@app.websocket("/ws/app")
async def websocket_app(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)
    print("App connected:", websocket.client)
    
    # 新连接时立即发送所有难度的配置数据
    try:
        all_data = get_all_difficulties_data()
        await websocket.send_text(json.dumps({
            "type": "update",
            "data": all_data
        }))
        print(f"已向新连接的App发送配置数据")
    except Exception as e:
        print(f"发送初始配置失败: {e}")

    try:
        while True:
            data = await websocket.receive_text()
            print("Received from app:", data)
    except WebSocketDisconnect:
        print("App disconnected:", websocket.client)
        active_connections.remove(websocket)

# 提供前端页面
@app.get("/")
async def index():
    return FileResponse("frontend.html")

# 获取所有难度的默认值
@app.get("/api/defaults")
async def get_defaults(username: str = Depends(verify_credentials)):
    return get_all_difficulties_data()

# 接收来自网页的修改，并广播给所有 App
@app.post("/send")
async def send_to_app(request: Request, username: str = Depends(verify_credentials)):
    body = await request.json()
    
    # body应该是一个包含所有难度（1-9）数据的JSON对象
    # 格式: {"难度1": {"比倍难度": 100, ...}, "难度2": {...}, ...}
    
    # 打印接收到的数据
    print("\n" + "="*60)
    print("收到配置数据:")
    print(json.dumps(body, indent=2, ensure_ascii=False))
    print("="*60 + "\n")
    
    # 更新服务器端的默认值
    if isinstance(body, dict):
        for difficulty_key, difficulty_data in body.items():
            try:
                # 支持"难度1"、"难度2"格式，也兼容"1"、"2"格式
                if difficulty_key.startswith("难度"):
                    difficulty = int(difficulty_key[2:])  # 去掉"难度"前缀
                else:
                    difficulty = int(difficulty_key)
                if 1 <= difficulty <= 9:
                    # 更新该难度的所有字段
                    for key, value in difficulty_data.items():
                        server_default_values[difficulty][key] = value
            except (ValueError, TypeError):
                continue
        print(f"已更新服务器端默认值")
    # 兼容旧格式（数组格式）
    elif isinstance(body, list):
        for difficulty_data in body:
            # 支持"难度"和"difficulty"两种格式
            difficulty = difficulty_data.get("难度") or difficulty_data.get("difficulty")
            if difficulty and 1 <= difficulty <= 9:
                # 更新该难度的所有字段
                for key, value in difficulty_data.items():
                    if key not in ["难度", "difficulty"]:
                        server_default_values[difficulty][key] = value
        print(f"已更新服务器端默认值（兼容旧格式）")
    
    # 广播逻辑：发送给所有连接的App
    removed_clients = []
    success_count = 0
    message = json.dumps({
        "type": "update",
        "data": body  # 发送完整的难度数组
    })
    
    print(f"准备发送给 {len(active_connections)} 个连接的App...")
    for ws in active_connections:
        try:
            await ws.send_text(message)
            success_count += 1
        except Exception as e:
            print(f"发送失败: {e}")
            removed_clients.append(ws)

    # 移除断开的客户端
    for ws in removed_clients:
        active_connections.remove(ws)

    return f"已发送给 {success_count} 个在线App（总共 {len(active_connections)} 个连接）"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9091)

