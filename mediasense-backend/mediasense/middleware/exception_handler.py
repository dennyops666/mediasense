import logging
import traceback

from django.http import JsonResponse
from rest_framework import status

logger = logging.getLogger("django")


class ExceptionHandlerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        """处理视图函数中的异常"""
        # 记录异常信息
        logger.error(f"Exception occurred: {str(exception)}")
        logger.error(traceback.format_exc())

        # 根据异常类型返回不同的响应
        if isinstance(exception, ValueError):
            return JsonResponse({"error": "参数错误", "detail": str(exception)}, status=status.HTTP_400_BAD_REQUEST)

        elif isinstance(exception, PermissionError):
            return JsonResponse({"error": "权限不足", "detail": str(exception)}, status=status.HTTP_403_FORBIDDEN)

        # 其他未知异常
        return JsonResponse(
            {"error": "服务器内部错误", "detail": "请联系管理员"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
