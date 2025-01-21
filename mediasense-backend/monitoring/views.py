from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework import viewsets, status, exceptions
from asgiref.sync import sync_to_async
import asyncio
from django.core.exceptions import ValidationError
from django.db import models
from rest_framework.decorators import action
from .models import (
    SystemMetrics, AlertRule, AlertHistory,
    MonitoringVisualization, ErrorLog
)
from .serializers import (
    SystemMetricsSerializer, AlertRuleSerializer,
    AlertHistorySerializer, MonitoringVisualizationSerializer,
    ErrorLogSerializer
)
from django.utils import timezone
from datetime import timedelta
from .mixins import SyncAsyncViewSetMixin
from rest_framework.permissions import IsAuthenticated
from django.urls import NoReverseMatch
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from django.db.models import Avg, Count, Max, Min, Q
from rest_framework.exceptions import NotAuthenticated, PermissionDenied, NotFound, APIException
from rest_framework.request import Request
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
import logging

logger = logging.getLogger(__name__)

class AsyncAPIView(APIView):
    """异步 API 视图基类"""
    
    async def dispatch(self, request, *args, **kwargs):
        """
        处理请求分发
        """
        try:
            response = await super().dispatch(request, *args, **kwargs)
            if asyncio.iscoroutine(response):
                response = await response
            return response
        except Exception as exc:
            return self.handle_exception(exc)

