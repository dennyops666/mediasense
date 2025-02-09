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
from django.db.models import Count, Avg, Max
from .async_viewset import AsyncViewSet
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication

logger = logging.getLogger(__name__)

class AsyncViewSet(viewsets.ModelViewSet):
    """异步视图集基类"""
    
    async def get_queryset(self):
        """获取异步查询集"""
        return await sync_to_async(super().get_queryset)()

    async def get_object(self):
        """获取异步对象"""
        return await sync_to_async(super().get_object)()

    async def get_serializer(self, *args, **kwargs):
        """获取异步序列化器"""
        return await sync_to_async(super().get_serializer)(*args, **kwargs)

    async def perform_create(self, serializer):
        """异步创建对象"""
        return await sync_to_async(serializer.save)()

    async def perform_update(self, serializer):
        """异步更新对象"""
        return await sync_to_async(serializer.save)()

    async def perform_destroy(self, instance):
        """异步删除对象"""
        return await sync_to_async(instance.delete)()

    async def list(self, request, *args, **kwargs):
        """列出所有对象"""
        try:
            queryset = await self.get_queryset()
            serializer = await self.get_serializer(queryset, many=True)
            data = await sync_to_async(lambda: serializer.data)()
            return Response(data)
        except Exception as e:
            logger.error(f"列出对象失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def retrieve(self, request, *args, **kwargs):
        """获取单个对象"""
        try:
            instance = await self.get_object()
            serializer = await self.get_serializer(instance)
            data = await sync_to_async(lambda: serializer.data)()
            return Response(data)
        except Exception as e:
            logger.error(f"获取对象失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def create(self, request, *args, **kwargs):
        """创建对象"""
        try:
            serializer = await self.get_serializer(data=request.data)
            if await sync_to_async(serializer.is_valid)():
                await self.perform_create(serializer)
                data = await sync_to_async(lambda: serializer.data)()
                return Response(data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"创建对象失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def update(self, request, *args, **kwargs):
        """更新对象"""
        try:
            instance = await self.get_object()
            serializer = await self.get_serializer(instance, data=request.data)
            if await sync_to_async(serializer.is_valid)():
                await self.perform_update(serializer)
                data = await sync_to_async(lambda: serializer.data)()
                return Response(data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
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
            await self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"删除对象失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class SystemMetricsViewSet(viewsets.ModelViewSet):
    queryset = SystemMetrics.objects.all()
    serializer_class = SystemMetricsSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    renderer_classes = [JSONRenderer]

    def list(self, request, *args, **kwargs):
        """列出系统指标"""
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"列出系统指标失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def retrieve(self, request, *args, **kwargs):
        """获取单个系统指标"""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"获取系统指标失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def performance_stats(self, request):
        """获取性能统计信息"""
        try:
            # 获取最新的系统指标
            latest_metrics = {}
            for metric_type in SystemMetrics.MetricType.choices:
                metric = self.queryset.filter(metric_type=metric_type[0]).order_by('-created_at').first()
                if metric:
                    latest_metrics[metric_type[0]] = {
                        'value': round(metric.value, 2),
                        'created_at': metric.created_at.isoformat()
                    }
                else:
                    latest_metrics[metric_type[0]] = None

            # 获取24小时内的平均值
            last_24h = timezone.now() - timedelta(hours=24)
            avg_metrics = {}
            max_metrics = {}
            
            for metric_type in SystemMetrics.MetricType.choices:
                metrics_24h = self.queryset.filter(
                    metric_type=metric_type[0],
                    created_at__gte=last_24h
                )
                
                if metrics_24h.exists():
                    # 计算平均值
                    avg = metrics_24h.aggregate(avg_value=Avg('value'))
                    avg_metrics[metric_type[0]] = round(avg['avg_value'], 2)
                    
                    # 计算最大值
                    max_val = metrics_24h.aggregate(max_value=Max('value'))
                    max_metrics[metric_type[0]] = round(max_val['max_value'], 2)
                else:
                    avg_metrics[metric_type[0]] = None
                    max_metrics[metric_type[0]] = None

            response_data = {
                'current_metrics': latest_metrics,
                'average_24h': avg_metrics,
                'max_24h': max_metrics,
                'timestamp': timezone.now().isoformat(),
                'metric_types': {
                    metric_type[0]: metric_type[1] 
                    for metric_type in SystemMetrics.MetricType.choices
                }
            }

            return Response(response_data)
        except Exception as e:
            logger.error(f"获取性能统计信息失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AlertRuleViewSet(viewsets.ModelViewSet):
    queryset = AlertRule.objects.all()
    serializer_class = AlertRuleSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def list(self, request, *args, **kwargs):
        """列出所有告警规则"""
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"列出告警规则失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def retrieve(self, request, *args, **kwargs):
        """获取单个告警规则"""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"获取告警规则失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AlertHistoryViewSet(viewsets.ModelViewSet):
    queryset = AlertHistory.objects.all()
    serializer_class = AlertHistorySerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def list(self, request, *args, **kwargs):
        """列出所有告警历史"""
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"列出告警历史失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def retrieve(self, request, *args, **kwargs):
        """获取单个告警历史"""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"获取告警历史失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class MonitoringVisualizationViewSet(viewsets.ModelViewSet):
    queryset = MonitoringVisualization.objects.all()
    serializer_class = MonitoringVisualizationSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def list(self, request, *args, **kwargs):
        """列出所有可视化"""
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
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

class DashboardViewSet(viewsets.ModelViewSet):
    queryset = Dashboard.objects.all()
    serializer_class = DashboardSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def list(self, request, *args, **kwargs):
        """列出所有仪表板"""
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"列出仪表板失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DashboardWidgetViewSet(viewsets.ModelViewSet):
    queryset = DashboardWidget.objects.all()
    serializer_class = DashboardWidgetSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def list(self, request, *args, **kwargs):
        """列出所有仪表板组件"""
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"列出仪表板组件失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AlertNotificationConfigViewSet(viewsets.ModelViewSet):
    queryset = AlertNotificationConfig.objects.all()
    serializer_class = AlertNotificationConfigSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def list(self, request, *args, **kwargs):
        """列出所有告警通知配置"""
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"列出告警通知配置失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class SystemStatusViewSet(viewsets.ViewSet):
    """系统状态视图集"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    renderer_classes = [JSONRenderer]

    def list(self, request):
        """获取系统状态概览"""
        try:
            # 获取系统状态信息
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # 获取最近的错误日志数量
            recent_errors = ErrorLog.objects.filter(
                created_at__gte=timezone.now() - timedelta(hours=24)
            ).count()
            
            # 获取活跃告警数量
            active_alerts = AlertHistory.objects.filter(
                status='active'
            ).count()
            
            status_data = {
                'system': {
                    'cpu_usage': cpu_percent,
                    'memory_usage': memory.percent,
                    'disk_usage': disk.percent,
                },
                'monitoring': {
                    'recent_errors': recent_errors,
                    'active_alerts': active_alerts,
                },
                'status': 'healthy' if cpu_percent < 80 and memory.percent < 80 and disk.percent < 80 else 'warning',
                'created_at': timezone.now().isoformat()
            }
            
            return Response(status_data)
        except Exception as e:
            logger.error(f"获取系统状态失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def health(self, request):
        """获取系统健康状态"""
        try:
            health_status = {
                'status': 'up',
                'database': 'up',
                'cache': 'up',
                'created_at': timezone.now().isoformat()
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
            # 获取24小时内的统计信息
            last_24h = timezone.now() - timedelta(hours=24)
            
            # 获取告警统计
            alerts = AlertHistory.objects.all()
            active_alerts = alerts.filter(status='active')
            rules = AlertRule.objects.all()
            enabled_rules = rules.filter(is_enabled=True)
            
            # 获取最近活动
            recent_errors = ErrorLog.objects.filter(created_at__gte=last_24h)
            recent_alerts = alerts.filter(triggered_at__gte=last_24h)
            
            overview_data = {
                'metrics': {
                    'total_alerts': alerts.count(),
                    'active_alerts': active_alerts.count(),
                    'total_rules': rules.count(),
                    'enabled_rules': enabled_rules.count(),
                },
                'recent_activity': {
                    'error_count': recent_errors.count(),
                    'alert_count': recent_alerts.count(),
                },
                'timestamp': timezone.now().isoformat()
            }
            
            return Response(overview_data)
        except Exception as e:
            logger.error(f"获取系统概览信息失败: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
