from rest_framework import serializers
from django.utils import timezone

from .models import (
    AlertHistory,
    AlertNotificationConfig,
    AlertRule,
    Dashboard,
    DashboardWidget,
    MonitoringVisualization,
    SystemMetrics,
    ErrorLog,
)


class SystemMetricsSerializer(serializers.ModelSerializer):
    """系统指标序列化器"""

    metric_type_display = serializers.CharField(source="get_metric_type_display", read_only=True)
    timestamp = serializers.DateTimeField(required=False)

    class Meta:
        model = SystemMetrics
        fields = ["id", "metric_type", "metric_type_display", "value", "timestamp", "metadata"]
        read_only_fields = ["id"]

    def validate_metric_type(self, value):
        """验证指标类型"""
        valid_types = [choice[0] for choice in SystemMetrics.MetricType.choices]
        if value not in valid_types:
            raise serializers.ValidationError(f"无效的指标类型: {value}")
        return value

    def validate_value(self, value):
        """验证指标值"""
        if not isinstance(value, (int, float)):
            raise serializers.ValidationError("指标值必须是数字")
        return value

    def validate_metadata(self, value):
        """验证元数据"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("元数据必须是字典类型")
        return value

    def create(self, validated_data):
        """创建系统指标"""
        if 'timestamp' not in validated_data:
            validated_data['timestamp'] = timezone.now()
        return super().create(validated_data)


class MonitoringVisualizationSerializer(serializers.ModelSerializer):
    """监控可视化序列化器"""

    created_by = serializers.ReadOnlyField(source="created_by.username")
    chart_type_display = serializers.CharField(source="get_chart_type_display", read_only=True)
    metric_type_display = serializers.CharField(source="get_metric_type_display", read_only=True)

    class Meta:
        model = MonitoringVisualization
        fields = [
            "id",
            "name",
            "description",
            "chart_type",
            "chart_type_display",
            "metric_type",
            "metric_type_display",
            "time_range",
            "interval",
            "warning_threshold",
            "critical_threshold",
            "is_active",
            "refresh_interval",
            "created_by",
            "created_at",
            "updated_at",
            "last_generated",
            "cached_data",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at", "last_generated", "cached_data"]

    def validate_chart_type(self, value):
        """验证图表类型"""
        valid_types = [choice[0] for choice in MonitoringVisualization.ChartType.choices]
        if value not in valid_types:
            raise serializers.ValidationError(f"无效的图表类型: {value}")
        return value

    def validate_metric_type(self, value):
        """验证指标类型"""
        valid_types = [choice[0] for choice in MonitoringVisualization.MetricType.choices]
        if value not in valid_types:
            raise serializers.ValidationError(f"无效的指标类型: {value}")
        return value

    def validate_time_range(self, value):
        """验证时间范围"""
        if value < 1:
            raise serializers.ValidationError("时间范围必须大于0")
        return value

    def validate_interval(self, value):
        """验证时间间隔"""
        if value < 1:
            raise serializers.ValidationError("时间间隔必须大于0")
        return value


class AlertRuleSerializer(serializers.ModelSerializer):
    """告警规则序列化器"""

    created_by = serializers.ReadOnlyField(source="created_by.username")
    metric_type_display = serializers.CharField(source="get_metric_type_display", read_only=True)
    operator_display = serializers.CharField(source="get_operator_display", read_only=True)
    alert_level_display = serializers.CharField(source="get_alert_level_display", read_only=True)

    class Meta:
        model = AlertRule
        fields = [
            "id",
            "name",
            "description",
            "metric_type",
            "metric_type_display",
            "operator",
            "operator_display",
            "threshold",
            "duration",
            "alert_level",
            "alert_level_display",
            "is_enabled",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def validate_duration(self, value):
        """验证持续时间"""
        if value < 1:
            raise serializers.ValidationError("持续时间必须大于0")
        return value

    def validate_alert_level(self, value):
        """验证告警级别"""
        valid_levels = [choice[0] for choice in AlertRule.AlertLevel.choices]
        if value not in valid_levels:
            raise serializers.ValidationError(f"无效的告警级别: {value}")
        return value

    def validate_metric_type(self, value):
        """验证指标类型"""
        valid_types = [choice[0] for choice in AlertRule.MetricType.choices]
        if value not in valid_types:
            raise serializers.ValidationError(f"无效的指标类型: {value}")
        return value

    def validate_operator(self, value):
        """验证操作符"""
        valid_operators = [choice[0] for choice in AlertRule.Operator.choices]
        if value not in valid_operators:
            raise serializers.ValidationError(f"无效的操作符: {value}")
        return value


class AlertHistorySerializer(serializers.ModelSerializer):
    """告警历史序列化器"""

    rule_name = serializers.CharField(source="rule.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    acknowledged_by_username = serializers.CharField(source="acknowledged_by.username", read_only=True)
    alert_level = serializers.CharField(source="rule.alert_level", read_only=True)
    alert_level_display = serializers.CharField(source="rule.get_alert_level_display", read_only=True)

    class Meta:
        model = AlertHistory
        fields = [
            "id",
            "rule",
            "rule_name",
            "status",
            "status_display",
            "metric_value",
            "triggered_at",
            "resolved_at",
            "acknowledged_at",
            "acknowledged_by",
            "acknowledged_by_username",
            "note",
            "alert_level",
            "alert_level_display",
        ]
        read_only_fields = [
            "id",
            "rule_name",
            "metric_value",
            "triggered_at",
            "resolved_at",
            "acknowledged_at",
            "acknowledged_by",
            "acknowledged_by_username",
            "alert_level",
            "alert_level_display",
        ]


class AlertNotificationConfigSerializer(serializers.ModelSerializer):
    """告警通知配置序列化器"""

    user = serializers.ReadOnlyField(source="user.username")
    notification_type_display = serializers.CharField(source="get_notification_type_display", read_only=True)

    class Meta:
        model = AlertNotificationConfig
        fields = [
            "id",
            "name",
            "notification_type",
            "notification_type_display",
            "config",
            "alert_levels",
            "is_active",
            "user",
            "created_at",
            "updated_at",
            "last_notified",
            "notification_count",
        ]
        read_only_fields = ["user", "created_at", "updated_at", "last_notified", "notification_count"]

    def validate_config(self, value):
        """验证配置信息"""
        notification_type = self.initial_data.get("notification_type", "").lower()
        if notification_type == "email":
            if "email" not in value:
                raise serializers.ValidationError("邮件通知配置必须包含email字段")
        elif notification_type == "webhook":
            if "url" not in value:
                raise serializers.ValidationError("Webhook通知配置必须包含url字段")
        elif notification_type == "dingtalk":
            if "webhook_url" not in value:
                raise serializers.ValidationError("钉钉通知配置必须包含webhook_url字段")
        elif notification_type == "wechat":
            if "corp_id" not in value or "agent_id" not in value or "secret" not in value:
                raise serializers.ValidationError("微信通知配置必须包含corp_id、agent_id和secret字段")
        return value

    def validate_alert_levels(self, value):
        """验证告警级别"""
        valid_levels = ["info", "warning", "error", "critical"]
        for level in value:
            if level.lower() not in valid_levels:
                raise serializers.ValidationError(f"无效的告警级别: {level}")
        return [level.lower() for level in value]


class DashboardWidgetSerializer(serializers.ModelSerializer):
    """仪表板组件序列化器"""

    widget_type_display = serializers.CharField(source="get_widget_type_display", read_only=True)

    class Meta:
        model = DashboardWidget
        fields = [
            "id",
            "dashboard",
            "name",
            "widget_type",
            "widget_type_display",
            "config",
            "position",
            "is_visible",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class DashboardSerializer(serializers.ModelSerializer):
    """仪表板序列化器"""

    created_by = serializers.ReadOnlyField(source="created_by.username")
    layout_type_display = serializers.CharField(source="get_layout_type_display", read_only=True)
    widgets = DashboardWidgetSerializer(many=True, read_only=True)

    class Meta:
        model = Dashboard
        fields = [
            "id",
            "name",
            "description",
            "layout_type",
            "layout_type_display",
            "is_default",
            "created_by",
            "created_at",
            "updated_at",
            "widgets",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]


class ErrorLogSerializer(serializers.ModelSerializer):
    """错误日志序列化器"""
    class Meta:
        model = ErrorLog
        fields = ['id', 'severity', 'message', 'stack_trace', 'source', 'created_by', 'created_at']
        read_only_fields = ['created_by', 'created_at']

    def validate_severity(self, value):
        """验证日志级别"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if value not in valid_levels:
            raise serializers.ValidationError(f"无效的日志级别: {value}")
        return value
