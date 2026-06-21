# 大文件永久免费存储网站 - 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个支持大文件分块上传、永久免费存储的个人文件存储网站

**Architecture:** 前后端分离架构，后端Django+DRF，前端Vue3+Element Plus，分块上传支持断点续传

**Tech Stack:** Django 5, Django REST Framework, Vue 3, Element Plus, Vite

---

## 文件结构

### 后端 (backend/)
```
backend/
├── manage.py
├── requirements.txt
├── cloudstore/
│   ├── __init__.py
│   ├── settings.py          # Django配置（含CORS、日志、MEDIA_ROOT）
│   ├── urls.py              # 根URL配置
│   └── wsgi.py
├── files/
│   ├── __init__.py
│   ├── models.py            # UploadSession, ChunkUpload, FileRecord
│   ├── views.py             # API视图
│   ├── serializers.py        # DRF序列化器
│   ├── urls.py              # files应用URL
│   ├── signals.py           # post_delete信号
│   └── management/
│       └── commands/
│           └── cleanup_chunks.py
└── media/
    ├── chunks/              # 分块存储
    └── files/               # 最终文件存储
```

### 前端 (frontend/)
```
frontend/
├── package.json
├── vite.config.js
├── index.html
└── src/
    ├── main.js
    ├── App.vue
    ├── router/index.js
    ├── api/files.js
    ├── views/
    │   ├── Home.vue
    │   ├── Upload.vue
    │   ├── Manage.vue
    │   ├── Download.vue
    │   └── Help.vue
    └── components/
        └── ChunkUploader.vue
```

---

## 实施任务

### Task 1: 后端项目初始化与配置

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/manage.py`
- Create: `backend/cloudstore/__init__.py`
- Create: `backend/cloudstore/settings.py`
- Create: `backend/cloudstore/urls.py`
- Create: `backend/cloudstore/wsgi.py`
- Create: `backend/files/__init__.py`

- [ ] **Step 1: 创建 requirements.txt**

```txt
Django>=5.0,<6.0
djangorestframework>=3.14,<4.0
django-cors-headers>=4.0,<5.0
Pillow>=10.0,<11.0
```

- [ ] **Step 2: 创建 manage.py**

```python
#!/usr/bin/env python
import os
import sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cloudstore.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
```

- [ ] **Step 3: 创建 cloudstore/settings.py**

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-change-in-production'

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'files',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'cloudstore.urls'

TEMPLATES = []

WSGI_APPLICATION = 'cloudstore.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# CORS
CORS_ALLOW_ALL_ORIGINS = True

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
    ],
}

# File upload settings
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB

# Logging
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'error.log',
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
    },
}

# Upload settings
MAX_FILE_SIZE = 100 * 1024 * 1024 * 1024  # 100GB
MIN_CHUNK_SIZE = 1 * 1024 * 1024  # 1MB
MAX_CHUNK_SIZE = 100 * 1024 * 1024  # 100MB
```

- [ ] **Step 4: 创建 cloudstore/urls.py**

```python
from django.urls import path, include

urlpatterns = [
    path('api/', include('files.urls')),
]
```

- [ ] **Step 5: 创建 cloudstore/wsgi.py**

```python
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cloudstore.settings')
application = get_wsgi_application()
```

- [ ] **Step 6: 创建 files/__init__.py**

```python
default_app_config = 'files.apps.FilesConfig'
```

- [ ] **Step 7: 创建 logs 目录**

Run: `mkdir -p /workspace/backend/logs`

- [ ] **Step 8: 验证Django项目**

Run: `cd /workspace/backend && python manage.py check`
Expected: System check identified no issues

- [ ] **Step 9: 提交**

```bash
cd /workspace && git add backend/requirements.txt backend/manage.py backend/cloudstore/ backend/files/__init__.py && git commit -m "feat: initialize Django backend project"
```

---

### Task 2: 数据模型定义

**Files:**
- Create: `backend/files/apps.py`
- Create: `backend/files/models.py`

- [ ] **Step 1: 创建 files/apps.py**

```python
from django.apps import AppConfig

class FilesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'files'

    def ready(self):
        import files.signals  # noqa
```

- [ ] **Step 2: 更新 settings.py 添加 apps.py 路径**

Modify: `backend/cloudstore/settings.py` - Add `'files.apps.FilesConfig'` to INSTALLED_APPS instead of `'files'`

- [ ] **Step 3: 创建 files/models.py**

