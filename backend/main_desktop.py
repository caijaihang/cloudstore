# -*- coding: utf-8 -*-
"""
云文件存储系统 - 桌面版入口
双击运行后会：
1. 启动本地 Django 服务器 (http://127.0.0.1:52731)
2. 自动打开系统默认浏览器
3. 用户可上传、下载、管理文件（完全离线运行）

打包后即使原网站被删除，此程序仍可独立运行。
"""

import os
import sys
import time
import socket
import threading
import webbrowser
from pathlib import Path


# ============================================================
# 1. 计算运行时路径
# ============================================================
# PyInstaller 打包后：
#   - sys.frozen = True
#   - sys._MEIPASS = 临时解压目录（只读）
#   - sys.executable = EXE 文件本身的路径
# 我们使用 EXE 所在目录作为 BASE_DIR（可写，用于存储用户上传的文件）
# ============================================================

if getattr(sys, 'frozen', False):
    # 打包后运行
    BASE_DIR = Path(sys.executable).parent          # EXE 所在目录（可写）
    MEIPASS_DIR = Path(getattr(sys, '_MEIPASS', BASE_DIR))  # 临时解压目录（只读）
    # 用户上传的文件存放在 EXE 同级的 data/ 目录中
    DATA_DIR = BASE_DIR / 'data'
    STATIC_DIR = MEIPASS_DIR / 'frontend'           # 前端构建产物（只读，随包分发）
    DB_PATH = DATA_DIR / 'db.sqlite3'
    MEDIA_ROOT = DATA_DIR / 'media'
    LOG_DIR = DATA_DIR / 'logs'
else:
    # 开发模式下直接运行
    BASE_DIR = Path(__file__).resolve().parent
    DATA_DIR = BASE_DIR
    STATIC_DIR = BASE_DIR / 'frontend_build'
    DB_PATH = BASE_DIR / 'db.sqlite3'
    MEDIA_ROOT = BASE_DIR / 'media'
    LOG_DIR = BASE_DIR / 'logs'

# 确保可写目录存在（首次运行自动创建）
DATA_DIR.mkdir(parents=True, exist_ok=True)
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
(MEDIA_ROOT / 'chunks').mkdir(parents=True, exist_ok=True)
(MEDIA_ROOT / 'files').mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 将 BASE_DIR 加入 Python 搜索路径，以便 Django 能找到 cloudstore / files 包
sys.path.insert(0, str(BASE_DIR))

# ============================================================
# 2. 注入环境变量，让 Django settings 感知打包环境
# ============================================================
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cloudstore.settings')
os.environ['CLOUDSTORE_MODE'] = 'desktop'             # 标记为桌面运行模式
os.environ['CLOUDSTORE_BASE_DIR'] = str(BASE_DIR)
os.environ['CLOUDSTORE_DATA_DIR'] = str(DATA_DIR)
os.environ['CLOUDSTORE_DB_PATH'] = str(DB_PATH)
os.environ['CLOUDSTORE_MEDIA_ROOT'] = str(MEDIA_ROOT)
os.environ['CLOUDSTORE_STATIC_DIR'] = str(STATIC_DIR)

# ============================================================
# 3. Django 初始化 + 数据库迁移（首次运行自动建表）
# ============================================================
import django
django.setup()

from django.core.management import call_command

# 自动执行 migrate，确保表存在（首次运行至关重要）
try:
    call_command('migrate', '--run-syncdb', verbosity=0)
except Exception as e:
    print(f'数据库初始化失败: {e}', file=sys.stderr)


# ============================================================
# 4. 端口配置
# ============================================================
DEFAULT_PORT = 52731  # 一个不太可能被占用的端口

def find_available_port(start_port):
    """找到可用端口，如果默认被占用则自动 +1"""
    port = start_port
    while port < start_port + 100:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        try:
            sock.bind(('127.0.0.1', port))
            sock.close()
            return port
        except OSError:
            sock.close()
            port += 1
    return start_port  # 实在找不到就用默认（启动会失败）

PORT = find_available_port(DEFAULT_PORT)
SERVER_URL = f'http://127.0.0.1:{PORT}/'


# ============================================================
# 5. 启动 Django 服务器（后台线程）
# ============================================================
def run_server():
    from django.core.servers.basehttp import run
    from django.core.handlers.wsgi import WSGIHandler
    handler = WSGIHandler()
    try:
        run('127.0.0.1', PORT, handler)
    except OSError as e:
        print(f'服务器启动失败: {e}', file=sys.stderr)
        sys.exit(1)


server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()

# 等待服务器就绪
print(f'正在启动本地服务器... ({SERVER_URL})')
for _ in range(30):
    try:
        sock = socket.create_connection(('127.0.0.1', PORT), timeout=1)
        sock.close()
        break
    except OSError:
        time.sleep(0.3)
else:
    print('警告：服务器可能未正常启动，尝试继续...')


# ============================================================
# 6. 打开浏览器
# ============================================================
try:
    webbrowser.open(SERVER_URL)
except Exception:
    print(f'请手动打开浏览器访问: {SERVER_URL}')


# ============================================================
# 7. 保持进程运行
# ============================================================
print()
print('=' * 60)
print('  云文件存储系统 - 本地版已启动')
print(f'  访问地址: {SERVER_URL}')
print(f'  数据目录: {DATA_DIR}')
print('  关闭此窗口将停止服务器')
print('=' * 60)
print()

try:
    while server_thread.is_alive():
        server_thread.join(1.0)
except KeyboardInterrupt:
    print('\n正在退出...')
