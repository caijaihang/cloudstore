import os
import sys
from pathlib import Path

# ============================================================
# 运行模式检测（桌面打包版 / 开发版）
# ============================================================
IS_DESKTOP = os.environ.get('CLOUDSTORE_MODE') == 'desktop'

if IS_DESKTOP:
    # 桌面打包模式：使用 main_desktop.py 注入的路径
    # 如果某个环境变量未设置，回退到 EXE 所在目录
    default_base = Path(getattr(sys, 'executable', __file__)).parent
    default_data = default_base / 'data'
    BASE_DIR = Path(os.environ.get('CLOUDSTORE_BASE_DIR', default_base))
    DATA_DIR = Path(os.environ.get('CLOUDSTORE_DATA_DIR', default_data))
    DB_PATH = Path(os.environ.get('CLOUDSTORE_DB_PATH', default_data / 'db.sqlite3'))
    MEDIA_ROOT = Path(os.environ.get('CLOUDSTORE_MEDIA_ROOT', default_data / 'media'))
    FRONTEND_DIR = Path(os.environ.get('CLOUDSTORE_STATIC_DIR', default_base / 'frontend_build'))
    LOG_DIR = Path(os.environ.get('CLOUDSTORE_LOG_DIR', default_data / 'logs'))
else:
    # 开发模式
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR
    DB_PATH = BASE_DIR / 'db.sqlite3'
    MEDIA_ROOT = BASE_DIR / 'media'
    FRONTEND_DIR = BASE_DIR / 'frontend_build'
    LOG_DIR = BASE_DIR / 'logs'

# 确保目录存在（开发模式也需要）
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
(MEDIA_ROOT / 'chunks').mkdir(parents=True, exist_ok=True)
(MEDIA_ROOT / 'files').mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

SECRET_KEY = 'django-insecure-change-in-production'

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'files.apps.FilesConfig',
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
        'NAME': str(DB_PATH),
    }
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# 静态文件服务（桌面版）：前端构建产物目录
STATIC_URL = 'static/'
STATICFILES_DIRS = [str(FRONTEND_DIR)]

MEDIA_URL = '/media/'
# MEDIA_ROOT 已在上方定义

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
            'filename': str(LOG_DIR / 'error.log'),
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
