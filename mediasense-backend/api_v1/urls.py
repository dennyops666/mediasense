from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt

app_name = "api"

urlpatterns = [
    path("auth/", include(("custom_auth.urls", "auth"), namespace="auth")),
    path("news/", include(("news.urls", "news"), namespace="news")),
    path("crawler/", include(("crawler.urls", "crawler"), namespace="crawler")),
    path("search/", include(("news_search.urls", "news_search"), namespace="news_search")),
    path("ai/", include("ai_service.urls")),
    path("monitoring/", include(("monitoring.urls", "monitoring"), namespace="monitoring")),
]
