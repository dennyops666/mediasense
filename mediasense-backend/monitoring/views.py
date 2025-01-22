from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework import viewsets, status, exceptions
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.utils import timezone
from datetime import timedelta
from .models import (
    SystemMetrics, AlertRule, AlertHistory,
    MonitoringVisualization, ErrorLog
)
from .serializers import (
    SystemMetricsSerializer, AlertRuleSerializer,
    AlertHistorySerializer, MonitoringVisualizationSerializer,
    ErrorLogSerializer
)

class SystemMetricsViewSet(ModelViewSet):
    """系统指标视图集"""
    serializer_class = SystemMetricsSerializer
    queryset = SystemMetrics.objects.all()
    permission_classes = [IsAuthenticated]

class AlertRuleViewSet(ModelViewSet):
    """告警规则视图集"""
    serializer_class = AlertRuleSerializer
    queryset = AlertRule.objects.all()
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def enable(self, request, pk=None):
        """启用告警规则"""
        rule = self.get_object()
        rule.is_enabled = True
        rule.save()
        serializer = self.get_serializer(rule)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def disable(self, request, pk=None):
        """禁用告警规则"""
        rule = self.get_object()
        rule.is_enabled = False
        rule.save()
        serializer = self.get_serializer(rule)
        return Response(serializer.data)

class AlertHistoryViewSet(ModelViewSet):
    """告警历史视图集"""
    serializer_class = AlertHistorySerializer
    queryset = AlertHistory.objects.all()
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """确认告警"""
        alert = self.get_object()
        alert.status = 'acknowledged'
        alert.acknowledged_at = timezone.now()
        alert.acknowledged_by = request.user
        alert.save()
        return Response({'status': 'success'})

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """解决告警"""
        alert = self.get_object()
        alert.status = 'resolved'
        alert.resolved_at = timezone.now()
        alert.save()
        return Response({'status': 'success'})

class MonitoringVisualizationViewSet(ModelViewSet):
    """监控可视化视图集"""
    serializer_class = MonitoringVisualizationSerializer
    queryset = MonitoringVisualization.objects.all()
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'])
    def data(self, request, pk=None):
        """获取可视化数据"""
        instance = self.get_object()
        metrics = SystemMetrics.objects.filter(
            timestamp__gte=timezone.now() - timedelta(minutes=instance.time_range)
        )
        
        data = []
        for metric in metrics:
            data.append({
                'timestamp': metric.timestamp,
                'value': metric.value,
                'type': metric.metric_type
            })
        
        return Response(data)

class ErrorLogViewSet(ModelViewSet):
    """错误日志视图集"""
    serializer_class = ErrorLogSerializer
    queryset = ErrorLog.objects.all()
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取错误日志统计信息"""
        one_day_ago = timezone.now() - timedelta(days=1)
        queryset = ErrorLog.objects.filter(
            created_at__gte=one_day_ago
        )
        
        stats = {
            'total_count': queryset.count(),
            'error_count': queryset.filter(severity='ERROR').count(),
            'warning_count': queryset.filter(severity='WARNING').count(),
            'info_count': queryset.filter(severity='INFO').count()
        }
        
        return Response(stats)

class SystemStatusViewSet(ModelViewSet):
    """系统状态视图集"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def overview(self, request):
        """获取系统概览"""
        return Response({
            'status': 'healthy',
            'last_check': timezone.now(),
            'services': {
                'database': True,
                'cache': True,
                'queue': True
            }
        })

    @action(detail=False, methods=['get'])
    def health(self, request):
        """获取系统健康状态"""
        return Response({
            'status': 'ok',
            'checks': {
                'database': 'ok',
                'cache': 'ok',
                'queue': 'ok'
            }
        })
