# -*- mode: python ; coding: utf-8 -*-
"""
云文件存储系统 - PyInstaller 打包配置
用法:
    pip install pyinstaller
    pyinstaller cloudstore.spec --clean

打包后产物:
    dist/CloudStore/CloudStore.exe  (主程序)
"""

import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files


# 项目根目录（backend/ 所在位置）
project_root = Path(os.path.abspath(os.path.dirname(SPEC)))
backend_dir = project_root
frontend_build = backend_dir / 'frontend_build'

# ============================================================
# 1. 收集所有 Django 相关模块
# ============================================================
hiddenimports = []

# Django 核心模块
hiddenimports += collect_submodules('django')

# Django 应用 - 必须显式包含，否则运行时报 ImportError
hiddenimports += [
    'cloudstore',
    'cloudstore.settings',
    'cloudstore.urls',
    'cloudstore.wsgi',
    'cloudstore.views',
    'files',
    'files.models',
    'files.views',
    'files.serializers',
    'files.signals',
    'files.urls',
    'files.apps',
    'files.management',
    'files.management.commands',
    'files.management.commands.cleanup_chunks',
]

# Django REST Framework
hiddenimports += collect_submodules('rest_framework')

# django-cors-headers
hiddenimports += collect_submodules('corsheaders')

# SQLite 相关（已包含在 Python stdlib 中，额外保险）
hiddenimports += ['sqlite3']


# ============================================================
# 2. 收集数据文件
# ============================================================
# datas 格式: [(源路径, 目标目录名), ...]
datas = []

# 前端构建产物：复制到 _MEIPASS/frontend/
if frontend_build.exists():
    datas.append((str(frontend_build) + os.sep, 'frontend'))
else:
    print(f'警告: 前端构建目录不存在: {frontend_build}')
    print('请先运行: cd frontend && npm install && npm run build')
    print('然后将 frontend/dist 复制到 backend/frontend_build/')

# Django 的 locale 文件（可选，减少报错）
try:
    import django
    django_root = Path(django.__file__).parent
    locale_dir = django_root / 'conf' / 'locale'
    if locale_dir.exists():
        datas.append((str(locale_dir), 'django/conf/locale'))
except Exception:
    pass


# ============================================================
# 3. 二进制依赖（通常为空即可）
# ============================================================
binaries = []


# ============================================================
# 4. 分析配置
# ============================================================
a = Analysis(
    ['main_desktop.py'],              # 入口脚本
    pathex=[str(backend_dir)],        # 额外搜索路径（Django 项目根）
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的大型库以减小体积
        'matplotlib', 'numpy', 'scipy', 'pandas',
        'PyQt5', 'PyQt6', 'PySide2', 'PySide6',
        'tkinter', 'unittest',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)


# ============================================================
# 5. 生成目录形式的 EXE（比单文件启动快）
# ============================================================
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CloudStore',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,         # 启用 UPX 压缩（如系统未装则自动忽略）
    console=True,      # 显示控制台窗口（便于查看日志）
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CloudStore',
)
