from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NewsArticleViewSet, CategoryViewSet

app_name = 'news'

router = DefaultRouter()
router.register(r'news-articles', NewsArticleViewSet, basename='news-article')
router.register(r'categories', CategoryViewSet, basename='category')

urlpatterns = [
    path('', include(router.urls)),
]
