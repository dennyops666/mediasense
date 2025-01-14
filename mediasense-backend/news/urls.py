from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NewsViewSet, CategoryViewSet

router = DefaultRouter()
router.register(r'news', NewsViewSet)
router.register(r'categories', CategoryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
