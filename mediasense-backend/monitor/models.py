from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class MonitorRule(models.Model):
    """监控规则模型"""
    
    class Condition(models.TextChoices):
        GREATER_THAN = 'gt', _('大于')
        LESS_THAN = 'lt', _('小于')
        EQUAL_TO = 'eq', _('等于')
        NOT_EQUAL_TO = 'ne', _('不等于')
        GREATER_EQUAL = 'ge', _('大于等于')
        LESS_EQUAL = 'le', _('小于等于')

    name = models.CharField(_('规则名称'), max_length=100)
    metric = models.CharField(_('监控指标'), max_length=50)
    condition = models.CharField(_('条件'), max_length=2, choices=Condition.choices)
    threshold = models.FloatField(_('阈值'))
    duration = models.IntegerField(_('持续时间(秒)'))
    description = models.TextField(_('描述'), blank=True)
    is_active = models.BooleanField(_('是否启用'), default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('创建者'),
        on_delete=models.CASCADE,
        related_name='monitor_rules'
    )
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)

    class Meta:
        verbose_name = _('监控规则')
        verbose_name_plural = _('监控规则')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.metric} {self.get_condition_display()} {self.threshold})"

class MonitorAlert(models.Model):
    """监控告警模型"""
    
    class Status(models.TextChoices):
        ACTIVE = 'active', _('活动')
        RESOLVED = 'resolved', _('已解决')
        IGNORED = 'ignored', _('已忽略')

    rule = models.ForeignKey(
        MonitorRule,
        verbose_name=_('告警规则'),
        on_delete=models.CASCADE,
        related_name='alerts'
    )
    metric_value = models.FloatField(_('指标值'))
    status = models.CharField(
        _('状态'),
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    message = models.TextField(_('告警消息'))
    resolved_at = models.DateTimeField(_('解决时间'), null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('解决者'),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_alerts'
    )
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)

    class Meta:
        verbose_name = _('监控告警')
        verbose_name_plural = _('监控告警')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.rule.name} - {self.message[:50]}"

class SystemMetric(models.Model):
    """系统指标模型"""
    
    metric_name = models.CharField(_('指标名称'), max_length=50)
    value = models.FloatField(_('指标值'))
    unit = models.CharField(_('单位'), max_length=20)
    timestamp = models.DateTimeField(_('时间戳'), auto_now_add=True)
    metadata = models.JSONField(_('元数据'), default=dict, blank=True)

    class Meta:
        verbose_name = _('系统指标')
        verbose_name_plural = _('系统指标')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['metric_name', '-timestamp']),
            models.Index(fields=['-timestamp'])
        ]

    def __str__(self):
        return f"{self.metric_name}: {self.value}{self.unit}"

class ErrorLog(models.Model):
    """错误日志模型"""
    
    class Level(models.TextChoices):
        DEBUG = 'DEBUG', _('调试')
        INFO = 'INFO', _('信息')
        WARNING = 'WARNING', _('警告')
        ERROR = 'ERROR', _('错误')
        CRITICAL = 'CRITICAL', _('严重')

    timestamp = models.DateTimeField(_('时间戳'), auto_now_add=True)
    level = models.CharField(_('日志级别'), max_length=10, choices=Level.choices)
    service = models.CharField(_('服务名称'), max_length=50)
    message = models.TextField(_('错误消息'))
    traceback = models.TextField(_('错误堆栈'), blank=True)
    metadata = models.JSONField(_('元数据'), default=dict, blank=True)

    class Meta:
        verbose_name = _('错误日志')
        verbose_name_plural = _('错误日志')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['level', '-timestamp']),
            models.Index(fields=['service', '-timestamp'])
        ]

    def __str__(self):
        return f"[{self.level}] {self.service} - {self.message[:50]}"
