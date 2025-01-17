import os
from datetime import timedelta
import environ
from pathlib import Path
from .base import *

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()

# 测试环境标识
ENV = 'test'

# 安全配置
SECRET_KEY = 'django-insecure-test-key-do-not-use-in-production'

# 模板配置
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# 数据库配置
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'test_db.sqlite3',
    }
}

# Redis配置
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = None

# Elasticsearch配置
ELASTICSEARCH_HOSTS = ['localhost:9200']
ELASTICSEARCH_INDEX_PREFIX = 'test_'
ELASTICSEARCH_USERNAME = None
ELASTICSEARCH_PASSWORD = None

# 缓存配置
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'RETRY_ON_TIMEOUT': True,
            'MAX_CONNECTIONS': 1000,
            'CONNECTION_POOL_KWARGS': {'max_connections': 100}
        }
    }
}

# 测试邮件配置
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# 测试文件存储配置
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media_test')

# 测试日志配置
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# 测试安全配置
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# 测试中间件配置
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'ai_service.middleware.AsyncMiddleware',  # 将异步中间件放在最后
]

# JWT测试配置
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=5),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'SIGNING_KEY': 'test-secret-key',
    'AUTH_HEADER_TYPES': ('Bearer',),
    'BLACKLIST_AFTER_ROTATION': True,  # 启用token blacklist
    'ROTATE_REFRESH_TOKENS': True,
    'TOKEN_BLACKLIST_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenBlacklistSerializer',
}

# 测试性能配置
DEBUG = False
ALLOWED_HOSTS = ['*']

# REST framework配置
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# 测试任务配置
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True 

# 添加token blacklist应用
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes', 
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_celery_beat',
    'django_celery_results',
    'custom_auth.apps.CustomAuthConfig',
    'news.apps.NewsConfig',
    'news_search.apps.NewsSearchConfig',
    'monitoring.apps.MonitoringConfig',
    'ai_service.apps.AIServiceConfig',
    'crawler.apps.CrawlerConfig',
]

# 测试数据库配置
TEST = {
    'NAME': 'mediasense',  # 使用同一个数据库
    'SERIALIZE': False,  # 禁用序列化
    'MIRROR': None,  # 不使用镜像
    'DEPENDENCIES': [],  # 不依赖其他数据库
    'CREATE_DB': False  # 不创建新数据库
} 

# OpenAI配置
OPENAI_API_KEY = "test-api-key"
OPENAI_API_BASE = "https://api.openai-proxy.com/v1"
OPENAI_MODEL = "gpt-4"
OPENAI_TEMPERATURE = 0.2
OPENAI_MAX_TOKENS = 2000
OPENAI_TIMEOUT = 30  # 添加超时设置
OPENAI_RATE_LIMIT = 60  # 每分钟请求限制
OPENAI_RATE_LIMIT_WINDOW = 60  # 速率限制窗口(秒)
OPENAI_CACHE_TTL = 3600  # 缓存过期时间(秒)

# AI服务配置
AUTO_ANALYZE_NEWS = True
GENERATE_SUMMARY = True 

# 测试环境异步配置
ASYNC_VIEW_TIMEOUT = 10  # 测试环境设置较短的超时时间
CELERY_TASK_ALWAYS_EAGER = True  # 测试环境同步执行任务
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_TASK_TIME_LIMIT = 30  # 测试环境30秒超时
CELERY_TASK_SOFT_TIME_LIMIT = 25  # 测试环境25秒软超时

# 确保正确设置 AUTH_USER_MODEL
AUTH_USER_MODEL = 'custom_auth.User' 