```python
import uuid
import os
from django.db import models
from django.conf import settings


def get_chunk_upload_path(instance, filename):
    """分块存储路径: chunks/{upload_id前两位}/{upload_id}/{chunk_index}.chunk"""
    upload_id = str(instance.upload.upload_id)
    prefix = upload_id[:2]
    return f'chunks/{prefix}/{upload_id}/{instance.chunk_index}.chunk'


def get_file_upload_path(instance, filename):
    """最终文件存储路径: files/{file_id前两位}/{file_id}"""
    prefix = instance.file_id[:2]
    return f'files/{prefix}/{instance.file_id}'


def generate_short_uuid():
    return uuid.uuid4().hex[:12]


class UploadSession(models.Model):
    upload_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    filename = models.CharField(max_length=255)
    total_chunks = models.IntegerField()
    file_size = models.BigIntegerField()
    content_type = models.CharField(max_length=100)
    chunk_size = models.IntegerField()
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ChunkUpload(models.Model):
    upload = models.ForeignKey(
        UploadSession,
        on_delete=models.CASCADE,
        related_name='chunks'
    )
    chunk_index = models.IntegerField()
    chunk_path = models.CharField(max_length=500)
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('upload', 'chunk_index')
        ordering = ['chunk_index']


class FileRecord(models.Model):
    file_id = models.CharField(max_length=12, primary_key=True, default=generate_short_uuid)
    filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField()
    content_type = models.CharField(max_length=100)
    file_path = models.CharField(max_length=500)
    download_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    upload_session = models.ForeignKey(
        UploadSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
```

- [ ] **Step 4: 创建迁移文件**

Run: `cd /workspace/backend && python manage.py makemigrations files`
Expected: migrations/0001_initial.py created

- [ ] **Step 5: 执行迁移**

Run: `cd /workspace/backend && python manage.py migrate`
Expected: Operations to perform: Apply all migrations

- [ ] **Step 6: 提交**

```bash
cd /workspace && git add backend/files/models.py backend/files/apps.py backend/cloudstore/settings.py backend/files/migrations/ && git commit -m "feat: add data models (UploadSession, ChunkUpload, FileRecord)"
```

---

### Task 3: API视图实现

**Files:**
- Create: `backend/files/serializers.py`
- Create: `backend/files/views.py`
- Create: `backend/files/urls.py`

- [ ] **Step 1: 创建 files/serializers.py**

```python
import math
from rest_framework import serializers
from .models import UploadSession, FileRecord


class UploadInitSerializer(serializers.Serializer):
    filename = serializers.CharField(max_length=255)
    total_chunks = serializers.IntegerField(min_value=1)
    file_size = serializers.IntegerField(min_value=1)
    content_type = serializers.CharField(max_length=100)

    def validate_file_size(self, value):
        max_size = 100 * 1024 * 1024 * 1024  # 100GB
        if value > max_size:
            raise serializers.ValidationError("File size exceeds limit")
        return value

    def create(self, validated_data):
        file_size = validated_data['file_size']
        chunk_size = self.calculate_chunk_size(file_size)

        # 验证total_chunks
        expected_chunks = math.ceil(file_size / chunk_size)
        if validated_data['total_chunks'] != expected_chunks:
            raise serializers.ValidationError({
                'total_chunks': f'Chunk count mismatch. Expected {expected_chunks}, got {validated_data["total_chunks"]}'
            })

        session = UploadSession.objects.create(
            filename=validated_data['filename'],
            total_chunks=validated_data['total_chunks'],
            file_size=validated_data['file_size'],
            content_type=validated_data['content_type'],
            chunk_size=chunk_size
        )
        return session

    @staticmethod
    def calculate_chunk_size(file_size):
        if file_size < 100 * 1024 * 1024:  # < 100MB
            return 5 * 1024 * 1024  # 5MB
        elif file_size < 1024 * 1024 * 1024:  # < 1GB
            return 10 * 1024 * 1024  # 10MB
        else:
            return 20 * 1024 * 1024  # 20MB


class UploadStatusSerializer(serializers.Serializer):
    uploaded_chunks = serializers.ListField(child=serializers.IntegerField())
    completed = serializers.BooleanField()
    expired = serializers.BooleanField()
    chunk_size = serializers.IntegerField()


class FileRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileRecord
        fields = ['file_id', 'filename', 'file_size', 'content_type', 'download_count', 'created_at']
```

- [ ] **Step 2: 创建 files/views.py**

