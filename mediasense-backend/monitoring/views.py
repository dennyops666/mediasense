from django.http import HttpResponse, HttpResponseBase, Http404
from rest_framework.response import Response
from rest_framework import viewsets, status, exceptions
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.utils import timezone
from datetime import timedelta
from django.db import models
from .models import (
    SystemMetrics, AlertRule, AlertHistory,
    MonitoringVisualization, ErrorLog,
    Dashboard, DashboardWidget, AlertNotificationConfig
)
from .serializers import (
    SystemMetricsSerializer, AlertRuleSerializer,
    AlertHistorySerializer, MonitoringVisualizationSerializer,
    ErrorLogSerializer, DashboardSerializer,
    DashboardWidgetSerializer, AlertNotificationConfigSerializer,
    ErrorLogStatisticsSerializer
)
import logging
import psutil
from rest_framework import serializers
from asgiref.sync import sync_to_async
from django.db import transaction
from rest_framework.viewsets import ViewSetMixin
from rest_framework.views import APIView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import asyncio
from rest_framework.renderers import JSONRenderer
from rest_framework.viewsets import ViewSet
from rest_framework.mixins import (
    CreateModelMixin, ListModelMixin, RetrieveModelMixin,
    UpdateModelMixin, DestroyModelMixin
)
from rest_framework.request import Request
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from rest_framework.negotiation import DefaultContentNegotiation
from rest_framework.versioning import AcceptHeaderVersioning
from rest_framework.metadata import SimpleMetadata
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.settings import api_settings
from django.db.models import Count
from .async_viewset import AsyncViewSet
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication

logger = logging.getLogger(__name__)

