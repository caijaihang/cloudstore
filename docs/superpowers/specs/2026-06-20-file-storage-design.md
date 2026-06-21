# 大文件永久免费存储网站 - 设计规格

**日期**: 2026-06-20
**项目类型**: 全栈Web应用（前后端分离）
**状态**: 已批准（第四版修订）

---

## 1. 技术栈

### 后端
- **框架**: Django 5 + Django REST Framework
- **语言**: Python 3.10+
- **存储**: 本地文件系统（开发阶段），预留云存储接口（阿里云OSS/腾讯云COS）
- **CORS**: django-cors-headers
- **日志**: Django logging（DEBUG/ERROR级别，ERROR邮件告警）

### 前端
- **框架**: Vue 3 (Composition API)
- **UI库**: Element Plus
- **构建工具**: Vite
- **路由**: Vue Router 4

### 项目结构
```
/workspace/
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── cloudstore/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── files/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── signals.py              # 文件删除信号
│   │   └── management/
│   │       └── commands/
│   │           └── cleanup_chunks.py
│   └── media/
│       ├── chunks/
│       └── files/
│
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── main.js
        ├── App.vue
        ├── router/index.js
        ├── views/
        ├── components/
        └── api/
```

---

## 2. 数据模型

### UploadSession（上传会话）
| 字段 | 类型 | 说明 |
|------|------|------|
| upload_id | UUID | 主键 |
| filename | String | 原始文件名 |
| total_chunks | Integer | 前端计算的总块数 |
| file_size | BigInteger | 文件总大小 |
| content_type | String | MIME类型 |
| chunk_size | Integer | 后端计算的分块大小（字节），持久化存储 |
| is_completed | Boolean | 是否已完成合并 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 最后更新时间 |

**file_size上限**: 100GB（可配置）

### ChunkUpload（分块记录）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigAuto | 主键 |
| upload | ForeignKey | 外键→UploadSession（on_delete=CASCADE） |
| chunk_index | Integer | 块序号（从0开始） |
| chunk_path | String | 分块存储路径 |
| status | String | pending/completed |
| created_at | DateTime | 创建时间 |

**唯一约束**: (upload_id, chunk_index) 组合唯一。

**物理文件清理**: post_delete信号删除物理文件。

### FileRecord（文件记录）
| 字段 | 类型 | 说明 |
|------|------|------|
| file_id | String(12) | 主键，短UUID |
| filename | String | 原始文件名 |
| file_size | BigInteger | 文件大小 |
| content_type | String | MIME类型 |
| file_path | String | 相对存储路径 |
| download_count | Integer | 下载次数（默认0） |
| created_at | DateTime | 创建时间 |
| upload_session | ForeignKey | 可选外键→UploadSession（on_delete=SET_NULL） |

**物理文件清理**: post_delete信号删除合并后的文件。

---

## 3. API 设计

### 上传接口

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|------|------|------|--------|------|
| POST | `/api/upload/init/` | 初始化上传 | `{filename, total_chunks, file_size, content_type}` | `{upload_id, chunk_size}` |
| POST | `/api/upload/chunk/` | 上传单个分块 | `FormData: upload_id, chunk_index, chunk` | `{status: "ok"}` |
| POST | `/api/upload/complete/` | 合并分块 | `{upload_id}` | `{file_id, filename, file_size}` |
| GET | `/api/upload/status/{upload_id}/` | 查询断点状态 | - | `{uploaded_chunks, completed, expired, chunk_size}` |

#### init 流程
1. 校验file_size ≤ 100GB
2. 后端根据file_size计算chunk_size并存储到UploadSession
3. 后端校验total_chunks是否与计算值一致（`ceil(file_size / chunk_size)`）
4. 返回 `{upload_id, chunk_size}`

#### chunk上传校验
- 校验chunk大小是否 ≤ chunk_size（最后一块除外）
- 记录分块到数据库，路径: `media/chunks/{upload_id前两位}/{upload_id}/{chunk_index}.chunk`

#### status 响应
```json
{
  "uploaded_chunks": [0, 1, 2],
  "completed": false,
  "expired": false,
  "chunk_size": 10485760
}
```
- `uploaded_chunks`: 仅返回物理文件实际存在的块索引
- `expired`: created_at + 7天

### 文件接口

| 方法 | 路径 | 说明 | 参数 | 响应 |
|------|------|------|------|------|
| GET | `/api/files/` | 获取文件列表 | `?page=1&page_size=20` | 分页（按created_at降序） |
| GET | `/api/files/{file_id}/` | 获取文件详情 | - | 文件信息 |
| DELETE | `/api/files/{file_id}/` | 删除文件 | - | `{status: "deleted"}` |

### 下载接口

| 方法 | 路径 | 说明 | 响应 |
|------|------|------|------|
| GET | `/api/download/{file_id}/` | 下载文件 | 文件流 |

**下载时**: `FileRecord.objects.filter(file_id=file_id).update(download_count=F('download_count') + 1)`

---

## 4. chunk_size 协商机制

