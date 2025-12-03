#!/usr/bin/env python3
"""
水果机配置管理系统 - 专业版
资深博彩设计师、产品经理、心理学家、程序员联合设计

核心特性：
1. 基于心理学原理的赔率设计
2. 精确的返奖率控制
3. 实时配置更新和广播
4. 完善的错误处理和数据验证
5. 高性能的WebSocket通信
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Depends, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
import json
import logging
from typing import Dict, Set
import asyncio
from datetime import datetime

# 导入核心配置模块
from core.game_config import GameConfigManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="水果机配置管理系统",
    description="专业的博彩游戏配置管理平台",
    version="2.0.0"
)

# CORS配置（如果需要）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 认证配置
security = HTTPBasic()
USERNAME = "lich"
PASSWORD = "123123"

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """验证用户凭证"""
    if credentials.username != USERNAME or credentials.password != PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# 全局配置管理器
config_manager = GameConfigManager()

# WebSocket连接管理
class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket):
        """接受新连接"""
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
        logger.info(f"新连接: {websocket.client}")
    
    async def disconnect(self, websocket: WebSocket):
        """断开连接"""
        async with self._lock:
            self.active_connections.discard(websocket)
        logger.info(f"连接断开: {websocket.client}")
    
    async def broadcast(self, message: dict):
        """广播消息给所有连接的客户端"""
        if not self.active_connections:
            return
        
        message_str = json.dumps(message, ensure_ascii=False)
        disconnected = []
        
        async with self._lock:
            connections = list(self.active_connections)
        
        for connection in connections:
            try:
                await connection.send_text(message_str)
            except Exception as e:
                logger.error(f"发送消息失败: {e}")
                disconnected.append(connection)
        
        # 移除断开的连接
        if disconnected:
            async with self._lock:
                for conn in disconnected:
                    self.active_connections.discard(conn)
        
        logger.info(f"已广播给 {len(connections) - len(disconnected)} 个客户端")

connection_manager = ConnectionManager()


@app.websocket("/ws/app")
async def websocket_app(websocket: WebSocket):
    """WebSocket端点：处理App连接"""
    await connection_manager.connect(websocket)
    
    # 新连接时立即发送所有难度的配置数据
    try:
        all_data = config_manager.to_dict_all()
        await websocket.send_text(json.dumps({
            "type": "update",
            "timestamp": datetime.now().isoformat(),
            "data": all_data
        }, ensure_ascii=False))
        logger.info("已向新连接的App发送配置数据")
    except Exception as e:
        logger.error(f"发送初始配置失败: {e}")
    
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"收到App消息: {data}")
            # 可以在这里处理App发送的消息
    except WebSocketDisconnect:
        await connection_manager.disconnect(websocket)


@app.get("/")
async def index(username: str = Depends(verify_credentials)):
    """提供前端页面"""
    return FileResponse("frontend.html")


@app.get("/api/defaults")
async def get_defaults(username: str = Depends(verify_credentials)):
    """获取所有难度的默认值"""
    try:
        data = config_manager.to_dict_all()
        return JSONResponse(content=data)
    except Exception as e:
        logger.error(f"获取默认值失败: {e}")
        raise HTTPException(status_code=500, detail="获取配置失败")


@app.get("/api/config/{difficulty}")
async def get_config(difficulty: int, username: str = Depends(verify_credentials)):
    """获取指定难度的配置"""
    if difficulty not in range(1, 10):
        raise HTTPException(status_code=400, detail="难度必须在1-9之间")
    
    try:
        data = config_manager.to_dict(difficulty)
        if not data:
            raise HTTPException(status_code=404, detail="配置不存在")
        return JSONResponse(content=data)
    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        raise HTTPException(status_code=500, detail="获取配置失败")


@app.get("/api/expected_return/{difficulty}")
async def get_expected_return(difficulty: int, username: str = Depends(verify_credentials)):
    """获取指定难度的期望返奖率"""
    if difficulty not in range(1, 10):
        raise HTTPException(status_code=400, detail="难度必须在1-9之间")
    
    try:
        expected_return = config_manager.calculate_expected_return_rate(difficulty)
        target_return = config_manager.TARGET_RETURN_RATES.get(difficulty, 0)
        
        return JSONResponse(content={
            "difficulty": difficulty,
            "expected_return_rate": round(expected_return, 2),
            "target_return_rate": target_return,
            "difference": round(expected_return - target_return, 2)
        })
    except Exception as e:
        logger.error(f"计算期望返奖率失败: {e}")
        raise HTTPException(status_code=500, detail="计算失败")


@app.post("/send")
async def send_to_app(request: Request, username: str = Depends(verify_credentials)):
    """
    接收来自网页的修改，并广播给所有 App
    数据格式: {"难度1": {...}, "难度2": {...}, ...}
    """
    try:
        body = await request.json()
        logger.info("=" * 60)
        logger.info("收到配置数据:")
        logger.info(json.dumps(body, indent=2, ensure_ascii=False))
        logger.info("=" * 60)
        
        # 验证和更新配置
        updated_count = 0
        errors = []
        
        if isinstance(body, dict):
            for difficulty_key, difficulty_data in body.items():
                try:
                    # 解析难度
                    if difficulty_key.startswith("难度"):
                        difficulty = int(difficulty_key[2:])
                    else:
                        difficulty = int(difficulty_key)
                    
                    if difficulty not in range(1, 10):
                        errors.append(f"无效的难度: {difficulty_key}")
                        continue
                    
                    # 更新配置
                    if config_manager.update_config(difficulty, difficulty_data):
                        updated_count += 1
                        logger.info(f"已更新难度 {difficulty} 的配置")
                    else:
                        errors.append(f"难度 {difficulty} 配置验证失败")
                except (ValueError, TypeError) as e:
                    errors.append(f"解析难度 {difficulty_key} 失败: {e}")
                    continue
        
        # 兼容旧格式（数组格式）
        elif isinstance(body, list):
            for difficulty_data in body:
                try:
                    difficulty = difficulty_data.get("难度") or difficulty_data.get("difficulty")
                    if difficulty and 1 <= difficulty <= 9:
                        if config_manager.update_config(difficulty, difficulty_data):
                            updated_count += 1
                        else:
                            errors.append(f"难度 {difficulty} 配置验证失败")
                except Exception as e:
                    errors.append(f"处理配置失败: {e}")
        
        if errors:
            logger.warning(f"配置更新错误: {errors}")
        
        # 广播更新
        all_data = config_manager.to_dict_all()
        await connection_manager.broadcast({
            "type": "update",
            "timestamp": datetime.now().isoformat(),
            "data": all_data
        })
        
        response_msg = f"已更新 {updated_count} 个难度配置，已广播给所有连接的App"
        if errors:
            response_msg += f"\n错误: {', '.join(errors)}"
        
        return JSONResponse(content={
            "success": True,
            "updated_count": updated_count,
            "errors": errors,
            "message": response_msg
        })
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="无效的JSON数据")
    except Exception as e:
        logger.error(f"处理配置更新失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return JSONResponse(content={
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_connections": len(connection_manager.active_connections)
    })


if __name__ == "__main__":
    import uvicorn
    
    # 创建日志目录
    os.makedirs("logs", exist_ok=True)
    
    logger.info("=" * 60)
    logger.info("水果机配置管理系统 - 专业版 v2.0")
    logger.info("=" * 60)
    logger.info("启动服务器...")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9091,
        log_level="info"
    )

