from django.core.management.base import BaseCommand
from crawler.models import CrawlerConfig

class Command(BaseCommand):
    help = '初始化爬虫配置'

    def handle(self, *args, **options):
        configs = [
            {
                'name': '新浪新闻',
                'description': '新浪新闻API源',
                'source_url': 'https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&k=&num=50&page=1',
                'crawler_type': 2,  # API类型
                'config_data': {
                    'data_path': 'result.data'
                },
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Referer': 'https://news.sina.com.cn/'
                },
                'interval': 3600,
                'status': 1
            },
            {
                'name': '网易新闻',
                'description': '网易新闻API源',
                'source_url': 'https://3g.163.com/touch/reconstruct/article/list/BBM54PGAwangning/0-10.html',
                'crawler_type': 2,
                'config_data': {
                    'data_path': 'BBM54PGAwangning'
                },
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Referer': 'https://news.163.com/'
                },
                'interval': 3600,
                'status': 1
            },
            {
                'name': '凤凰新闻',
                'description': '凤凰新闻API源',
                'source_url': 'https://api.3g.ifeng.com/client_news_list?id=SYLB10,SYDT10&page=1',
                'crawler_type': 2,
                'config_data': {
                    'data_path': 'data'
                },
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Referer': 'https://news.ifeng.com/'
                },
                'interval': 3600,
                'status': 1
            }
        ]

        # 先清除现有配置
        CrawlerConfig.objects.all().delete()
        
        # 创建新配置
        for config in configs:
            CrawlerConfig.objects.create(**config)
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created crawler config for {config["name"]}')
            ) 