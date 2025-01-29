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

    async def dispatch(self, request, *args, **kwargs):
        """处理请求调度"""
        try:
            self.args = args
            self.kwargs = kwargs
            
            request = await self.initialize_request(request, *args, **kwargs)
            self.request = request
            self.headers = self.default_response_headers

            await self.initial(request, *args, **kwargs)
            handler = await self.get_handler(request, *args, **kwargs)
            
            if handler is None:
                handler = self.http_method_not_allowed
            
            response = await handler(request, *args, **kwargs)
            return await self.finalize_response(request, response, *args, **kwargs)
        except Exception as exc:
            return await self.handle_exception(exc)

    async def initialize_request(self, request, *args, **kwargs):
        """初始化请求"""
        try:
            if not hasattr(request, 'data'):
                request.data = {}
            return request
        except Exception as e:
            logger.error(f"初始化请求失败: {str(e)}")
            raise

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
        try:
            await self.perform_authentication(request)
            await self.check_permissions(request)
            await self.check_throttles(request)
        except Exception as e:
            logger.error(f"初始化操作失败: {str(e)}")
            raise

    async def finalize_response(self, request, response, *args, **kwargs):
        """完成响应处理"""
        try:
            if isinstance(response, HttpResponseBase):
                return response

            if not isinstance(response, Response):
                response = Response(response)

            response.accepted_renderer = self.get_renderers()[0]
            response.accepted_media_type = self.get_content_negotiator().select_renderer(
                request, self.get_renderers(), self.get_parser_context(request)
            )[0]
            response.renderer_context = self.get_renderer_context()

            return response
        except Exception as e:
            logger.error(f"完成响应处理失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def handle_exception(self, exc):
        """处理异常"""
        try:
            if isinstance(exc, (exceptions.NotAuthenticated,
                            exceptions.AuthenticationFailed)):
                auth_header = await self.get_authenticate_header(self.request)
                if auth_header:
                    exc.auth_header = auth_header
                else:
                    exc.status_code = status.HTTP_403_FORBIDDEN

            # 获取异常处理器
            handler = self.get_exception_handler()
            context = self.get_exception_handler_context()

            # 处理异常
            if handler is not None:
                response = await sync_to_async(handler)(exc, context)
            else:
                response = None

            if response is None:
                raise exc

            response.exception = True
            return response

        except Exception as e:
            logger.error(f"处理异常失败: {str(e)}")
            return Response(
                {'detail': str(exc)},
                status=getattr(exc, 'status_code', status.HTTP_500_INTERNAL_SERVER_ERROR)
            )

    async def list(self, request, *args, **kwargs):
        """列出对象"""
        try:
            queryset = await self.get_filtered_queryset()
            if queryset is None:
                return Response([])
                
            queryset = await self.filter_queryset(queryset)
            
            # 处理分页
            page = await self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return await self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"列出对象失败: {str(e)}")
            raise

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

    async def retrieve(self, request, *args, **kwargs):
        """获取单个对象"""
        try:
            instance = await self.get_object()
            await self.check_object_permissions(request, instance)
            
            try:
                serializer = self.get_serializer(instance)
                return Response(serializer.data)
            except Exception as e:
                logger.error(f"序列化对象失败: {str(e)}")
                raise
        except Http404:
            raise
        except Exception as e:
            logger.error(f"获取对象失败: {str(e)}")
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
            # 获取过滤后的查询集
            queryset = await self.get_filtered_queryset()
            if queryset is None:
                raise Http404("未找到查询集")

            # 获取查找参数
            lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
            if lookup_url_kwarg not in self.kwargs:
                raise AssertionError(
                    f'视图 {self.__class__.__name__} 需要一个名为 "{lookup_url_kwarg}" 的URL关键字参数。'
                    f'请检查URL配置，或正确设置视图的 lookup_field 属性。'
                )

            # 构建过滤条件
            filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
            
            try:
                # 在查询集中查找对象
                if isinstance(queryset, models.QuerySet):
                    # 如果是QuerySet，使用get方法
                    obj = await sync_to_async(queryset.get)(**filter_kwargs)
                else:
                    # 如果是列表，手动查找
                    for obj in queryset:
                        if str(getattr(obj, self.lookup_field)) == str(filter_kwargs[self.lookup_field]):
                            return obj
                    raise models.ObjectDoesNotExist("未找到匹配的对象")
                return obj
            except models.ObjectDoesNotExist:
                raise Http404("未找到匹配的对象")
            except Exception as e:
                logger.error(f"查找对象失败: {str(e)}")
                raise
        except Exception as e:
            logger.error(f"获取对象失败: {str(e)}")
            raise

    async def get_filtered_queryset(self):
        """获取过滤后的查询集"""
        try:
            # 获取基础查询集
            queryset = await self.get_queryset()
            
            # 如果是QuerySet对象，转换为列表
            if isinstance(queryset, models.QuerySet):
                queryset = await sync_to_async(lambda: list(queryset.all()))()
            
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
                filter_func = sync_to_async(backend().filter_queryset)
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