```python
import os
import math
import shutil
import uuid
from datetime import timedelta
from django.conf import settings
from django.db import transaction, models
from django.db.models import F
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import UploadSession, ChunkUpload, FileRecord
from .serializers import UploadInitSerializer, UploadStatusSerializer, FileRecordSerializer


CHUNK_SIZE_MIN = 1 * 1024 * 1024  # 1MB
CHUNK_SIZE_MAX = 100 * 1024 * 1024  # 100MB


def get_chunk_path(upload_id, chunk_index):
    prefix = str(upload_id)[:2]
    return f'chunks/{prefix}/{upload_id}/{chunk_index}.chunk'


def get_file_path(file_id):
    prefix = file_id[:2]
    return f'files/{prefix}/{file_id}'


class UploadInitView(APIView):
    def post(self, request):
        serializer = UploadInitSerializer(data=request.data)
        if serializer.is_valid():
            session = serializer.save()
            return Response({
                'upload_id': str(session.upload_id),
                'chunk_size': session.chunk_size
            }, status=status.HTTP_201_CREATED)
        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class UploadChunkView(APIView):
    def post(self, request):
        upload_id = request.data.get('upload_id')
        chunk_index = request.data.get('chunk_index')
        chunk_file = request.FILES.get('chunk')

        if not all([upload_id, chunk_index is not None, chunk_file]):
            return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            session = UploadSession.objects.get(upload_id=upload_id)
        except UploadSession.DoesNotExist:
            return Response({'error': 'Upload session not found'}, status=status.HTTP_404_NOT_FOUND)

        # 校验chunk大小（最后一块除外）
        if chunk_file.size > session.chunk_size:
            return Response({'error': 'Chunk size exceeds limit'}, status=status.HTTP_400_BAD_REQUEST)

        chunk_path = get_chunk_path(upload_id, chunk_index)
        full_path = os.path.join(settings.MEDIA_ROOT, chunk_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, 'wb') as dest:
            shutil.copyfileobj(chunk_file, dest, length=8 * 1024 * 1024)

        ChunkUpload.objects.update_or_create(
            upload=session,
            chunk_index=chunk_index,
            defaults={'chunk_path': chunk_path, 'status': 'completed'}
        )

        return Response({'status': 'ok'})


class UploadCompleteView(APIView):
    def post(self, request):
        upload_id = request.data.get('upload_id')
        if not upload_id:
            return Response({'error': 'Missing upload_id'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                session = UploadSession.objects.select_for_update().get(upload_id=upload_id)

                if session.is_completed:
                    file_record = FileRecord.objects.get(upload_session=session)
                    return Response({
                        'file_id': file_record.file_id,
                        'filename': file_record.filename,
                        'file_size': file_record.file_size
                    })

                # 校验所有分块存在
                for i in range(session.total_chunks):
                    chunk_path = get_chunk_path(upload_id, i)
                    full_path = os.path.join(settings.MEDIA_ROOT, chunk_path)
                    if not os.path.exists(full_path):
                        return Response(
                            {'error': f'Chunk {i} missing'},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                # 生成file_id并创建目标文件
                file_id = uuid.uuid4().hex[:12]
                file_path = get_file_path(file_id)
                dest_path = os.path.join(settings.MEDIA_ROOT, file_path)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)

                # 合并到临时文件
                temp_path = dest_path + '.tmp'
                with open(temp_path, 'wb') as dest:
                    for i in range(session.total_chunks):
                        chunk_path = get_chunk_path(upload_id, i)
                        chunk_full_path = os.path.join(settings.MEDIA_ROOT, chunk_path)
                        with open(chunk_full_path, 'rb') as src:
                            shutil.copyfileobj(src, dest, length=8 * 1024 * 1024)

                # 原子重命名
                os.replace(temp_path, dest_path)

                # 创建FileRecord
                file_record = FileRecord.objects.create(
                    file_id=file_id,
                    filename=session.filename,
                    file_size=session.file_size,
                    content_type=session.content_type,
                    file_path=file_path,
                    upload_session=session
                )

                # 标记完成
                session.is_completed = True
                session.save()

                return Response({
                    'file_id': file_record.file_id,
                    'filename': file_record.filename,
                    'file_size': file_record.file_size
                })

        except UploadSession.DoesNotExist:
            return Response({'error': 'Upload session not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UploadStatusView(APIView):
    def get(self, request, upload_id):
        try:
            session = UploadSession.objects.get(upload_id=upload_id)
        except UploadSession.DoesNotExist:
            return Response({'error': 'Upload session not found or expired'}, status=status.HTTP_404_NOT_FOUND)

        # 检查是否过期（7天）
        expired = (timezone.now() - session.created_at) > timedelta(days=7)

        # 获取已上传且物理文件存在的分块
        uploaded_chunks = []
        for chunk in session.chunks.filter(status='completed'):
            full_path = os.path.join(settings.MEDIA_ROOT, chunk.chunk_path)
            if os.path.exists(full_path):
                uploaded_chunks.append(chunk.chunk_index)

        return Response({
            'uploaded_chunks': sorted(uploaded_chunks),
            'completed': session.is_completed,
            'expired': expired,
            'chunk_size': session.chunk_size
        })


class FileListView(APIView):
    def get(self, request):
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        page_size = min(page_size, 100)

        files = FileRecord.objects.all().order_by('-created_at')
        total = files.count()
        files = files[(page - 1) * page_size:page * page_size]

        serializer = FileRecordSerializer(files, many=True)
        return Response({
            'total': total,
            'page': page,
            'page_size': page_size,
            'files': serializer.data
        })


class FileDetailView(APIView):
    def get(self, request, file_id):
        try:
            file_record = FileRecord.objects.get(file_id=file_id)
        except FileRecord.DoesNotExist:
            return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = FileRecordSerializer(file_record)
        data = serializer.data
        data['download_url'] = f'/api/download/{file_id}/'
        return Response(data)

    def delete(self, request, file_id):
        try:
            file_record = FileRecord.objects.get(file_id=file_id)
        except FileRecord.DoesNotExist:
            return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)

        file_record.delete()  # 触发signal删除物理文件
        return Response({'status': 'deleted'})


class FileDownloadView(APIView):
    def get(self, request, file_id):
        try:
            file_record = FileRecord.objects.get(file_id=file_id)
        except FileRecord.DoesNotExist:
            return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)

        # 增加下载计数
        FileRecord.objects.filter(file_id=file_id).update(download_count=F('download_count') + 1)

        full_path = os.path.join(settings.MEDIA_ROOT, file_record.file_path)
        if not os.path.exists(full_path):
            return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)

        from django.http import FileResponse
        response = FileResponse(open(full_path, 'rb'))
        response['Content-Disposition'] = f'attachment; filename="{file_record.filename}"'
        response['Content-Type'] = file_record.content_type
        return response
```

