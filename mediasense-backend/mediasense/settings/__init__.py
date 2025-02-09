import os
import logging

logger = logging.getLogger(__name__)

# 根据环境变量选择配置文件
environment = os.getenv("DJANGO_ENV", "development")
logger.debug("Loading settings for environment: %s", environment)

# 首先加载基础配置
from .base import *
logger.debug("Base settings loaded")

# 然后根据环境加载特定配置
if environment == "production":
    from .production import *
    logger.debug("Production settings loaded")
else:
    from .development import *
    logger.debug("Development settings loaded")

# 确保 Elasticsearch 配置存在
if not hasattr(globals(), 'ELASTICSEARCH_HOSTS'):
    logger.debug("Setting default ELASTICSEARCH_HOSTS")
    ELASTICSEARCH_HOSTS = ['http://localhost:9200']
if not hasattr(globals(), 'ELASTICSEARCH_INDEX_PREFIX'):
    ELASTICSEARCH_INDEX_PREFIX = ''  # 不使用前缀
if not hasattr(globals(), 'ELASTICSEARCH_USERNAME'):
    ELASTICSEARCH_USERNAME = None
if not hasattr(globals(), 'ELASTICSEARCH_PASSWORD'):
    ELASTICSEARCH_PASSWORD = None
if not hasattr(globals(), 'ELASTICSEARCH_TIMEOUT'):
    ELASTICSEARCH_TIMEOUT = 30
if not hasattr(globals(), 'ELASTICSEARCH_MAX_RETRIES'):
    ELASTICSEARCH_MAX_RETRIES = 3
if not hasattr(globals(), 'ELASTICSEARCH_RETRY_ON_TIMEOUT'):
    ELASTICSEARCH_RETRY_ON_TIMEOUT = True

logger.debug("Final ELASTICSEARCH_HOSTS: %s", ELASTICSEARCH_HOSTS)

# 搜索配置
if not hasattr(globals(), 'SEARCH_CACHE_TIMEOUT'):
    SEARCH_CACHE_TIMEOUT = 300  # 5分钟
if not hasattr(globals(), 'SEARCH_RESULT_PAGE_SIZE'):
    SEARCH_RESULT_PAGE_SIZE = 10
if not hasattr(globals(), 'SEARCH_MAX_SUGGESTIONS'):
    SEARCH_MAX_SUGGESTIONS = 10
if not hasattr(globals(), 'SEARCH_HOT_THRESHOLD'):
    SEARCH_HOT_THRESHOLD = 100  # 热门搜索阈值
if not hasattr(globals(), 'SEARCH_HISTORY_MAX_SIZE'):
    SEARCH_HISTORY_MAX_SIZE = 50  # 每个用户最多保存50条搜索历史
