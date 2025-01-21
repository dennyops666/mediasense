import os
import django
import uuid
import datetime
import requests
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediasense.settings')
django.setup()

from crawler.tasks import schedule_crawlers
from crawler.models import CrawlerConfig, CrawlerTask
from crawler.services import CrawlerService

def check_api_response(config):
    """检查API响应"""
    print(f"\n检查 {config.name} API响应:")
    try:
        headers = config.headers or {}
        response = requests.get(config.source_url, headers=headers, timeout=30)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text[:1000]}")
        try:
            json_data = response.json()
            print(f"JSON数据: {json.dumps(json_data, ensure_ascii=False, indent=2)[:1000]}")
        except:
            print("响应不是有效的JSON格式")
    except Exception as e:
        print(f"请求失败: {str(e)}")

def main():
    print("开始执行爬虫任务...")
    
    # 获取所有启用的爬虫配置
    configs = CrawlerConfig.objects.filter(status=1)
    print(f"找到 {configs.count()} 个启用的爬虫配置")
    
    for config in configs:
        print(f"\n处理爬虫配置: {config.name}")
        
        # 先检查API响应
        check_api_response(config)
        
        try:
            # 生成唯一任务ID
            task_id = str(uuid.uuid4())
            
            # 创建爬虫任务
            task = CrawlerTask.objects.create(
                config=config,
                task_id=task_id,
                status=0,  # 未开始状态
                start_time=datetime.datetime.now()
            )
            
            # 执行爬虫任务
            result = CrawlerService.run_task(task)
            print(f"任务执行结果: {'成功' if result else '失败'}")
            
            # 打印任务详情
            if task.result:
                print(f"抓取数据: {task.result.get('items_count', 0)} 条")
                if 'stats' in task.result:
                    stats = task.result['stats']
                    print(f"统计信息:")
                    print(f"- 总数: {stats.get('total', 0)}")
                    print(f"- 保存: {stats.get('saved', 0)}")
                    print(f"- 过滤: {stats.get('filtered', 0)}")
                    print(f"- 错误: {stats.get('error', 0)}")
                    print(f"- 重复: {stats.get('duplicate', 0)}")
            
            if task.error_message:
                print(f"错误信息: {task.error_message}")
                
        except Exception as e:
            print(f"执行失败: {str(e)}")
            
    print("\n爬虫任务执行完成")

if __name__ == '__main__':
    main() 