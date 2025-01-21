import logging
import uuid
from celery import shared_task
from django.utils import timezone

from .models import CrawlerTask, CrawlerConfig
from .services import CrawlerService

logger = logging.getLogger(__name__)


@shared_task
def crawl_single_website(config_id):
    """
    爬取单个网站的任务
    """
    try:
        # 获取配置
        config = CrawlerConfig.objects.get(id=config_id)
        
        # 检查是否有运行中的任务
        if CrawlerTask.objects.filter(config=config, status=1).exists():
            return {
                'status': 'skipped',
                'message': 'Task already running'
            }
            
        # 创建新任务
        task = CrawlerTask.objects.create(
            config=config,
            task_id=str(uuid.uuid4()),  # 使用UUID作为任务ID
            status=1,  # 运行中
            start_time=timezone.now()
        )
        
        try:
            # 执行爬虫
            result = CrawlerService.crawl_website(config, task)
            
            # 更新任务状态
            if result['status'] == 'success':
                task.status = 2  # 已完成
                task.result = result
            else:
                task.status = 4  # 失败
                task.error_message = result['message']
                
            task.end_time = timezone.now()
            task.save()
            
            return {
                'status': 'success',
                'task_id': task.task_id,
                'items_count': len(result.get('items', []))
            }
            
        except Exception as e:
            task.status = 4  # 失败
            task.end_time = timezone.now()
            task.error_message = str(e)
            task.save()
            
            return {
                'status': 'error',
                'message': str(e)
            }
            
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }

@shared_task
def schedule_crawlers():
    """
    调度所有启用的爬虫配置
    """
    configs = CrawlerConfig.objects.filter(status=1)  # 获取所有启用的配置
    
    for config in configs:
        # 检查上次运行时间
        if config.last_run_time:
            time_diff = timezone.now() - config.last_run_time
            if time_diff.total_seconds() < config.interval * 60:
                continue
                
        # 启动爬虫任务
        crawl_single_website.delay(config.id)
        
        # 更新上次运行时间
        config.last_run_time = timezone.now()
        config.save()
