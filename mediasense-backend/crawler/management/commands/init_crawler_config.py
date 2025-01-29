from django.core.management.base import BaseCommand
from crawler.models import CrawlerConfig
from django.utils import timezone

class Command(BaseCommand):
    help = '初始化爬虫配置'

    def handle(self, *args, **options):
        try:
            # 检查是否已存在
            if CrawlerConfig.objects.filter(name='凤凰新闻').exists():
                self.stdout.write(self.style.WARNING('凤凰新闻爬虫配置已存在'))
                return

            # 创建凤凰新闻爬虫配置
            config = CrawlerConfig.objects.create(
                name='凤凰新闻',
                description='爬取凤凰新闻API内容',
                source_url='https://api.ifeng.com/v1/news/feed',
                crawler_type=2,  # API类型
                config_data={
                    'data_path': 'data',
                    'title_path': 'title',
                    'content_path': 'content',
                    'link_path': 'url',
                    'pub_date_path': 'publish_time',
                    'description_path': 'digest'
                },
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'application/json',
                    'Referer': 'https://news.ifeng.com/'
                },
                interval=30,  # 30分钟抓取一次
                status=1,  # 启用状态
                is_active=True,
                max_retries=3,
                retry_delay=60
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'成功创建凤凰新闻爬虫配置:\n'
                                 f'- ID: {config.id}\n'
                                 f'- 名称: {config.name}\n'
                                 f'- URL: {config.source_url}\n'
                                 f'- 状态: {"启用" if config.is_active else "禁用"}\n'
                                 f'- 间隔: {config.interval}分钟')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'创建爬虫配置失败: {str(e)}')
            ) 