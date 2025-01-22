from django.urls import path
from rest_framework.routers import DefaultRouter

from news.views import NewsViewSet, NewsCategoryViewSet

app_name = "news"

router = DefaultRouter()
router.register('news-articles', NewsViewSet, basename='news-article')
router.register('categories', NewsCategoryViewSet, basename='category')

urlpatterns = [
    path('news-articles/bulk-update/', NewsViewSet.as_view({'put': 'bulk_update'}), name='news-article-bulk-update'),
    path('news-articles/bulk-delete/', NewsViewSet.as_view({'post': 'bulk_delete'}), name='news-article-bulk-delete'),
] + router.urls
