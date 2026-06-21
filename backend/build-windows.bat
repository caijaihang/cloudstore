@echo off
REM ============================================================
REM  云文件存储系统 - Windows 一键打包脚本
REM  产物: dist\CloudStore\CloudStore.exe
REM  双击运行即可启动（启动本地服务器 + 打开浏览器）
REM ============================================================

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ============================================================
echo   Cloud File Storage - Windows Build Script
echo ============================================================
echo.

REM ------------------------------------------------------------
REM Step 1: 检查 Python
REM ------------------------------------------------------------
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] 未检测到 Python，请先安装 Python 3.10+
    echo         下载地址: https://www.python.org/downloads/
    echo         安装时请勾选 "Add Python to PATH"
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo [1/5] 检测到 Python %PYVER% ... OK

REM ------------------------------------------------------------
REM Step 2: 安装后端依赖
REM ------------------------------------------------------------
echo.
echo [2/5] 安装后端依赖 (Django, DRF, django-cors-headers, pyinstaller)
pip install django djangorestframework django-cors-headers pyinstaller Pillow
if errorlevel 1 (
    echo [ERROR] 依赖安装失败，请检查网络
    pause
    exit /b 1
)
echo   后端依赖安装完成

REM ------------------------------------------------------------
REM Step 3: 安装前端依赖并构建
REM ------------------------------------------------------------
echo.
echo [3/5] 构建 Vue 前端
where npm >nul 2>nul
if errorlevel 1 (
    echo [WARN] 未检测到 npm，跳过前端构建
    echo        请手动执行: cd frontend && npm install && npm run build
    echo        或确保已安装 Node.js: https://nodejs.org/
) else (
    echo   安装前端依赖...
    pushd frontend
    if not exist node_modules (
        call npm install --no-audit --no-fund
        if errorlevel 1 (
            echo [ERROR] 前端依赖安装失败
            popd
            pause
            exit /b 1
        )
    ) else (
        echo   前端依赖已存在，跳过安装
    )
    echo   执行构建...
    call npm run build
    if errorlevel 1 (
        echo [ERROR] 前端构建失败
        popd
        pause
        exit /b 1
    )
    popd
)

REM 验证前端构建产物
if not exist "frontend_build\index.html" (
    echo.
    echo [ERROR] 前端构建产物不存在: backend\frontend_build\index.html
    echo 请检查前端是否构建成功
    pause
    exit /b 1
)
echo   前端构建完成

REM ------------------------------------------------------------
REM Step 4: Django 数据库迁移
REM ------------------------------------------------------------
echo.
echo [4/5] 初始化 Django 数据库
python manage.py migrate --run-syncdb >nul 2>&1
if errorlevel 1 (
    echo [WARN] Django 迁移可能有问题，但不影响打包
) else (
    echo   数据库初始化完成
)

REM ------------------------------------------------------------
REM Step 5: PyInstaller 打包
REM ------------------------------------------------------------
echo.
echo [5/5] 运行 PyInstaller 打包 (这一步较慢，约 3-8 分钟)
echo.

REM 清理旧的构建产物
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

pyinstaller cloudstore.spec --clean --noconfirm
if errorlevel 1 (
    echo.
    echo [ERROR] 打包失败
    pause
    exit /b 1
)

REM ------------------------------------------------------------
REM 完成
REM ------------------------------------------------------------
echo.
echo ============================================================
echo   打包完成！
echo ============================================================
echo.
echo 主程序: dist\CloudStore\CloudStore.exe
echo 双击运行，自动启动服务器并打开浏览器
echo.
echo 用户数据保存在 EXE 同级目录下的 data\ 文件夹中
echo   - data\db.sqlite3        (文件信息数据库)
echo   - data\media\files\      (实际文件存储)
echo   - data\logs\             (运行日志)
echo.

REM 检查产物
if exist "dist\CloudStore\CloudStore.exe" (
    echo 可执行文件: [OK]
) else (
    echo [WARN] 未找到 dist\CloudStore\CloudStore.exe，请检查上面的报错
)

echo.
echo 按任意键退出...
pause >nul
endlocal
