import os

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# 设置默认Django settings模块
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mediasense.settings")

# 创建Celery应用
app = Celery("mediasense")

# 使用Django的settings文件配置Celery
app.config_from_object("django.conf:settings", namespace="CELERY")

# 自动发现任务
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# 配置定时任务
app.conf.beat_schedule = {
    # 每小时验证一次代理池
    "verify-proxy-pool": {
        "task": "crawler.verify_proxy_pool",
        "schedule": crontab(minute=0),  # 每小时整点执行
    },
    # 每天凌晨2点清理无效代理
    "clean-proxy-pool": {
        "task": "crawler.clean_proxy_pool",
        "schedule": crontab(hour=2, minute=0),  # 每天凌晨2点执行
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
