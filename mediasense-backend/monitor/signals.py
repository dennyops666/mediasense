import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import MonitorRule, MonitorAlert, SystemMetric
from .services import MonitorService

logger = logging.getLogger(__name__)

@receiver(post_save, sender=SystemMetric)
def check_metric_alerts(sender, instance, created, **kwargs):
    """检查指标是否触发告警"""
    if not created:
        return

    try:
        # 获取相关的告警规则
        rules = MonitorRule.objects.filter(
            metric=instance.metric_name,
            is_active=True
        )

        for rule in rules:
            # 检查是否满足告警条件
            should_alert = False
            
            if rule.condition == MonitorRule.Condition.GREATER_THAN:
                should_alert = instance.value > rule.threshold
            elif rule.condition == MonitorRule.Condition.LESS_THAN:
                should_alert = instance.value < rule.threshold
            elif rule.condition == MonitorRule.Condition.EQUAL_TO:
                should_alert = instance.value == rule.threshold
            elif rule.condition == MonitorRule.Condition.NOT_EQUAL_TO:
                should_alert = instance.value != rule.threshold
            elif rule.condition == MonitorRule.Condition.GREATER_EQUAL:
                should_alert = instance.value >= rule.threshold
            elif rule.condition == MonitorRule.Condition.LESS_EQUAL:
                should_alert = instance.value <= rule.threshold

            if should_alert:
                # 检查是否已存在活动告警
                existing_alert = MonitorAlert.objects.filter(
                    rule=rule,
                    status=MonitorAlert.Status.ACTIVE
                ).first()

                if not existing_alert:
                    # 创建新告警
                    MonitorAlert.objects.create(
                        rule=rule,
                        metric_value=instance.value,
                        message=f"{rule.name}告警: 当前值{instance.value}{instance.unit}超过阈值{rule.threshold}"
                    )
                    logger.info(f"创建新告警: {rule.name}")

    except Exception as e:
        logger.error(f"处理指标告警失败: {str(e)}")

@receiver(post_save, sender=MonitorAlert)
def handle_alert_status_change(sender, instance, created, **kwargs):
    """处理告警状态变更"""
    if not created and instance.status in [MonitorAlert.Status.RESOLVED, MonitorAlert.Status.IGNORED]:
        try:
            # 更新解决时间
            if not instance.resolved_at:
                instance.resolved_at = timezone.now()
                instance.save(update_fields=['resolved_at'])
                
            logger.info(f"告警 {instance.id} 状态更新为 {instance.status}")
            
        except Exception as e:
            logger.error(f"处理告警状态变更失败: {str(e)}")

@receiver(post_save, sender=MonitorRule)
def handle_rule_status_change(sender, instance, created, **kwargs):
    """处理规则状态变更"""
    if not created and not instance.is_active:
        try:
            # 关闭该规则的所有活动告警
            active_alerts = MonitorAlert.objects.filter(
                rule=instance,
                status=MonitorAlert.Status.ACTIVE
            )
            
            for alert in active_alerts:
                alert.status = MonitorAlert.Status.RESOLVED
                alert.resolved_at = timezone.now()
                alert.save()
                
            logger.info(f"规则 {instance.name} 已禁用，关闭相关告警")
            
        except Exception as e:
            logger.error(f"处理规则状态变更失败: {str(e)}")