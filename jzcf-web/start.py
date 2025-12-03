#!/usr/bin/env python3
"""
一键启动脚本（Python版本）
启动所有服务：Web服务器、模拟设备等
"""
import subprocess
import sys
import os
import time
import signal
import socket
import base64
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# 获取脚本所在目录
SCRIPT_DIR = Path(__file__).parent.absolute()
os.chdir(SCRIPT_DIR)

# 进程列表
processes = []
PORT = 9091
WEB_LOG = Path("logs/web.log")
APP_LOG = Path("logs/app_simulator.log")

def cleanup(signum=None, frame=None):
    """清理所有后台进程"""
    print("\n正在停止所有服务...")
    for proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except:
            try:
                proc.kill()
            except:
                pass
    sys.exit(0)

# 注册信号处理
signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

def check_dependencies():
    """检查依赖"""
    print("检查依赖...")
    try:
        import fastapi
        import uvicorn
        import websockets
    except ImportError:
        print("正在安装依赖...")
        subprocess.run([sys.executable, "-m", "pip", "install",
                        "fastapi", "uvicorn", "websockets", "-q"],
                       check=True)

def show_log_tail(path: Path, title: str = "日志"):
    try:
        content = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"未找到日志文件 {path}")
        return
    if content.strip():
        print(f"------ {title} ------")
        print("\n".join(content.strip().splitlines()[-50:]))
        print("----------------------")
    else:
        print(f"{path} 为空，进程可能在启动前即退出。")

def free_port():
    try:
        result = subprocess.run(
            ["lsof", "-ti", f":{PORT}"],
            capture_output=True,
            text=True,
            check=False
        )
        pids = [pid.strip() for pid in result.stdout.splitlines() if pid.strip()]
        if pids:
            print(f"检测到端口 {PORT} 被占用，正在终止进程: {' '.join(pids)}")
            for pid in pids:
                subprocess.run(["kill", "-9", pid], check=False)
            time.sleep(1)
    except FileNotFoundError:
        pass  # lsof 不存在时忽略

def wait_for_server(proc, timeout=20):
    auth_header = "Basic " + base64.b64encode(b"lich:123123").decode()
    url = f"http://localhost:{PORT}/api/defaults"
    for _ in range(timeout * 2):
        if proc.poll() is not None:
            return False
        req = Request(url, headers={"Authorization": auth_header})
        try:
            with urlopen(req, timeout=1) as resp:
                if resp.status == 200:
                    return True
        except (URLError, HTTPError):
            time.sleep(0.5)
    return False

def start_web_server():
    """启动Web服务器"""
    print(f"\n启动 Web 服务器 (端口 {PORT})...")
    WEB_LOG.parent.mkdir(exist_ok=True)
    WEB_LOG.write_text("", encoding="utf-8")
    free_port()
    log_file = WEB_LOG.open("w", encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, "-u", "web.py"],
        stdout=log_file,
        stderr=subprocess.STDOUT,
        cwd=SCRIPT_DIR
    )
    processes.append(proc)

    if wait_for_server(proc):
        print(f"✓ Web 服务器已启动 (PID: {proc.pid})")
        print(f"  访问地址: http://localhost:{PORT}")
        print("  用户名: lich")
        print("  密码: 123123")
        return True

    print("✗ Web 服务器启动失败，请查看 logs/web.log")
    show_log_tail(WEB_LOG, "Web 日志")
    processes.remove(proc)
    return False

def start_app_simulator():
    """启动 App 模拟器"""
    print("\n启动 App 模拟器...")
    APP_LOG.parent.mkdir(exist_ok=True)
    APP_LOG.write_text("", encoding="utf-8")
    log_file = APP_LOG.open("w", encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, "-u", "app_simulator.py"],
        stdout=log_file,
        stderr=subprocess.STDOUT,
        cwd=SCRIPT_DIR
    )
    processes.append(proc)
    time.sleep(1)
    
    if proc.poll() is None:
        print(f"✓ App 模拟器已启动 (PID: {proc.pid})")
        return True
    else:
        print("✗ App 模拟器启动失败，请查看 logs/app_simulator.log")
        show_log_tail(APP_LOG, "模拟器日志")
        processes.remove(proc)
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("水果机配置管理系统 - 一键启动脚本")
    print("=" * 50)
    
    # 创建日志目录
    Path("logs").mkdir(exist_ok=True)
    
    # 检查依赖
    check_dependencies()
    
    # 启动Web服务器
    if not start_web_server():
        cleanup()
        return
    
    # 解析参数
    start_simulator = True
    prompt_simulator = False
    for arg in sys.argv[1:]:
        if arg == "--no-simulator":
            start_simulator = False
        elif arg == "--prompt-simulator":
            prompt_simulator = True
    
    if prompt_simulator:
        try:
            response = input("\n是否启动 App 模拟器? (y/n): ").strip().lower()
            if response in ['y', 'yes']:
                start_app_simulator()
        except KeyboardInterrupt:
            cleanup()
            return
    elif start_simulator:
        start_app_simulator()
    else:
        print("已跳过 App 模拟器启动（--no-simulator）")
    
    print("\n" + "=" * 50)
    print("所有服务已启动！")
    print("=" * 50)
    print("\n服务列表:")
    print(f"  - Web 服务器: http://localhost:{PORT} (PID: {processes[0].pid})")
    if len(processes) > 1:
        print(f"  - App 模拟器: (PID: {processes[1].pid})")
    print("\n日志文件:")
    print("  - Web 服务器: logs/web.log")
    if len(processes) > 1:
        print("  - App 模拟器: logs/app_simulator.log")
    print("\n按 Ctrl+C 停止所有服务\n")
    
    # 等待所有进程
    try:
        for proc in processes:
            proc.wait()
    except KeyboardInterrupt:
        cleanup()

if __name__ == "__main__":
    main()

