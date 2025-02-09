import os
import django
import json
import time
from datetime import datetime, timedelta

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediasense.settings')
django.setup()

from crawler.models import CrawlerTask

def check_task_status():
    """检查测试任务的状态"""
    # 获取最近创建的测试任务
    tasks = CrawlerTask.objects.filter(
        created_at__gte=datetime.now() - timedelta(hours=1)
    ).select_related('config').order_by('-created_at')

    if not tasks:
        print("\n没有找到最近的测试任务")
        return

    print("\n检查测试任务状态...")
    for task in tasks:
        print(f"\n数据源: {task.config.name}")
        print(f"任务ID: {task.task_id}")
        print(f"状态: {task.status}")
        print(f"开始时间: {task.start_time}")
        print(f"结束时间: {task.end_time}")
        if task.result:
            print("结果:", json.dumps(task.result, ensure_ascii=False, indent=2))
        print("-" * 50)

def main():
    """主函数"""
    while True:
        check_task_status()
        print("\n等待30秒后重新检查...")
        time.sleep(30)

if __name__ == "__main__":
    main() 