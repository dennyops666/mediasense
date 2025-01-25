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

urlpatterns = router.urls
