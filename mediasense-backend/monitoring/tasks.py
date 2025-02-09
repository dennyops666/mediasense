import psutil
import logging
from celery import shared_task
from django.utils import timezone
from .models import SystemMetrics

logger = logging.getLogger(__name__)

@shared_task
def collect_system_metrics():
    """收集系统指标"""
    try:
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        SystemMetrics.objects.create(
            metric_type='cpu_usage',
            value=cpu_percent,
            timestamp=timezone.now()
        )

        # 内存使用率
        memory = psutil.virtual_memory()
        SystemMetrics.objects.create(
            metric_type='memory_usage',
            value=memory.percent,
            timestamp=timezone.now()
        )

        # 磁盘使用率
        disk = psutil.disk_usage('/')
        SystemMetrics.objects.create(
            metric_type='disk_usage',
            value=disk.percent,
            timestamp=timezone.now()
        )

        # 系统负载
        load = psutil.getloadavg()
        SystemMetrics.objects.create(
            metric_type='system_load',
            value=load[0],  # 1分钟负载
            timestamp=timezone.now()
        )

        logger.info("系统指标收集成功")
        return True
    except Exception as e:
        logger.error(f"系统指标收集失败: {str(e)}")
        return False 