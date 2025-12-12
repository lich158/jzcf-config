#!/usr/bin/env python3
"""
轻量级后端服务
专门为大量只读设备提供配置数据推送服务
优化资源使用，无心跳机制，设备不发送数据
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Depends, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import json
import weakref
import asyncio
import datetime
import os
import sys

# 添加当前目录到Python路径，以便正确导入difficulty_config
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入真实的难度配置数据
from difficulty_config import DIFFICULTY_CONFIG

app = FastAPI()
security = HTTPBasic()

# 认证信息
USERNAME = "lich"
PASSWORD = "123123"

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != USERNAME or credentials.password != PASSWORD:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# 使用弱引用集合保存轻量级连接，避免内存泄漏
lightweight_connections = weakref.WeakSet()

# 服务器端保存所有难度的默认值（使用真实配置）
server_default_values = {}

# 初始化服务器端默认值（使用真实配置）
def init_server_default_values():
    # 基础配置字段
    base_fields = ['比倍难度', '吃分最大值', '吃分最小值', '吃分返奖率', '营业返奖率']
    # 开奖奖项字段
    prize_fields = ['三倍小奖', '苹果', '橘子', '柠檬', '金钟', '西瓜', '双星', '99', 
                    '小bar', '中bar', '大bar', '金猪奖']
    # 加奖奖项字段
    bonus_fields = ['双响炮', '大四喜', '小三元', '大三元', '彩金', '开火车', '统统有奖', '大满贯', '仙女散花', '小猫变身']
    
    # 使用真实的难度配置数据
    for difficulty_index, config_data in enumerate(DIFFICULTY_CONFIG):
        difficulty = difficulty_index + 1
        server_default_values[difficulty] = {}
        
        # 复制所有配置字段
        for field in base_fields + prize_fields + bonus_fields:
            if field in config_data:
                server_default_values[difficulty][field] = config_data[field]
            else:
                # 对于不存在的字段，设置默认值为0
                server_default_values[difficulty][field] = 0

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

# 轻量级WebSocket连接处理函数
async def lightweight_websocket_handler(websocket: WebSocket):
    """处理大量只读设备的轻量级WebSocket连接"""
    await websocket.accept()
    
    # 添加到轻量级连接集合
    lightweight_connections.add(websocket)
    print(f"轻量级设备连接: {websocket.client}, 当前轻量级连接数: {len(lightweight_connections)}")
    
    # 发送初始配置数据
    try:
        all_data = get_all_difficulties_data()
        await websocket.send_text(json.dumps({
            "type": "update",
            "timestamp": datetime.datetime.now().isoformat(),
            "data": all_data
        }, ensure_ascii=False))
        print(f"已向新连接的轻量级设备发送初始配置")
    except Exception as e:
        print(f"发送初始配置失败: {e}")
    
    # 等待连接断开，不处理任何接收的消息
    try:
        # 简单等待，不接收任何数据
        await asyncio.Future()  # 永远不会完成，除非连接断开
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"轻量级连接处理异常: {e}")
    finally:
        # 从连接集合中移除
        try:
            lightweight_connections.discard(websocket)  # WeakSet使用discard而不是remove
            print(f"轻量级设备断开: {websocket.client}, 剩余连接数: {len(lightweight_connections)}")
        except Exception as e:
            print(f"移除轻量级连接时出错: {e}")

# 广播配置更新给所有轻量级设备
async def broadcast_to_lightweight_devices(message_data):
    """向所有轻量级设备广播配置更新"""
    if not lightweight_connections:
        return
    
    # 转换为列表以避免在迭代过程中集合发生变化
    connections = list(lightweight_connections)
    print(f"准备向 {len(connections)} 个轻量级设备广播配置更新")
    
    # 创建发送任务
    tasks = []
    message_json = json.dumps({
        "type": "update",
        "timestamp": datetime.datetime.now().isoformat(),
        "data": message_data
    }, ensure_ascii=False)
    
    for connection in connections:
        task = asyncio.create_task(send_to_single_lightweight_device(connection, message_json))
        tasks.append(task)
    
    # 并发执行所有发送任务
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
    
    print(f"已完成向轻量级设备广播配置更新")

async def send_to_single_lightweight_device(connection, message_json):
    """向单个轻量级设备发送消息"""
    try:
        await connection.send_text(message_json)
    except Exception as e:
        print(f"向轻量级设备发送消息失败: {e}")
        try:
            lightweight_connections.discard(connection)
        except:
            pass

# 初始化服务器默认值
init_server_default_values()

@app.websocket("/ws/lightweight")
async def lightweight_websocket(websocket: WebSocket):
    """轻量级WebSocket端点，用于大量只读设备连接"""
    await lightweight_websocket_handler(websocket)

# 提供前端页面
@app.get("/")
async def index():
    return FileResponse("frontend.html")

# 获取所有难度的默认值
@app.get("/api/defaults")
async def get_defaults(username: str = Depends(verify_credentials)):
    return get_all_difficulties_data()

# 接收来自网页的修改，并广播给所有轻量级设备
@app.post("/send")
async def send_to_app(request: Request, username: str = Depends(verify_credentials)):
    body = await request.json()
    
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
    
    # 广播给所有轻量级设备 - 发送完整的配置数据而不是部分更新
    full_config_data = get_all_difficulties_data()
    asyncio.create_task(broadcast_to_lightweight_devices(full_config_data))

    return {"status": "success", "message": f"已发送给 {len(lightweight_connections)} 个轻量级设备"}

if __name__ == "__main__":
    import uvicorn
    # 兼容Python 3.6版本，使用替代方法启动uvicorn服务器
    loop = asyncio.get_event_loop()
    config = uvicorn.Config(app, host="0.0.0.0", port=9092)
    server = uvicorn.Server(config)
    loop.run_until_complete(server.serve())