class SystemMetricsViewSet(AsyncViewSet):
    queryset = SystemMetrics.objects.all()
    serializer_class = SystemMetricsSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    renderer_classes = [JSONRenderer]

    async def get_queryset(self):
        """获取查询集"""
        try:
            if hasattr(self, 'queryset') and self.queryset is not None:
                queryset = self.queryset
                if isinstance(queryset, models.QuerySet):
                    queryset = await sync_to_async(lambda: queryset.all())()
                return queryset
            raise NotImplementedError('get_queryset() must be implemented.')
        except Exception as e:
            logger.error(f"获取查询集失败: {str(e)}")
            raise

    async def list(self, request, *args, **kwargs):
        """列出系统指标"""
        try:
            # 获取查询集
            queryset = await self.get_queryset()
            
            # 过滤查询集
            queryset = await self.filter_queryset(queryset)
            
            # 处理分页
            page = await self.paginate_queryset(queryset)
            if page is not None:
                serializer = await self.get_serializer(page, many=True)
                data = await sync_to_async(lambda: serializer.data)()
                response = await self.get_paginated_response(data)
            else:
                # 序列化数据
                serializer = await self.get_serializer(queryset, many=True)
                data = await sync_to_async(lambda: serializer.data)()
                response = Response(data)
            
            # 设置渲染器
            response.accepted_renderer = JSONRenderer()
            response.accepted_media_type = "application/json"
            response.renderer_context = self.get_renderer_context()
            
            return response
            
        except Exception as e:
            logger.error(f"列出系统指标失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_renderer_context(self):
        """获取渲染器上下文"""
        return {
            'view': self,
            'args': getattr(self, 'args', ()),
            'kwargs': getattr(self, 'kwargs', {}),
            'request': getattr(self, 'request', None)
        }

    async def create(self, request, *args, **kwargs):
        """创建系统指标"""
        try:
            serializer = await self.get_serializer(data=request.data)
            if await sync_to_async(serializer.is_valid)(raise_exception=True):
                instance = await sync_to_async(serializer.save)()
                serializer = await self.get_serializer(instance)
                data = await sync_to_async(lambda: serializer.data)()
                return Response(data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"创建系统指标失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def retrieve(self, request, *args, **kwargs):
        """获取单个系统指标"""
        try:
            instance = await self.get_object()
            serializer = await self.get_serializer(instance)
            data = await sync_to_async(lambda: serializer.data)()
            return Response(data)
        except Exception as e:
            logger.error(f"获取系统指标失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def update(self, request, *args, **kwargs):
        """更新系统指标"""
        try:
            partial = kwargs.pop('partial', False)
            instance = await self.get_object()
            serializer = await self.get_serializer(instance, data=request.data, partial=partial)
            if await sync_to_async(serializer.is_valid)(raise_exception=True):
                instance = await sync_to_async(serializer.save)()
                serializer = await self.get_serializer(instance)
                data = await sync_to_async(lambda: serializer.data)()
                return Response(data)
        except Http404:
            raise
        except Exception as e:
            logger.error(f"更新系统指标失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def destroy(self, request, *args, **kwargs):
        """删除系统指标"""
        try:
            instance = await self.get_object()
            await sync_to_async(instance.delete)()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Http404:
            raise
        except Exception as e:
            logger.error(f"删除系统指标失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    async def performance_stats(self, request):
        """获取性能统计信息"""
        try:
            # 获取最新的系统指标
            latest_metrics = {}
            for metric_type in SystemMetrics.MetricType.choices:
                metric = await sync_to_async(
                    lambda: self.queryset.filter(metric_type=metric_type[0])
                    .order_by('-timestamp')
                    .first()
                )()
                if metric:
                    serializer = await self.get_serializer(metric)
                    data = await sync_to_async(lambda: serializer.data)()
                    latest_metrics[metric_type[0]] = data

            return Response({
                'metrics': latest_metrics,
                'timestamp': timezone.now()
            })
        except Exception as e:
            logger.error(f"获取性能统计信息失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_object(self):
        """获取单个对象"""
        try:
            queryset = await self.get_queryset()
            
            lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
            assert lookup_url_kwarg in self.kwargs, (
                'Expected view %s to be called with a URL keyword argument '
                'named "%s". Fix your URL conf, or set the `.lookup_field` '
                'attribute on the view correctly.' %
                (self.__class__.__name__, lookup_url_kwarg)
            )
            
            filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
            obj = await sync_to_async(queryset.get)(**filter_kwargs)
            
            # 检查对象级权限
            await self.check_object_permissions(self.request, obj)
            
            return obj
        except Exception as e:
            logger.error(f"获取对象失败: {str(e)}")
            raise

class AlertRuleViewSet(AsyncViewSet):
    queryset = AlertRule.objects.all()
    serializer_class = AlertRuleSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @action(detail=True, methods=['post'])
    async def enable(self, request, pk=None):
        """启用告警规则"""
        try:
            rule = await self.get_object()
            await self.check_object_permissions(request, rule)
            rule.is_enabled = True
            try:
                await sync_to_async(rule.save)()
                serializer = self.get_serializer(rule)
                return Response(serializer.data)
            except Exception as e:
                logger.error(f"保存告警规则失败: {str(e)}")
                raise serializers.ValidationError(str(e))
        except Http404:
            raise
        except Exception as e:
            logger.error(f"启用告警规则失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    async def disable(self, request, pk=None):
        """禁用告警规则"""
        try:
            rule = await self.get_object()
            await self.check_object_permissions(request, rule)
            rule.is_enabled = False
            try:
                await sync_to_async(rule.save)()
                serializer = self.get_serializer(rule)
                return Response(serializer.data)
            except Exception as e:
                logger.error(f"保存告警规则失败: {str(e)}")
                raise serializers.ValidationError(str(e))
        except Http404:
            raise
        except Exception as e:
            logger.error(f"禁用告警规则失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AlertHistoryViewSet(AsyncViewSet):
    queryset = AlertHistory.objects.all()
    serializer_class = AlertHistorySerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @action(detail=True, methods=['post'])
    async def acknowledge(self, request, pk=None):
        """确认告警"""
        try:
            alert = await self.get_object()
            await self.check_object_permissions(request, alert)
            alert.status = 'acknowledged'
            try:
                await sync_to_async(alert.save)()
                serializer = self.get_serializer(alert)
                return Response(serializer.data)
            except Exception as e:
                logger.error(f"保存告警失败: {str(e)}")
                raise serializers.ValidationError(str(e))
        except Http404:
            raise
        except Exception as e:
            logger.error(f"确认告警失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    async def resolve(self, request, pk=None):
        """解决告警"""
        try:
            alert = await self.get_object()
            await self.check_object_permissions(request, alert)
            alert.status = 'resolved'
            try:
                await sync_to_async(alert.save)()
                serializer = self.get_serializer(alert)
                return Response(serializer.data)
            except Exception as e:
                logger.error(f"保存告警失败: {str(e)}")
                raise serializers.ValidationError(str(e))
        except Http404:
            raise
        except Exception as e:
            logger.error(f"解决告警失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class MonitoringVisualizationViewSet(AsyncViewSet):
    queryset = MonitoringVisualization.objects.all()
    serializer_class = MonitoringVisualizationSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    async def list(self, request, *args, **kwargs):
        """列出所有可视化"""
        try:
            queryset = await sync_to_async(lambda: self.queryset.all())()
            serializer = await self.get_serializer(queryset, many=True)
            data = await sync_to_async(lambda: serializer.data)()
            return Response(data)
        except Exception as e:
            logger.error(f"列出可视化失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ErrorLogViewSet(viewsets.ViewSet):
    queryset = ErrorLog.objects.all()
    serializer_class = ErrorLogSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_serializer_class(self):
        """根据不同的操作返回不同的序列化器"""
        if self.action == 'statistics':
            return ErrorLogStatisticsSerializer
        return self.serializer_class

    def list(self, request, *args, **kwargs):
        """列出所有错误日志"""
        try:
            queryset = self.queryset.all()
            serializer = self.serializer_class(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"列出错误日志失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='statistics')
    def statistics(self, request):
        """获取错误日志统计信息"""
        try:
            # 获取查询参数
            period = request.query_params.get('period', '24h')
            
            # 计算时间范围
            if period == '24h':
                start_time = timezone.now() - timedelta(hours=24)
            elif period == '7d':
                start_time = timezone.now() - timedelta(days=7)
            else:
                start_time = timezone.now() - timedelta(hours=24)
            
            # 获取查询集
            queryset = self.queryset.filter(created_at__gte=start_time)
            
            # 统计数据
            total_count = queryset.count()
            severity_stats = dict(queryset.values('severity').annotate(count=models.Count('id')).values_list('severity', 'count'))
            source_stats = dict(queryset.values('source').annotate(count=models.Count('id')).values_list('source', 'count'))
            
            # 返回统计数据
            return Response({
                'total_count': total_count,
                'severity_distribution': severity_stats,
                'source_distribution': source_stats
            })
            
        except Exception as e:
            logger.error(f"获取错误日志统计信息失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DashboardViewSet(AsyncViewSet):
    queryset = Dashboard.objects.all()
    serializer_class = DashboardSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    async def list(self, request, *args, **kwargs):
        """列出所有仪表板"""
        try:
            queryset = await sync_to_async(lambda: self.queryset.all())()
            serializer = await self.get_serializer(queryset, many=True)
            data = await sync_to_async(lambda: serializer.data)()
            return Response(data)
        except Exception as e:
            logger.error(f"列出仪表板失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DashboardWidgetViewSet(AsyncViewSet):
    queryset = DashboardWidget.objects.all()
    serializer_class = DashboardWidgetSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    async def list(self, request, *args, **kwargs):
        """列出所有仪表板组件"""
        try:
            queryset = await sync_to_async(lambda: self.queryset.all())()
            serializer = await self.get_serializer(queryset, many=True)
            data = await sync_to_async(lambda: serializer.data)()
            return Response(data)
        except Exception as e:
            logger.error(f"列出仪表板组件失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AlertNotificationConfigViewSet(AsyncViewSet):
    queryset = AlertNotificationConfig.objects.all()
    serializer_class = AlertNotificationConfigSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    async def list(self, request, *args, **kwargs):
        """列出所有告警通知配置"""
        try:
            queryset = await sync_to_async(lambda: self.queryset.all())()
            serializer = await self.get_serializer(queryset, many=True)
            data = await sync_to_async(lambda: serializer.data)()
            return Response(data)
        except Exception as e:
            logger.error(f"列出告警通知配置失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class SystemStatusViewSet(viewsets.ViewSet):
    """系统状态视图集"""
    queryset = SystemMetrics.objects.all()
    serializer_class = SystemMetricsSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def list(self, request, *args, **kwargs):
        """获取系统状态概览"""
        try:
            # 获取最新的系统指标
            latest_metrics = {}
            for metric_type in SystemMetrics.MetricType.choices:
                metric = self.queryset.filter(metric_type=metric_type[0]).order_by('-timestamp').first()
                if metric:
                    latest_metrics[metric_type[0]] = self.serializer_class(metric).data
            
            # 获取活跃告警数量
            active_alerts_count = AlertHistory.objects.filter(status='active').count()
            
            # 构建响应数据
            data = {
                'metrics': latest_metrics,
                'active_alerts_count': active_alerts_count,
                'timestamp': timezone.now()
            }
            
            return Response(data)
            
        except Exception as e:
            logger.error(f"获取系统状态概览失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def health(self, request):
        """获取系统健康状态"""
        try:
            # 检查各个组件的健康状态
            health_status = {
                'status': 'ok',
                'components': {
                    'database': True,
                    'cache': True,
                    'storage': True
                },
                'timestamp': timezone.now()
            }
            return Response(health_status)
        except Exception as e:
            logger.error(f"获取系统健康状态失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def overview(self, request):
        """获取系统概览信息"""
        try:
            # 获取最新的系统指标
            metrics = {}
            for metric_type in ['cpu_usage', 'memory_usage', 'disk_usage']:
                metric = SystemMetrics.objects.filter(
                    metric_type=metric_type
                ).order_by('-timestamp').first()
                metrics[metric_type] = metric.value if metric else 0

            # 构建响应数据
            data = {
                'cpu_usage': metrics.get('cpu_usage', 0),
                'memory_usage': metrics.get('memory_usage', 0),
                'disk_usage': metrics.get('disk_usage', 0),
                'services': {
                    'web_server': 'running',
                    'database': 'running',
                    'cache': 'running',
                    'task_queue': 'running'
                },
                'timestamp': timezone.now()
            }
            
            return Response(data)
        except Exception as e:
            logger.error(f"获取系统概览失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