- [ ] **Step 3: 创建 files/urls.py**

```python
from django.urls import path
from .views import (
    UploadInitView,
    UploadChunkView,
    UploadCompleteView,
    UploadStatusView,
    FileListView,
    FileDetailView,
    FileDownloadView,
)

urlpatterns = [
    path('upload/init/', UploadInitView.as_view(), name='upload-init'),
    path('upload/chunk/', UploadChunkView.as_view(), name='upload-chunk'),
    path('upload/complete/', UploadCompleteView.as_view(), name='upload-complete'),
    path('upload/status/<uuid:upload_id>/', UploadStatusView.as_view(), name='upload-status'),
    path('files/', FileListView.as_view(), name='file-list'),
    path('files/<str:file_id>/', FileDetailView.as_view(), name='file-detail'),
    path('download/<str:file_id>/', FileDownloadView.as_view(), name='file-download'),
]
```

- [ ] **Step 4: 提交**

```bash
cd /workspace && git add backend/files/serializers.py backend/files/views.py backend/files/urls.py && git commit -m "feat: implement upload and file management APIs"
```

---

### Task 4: 信号与清理命令

**Files:**
- Create: `backend/files/signals.py`
- Create: `backend/files/management/__init__.py`
- Create: `backend/files/management/commands/__init__.py`
- Create: `backend/files/management/commands/cleanup_chunks.py`

- [ ] **Step 1: 创建 files/signals.py**

```python
import os
from django.dispatch import receiver
from django.db.models.signals import post_delete
from django.conf import settings
from .models import ChunkUpload, FileRecord


@receiver(post_delete, sender=ChunkUpload)
def delete_chunk_file(sender, instance, **kwargs):
    """删除ChunkUpload记录时自动删除物理分块文件"""
    try:
        if instance.chunk_path:
            full_path = os.path.join(settings.MEDIA_ROOT, instance.chunk_path)
            if os.path.exists(full_path):
                os.remove(full_path)
    except FileNotFoundError:
        pass  # 文件已被删除，忽略


@receiver(post_delete, sender=FileRecord)
def delete_file(sender, instance, **kwargs):
    """删除FileRecord时自动删除合并后的文件"""
    try:
        if instance.file_path:
            full_path = os.path.join(settings.MEDIA_ROOT, instance.file_path)
            if os.path.exists(full_path):
                os.remove(full_path)
    except FileNotFoundError:
        pass
```

- [ ] **Step 2: 创建 management 目录结构**

Run: `mkdir -p /workspace/backend/files/management/commands && touch /workspace/backend/files/management/__init__.py /workspace/backend/files/management/commands/__init__.py`

- [ ] **Step 3: 创建 cleanup_chunks.py**

```python
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from files.models import UploadSession


class Command(BaseCommand):
    help = 'Cleanup expired upload sessions and their chunk files'

    def handle(self, *args, **options):
        expired_sessions = UploadSession.objects.filter(
            is_completed=False,
            created_at__lt=timezone.now() - timedelta(days=7)
        )

        count = expired_sessions.count()
        for session in expired_sessions:
            session.delete()  # CASCADE删除ChunkUpload，触发信号删除物理文件
            self.stdout.write(f'Deleted expired session: {session.upload_id}')

        self.stdout.write(self.style.SUCCESS(f'Cleaned up {count} expired sessions'))
```

- [ ] **Step 4: 提交**

```bash
cd /workspace && git add backend/files/signals.py backend/files/management/ && git commit -m "feat: add file cleanup signals and management command"
```

---

### Task 5: 前端项目初始化

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/main.js`

- [ ] **Step 1: 创建 package.json**

```json
{
  "name": "cloudstore-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.2.0",
    "element-plus": "^2.5.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "vite": "^5.0.0"
  }
}
```

- [ ] **Step 2: 创建 vite.config.js**

```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

