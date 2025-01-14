import html
import logging
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify

from .crawlers import APICrawler, RSSCrawler, WebCrawler
from .models import CrawlerConfig, CrawlerTask, ProxyPool

logger = logging.getLogger(__name__)


class CrawlerService:
    """爬虫服务"""

    CRAWLER_TYPES = {
        1: RSSCrawler,  # RSS爬虫
        2: APICrawler,  # API爬虫
        3: WebCrawler,  # 网页爬虫
    }

    @classmethod
    def get_crawler(cls, config: CrawlerConfig) -> Optional[RSSCrawler]:
        """
        根据配置获取爬虫实例
        :param config: 爬虫配置
        :return: 爬虫实例
        """
        crawler_class = cls.CRAWLER_TYPES.get(config.crawler_type)
        if not crawler_class:
            logger.error(f"不支持的爬虫类型: {config.crawler_type}")
            return None

        return crawler_class(
            {
                "source_url": config.source_url,
                "headers": config.headers,
                "source_name": config.name,
                **config.config_data,
            }
        )

    @classmethod
    def create_task(cls, config: CrawlerConfig) -> Optional[CrawlerTask]:
        """
        创建爬虫任务
        :param config: 爬虫配置
        :return: 爬虫任务
        """
        task = CrawlerTask.objects.create(
            config=config,
            task_id=str(uuid.uuid4()),
            status=CrawlerTask.Status.PENDING,
        )
        return task

    @classmethod
    def run_task(cls, task: CrawlerTask) -> bool:
        """
        执行爬虫任务
        :param task: 爬虫任务
        :return: 是否执行成功
        """
        try:
            # 更新任务状态为运行中
            task.status = 1
            task.start_time = timezone.now()
            task.save()

            # 获取爬虫实例
            crawler = cls.get_crawler(task.config)
            if not crawler:
                raise ValueError(f"无法创建爬虫实例: {task.config.name}")

            # 执行爬虫
            articles = crawler.crawl()

            # 更新任务状态为已完成
            task.status = 2
            task.end_time = timezone.now()
            task.result = {"total": len(articles), "articles": articles}
            task.save()

            # 更新配置最后运行时间
            task.config.last_run_time = task.end_time
            task.config.save()

            return True

        except Exception as e:
            logger.error(f"执行爬虫任务失败: {str(e)}")
            # 更新任务状态为出错
            task.status = 4
            task.end_time = timezone.now()
            task.error_message = str(e)
            task.save()
            return False

    @classmethod
    def get_pending_configs(cls) -> List[CrawlerConfig]:
        """
        获取待执行的爬虫配置
        :return: 配置列表
        """
        now = timezone.now()
        return (
            CrawlerConfig.objects.filter(status=1)  # 启用状态
            .filter(
                # 从未运行或已到达下次运行时间
                models.Q(last_run_time__isnull=True)
                | models.Q(last_run_time__lte=now - models.F("interval"))
            )
            .order_by("last_run_time")
        )


class ProxyPoolService:
    """代理池管理服务"""

    @classmethod
    def get_proxy(cls, protocol: str = "http") -> Optional[ProxyPool]:
        """获取一个可用代理"""
        return (
            ProxyPool.objects.filter(
                status=1,  # 可用状态
                protocol=protocol,
                success_rate__gte=0.7,  # 成功率大于70%
                speed__lte=2000,  # 响应速度小于2秒
            )
            .order_by("-success_rate", "speed")
            .first()
        )

    @classmethod
    def add_proxy(cls, ip: str, port: int, protocol: str = "http", location: str = "") -> ProxyPool:
        """添加新代理"""
        proxy = ProxyPool.objects.create(ip=ip, port=port, protocol=protocol, location=location)
        # 立即验证新代理
        proxy.check_availability()
        return proxy

    @classmethod
    def verify_proxies(cls) -> None:
        """验证所有代理"""
        # 获取所有未验证或最后验证时间超过1小时的代理
        proxies = ProxyPool.objects.filter(
            Q(status=0)  # 未验证
            | Q(last_check_time__lte=timezone.now() - timezone.timedelta(hours=1))  # 或超过1小时未验证
        )
        for proxy in proxies:
            proxy.check_availability()

    @classmethod
    def clean_invalid_proxies(cls) -> None:
        """清理无效代理"""
        # 删除成功率低于30%或连续3次验证失败的代理
        ProxyPool.objects.filter(
            Q(success_rate__lt=0.3)  # 成功率低于30%
            | Q(status=2, last_check_time__gte=timezone.now() - timezone.timedelta(hours=3))  # 最近3小时内验证失败
        ).delete()

    @classmethod
    def get_proxy_stats(cls) -> dict:
        """获取代理池统计信息"""
        total = ProxyPool.objects.count()
        available = ProxyPool.objects.filter(status=1).count()
        unavailable = ProxyPool.objects.filter(status=2).count()
        unverified = ProxyPool.objects.filter(status=0).count()

        return {
            "total": total,
            "available": available,
            "unavailable": unavailable,
            "unverified": unverified,
            "available_rate": round(available / total * 100, 2) if total > 0 else 0,
        }
