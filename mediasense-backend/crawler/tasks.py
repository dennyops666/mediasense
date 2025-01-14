import logging

from celery import shared_task
from django.utils import timezone

from .models import CrawlerTask
from .services import CrawlerService, ProxyPoolService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def execute_crawler_task(self, task_id: int):
    """
    执行爬虫任务的Celery任务

    Args:
        task_id: 爬虫任务ID
    """
    try:
        # 获取任务实例
        task = CrawlerTask.objects.get(id=task_id)

        # 更新任务状态为执行中
        task.status = CrawlerTask.Status.RUNNING
        task.start_time = timezone.now()
        task.save()

        # 执行任务
        CrawlerService.run_task(task)

    except CrawlerTask.DoesNotExist:
        logger.error(f"爬虫任务 {task_id} 不存在")

    except Exception as e:
        logger.error(f"执行爬虫任务 {task_id} 时出错: {str(e)}")
        # 重试任务
        try:
            self.retry(countdown=60 * (self.request.retries + 1))
        except self.MaxRetriesExceededError:
            # 更新任务状态为失败
            task = CrawlerTask.objects.get(id=task_id)
            task.status = CrawlerTask.Status.FAILED
            task.error_message = str(e)
            task.end_time = timezone.now()
            task.save()


@shared_task
def check_crawler_tasks():
    """
    检查并创建新的爬虫任务
    """
    try:
        # 获取待执行的爬虫配置
        configs = CrawlerService.get_pending_configs()

        # 为每个配置创建任务
        for config in configs:
            try:
                task = CrawlerService.create_task(config)
                if task:
                    # 异步执行任务
                    execute_crawler_task.delay(task.id)

            except Exception as e:
                logger.error(f"为爬虫配置 {config.name} 创建任务时出错: {str(e)}")
                continue

    except Exception as e:
        logger.error(f"检查爬虫任务时出错: {str(e)}")


@shared_task(name="crawler.verify_proxy_pool", bind=True, max_retries=3, default_retry_delay=300)  # 5分钟后重试
def verify_proxy_pool(self):
    """验证代理池中的代理"""
    try:
        logger.info("开始验证代理池...")
        ProxyPoolService.verify_proxies()

        # 获取代理池统计信息
        stats = ProxyPoolService.get_proxy_stats()
        logger.info(f"代理池验证完成: {stats}")

        return {"status": "success", "stats": stats}

    except Exception as e:
        logger.error(f"验证代理池失败: {str(e)}")
        raise self.retry(exc=e)


@shared_task(name="crawler.clean_proxy_pool", bind=True, max_retries=3, default_retry_delay=300)
def clean_proxy_pool(self):
    """清理无效代理"""
    try:
        logger.info("开始清理无效代理...")

        # 获取清理前的统计信息
        before_stats = ProxyPoolService.get_proxy_stats()

        # 执行清理
        ProxyPoolService.clean_invalid_proxies()

        # 获取清理后的统计信息
        after_stats = ProxyPoolService.get_proxy_stats()

        removed_count = before_stats["total"] - after_stats["total"]
        logger.info(f"代理池清理完成,删除了 {removed_count} 个无效代理")

        return {
            "status": "success",
            "removed_count": removed_count,
            "before_stats": before_stats,
            "after_stats": after_stats,
        }

    except Exception as e:
        logger.error(f"清理代理池失败: {str(e)}")
        raise self.retry(exc=e)
