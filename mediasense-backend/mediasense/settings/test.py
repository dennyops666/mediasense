from environ import Env
import os
from datetime import timedelta

env = Env()
env.read_env(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

from .base import *

# 标记为测试环境
TESTING = True

# 允许所有主机名
ALLOWED_HOSTS = ['*']

# 允许在异步上下文中执行同步操作
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

# 设置用户模型
AUTH_USER_MODEL = 'custom_auth.User'  # 使用自定义用户模型

# 配置认证后端
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# 使用 pytest 测试运行器
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# REST框架测试设置
REST_FRAMEWORK = {
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'UNAUTHENTICATED_USER': None,
    'EXCEPTION_HANDLER': 'mediasense.utils.custom_exception_handler',
}

# 使用现有的MySQL数据库进行测试
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env('MYSQL_DATABASE', default='mediasense'),
        'USER': env('MYSQL_USER', default='mediasense'),
        'PASSWORD': env('MYSQL_PASSWORD'),
        'HOST': env('MYSQL_HOST', default='localhost'),
        'PORT': env('MYSQL_PORT', default='3306'),
        'CONN_MAX_AGE': 60,
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
        'TEST': {
            'NAME': env('MYSQL_DATABASE'),  # 使用相同的数据库
            'MIRROR': None,
            'CREATE_DB': False,  # 不创建新的测试数据库
            'DEPENDENCIES': [],
            'MIGRATE': False,  # 不进行迁移
            'SERIALIZE': False  # 不序列化数据
        },
    }
}

# 禁用密码哈希以加快测试速度
PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)

# 使用测试邮件后端
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# 禁用 Celery
CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

# JWT配置
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': env('DJANGO_SECRET_KEY', default='your-secret-key-for-testing'),
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# Elasticsearch配置
ELASTICSEARCH_HOSTS = ['http://localhost:9200']
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

# 启用日志记录
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'logs/test.log',
            'mode': 'w',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'ai_service': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# 异步测试配置
DJANGO_ALLOW_ASYNC_UNSAFE = True
ASYNC_TEST_TIMEOUT = 30  # 秒

# 其他测试相关设置
DEBUG = False
TEMPLATE_DEBUG = False

# 禁用异步中间件
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'mediasense.middleware.routing.RoutingMiddleware',
    'mediasense.middleware.rate_limit.RateLimitMiddleware',
]

# 数据库应用映射配置
DATABASE_APPS_MAPPING = {
    'news': 'default',
    'search': 'default',
    'auth': 'default',
    'ai': 'default',
}

# 服务注册配置
SERVICE_REGISTRY = {
    'news': {
        'hosts': ['http://localhost:8000'],
        'weight': 1,
    },
    'search': {
        'hosts': ['http://localhost:8000'],
        'weight': 1,
    },
    'auth': {
        'hosts': ['http://localhost:8000'],
        'weight': 1,
    },
    'ai': {
        'hosts': ['http://localhost:8000'],
        'weight': 1,
    },
}

# 网关配置
GATEWAY = {
    'rate_limit': {
        'enabled': True,
        'default_limit': 60,  # 每分钟请求次数
        'window': 60,  # 时间窗口（秒）
    },
    'load_balancing': {
        'algorithm': 'round_robin',  # 负载均衡算法
    },
}

# API网关配置
API_GATEWAY = {
    'enabled': True,
    'auth': {
        'required': True,
        'exempt_paths': [
            '/api/v1/auth/login/',
            '/api/v1/auth/register/',
        ],
    },
    'load_balancing': {
        'enabled': True,
        'algorithm': 'round_robin',
        'health_check': {
            'enabled': True,
            'interval': 30,  # 健康检查间隔（秒）
            'timeout': 5,    # 健康检查超时（秒）
        },
    },
    'rate_limiting': {
        'enabled': True,
        'default_limit': 60,  # 每分钟请求数
        'window': 60,         # 时间窗口（秒）
    },
}

# Redis配置
REDIS_HOST = env('REDIS_HOST', default='localhost')
REDIS_PORT = env('REDIS_PORT', default='6379')
REDIS_DB = env('REDIS_DB', default='0')
REDIS_PASSWORD = env('REDIS_PASSWORD', default=None)

# Redis缓存配置
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PASSWORD': REDIS_PASSWORD,
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'RETRY_ON_TIMEOUT': True,
            'MAX_CONNECTIONS': 1000,
            'CONNECTION_POOL_KWARGS': {'max_connections': 100},
        }
    }
}

# Redis会话配置
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Redis限流配置
RATE_LIMIT = {
    'ENABLED': True,
    'BACKEND': 'django_redis.cache.RedisCache',
    'DEFAULT_LIMIT': 60,  # 每分钟请求次数
    'WINDOW': 60,  # 时间窗口（秒）
}

# Redis队列配置
RQ_QUEUES = {
    'default': {
        'HOST': REDIS_HOST,
        'PORT': REDIS_PORT,
        'DB': REDIS_DB,
        'PASSWORD': REDIS_PASSWORD,
        'DEFAULT_TIMEOUT': 360,
    },
    'high': {
        'HOST': REDIS_HOST,
        'PORT': REDIS_PORT,
        'DB': REDIS_DB,
        'PASSWORD': REDIS_PASSWORD,
        'DEFAULT_TIMEOUT': 500,
    },
    'low': {
        'HOST': REDIS_HOST,
        'PORT': REDIS_PORT,
        'DB': REDIS_DB,
        'PASSWORD': REDIS_PASSWORD,
        'DEFAULT_TIMEOUT': 180,
    }
}

# 测试运行器配置
TEST_RUNNER = 'django.test.runner.DiscoverRunner'
TEST_NON_SERIALIZED_APPS = []