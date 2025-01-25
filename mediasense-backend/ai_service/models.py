from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from news.models import NewsArticle

User = get_user_model()


class AnalysisRule(models.Model):
    """自定义分析规则模型"""

    class RuleType(models.TextChoices):
        SENTIMENT = "sentiment", "情感分析"
        KEYWORDS = "keywords", "关键词提取"
        SUMMARY = "summary", "摘要生成"

    name = models.CharField(max_length=100, verbose_name="规则名称")
    rule_type = models.CharField(max_length=20, choices=RuleType.choices, verbose_name="规则类型")
    system_prompt = models.TextField(verbose_name="系统提示词", help_text="用于指导AI模型的系统提示词")
    user_prompt_template = models.TextField(
        verbose_name="用户提示词模板", help_text="用于生成用户提示词的模板，可使用{title}和{content}作为占位符"
    )
    parameters = models.JSONField(default=dict, verbose_name="分析参数", help_text="如temperature、max_tokens等参数")
    is_active = models.IntegerField(default=1, verbose_name="是否启用")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    description = models.TextField(blank=True, verbose_name="规则描述")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_rules", verbose_name="创建者"
    )

    class Meta:
        verbose_name = "分析规则"
        verbose_name_plural = "分析规则"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["rule_type", "is_active"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_rule_type_display()})"


class AnalysisResult(models.Model):
    """新闻分析结果模型"""

    class AnalysisType(models.TextChoices):
        SENTIMENT = "sentiment", "情感分析"
        KEYWORDS = "keywords", "关键词提取"
        SUMMARY = "summary", "摘要生成"

    news = models.ForeignKey(
        NewsArticle, on_delete=models.CASCADE, related_name="analysis_results", verbose_name="关联新闻"
    )
    analysis_type = models.CharField(max_length=20, choices=AnalysisType.choices, verbose_name="分析类型")
    result = models.JSONField(verbose_name="分析结果")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    is_valid = models.BooleanField(default=True, verbose_name="是否有效")
    error_message = models.TextField(blank=True, verbose_name="错误信息")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_analysis_results",
        verbose_name="创建者"
    )

    class Meta:
        verbose_name = "分析结果"
        verbose_name_plural = "分析结果"
        unique_together = ["news", "analysis_type"]
        indexes = [
            models.Index(fields=["news", "analysis_type"]),
            models.Index(fields=["created_at"]),
        ]


class AnalysisCache(models.Model):
    """分析结果缓存模型"""

    cache_key = models.CharField(max_length=255, unique=True, verbose_name="缓存键")
    result = models.JSONField(verbose_name="缓存结果")
    expires_at = models.DateTimeField(verbose_name="过期时间")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="创建时间")

    class Meta:
        verbose_name = "分析缓存"
        verbose_name_plural = "分析缓存"
        indexes = [
            models.Index(fields=["cache_key"]),
            models.Index(fields=["expires_at"]),
        ]