### 规则
1. 前端init时传filename, total_chunks, file_size, content_type
2. 后端计算chunk_size并持久化到UploadSession.chunk_size
3. 后端验证: `total_chunks == ceil(file_size / chunk_size)`
4. 前端必须以返回的chunk_size为准进行分块

### 计算规则
| file_size | chunk_size |
|-----------|------------|
| < 100MB | 5MB |
| 100MB ~ 1GB | 10MB |
| > 1GB | 20MB |

### 校验
- chunk_size范围: 1MB ~ 100MB
- file_size上限: 100GB（可配置）

---

## 5. 目录分片策略

### 分块存储
```
media/chunks/{upload_id前两位}/{upload_id}/
├── 0.chunk
├── 1.chunk
└── ...
```

### 最终文件存储
```
media/files/{file_id前两位}/{file_id}
```

---

## 6. 合并操作原子性保证

### 流程
```
1. 校验所有分块物理文件存在
2. 创建临时文件 dest_path.tmp
3. 流式合并到临时文件（8MB缓冲）
4. os.rename(dest_path.tmp, dest_path) 原子替换
5. 数据库事务内：
   - 创建FileRecord
   - 标记session.is_completed=True
6. 事务提交后，删除分块文件和记录（通过CASCADE+信号）
```

### 异常处理
- 若临时文件写入失败，删除临时文件，事务回滚
- 若事务提交失败（数据库错误），删除临时文件和已写入的部分数据
- 信号中捕获FileNotFoundError，避免文件不存在时删除失败

---

## 7. 并发安全

### 合并操作
```python
with transaction.atomic():
    session = UploadSession.objects.select_for_update().get(upload_id=upload_id)
    if session.is_completed:
        file_record = FileRecord.objects.get(upload_session=session)
        return {'file_id': file_record.file_id}
    
    # 1. 校验所有分块存在（事务外已完成）
    # 2. 合并到临时文件
    # 3. 原子重命名
    # 4. 创建FileRecord
    # 5. 标记is_completed=True
```

### 乐观锁策略
- 前端轮询status时使用短超时
- 合并完成后is_completed=True，其他请求直接返回

---

## 8. 物理文件清理机制

### signals.py
```python
@receiver(post_delete, sender=ChunkUpload)
def delete_chunk_file(sender, instance, **kwargs):
    try:
        if instance.chunk_path and os.path.exists(instance.chunk_path):
            os.remove(instance.chunk_path)
    except FileNotFoundError:
        pass  # 文件已被删除，忽略

@receiver(post_delete, sender=FileRecord)
def delete_file(sender, instance, **kwargs):
    try:
        full_path = os.path.join(settings.MEDIA_ROOT, instance.file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
    except FileNotFoundError:
        pass
```

### 清理命令
```python
expired_sessions = UploadSession.objects.filter(
    is_completed=False,
    created_at__lt=now() - timedelta(days=7)
)
for session in expired_sessions:
    session.delete()  # CASCADE + 信号清理
```

---

## 9. 异常处理

| 场景 | HTTP状态码 | 响应 |
|------|-----------|------|
| 磁盘空间不足 | 500 | `{"error": "Insufficient storage"}` |
| file_size超限 | 400 | `{"error": "File size exceeds limit"}` |
| upload_id不存在/过期 | 404 | `{"error": "Upload session not found or expired"}` |
| 分块缺失 | 400 | `{"error": "Chunk N missing"}` |
| 分块大小超限 | 400 | `{"error": "Chunk size exceeds limit"}` |
| 文件不存在 | 404 | `{"error": "File not found"}` |
| 并发合并冲突 | 409 | `{"error": "Upload already being processed"}` |
| total_chunks不一致 | 400 | `{"error": "Chunk count mismatch"}` |

---

## 10. CORS 配置

```python
# settings.py
CORS_ALLOW_ALL_ORIGINS = True  # 开发环境
# 生产环境应配置具体域名
CORS_ALLOWED_ORIGINS = ['http://localhost:5173', 'http://127.0.0.1:5173']
```

---

## 11. 日志配置

```python
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': 'logs/error.log',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'files': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
        },
        'django': {
            'handlers': ['file'],
            'level': 'WARNING',
        },
    },
}
```

---

## 12. 前端 localStorage 结构

```javascript
{
  "upload_sessions": [
    {
      "upload_id": "abc123",
      "filename": "test.zip",
      "chunk_size": 5242880,
      "total_chunks": 100,
      "uploaded_chunks": [0, 1, 2]
    }
  ],
  "file_records": [
    {
      "file_id": "xyz789",
      "filename": "test.zip",
      "file_size": 524288000,
      "created_at": "2026-06-20T10:00:00Z"
    }
  ]
}
```

---

## 13. 前端页面

| 页面 | 功能 |
|------|------|
| Home | 上传入口、文件管理入口、使用说明 |
| Upload | 拖拽/点击上传、实时进度、暂停/继续 |
| Manage | 分页文件列表、复制链接、删除文件 |
| Download | file_id下载、显示文件名大小 |
| Help | 功能介绍、断点续传说明 |

---

## 14. 响应式设计

- CSS3媒体查询 + Flexbox/Grid
- 适配电脑、平板、手机
- Element Plus响应式组件
