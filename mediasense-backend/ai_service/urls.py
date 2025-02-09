from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AIServiceViewSet,
    TextAnalysisViewSet,
    NewsClassificationViewSet,
    ContentGenerationViewSet
)

app_name = 'ai_service'

# 创建路由器并设置尾部斜杠为False
router = DefaultRouter(trailing_slash=False)
router.include_format_suffixes = False

# 注册视图集
router.register('services', AIServiceViewSet, basename='ai-services')
router.register('text-analysis', TextAnalysisViewSet, basename='text-analysis')
router.register('classification', NewsClassificationViewSet, basename='classification')
router.register('generation', ContentGenerationViewSet, basename='generation')

# URL模式
urlpatterns = router.urls
