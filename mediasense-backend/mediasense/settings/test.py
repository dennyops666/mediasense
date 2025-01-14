from .base import *
import environ

env = environ.Env()

# 测试环境标识
ENV = 'test'

# 数据库配置
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'test_db.sqlite3'),
    }
}

# 测试缓存配置
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# 测试Elasticsearch配置
ELASTICSEARCH_DSL = {
    'default': {
        'hosts': 'localhost:9200'
    },
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