- [ ] **Step 3: 创建 index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>云文件存储</title>
</head>
<body>
  <div id="app"></div>
  <script type="module" src="/src/main.js"></script>
</body>
</html>
```

- [ ] **Step 4: 创建 src/main.js**

```javascript
import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(ElementPlus)
app.use(router)
app.mount('#app')
```

- [ ] **Step 5: 安装依赖**

Run: `cd /workspace/frontend && npm install`

- [ ] **Step 6: 提交**

```bash
cd /workspace && git add frontend/package.json frontend/vite.config.js frontend/index.html frontend/src/main.js && git commit -m "feat: initialize Vue frontend project"
```

---

### Task 6: 前端API与路由配置

**Files:**
- Create: `frontend/src/router/index.js`
- Create: `frontend/src/api/files.js`

- [ ] **Step 1: 创建 router/index.js**

```javascript
import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Upload from '../views/Upload.vue'
import Manage from '../views/Manage.vue'
import Download from '../views/Download.vue'
import Help from '../views/Help.vue'

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/upload', name: 'Upload', component: Upload },
  { path: '/manage', name: 'Manage', component: Manage },
  { path: '/download/:fileId', name: 'Download', component: Download },
  { path: '/help', name: 'Help', component: Help },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
```

- [ ] **Step 2: 创建 api/files.js**

```javascript
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 300000, // 5分钟，大文件上传需要更长超时
})

// 上传初始化
export function initUpload(data) {
  return api.post('/upload/init/', data)
}

// 上传分块
export function uploadChunk(uploadId, chunkIndex, chunk) {
  const formData = new FormData()
  formData.append('upload_id', uploadId)
  formData.append('chunk_index', chunkIndex)
  formData.append('chunk', chunk)
  return api.post('/upload/chunk/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 600000, // 10分钟超大块
  })
}

// 完成上传
export function completeUpload(uploadId) {
  return api.post('/upload/complete/', { upload_id: uploadId })
}

// 查询上传状态
export function getUploadStatus(uploadId) {
  return api.get(`/upload/status/${uploadId}/`)
}

// 获取文件列表
export function getFileList(page = 1, pageSize = 20) {
  return api.get('/files/', { params: { page, page_size: pageSize } })
}

// 获取文件详情
export function getFileDetail(fileId) {
  return api.get(`/files/${fileId}/`)
}

// 删除文件
export function deleteFile(fileId) {
  return api.delete(`/files/${fileId}/`)
}

// 获取下载URL
export function getDownloadUrl(fileId) {
  return `/api/download/${fileId}/`
}

export default api
```

- [ ] **Step 3: 提交**

```bash
cd /workspace && git add frontend/src/router/index.js frontend/src/api/files.js && git commit -m "feat: add frontend router and API"
```

---

### Task 7: 前端页面组件开发

**Files:**
- Create: `frontend/src/App.vue`
- Create: `frontend/src/views/Home.vue`
- Create: `frontend/src/views/Upload.vue`
- Create: `frontend/src/views/Manage.vue`
- Create: `frontend/src/views/Download.vue`
- Create: `frontend/src/views/Help.vue`

- [ ] **Step 1: 创建 App.vue**

```vue
<template>
  <div id="app">
    <el-container>
      <el-header>
        <h1>云文件存储</h1>
        <el-menu mode="horizontal" :router="true">
          <el-menu-item index="/">首页</el-menu-item>
          <el-menu-item index="/upload">上传</el-menu-item>
          <el-menu-item index="/manage">管理</el-menu-item>
          <el-menu-item index="/help">帮助</el-menu-item>
        </el-menu>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
}
.el-header {
  display: flex;
  align-items: center;
  gap: 20px;
}
.el-main {
  padding: 20px;
}
</style>
```

- [ ] **Step 2: 创建 Home.vue**

```vue
<template>
  <div class="home">
    <el-card class="upload-card">
      <template #header>
        <h2>上传文件</h2>
      </template>
      <el-button type="primary" size="large" @click="$router.push('/upload')">
        前往上传
      </el-button>
    </el-card>

    <el-card class="manage-card">
      <template #header>
        <h2>文件管理</h2>
      </template>
      <el-button size="large" @click="$router.push('/manage')">
        查看已上传文件
      </el-button>
    </el-card>

    <el-card>
      <template #header>
        <h2>使用说明</h2>
      </template>
      <ul>
        <li>支持任意格式文件上传</li>
        <li>支持超大文件（分块上传）</li>
        <li>支持断点续传</li>
        <li>下载无速度限制</li>
      </ul>
    </el-card>
  </div>
</template>

<script setup>
</script>

<style scoped>
.home {
  max-width: 800px;
  margin: 0 auto;
}
.upload-card, .manage-card {
  margin-bottom: 20px;
}
</style>
```

- [ ] **Step 3: 创建 Upload.vue**

```vue
<template>
  <div class="upload-page">
    <ChunkUploader />
  </div>
