from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models

User = get_user_model()


class MonitoringVisualization(models.Model):
    """监控数据可视化模型"""

    class ChartType(models.TextChoices):
        LINE = "line", "折线图"
        BAR = "bar", "柱状图"
        GAUGE = "gauge", "仪表盘"
        PIE = "pie", "饼图"

    class MetricType(models.TextChoices):
        CPU = "cpu", "CPU使用率"
        MEMORY = "memory", "内存使用率"
        DISK = "disk", "磁盘使用率"
        NETWORK = "network", "网络流量"
        API_LATENCY = "api_latency", "API响应时间"
        ERROR_RATE = "error_rate", "错误率"
        REQUEST_COUNT = "request_count", "请求数"
        TASK_COUNT = "task_count", "任务数"

    name = models.CharField("图表名称", max_length=100)
    description = models.TextField("图表描述", blank=True)
    chart_type = models.CharField("图表类型", max_length=20, choices=ChartType.choices, default=ChartType.LINE)
    metric_type = models.CharField("指标类型", max_length=20, choices=MetricType.choices)
    time_range = models.IntegerField("时间范围(分钟)", default=60, help_text="统计最近n分钟的数据")
    interval = models.IntegerField("统计间隔(秒)", default=60, help_text="数据聚合的时间间隔")
    aggregation_method = models.CharField(
        "聚合方法",
        max_length=20,
        choices=[("avg", "平均值"), ("max", "最大值"), ("min", "最小值"), ("sum", "求和"), ("count", "计数")],
        default="avg",
    )
    warning_threshold = models.FloatField("警告阈值", null=True, blank=True, help_text="超过此值显示警告")
    critical_threshold = models.FloatField("严重阈值", null=True, blank=True, help_text="超过此值显示严重警告")
    is_active = models.IntegerField("是否启用", default=1)
    refresh_interval = models.IntegerField("刷新间隔(秒)", default=30, help_text="数据自动刷新的间隔")
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="monitoring_visualizations", verbose_name="创建者"
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)
    last_generated = models.DateTimeField("上次生成时间", null=True, blank=True)
    cached_data = models.JSONField("缓存数据", null=True, blank=True, help_text="缓存的图表数据")

    class Meta:
        verbose_name = "监控可视化"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["metric_type", "is_active"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_metric_type_display()})"

    def clean(self):
        """验证数据"""
        if self.time_range < 1:
            raise ValidationError("时间范围必须大于0")
        if self.interval < 1:
            raise ValidationError("统计间隔必须大于0")
        if self.refresh_interval < 1:
            raise ValidationError("刷新间隔必须大于0")
        if self.warning_threshold and self.critical_threshold:
            if self.warning_threshold > self.critical_threshold:
                raise ValidationError("警告阈值不能大于严重阈值")


class AlertRule(models.Model):
    """告警规则模型"""

    class AlertLevel(models.TextChoices):
        INFO = "info", "信息"
        WARNING = "warning", "警告"
        CRITICAL = "critical", "严重"

    class MetricType(models.TextChoices):
        CPU = "cpu", "CPU使用率"
        MEMORY = "memory", "内存使用率"
        DISK = "disk", "磁盘使用率"
        NETWORK = "network", "网络流量"
        API_LATENCY = "api_latency", "API响应时间"
        ERROR_RATE = "error_rate", "错误率"
        REQUEST_COUNT = "request_count", "请求数"
        TASK_COUNT = "task_count", "任务数"

    class Operator(models.TextChoices):
        GT = "gt", "大于"
        LT = "lt", "小于"
        GTE = "gte", "大于等于"
        LTE = "lte", "小于等于"
        EQ = "eq", "等于"
        NEQ = "neq", "不等于"

    name = models.CharField("规则名称", max_length=100)
    description = models.TextField("规则描述", blank=True)
    metric_type = models.CharField("监控指标", max_length=20, choices=MetricType.choices)
    operator = models.CharField("比较运算符", max_length=10, choices=Operator.choices)
    threshold = models.FloatField("阈值")
    duration = models.IntegerField("持续时间(分钟)", default=5, help_text="指标超过阈值持续n分钟后触发告警")
    alert_level = models.CharField("告警级别", max_length=20, choices=AlertLevel.choices, default=AlertLevel.WARNING)
    is_active = models.IntegerField("是否启用", default=1)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="alert_rules", verbose_name="创建者"
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "告警规则"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["metric_type", "is_active"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_metric_type_display()})"

    def clean(self):
        """验证数据"""
        if self.duration < 1:
            raise ValidationError("持续时间必须大于0")


