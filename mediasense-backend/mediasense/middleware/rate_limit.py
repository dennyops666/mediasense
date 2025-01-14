import time

from django.core.cache import cache
from django.http import JsonResponse


class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 获取用户IP
        ip = request.META.get("REMOTE_ADDR")
        # 获取当前时间戳
        current = time.time()
        # 生成缓存key
        cache_key = f"rate_limit_{ip}"

        # 获取用户访问历史
        history = cache.get(cache_key, [])
        # 清理60秒前的记录
        history = [x for x in history if current - x < 60]

        if len(history) >= 60:  # 每分钟最多60次请求
            return JsonResponse({"code": 429, "message": "Too many requests"}, status=429)

        history.append(current)
        cache.set(cache_key, history, 60)

        return self.get_response(request)
