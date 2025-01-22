from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import NewsSearchViewSet

app_name = 'news_search'

router = DefaultRouter()
router.register(r'search', NewsSearchViewSet, basename='news-search')

urlpatterns = [
    path('search/', NewsSearchViewSet.as_view({'get': 'search'}), name='news-search-search'),
    path('suggest/', NewsSearchViewSet.as_view({'get': 'suggest'}), name='news-search-suggest'),
] + router.urls
