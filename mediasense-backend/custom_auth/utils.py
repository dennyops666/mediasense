from rest_framework import status
from rest_framework.views import exception_handler
from rest_framework.exceptions import NotAuthenticated, PermissionDenied, AuthenticationFailed
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

def custom_exception_handler(exc, context):
    """自定义异常处理器"""
    response = exception_handler(exc, context)

    if response is None:
        return response

    if isinstance(exc, (NotAuthenticated, AuthenticationFailed, InvalidToken, TokenError)):
        response.status_code = status.HTTP_401_UNAUTHORIZED
        response.data = {'message': '认证失败'}
    elif isinstance(exc, PermissionDenied):
        response.status_code = status.HTTP_403_FORBIDDEN
        response.data = {'message': '权限不足'}
    else:
        # 处理其他类型的错误
        if not response.data:
            response.data = {'message': '服务器内部错误，请稍后重试'}
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return response
        
        if isinstance(response.data, dict):
            if 'detail' in response.data:
                detail = response.data.pop('detail')
                if isinstance(detail, dict) and 'message' in detail:
                    response.data = detail
                else:
                    response.data = {'message': str(detail)}
            elif not any(key == 'message' for key in response.data.keys()):
                response.data = {'message': str(response.data)}
            elif isinstance(response.data.get('message'), (list, dict)):
                response.data['message'] = str(response.data['message'])
        else:
            response.data = {'message': str(response.data)}

    return response 