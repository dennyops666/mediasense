from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AIServiceViewSet,
    AnalysisRuleViewSet,
    AnalysisScheduleViewSet,
    AnalysisVisualizationViewSet,
    BatchAnalysisTaskViewSet,
    NotificationSubscriptionViewSet,
    NotificationViewSet,
    ScheduleExecutionViewSet,
)

app_name = 'ai_service'

router = DefaultRouter()
router.register(r"ai", AIServiceViewSet, basename="ai")
router.register(r"rules", AnalysisRuleViewSet, basename="rules")
router.register(r"batch-tasks", BatchAnalysisTaskViewSet, basename="batch-tasks")
router.register(r"schedules", AnalysisScheduleViewSet, basename="schedules")
router.register(r"executions", ScheduleExecutionViewSet, basename="executions")
router.register(r"notifications", NotificationViewSet, basename="notifications")
router.register(r"notification-settings", NotificationSubscriptionViewSet, basename="notification-settings")
router.register(r"visualizations", AnalysisVisualizationViewSet, basename="visualizations")

custom_urls = [
    # AI分析相关
    path('ai/analyze/', AIServiceViewSet.as_view({'post': 'analyze_article'}), name='ai-analyze'),
    path('ai/<int:pk>/analyze-with-rules/', AIServiceViewSet.as_view({'post': 'analyze_with_rules'}), name='ai-analyze-with-rules'),
    path('ai/<int:pk>/results/', AIServiceViewSet.as_view({'get': 'get_analysis_result'}), name='ai-results'),
    
    # 规则相关
    path('rules/<int:pk>/', AnalysisRuleViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='rule-detail'),
    
    # 批量任务相关
    path('batch-tasks/<int:pk>/control/', BatchAnalysisTaskViewSet.as_view({'post': 'control'}), name='batch-tasks-control'),
    
    # 分析调度相关
    path('schedules/<int:pk>/control/', AnalysisScheduleViewSet.as_view({'post': 'control'}), name='schedules-control'),
    
    # 通知相关
    path('notifications/subscribe/', NotificationSubscriptionViewSet.as_view({'post': 'create'}), name='notification-subscribe'),
    path('notifications/unsubscribe/', NotificationSubscriptionViewSet.as_view({'post': 'destroy'}), name='notification-unsubscribe'),
]

urlpatterns = router.urls + custom_urls
