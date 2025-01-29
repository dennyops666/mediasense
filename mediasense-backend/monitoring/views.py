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

logger = logging.getLogger(__name__)

class SystemMetricsViewSet(AsyncViewSet):
    queryset = SystemMetrics.objects.all()
    serializer_class = SystemMetricsSerializer
    permission_classes = [IsAuthenticated]

class AlertRuleViewSet(AsyncViewSet):
    queryset = AlertRule.objects.all()
    serializer_class = AlertRuleSerializer
    permission_classes = [IsAuthenticated]

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

class ErrorLogViewSet(AsyncViewSet):
    queryset = ErrorLog.objects.all()
    serializer_class = ErrorLogSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    async def statistics(self, request):
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
            queryset = await sync_to_async(lambda: self.queryset.filter(timestamp__gte=start_time))()
            
            # 统计数据
            stats = await sync_to_async(lambda: queryset.values('severity').annotate(count=Count('id')))()
            
            return Response(list(stats))
            
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

class DashboardWidgetViewSet(AsyncViewSet):
    queryset = DashboardWidget.objects.all()
    serializer_class = DashboardWidgetSerializer
    permission_classes = [IsAuthenticated]

class AlertNotificationConfigViewSet(AsyncViewSet):
    queryset = AlertNotificationConfig.objects.all()
    serializer_class = AlertNotificationConfigSerializer
    permission_classes = [IsAuthenticated]

class SystemStatusViewSet(AsyncViewSet):
    queryset = SystemMetrics.objects.all()
    serializer_class = SystemMetricsSerializer
    permission_classes = [IsAuthenticated]

    async def list(self, request, *args, **kwargs):
        """获取系统状态概览"""
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
                    latest_metrics[metric_type[0]] = await sync_to_async(self.get_serializer)(metric).data
            
            # 获取活跃告警数量
            active_alerts_count = await sync_to_async(
                lambda: AlertHistory.objects.filter(status='active').count()
            )()
            
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
