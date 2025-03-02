from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

User = get_user_model()


class MonitoringVisualization(models.Model):
    """监控数据可视化模型"""

    class ChartType(models.TextChoices):
        LINE_CHART = "line_chart", "折线图"
        GAUGE = "gauge", "仪表盘"

    class MetricType(models.TextChoices):
        CPU_USAGE = "cpu_usage", "CPU使用率"
        MEMORY_USAGE = "memory_usage", "内存使用率"
        DISK_USAGE = "disk_usage", "磁盘使用率"
        NETWORK_IN = "network_in", "网络入流量"
        NETWORK_OUT = "network_out", "网络出流量"

    name = models.CharField("图表名称", max_length=100)
    description = models.TextField("图表描述", blank=True)
    visualization_type = models.CharField("可视化类型", max_length=20, choices=ChartType.choices)
    metric_type = models.CharField("指标类型", max_length=20, choices=MetricType.choices)
    config = models.JSONField("配置信息", default=dict)
    is_active = models.BooleanField("是否启用", default=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)
    cached_data = models.JSONField("缓存数据", null=True, blank=True)

    class Meta:
        verbose_name = "监控可视化"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.get_metric_type_display()})"

    def clean(self):
        if not self.config:
            raise ValidationError("配置信息不能为空")
        if 'time_range' not in self.config:
            raise ValidationError("配置信息必须包含time_range字段")


class AlertRule(models.Model):
    """告警规则模型"""

    class AlertLevel(models.TextChoices):
        INFO = "info", "信息"
        WARNING = "warning", "警告"
        CRITICAL = "critical", "严重"

    class MetricType(models.TextChoices):
        CPU_USAGE = "cpu_usage", "CPU使用率"
        MEMORY_USAGE = "memory_usage", "内存使用率"
        DISK_USAGE = "disk_usage", "磁盘使用率"
        NETWORK_IN = "network_in", "网络入流量"
        NETWORK_OUT = "network_out", "网络出流量"

    class Operator(models.TextChoices):
        GT = "gt", "大于"
        LT = "lt", "小于"

    name = models.CharField("规则名称", max_length=100)
    description = models.TextField("规则描述", blank=True)
    metric_type = models.CharField("监控指标", max_length=20, choices=MetricType.choices)
    operator = models.CharField("比较运算符", max_length=10, choices=Operator.choices)
    threshold = models.FloatField("阈值")
    duration = models.IntegerField("持续时间(秒)", default=60)  # 默认持续60秒
    alert_level = models.CharField("告警级别", max_length=20, choices=AlertLevel.choices, default=AlertLevel.WARNING)
    is_enabled = models.BooleanField("是否启用", default=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="alert_rules", verbose_name="创建者"
    )

    class Meta:
        verbose_name = "告警规则"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.get_metric_type_display()})"


class SystemMetrics(models.Model):
    """系统指标数据模型"""

    class MetricType(models.TextChoices):
        CPU_USAGE = "cpu_usage", "CPU使用率"
        MEMORY_USAGE = "memory_usage", "内存使用率"
        DISK_USAGE = "disk_usage", "磁盘使用率"
        NETWORK_IN = "network_in", "网络入流量"
        NETWORK_OUT = "network_out", "网络出流量"

    metric_type = models.CharField("指标类型", max_length=20, choices=MetricType.choices)
    value = models.FloatField("指标值")
    created_at = models.DateTimeField("记录时间", auto_now_add=True)
    metadata = models.JSONField("元数据", default=dict, blank=True)

    class Meta:
        verbose_name = "系统指标"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["metric_type", "created_at"]),
        ]

    def __str__(self):
        return f"{self.get_metric_type_display()}: {self.value}"


class AlertHistory(models.Model):
    """告警历史记录"""

    class Status(models.TextChoices):
        ACTIVE = "active", "活动"
        RESOLVED = "resolved", "已解决"
        ACKNOWLEDGED = "acknowledged", "已确认"

    rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE, related_name="alert_history", verbose_name="告警规则")
    status = models.CharField("状态", max_length=20, choices=Status.choices, default=Status.ACTIVE)
    message = models.TextField("告警消息", blank=True, default="")
    metric_value = models.FloatField("指标值")
    triggered_at = models.DateTimeField("触发时间", auto_now_add=True)
    resolved_at = models.DateTimeField("解决时间", null=True, blank=True)
    acknowledged_at = models.DateTimeField("确认时间", null=True, blank=True)
    acknowledged_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="acknowledged_alerts", verbose_name="确认者"
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_alerts", verbose_name="创建者"
    )
    note = models.TextField("备注", blank=True, default="")

    class Meta:
        verbose_name = "告警历史"
        verbose_name_plural = verbose_name
        ordering = ["-triggered_at"]
        indexes = [
            models.Index(fields=["rule", "status"]),
            models.Index(fields=["triggered_at"]),
        ]

    def __str__(self):
        return f"{self.rule.name} - {self.triggered_at}"


