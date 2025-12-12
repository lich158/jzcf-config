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
import signal
import sys

app = FastAPI()
security = HTTPBasic()

# 认证信息
USERNAME = "lich"
PASSWORD = "123123"

# 引入配置管理模块
from config_manager import load_config, save_config

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

# 服务器端保存所有难度的默认值（简化版本）
server_default_values = {}

# 初始化服务器端默认值（简化版本）
def init_server_default_values():
    # 从config_manager获取配置
    difficulty_configs = load_config()
    
    for difficulty in range(1, 10):
        server_default_values[difficulty] = {}
        difficulty_key = f"难度{difficulty}"
        if difficulty_key in difficulty_configs:
            # 复制配置中的配置
            for field, value in difficulty_configs[difficulty_key].items():
                server_default_values[difficulty][field] = value

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

# 添加信号处理器以实现优雅关闭
def signal_handler(signum, frame):
    print(f"收到信号 {signum}，正在优雅关闭...")
    # 这里可以添加清理代码
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

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
            # 提取难度数字（支持"难度1"或"1"格式）
            diff_str = difficulty_key[2:] if difficulty_key.startswith("难度") else difficulty_key
            try:
                difficulty = int(diff_str)
                if 1 <= difficulty <= 9 and isinstance(difficulty_data, dict):
                    server_default_values[difficulty].update(difficulty_data)
            except (ValueError, TypeError):
                continue
        print(f"已更新服务器端默认值")
        
        # 保存配置到持久化存储
        try:
            save_config(body)
            print("配置已保存到持久化存储")
        except Exception as e:
            print(f"保存配置时出错: {e}")
    
    # 广播完整配置给所有轻量级设备
    full_config_data = get_all_difficulties_data()
    asyncio.create_task(broadcast_to_lightweight_devices(full_config_data))

    return {"status": "success", "message": f"已发送给 {len(lightweight_connections)} 个轻量级设备"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9092)
