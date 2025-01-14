import logging

from django.core.exceptions import ValidationError
from django.http import Http404, JsonResponse
from rest_framework.exceptions import APIException
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class APIResponseMiddleware:
    """统一API响应格式的中间件"""

    ERROR_CODES = {
        400: "请求参数错误",
        401: "未经授权",
        403: "权限不足",
        404: "资源不存在",
        405: "不支持的请求方法",
        429: "请求过于频繁",
        500: "服务器内部错误",
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)

            # 只处理API请求
            if not request.path.startswith("/api/"):
                return response

            # 如果是DRF的Response,转换格式
            if isinstance(response, Response):
                data = {"code": response.status_code, "message": "success", "data": response.data}
                return JsonResponse(data, status=response.status_code)

            # 如果是JsonResponse,检查是否符合统一格式
            if isinstance(response, JsonResponse):
                if not isinstance(response.data, dict):
                    return response

                if "code" not in response.data:
                    data = {"code": response.status_code, "message": "success", "data": response.data}
                    return JsonResponse(data, status=response.status_code)

            return response

        except Http404 as e:
            return self.handle_error(404, str(e))
        except ValidationError as e:
            return self.handle_error(400, str(e))
        except APIException as e:
            return self.handle_error(e.status_code, str(e.detail))
        except Exception as e:
            logger.exception("Unhandled exception in API request")
            return self.handle_error(500, "服务器内部错误")

    def handle_error(self, status_code, message=None):
        """统一错误响应处理"""
        if message is None:
            message = self.ERROR_CODES.get(status_code, "未知错误")

        data = {"code": status_code, "message": message, "data": None}
        return JsonResponse(data, status=status_code)
