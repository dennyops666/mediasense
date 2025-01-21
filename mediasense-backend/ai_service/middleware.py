from django.http import HttpResponse, JsonResponse
from django.core.exceptions import MiddlewareNotUsed
import asyncio
from asgiref.sync import sync_to_async
from django.http import HttpResponse
from django.core.handlers.asgi import ASGIRequest
from rest_framework.response import Response
from rest_framework import status
from rest_framework.renderers import JSONRenderer
import json
import openai

class AsyncMiddleware:
    """异步中间件"""

    def __init__(self, get_response):
        """初始化中间件"""
        self.get_response = get_response

    async def __call__(self, request):
        """处理请求"""
        try:
            response = await self.get_response(request)
            
            # 如果响应是协程，等待它完成
            if asyncio.iscoroutine(response):
                response = await response
            
            # 处理 DRF Response 对象
            if isinstance(response, Response):
                # 设置渲染器
                if not hasattr(response, 'accepted_renderer'):
                    response.accepted_renderer = JSONRenderer()
                    response.accepted_media_type = "application/json"
                    response.renderer_context = {}
                
                # 渲染响应
                if asyncio.iscoroutinefunction(response.render):
                    rendered = await response.render()
                else:
                    rendered = response.render()
                
                # 创建新的 HttpResponse
                http_response = HttpResponse(
                    content=rendered.content,
                    status=response.status_code,
                    content_type=response.content_type
                )
                
                # 复制原始响应的属性
                if hasattr(response, 'headers'):
                    for key, value in response.headers.items():
                        http_response[key] = value
                
                # 确保响应有 headers 属性
                if not hasattr(http_response, 'headers'):
                    http_response.headers = {}
                
                return http_response
            
            # 处理 JsonResponse 对象
            if isinstance(response, JsonResponse):
                # 确保响应有 headers 属性
                if not hasattr(response, 'headers'):
                    response.headers = {}
                return response
            
            # 处理其他类型的响应
            if not isinstance(response, HttpResponse):
                if isinstance(response, (dict, list)):
                    response = JsonResponse(response, safe=False)
                elif isinstance(response, str):
                    response = JsonResponse({'message': response})
                else:
                    response = JsonResponse({'data': str(response)})
                
                # 确保响应有 headers 属性
                if not hasattr(response, 'headers'):
                    response.headers = {}
                
                return response
            
            # 确保 HttpResponse 有 headers 属性
            if not hasattr(response, 'headers'):
                response.headers = {}
            
            return response
            
        except openai.RateLimitError as e:
            response = JsonResponse(
                {'error': 'rate_limit_exceeded', 'detail': str(e)},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
            response.headers = {}
            return response
        except openai.APIStatusError as e:
            if e.response.status == 429:
                response = JsonResponse(
                    {'error': 'rate_limit_exceeded', 'detail': str(e)},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            else:
                response = JsonResponse(
                    {'error': 'openai_error', 'detail': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            response.headers = {}
            return response
        except ValueError as e:
            response = JsonResponse(
                {'error': 'invalid_input', 'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
            response.headers = {}
            return response
        except Exception as e:
            response = JsonResponse(
                {'error': 'internal_error', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            response.headers = {}
            return response

    async def process_request(self, request):
        """处理请求"""
        pass

    async def process_response(self, request, response):
        """处理响应"""
        try:
            # 如果响应是协程对象，等待它完成
            if asyncio.iscoroutine(response):
                response = await response
            
            # 如果响应是Response对象，渲染它
            if isinstance(response, Response):
                # 设置渲染器
                if not hasattr(response, 'accepted_renderer'):
                    response.accepted_renderer = JSONRenderer()
                    response.accepted_media_type = "application/json"
                    response.renderer_context = {}
                
                # 渲染响应
                if asyncio.iscoroutinefunction(response.render):
                    rendered = await response.render()
                else:
                    rendered = response.render()
                
                # 创建新的 JsonResponse
                return JsonResponse(
                    response.data,
                    status=response.status_code,
                    safe=False
                )
            
            # 处理 JsonResponse 对象
            if isinstance(response, JsonResponse):
                return response
            
            # 处理其他类型的响应
            if not isinstance(response, HttpResponse):
                if isinstance(response, (dict, list)):
                    return JsonResponse(response, safe=False)
                elif isinstance(response, str):
                    return JsonResponse({'message': response})
                else:
                    return JsonResponse({'data': str(response)})
            
            return response
            
        except Exception as e:
            return JsonResponse(
                {'error': 'internal_error', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def process_exception(self, request, exception):
        """处理异常"""
        try:
            if isinstance(exception, openai.RateLimitError):
                return JsonResponse(
                    {'error': 'rate_limit_exceeded', 'detail': str(exception)},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            elif isinstance(exception, openai.APIStatusError):
                if exception.response.status == 429:
                    return JsonResponse(
                        {'error': 'rate_limit_exceeded', 'detail': str(exception)},
                        status=status.HTTP_429_TOO_MANY_REQUESTS
                    )
                return JsonResponse(
                    {'error': 'openai_error', 'detail': str(exception)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            elif isinstance(exception, ValueError):
                return JsonResponse(
                    {'error': 'invalid_input', 'detail': str(exception)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                return JsonResponse(
                    {'error': 'internal_error', 'detail': str(exception)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            return JsonResponse(
                {'error': 'internal_error', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 