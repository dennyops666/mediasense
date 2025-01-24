from django.urls import path
from rest_framework.routers import DefaultRouter

from news.views import NewsViewSet, NewsCategoryViewSet

app_name = "news"

router = DefaultRouter(trailing_slash=False)
router.include_format_suffixes = False
router.register('news-articles', NewsViewSet, basename='news-article')
router.register('categories', NewsCategoryViewSet, basename='category')

urlpatterns = [
    path('news-articles/bulk-create/', NewsViewSet.as_view({'post': 'bulk_create'}), name='news-article-bulk-create'),
    path('news-articles/bulk-update/', NewsViewSet.as_view({'put': 'bulk_update'}), name='news-article-bulk-update'),
    path('news-articles/bulk-delete/', NewsViewSet.as_view({'post': 'bulk_delete'}), name='news-article-bulk-delete'),
    
    path('categories/bulk-create/', NewsCategoryViewSet.as_view({'post': 'bulk_create'}), name='category-bulk-create'),
    path('categories/bulk-update/', NewsCategoryViewSet.as_view({'put': 'bulk_update'}), name='category-bulk-update'),
    path('categories/bulk-delete/', NewsCategoryViewSet.as_view({'post': 'bulk_delete'}), name='category-bulk-delete'),
] + router.urls