</template>

<script setup>
import ChunkUploader from '../components/ChunkUploader.vue'
</script>
```

- [ ] **Step 4: 创建 Manage.vue**

```vue
<template>
  <div class="manage-page">
    <h2>文件管理</h2>
    <el-table :data="files" v-loading="loading">
      <el-table-column prop="filename" label="文件名" />
      <el-table-column prop="file_size" label="大小">
        <template #default="{ row }">
          {{ formatSize(row.file_size) }}
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="上传时间">
        <template #default="{ row }">
          {{ new Date(row.created_at).toLocaleString() }}
        </template>
      </el-table-column>
      <el-table-column prop="download_count" label="下载次数" />
      <el-table-column label="操作">
        <template #default="{ row }">
          <el-button size="small" @click="copyLink(row.file_id)">复制链接</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row.file_id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-if="total > pageSize"
      layout="prev, pager, next"
      :total="total"
      :page-size="pageSize"
      :current-page="currentPage"
      @current-change="handlePageChange"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getFileList, deleteFile, getDownloadUrl } from '../api/files'

const files = ref([])
const loading = ref(false)
const total = ref(0)
const pageSize = 20
const currentPage = ref(1)

async function loadFiles() {
  loading.value = true
  try {
    const res = await getFileList(currentPage.value, pageSize)
    files.value = res.data.files
    total.value = res.data.total
  } catch (e) {
    ElMessage.error('加载文件列表失败')
  } finally {
    loading.value = false
  }
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / 1024 / 1024).toFixed(2) + ' MB'
  return (bytes / 1024 / 1024 / 1024).toFixed(2) + ' GB'
}

function copyLink(fileId) {
  const url = window.location.origin + getDownloadUrl(fileId)
  navigator.clipboard.writeText(url)
  ElMessage.success('链接已复制')
}

async function handleDelete(fileId) {
  try {
    await deleteFile(fileId)
    ElMessage.success('删除成功')
    loadFiles()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

function handlePageChange(page) {
  currentPage.value = page
  loadFiles()
}

onMounted(loadFiles)
</script>
```

- [ ] **Step 5: 创建 Download.vue**

```vue
<template>
  <div class="download-page">
    <el-card v-if="file">
      <h2>{{ file.filename }}</h2>
      <p>大小: {{ formatSize(file.file_size) }}</p>
      <p>下载次数: {{ file.download_count }}</p>
      <el-button type="primary" size="large" @click="downloadFile">
        下载文件
      </el-button>
    </el-card>
    <el-loading v-else />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getFileDetail, getDownloadUrl } from '../api/files'

const route = useRoute()
const file = ref(null)

async function loadFile() {
  try {
    const res = await getFileDetail(route.params.fileId)
    file.value = res.data
  } catch (e) {
    // 文件不存在
  }
}

function downloadFile() {
  window.location.href = getDownloadUrl(route.params.fileId)
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / 1024 / 1024).toFixed(2) + ' MB'
  return (bytes / 1024 / 1024 / 1024).toFixed(2) + ' GB'
}

onMounted(loadFile)
</script>
```

- [ ] **Step 6: 创建 Help.vue**

```vue
<template>
  <div class="help-page">
    <el-card>
      <template #header>
        <h2>功能特点</h2>
      </template>
      <ul>
        <li><strong>大文件支持</strong>：采用分块上传技术，支持超过2TB的超大文件</li>
        <li><strong>断点续传</strong>：上传中断可从断点继续，无需重新开始</li>
        <li><strong>永久免费</strong>：文件永久存储，下载无速度限制</li>
        <li><strong>全格式支持</strong>：支持任意文件格式上传</li>
      </ul>
    </el-card>

    <el-card>
      <template #header>
        <h2>断点续传说明</h2>
      </template>
      <p>如果您在上传大文件时网络中断，可以稍后重新进入上传页面继续上传。</p>
      <p>系统会自动检测未完成的上传任务，并从断点继续。</p>
      <el-alert type="warning" :closable="false">
        请勿清除浏览器缓存，否则将丢失未完成上传的记录
      </el-alert>
    </el-card>

    <el-card>
      <template #header>
        <h2>常见问题</h2>
      </template>
      <p><strong>Q: 支持多大的文件？</strong></p>
      <p>A: 单个文件最大支持100GB。</p>
      <p><strong>Q: 文件多久保存？</strong></p>
      <p>A: 文件永久保存，永久免费。</p>
      <p><strong>Q: 下载速度有限制吗？</strong></p>
      <p>A: 完全无限制。</p>
    </el-card>
  </div>
</template>

<script setup>
</script>

