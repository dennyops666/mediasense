from django.urls import path
from rest_framework.routers import DefaultRouter
from django.views.decorators.csrf import csrf_exempt
import rest_framework.routers
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

app_name = "monitoring"

class AsyncDefaultRouter(DefaultRouter):
    """异步路由器"""
    def get_urls(self):
        """获取URL模式"""
        urls = super().get_urls()
        processed_urls = []
        for pattern in urls:
            if hasattr(pattern, 'callback'):
                if hasattr(pattern.callback, 'cls'):
                    view_class = pattern.callback.cls
                    if hasattr(view_class, 'as_view'):
                        initkwargs = pattern.callback.initkwargs or {}
                        
                        if view_class == rest_framework.routers.APIRootView:
                            view_func = view_class.as_view(**initkwargs)
                        else:
                            if pattern.name and pattern.name.endswith('-list'):
                                actions = {'get': 'list', 'post': 'create'}
                            elif pattern.name and pattern.name.endswith('-detail'):
                                actions = {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}
                            else:
                                actions = getattr(pattern.callback, 'actions', {})
                            
                            view_func = view_class.as_view(actions=actions, **initkwargs)
                        
                        url_pattern = pattern.pattern.regex.pattern.lstrip('^').rstrip('$')
                        processed_urls.append(
                            path(url_pattern, csrf_exempt(view_func), name=pattern.name)
                        )
                    else:
                        processed_urls.append(pattern)
                else:
                    processed_urls.append(pattern)
            else:
                processed_urls.append(pattern)
        return processed_urls

router = AsyncDefaultRouter()
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
urlpatterns = [
    path('error-logs/statistics/', csrf_exempt(ErrorLogViewSet.as_view({'get': 'statistics'})), name='error-logs-statistics'),
    path('alert-rules/<int:pk>/enable/', csrf_exempt(AlertRuleViewSet.as_view({'post': 'enable'})), name='alert-rule-enable'),
    path('alert-rules/<int:pk>/disable/', csrf_exempt(AlertRuleViewSet.as_view({'post': 'disable'})), name='alert-rule-disable'),
    path('alert-history/<int:pk>/acknowledge/', csrf_exempt(AlertHistoryViewSet.as_view({'post': 'acknowledge'})), name='alert-history-acknowledge'),
    path('alert-history/<int:pk>/resolve/', csrf_exempt(AlertHistoryViewSet.as_view({'post': 'resolve'})), name='alert-history-resolve'),
] + router.urls
