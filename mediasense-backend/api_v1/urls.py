from django.urls import path, include

app_name = "api"

urlpatterns = [
    path("v1/auth/", include("custom_auth.urls", namespace="custom_auth")),
    path("v1/news/", include("news.urls", namespace="news")),
]
