import os

import psutil
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (
    AlertHistory,
    AlertNotificationConfig,
    AlertRule,
    Dashboard,
    DashboardWidget,
    MonitoringVisualization,
    SystemMetrics,
)
from .serializers import (
    AlertHistorySerializer,
    AlertNotificationConfigSerializer,
    AlertRuleSerializer,
    DashboardSerializer,
    DashboardWidgetSerializer,
    MonitoringVisualizationSerializer,
    SystemMetricsSerializer,
)


class SystemMetricsViewSet(viewsets.ModelViewSet):
    """
    系统指标视图集
    """

    queryset = SystemMetrics.objects.all()
    serializer_class = SystemMetricsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        根据查询参数过滤系统指标
        """
        queryset = SystemMetrics.objects.all()
        metric_type = self.request.query_params.get("type", None)
        if metric_type:
            queryset = queryset.filter(metric_type=metric_type)
        return queryset


class SystemStatusViewSet(viewsets.ViewSet):
    """
    系统状态视图集
    """

    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=["get"])
    def get_status(self, request):
        """
        获取系统状态
        """
        # 获取CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)

        # 获取内存使用情况
        memory = psutil.virtual_memory()
        memory_usage = {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used,
            "free": memory.free,
        }

        # 获取磁盘使用情况
        disk = psutil.disk_usage("/")
        disk_usage = {"total": disk.total, "used": disk.used, "free": disk.free, "percent": disk.percent}

        return Response({"cpu_percent": cpu_percent, "memory_usage": memory_usage, "disk_usage": disk_usage})


class PerformanceMonitorViewSet(viewsets.ViewSet):
    """
    性能监控视图集
    """

    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=["get"])
    def get_performance(self, request):
        """
        获取性能指标
        """
        # 获取进程信息
        process = psutil.Process(os.getpid())

        # 获取进程CPU使用率
        process_cpu_percent = process.cpu_percent(interval=1)

        # 获取进程内存使用情况
        process_memory_info = process.memory_info()

        # 获取进程打开的文件数
        open_files_count = len(process.open_files())

        # 获取进程的线程数
        threads_count = process.num_threads()

        return Response(
            {
                "process_cpu_percent": process_cpu_percent,
                "process_memory_rss": process_memory_info.rss,
                "process_memory_vms": process_memory_info.vms,
                "open_files_count": open_files_count,
                "threads_count": threads_count,
            }
        )


class ErrorLogViewSet(viewsets.ViewSet):
    """
    错误日志视图集
    """

    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        """
        获取错误日志列表
        """
        # TODO: 实现错误日志获取逻辑
        return Response({"logs": [{"timestamp": "2024-01-12 10:00:00", "level": "ERROR", "message": "示例错误日志"}]})


class MonitoringVisualizationViewSet(viewsets.ModelViewSet):
    """监控可视化视图集"""

    serializer_class = MonitoringVisualizationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """获取查询集"""
        return MonitoringVisualization.objects.filter(created_by=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        """创建时设置创建者"""
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["get"])
    def data(self, request, pk=None):
        """获取图表数据"""
        try:
            visualization = self.get_object()
            chart_data = MonitoringVisualizationService.get_chart_data(visualization)
            return Response(chart_data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "获取图表数据失败"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=["post"])
    def refresh(self, request, pk=None):
        """刷新图表数据"""
        try:
            visualization = self.get_object()
            chart_data = MonitoringVisualizationService.generate_chart_data(visualization)
            return Response(chart_data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "刷新图表数据失败"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["get"])
    def available_fields(self, request):
        """获取可用字段"""
        try:
            fields = MonitoringVisualizationService.get_available_fields()
            return Response(fields)
        except Exception as e:
            return Response({"error": "获取可用字段失败"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=["post"])
    def toggle_active(self, request, pk=None):
        """切换启用状态"""
        try:
            visualization = self.get_object()
            visualization.is_active = not visualization.is_active
            visualization.save()
            return Response({"id": visualization.id, "is_active": visualization.is_active})
        except Exception as e:
            return Response({"error": "切换状态失败"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AlertRuleViewSet(viewsets.ModelViewSet):
    """告警规则视图集"""

    serializer_class = AlertRuleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """获取当前用户创建的告警规则"""
        return AlertRule.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        """创建告警规则时设置创建者"""
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def toggle_active(self, request, pk=None):
        """切换告警规则的启用状态"""
        rule = self.get_object()
        rule.is_active = not rule.is_active
        rule.save()
        return Response({"status": "success", "is_active": rule.is_active})


class AlertHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """告警历史视图集"""

    serializer_class = AlertHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """获取告警历史记录，支持按规则ID和状态过滤"""
        queryset = AlertHistory.objects.all()

        # 按规则ID过滤
        rule_id = self.request.query_params.get("rule_id")
        if rule_id:
            queryset = queryset.filter(rule_id=rule_id)

        # 按状态过滤
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by("-triggered_at")

    @action(detail=True, methods=["post"])
    def acknowledge(self, request, pk=None):
        """确认告警"""
        history = self.get_object()
        if history.status != AlertHistory.Status.ACTIVE:
            return Response(
                {"status": "error", "message": "只能确认活动状态的告警"}, status=status.HTTP_400_BAD_REQUEST
            )

        history.status = AlertHistory.Status.ACKNOWLEDGED
        history.acknowledged_at = timezone.now()
        history.acknowledged_by = request.user
        history.note = request.data.get("note", "")
        history.save()

        return Response({"status": "success", "message": "告警已确认"})


class AlertNotificationConfigViewSet(viewsets.ModelViewSet):
    """告警通知配置视图集"""

    serializer_class = AlertNotificationConfigSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """获取当前用户的通知配置"""
        return AlertNotificationConfig.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """创建通知配置时设置用户"""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def test(self, request, pk=None):
        """测试通知配置"""
        config = self.get_object()
        try:
            # TODO: 实现发送测试通知的逻辑
            return Response({"status": "success", "message": "测试通知已发送"})
        except Exception as e:
            return Response(
                {"status": "error", "message": f"发送测试通知失败: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["post"])
    def toggle_active(self, request, pk=None):
        """切换通知配置的启用状态"""
        config = self.get_object()
        config.is_active = not config.is_active
        config.save()
        return Response({"status": "success", "is_active": config.is_active})


class DashboardViewSet(viewsets.ModelViewSet):
    """仪表板视图集"""

    serializer_class = DashboardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """获取当前用户的仪表板"""
        return Dashboard.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        """创建仪表板时设置创建者"""
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def set_default(self, request, pk=None):
        """设置为默认仪表板"""
        dashboard = self.get_object()
        dashboard.is_default = True
        dashboard.save()
        return Response({"status": "success", "message": "已设置为默认仪表板"})

    @action(detail=False, methods=["get"])
    def default(self, request):
        """获取默认仪表板"""
        try:
            dashboard = Dashboard.objects.get(created_by=request.user, is_default=True)
            serializer = self.get_serializer(dashboard)
            return Response(serializer.data)
        except Dashboard.DoesNotExist:
            return Response({"status": "error", "message": "未设置默认仪表板"}, status=status.HTTP_404_NOT_FOUND)


class DashboardWidgetViewSet(viewsets.ModelViewSet):
    """仪表板组件视图集"""

    serializer_class = DashboardWidgetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """获取指定仪表板的组件"""
        dashboard_id = self.request.query_params.get("dashboard_id")
        queryset = DashboardWidget.objects.all()

        if dashboard_id:
            queryset = queryset.filter(dashboard_id=dashboard_id)

        return queryset

    @action(detail=True, methods=["post"])
    def toggle_visibility(self, request, pk=None):
        """切换组件可见性"""
        widget = self.get_object()
        widget.is_visible = not widget.is_visible
        widget.save()
        return Response({"status": "success", "is_visible": widget.is_visible})

    @action(detail=True, methods=["post"])
    def update_position(self, request, pk=None):
        """更新组件位置"""
        widget = self.get_object()
        position = request.data.get("position", {})

        if not isinstance(position, dict):
            return Response({"status": "error", "message": "位置信息格式错误"}, status=status.HTTP_400_BAD_REQUEST)

        widget.position = position
        widget.save()
        return Response({"status": "success", "position": widget.position})
