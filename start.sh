#!/bin/bash
# 一键启动脚本：Web 服务 + App 模拟器

set -euo pipefail

PORT=9091
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
WEB_LOG="logs/web.log"
APP_LOG="logs/app_simulator.log"
WEB_PID=""
MOCK_PID=""

echo "=========================================="
echo "配置管理系统 - 一键启动脚本"
echo "=========================================="
cd "$SCRIPT_DIR"

if ! command -v python3 >/dev/null 2>&1; then
    echo "错误: 未找到 python3，请先安装 Python 3"
    exit 1
fi

echo "检查依赖..."
if ! python3 - <<'PY' >/dev/null 2>&1; then
import fastapi, uvicorn, websockets  # noqa: F401
PY
    echo "正在安装缺失依赖..."
    pip3 install fastapi uvicorn websockets >/dev/null
fi

mkdir -p logs
: > "$WEB_LOG"
: > "$APP_LOG"

START_SIMULATOR=1
PROMPT_SIMULATOR=0
for arg in "$@"; do
    case "$arg" in
        --no-simulator) START_SIMULATOR=0 ;;
        --prompt-simulator) PROMPT_SIMULATOR=1 ;;
    esac
done

cleanup() {
    echo ""
    echo "正在停止所有服务..."
    [[ -n "$MOCK_PID" ]] && kill "$MOCK_PID" 2>/dev/null || true
    [[ -n "$WEB_PID" ]] && kill "$WEB_PID" 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM

check_port() {
    local existing
    existing=$(lsof -ti:$PORT || true)
    if [[ -n "$existing" ]]; then
        echo "检测到端口 $PORT 被以下进程占用: $existing"
        echo "正在终止这些进程..."
        kill $existing >/dev/null 2>&1 || true
        sleep 1
    fi
}

wait_for_server() {
    local retries=40
    local auth="lich:123123"
    for ((i=0;i<retries;i++)); do
        if ! ps -p "$WEB_PID" >/dev/null 2>&1; then
            return 1
        fi
        if curl -su "$auth" -o /dev/null -s -w "%{http_code}" \
            "http://localhost:$PORT/api/defaults" | grep -q "200"; then
            return 0
        fi
        sleep 0.5
    done
    return 1
}

start_web() {
    check_port
    echo ""
    echo "启动 Web 服务器 (端口 $PORT)..."
    python3 -u web.py > "$WEB_LOG" 2>&1 &
    WEB_PID=$!
    if wait_for_server; then
        echo "✓ Web 服务器已启动 (PID: $WEB_PID)"
        echo "  访问地址: http://localhost:$PORT"
        echo "  用户名: lich"
        echo "  密码: 123123"
        return 0
    fi

    echo "✗ Web 服务器启动失败，请查看 $WEB_LOG"
    if [ -s "$WEB_LOG" ]; then
        echo "------ Web 日志 ------"
        tail -n 50 "$WEB_LOG"
        echo "----------------------"
    else
        echo "日志为空，尝试输出 Python 错误信息..."
        wait "$WEB_PID" 2>/dev/null || true
    fi
    WEB_PID=""
    return 1
}

start_simulator() {
    echo "启动 App 模拟器..."
    python3 -u app_simulator.py > "$APP_LOG" 2>&1 &
    MOCK_PID=$!
    sleep 2
    if ps -p "$MOCK_PID" >/dev/null 2>&1; then
        echo "✓ App 模拟器已启动 (PID: $MOCK_PID)"
    else
        echo "✗ App 模拟器启动失败，请查看 $APP_LOG"
        if [ -s "$APP_LOG" ]; then
            echo "------ 模拟器日志 ------"
            tail -n 50 "$APP_LOG"
            echo "------------------------"
        fi
        MOCK_PID=""
    fi
}

main() {
    if ! start_web; then
        exit 1
    fi

    if [[ $PROMPT_SIMULATOR -eq 1 ]]; then
        read -p "是否启动 App 模拟器? (y/n): " -r -n 1
        echo
        [[ $REPLY =~ ^[Yy]$ ]] && start_simulator
    elif [[ $START_SIMULATOR -eq 1 ]]; then
        start_simulator
    else
        echo "已跳过 App 模拟器启动（--no-simulator）"
    fi

    echo ""
    echo "=========================================="
    echo "所有服务已启动！"
    echo "=========================================="
    echo ""
    echo "服务列表:"
    echo "  - Web 服务器: http://localhost:$PORT (PID: ${WEB_PID:-N/A})"
    if [[ -n "$MOCK_PID" ]]; then
        echo "  - App 模拟器: (PID: $MOCK_PID)"
    fi
    echo ""
    echo "日志文件:"
    echo "  - Web 服务器: $WEB_LOG"
    if [[ -n "$MOCK_PID" ]]; then
        echo "  - App 模拟器: $APP_LOG"
    fi
    echo ""
    echo "按 Ctrl+C 停止所有服务"
    echo ""
    wait
}

main "$@"

