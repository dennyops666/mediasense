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

# 配置路由器，使用自定义URL名称
router = DefaultRouter()
router.register(r"ai", AIServiceViewSet, basename="ai")
router.register(r"rules", AnalysisRuleViewSet, basename="rules")
router.register(r"batch-tasks", BatchAnalysisTaskViewSet, basename="batch-tasks")
router.register(r"schedules", AnalysisScheduleViewSet, basename="schedules")
router.register(r"executions", ScheduleExecutionViewSet, basename="executions")
router.register(r"notifications", NotificationViewSet, basename="notifications")
router.register(r"notification-settings", NotificationSubscriptionViewSet, basename="notification-settings")
router.register(r"visualizations", AnalysisVisualizationViewSet, basename="visualizations")

# 自定义URL模式
urlpatterns = [
    # AI分析相关
    path('ai/<int:pk>/analyze/', AIServiceViewSet.as_view({'post': 'analyze'}), name='ai-analyze'),
    path('ai/<int:pk>/analyze-with-rules/', AIServiceViewSet.as_view({'post': 'analyze_with_rules'}), name='ai-analyze-with-rules'),
    path('ai/<int:pk>/results/', AIServiceViewSet.as_view({'get': 'get_results'}), name='ai-results'),
    
    # 批量分析任务相关
    path('batch-tasks/<int:pk>/start/', BatchAnalysisTaskViewSet.as_view({'post': 'start_task'}), name='batch-tasks-start-task'),
    path('batch-tasks/<int:pk>/cancel/', BatchAnalysisTaskViewSet.as_view({'post': 'cancel_task'}), name='batch-tasks-cancel-task'),
    
    # 通知设置相关
    path('notification-settings/<int:pk>/toggle/', NotificationSubscriptionViewSet.as_view({'post': 'toggle_subscription'}), name='notification-settings-toggle-subscription'),
    
    # 包含路由器生成的URL
    path('', include(router.urls)),
]
