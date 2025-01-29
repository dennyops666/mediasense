from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MonitorRuleViewSet, 
    MonitorAlertViewSet, 
    SystemMetricViewSet,
    HealthCheckView,
    HealthReportView,
    ErrorLogViewSet
)

router = DefaultRouter()
router.register(r'rules', MonitorRuleViewSet, basename='rules')
router.register(r'alerts', MonitorAlertViewSet, basename='alerts')
router.register(r'metrics', SystemMetricViewSet, basename='metrics')
router.register(r'error-logs', ErrorLogViewSet, basename='error-logs')

app_name = 'monitor'

urlpatterns = [
    path('', include(router.urls)),
    path('health-check/', HealthCheckView.as_view(), name='health-check'),
    path('health-report/', HealthReportView.as_view(), name='health-report'),
] 