class AsyncViewSet(AsyncAPIView, viewsets.ModelViewSet):
    """异步视图集基类"""
    
    renderer_classes = [JSONRenderer]
    parser_classes = [JSONParser]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    basename = None
    lookup_field = 'pk'
    lookup_url_kwarg = None
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace']
    
    default_action_map = {
        'get': 'list',
        'post': 'create',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }

    @classmethod
    def as_view(cls, actions=None, **initkwargs):
        """视图工厂方法"""
        print(f"[DEBUG] as_view called with actions: {actions}, initkwargs: {initkwargs}")
        if actions is None:
            actions = {}

        # 确保基本动作映射存在
        for method in ['get', 'post', 'put', 'patch', 'delete']:
            if method not in actions:
                if method == 'get' and 'pk' in initkwargs:
                    actions[method] = 'retrieve'
                else:
                    actions[method] = cls.default_action_map.get(method)

        # 设置lookup_url_kwarg如果存在pk
        if 'pk' in initkwargs:
            initkwargs['lookup_url_kwarg'] = 'pk'

        print(f"[DEBUG] Final actions map: {actions}")
        
        async def async_view(request, *args, **kwargs):
            print(f"[DEBUG] async_view called with request: {request.method} {request.path}")
            try:
                self = cls(**initkwargs)
                self.action_map = actions
                self.actions = actions
                self.request = request
                self.args = args
                self.kwargs = kwargs

                # 设置查询参数
                if 'pk' in kwargs:
                    self.lookup_url_kwarg = 'pk'
                    
                # 确定处理方法
                handler = None
                method = request.method.lower()
                
                if method in actions:
                    handler_name = actions[method]
                    if hasattr(self, handler_name):
                        handler = getattr(self, handler_name)
                
                if handler is None:
                    handler_name = cls.default_action_map.get(method)
                    if hasattr(self, handler_name):
                        handler = getattr(self, handler_name)
                
                if handler is None:
                    print(f"[DEBUG] No handler found for method: {method}")
                    raise exceptions.MethodNotAllowed(method)

                print(f"[DEBUG] Handler found: {handler.__name__}")
                
                # 初始化请求
                request = await self.initialize_request(request, *args, **kwargs)
                
                # 执行初始化检查
                await self.initial(request, *args, **kwargs)
                
                # 调用处理方法
                response = await handler(request, *args, **kwargs)
                if asyncio.iscoroutine(response):
                    response = await response
                
                # 确保返回 HttpResponse 对象
                if not isinstance(response, HttpResponse):
                    if isinstance(response, dict):
                        response = Response(response)
                    elif response is None:
                        response = Response(status=status.HTTP_204_NO_CONTENT)
                    else:
                        response = Response(response)
                
                print(f"[DEBUG] Response status code: {response.status_code}")
                return response
            except Exception as e:
                print(f"[DEBUG] Error in async_view: {str(e)}")
                raise

        return async_view

    async def initialize_request(self, request, *args, **kwargs):
        """
        初始化请求
        """
        if isinstance(request, Request):
            return request
        
        request = await super().initialize_request(request, *args, **kwargs)
        return request
    
    async def initial(self, request, *args, **kwargs):
        """
        初始化处理
        """
        await super().initial(request, *args, **kwargs)
        
        # 认证检查
        if not request.user.is_authenticated:
            raise NotAuthenticated()
        
        # 权限检查
        if not self.has_permission(request, self.action):
            raise PermissionDenied()
    
    async def dispatch(self, request, *args, **kwargs):
        """
        处理请求分发
        """
        try:
            response = await super().dispatch(request, *args, **kwargs)
            if asyncio.iscoroutine(response):
                response = await response
            return response
        except Exception as exc:
            return self.handle_exception(exc)
    
    def get_queryset(self):
        """
        获取查询集
        """
        return self.queryset.filter(created_by=self.request.user)
    
    def perform_create(self, serializer):
        """
        执行创建
        """
        serializer.save(created_by=self.request.user)

    async def get_object(self):
        """获取单个对象"""
        print(f"[DEBUG] Getting object with lookup: {self.lookup_field}={self.kwargs.get(self.lookup_url_kwarg)}")
        queryset = await self.get_queryset()
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        
        for obj in queryset:
            if str(getattr(obj, self.lookup_field)) == str(filter_kwargs[self.lookup_field]):
                print(f"[DEBUG] Object found: {obj}")
                return obj
        print(f"[DEBUG] No object found")
        raise Http404("No object found matching this query")

    async def list(self, request, *args, **kwargs):
        """列表视图"""
        queryset = await self.get_queryset()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)
    
    async def create(self, request, *args, **kwargs):
        """创建视图"""
        serializer = self.serializer_class(data=request.data)
        if not await sync_to_async(serializer.is_valid)():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        instance = await sync_to_async(serializer.save)(created_by=request.user)
        return Response(self.serializer_class(instance).data, status=status.HTTP_201_CREATED)

    async def retrieve(self, request, *args, **kwargs):
        """检索视图"""
        instance = await self.get_object()
        serializer = self.serializer_class(instance)
        return Response(serializer.data)
    
    async def update(self, request, *args, **kwargs):
        """更新视图"""
        instance = await self.get_object()
        serializer = self.serializer_class(instance, data=request.data, partial=True)
        if not await sync_to_async(serializer.is_valid)():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        instance = await sync_to_async(serializer.save)()
        return Response(self.serializer_class(instance).data)

    async def destroy(self, request, *args, **kwargs):
        """删除视图"""
        instance = await self.get_object()
        await sync_to_async(instance.delete)()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    async def get(self, request, *args, **kwargs):
        """GET 请求"""
        if self.lookup_url_kwarg and self.lookup_url_kwarg in kwargs:
            return await self.retrieve(request, *args, **kwargs)
        return await self.list(request, *args, **kwargs)

    async def post(self, request, *args, **kwargs):
        """POST 请求"""
        if self.action in self.actions:
            handler = getattr(self, self.action)
            return await handler(request, *args, **kwargs)
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

    def get_handler(self, request):
        """
        获取请求处理方法
        """
        method = request.method.lower()
        
        # 从action_map中获取action
        if method in self.action_map:
            self.action = self.action_map[method]
        else:
            self.action = self.default_action_map.get(method)
            
        print(f"[DEBUG] Action determined: {self.action}")
        print(f"[DEBUG] Action map: {self.action_map}")
        print(f"[DEBUG] Default action map: {self.default_action_map}")
        
        # 获取处理函数
        handler = None
        if self.action:
            if hasattr(self, self.action):
                handler = getattr(self, self.action)
            else:
                handler = getattr(self, method, None)
        else:
            handler = getattr(self, method, None)
            
        if handler is None:
            print(f"[DEBUG] No handler found for action: {self.action}")
            print(f"[DEBUG] Available methods: {dir(self)}")
            
        return handler

    @classmethod
    def get_extra_actions(cls):
        """获取额外的动作"""
        return []

    def get_view_name(self):
        """获取视图名称"""
        name = self.__class__.__name__
        name = ''.join([i.title() for i in name.split('_')])
        if name.endswith('ViewSet'):
            name = name[:-7]
        return name

    def get_view_description(self, html=False):
        """获取视图描述"""
        return self.__class__.__doc__ or ''

