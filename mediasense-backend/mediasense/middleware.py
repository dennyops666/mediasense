from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from rest_framework import status
from django.core.cache import cache
from django.conf import settings
from rest_framework.response import Response
import time

class RateLimitMiddleware:
    """
    API请求限流中间件
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not hasattr(settings, 'API_GATEWAY') or not settings.API_GATEWAY['RATE_LIMIT']['ENABLED']:
            return self.get_response(request)

        # 获取限流配置
        rate_limit = settings.API_GATEWAY['RATE_LIMIT']['DEFAULT_LIMIT']
        window = settings.API_GATEWAY['RATE_LIMIT']['DEFAULT_WINDOW']

        # 获取用户标识
        if request.user.is_authenticated:
            key = f"rate_limit:{request.user.id}"
        else:
            key = f"rate_limit:{request.META.get('REMOTE_ADDR', 'anonymous')}"

        # 获取当前时间窗口的请求次数
        current_time = int(time.time())
        window_key = f"{key}:{current_time // window}"
        request_count = cache.get(window_key, 0)

        if request_count >= rate_limit:
            return Response(
                {"detail": "请求过于频繁，请稍后再试"},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        # 更新请求计数
        cache.set(window_key, request_count + 1, window)
        
        return self.get_response(request)

class Custom404Middleware:
    """
    自定义404错误处理中间件
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response.status_code == 404:
            return Response(
                {"detail": "请求的资源不存在"},
                status=status.HTTP_404_NOT_FOUND
            )
        return response 