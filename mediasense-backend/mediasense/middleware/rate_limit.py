from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
import time
import logging

logger = logging.getLogger(__name__)

class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limit = getattr(settings, 'RATE_LIMIT', {
            'enabled': True,
            'requests_per_minute': 60
        })

    def __call__(self, request):
        if not self.rate_limit.get('enabled', True):
            return self.get_response(request)

        # 获取用户标识
        if request.user.is_authenticated:
            key = f"rate_limit_user_{request.user.id}"
        else:
            key = f"rate_limit_ip_{request.META.get('REMOTE_ADDR')}"

        # 获取当前时间戳
        now = time.time()
        window_start = now - 60  # 1分钟窗口

        # 获取请求历史
        request_history = cache.get(key, [])
        if not isinstance(request_history, list):
            request_history = []
        
        # 清理过期记录
        request_history = [ts for ts in request_history if ts > window_start]
        
        # 检查是否超过限制
        if len(request_history) >= self.rate_limit.get('requests_per_minute', 60):
            logger.warning(f"Rate limit exceeded for {key}")
            return JsonResponse({
                'error': 'rate_limit_exceeded',
                'detail': '请求频率超过限制，请稍后再试'
            }, status=429)

        # 添加新请求记录
        request_history.append(now)
        cache.set(key, request_history, 60)  # 60秒过期

        return self.get_response(request)
