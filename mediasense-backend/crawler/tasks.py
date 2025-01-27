import logging
import uuid
from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone
from datetime import timedelta

from .models import CrawlerTask, CrawlerConfig
from .services import CrawlerService

# 配置爬虫日志
logger = get_task_logger(__name__)
file_handler = logging.FileHandler('logs/crawler.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s %(asctime)s %(name)s %(process)d %(thread)d %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


@shared_task(bind=True)
def run_crawler(self, task_id):
    """
    运行爬虫任务
    :param task_id: 任务ID
    :return: 爬虫结果
    """
    try:
        # 获取任务
        task = CrawlerTask.objects.get(task_id=task_id)
        if not task:
            logger.error(f"任务不存在: {task_id}")
            return
            
        # 更新任务状态
        task.status = 1  # running
        task.start_time = timezone.now()
        task.save()
        
        # 执行爬虫
        result = CrawlerService.crawl_website(task.config, task)
        
        # 更新任务状态和结果
        if result['status'] == 'success':
            task.status = 2  # completed
            task.result = result
        else:
            task.status = 4  # failed
            task.error_message = result.get('message', '未知错误')
            
        task.end_time = timezone.now()
        task.save()
        
        return result
        
    except Exception as e:
        logger.error(f"爬虫任务执行失败: {str(e)}", exc_info=True)
        if task:
            task.status = 4  # failed
            task.error_message = str(e)
            task.end_time = timezone.now()
            task.save()
        return {
            'status': 'error',
            'message': str(e)
        }


@shared_task
def schedule_crawlers():
    """
    调度爬虫任务
    """
    logger.info("开始调度爬虫任务")
    
    # 获取所有启用的爬虫配置
    configs = CrawlerConfig.objects.filter(
        status=1,  # 启用状态
        is_active=True
    )
    
    for config in configs:
        try:
            # 检查是否需要运行
            if config.last_run_time:
                next_run_time = config.last_run_time + timedelta(minutes=config.interval)
                if timezone.now() < next_run_time:
                    logger.info(f"爬虫 {config.name} 未到运行时间")
                    continue
                    
            # 创建任务
            task = CrawlerTask.objects.create(
                config=config,
                status=0  # pending
            )
            
            # 更新最后运行时间
            config.last_run_time = timezone.now()
            config.save()
            
            # 启动任务
            run_crawler.delay(task.task_id)
            logger.info(f"已创建爬虫任务: {config.name}")
            
        except Exception as e:
            logger.error(f"调度爬虫失败 {config.name}: {str(e)}", exc_info=True)
