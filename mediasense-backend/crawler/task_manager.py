import logging
import threading
import time
from typing import Optional

from django.conf import settings

from .services import CrawlerService

logger = logging.getLogger(__name__)


class CrawlerTaskManager:
    """爬虫任务调度管理器"""

    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._check_interval = getattr(settings, "CRAWLER_CHECK_INTERVAL", 60)  # 默认60秒检查一次

    def start(self):
        """启动任务调度"""
        if self._running:
            logger.warning("任务调度管理器已在运行")
            return

        self._running = True
        self._thread = threading.Thread(target=self._run)
        self._thread.daemon = True
        self._thread.start()
        logger.info("任务调度管理器已启动")

    def stop(self):
        """停止任务调度"""
        if not self._running:
            logger.warning("任务调度管理器未在运行")
            return

        self._running = False
        if self._thread:
            self._thread.join()
            self._thread = None
        logger.info("任务调度管理器已停止")

    def _run(self):
        """运行任务调度循环"""
        while self._running:
            try:
                # 获取待执行的爬虫配置
                configs = CrawlerService.get_pending_configs()

                # 为每个配置创建并执行任务
                for config in configs:
                    try:
                        # 创建任务
                        task = CrawlerService.create_task(config)
                        if not task:
                            continue

                        # 执行任务
                        CrawlerService.run_task(task)

                    except Exception as e:
                        logger.error(f"处理爬虫配置 {config.name} 时出错: {str(e)}")
                        continue

            except Exception as e:
                logger.error(f"任务调度循环出错: {str(e)}")

            # 等待下次检查
            time.sleep(self._check_interval)


# 创建全局任务管理器实例
task_manager = CrawlerTaskManager()
