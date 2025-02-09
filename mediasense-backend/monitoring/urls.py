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

# 创建路由器并设置尾部斜杠为False
router = DefaultRouter(trailing_slash=False)
router.include_format_suffixes = False

# 注册视图集
router.register('system-metrics', SystemMetricsViewSet, basename='system-metrics')
router.register('alert-rules', AlertRuleViewSet, basename='alert-rules')
router.register('alert-history', AlertHistoryViewSet, basename='alert-history')
router.register('visualizations', MonitoringVisualizationViewSet, basename='visualizations')
router.register('error-logs', ErrorLogViewSet, basename='error-logs')
router.register('dashboards', DashboardViewSet, basename='dashboards')
router.register('dashboard-widgets', DashboardWidgetViewSet, basename='dashboard-widgets')
router.register('alert-notification-config', AlertNotificationConfigViewSet, basename='alert-notification-config')

# 基础URL模式
urlpatterns = router.urls

# 添加自定义操作的URL
urlpatterns += [
    # System Status
    path('system-status', SystemStatusViewSet.as_view({'get': 'list'}), name='system-status'),
    path('system-status/health', SystemStatusViewSet.as_view({'get': 'health'}), name='system-status-health'),
    path('system-status/overview', SystemStatusViewSet.as_view({'get': 'overview'}), name='system-status-overview'),
    
    # Alert Rules
    path('alert-rules/<int:pk>/enable', AlertRuleViewSet.as_view({'post': 'enable'}), name='alert-rule-enable'),
    path('alert-rules/<int:pk>/disable', AlertRuleViewSet.as_view({'post': 'disable'}), name='alert-rule-disable'),
    
    # Alert History
    path('alert-history/<int:pk>/acknowledge', AlertHistoryViewSet.as_view({'post': 'acknowledge'}), name='alert-history-acknowledge'),
    path('alert-history/<int:pk>/resolve', AlertHistoryViewSet.as_view({'post': 'resolve'}), name='alert-history-resolve'),

    # System Metrics
    path('system-metrics/performance_stats', SystemMetricsViewSet.as_view({'get': 'performance_stats'}), name='system-metrics-performance-stats'),
]
