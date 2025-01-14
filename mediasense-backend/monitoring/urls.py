from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AlertHistoryViewSet,
    AlertNotificationConfigViewSet,
    AlertRuleViewSet,
    DashboardViewSet,
    DashboardWidgetViewSet,
    ErrorLogViewSet,
    MonitoringVisualizationViewSet,
    PerformanceMonitorViewSet,
    SystemMetricsViewSet,
    SystemStatusViewSet,
)

router = DefaultRouter()
router.register(r"metrics", SystemMetricsViewSet, basename="metrics")
router.register(r"system-status", SystemStatusViewSet, basename="system-status")
router.register(r"performance", PerformanceMonitorViewSet, basename="performance")
router.register(r"error-logs", ErrorLogViewSet, basename="error-logs")
router.register(r"visualizations", MonitoringVisualizationViewSet, basename="visualizations")
router.register(r"alert-rules", AlertRuleViewSet, basename="alert-rules")
router.register(r"alert-history", AlertHistoryViewSet, basename="alert-history")
router.register(r"alert-notifications", AlertNotificationConfigViewSet, basename="alert-notifications")
router.register(r"dashboards", DashboardViewSet, basename="dashboards")
router.register(r"dashboard-widgets", DashboardWidgetViewSet, basename="dashboard-widgets")

urlpatterns = [
    path("", include(router.urls)),
]
