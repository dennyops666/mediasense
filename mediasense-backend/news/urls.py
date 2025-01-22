from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import NewsViewSet, NewsCategoryViewSet

app_name = 'news'

router = DefaultRouter()
router.register('news-articles', NewsViewSet, basename='news-article')
router.register('categories', NewsCategoryViewSet, basename='category')

urlpatterns = router.urls
