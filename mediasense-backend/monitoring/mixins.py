from asgiref.sync import sync_to_async
import asyncio
from django.http import HttpResponse, Http404
from rest_framework.response import Response
from rest_framework import status, exceptions, viewsets
from django.core.exceptions import ValidationError
from django.db import models
from rest_framework.request import Request, Empty
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
import json

class SyncAsyncViewSetMixin(viewsets.ViewSetMixin):
    """同步异步视图集混入类"""

    renderer_classes = [JSONRenderer]
    parser_classes = [JSONParser]

    @classmethod
    def as_view(cls, actions=None, **initkwargs):
        """视图工厂"""
        if not actions:
            actions = {}
        
        # 确保基类的 __init__ 方法被调用
        async def view(request, *args, **kwargs):
            self = cls()
            self.action_map = actions
            self.actions = actions
            for key, value in initkwargs.items():
                setattr(self, key, value)
            
            # 设置当前动作
            handler = actions.get(request.method.lower())
            if handler:
                self.action = handler
            
            # 处理自定义动作
            if request.path.endswith('/resolve/'):
                self.action = 'resolve'
                handler = getattr(self, 'resolve', None)
                if handler:
                    return await handler(request, *args, **kwargs)
            elif request.path.endswith('/ignore/'):
                self.action = 'ignore'
                handler = getattr(self, 'ignore', None)
                if handler:
                    return await handler(request, *args, **kwargs)
            elif request.path.endswith('/stats/'):
                self.action = 'stats'
                handler = getattr(self, 'stats', None)
                if handler:
                    return await handler(request, *args, **kwargs)
            
            return await self.dispatch(request, *args, **kwargs)
        
        return view

    async def initialize_request(self, request, *args, **kwargs):
        """初始化请求"""
        try:
            if not isinstance(request, Request):
                request = Request(request)

            request.method = request.method.upper()
            if request.content_type == 'application/json' or request.content_type is None:
                request.META['CONTENT_TYPE'] = 'application/json'
                request.META['HTTP_ACCEPT'] = 'application/json'
                if request.body:
                    try:
                        data = json.loads(request.body.decode('utf-8'))
                        print(f"原始请求体: {request.body.decode('utf-8')}")  # 调试信息
                        print(f"解析后的数据: {data}")  # 调试信息
                        # 创建一个新的请求对象
                        new_request = Request(request)
                        # 设置请求属性
                        object.__setattr__(new_request, '_data', data if data is not None else Empty)
                        object.__setattr__(new_request, '_full_data', data if data is not None else Empty)
                        object.__setattr__(new_request, '_request', request)
                        object.__setattr__(new_request, 'method', request.method)
                        object.__setattr__(new_request, 'META', request.META)
                        object.__setattr__(new_request, 'user', request.user)
                        object.__setattr__(new_request, 'authenticators', request.authenticators)
                        object.__setattr__(new_request, 'successful_authenticator', request.successful_authenticator)
                        object.__setattr__(new_request, 'parser_context', {
                            'kwargs': kwargs,
                            'args': args,
                            'request': new_request,
                            'encoding': request.encoding or 'utf-8'
                        })
                        return new_request
                    except json.JSONDecodeError as e:
                        print(f"JSON解析错误: {str(e)}")  # 调试信息
                        new_request = Request(request)
                        # 设置请求属性
                        object.__setattr__(new_request, '_data', Empty)
                        object.__setattr__(new_request, '_full_data', Empty)
                        object.__setattr__(new_request, '_request', request)
                        object.__setattr__(new_request, 'method', request.method)
                        object.__setattr__(new_request, 'META', request.META)
                        object.__setattr__(new_request, 'user', request.user)
                        object.__setattr__(new_request, 'authenticators', request.authenticators)
                        object.__setattr__(new_request, 'successful_authenticator', request.successful_authenticator)
                        object.__setattr__(new_request, 'parser_context', {
                            'kwargs': kwargs,
                            'args': args,
                            'request': new_request,
                            'encoding': request.encoding or 'utf-8'
                        })
                        return new_request
                else:
                    print("请求体为空")  # 调试信息
                    new_request = Request(request)
                    # 设置请求属性
                    object.__setattr__(new_request, '_data', Empty)
                    object.__setattr__(new_request, '_full_data', Empty)
                    object.__setattr__(new_request, '_request', request)
                    object.__setattr__(new_request, 'method', request.method)
                    object.__setattr__(new_request, 'META', request.META)
                    object.__setattr__(new_request, 'user', request.user)
                    object.__setattr__(new_request, 'authenticators', request.authenticators)
                    object.__setattr__(new_request, 'successful_authenticator', request.successful_authenticator)
                    object.__setattr__(new_request, 'parser_context', {
                        'kwargs': kwargs,
                        'args': args,
                        'request': new_request,
                        'encoding': request.encoding or 'utf-8'
                    })
                    return new_request
            
            return request
        except Exception as e:
            print(f"初始化请求异常: {str(e)}")  # 调试信息
            raise

    async def get_handler(self, request):
        """获取处理器"""
        handler = getattr(self, request.method.lower(), None)
        if handler is None:
            return self.http_method_not_allowed
        return handler

    async def dispatch(self, request, *args, **kwargs):
        """分发请求"""
        try:
            print(f"开始处理请求: {request.method} {request.path}")  # 调试信息
            
            # 初始化请求
            request = await self.initialize_request(request, *args, **kwargs)
            self.request = request
            self.args = args
            self.kwargs = kwargs
            
            print(f"请求数据: {request.data}")  # 调试信息
            print(f"请求用户: {request.user}")  # 调试信息
            
            # 获取处理器
            handler = await self.get_handler(request)
            print(f"处理器: {handler}")  # 调试信息
            
            # 执行处理
            try:
                response = await handler(request, *args, **kwargs)
                print(f"处理结果: {response}")  # 调试信息
            except Exception as e:
                print(f"处理异常: {str(e)}")  # 调试信息
                raise
            
            # 完成响应
            try:
                response = await self.finalize_response(request, response, *args, **kwargs)
                print(f"最终响应: {response}")  # 调试信息
                return response
            except Exception as e:
                print(f"完成响应异常: {str(e)}")  # 调试信息
                raise
            
        except Exception as e:
            print(f"请求处理异常: {str(e)}")  # 调试信息
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
        if hasattr(self, 'queryset') and self.queryset is not None:
            queryset = self.queryset
            if isinstance(queryset, models.QuerySet):
                queryset = queryset._chain()
            return queryset
        raise NotImplementedError('get_queryset() must be implemented.')

    async def get_object(self):
        """获取对象"""
        queryset = await self.get_queryset()
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs[lookup_url_kwarg]

        try:
            obj = await sync_to_async(queryset.get)(pk=lookup_value)
            return obj
        except models.ObjectDoesNotExist:
            raise Http404

    async def get_serializer_class(self):
        """获取序列化器类"""
        if hasattr(self, 'serializer_class'):
            return self.serializer_class
        raise NotImplementedError('get_serializer_class() must be implemented.')

    async def get_serializer(self, *args, **kwargs):
        """获取序列化器实例"""
        serializer_class = await self.get_serializer_class()
        kwargs['context'] = await self.get_serializer_context()
        return serializer_class(*args, **kwargs)

    async def get_serializer_context(self):
        """获取序列化器上下文"""
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }

    async def create(self, request, *args, **kwargs):
        """创建对象"""
        try:
            print("开始创建对象...")  # 调试信息
            print(f"请求数据: {request.data}")  # 调试信息
            
            # 获取序列化器
            serializer = await self.get_serializer(data=request.data)
            
            # 验证数据
            await sync_to_async(serializer.is_valid)(raise_exception=True)
            
            # 保存数据
            instance = await sync_to_async(serializer.save)()
            
            # 返回响应
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            print(f"Error in create: {str(e)}")  # 调试信息
            raise

    async def __call__(self, request, *args, **kwargs):
        """调用视图"""
        try:
            # 调用 dispatch 方法并等待结果
            response = await self.dispatch(request, *args, **kwargs)
            
            # 如果响应是协程,等待它
            if asyncio.iscoroutine(response):
                response = await response
                
            # 确保响应有 _resource_closers 属性
            if not hasattr(response, '_resource_closers'):
                response._resource_closers = []
                
            return response
            
        except Exception as exc:
            # 处理异常
            if asyncio.iscoroutine(exc):
                exc = await exc
            response = await self.handle_exception(exc)
            if not hasattr(response, '_resource_closers'):
                response._resource_closers = []
            return response

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