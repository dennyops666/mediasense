from rest_framework import serializers

from .models import (
    AlertHistory,
    AlertNotificationConfig,
    AlertRule,
    Dashboard,
    DashboardWidget,
    MonitoringVisualization,
    SystemMetrics,
)


class SystemMetricsSerializer(serializers.ModelSerializer):
    """系统指标序列化器"""

    metric_type_display = serializers.CharField(source="get_metric_type_display", read_only=True)

    class Meta:
        model = SystemMetrics
        fields = ["id", "metric_type", "metric_type_display", "value", "unit", "timestamp", "description"]
        read_only_fields = ["timestamp"]


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
            "is_active",
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
            "rule",
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
            "user",
            "notification_type",
            "notification_type_display",
            "name",
            "config",
            "alert_levels",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at"]

    def validate_config(self, value):
        """验证配置参数"""
        notification_type = self.initial_data.get("notification_type")

        if notification_type == AlertNotificationConfig.NotificationType.EMAIL:
            required_fields = ["email"]
        elif notification_type == AlertNotificationConfig.NotificationType.SMS:
            required_fields = ["phone"]
        elif notification_type == AlertNotificationConfig.NotificationType.WEBHOOK:
            required_fields = ["url"]
        elif notification_type == AlertNotificationConfig.NotificationType.DINGTALK:
            required_fields = ["webhook_url", "secret"]
        elif notification_type == AlertNotificationConfig.NotificationType.WECHAT:
            required_fields = ["corp_id", "agent_id", "secret"]
        else:
            return value

        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"缺少必需的配置参数: {field}")

        return value

    def validate_alert_levels(self, value):
        """验证告警级别列表"""
        valid_levels = [level[0] for level in AlertRule.AlertLevel.choices]

        if not isinstance(value, list):
            raise serializers.ValidationError("告警级别必须是一个列表")

        if not value:
            raise serializers.ValidationError("至少需要选择一个告警级别")

        for level in value:
            if level not in valid_levels:
                raise serializers.ValidationError(f"无效的告警级别: {level}")

        return value


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
