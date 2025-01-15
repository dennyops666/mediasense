from .base import *
import environ

env = environ.Env()

# 测试环境标识
ENV = 'test'

# 数据库配置
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'mediasense',
        'USER': 'mediasense',
        'PASSWORD': '123456',
        'HOST': 'localhost',
        'PORT': '3306',
        'CONN_MAX_AGE': 600,  # 连接池配置，保持连接10分钟
        'OPTIONS': {
            'connect_timeout': 20,  # 连接超时时间20秒
            'charset': 'utf8mb4',  # 使用utf8mb4字符集
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",  # 设置严格模式
        },
        'TEST': {
            'NAME': 'mediasense',  # 使用同一个数据库
            'SERIALIZE': False,  # 禁用序列化
            'MIRROR': None,  # 不使用镜像
            'DEPENDENCIES': [],  # 不依赖其他数据库
            'CREATE_DB': False,  # 不创建新数据库
        }
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
    'rest_framework_simplejwt.token_blacklist',  # 添加token blacklist应用
    'custom_auth',
    'news',
    'news_search',
    'monitoring',
    'ai_service',
    'crawler',
] 

# 测试数据库配置
TEST = {
    'NAME': 'mediasense',  # 使用同一个数据库
    'SERIALIZE': False,  # 禁用序列化
    'MIRROR': None,  # 不使用镜像
    'DEPENDENCIES': [],  # 不依赖其他数据库
} 