<style scoped>
.help-page {
  max-width: 800px;
  margin: 0 auto;
}
.help-page > .el-card {
  margin-bottom: 20px;
}
</style>
```

- [ ] **Step 7: 提交**

```bash
cd /workspace && git add frontend/src/App.vue frontend/src/views/ && git commit -m "feat: add frontend view components"
```

---

### Task 8: 分块上传组件

**Files:**
- Create: `frontend/src/components/ChunkUploader.vue`

- [ ] **Step 1: 创建 ChunkUploader.vue**

```vue
<template>
  <div class="chunk-uploader">
    <el-card>
      <template #header>
        <h2>上传文件</h2>
      </template>

      <el-upload
        ref="uploadRef"
        :auto-upload="false"
        :show-file-list="false"
        :on-change="handleFileChange"
        drag
      >
        <el-icon><upload-filled /></el-icon>
        <div>将文件拖拽到此处，或<em>点击选择</em></div>
      </el-upload>

      <div v-if="file" class="file-info">
        <p>文件名: {{ file.name }}</p>
        <p>大小: {{ formatSize(file.size) }}</p>
        <p v-if="chunkSize">分块大小: {{ formatSize(chunkSize) }}</p>
      </div>

      <div v-if="uploading" class="progress">
        <el-progress :percentage="progress" :status="progressStatus" />
        <p>上传速度: {{ formatSize(speed) }}/s | 剩余时间: {{ remainingTime }}</p>
        <el-button @click="togglePause">
          {{ paused ? '继续' : '暂停' }}
        </el-button>
      </div>

      <el-button
        v-if="file && !uploading"
        type="primary"
        size="large"
        @click="startUpload"
      >
        开始上传
      </el-button>

      <el-result
        v-if="uploaded"
        title="上传完成"
        :sub-title="`文件ID: ${fileId}`"
      >
        <template #extra>
          <el-button type="primary" @click="copyLink">复制下载链接</el-button>
          <el-button @click="reset">上传新文件</el-button>
        </template>
      </el-result>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { initUpload, uploadChunk, completeUpload, getUploadStatus, getDownloadUrl } from '../api/files'

const CHUNK_CONCURRENCY = 3

const uploadRef = ref(null)
const file = ref(null)
const chunkSize = ref(0)
const uploading = ref(false)
const paused = ref(false)
const progress = ref(0)
const speed = ref(0)
const startTime = ref(null)
const uploadedBytes = ref(0)
const uploaded = ref(false)
const fileId = ref(null)
const uploadId = ref(null)
const totalChunks = ref(0)
const uploadedChunks = ref([])

let uploadQueue = []
let activeUploads = 0
let lastLoaded = 0
let speedTimer = null

function formatSize(bytes) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / 1024 / 1024).toFixed(2) + ' MB'
  return (bytes / 1024 / 1024 / 1024).toFixed(2) + ' GB'
}

function calculateChunkSize(fileSize) {
  if (fileSize < 100 * 1024 * 1024) return 5 * 1024 * 1024
  if (fileSize < 1024 * 1024 * 1024) return 10 * 1024 * 1024
  return 20 * 1024 * 1024
}

async function handleFileChange(f) {
  file.value = f.raw
  chunkSize.value = calculateChunkSize(f.size)
  totalChunks.value = Math.ceil(f.size / chunkSize.value)
  uploadedChunks.value = []
}

async function startUpload() {
  if (!file.value) return

  try {
    const initRes = await initUpload({
      filename: file.value.name,
      total_chunks: totalChunks.value,
      file_size: file.value.size,
      content_type: file.value.type || 'application/octet-stream',
    })

    uploadId.value = initRes.data.upload_id
    chunkSize.value = initRes.data.chunk_size
    totalChunks.value = Math.ceil(file.value.size / chunkSize.value)

    saveToLocalStorage()

    uploading.value = true
    paused.value = false
    startTime.value = Date.now()
    lastLoaded = 0

    startSpeedTimer()
    await processUpload()
  } catch (e) {
    ElMessage.error('初始化上传失败')
  }
}

async function processUpload() {
  while (uploadedChunks.value.length < totalChunks.value && !paused.value) {
    if (activeUploads >= CHUNK_CONCURRENCY) {
      await waitForSlot()
      continue
    }

    const nextChunk = findNextChunk()
    if (nextChunk === null) break

    activeUploads++
    uploadChunk(nextChunk)
      .then(() => {
        uploadedChunks.value.push(nextChunk)
        uploadedBytes.value += getChunkSize(nextChunk)
        progress.value = Math.round((uploadedChunks.value.length / totalChunks.value) * 100)
        saveToLocalStorage()
      })
      .catch(e => {
        ElMessage.error(`分块 ${nextChunk} 上传失败`)
      })
      .finally(() => {
        activeUploads--
      })
  }

  if (uploadedChunks.value.length >= totalChunks.value && activeUploads === 0) {
    await finishUpload()
  }
}

function findNextChunk() {
  for (let i = 0; i < totalChunks.value; i++) {
    if (!uploadedChunks.value.includes(i)) {
      return i
    }
  }
  return null
}