class SystemMetricsViewSet(AsyncViewSet):
    """系统指标视图集"""
    serializer_class = SystemMetricsSerializer
    queryset = SystemMetrics.objects.all()
    lookup_field = 'id'
    
    @action(detail=False, methods=['get'])
    async def aggregate(self, request):
        """聚合系统指标"""
        try:
            # 获取时间范围
            end_time = timezone.now()
            start_time = end_time - timedelta(hours=24)

            # 获取指标数据
            metrics = await sync_to_async(SystemMetrics.objects.filter)(
                timestamp__range=(start_time, end_time)
            )

            # 计算聚合值
            aggregates = {
                'cpu_usage': await sync_to_async(metrics.aggregate)(Avg('cpu_usage')),
                'memory_usage': await sync_to_async(metrics.aggregate)(Avg('memory_usage')),
                'disk_usage': await sync_to_async(metrics.aggregate)(Avg('disk_usage')),
                'network_io': await sync_to_async(metrics.aggregate)(Avg('network_io')),
            }

            return Response({
                'start_time': start_time,
                'end_time': end_time,
                'aggregates': aggregates
            })
        except Exception as e:
            logger.error(f"Error in aggregate metrics: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Failed to aggregate metrics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AlertRuleViewSet(AsyncViewSet):
    """告警规则视图集"""
    serializer_class = AlertRuleSerializer
    queryset = AlertRule.objects.all()
    lookup_field = 'id'
    
    @action(detail=True, methods=['post'])
    async def enable(self, request, *args, **kwargs):
        """启用告警规则"""
        instance = await self.get_object()
        instance.is_enabled = True
        await sync_to_async(instance.save)()
        return Response(self.serializer_class(instance).data)
    
    @action(detail=True, methods=['post'])
    async def disable(self, request, *args, **kwargs):
        """禁用告警规则"""
        instance = await self.get_object()
        instance.is_enabled = False
        await sync_to_async(instance.save)()
        return Response(self.serializer_class(instance).data)

class AlertHistoryViewSet(AsyncViewSet):
    """告警历史视图集"""
    serializer_class = AlertHistorySerializer
    queryset = AlertHistory.objects.all()
    lookup_field = 'id'
    
    @action(detail=True, methods=['post'])
    async def notify(self, request, *args, **kwargs):
        """发送告警通知"""
        instance = await self.get_object()
        # 在这里实现告警通知的逻辑
        return Response({'status': 'notification sent'})
    
    @action(detail=True, methods=['post'])
    async def acknowledge(self, request, *args, **kwargs):
        """确认告警"""
        instance = await self.get_object()
        instance.status = 'acknowledged'
        instance.acknowledged_at = timezone.now()
        await sync_to_async(instance.save)()
        return Response(self.serializer_class(instance).data)
    
    @action(detail=True, methods=['post'])
    async def resolve(self, request, *args, **kwargs):
        """解决告警"""
        instance = await self.get_object()
        instance.status = 'resolved'
        instance.resolved_at = timezone.now()
        await sync_to_async(instance.save)()
        return Response(self.serializer_class(instance).data)

class MonitoringVisualizationViewSet(AsyncViewSet):
    """监控可视化视图集"""
    serializer_class = MonitoringVisualizationSerializer
    queryset = MonitoringVisualization.objects.all()
    lookup_field = 'id'
    
    @action(detail=True, methods=['get'])
    async def data(self, request, *args, **kwargs):
        """获取可视化数据"""
        instance = await self.get_object()
        metrics = await sync_to_async(list)(
            SystemMetrics.objects.filter(
                timestamp__gte=timezone.now() - timedelta(hours=instance.time_range)
            )
        )
        
        data = []
        for metric in metrics:
            data.append({
                'timestamp': metric.timestamp,
                'value': metric.value,
                'type': metric.metric_type
            })
        
        return Response(data)

class ErrorLogViewSet(AsyncViewSet):
    """错误日志视图集"""
    serializer_class = ErrorLogSerializer
    queryset = ErrorLog.objects.all()
    lookup_field = 'id'
    
    @action(detail=False, methods=['get'])
    async def statistics(self, request):
        """获取错误日志统计信息"""
        one_day_ago = timezone.now() - timedelta(days=1)
        queryset = await sync_to_async(list)(
            ErrorLog.objects.filter(
                timestamp__gte=one_day_ago
            )
        )
        
        stats = {
            'total_count': len(queryset),
            'error_count': len([log for log in queryset if log.severity == 'ERROR']),
            'warning_count': len([log for log in queryset if log.severity == 'WARNING']),
            'info_count': len([log for log in queryset if log.severity == 'INFO'])
        }
        
        return Response(stats)

class SystemStatusViewSet(AsyncViewSet):
    """系统状态视图集"""
    serializer_class = SystemMetricsSerializer
    queryset = SystemMetrics.objects.all()
    lookup_field = 'id'
    
    @action(detail=False, methods=['get'])
    async def health(self, request):
        """获取系统健康状态"""
        try:
            metrics = await sync_to_async(list)(
                SystemMetrics.objects.filter(
                    timestamp__gte=timezone.now() - timedelta(minutes=5)
                )
            )
            
            if not metrics:
                return Response({
                    'status': 'unknown',
                    'message': 'No recent metrics available'
                })
            
            latest_metric = max(metrics, key=lambda m: m.timestamp)
            status = 'healthy'
            message = 'System is operating normally'
            
            return Response({
                'status': status,
                'message': message,
                'latest_check': latest_metric.timestamp.isoformat(),
                'metrics': {
                    'cpu': latest_metric.cpu_usage,
                    'memory': latest_metric.memory_usage,
                    'disk': latest_metric.disk_usage,
                    'network': latest_metric.network_usage
                }
            })
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    async def overview(self, request):
        """获取系统概览"""
        metrics = await sync_to_async(list)(
            SystemMetrics.objects.filter(
                timestamp__gte=timezone.now() - timedelta(hours=1)
            )
        )
        
        if not metrics:
            return Response({
                'cpu': {'current': 0, 'trend': []},
                'memory': {'current': 0, 'trend': []},
                'disk': {'current': 0, 'trend': []},
                'network': {'current': 0, 'trend': []}
            })
        
        latest_metric = max(metrics, key=lambda m: m.timestamp)
        trend_data = {
            'cpu': [{'timestamp': m.timestamp, 'value': m.cpu_usage} for m in metrics],
            'memory': [{'timestamp': m.timestamp, 'value': m.memory_usage} for m in metrics],
            'disk': [{'timestamp': m.timestamp, 'value': m.disk_usage} for m in metrics],
            'network': [{'timestamp': m.timestamp, 'value': m.network_usage} for m in metrics]
        }
        
        return Response({
            'cpu': {
                'current': latest_metric.cpu_usage,
                'trend': trend_data['cpu']
            },
            'memory': {
                'current': latest_metric.memory_usage,
                'trend': trend_data['memory']
            },
            'disk': {
                'current': latest_metric.disk_usage,
                'trend': trend_data['disk']
            },
            'network': {
                'current': latest_metric.network_usage,
                'trend': trend_data['network']
            }
        })
    
    @action(detail=False, methods=['get'])
    async def performance(self, request):
        """获取性能指标"""
        metrics = await sync_to_async(list)(
            SystemMetrics.objects.filter(
                timestamp__gte=timezone.now() - timedelta(hours=24)
            )
        )
        
        if not metrics:
            return Response({
                'cpu_usage_avg': 0,
                'memory_usage_avg': 0,
                'disk_usage_avg': 0,
                'network_usage_avg': 0,
                'peak_cpu_usage': 0,
                'peak_memory_usage': 0,
                'peak_disk_usage': 0,
                'peak_network_usage': 0
            })
        
        stats = {
            'cpu_usage_avg': sum(m.cpu_usage for m in metrics) / len(metrics),
            'memory_usage_avg': sum(m.memory_usage for m in metrics) / len(metrics),
            'disk_usage_avg': sum(m.disk_usage for m in metrics) / len(metrics),
            'network_usage_avg': sum(m.network_usage for m in metrics) / len(metrics),
            'peak_cpu_usage': max(m.cpu_usage for m in metrics),
            'peak_memory_usage': max(m.memory_usage for m in metrics),
            'peak_disk_usage': max(m.disk_usage for m in metrics),
            'peak_network_usage': max(m.network_usage for m in metrics)
        }
        
        return Response(stats)
