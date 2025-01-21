from asgiref.sync import sync_to_async
import asyncio
from django.http import HttpResponse, Http404
from rest_framework.response import Response
from rest_framework import status, exceptions, viewsets
from django.core.exceptions import ValidationError
from django.db import models
from rest_framework.request import Request
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser

class SyncAsyncViewSetMixin(viewsets.ViewSetMixin):
    """同步异步视图集混入类"""

    renderer_classes = [JSONRenderer]
    parser_classes = [JSONParser]

    @classmethod
    def as_view(cls, actions=None, **initkwargs):
        """视图工厂"""
        instance = cls(**initkwargs)
        instance.action_map = actions or {}
        instance.actions = actions or {}
        return instance.dispatch

    async def initialize_request(self, request, *args, **kwargs):
        """初始化请求"""
        if not isinstance(request, Request):
            request = Request(request)

        request.method = request.method.upper()
        if request.content_type == 'application/json':
            request.META['CONTENT_TYPE'] = 'application/json'
            request.META['HTTP_ACCEPT'] = 'application/json'
            
        return request

    async def get_handler(self, request):
        """获取处理器"""
        handler = getattr(self, request.method.lower(), None)
        if handler is None:
            return self.http_method_not_allowed
        return handler

    async def dispatch(self, request, *args, **kwargs):
        """分发请求"""
        try:
            request = await self.initialize_request(request, *args, **kwargs)
            self.request = request
            self.args = args
            self.kwargs = kwargs
            
            handler = await self.get_handler(request)
            response = await handler(request, *args, **kwargs)
            return await self.finalize_response(request, response, *args, **kwargs)
        except Exception as e:
            return await self.handle_exception(e)

    async def finalize_response(self, request, response, *args, **kwargs):
        """完成响应"""
        if isinstance(response, Response):
            if not hasattr(response, '_closable_objects'):
                response._closable_objects = []
            response.accepted_renderer = JSONRenderer()
            response.accepted_media_type = 'application/json'
            response.renderer_context = {
                'request': request,
                'format': kwargs.get('format', None),
                'view': self,
            }
        return response

    async def handle_exception(self, exc):
        """处理异常"""
        if isinstance(exc, (ValidationError, exceptions.ValidationError)):
            return Response(
                {'detail': await self._get_error_details(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )
        elif isinstance(exc, exceptions.APIException):
            return Response(
                {'detail': await self._get_error_details(exc)},
                status=exc.status_code
            )
        elif isinstance(exc, Http404):
            return Response(
                {'detail': 'Not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        elif isinstance(exc, models.ObjectDoesNotExist):
            return Response(
                {'detail': str(exc)},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(
            {'detail': 'Internal server error.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    async def _get_error_details(self, exc):
        """获取错误详情"""
        if hasattr(exc, 'detail'):
            return exc.detail
        return str(exc)

    async def get_renderer_context(self):
        """获取渲染器上下文"""
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }

    async def get_renderers(self):
        """获取渲染器"""
        return [renderer() for renderer in self.renderer_classes]

    async def get_queryset(self):
        """获取查询集"""
        if self.queryset is not None:
            return self.queryset
        raise NotImplementedError('get_queryset() must be implemented.')

    async def get_object(self):
        """获取对象"""
        queryset = await self.get_queryset()
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs[lookup_url_arg]

        try:
            obj = await sync_to_async(queryset.get)(id=lookup_value)
            await sync_to_async(self.check_object_permissions)(self.request, obj)
            return obj
        except models.ObjectDoesNotExist:
            raise Http404

    async def get_serializer(self, *args, **kwargs):
        """获取序列化器"""
        serializer_class = await sync_to_async(self.get_serializer_class)()
        kwargs.setdefault('context', await self.get_serializer_context())
        return serializer_class(*args, **kwargs)

    async def get_serializer_context(self):
        """获取序列化器上下文"""
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }

    async def get_serializer_class(self):
        """获取序列化器类"""
        if self.serializer_class is None:
            raise NotImplementedError('serializer_class must be implemented.')
        return self.serializer_class

    def __call__(self, request, *args, **kwargs):
        """调用视图"""
        try:
            # 获取事件循环
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            # 调用 dispatch 方法并等待结果
            response = loop.run_until_complete(self.dispatch(request, *args, **kwargs))
            
            # 如果响应是协程,等待它
            if asyncio.iscoroutine(response):
                response = loop.run_until_complete(response)
                
            # 确保响应有 _resource_closers 属性
            if not hasattr(response, '_resource_closers'):
                response._resource_closers = []
                
            return response
            
        except Exception as exc:
            # 处理异常
            if asyncio.iscoroutine(exc):
                exc = loop.run_until_complete(exc)
            response = self.handle_exception(exc)
            if not hasattr(response, '_resource_closers'):
                response._resource_closers = []
            return response
            
        finally:
            # 关闭事件循环
            if loop and not loop.is_closed():
                loop.close()

    async def get(self, request, *args, **kwargs):
        """GET 请求"""
        return await self.list(request, *args, **kwargs)

    async def post(self, request, *args, **kwargs):
        """POST 请求"""
        return await self.create(request, *args, **kwargs)

    async def put(self, request, *args, **kwargs):
        """PUT 请求"""
        return await self.update(request, *args, **kwargs)

    async def patch(self, request, *args, **kwargs):
        """PATCH 请求"""
        return await self.partial_update(request, *args, **kwargs)

    async def delete(self, request, *args, **kwargs):
        """DELETE 请求"""
        return await self.destroy(request, *args, **kwargs)

    async def partial_update(self, request, *args, **kwargs):
        """部分更新"""
        kwargs['partial'] = True
        return await self.update(request, *args, **kwargs)

    async def list(self, request, *args, **kwargs):
        """列表视图"""
        queryset = await self.get_queryset()
        serializer = await self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    async def create(self, request, *args, **kwargs):
        """创建视图"""
        serializer = await self.get_serializer(data=request.data)
        await sync_to_async(serializer.is_valid)(raise_exception=True)
        instance = await sync_to_async(serializer.save)()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    async def retrieve(self, request, *args, **kwargs):
        """详情视图"""
        instance = await self.get_object()
        serializer = await self.get_serializer(instance)
        return Response(serializer.data)

    async def update(self, request, *args, **kwargs):
        """更新视图"""
        partial = kwargs.pop('partial', False)
        instance = await self.get_object()
        serializer = await self.get_serializer(instance, data=request.data, partial=partial)
        await sync_to_async(serializer.is_valid)(raise_exception=True)
        instance = await sync_to_async(serializer.save)()
        return Response(serializer.data)

    async def destroy(self, request, *args, **kwargs):
        """删除视图"""
        instance = await self.get_object()
        await sync_to_async(instance.delete)()
        return Response(status=status.HTTP_204_NO_CONTENT) 