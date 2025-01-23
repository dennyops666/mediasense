from django.urls import path, include

app_name = "api"

urlpatterns = [
    path("auth/", include("custom_auth.urls", namespace="custom_auth")),
    path("news/", include("news.urls", namespace="news")),
    path("monitoring/", include("monitoring.urls", namespace="monitoring")),
    path("crawler/", include("crawler.urls", namespace="crawler")),
]
