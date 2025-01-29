import os
import psutil
import logging
import redis
import time
import platform
import django
from django.conf import settings
from django.db import connection
from django.core.cache import cache
from django.utils import timezone
from celery import current_app
from celery.app.control import Control
from asgiref.sync import sync_to_async
from .models import MonitorRule, MonitorAlert, SystemMetric

logger = logging.getLogger(__name__)

class MonitorService:
    """监控服务类"""

    async def collect_system_metrics(self):
        """收集系统指标"""
        try:
            # CPU使用率
            cpu_usage = psutil.cpu_percent(interval=1)
            await SystemMetric.objects.acreate(
                metric_name='cpu_usage',
                value=cpu_usage,
                unit='%'
            )

            # 内存使用率
            memory = psutil.virtual_memory()
            await SystemMetric.objects.acreate(
                metric_name='memory_usage',
                value=memory.percent,
                unit='%'
            )

            # 磁盘使用率
            disk = psutil.disk_usage('/')
            await SystemMetric.objects.acreate(
                metric_name='disk_usage',
                value=disk.percent,
                unit='%'
            )

            # 网络IO
            net_io = psutil.net_io_counters()
            await SystemMetric.objects.acreate(
                metric_name='network_io',
                value=net_io.bytes_sent + net_io.bytes_recv,
                unit='bytes',
                metadata={
                    'bytes_sent': net_io.bytes_sent,
                    'bytes_recv': net_io.bytes_recv
                }
            )

            return True
        except Exception as e:
            logger.error(f"收集系统指标失败: {str(e)}")
            return False

    async def check_system_health(self):
        """检查系统健康状态"""
        try:
            # 使用 sync_to_async 包装同步操作
            def check_all():
                # 检查数据库连接
                db_status = False
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT 1")
                        cursor.fetchone()
                    db_status = True
                except Exception as e:
                    print(f"数据库检查失败: {str(e)}")

                # 检查缓存服务
                cache_status = False
                try:
                    cache.set('health_check', 'ok', 1)
                    result = cache.get('health_check')
                    cache_status = result == 'ok'
                except Exception as e:
                    print(f"缓存检查失败: {str(e)}")

                # 检查 Celery 服务
                celery_status = False
                try:
                    control = Control(current_app)
                    workers = control.ping()
                    celery_status = len(workers) > 0
                except Exception as e:
                    print(f"Celery检查失败: {str(e)}")

                return db_status, cache_status, celery_status

            # 执行同步检查
            db_status, cache_status, celery_status = await sync_to_async(check_all)()
            
            # 所有服务都正常时返回健康状态
            if all([db_status, cache_status, celery_status]):
                return {"status": "healthy"}
            else:
                return {
                    "status": "unhealthy",
                    "details": {
                        "database": "healthy" if db_status else "unhealthy",
                        "cache": "healthy" if cache_status else "unhealthy",
                        "celery": "healthy" if celery_status else "unhealthy"
                    }
                }
        except Exception as e:
            print(f"健康检查失败: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def generate_health_report(self):
        """生成健康报告"""
        try:
            # 使用 sync_to_async 包装同步操作
            def get_system_info():
                return {
                    'hostname': os.uname().nodename,
                    'os': os.uname().sysname,
                    'version': os.uname().release,
                    'python_version': platform.python_version(),
                    'django_version': django.get_version()
                }

            def get_resource_usage():
                return {
                    'cpu': {
                        'usage': psutil.cpu_percent(interval=1),
                        'count': psutil.cpu_count()
                    },
                    'memory': {
                        'total': psutil.virtual_memory().total,
                        'available': psutil.virtual_memory().available,
                        'used': psutil.virtual_memory().used,
                        'percent': psutil.virtual_memory().percent
                    },
                    'disk': {
                        'total': psutil.disk_usage('/').total,
                        'used': psutil.disk_usage('/').used,
                        'free': psutil.disk_usage('/').free,
                        'percent': psutil.disk_usage('/').percent
                    }
                }

            # 获取系统信息和资源使用情况
            system_info = await sync_to_async(get_system_info)()
            resource_usage = await sync_to_async(get_resource_usage)()
            
            # 获取服务状态
            service_status = await self.check_system_health()

            return {
                'system_info': system_info,
                'resource_usage': resource_usage,
                'service_status': service_status,
                'timestamp': timezone.now()
            }
        except Exception as e:
            print(f"生成健康报告失败: {str(e)}")
            raise 