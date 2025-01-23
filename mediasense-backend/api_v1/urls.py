from django.urls import include, path

app_name = "api"

urlpatterns = [
    path("auth/", include(("custom_auth.urls", "auth"), namespace="auth")),
    path("news/", include(("news.urls", "news"), namespace="news")),
    path("monitoring/", include(("monitoring.urls", "monitoring"), namespace="monitoring")),
    path("crawler/", include(("crawler.urls", "crawler"), namespace="crawler")),
    path("search/", include(("news_search.urls", "news_search"), namespace="news_search")),
    path("ai/", include(("ai_service.urls", "ai_service"), namespace="ai_service")),
]
