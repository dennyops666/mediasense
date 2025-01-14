from django.urls import include, path
from rest_framework import routers

from .views import docs_view, schema_view

app_name = "api_v1"

# API路由注册
router = routers.DefaultRouter()

# API版本
API_VERSION = "v1"

urlpatterns = [
    # API文档
    path("schema/", schema_view.with_ui("swagger", cache_timeout=0), name="schema"),
    path("docs/", docs_view, name="docs"),
    # 认证相关API
    path(f"{API_VERSION}/auth/", include("custom_auth.urls")),
    # 新闻相关API
    path(f"{API_VERSION}/news/", include("news.urls")),
    # 新闻搜索API
    path(f"{API_VERSION}/search/", include("news_search.urls")),
    # 爬虫管理API
    path(f"{API_VERSION}/crawler/", include("crawler.urls")),
    # AI服务API
    path(f"{API_VERSION}/ai/", include("ai_service.urls")),
    # 系统监控API
    path(f"{API_VERSION}/monitoring/", include("monitoring.urls")),
    # 默认API路由
    path(f"{API_VERSION}/", include(router.urls)),
]
