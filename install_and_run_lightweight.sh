#!/bin/bash

# 一键安装和运行轻量级后端服务脚本

echo "========================================="
echo "水果机配置管理系统 - 轻量级服务安装启动脚本"
echo "========================================="

# 检查是否已经安装了必要的依赖
echo "检查Python依赖..."

# 检查pip是否可用
if ! command -v pip3 &> /dev/null
then
    echo "错误: 未找到pip3，请先安装pip3"
    exit 1
fi

# 安装必要的Python包
echo "安装必要的Python包..."
pip3 install fastapi uvicorn websockets

# 检查安装是否成功
if [ $? -ne 0 ]; then
    echo "错误: Python包安装失败"
    exit 1
fi

echo "Python包安装完成"

# 检查轻量级后端服务文件是否存在
if [ ! -f "lightweight_backend.py" ]; then
    echo "错误: lightweight_backend.py 文件不存在"
    exit 1
fi

# 检查是否已经有服务在运行
if pgrep -f "lightweight_backend.py" > /dev/null
then
    echo "检测到轻量级服务已在运行，正在停止..."
    pkill -f "lightweight_backend.py"
    sleep 2
fi

# 启动轻量级后端服务
echo "启动轻量级后端服务..."
nohup python3 lightweight_backend.py > lightweight_backend.log 2>&1 &

# 等待服务启动
sleep 3

# 检查服务是否成功启动
if pgrep -f "lightweight_backend.py" > /dev/null
then
    echo "轻量级后端服务启动成功！"
    echo "服务日志: lightweight_backend.log"
    echo "服务端口: 9092"
    echo ""
    echo "使用以下命令查看服务状态:"
    echo "  ps aux | grep lightweight_backend.py"
    echo ""
    echo "使用以下命令查看服务日志:"
    echo "  tail -f lightweight_backend.log"
    echo ""
    echo "使用以下命令停止服务:"
    echo "  pkill -f lightweight_backend.py"
else
    echo "错误: 轻量级后端服务启动失败"
    echo "请检查 lightweight_backend.log 文件获取更多信息"
    exit 1
fi

echo "========================================="
echo "安装和启动完成"
echo "========================================="