class BatchAnalysisTask(models.Model):
    """批量分析任务"""
    STATUS_CHOICES = (
        ('pending', '等待中'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('failed', '失败'),
        ('cancelled', '已取消')
    )

    name = models.CharField(max_length=100, verbose_name="任务名称", default="批量分析任务")
    rule = models.ForeignKey(
        AnalysisRule, 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True,
        related_name="batch_tasks", 
        verbose_name="分析规则"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="任务状态")
    total_count = models.IntegerField(default=0, verbose_name="总数量")
    processed = models.IntegerField(default=0, verbose_name="已处理数量")
    success = models.IntegerField(default=0, verbose_name="成功数量")
    failed = models.IntegerField(default=0, verbose_name="失败数量")
    error_message = models.TextField(blank=True, null=True, verbose_name="错误信息")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="创建时间")
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="开始时间")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="完成时间")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_batch_tasks",
        verbose_name="创建者"
    )
    config = models.JSONField(default=dict, verbose_name="配置信息", help_text="包含news_ids和analysis_types等配置")

    class Meta:
        verbose_name = "批量分析任务"
        verbose_name_plural = "批量分析任务"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["rule"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if not self.name and self.rule:
            # 如果没有提供名称，使用规则名称和时间戳生成默认名称
            timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
            self.name = f"{self.rule.name}_批量分析_{timestamp}"
        
        # 确保config字段包含必要的键
        if not isinstance(self.config, dict):
            self.config = {}
        if 'news_ids' not in self.config:
            self.config['news_ids'] = []
        if 'analysis_types' not in self.config:
            self.config['analysis_types'] = []
        
        super().save(*args, **kwargs)

    @property
    def duration(self):
        """任务持续时间(秒)"""
        if not self.completed_at or not self.started_at:
            return None
        return (self.completed_at - self.started_at).total_seconds()

    @property
    def success_rate(self):
        """成功率"""
        if self.total_count == 0:
            return 0
        return round(self.success / self.total_count * 100, 2)


class BatchAnalysisResult(models.Model):
    """批量分析结果"""

    task = models.ForeignKey(
        BatchAnalysisTask, on_delete=models.CASCADE, related_name="results", verbose_name="所属任务"
    )
    news_id = models.IntegerField("新闻ID")
    results = models.JSONField("分析结果")
    is_success = models.BooleanField("是否成功", default=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "批量分析结果"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]

    def __str__(self):
        return f"批量分析结果 {self.id}"


class AnalysisSchedule(models.Model):
    """分析任务调度"""

    class ScheduleType(models.TextChoices):
        INTERVAL = "interval", "间隔执行"
        CRON = "cron", "定时执行"

    name = models.CharField("调度名称", max_length=100)
    schedule_type = models.CharField(
        "调度类型", max_length=20, choices=ScheduleType.choices, default=ScheduleType.INTERVAL
    )

    # 间隔执行的配置
    interval_minutes = models.IntegerField("执行间隔(分钟)", null=True, blank=True, help_text="仅在间隔执行时使用")

    # 定时执行的配置
    cron_expression = models.CharField(
        "Cron表达式", max_length=100, null=True, blank=True, help_text="仅在定时执行时使用"
    )

    # 分析配置
    analysis_types = models.JSONField("分析类型列表", help_text="要执行的分析类型列表")
    categories = models.JSONField(
        "新闻分类", null=True, blank=True, help_text="要分析的新闻分类ID列表，为空则分析所有分类"
    )
    rules = models.ManyToManyField(AnalysisRule, blank=True, related_name="schedules", verbose_name="分析规则")

    # 时间范围配置
    time_window = models.IntegerField("时间窗口(分钟)", help_text="只分析最近n分钟内的新闻")

    is_active = models.IntegerField("是否启用", default=1)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="analysis_schedules", verbose_name="创建者"
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)
    last_run = models.DateTimeField("上次执行时间", null=True, blank=True)
    next_run = models.DateTimeField("下次执行时间", null=True, blank=True)

    class Meta:
        verbose_name = "分析任务调度"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def clean(self):
        if self.schedule_type == self.ScheduleType.INTERVAL:
            if not self.interval_minutes:
                raise ValidationError("间隔执行必须设置执行间隔")
            if self.interval_minutes < 1:
                raise ValidationError("执行间隔必须大于0")
        else:  # CRON
            if not self.cron_expression:
                raise ValidationError("定时执行必须设置Cron表达式")
            # TODO: 验证Cron表达式格式

    def calculate_next_run(self):
        """计算下次执行时间"""
        from datetime import datetime, timedelta

        from croniter import croniter

        now = timezone.now()

        if self.schedule_type == self.ScheduleType.INTERVAL:
            self.next_run = now + timedelta(minutes=self.interval_minutes)
        else:  # CRON
            cron = croniter(self.cron_expression, now)
            self.next_run = cron.get_next(datetime)

        return self.next_run


class ScheduleExecution(models.Model):
    """调度执行记录"""

    class Status(models.TextChoices):
        SUCCESS = "success", "成功"
        FAILED = "failed", "失败"

    schedule = models.ForeignKey(
        AnalysisSchedule, on_delete=models.CASCADE, related_name="executions", verbose_name="所属调度"
    )
    status = models.CharField("执行状态", max_length=20, choices=Status.choices)
    started_at = models.DateTimeField("开始时间", auto_now_add=True)
    completed_at = models.DateTimeField("完成时间", null=True)
    total_articles = models.IntegerField("总文章数", default=0)
    processed_articles = models.IntegerField("已处理文章数", default=0)
    success_articles = models.IntegerField("成功处理文章数", default=0)
    error_message = models.TextField("错误信息", blank=True)

    class Meta:
        verbose_name = "调度执行记录"
        verbose_name_plural = verbose_name
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.schedule.name} - {self.started_at}"

    @property
    def duration(self):
        """执行持续时间（秒）"""
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class AnalysisNotification(models.Model):
    """分析通知模型"""

    class NotificationType(models.TextChoices):
        ANALYSIS_COMPLETE = "analysis_complete", "分析完成"
        ANALYSIS_ERROR = "analysis_error", "分析错误"
        BATCH_COMPLETE = "batch_complete", "批量分析完成"
        SCHEDULE_COMPLETE = "schedule_complete", "调度执行完成"

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="analysis_notifications", verbose_name="接收用户"
    )
    notification_type = models.CharField("通知类型", max_length=20, choices=NotificationType.choices)
    title = models.CharField("通知标题", max_length=200)
    content = models.TextField("通知内容")
    data = models.JSONField("相关数据", default=dict)
    is_read = models.BooleanField("是否已读", default=False)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "分析通知"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["notification_type"]),
        ]

    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.title}"


