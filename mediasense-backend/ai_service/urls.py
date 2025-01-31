from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AIServiceViewSet,
    BatchAnalysisTaskViewSet,
    AnalysisScheduleViewSet,
    NotificationViewSet,
    NotificationSubscriptionViewSet,
    VisualizationViewSet,
)

app_name = 'ai_service'

class AsyncDefaultRouter(DefaultRouter):
    """异步路由器"""
    def get_routes(self, viewset):
        routes = super().get_routes(viewset)
        for route in routes:
            route.initkwargs.setdefault('detail', False)
        return routes

# 配置路由器，使用自定义URL名称
router = AsyncDefaultRouter()
router.register(r'services', AIServiceViewSet, basename='services')
router.register(r'batch-tasks', BatchAnalysisTaskViewSet, basename='batch-tasks')
router.register(r'schedules', AnalysisScheduleViewSet, basename='schedules')
router.register(r'notifications', NotificationViewSet, basename='notifications')
router.register(r'notification-settings', NotificationSubscriptionViewSet, basename='notification-settings')
router.register(r'visualizations', VisualizationViewSet, basename='visualizations')

# 自定义URL模式
urlpatterns = [
    path('', include(router.urls)),
]
