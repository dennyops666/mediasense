from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt

app_name = "api"

class AsyncURLPattern:
    """支持异步视图的URL模式包装器"""
    def __init__(self, urlpatterns):
        self.urlpatterns = urlpatterns

    def __iter__(self):
        for pattern in self.urlpatterns:
            if hasattr(pattern, 'callback'):
                pattern.callback = csrf_exempt(pattern.callback)
            yield pattern

    def __reversed__(self):
        return reversed(list(self))

urlpatterns = AsyncURLPattern([
    path("auth/", include(("custom_auth.urls", "auth"), namespace="auth")),
    path("news/", include(("news.urls", "news"), namespace="news")),
    path("crawler/", include(("crawler.urls", "crawler"), namespace="crawler")),
    path("search/", include(("news_search.urls", "news_search"), namespace="news_search")),
    path("ai/", include(("ai_service.urls", "ai_service"), namespace="ai_service")),
    path("monitoring/", include(("monitoring.urls", "monitoring"), namespace="monitoring")),
])
