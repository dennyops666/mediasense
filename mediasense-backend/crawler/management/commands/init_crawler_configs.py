"""初始化爬虫配置

添加新的爬虫配置到数据库
"""

from django.core.management.base import BaseCommand
from crawler.models import CrawlerConfig
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '初始化爬虫配置'

    def handle(self, *args, **options):
        # 配置列表
        configs = [
            {
                'name': '科技爱好者周刊',
                'description': '阮一峰的科技爱好者周刊',
                'source_url': 'https://feeds.feedburner.com/ruanyifeng',
                'crawler_type': 1,
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                },
                'interval': 30,
                'is_active': True
            },
            {
                'name': 'InfoQ',
                'description': 'InfoQ中文站',
                'source_url': 'https://feed.infoq.cn/feed.xml',
                'crawler_type': 1,
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                },
                'interval': 30,
                'is_active': True
            },
            {
                'name': '开源中国',
                'description': '开源中国社区最新新闻',
                'source_url': 'https://www.oschina.net/news/rss',
                'crawler_type': 1,
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                },
                'interval': 30,
                'is_active': True
            },
            {
                'name': '36氪',
                'description': '36氪 - 让一部分人先看到未来',
                'source_url': 'https://www.36kr.com/feed',
                'crawler_type': 1,
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                },
                'interval': 30,
                'is_active': True
            },
            {
                'name': '虎嗅网',
                'description': '虎嗅网 - 科技和商业评论',
                'source_url': 'https://www.huxiu.com/rss/0.xml',
                'crawler_type': 1,
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                },
                'interval': 30,
                'is_active': True
            },
            {
                'name': '少数派',
                'description': '少数派 - 高品质数字消费指南',
                'source_url': 'https://sspai.com/feed',
                'crawler_type': 1,
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                },
                'interval': 30,
                'is_active': True
            },
            {
                'name': '爱范儿',
                'description': '爱范儿 - 让未来触手可及',
                'source_url': 'https://www.ifanr.com/feed',
                'crawler_type': 1,
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                },
                'interval': 30,
                'is_active': True
            },
            {
                'name': '极客公园',
                'description': '极客公园 - 科技创新者社区',
                'source_url': 'https://www.geekpark.net/rss',
                'crawler_type': 1,
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                },
                'interval': 30,
                'is_active': True
            },
            {
                'name': 'PingWest',
                'description': 'PingWest品玩 - 有品好玩的科技生活',
                'source_url': 'https://www.pingwest.com/feed',
                'crawler_type': 1,
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                },
                'interval': 30,
                'is_active': True
            }
        ]

        # 添加配置
        for config in configs:
            try:
                if CrawlerConfig.objects.filter(name=config['name']).exists():
                    self.stdout.write(f"{config['name']}爬虫配置已存在")
                    continue
                    
                crawler_config = CrawlerConfig.objects.create(
                    name=config['name'],
                    description=config['description'],
                    source_url=config['source_url'],
                    crawler_type=config['crawler_type'],
                    headers=config['headers'],
                    interval=config['interval'],
                    is_active=config['is_active']
                )
                
                self.stdout.write(f"成功创建{config['name']}爬虫配置:")
                self.stdout.write(f"ID: {crawler_config.id}")
                self.stdout.write(f"URL: {crawler_config.source_url}")
                self.stdout.write(f"状态: {'启用' if crawler_config.is_active else '禁用'}")
                self.stdout.write(f"间隔: {crawler_config.interval}分钟")
                
            except Exception as e:
                self.stdout.write(f"创建{config['name']}爬虫配置失败: {str(e)}")