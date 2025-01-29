from django.core.management.base import BaseCommand, CommandError
from crawler.models import CrawlerConfig, CrawlerTask
from crawler.services import CrawlerService
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '运行新闻爬虫'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            help='指定爬虫源（例如：ifeng, sina）'
        )
        parser.add_argument(
            '--test',
            action='store_true',
            help='以测试模式运行爬虫'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制运行爬虫，忽略时间间隔限制'
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='限制抓取的文章数量'
        )

    def handle(self, *args, **options):
        source = options.get('source')
        is_test = options.get('test', False)
        force = options.get('force', False)
        limit = options.get('limit')

        try:
            # 获取爬虫配置
            try:
                config = CrawlerConfig.objects.get(name__icontains=source)
            except CrawlerConfig.DoesNotExist:
                raise CommandError(f'未找到爬虫配置: {source}')

            # 检查配置状态
            if config.status != 1:  # 1表示启用状态
                self.stdout.write(self.style.WARNING(f'爬虫 {source} 未启用'))
                return

            # 检查运行间隔（除非强制运行）
            if not force and config.last_run_time:
                next_run_time = config.last_run_time + timezone.timedelta(minutes=config.interval)
                if timezone.now() < next_run_time:
                    self.stdout.write(
                        self.style.WARNING(
                            f'爬虫 {source} 运行间隔未到\n'
                            f'上次运行: {config.last_run_time}\n'
                            f'下次运行: {next_run_time}'
                        )
                    )
                    return

            # 创建爬虫任务
            task = CrawlerTask.objects.create(
                config=config,
                is_test=is_test,
                status=CrawlerTask.Status.PENDING
            )

            # 运行爬虫服务
            self.stdout.write(self.style.SUCCESS(f'开始运行爬虫: {source}'))
            crawler_service = CrawlerService()
            result = crawler_service.run_task(task)

            # 输出结果
            if result:
                stats = task.result.get('stats', {})
                self.stdout.write(
                    self.style.SUCCESS(
                        f'爬虫运行完成: {source}\n'
                        f'- 任务ID: {task.task_id}\n'
                        f'- 总文章数: {stats.get("total", 0)}\n'
                        f'- 保存成功: {stats.get("saved", 0)}\n'
                        f'- 重复文章: {stats.get("duplicate", 0)}\n'
                        f'- 已过滤: {stats.get("filtered", 0)}\n'
                        f'- 错误数: {stats.get("error", 0)}\n'
                        f'- 耗时: {task.end_time - task.start_time}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'爬虫运行失败: {source}\n'
                        f'- 任务ID: {task.task_id}\n'
                        f'- 错误信息: {task.error_message}'
                    )
                )

        except Exception as e:
            logger.exception(f'爬虫运行异常: {str(e)}')
            self.stdout.write(self.style.ERROR(f'爬虫运行异常: {str(e)}')) 