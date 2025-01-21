from django.http import HttpResponse, JsonResponse
from rest_framework.response import Response
import asyncio
from asgiref.sync import sync_to_async, iscoroutinefunction, async_to_sync
from django.core.handlers.asgi import ASGIRequest
from django.core.handlers.wsgi import WSGIRequest
from django.utils.decorators import sync_and_async_middleware
from rest_framework.renderers import JSONRenderer
from rest_framework import status
from functools import wraps

@sync_and_async_middleware
class AsyncMiddleware:
    """异步中间件"""

    def __init__(self, get_response):
        """初始化"""
        self.get_response = get_response
        self.renderer = JSONRenderer()

    async def __call__(self, request):
        """处理请求和响应"""
        try:
            # 处理请求
            if request.content_type == 'application/json':
                request.META['CONTENT_TYPE'] = 'application/json'
                request.META['HTTP_ACCEPT'] = 'application/json'
            
            # 获取响应
            response = await self.get_response(request)
            
            # 如果响应是协程，等待它
            if asyncio.iscoroutine(response):
                response = await response
            
            # 如果是DRF Response，转换为HttpResponse
            if isinstance(response, Response):
                # 设置渲染器
                if not hasattr(response, 'accepted_renderer'):
                    response.accepted_renderer = self.renderer
                    response.accepted_media_type = 'application/json'
                    response.renderer_context = {
                        'request': request,
                        'response': response,
                    }
                
                # 渲染响应
                if not hasattr(response, 'rendered_content'):
                    response.rendered_content = self.renderer.render(response.data)
                
                http_response = HttpResponse(
                    content=response.rendered_content,
                    status=response.status_code,
                    content_type='application/json'
                )
                
                # 复制headers
                for key, value in response.items():
                    http_response[key] = value
                
                return http_response
            
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
                {'error': str(e)},
                status=500
            )

    def __call__(self, request):
        """同步调用"""
        if asyncio.iscoroutinefunction(self.get_response):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(self.__acall__(request))
            finally:
                loop.close()
            return response
        return self.get_response(request)

    async def __acall__(self, request):
        """异步调用"""
        try:
            # 处理请求
            if request.content_type == 'application/json':
                request.META['CONTENT_TYPE'] = 'application/json'
                request.META['HTTP_ACCEPT'] = 'application/json'
            
            # 获取响应
            response = await self.get_response(request)
            
            # 如果响应是协程，等待它
            if asyncio.iscoroutine(response):
                response = await response
            
            # 如果是DRF Response，转换为HttpResponse
            if isinstance(response, Response):
                # 设置渲染器
                if not hasattr(response, 'accepted_renderer'):
                    response.accepted_renderer = self.renderer
                    response.accepted_media_type = 'application/json'
                    response.renderer_context = {
                        'request': request,
                        'response': response,
                    }
                
                # 渲染响应
                if not hasattr(response, 'rendered_content'):
                    response.rendered_content = self.renderer.render(response.data)
                
                http_response = HttpResponse(
                    content=response.rendered_content,
                    status=response.status_code,
                    content_type='application/json'
                )
                
                # 复制headers
                for key, value in response.items():
                    http_response[key] = value
                
                return http_response
            
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
                {'error': str(e)},
                status=500
            ) 