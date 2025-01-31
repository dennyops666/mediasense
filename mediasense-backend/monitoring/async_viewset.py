from django.http import HttpResponse, HttpResponseBase, Http404
from rest_framework.response import Response
from rest_framework import viewsets, status, exceptions
from rest_framework.viewsets import ViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.utils import timezone
from datetime import timedelta
from django.db import models
from rest_framework import serializers
from asgiref.sync import sync_to_async
import asyncio
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from rest_framework.negotiation import DefaultContentNegotiation
from rest_framework.versioning import AcceptHeaderVersioning
from rest_framework.metadata import SimpleMetadata
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.settings import api_settings
import logging
from rest_framework.request import Request
import json
from django.conf import settings
from django.utils.decorators import classonlymethod
from django.core.exceptions import ObjectDoesNotExist

logger = logging.getLogger(__name__)

class AsyncViewSet(ViewSet):
    """异步视图集基类"""
    renderer_classes = [JSONRenderer]
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    authentication_classes = []
    throttle_classes = []
    permission_classes = []
    content_negotiation_class = DefaultContentNegotiation
    metadata_class = SimpleMetadata
    versioning_class = AcceptHeaderVersioning
    
    lookup_field = 'pk'
    lookup_url_kwarg = None
    
    filter_backends = [SearchFilter, OrderingFilter]
    pagination_class = PageNumberPagination
    
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._paginator = None
        self.format_kwarg = None
        self.request = None
        self.action = None

    @classonlymethod
    def as_view(cls, actions=None, **initkwargs):
        """返回一个异步视图函数"""
        if not actions:
            actions = {}

        # 确保基类的 __init__ 方法被调用
        async def view(request, *args, **kwargs):
            self = cls(**initkwargs)
            self.action_map = actions
            self.actions = actions
            
            # 设置当前动作
            handler = actions.get(request.method.lower())
            if handler:
                self.action = handler
            
            return await self.dispatch(request, *args, **kwargs)
        
        return view

    async def get_serializer(self, *args, **kwargs):
        """获取序列化器实例"""
        try:
            serializer_class = await self.get_serializer_class()
            kwargs['context'] = await self.get_serializer_context()
            serializer = serializer_class(*args, **kwargs)
            return serializer
        except Exception as e:
            logger.error(f"获取序列化器实例失败: {str(e)}")
            raise

    async def get_serializer_class(self):
        """获取序列化器类"""
        if hasattr(self, 'serializer_class'):
            return self.serializer_class
        raise NotImplementedError('get_serializer_class() must be implemented.')

    async def get_serializer_context(self):
        """获取序列化器上下文"""
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }

    async def __call__(self, request, *args, **kwargs):
        """调用视图"""
        try:
            response = await self.dispatch(request, *args, **kwargs)
            
            # 确保响应是一个Response或HttpResponseBase对象
            if asyncio.iscoroutine(response):
                response = await response
                
            if not isinstance(response, (Response, HttpResponseBase)):
                if isinstance(response, dict):
                    response = Response(response)
                else:
                    response = Response({'data': response})
                
            if not hasattr(response, '_resource_closers'):
                response._resource_closers = []
                
            return response
            
        except Exception as exc:
            if asyncio.iscoroutine(exc):
                exc = await exc
            response = await self.handle_exception(exc)
            if not hasattr(response, '_resource_closers'):
                response._resource_closers = []
            return response

    async def dispatch(self, request, *args, **kwargs):
        """处理请求"""
        try:
            # 设置基本属性
            self.request = request
            self.args = args
            self.kwargs = kwargs
            
            # 获取处理方法
            handler = getattr(self, request.method.lower(), None)
            if handler is None:
                raise exceptions.MethodNotAllowed(request.method)
            
            # 调用处理方法
            response = await handler(request, *args, **kwargs)
            
            # 设置渲染器
            if isinstance(response, Response):
                if not hasattr(response, 'accepted_renderer'):
                    response.accepted_renderer = self.get_renderers()[0]
                if not hasattr(response, 'accepted_media_type'):
                    response.accepted_media_type = "application/json"
                if not hasattr(response, 'renderer_context'):
                    response.renderer_context = self.get_renderer_context()
            
            return response
            
        except Exception as e:
            logger.error(f"请求处理失败: {str(e)}")
            response = Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            response.accepted_renderer = self.get_renderers()[0]
            response.accepted_media_type = "application/json"
            response.renderer_context = self.get_renderer_context()
            return response

    async def initialize_request(self, request, *args, **kwargs):
        """初始化请求"""
        if isinstance(request, Request):
            return request
            
        new_request = Request(
            request,
            parsers=self.get_parsers(),
            authenticators=self.get_authenticators(),
            negotiator=self.get_content_negotiator(),
            parser_context=self.get_parser_context(request)
        )
        return new_request

    async def check_permissions(self, request):
        """检查权限"""
        for permission in self.get_permissions():
            if not await sync_to_async(permission.has_permission)(request, self):
                self.permission_denied(request)

    async def check_object_permissions(self, request, obj):
        """检查对象权限"""
        for permission in self.get_permissions():
            if not await sync_to_async(permission.has_object_permission)(request, self, obj):
                self.permission_denied(request)

    async def handle_exception(self, exc):
        """处理异常"""
        if isinstance(exc, Http404):
            exc = exceptions.NotFound()
        elif isinstance(exc, exceptions.PermissionDenied):
            exc = exceptions.PermissionDenied()
            
        if isinstance(exc, exceptions.APIException):
            headers = {}
            if getattr(exc, 'auth_header', None):
                headers['WWW-Authenticate'] = exc.auth_header
            if getattr(exc, 'wait', None):
                headers['Retry-After'] = '%d' % exc.wait
                
            return Response(
                {'detail': str(exc)},
                status=exc.status_code,
                headers=headers
            )
            
        return Response(
            {'detail': '服务器内部错误'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    async def perform_authentication(self, request):
        """执行认证"""
        try:
            # 如果请求已经认证过，直接返回
            if hasattr(request, 'user') and request.user is not None:
                return
            
            # 遍历认证器进行认证
            for authenticator in request.authenticators:
                try:
                    auth_tuple = await sync_to_async(authenticator.authenticate)(request)
                    if auth_tuple is not None:
                        request.user, request.auth = auth_tuple
                        request.successful_authenticator = authenticator
                        return
                except exceptions.APIException:
                    continue
            
            # 如果没有认证成功，设置默认用户
            if not hasattr(request, 'user'):
                request.user = None
            if not hasattr(request, 'auth'):
                request.auth = None
        except Exception as e:
            logger.error(f"执行认证失败: {str(e)}")
            raise

    def get_permissions(self):
        """获取权限类列表"""
        return [permission() for permission in self.permission_classes]

    def get_authenticators(self):
        """获取认证器列表"""
        return [auth() for auth in self.authentication_classes]

    def get_content_negotiator(self):
        """获取内容协商器"""
        if not hasattr(self, '_negotiator'):
            self._negotiator = self.content_negotiation_class()
        return self._negotiator

    def get_parser_context(self, request):
        """获取解析器上下文"""
        return {
            'view': self,
            'request': request,
            'args': getattr(self, 'args', ()),
            'kwargs': getattr(self, 'kwargs', {})
        }

    def get_parsers(self):
        """获取解析器列表"""
        return [parser() for parser in self.parser_classes]

    async def get_handler(self, request, *args, **kwargs):
        """获取请求处理方法"""
        try:
            if request.method.lower() in self.http_method_names:
                handler = getattr(self, request.method.lower(), self.http_method_not_allowed)
                return handler
            return self.http_method_not_allowed
        except Exception as e:
            logger.error(f"获取处理方法失败: {str(e)}")
            return None

    async def initial(self, request, *args, **kwargs):
        """初始化操作"""
        await self.check_permissions(request)
        await self.check_throttles(request)

    async def finalize_response(self, request, response, *args, **kwargs):
        """完成响应处理"""
        try:
            if isinstance(response, HttpResponseBase):
                return response

            if not isinstance(response, Response):
                response = Response(response)

            if not hasattr(response, 'accepted_renderer'):
                response.accepted_renderer = self.get_renderers()[0]
            if not hasattr(response, 'accepted_media_type'):
                response.accepted_media_type = "application/json"
            if not hasattr(response, 'renderer_context'):
                response.renderer_context = self.get_renderer_context()

            return response
        except Exception as e:
            logger.error(f"完成响应处理失败: {str(e)}")
            response = Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            response.accepted_renderer = self.get_renderers()[0]
            response.accepted_media_type = "application/json"
            response.renderer_context = self.get_renderer_context()
            return response

    async def get(self, request, *args, **kwargs):
        """处理 GET 请求"""
        try:
            if 'pk' in kwargs:
                return await self.retrieve(request, *args, **kwargs)
            return await self.list(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"处理 GET 请求失败: {str(e)}")
            response = Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            response.accepted_renderer = self.get_renderers()[0]
            response.accepted_media_type = "application/json"
            response.renderer_context = self.get_renderer_context()
            return response

    async def list(self, request, *args, **kwargs):
        """列出资源"""
        raise NotImplementedError('list() must be implemented.')

    async def retrieve(self, request, *args, **kwargs):
        """获取单个资源"""
        try:
            instance = await self.get_object()
            serializer = await self.get_serializer(instance)
            response = Response(serializer.data)
            response.accepted_renderer = self.get_renderers()[0]
            response.accepted_media_type = "application/json"
            response.renderer_context = self.get_renderer_context()
            return response
        except exceptions.NotFound:
            response = Response(
                {'detail': '未找到对象'},
                status=status.HTTP_404_NOT_FOUND
            )
            response.accepted_renderer = self.get_renderers()[0]
            response.accepted_media_type = "application/json"
            response.renderer_context = self.get_renderer_context()
            return response
        except Exception as e:
            logger.error(f"获取单个资源失败: {str(e)}")
            response = Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            response.accepted_renderer = self.get_renderers()[0]
            response.accepted_media_type = "application/json"
            response.renderer_context = self.get_renderer_context()
            return response

    async def create(self, request, *args, **kwargs):
        """创建对象"""
        try:
            serializer = self.get_serializer(data=request.data)
            await sync_to_async(serializer.is_valid)(raise_exception=True)
            instance = await self.perform_create(serializer)
            
            if instance:
                serializer = self.get_serializer(instance)
            
            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
                headers=headers
            )
        except serializers.ValidationError as e:
            logger.error(f"数据验证失败: {str(e)}")
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"创建对象失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def update(self, request, *args, **kwargs):
        """更新对象"""
        try:
            partial = kwargs.pop('partial', False)
            instance = await self.get_object()
            await self.check_object_permissions(request, instance)
            
            try:
                serializer = self.get_serializer(instance, data=request.data, partial=partial)
                if await sync_to_async(serializer.is_valid)(raise_exception=True):
                    instance = await self.perform_update(serializer)
                    if instance:
                        serializer = self.get_serializer(instance)
                    return Response(serializer.data)
            except Exception as e:
                logger.error(f"执行更新操作失败: {str(e)}")
                raise
        except serializers.ValidationError as e:
            logger.error(f"数据验证失败: {str(e)}")
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"更新对象失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def destroy(self, request, *args, **kwargs):
        """删除对象"""
        try:
            instance = await self.get_object()
            await self.check_object_permissions(request, instance)
            
            try:
                await self.perform_destroy(instance)
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Exception as e:
                logger.error(f"执行删除操作失败: {str(e)}")
                raise
        except Http404:
            raise
        except Exception as e:
            logger.error(f"删除对象失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def perform_create(self, serializer):
        """执行创建操作"""
        try:
            save_func = sync_to_async(serializer.save)
            try:
                instance = await save_func()
                return instance
            except Exception as e:
                logger.error(f"保存对象失败: {str(e)}")
                raise serializers.ValidationError(str(e))
        except Exception as e:
            logger.error(f"执行创建操作失败: {str(e)}")
            raise

    async def perform_update(self, serializer):
        """执行更新操作"""
        try:
            save_func = sync_to_async(serializer.save)
            try:
                instance = await save_func()
                return instance
            except Exception as e:
                logger.error(f"保存对象失败: {str(e)}")
                raise serializers.ValidationError(str(e))
        except Exception as e:
            logger.error(f"执行更新操作失败: {str(e)}")
            raise

    async def perform_destroy(self, instance):
        """执行删除操作"""
        try:
            delete_func = sync_to_async(instance.delete)
            try:
                await delete_func()
            except Exception as e:
                logger.error(f"删除对象失败: {str(e)}")
                raise serializers.ValidationError(str(e))
        except Exception as e:
            logger.error(f"执行删除操作失败: {str(e)}")
            raise

    async def get_object(self):
        """获取单个对象"""
        try:
            # 获取查询参数
            lookup_url_kwarg = getattr(self, 'lookup_url_kwarg', None) or self.lookup_field
            
            # 检查参数是否存在
            if lookup_url_kwarg not in self.kwargs:
                raise exceptions.NotFound()
            
            # 获取对象
            queryset = await self.get_queryset()
            filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
            
            # 使用 sync_to_async 包装 queryset.get
            get_object = sync_to_async(queryset.get)
            obj = await get_object(**filter_kwargs)
            
            # 检查对象权限
            await self.check_object_permissions(self.request, obj)
            
            return obj
        except (KeyError, AttributeError) as e:
            logger.error(f"获取对象参数错误: {str(e)}")
            raise exceptions.NotFound()
        except ObjectDoesNotExist:
            raise exceptions.NotFound()
        except Exception as e:
            logger.error(f"获取对象失败: {str(e)}")
            raise exceptions.APIException(str(e))

    async def get_filtered_queryset(self, queryset):
        """获取过滤后的查询集"""
        try:
            # 应用过滤器
            if self.filter_backends:
                for backend in self.filter_backends:
                    filter_func = sync_to_async(backend().filter_queryset)
                    queryset = await filter_func(self.request, queryset, self)
            
            return queryset
        except Exception as e:
            logger.error(f"获取过滤后的查询集失败: {str(e)}")
            raise

    async def filter_queryset(self, queryset):
        """过滤查询集"""
        try:
            # 应用所有过滤器
            for backend in list(self.filter_backends):
                backend_instance = backend()
                filter_func = sync_to_async(backend_instance.filter_queryset)
                queryset = await filter_func(self.request, queryset, self)
            return queryset
        except Exception as e:
            logger.error(f"过滤查询集失败: {str(e)}")
            return queryset

    async def paginate_queryset(self, queryset):
        """分页查询集"""
        try:
            if self.paginator is None:
                return None
            paginate_func = sync_to_async(self.paginator.paginate_queryset)
            return await paginate_func(queryset, self.request, view=self)
        except Exception as e:
            logger.error(f"分页查询集失败: {str(e)}")
            return None

    async def get_paginated_response(self, data):
        """获取分页响应"""
        try:
            assert self.paginator is not None
            paginate_func = sync_to_async(self.paginator.get_paginated_response)
            return await paginate_func(data)
        except Exception as e:
            logger.error(f"获取分页响应失败: {str(e)}")
            return Response(data)

    @property
    def paginator(self):
        """分页器属性"""
        if not hasattr(self, '_paginator'):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        return self._paginator

    def get_success_headers(self, data):
        """获取成功响应的头部信息"""
        try:
            return {'Location': str(data[api_settings.URL_FIELD_NAME])}
        except (KeyError, TypeError):
            return {}

    async def get_queryset(self):
        """获取查询集"""
        if hasattr(self, 'queryset'):
            return self.queryset
        elif hasattr(self, 'model'):
            return self.model.objects.all()
        raise NotImplementedError('get_queryset() must be implemented.')

    async def check_throttles(self, request):
        """检查限流"""
        try:
            for throttle in self.get_throttles():
                if not await sync_to_async(throttle.allow_request)(request, self):
                    self.throttled(request, throttle.wait())
        except Exception as e:
            logger.error(f"检查限流失败: {str(e)}")
            raise

    def get_throttles(self):
        """获取限流器列表"""
        return [throttle() for throttle in self.throttle_classes]

    def throttled(self, request, wait):
        """处理限流"""
        raise exceptions.Throttled(wait)

    def permission_denied(self, request):
        """处理权限拒绝"""
        if request.authenticators and not request.successful_authenticator:
            raise exceptions.NotAuthenticated()
        raise exceptions.PermissionDenied()

    def get_authenticate_header(self, request):
        """获取认证头部"""
        authenticators = self.get_authenticators()
        if authenticators:
            return authenticators[0].authenticate_header(request)

    def get_exception_handler(self):
        """获取异常处理器"""
        return api_settings.EXCEPTION_HANDLER

    def get_exception_handler_context(self):
        """获取异常处理器上下文"""
        return {
            'view': self,
            'args': getattr(self, 'args', ()),
            'kwargs': getattr(self, 'kwargs', {}),
            'request': getattr(self, 'request', None)
        }

    def get_renderer_context(self):
        """获取渲染器上下文"""
        return {
            'view': self,
            'args': getattr(self, 'args', ()),
            'kwargs': getattr(self, 'kwargs', {}),
            'request': getattr(self, 'request', None)
        }

    def get_renderers(self):
        """获取渲染器列表"""
        return [JSONRenderer()]

    @property
    def default_response_headers(self):
        """默认响应头部"""
        headers = {}
        if getattr(self, 'paginator', None) and self.paginator.is_async:
            headers['Prefer'] = 'count=exact'
        return headers

    async def http_method_not_allowed(self, request, *args, **kwargs):
        """处理不允许的HTTP方法"""
        logger.warning(f'方法 {request.method} 不被允许。')
        return Response(
            {'detail': f'方法 "{request.method}" 不被允许。'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    async def options(self, request, *args, **kwargs):
        """处理OPTIONS请求"""
        try:
            if self.metadata_class is None:
                return self.http_method_not_allowed(request, *args, **kwargs)

            data = await sync_to_async(self.metadata_class().determine_metadata)(
                request, self
            )
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"处理OPTIONS请求失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def format_response(self, response_data, status_code=status.HTTP_200_OK):
        """格式化响应数据"""
        try:
            if isinstance(response_data, Response):
                return response_data

            return Response(
                {
                    'status': 'success' if status_code < 400 else 'error',
                    'data': response_data,
                    'timestamp': timezone.now()
                },
                status=status_code
            )
        except Exception as e:
            logger.error(f"格式化响应数据失败: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'detail': str(e),
                    'timestamp': timezone.now()
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def handle_validation_error(self, exc):
        """处理验证错误"""
        try:
            return Response(
                {
                    'status': 'error',
                    'detail': exc.detail if hasattr(exc, 'detail') else str(exc),
                    'code': 'validation_error',
                    'timestamp': timezone.now()
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"处理验证错误失败: {str(e)}")
            return Response(
                {
                    'status': 'error',
                    'detail': str(e),
                    'code': 'internal_error',
                    'timestamp': timezone.now()
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_schema(self):
        """获取视图的模式信息"""
        try:
            # 获取序列化器类
            serializer_class = self.get_serializer_class()
            
            # 构建基本模式信息
            schema = {
                'name': self.__class__.__name__,
                'description': self.__doc__ or '',
                'endpoints': {}
            }
            
            # 添加支持的HTTP方法
            for method in self.http_method_names:
                if hasattr(self, method):
                    handler = getattr(self, method)
                    schema['endpoints'][method.upper()] = {
                        'description': handler.__doc__ or '',
                        'parameters': {}
                    }
            
            # 添加序列化器字段信息
            if hasattr(serializer_class, 'Meta'):
                schema['fields'] = {
                    field_name: str(field.__class__.__name__)
                    for field_name, field in serializer_class().fields.items()
                }
            
            return schema
        except Exception as e:
            logger.error(f"获取模式信息失败: {str(e)}")
            return {}

    async def get_cache_key(self, request):
        """生成缓存键"""
        try:
            # 基于请求路径和查询参数生成缓存键
            path = request.path
            query_params = str(sorted(request.query_params.items()))
            user_id = request.user.id if request.user and request.user.is_authenticated else 'anonymous'
            return f"{path}:{query_params}:{user_id}"
        except Exception as e:
            logger.error(f"生成缓存键失败: {str(e)}")
            return None

    async def get_cached_response(self, cache_key):
        """获取缓存的响应"""
        try:
            from django.core.cache import cache
            cached_data = await sync_to_async(cache.get)(cache_key)
            if cached_data is not None:
                return Response(cached_data)
            return None
        except Exception as e:
            logger.error(f"获取缓存响应失败: {str(e)}")
            return None

    async def set_cached_response(self, cache_key, response_data, timeout=300):
        """设置响应缓存"""
        try:
            from django.core.cache import cache
            if cache_key and response_data:
                await sync_to_async(cache.set)(
                    cache_key,
                    response_data,
                    timeout
                )
        except Exception as e:
            logger.error(f"设置响应缓存失败: {str(e)}")

    async def get_request_meta(self, request):
        """获取请求元信息"""
        try:
            return {
                'method': request.method,
                'path': request.path,
                'query_params': dict(request.query_params),
                'user_id': request.user.id if request.user and request.user.is_authenticated else None,
                'ip': request.META.get('REMOTE_ADDR'),
                'user_agent': request.META.get('HTTP_USER_AGENT'),
                'timestamp': timezone.now()
            }
        except Exception as e:
            logger.error(f"获取请求元信息失败: {str(e)}")
            return {}

    async def log_request(self, request, response=None, error=None, extra=None):
        """记录请求日志"""
        try:
            meta = await self.get_request_meta(request)
            log_data = {
                'meta': meta,
                'response_status': getattr(response, 'status_code', None),
                'error': str(error) if error else None,
                'extra': extra or {}
            }
            
            # 这里可以根据需要将日志写入数据库或日志文件
            logger.info(f"请求日志: {log_data}")
            
            return log_data
        except Exception as e:
            logger.error(f"记录请求日志失败: {str(e)}")
            return None

    async def check_rate_limit(self, request):
        """检查请求频率限制"""
        try:
            from django.core.cache import cache
            
            # 获取限制配置
            rate_limit = getattr(self, 'rate_limit', '60/minute')
            num, period = rate_limit.split('/')
            num = int(num)
            
            # 生成限制键
            key = f"rate_limit:{request.path}:{request.user.id if request.user else 'anonymous'}"
            
            # 获取当前计数
            count = await sync_to_async(cache.get)(key) or 0
            
            if count >= num:
                return False
            
            # 更新计数
            await sync_to_async(cache.incr)(key)
            if count == 0:
                await sync_to_async(cache.expire)(
                    key,
                    60 if period == 'minute' else 3600 if period == 'hour' else 86400
                )
            
            return True
        except Exception as e:
            logger.error(f"检查请求频率限制失败: {str(e)}")
            return True

    async def in_transaction(self, func, *args, **kwargs):
        """在事务中执行操作"""
        try:
            from django.db import transaction
            async with transaction.atomic():
                return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"事务执行失败: {str(e)}")
            raise

    async def bulk_create(self, model_class, objects, batch_size=1000):
        """批量创建对象"""
        try:
            from django.db import transaction
            
            # 分批处理
            batches = [objects[i:i + batch_size] for i in range(0, len(objects), batch_size)]
            created_objects = []
            
            async with transaction.atomic():
                for batch in batches:
                    # 使用sync_to_async包装bulk_create
                    batch_objects = await sync_to_async(model_class.objects.bulk_create)(batch)
                    created_objects.extend(batch_objects)
            
            return created_objects
        except Exception as e:
            logger.error(f"批量创建对象失败: {str(e)}")
            raise

    async def bulk_update(self, model_class, objects, fields, batch_size=1000):
        """批量更新对象"""
        try:
            from django.db import transaction
            
            # 分批处理
            batches = [objects[i:i + batch_size] for i in range(0, len(objects), batch_size)]
            
            async with transaction.atomic():
                for batch in batches:
                    # 使用sync_to_async包装bulk_update
                    await sync_to_async(model_class.objects.bulk_update)(batch, fields)
            
            return True
        except Exception as e:
            logger.error(f"批量更新对象失败: {str(e)}")
            raise

    async def get_or_create(self, model_class, defaults=None, **kwargs):
        """获取或创建对象"""
        try:
            # 使用sync_to_async包装get_or_create
            obj, created = await sync_to_async(model_class.objects.get_or_create)(
                defaults=defaults or {},
                **kwargs
            )
            return obj, created
        except Exception as e:
            logger.error(f"获取或创建对象失败: {str(e)}")
            raise

    async def update_or_create(self, model_class, defaults=None, **kwargs):
        """更新或创建对象"""
        try:
            # 使用sync_to_async包装update_or_create
            obj, created = await sync_to_async(model_class.objects.update_or_create)(
                defaults=defaults or {},
                **kwargs
            )
            return obj, created
        except Exception as e:
            logger.error(f"更新或创建对象失败: {str(e)}")
            raise

    async def safe_delete(self, instance):
        """安全删除对象"""
        try:
            # 检查是否有关联对象
            has_related = False
            for related in instance._meta.related_objects:
                related_name = related.get_accessor_name()
                if hasattr(instance, related_name):
                    related_queryset = getattr(instance, related_name)
                    count = await sync_to_async(related_queryset.count)()
                    if count > 0:
                        has_related = True
                        break
            
            if has_related:
                # 如果有关联对象，标记为删除而不是真实删除
                if hasattr(instance, 'is_deleted'):
                    instance.is_deleted = True
                    await sync_to_async(instance.save)()
                    return True, "对象已标记为删除"
                else:
                    return False, "对象有关联数据且不支持软删除"
            else:
                # 如果没有关联对象，执行真实删除
                await sync_to_async(instance.delete)()
                return True, "对象已删除"
        except Exception as e:
            logger.error(f"安全删除对象失败: {str(e)}")
            raise

    async def measure_performance(self, func_name, start_time):
        """测量性能指标"""
        try:
            end_time = timezone.now()
            duration = (end_time - start_time).total_seconds()
            
            # 记录性能指标
            from django.core.cache import cache
            
            # 更新平均响应时间
            avg_key = f"perf:avg:{func_name}"
            count_key = f"perf:count:{func_name}"
            
            current_avg = await sync_to_async(cache.get)(avg_key) or 0
            current_count = await sync_to_async(cache.get)(count_key) or 0
            
            new_count = current_count + 1
            new_avg = ((current_avg * current_count) + duration) / new_count
            
            await sync_to_async(cache.set)(avg_key, new_avg, 86400)  # 24小时过期
            await sync_to_async(cache.set)(count_key, new_count, 86400)
            
            # 记录最大响应时间
            max_key = f"perf:max:{func_name}"
            current_max = await sync_to_async(cache.get)(max_key) or 0
            if duration > current_max:
                await sync_to_async(cache.set)(max_key, duration, 86400)
            
            return {
                'duration': duration,
                'average': new_avg,
                'count': new_count
            }
        except Exception as e:
            logger.error(f"测量性能指标失败: {str(e)}")
            return None

    async def collect_metrics(self):
        """收集性能指标"""
        try:
            from django.core.cache import cache
            
            metrics = {
                'response_times': {},
                'error_rates': {},
                'request_counts': {}
            }
            
            # 获取所有性能指标
            async def get_metric(key):
                return await sync_to_async(cache.get)(key)
            
            # 收集响应时间指标
            for method in self.http_method_names:
                if hasattr(self, method):
                    avg_key = f"perf:avg:{method}"
                    max_key = f"perf:max:{method}"
                    count_key = f"perf:count:{method}"
                    
                    metrics['response_times'][method] = {
                        'average': await get_metric(avg_key),
                        'maximum': await get_metric(max_key),
                        'count': await get_metric(count_key)
                    }
            
            return metrics
        except Exception as e:
            logger.error(f"收集性能指标失败: {str(e)}")
            return None

    async def monitor_database_performance(self):
        """监控数据库性能"""
        try:
            from django.db import connection
            
            # 获取数据库连接信息
            db_info = {
                'vendor': connection.vendor,
                'queries': len(connection.queries),
                'time_spent': sum(float(q.get('time', 0)) for q in connection.queries)
            }
            
            # 获取慢查询
            slow_queries = [
                q for q in connection.queries
                if float(q.get('time', 0)) > 1.0  # 超过1秒的查询
            ]
            
            db_info['slow_queries'] = [{
                'sql': q['sql'],
                'time': float(q['time']),
                'timestamp': q.get('start_time', None)
            } for q in slow_queries]
            
            return db_info
        except Exception as e:
            logger.error(f"监控数据库性能失败: {str(e)}")
            return None

    async def analyze_request_patterns(self):
        """分析请求模式"""
        try:
            from django.core.cache import cache
            
            patterns = {
                'hourly_distribution': {},
                'method_distribution': {},
                'status_distribution': {}
            }
            
            # 获取最近的请求日志
            logs = await sync_to_async(cache.get)('request_logs') or []
            
            for log in logs:
                # 按小时统计
                hour = log['meta']['timestamp'].hour
                patterns['hourly_distribution'][hour] = patterns['hourly_distribution'].get(hour, 0) + 1
                
                # 按方法统计
                method = log['meta']['method']
                patterns['method_distribution'][method] = patterns['method_distribution'].get(method, 0) + 1
                
                # 按状态码统计
                status = log['response_status']
                patterns['status_distribution'][status] = patterns['status_distribution'].get(status, 0) + 1
            
            return patterns
        except Exception as e:
            logger.error(f"分析请求模式失败: {str(e)}")
            return None

    async def get_performance_summary(self):
        """获取性能总结"""
        try:
            # 收集性能指标
            metrics = await self.collect_metrics()
            if not metrics:
                return None
            
            # 计算总体统计
            summary = {
                'response_times': {
                    'average': {},
                    'maximum': {},
                    'total_requests': {}
                },
                'error_rates': {},
                'cache_stats': {
                    'hits': 0,
                    'misses': 0,
                    'hit_rate': 0
                }
            }
            
            # 处理响应时间数据
            for method, data in metrics['response_times'].items():
                if data['average'] is not None:
                    summary['response_times']['average'][method] = round(data['average'], 3)
                    summary['response_times']['maximum'][method] = round(data['maximum'], 3)
                    summary['response_times']['total_requests'][method] = data['count']
            
            # 获取缓存统计
            from django.core.cache import cache
            cache_hits = await sync_to_async(cache.get)('cache_hits') or 0
            cache_misses = await sync_to_async(cache.get)('cache_misses') or 0
            total_requests = cache_hits + cache_misses
            
            if total_requests > 0:
                summary['cache_stats'] = {
                    'hits': cache_hits,
                    'misses': cache_misses,
                    'hit_rate': round(cache_hits / total_requests * 100, 2)
                }
            
            return summary
        except Exception as e:
            logger.error(f"获取性能总结失败: {str(e)}")
            return None

    async def get_slow_requests(self, threshold=1.0):
        """获取慢请求列表"""
        try:
            from django.core.cache import cache
            
            # 获取请求日志
            logs = await sync_to_async(cache.get)('request_logs') or []
            
            # 筛选慢请求
            slow_requests = []
            for log in logs:
                duration = log.get('extra', {}).get('duration')
                if duration and duration > threshold:
                    slow_requests.append({
                        'path': log['meta']['path'],
                        'method': log['meta']['method'],
                        'duration': duration,
                        'timestamp': log['meta']['timestamp'],
                        'status_code': log['response_status'],
                        'db_queries': log.get('extra', {}).get('db_queries'),
                        'db_time': log.get('extra', {}).get('db_time')
                    })
            
            # 按持续时间排序
            slow_requests.sort(key=lambda x: x['duration'], reverse=True)
            
            return slow_requests
        except Exception as e:
            logger.error(f"获取慢请求列表失败: {str(e)}")
            return []

    async def get_error_summary(self):
        """获取错误总结"""
        try:
            from django.core.cache import cache
            
            # 获取请求日志
            logs = await sync_to_async(cache.get)('request_logs') or []
            
            # 统计错误
            error_summary = {
                'total_errors': 0,
                'error_types': {},
                'error_endpoints': {},
                'recent_errors': []
            }
            
            for log in logs:
                if log['error']:
                    error_summary['total_errors'] += 1
                    
                    # 统计错误类型
                    error_type = log['error'].split(':')[0]
                    error_summary['error_types'][error_type] = error_summary['error_types'].get(error_type, 0) + 1
                    
                    # 统计错误端点
                    endpoint = f"{log['meta']['method']} {log['meta']['path']}"
                    error_summary['error_endpoints'][endpoint] = error_summary['error_endpoints'].get(endpoint, 0) + 1
                    
                    # 记录最近的错误
                    if len(error_summary['recent_errors']) < 10:  # 只保留最近10个错误
                        error_summary['recent_errors'].append({
                            'error': log['error'],
                            'path': log['meta']['path'],
                            'method': log['meta']['method'],
                            'timestamp': log['meta']['timestamp'],
                            'status_code': log['response_status']
                        })
            
            return error_summary
        except Exception as e:
            logger.error(f"获取错误总结失败: {str(e)}")
            return None

    @action(detail=False, methods=['get'])
    async def performance_stats(self, request):
        """获取性能统计信息"""
        try:
            # 收集各类统计信息
            stats = {
                'performance': await self.get_performance_summary(),
                'slow_requests': await self.get_slow_requests(),
                'errors': await self.get_error_summary(),
                'request_patterns': await self.analyze_request_patterns(),
                'database': await self.monitor_database_performance(),
                'timestamp': timezone.now()
            }
            
            return Response(stats)
        except Exception as e:
            logger.error(f"获取性能统计信息失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 