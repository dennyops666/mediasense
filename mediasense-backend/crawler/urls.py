from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import CrawlerConfigViewSet, CrawlerTaskViewSet

app_name = "crawler"

router = DefaultRouter()
router.register('configs', CrawlerConfigViewSet, basename='crawler-config')
router.register('tasks', CrawlerTaskViewSet, basename='crawler-task')

urlpatterns = [
    path('configs/<int:pk>/enable/', CrawlerConfigViewSet.as_view({'post': 'enable'}), name='crawler-config-enable'),
    path('configs/<int:pk>/disable/', CrawlerConfigViewSet.as_view({'post': 'disable'}), name='crawler-config-disable'),
    path('configs/<int:pk>/test/', CrawlerConfigViewSet.as_view({'post': 'test'}), name='crawler-config-test'),
    path('tasks/<int:pk>/retry/', CrawlerTaskViewSet.as_view({'post': 'retry'}), name='crawler-task-retry'),
] + router.urls
