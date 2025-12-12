#!/bin/bash

# 水果机配置管理系统 - 一键部署脚本
# 功能：安装依赖、设置开机自启、启动服务

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="lightweight_backend"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

echo "========================================="
echo "水果机配置管理系统 - 一键部署脚本"
echo "========================================="

# 检查是否以root权限运行
if [[ $EUID -ne 0 ]]; then
   echo "此脚本必须以root权限运行" 
   exit 1
fi

# 检查Python路径
PYTHON_PATH=$(which python3)
if [ -z "$PYTHON_PATH" ]; then
    echo "错误: 未找到python3"
    exit 1
fi

echo "使用Python路径: $PYTHON_PATH"

# 检查pip路径
PIP_PATH=$(which pip3)
if [ -z "$PIP_PATH" ]; then
    echo "错误: 未找到pip3"
    exit 1
fi

# 安装必要的Python包
echo "安装必要的Python包..."
$PIP_PATH install fastapi uvicorn websockets

# 检查轻量级后端服务文件是否存在
if [ ! -f "${SCRIPT_DIR}/lightweight_backend.py" ]; then
    echo "错误: lightweight_backend.py 文件不存在"
    exit 1
fi

# 1. 停止已运行的服务（如果存在）
echo "检查并停止正在运行的服务..."
if systemctl is-active --quiet ${SERVICE_NAME}.service; then
    echo "停止正在运行的服务..."
    systemctl stop ${SERVICE_NAME}.service
elif pgrep -f "lightweight_backend.py" > /dev/null; then
    echo "检测到轻量级服务已在运行，正在停止..."
    pkill -f "lightweight_backend.py"
    sleep 2
fi

# 2. 创建 systemd 服务文件
echo "创建 systemd 服务文件..."
cat > ${SERVICE_FILE} << EOF
[Unit]
Description=Fruit Machine Lightweight Backend Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${SCRIPT_DIR}
ExecStart=${PYTHON_PATH} ${SCRIPT_DIR}/lightweight_backend.py
Restart=always
RestartSec=2
StandardOutput=journal
StandardError=journal
SyslogIdentifier=${SERVICE_NAME}
Environment=PATH=/usr/local/bin:/usr/bin:/bin
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=10
TimeoutStartSec=15

[Install]
WantedBy=multi-user.target
EOF

# 3. 重新加载 systemd 配置
echo "重新加载 systemd 配置..."
systemctl daemon-reload

# 4. 启用服务（开机自启）
echo "启用服务（开机自启）..."
systemctl enable ${SERVICE_NAME}.service

# 5. 启动服务
echo "启动服务..."
systemctl start ${SERVICE_NAME}.service

# 6. 检查服务状态
echo "检查服务状态..."
sleep 3
if systemctl is-active --quiet ${SERVICE_NAME}.service; then
    echo "服务启动成功！"
    echo ""
    echo "访问地址:"
    echo "  Web管理界面: http://localhost:9092"
    echo ""
    echo "服务管理命令:"
    echo "  启动服务: systemctl start ${SERVICE_NAME}.service"
    echo "  停止服务: systemctl stop ${SERVICE_NAME}.service"
    echo "  重启服务: systemctl restart ${SERVICE_NAME}.service"
    echo "  查看状态: systemctl status ${SERVICE_NAME}.service"
    echo "  实时日志: journalctl -u ${SERVICE_NAME}.service -f"
    echo ""
    echo "配置文件:"
    echo "  持久化配置: ${SCRIPT_DIR}/config_data.json"
    echo ""
else
    echo "服务启动失败，请检查日志: journalctl -u ${SERVICE_NAME}.service"
    exit 1
fi

echo "========================================="
echo "部署完成！"
echo "========================================="