class AlertNotificationConfig(models.Model):
    """告警通知配置模型"""

    class NotificationType(models.TextChoices):
        EMAIL = "email", "邮件通知"
        SMS = "sms", "短信通知"
        WEBHOOK = "webhook", "Webhook通知"
        DINGTALK = "dingtalk", "钉钉通知"
        WECHAT = "wechat", "微信通知"

    name = models.CharField("通知名称", max_length=100)
    notification_type = models.CharField("通知类型", max_length=20, choices=NotificationType.choices)
    config = models.JSONField("通知配置", help_text="通知相关的配置信息")
    alert_levels = models.JSONField("告警级别", help_text="接收哪些级别的告警")
    is_active = models.BooleanField("是否启用", default=True)
    notification_interval = models.IntegerField("通知间隔(秒)", default=300, help_text="两次通知之间的最小间隔时间")
    recovery_notify = models.BooleanField("恢复通知", default=True, help_text="告警恢复时是否发送通知")
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="alert_notifications", verbose_name="用户"
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)
    last_notified = models.DateTimeField("上次通知时间", null=True, blank=True)
    notification_count = models.IntegerField("通知次数", default=0)

    class Meta:
        verbose_name = "告警通知配置"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.get_notification_type_display()})"

    async def send_test_notification(self):
        """发送测试通知"""
        try:
            # 这里应该实现实际的通知发送逻辑
            return True
        except Exception as e:
            return False


class Dashboard(models.Model):
    """仪表盘模型"""
    
    class LayoutType(models.TextChoices):
        GRID = "grid", "网格布局"
        FLEX = "flex", "弹性布局"
        FIXED = "fixed", "固定布局"
    
    name = models.CharField("仪表盘名称", max_length=100)
    description = models.TextField("仪表盘描述", blank=True)
    layout_type = models.CharField("布局类型", max_length=20, choices=LayoutType.choices, default=LayoutType.GRID)
    layout = models.JSONField("布局配置", default=dict)
    is_default = models.BooleanField("是否默认", default=False)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="dashboards", verbose_name="创建者"
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "仪表盘"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["created_by", "is_default"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return self.name


class DashboardWidget(models.Model):
    """仪表盘小部件模型"""
    
    class WidgetType(models.TextChoices):
        CHART = "chart", "图表"
        METRIC = "metric", "指标"
        TEXT = "text", "文本"
        ALERT = "alert", "告警"
    
    dashboard = models.ForeignKey(
        Dashboard, on_delete=models.CASCADE, related_name="widgets", verbose_name="所属仪表盘"
    )
    name = models.CharField("小部件名称", max_length=100)
    widget_type = models.CharField("小部件类型", max_length=20, choices=WidgetType.choices, default=WidgetType.CHART)
    visualization = models.ForeignKey(
        MonitoringVisualization, on_delete=models.CASCADE, related_name="widgets", 
        verbose_name="可视化配置", null=True, blank=True
    )
    config = models.JSONField("配置信息", default=dict)
    position = models.JSONField("位置信息", default=dict)
    is_visible = models.BooleanField("是否可见", default=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "仪表盘小部件"
        verbose_name_plural = verbose_name
        ordering = ["dashboard", "created_at"]
        indexes = [
            models.Index(fields=["dashboard", "is_visible"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.dashboard.name} - {self.name}"


class ErrorLog(models.Model):
    """错误日志模型"""
    
    class ErrorType(models.TextChoices):
        SYSTEM = "system", "系统错误"
        APPLICATION = "application", "应用错误"
        DATABASE = "database", "数据库错误"
        NETWORK = "network", "网络错误"
        SECURITY = "security", "安全错误"
        OTHER = "other", "其他错误"
    
    class Severity(models.TextChoices):
        INFO = "info", "信息"
        WARNING = "warning", "警告"
        ERROR = "error", "错误"
        CRITICAL = "critical", "严重"
    
    error_type = models.CharField("错误类型", max_length=20, choices=ErrorType.choices)
    severity = models.CharField("严重程度", max_length=20, choices=Severity.choices)
    error_message = models.TextField("错误消息")
    stack_trace = models.TextField("堆栈跟踪", blank=True, null=True)
    source = models.CharField("错误来源", max_length=255)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="error_logs", verbose_name="创建者"
    )

    class Meta:
        verbose_name = "错误日志"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["error_type", "severity"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.get_error_type_display()} - {self.error_message[:50]}"
