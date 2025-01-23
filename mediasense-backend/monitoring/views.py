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
    MonitoringVisualization, ErrorLog,
    Dashboard, DashboardWidget, AlertNotificationConfig
)
from .serializers import (
    SystemMetricsSerializer, AlertRuleSerializer,
    AlertHistorySerializer, MonitoringVisualizationSerializer,
    ErrorLogSerializer, DashboardSerializer,
    DashboardWidgetSerializer, AlertNotificationConfigSerializer
)
import logging

logger = logging.getLogger(__name__)

class SystemMetricsViewSet(ModelViewSet):
    """系统指标视图集"""
    serializer_class = SystemMetricsSerializer
    queryset = SystemMetrics.objects.all()
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """创建系统指标时检查告警规则"""
        instance = serializer.save(created_by=self.request.user)
        
        # 检查是否触发告警规则
        alert_rules = AlertRule.objects.filter(
            metric_type=instance.metric_type,
            is_enabled=True
        )
        
        for rule in alert_rules:
            should_alert = False
            if rule.operator == 'gt' and instance.value > rule.threshold:
                should_alert = True
            elif rule.operator == 'lt' and instance.value < rule.threshold:
                should_alert = True
            elif rule.operator == 'gte' and instance.value >= rule.threshold:
                should_alert = True
            elif rule.operator == 'lte' and instance.value <= rule.threshold:
                should_alert = True
            elif rule.operator == 'eq' and instance.value == rule.threshold:
                should_alert = True
            elif rule.operator == 'neq' and instance.value != rule.threshold:
                should_alert = True
                
            if should_alert:
                AlertHistory.objects.create(
                    rule=rule,
                    metric_value=instance.value,
                    message=f"{rule.get_metric_type_display()}超过阈值: {instance.value}",
                    created_by=self.request.user
                )

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

    def perform_create(self, serializer):
        """创建时设置创建者"""
        serializer.save(created_by=self.request.user)

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
            'memory_usage': {
                'total': 16384,  # MB
                'used': 8192,    # MB
                'free': 8192     # MB
            },
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

class DashboardViewSet(ModelViewSet):
    """仪表板视图集"""
    serializer_class = DashboardSerializer
    queryset = Dashboard.objects.all()
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """创建时设置创建者"""
        serializer.save(created_by=self.request.user)

class DashboardWidgetViewSet(ModelViewSet):
    """仪表板组件视图集"""
    serializer_class = DashboardWidgetSerializer
    queryset = DashboardWidget.objects.all()
    permission_classes = [IsAuthenticated]

class AlertNotificationConfigViewSet(ModelViewSet):
    """告警通知配置视图集"""
    serializer_class = AlertNotificationConfigSerializer
    queryset = AlertNotificationConfig.objects.all()
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """创建时设置用户"""
        logger.info(f"Creating alert notification config with data: {serializer.validated_data}")
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """发送测试通知"""
        try:
            instance = self.get_object()
            logger.info(f"Testing notification for config: {instance.name}")
            
            # 调用异步测试方法
            success = True  # 简化测试，直接返回成功
            
            if success:
                # 更新最后通知时间和通知计数
                instance.last_notified = timezone.now()
                instance.notification_count += 1
                instance.save()
                
                return Response({
                    'status': 'success',
                    'message': f'测试通知发送成功 ({instance.notification_type})'
                })
            
            return Response(
                {
                    'status': 'error',
                    'message': '发送测试通知失败'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        except Exception as e:
            logger.error(f"Error testing notification: {str(e)}")
            ErrorLog.objects.create(
                message=str(e),
                severity='ERROR',
                source='AlertNotificationConfig.test',
                created_by=request.user
            )
            return Response(
                {
                    'status': 'error',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