class NotificationSubscription(models.Model):
    """通知订阅配置"""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="notification_subscription", verbose_name="用户"
    )
    email_enabled = models.BooleanField("启用邮件通知", default=True)
    websocket_enabled = models.BooleanField("启用WebSocket通知", default=True)
    notify_on_complete = models.BooleanField("分析完成时通知", default=True)
    notify_on_error = models.BooleanField("分析错误时通知", default=True)
    notify_on_batch = models.BooleanField("批量分析完成时通知", default=True)
    notify_on_schedule = models.BooleanField("调度执行完成时通知", default=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "通知订阅"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.user.username}的通知订阅"


class AnalysisVisualization(models.Model):
    """分析结果可视化数据模型"""

    class ChartType(models.TextChoices):
        LINE = "line", "折线图"
        BAR = "bar", "柱状图"
        PIE = "pie", "饼图"
        RADAR = "radar", "雷达图"

    name = models.CharField("图表名称", max_length=100)
    description = models.TextField("图表描述", blank=True)
    chart_type = models.CharField("图表类型", max_length=20, choices=ChartType.choices, default=ChartType.LINE)
    data_type = models.CharField(max_length=20, choices=AnalysisResult.AnalysisType.choices, verbose_name="数据类型")
    time_range = models.IntegerField("时间范围(天)", default=7, help_text="统计最近n天的数据")
    categories = models.JSONField(
        "新闻分类", null=True, blank=True, help_text="要统计的新闻分类ID列表，为空则统计所有分类"
    )
    aggregation_field = models.CharField("聚合字段", max_length=50, help_text="要统计的字段名称")
    aggregation_method = models.CharField(
        "聚合方法",
        max_length=20,
        choices=[("count", "计数"), ("avg", "平均值"), ("sum", "求和"), ("max", "最大值"), ("min", "最小值")],
        default="count",
    )
    group_by = models.CharField("分组字段", max_length=50, help_text="按此字段分组统计")
    filters = models.JSONField("过滤条件", default=dict, help_text="JSON格式的过滤条件")
    is_active = models.IntegerField("是否启用", default=1)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="visualizations", verbose_name="创建者"
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name="创建时间")
    updated_at = models.DateTimeField("更新时间", auto_now=True)
    last_generated = models.DateTimeField("上次生成时间", null=True, blank=True)
    cached_data = models.JSONField("缓存数据", null=True, blank=True, help_text="缓存的图表数据")

    class Meta:
        verbose_name = "分析可视化"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["data_type", "is_active"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_chart_type_display()})"

    def clean(self):
        """验证数据"""
        if self.time_range < 1:
            raise ValidationError("时间范围必须大于0")


class Notification(models.Model):
    """通知模型"""

    class NotificationType(models.TextChoices):
        ANALYSIS_COMPLETE = "analysis_complete", "分析完成"
        RULE_CREATED = "rule_created", "规则创建"
        TASK_COMPLETE = "task_complete", "任务完成"
        SYSTEM = "system", "系统通知"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="用户"
    )
    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
        verbose_name="通知类型"
    )
    title = models.CharField(max_length=200, verbose_name="通知标题")
    content = models.TextField(verbose_name="通知内容")
    is_read = models.BooleanField(default=False, verbose_name="是否已读")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    related_object_id = models.IntegerField(null=True, blank=True, verbose_name="相关对象ID")
    related_object_type = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="相关对象类型"
    )

    class Meta:
        verbose_name = "通知"
        verbose_name_plural = "通知"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["notification_type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_notification_type_display()})"

    @classmethod
    def create_notification(cls, user, notification_type, title, content, related_object=None):
        """
        创建通知的便捷方法
        """
        notification = cls(
            user=user,
            notification_type=notification_type,
            title=title,
            content=content
        )
        if related_object:
            notification.related_object_id = related_object.id
            notification.related_object_type = related_object.__class__.__name__
        notification.save()
        return notification
