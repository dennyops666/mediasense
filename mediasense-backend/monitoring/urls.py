from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    SystemMetricsViewSet,
    AlertRuleViewSet,
    AlertHistoryViewSet,
    MonitoringVisualizationViewSet,
    ErrorLogViewSet,
    SystemStatusViewSet
)

app_name = "monitoring"

router = DefaultRouter()
router.register('system-metrics', SystemMetricsViewSet, basename='system-metrics')
router.register('alert-rules', AlertRuleViewSet, basename='alert-rules')
router.register('alert-history', AlertHistoryViewSet, basename='alert-history')
router.register('visualization', MonitoringVisualizationViewSet, basename='visualization')
router.register('error-logs', ErrorLogViewSet, basename='error-logs')
router.register('system-status', SystemStatusViewSet, basename='system-status')

urlpatterns = [
    path('system-status/overview/', SystemStatusViewSet.as_view({'get': 'overview'}), name='system-status-overview'),
    path('system-status/health/', SystemStatusViewSet.as_view({'get': 'health'}), name='system-status-health'),
    
    path('alert-rules/<int:pk>/enable/', AlertRuleViewSet.as_view({'post': 'enable'}), name='alert-rule-enable'),
    path('alert-rules/<int:pk>/disable/', AlertRuleViewSet.as_view({'post': 'disable'}), name='alert-rule-disable'),
    
    path('alert-history/<int:pk>/acknowledge/', AlertHistoryViewSet.as_view({'post': 'acknowledge'}), name='alert-history-acknowledge'),
    path('alert-history/<int:pk>/resolve/', AlertHistoryViewSet.as_view({'post': 'resolve'}), name='alert-history-resolve'),
    
    path('visualization/<int:pk>/data/', MonitoringVisualizationViewSet.as_view({'get': 'data'}), name='visualization-data'),
    
    path('error-logs/statistics/', ErrorLogViewSet.as_view({'get': 'statistics'}), name='error-log-statistics'),
] + router.urls