class AlertHistory(models.Model):
    """告警历史记录"""

    class Status(models.TextChoices):
        ACTIVE = "active", "活动"
        RESOLVED = "resolved", "已解决"
        ACKNOWLEDGED = "acknowledged", "已确认"

    rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE, related_name="alert_history", verbose_name="告警规则")
    status = models.CharField("状态", max_length=20, choices=Status.choices, default=Status.ACTIVE)
    metric_value = models.FloatField("指标值")
    triggered_at = models.DateTimeField("触发时间", auto_now_add=True)
    resolved_at = models.DateTimeField("解决时间", null=True, blank=True)
    acknowledged_at = models.DateTimeField("确认时间", null=True, blank=True)
    acknowledged_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="acknowledged_alerts", verbose_name="确认者"
    )
    note = models.TextField("备注", blank=True)

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
    """告警通知配置"""

    class NotificationType(models.TextChoices):
        EMAIL = "email", "邮件"
        SMS = "sms", "短信"
        WEBHOOK = "webhook", "Webhook"
        DINGTALK = "dingtalk", "钉钉"
        WECHAT = "wechat", "企业微信"

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="alert_notification_configs", verbose_name="用户"
    )
    notification_type = models.CharField("通知类型", max_length=20, choices=NotificationType.choices)
    name = models.CharField("配置名称", max_length=100)
    config = models.JSONField("配置详情", help_text="不同通知类型的具体配置参数")
    alert_levels = models.JSONField("接收的告警级别", default=list, help_text="接收哪些级别的告警")
    is_active = models.IntegerField("是否启用", default=1)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "告警通知配置"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "notification_type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_notification_type_display()})"


class Dashboard(models.Model):
    """监控仪表板"""

    class LayoutType(models.TextChoices):
        GRID = "GRID", "网格布局"
        FLOW = "FLOW", "流式布局"

    name = models.CharField("名称", max_length=100)
    description = models.TextField("描述", blank=True)
    layout_type = models.CharField("布局类型", max_length=20, choices=LayoutType.choices, default=LayoutType.GRID)
    is_default = models.IntegerField("是否默认", default=0)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="创建者")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "监控仪表板"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["created_by", "-created_at"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """确保只有一个默认仪表板"""
        if self.is_default:
            Dashboard.objects.filter(created_by=self.created_by, is_default=True).exclude(pk=self.pk).update(
                is_default=False
            )
        super().save(*args, **kwargs)


class DashboardWidget(models.Model):
    """仪表板组件"""

    class WidgetType(models.TextChoices):
        SYSTEM_OVERVIEW = "SYSTEM_OVERVIEW", "系统概览"
        PERFORMANCE_TREND = "PERFORMANCE_TREND", "性能趋势"
        ALERT_STATISTICS = "ALERT_STATISTICS", "告警统计"
        CUSTOM_METRICS = "CUSTOM_METRICS", "自定义指标"

    dashboard = models.ForeignKey(
        Dashboard, on_delete=models.CASCADE, related_name="widgets", verbose_name="所属仪表板"
    )
    name = models.CharField("名称", max_length=100)
    widget_type = models.CharField("组件类型", max_length=20, choices=WidgetType.choices)
    config = models.JSONField("配置", default=dict)
    position = models.JSONField("位置", default=dict)
    is_visible = models.IntegerField("是否可见", default=1)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "仪表板组件"
        verbose_name_plural = verbose_name
        ordering = ["dashboard", "created_at"]
        indexes = [
            models.Index(fields=["dashboard", "widget_type"]),
        ]

    def __str__(self):
        return f"{self.dashboard.name} - {self.name}"


class SystemMetrics(models.Model):
    """系统指标模型"""

    class MetricType(models.TextChoices):
        CPU = "cpu", "CPU使用率"
        MEMORY = "memory", "内存使用率"
        DISK = "disk", "磁盘使用率"
        NETWORK = "network", "网络流量"
        API_LATENCY = "api_latency", "API响应时间"
        ERROR_RATE = "error_rate", "错误率"
        REQUEST_COUNT = "request_count", "请求数"
        TASK_COUNT = "task_count", "任务数"

    metric_type = models.CharField("指标类型", max_length=20, choices=MetricType.choices)
    value = models.FloatField("指标值")
    timestamp = models.DateTimeField("记录时间", auto_now_add=True)
    metadata = models.JSONField("元数据", default=dict, blank=True)

    class Meta:
        verbose_name = "系统指标"
        verbose_name_plural = verbose_name
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["metric_type", "-timestamp"]),
        ]

    def __str__(self):
        return f"{self.get_metric_type_display()}: {self.value} ({self.timestamp})"
