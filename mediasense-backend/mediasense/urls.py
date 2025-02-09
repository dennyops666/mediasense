"""
URL configuration for mediasense project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.sites import AdminSite

# 创建一个支持异步的AdminSite
class AsyncAdminSite(AdminSite):
    def get_urls(self):
        urls = super().get_urls()
        processed_urls = []
        for url in urls:
            if hasattr(url, 'callback'):
                # 使用新的path()格式,移除正则表达式语法
                pattern = url.pattern.regex.pattern
                pattern = pattern.lstrip('^').rstrip('$').replace('(?P<', '<').replace('>', '>')
                processed_urls.append(
                    path(pattern,
                         csrf_exempt(url.callback),
                         name=url.name if hasattr(url, 'name') else None)
                )
            else:
                processed_urls.append(url)
        return processed_urls

admin_site = AsyncAdminSite(name='admin')

urlpatterns = [
    path('admin/', admin_site.urls),
    # API路由
    path('api/auth/', include('custom_auth.urls')),  # 认证模块URLs
    path('api/news/', include('news.urls')),  # 新闻模块URLs
    path('api/crawler/', include('crawler.urls')),  # 爬虫模块URLs
    path('api/search/', include('news_search.urls')),  # 搜索模块URLs
    path('api/ai/', include('ai_service.urls')),  # AI模块URLs
    path('api/monitoring/', include('monitoring.urls')),  # 监控模块URLs
]
