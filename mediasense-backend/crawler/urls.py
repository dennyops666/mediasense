from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import CrawlerConfigViewSet, CrawlerTaskViewSet

app_name = "crawler"

router = DefaultRouter()
router.register('configs', CrawlerConfigViewSet, basename='crawler-config')
router.register('tasks', CrawlerTaskViewSet, basename='crawler-task')

urlpatterns = [
    # 配置管理
    path('configs/<int:pk>/enable/', CrawlerConfigViewSet.as_view({'post': 'enable'}), name='crawler-config-enable'),
    path('configs/<int:pk>/disable/', CrawlerConfigViewSet.as_view({'post': 'disable'}), name='crawler-config-disable'),
    path('configs/<int:pk>/test/', CrawlerConfigViewSet.as_view({'post': 'test'}), name='crawler-config-test'),
    path('configs/bulk-create/', CrawlerConfigViewSet.as_view({'post': 'bulk_create'}), name='crawler-config-bulk-create'),
    path('configs/bulk-update/', CrawlerConfigViewSet.as_view({'put': 'bulk_update'}), name='crawler-config-bulk-update'),
    path('configs/bulk-delete/', CrawlerConfigViewSet.as_view({'post': 'bulk_delete'}), name='crawler-config-bulk-delete'),
    path('configs/stats/', CrawlerConfigViewSet.as_view({'get': 'stats'}), name='crawler-config-stats'),
    
    # 任务管理
    path('tasks/<int:pk>/retry/', CrawlerTaskViewSet.as_view({'post': 'retry'}), name='crawler-task-retry'),
    path('tasks/bulk-create/', CrawlerTaskViewSet.as_view({'post': 'bulk_create'}), name='crawler-task-bulk-create'),
    path('tasks/bulk-update/', CrawlerTaskViewSet.as_view({'put': 'bulk_update'}), name='crawler-task-bulk-update'),
    path('tasks/bulk-delete/', CrawlerTaskViewSet.as_view({'post': 'bulk_delete'}), name='crawler-task-bulk-delete'),
    path('tasks/stats/', CrawlerTaskViewSet.as_view({'get': 'stats'}), name='crawler-task-stats'),
] + router.urls
