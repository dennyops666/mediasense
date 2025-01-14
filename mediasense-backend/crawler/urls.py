from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CrawlerConfigViewSet, CrawlerTaskViewSet

# 创建路由器
router = DefaultRouter()
router.register(r"configs", CrawlerConfigViewSet)
router.register(r"tasks", CrawlerTaskViewSet)

# URL配置
urlpatterns = [
    path("", include(router.urls)),
]
