# 云文件存储系统 - GitHub Actions 云端打包指南

本指南详细说明如何将代码上传到 GitHub，利用 GitHub Actions 在云端自动构建 Windows EXE 程序，你直接下载即可使用。

---

## 目录

1. [前提条件](#前提条件)
2. [完整操作步骤](#完整操作步骤)
3. [文件结构](#文件结构)
4. [触发构建的方式](#触发构建的方式)
5. [下载 EXE](#下载-exe)
6. [后续更新](#后续更新)
7. [常见问题](#常见问题)

---

## 前提条件

- 一个 GitHub 账号（免费注册：https://github.com/）
- 代码已完整（在本地已完成开发）

---

## 完整操作步骤

### 第一步：在 GitHub 创建空仓库

1. 打开 https://github.com/new
2. 填写仓库信息：

| 字段 | 填写内容 |
|------|---------|
| **Repository name** | `cloudstore` |
| **Description** | `大文件永久免费存储网站` |
| **Private/Public** | 选择 **Private**（私有）或 **Public**（公开）均可 |
| **不要勾选** | 不要勾选 "Add a README file" |
| **不要勾选** | 不要勾选 ".gitignore" |
| **不要勾选** | 不要勾选 "Choose a license" |

3. 点击 **Create repository**
4. 页面会显示仓库地址，例如：
   ```
   https://github.com/你的用户名/cloudstore
   ```

---

### 第二步：本地初始化 Git 并推送代码

打开终端（Windows 上用 CMD 或 PowerShell），依次执行：

```cmd
:: 1. 进入项目目录（backend 的上一级）
cd 项目根目录

:: 2. 初始化 Git 仓库
git init

:: 3. 添加所有文件
git add .

:: 4. 提交代码
git commit -m "Initial commit: cloud file storage system with GitHub Actions build"

:: 5. 添加远程仓库（把 YOUR_USERNAME 改成你的 GitHub 用户名）
git remote add origin https://github.com/YOUR_USERNAME/cloudstore.git

:: 6. 推送到 GitHub
git branch -M main
git push -u origin main
```

> 如果提示 `git remote origin already exists`，说明之前初始化过，先执行：
> ```cmd
> git remote remove origin
> git remote add origin https://github.com/YOUR_USERNAME/cloudstore.git
> ```

---

### 第三步：查看 Actions 构建状态

1. 打开你的 GitHub 仓库页面：`https://github.com/YOUR_USERNAME/cloudstore`
2. 点击顶部的 **Actions** 标签
3. 你会看到 "Build Windows EXE" workflow 正在运行
4. 黄色圆点 = 运行中，绿色勾 = 成功，红色叉 = 失败

> **注意**：首次推送会自动触发构建，因为 `.github/workflows/build-exe.yml` 已配置 `on: push`

---

### 第四步：下载 EXE

构建完成后（约 5-10 分钟）：

1. 进入 **Actions** 页面
2. 点击左侧 "Build Windows EXE"
3. 点击中间的 **build** 任务（带有绿色勾的那行）
4. 滚动到页面底部，找到 **Artifacts** 区域
5. 点击 **CloudStore-Windows-EXE** 旁边的下载按钮

下载的是一个 zip 文件，解压后：
```
CloudStore/
└── CloudStore.exe    ← 双击运行
```

---

## 文件结构

```
cloudstore/                          ← GitHub 仓库根目录
├── .github/
│   └── workflows/
│       └── build-exe.yml           ← GitHub Actions 构建配置
├── backend/
│   ├── main_desktop.py            ← 桌面版入口
│   ├── cloudstore.spec            ← PyInstaller 配置
│   ├── build-windows.bat          ← 本地打包脚本（可选）
│   ├── cloudstore/
│   │   ├── settings.py            ← Django 配置
│   │   ├── urls.py                ← 路由（含 SPA fallback）
│   │   └── views.py               ← 首页/静态文件视图
│   ├── files/
│   │   ├── models.py              ← 数据模型
│   │   ├── views.py               ← API 视图
│   │   └── ...
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/                 ← 页面组件
│   │   ├── components/           ← 分块上传组件
│   │   └── api/                   ← API 调用
│   ├── package.json
│   └── vite.config.js             ← 构建配置
├── .gitignore
├── README.md
└── README_GITHUB_ACTIONS.md       ← 本文档
```

---

## 触发构建的方式

### 方式 1：推送代码自动构建（最常用）

每当你 `git push` 代码到 GitHub，云端自动开始构建。

```cmd
git add .
git commit -m "your changes"
git push
```

### 方式 2：手动触发（不改动代码也想重新打包）

1. 进入仓库 **Actions** 页面
2. 点击左侧 "Build Windows EXE"
3. 点击右侧 **"Run workflow"** 按钮
4. 选择分支，点击绿色 **Run workflow**
5. 无需改代码也能重新构建

### 方式 3：按需选择 Python 版本

在手动触发时，可以选择 Python 版本（3.10 / 3.11 / 3.12）。

---

## 后续更新

### 更新代码后重新打包

```cmd
git add .
git commit -m "修复了 xxx 问题"
git push
```

推送后自动构建，完成后重新下载 EXE 即可。

### 保留用户数据

用户数据保存在 EXE 同级的 `data/` 目录中。更新程序时：

1. 保留旧的 `data/` 文件夹
2. 用新的 EXE 替换旧的 EXE
3. 数据不会丢失

---

## 常见问题

### Q: 构建失败怎么办？

点击失败的 workflow run，查看日志找出错在哪一步。常见问题：

- **npm install 失败**：检查 `frontend/package.json` 是否正确
- **PyInstaller 报错**：检查 `cloudstore.spec` 文件路径
- **Python 版本不兼容**：在 workflow 里改 `python-version`

### Q: EXE 下载太慢？

GitHub Actions 产物下载有时较慢。可以使用 [GitHub Raw](https://raw.githubusercontent.com/) 或第三方下载工具。

### Q: 私有仓库能使用 Actions 吗？

可以。GitHub 免费账户每月有 2000 分钟的 Actions 时长，本项目构建一次约需 5-10 分钟，完全够用。

### Q: 能否构建 macOS 或 Linux 版本？

可以。GitHub 提供了 `macos-latest` 和 `ubuntu-latest` runner，只需修改 `runs-on` 字段即可交叉打包。但 Windows EXE 需要在 Windows 环境构建。

### Q: 如何删除 EXE 产物？

GitHub 默认保留 30 天。手动删除：进入仓库 **Settings** → **Actions** → **Artifacts**，可手动清除。

---

## 技术细节

### 构建流程（云端自动执行）

```
GitHub Actions (windows-latest)
    │
    ├─ actions/checkout@v4          拉取代码
    ├─ actions/setup-python@v5     安装 Python 3.11
    ├─ pip install                 安装 Django, DRF, PyInstaller...
    ├─ npm install                 安装前端依赖
    ├─ npm run build               构建 Vue 前端 → backend/frontend_build/
    ├─ python manage.py migrate    初始化数据库
    ├─ pyinstaller                打包成 EXE → dist/CloudStore/
    └─ actions/upload-artifact@v4 上传产物
```

### 产物保存时间

EXE 作为 GitHub Actions Artifact 保存 **30 天**。建议及时下载备份。

### 费用

GitHub Actions 免费额度：

| 账户类型 | 每月免费分钟数 |
|---------|--------------|
| 免费账户 | 2000 分钟/月 |
| Pro 账户 | 3000 分钟/月 |

本项目构建一次约消耗 **5-10 分钟**，完全在免费额度内。
