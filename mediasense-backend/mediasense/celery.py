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
app.autodiscover_tasks()

# 配置定时任务
app.conf.beat_schedule = {
    'crawl-news-every-hour': {
        'task': 'crawler.tasks.schedule_crawlers',
        'schedule': crontab(minute='0'),  # 每小时执行一次
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
