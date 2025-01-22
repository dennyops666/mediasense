from django.http import HttpResponse, JsonResponse
from rest_framework.response import Response
import asyncio
from asgiref.sync import sync_to_async, iscoroutinefunction
from django.utils.decorators import sync_and_async_middleware
from rest_framework.renderers import JSONRenderer
from django.core.handlers.asgi import ASGIRequest

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
            # 获取响应
            response = self.get_response(request)
            
            # 如果响应是协程,等待它完成
            if asyncio.iscoroutine(response):
                response = await response
            
            # 如果是DRF Response,转换为HttpResponse
            if isinstance(response, Response):
                response = self._convert_drf_response(response, request)
                
            # 如果响应是协程,等待它完成
            if asyncio.iscoroutine(response):
                response = await response
                
            # 如果响应是DRF Response,再次转换
            if isinstance(response, Response):
                response = self._convert_drf_response(response, request)
                
            return response
            
        except Exception as e:
            return JsonResponse(
                {
                    'error': str(e),
                    'detail': 'Request failed'
                },
                status=500
            )

    def _convert_drf_response(self, response, request):
        """转换DRF响应为HttpResponse"""
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
            response.rendered_content = response.accepted_renderer.render(response.data)
        
        # 创建HttpResponse
        http_response = HttpResponse(
            content=response.rendered_content,
            status=response.status_code,
            content_type=response.content_type or 'application/json'
        )
        
        # 复制headers
        for key, value in response.items():
            http_response[key] = value
            
        # 复制data属性
        http_response.data = response.data
        
        return http_response

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
            # 获取响应
            response = await self.get_response(request)
            
            # 如果是DRF Response,转换为HttpResponse
            if isinstance(response, Response):
                response = self._convert_drf_response(response, request)
                
            return response
            
        except Exception as e:
            return JsonResponse(
                {
                    'error': str(e),
                    'detail': 'Request failed'
                },
                status=500
            ) 