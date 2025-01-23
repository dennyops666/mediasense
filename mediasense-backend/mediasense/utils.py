from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from django.core.exceptions import PermissionDenied
from rest_framework.exceptions import (
    APIException,
    NotAuthenticated,
    AuthenticationFailed,
    MethodNotAllowed,
    NotFound,
    ValidationError
)

def custom_exception_handler(exc, context):
    """自定义异常处理器"""
    if isinstance(exc, Http404):
        exc = NotFound()
    elif isinstance(exc, PermissionDenied):
        exc = AuthenticationFailed()

    response = exception_handler(exc, context)

    if response is not None:
        # 将 detail 字段重命名为 message
        if 'detail' in response.data:
            response.data = {'message': response.data['detail']}
        # 确保所有错误响应都有 message 字段
        elif 'message' not in response.data:
            response.data = {'message': str(exc)}
    else:
        # 处理未捕获的异常
        response = Response(
            {'message': '服务器内部错误'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return response 