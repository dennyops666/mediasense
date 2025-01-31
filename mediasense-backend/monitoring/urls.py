from django.urls import path
from rest_framework.routers import DefaultRouter
from django.views.decorators.csrf import csrf_exempt
from asgiref.sync import sync_to_async
from django.views.decorators.http import require_http_methods
from .views import (
    SystemMetricsViewSet,
    AlertRuleViewSet,
    AlertHistoryViewSet,
    MonitoringVisualizationViewSet,
    ErrorLogViewSet,
    DashboardViewSet,
    DashboardWidgetViewSet,
    AlertNotificationConfigViewSet,
    SystemStatusViewSet
)
import asyncio
from asgiref.sync import sync_to_async
from django.utils.decorators import classonlymethod

app_name = "monitoring"

router = DefaultRouter()
router.register('system-metrics', SystemMetricsViewSet, basename='system-metrics')
router.register('alert-rules', AlertRuleViewSet, basename='alert-rules')
router.register('alert-history', AlertHistoryViewSet, basename='alert-history')
router.register('visualizations', MonitoringVisualizationViewSet, basename='visualizations')
router.register('error-logs', ErrorLogViewSet, basename='error-logs')
router.register('dashboards', DashboardViewSet, basename='dashboards')
router.register('dashboard-widgets', DashboardWidgetViewSet, basename='dashboard-widgets')
router.register('alert-notification-config', AlertNotificationConfigViewSet, basename='alert-notification-config')
router.register('system-status', SystemStatusViewSet, basename='system-status')

# 添加自定义操作的URL
urlpatterns = router.urls + [
    path('alert-rules/<int:pk>/enable/', AlertRuleViewSet.as_view({'post': 'enable'}), name='alert-rule-enable'),
    path('alert-rules/<int:pk>/disable/', AlertRuleViewSet.as_view({'post': 'disable'}), name='alert-rule-disable'),
    path('alert-history/<int:pk>/acknowledge/', AlertHistoryViewSet.as_view({'post': 'acknowledge'}), name='alert-history-acknowledge'),
    path('alert-history/<int:pk>/resolve/', AlertHistoryViewSet.as_view({'post': 'resolve'}), name='alert-history-resolve'),
]
