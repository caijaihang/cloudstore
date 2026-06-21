# 云文件存储系统 - Windows 桌面版打包说明

将 Web 应用打包为独立的 EXE，即使网站下线，用户仍可在本地安全地使用文件存储功能。

---

## 快速开始（Windows 上打包）

### 步骤 1：准备 Python 环境

1. 安装 **Python 3.10 或更高版本**（https://www.python.org/downloads/）
2. 安装时勾选 **"Add Python to PATH"**
3. 安装 **Node.js 18+**（用于构建前端，https://nodejs.org/）

### 步骤 2：一键打包

在 `backend/` 目录下双击运行 **`build-windows.bat`**：

```
项目根目录/
└── backend/
    └── build-windows.bat   ← 双击此文件
```

脚本会自动完成：
- 安装 Python 依赖（Django, DRF, django-cors-headers, Pillow, PyInstaller）
- 安装前端 npm 依赖
- 构建 Vue 前端（输出到 `backend/frontend_build/`）
- 初始化数据库
- 运行 PyInstaller 打包

### 步骤 3：获取打包产物

打包完成后，在 `dist/CloudStore/` 目录下：

```
dist/CloudStore/
├── CloudStore.exe           ← 主程序（双击运行）
├── python310.dll            ─┐
├── lib-dynload/              │ 内嵌的 Python 运行环境
├── site-packages/            │ （自动管理，无需关注）
└── ...                       ─┘
```

### 步骤 4：运行

双击 **`CloudStore.exe`**，程序会：
1. 在后台启动本地 Django 服务器（`http://127.0.0.1:52731`）
2. 自动打开系统默认浏览器
3. 显示文件存储页面，可上传、下载、管理文件

**注意：** 首次启动可能需要 10-30 秒解包内嵌资源。关闭窗口即停止服务器。

---

## 手动打包（如果一键脚本遇到问题）

```cmd
:: 进入 backend 目录
cd backend

:: 1. 安装 Python 依赖
pip install django djangorestframework django-cors-headers pyinstaller pillow

:: 2. 构建前端
cd ..\frontend
npm install
npm run build
cd ..\backend

:: 3. 数据库初始化
python manage.py migrate --run-syncdb

:: 4. 打包
pyinstaller cloudstore.spec --clean --noconfirm
```

打包完成后，EXE 在 `dist\CloudStore\` 目录。

---

## 用户数据存储位置

用户上传的文件和数据库保存在 **EXE 同级目录**下的 `data/` 中：

```
dist/CloudStore/
├── CloudStore.exe
├── data/                       ← 用户数据（备份整个目录即可）
│   ├── db.sqlite3              ── 文件信息数据库
│   ├── media/
│   │   ├── files/              ── 合并后的文件
│   │   └── chunks/             ── 上传时的临时分块
│   └── logs/                   ── 运行日志
└── [其它内嵌资源...]
```

**备份数据**：只需复制整个 `data/` 目录。
**重置系统**：删除 `data/` 目录，重新运行 CloudStore.exe。

---

## 功能特性

| 功能 | 说明 |
|------|------|
| 大文件上传 | 自动分块上传，支持超大文件 |
| 断点续传 | 上传中断后，下次进入可从断点继续 |
| 文件管理 | 查看已上传文件列表，复制下载链接，删除文件 |
| 无限制下载 | 对下载速度、次数、大小无限制 |
| 独立运行 | 不依赖任何服务器，完全离线 |

---

## 文件结构说明

```
项目根目录/
├── backend/                      ← 后端（Django）
│   ├── main_desktop.py          ← 桌面版入口程序
│   ├── cloudstore.spec          ← PyInstaller 打包配置
│   ├── build-windows.bat        ← 一键打包脚本
│   ├── cloudstore/              ← Django 项目配置
│   │   ├── settings.py          ← 配置（检测桌面/开发模式）
│   │   ├── urls.py              ← 路由（SPA fallback）
│   │   └── views.py             ← 首页/静态文件服务
│   ├── files/                   ← 文件管理应用
│   │   ├── models.py            ← UploadSession, FileRecord 模型
│   │   ├── views.py             ← 上传/下载 API
│   │   ├── serializers.py       ← API 数据序列化
│   │   ├── signals.py           ← 文件删除时的清理信号
│   │   └── management/commands/cleanup_chunks.py
│   ├── requirements.txt         ← Python 依赖
│   └── frontend_build/          ← 前端构建产物（打包时自动生成）
│
└── frontend/                     ← 前端（Vue 3 + Element Plus）
    ├── src/
    │   ├── views/               ← 页面组件（Home, Upload, Manage, Download, Help）
    │   ├── components/ChunkUploader.vue  ← 分块上传 + 断点续传组件
    │   └── api/files.js         ← API 客户端
    └── vite.config.js           ← 构建配置（输出到 backend/frontend_build）
```

---

## 常见问题

**Q: 杀毒软件误报？**
A: PyInstaller 打包的程序有时被误报。将 `CloudStore.exe` 所在目录加入白名单即可。

**Q: 端口 52731 被占用？**
A: 程序会自动尝试下一个端口（52732, 52733...）。如果多个实例同时运行，会使用不同端口。

**Q: 上传失败？**
A: 请检查 `data/logs/` 下的日志文件查看详细错误。常见原因：磁盘空间不足、文件过大。

**Q: 如何更新程序？**
A: 保留 `data/` 目录，替换 `CloudStore.exe` 即可。用户数据不会丢失。

**Q: 能上传多大的文件？**
A: 理论上无限制（受限于你的磁盘空间）。大文件会自动分块上传。

**Q: 上传中断后如何继续？**
A: 重新进入上传页面，选择同一个文件，系统会自动检测未完成的分块并继续。

---

## 技术原理

```
用户双击 CloudStore.exe
    ↓
PyInstaller Bootloader 解压 Python 环境和代码
    ↓
main_desktop.py 启动：
  ├─ 注入运行模式环境变量（CLOUDSTORE_MODE=desktop）
  ├─ Django settings 根据环境变量确定 data/ 目录
  ├─ 自动执行 migrate（首次运行创建数据库）
  ├─ 启动 Django 开发服务器监听 127.0.0.1:52731
  └─ 使用 webbrowser.open() 打开默认浏览器
    ↓
浏览器访问 http://127.0.0.1:52731/
    ↓
Django 返回前端 index.html
    ↓
用户交互通过 /api/ 调用 Django 后端
```
