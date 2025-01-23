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

# 使用内存数据库进行测试
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
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
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'mediasense.middleware.Custom404Middleware',
]

# 使用Redis缓存
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Redis配置
REDIS_URL = env('REDIS_URL')
REDIS_HOST = env('REDIS_HOST')
REDIS_PORT = env('REDIS_PORT')
REDIS_DB = 1  # 使用DB 1作为测试数据库

# 禁用密码哈希以加快测试速度
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# 使用测试邮件后端
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# 禁用 Celery
CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

# REST Framework测试配置
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'EXCEPTION_HANDLER': 'mediasense.utils.custom_exception_handler',
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser'
    ),
    'NON_FIELD_ERRORS_KEY': 'error',
    'DEFAULT_PAGINATION_CLASS': None,
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
ELASTICSEARCH_HOSTS = [env('ELASTICSEARCH_HOST', default='http://localhost:9200')]
ELASTICSEARCH_INDEX_PREFIX = 'test_'

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

# 媒体文件配置
MEDIA_ROOT = os.path.join(BASE_DIR, 'media_test')
MEDIA_URL = '/media/'

# 静态文件配置
STATIC_ROOT = os.path.join(BASE_DIR, 'static_test')
STATIC_URL = '/static/'

# 禁用日志记录
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
        'level': 'CRITICAL',
    },
}