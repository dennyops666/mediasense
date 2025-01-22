from django.urls import path, include
from rest_framework.schemas import get_schema_view
from rest_framework.documentation import include_docs_urls

API_VERSION = 'v1'

app_name = "api"

urlpatterns = [
    path(f"{API_VERSION}/schema/", get_schema_view(title="MediaSense API"), name="schema"),
    path(f"{API_VERSION}/docs/", include_docs_urls(title="MediaSense API"), name="docs"),
    path(f"{API_VERSION}/auth/", include("custom_auth.urls", namespace="auth")),
    path(f"{API_VERSION}/news/", include("news.urls")),
    path(f"{API_VERSION}/search/", include("news_search.urls")),
    path(f"{API_VERSION}/crawler/", include("crawler.urls")),
    path(f"{API_VERSION}/ai/", include("ai_service.urls")),
    path(f"{API_VERSION}/monitoring/", include("monitoring.urls", namespace="monitoring")),
]