function getChunkSize(chunkIndex) {
  if (chunkIndex === totalChunks.value - 1) {
    return file.value.size - chunkIndex * chunkSize.value
  }
  return chunkSize.value
}

function waitForSlot() {
  return new Promise(resolve => {
    const check = () => {
      if (activeUploads < CHUNK_CONCURRENCY || paused.value) {
        resolve()
      } else {
        setTimeout(check, 100)
      }
    }
    check()
  })
}

function togglePause() {
  paused.value = !paused.value
  if (!paused.value) {
    processUpload()
  }
}

function startSpeedTimer() {
  speedTimer = setInterval(() => {
    const now = Date.now()
    const elapsed = (now - startTime.value) / 1000
    speed.value = uploadedBytes.value / elapsed
  }, 1000)
}

function stopSpeedTimer() {
  if (speedTimer) {
    clearInterval(speedTimer)
    speedTimer = null
  }
}

const remainingTime = computed(() => {
  if (!speed.value) return '计算中...'
  const remaining = file.value.size - uploadedBytes.value
  const seconds = Math.round(remaining / speed.value)
  if (seconds < 60) return seconds + '秒'
  if (seconds < 3600) return Math.round(seconds / 60) + '分钟'
  return Math.round(seconds / 3600) + '小时'
})

const progressStatus = computed(() => {
  if (progress.value === 100) return 'success'
  return null
})

async function finishUpload() {
  try {
    const res = await completeUpload(uploadId.value)
    fileId.value = res.data.file_id
    uploaded.value = true
    uploading.value = false
    stopSpeedTimer()
    clearFromLocalStorage()
    ElMessage.success('上传完成')
  } catch (e) {
    ElMessage.error('合并失败')
  }
}

function copyLink() {
  const url = window.location.origin + getDownloadUrl(fileId.value)
  navigator.clipboard.writeText(url)
  ElMessage.success('链接已复制')
}

function reset() {
  file.value = null
  uploading.value = false
  uploaded.value = false
  fileId.value = null
  uploadId.value = null
  progress.value = 0
  speed.value = 0
  uploadedBytes.value = 0
  uploadedChunks.value = []
  totalChunks.value = 0
}

function saveToLocalStorage() {
  const sessions = JSON.parse(localStorage.getItem('upload_sessions') || '[]')
  const idx = sessions.findIndex(s => s.upload_id === uploadId.value)
  const session = {
    upload_id: uploadId.value,
    filename: file.value.name,
    chunk_size: chunkSize.value,
    total_chunks: totalChunks.value,
    uploaded_chunks: uploadedChunks.value,
  }
  if (idx >= 0) {
    sessions[idx] = session
  } else {
    sessions.push(session)
  }
  localStorage.setItem('upload_sessions', JSON.stringify(sessions))
}

function clearFromLocalStorage() {
  const sessions = JSON.parse(localStorage.getItem('upload_sessions') || '[]')
  const filtered = sessions.filter(s => s.upload_id !== uploadId.value)
  localStorage.setItem('upload_sessions', JSON.stringify(filtered))
}

onUnmounted(() => {
  stopSpeedTimer()
})
</script>

<style scoped>
.chunk-uploader {
  max-width: 600px;
  margin: 0 auto;
}
.file-info {
  margin: 20px 0;
}
.progress {
  margin: 20px 0;
}
</style>
```

- [ ] **Step 2: 提交**

```bash
cd /workspace && git add frontend/src/components/ChunkUploader.vue && git commit -m "feat: add chunk uploader component"
```

---

### Task 9: 联调测试

- [ ] **Step 1: 启动后端服务**

Run: `cd /workspace/backend && python manage.py runserver 0.0.0.0:8000`
Expected: Starting development server

- [ ] **Step 2: 启动前端服务**

Run: `cd /workspace/frontend && npm run dev`
Expected: Local: http://localhost:5173

- [ ] **Step 3: 测试上传小文件**

使用浏览器访问 http://localhost:5173，上传一个小文件（如 10MB），验证：
- 分块上传成功
- 进度条显示正确
- 上传完成后返回 file_id
- 文件列表显示正确

- [ ] **Step 4: 测试下载**

点击文件管理中的下载链接，验证文件能正确下载

- [ ] **Step 5: 测试删除**

在文件管理中删除文件，验证物理文件被删除

- [ ] **Step 6: 最终提交**

```bash
cd /workspace && git add -A && git commit -m "feat: complete file storage system with chunk upload support"
```

---

## 实施检查清单

- [ ] 后端 Django 项目可运行
- [ ] 数据库迁移成功
- [ ] API 接口可正常调用
- [ ] 前端可正常启动
- [ ] 文件上传功能正常
- [ ] 文件下载功能正常
- [ ] 文件删除功能正常
- [ ] 分页功能正常
- [ ] 断点续传逻辑正确

---

**Plan complete.** 文件已保存至 `docs/superpowers/plans/2026-06-20-file-storage-implementation-plan.md`
