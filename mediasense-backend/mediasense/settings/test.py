from environ import Env
import os

env = Env()
env.read_env(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

from .base import *

# 允许在异步上下文中执行同步操作
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

# 设置用户模型
AUTH_USER_MODEL = 'custom_auth.User'  # 使用自定义用户模型

# 配置认证后端
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# 使用 pytest 测试运行器
TEST_RUNNER = 'mediasense.test_runner.PytestTestRunner'

# 使用现有的 MySQL 数据库
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env('MYSQL_DATABASE'),
        'USER': env('MYSQL_USER'),
        'PASSWORD': env('MYSQL_PASSWORD'),
        'HOST': env('MYSQL_HOST'),
        'PORT': env('MYSQL_PORT'),
        'CONN_MAX_AGE': 600,  # 连接池配置，保持连接10分钟
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'isolation_level': 'read committed',
            'connect_timeout': 20,  # 连接超时时间20秒
        },
        'ATOMIC_REQUESTS': False,  # 禁用自动事务
        'AUTOCOMMIT': True,  # 启用自动提交
        'CONN_MAX_AGE': 600,  # 连接池配置
        'TEST': {
            'NAME': env('MYSQL_DATABASE'),
            'MIRROR': None,
            'CREATE_DB': False,
            'DEPENDENCIES': [],
        }
    }
}

# 配置数据库并发设置
DATABASE_ROUTERS = []

# 禁用不必要的应用
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'monitoring',
    'custom_auth',
    'news',
    'news_search',
    'crawler',
    'ai_service',
]

# 使用异步中间件
MIDDLEWARE = [
    'monitoring.middleware.AsyncMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# 使用Redis缓存
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'db': 1,
            'socket_connect_timeout': 5,
            'socket_timeout': 5,
            'retry_on_timeout': True,
            'max_connections': 100,
        },
        'KEY_PREFIX': 'test',
        'TIMEOUT': 300,
    }
}

# Redis配置
REDIS_URL = env('REDIS_URL')
REDIS_HOST = env('REDIS_HOST')
REDIS_PORT = env('REDIS_PORT')
REDIS_DB = 1  # 使用DB 1作为测试数据库

# 禁用密码哈希器以加快测试速度
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# 禁用日志记录
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['null'],
            'level': 'CRITICAL',
        },
    },
}

# 使用控制台邮件后端
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# 禁用 Celery
CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

# REST Framework 配置
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
        'rest_framework.renderers.MultiPartRenderer',
    ],
    'UNAUTHENTICATED_USER': None,
    'UNAUTHENTICATED_TOKEN': None,
}

# JWT 配置
SIMPLE_JWT = {
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# Elasticsearch配置
ELASTICSEARCH_HOSTS = ['http://localhost:9200']
ELASTICSEARCH_INDEX_NAMES = {
    'news_search.documents.NewsArticleDocument': 'test_news_articles'
}
ELASTICSEARCH_DSL = {
    'default': {
        'hosts': ELASTICSEARCH_HOSTS
    },
}

# OpenAI配置
OPENAI_API_KEY = env('OPENAI_API_KEY')  # 从环境变量获取API密钥
OPENAI_API_BASE = env('OPENAI_API_BASE')  # OpenAI API代理地址
OPENAI_MODEL = env('OPENAI_MODEL')  # 使用的模型
OPENAI_MAX_TOKENS = int(env('OPENAI_MAX_TOKENS'))  # 最大token数
OPENAI_TEMPERATURE = float(env('OPENAI_TEMPERATURE'))  # 温度参数
OPENAI_TIMEOUT = 30  # API请求超时时间（秒）
OPENAI_RATE_LIMIT = 60  # 每分钟最大请求次数
OPENAI_RATE_LIMIT_WINDOW = 60  # 速率限制窗口（秒）
OPENAI_CACHE_TTL = 3600  # 缓存过期时间（秒）