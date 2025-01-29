"""更新爬虫配置

更新指定爬虫的配置信息
"""

from django.core.management.base import BaseCommand
from crawler.models import CrawlerConfig
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '更新爬虫配置'

    def add_arguments(self, parser):
        parser.add_argument('name', type=str, help='爬虫名称')
        parser.add_argument('--status', type=int, choices=[0, 1], help='爬虫状态: 0-禁用, 1-启用')
        parser.add_argument('--description', type=str, help='爬虫描述')
        parser.add_argument('--source_url', type=str, help='数据源URL')
        parser.add_argument('--crawler_type', type=int, choices=[1, 2], help='爬虫类型: 1-RSS, 2-网页')
        parser.add_argument('--interval', type=int, help='抓取间隔(分钟)')

    def handle(self, *args, **options):
        name = options['name']
        
        try:
            config = CrawlerConfig.objects.get(name=name)
            
            # 更新状态
            if options['status'] is not None:
                config.status = options['status']
                
            # 更新描述
            if options['description']:
                config.description = options['description']
                
            # 更新源URL
            if options['source_url']:
                config.source_url = options['source_url']
                
            # 更新爬虫类型
            if options['crawler_type'] is not None:
                config.crawler_type = options['crawler_type']
                
            # 更新抓取间隔
            if options['interval'] is not None:
                config.interval = options['interval']
                
            config.save()
            
            self.stdout.write(f"成功更新{name}爬虫配置:")
            self.stdout.write(f"ID: {config.id}")
            self.stdout.write(f"描述: {config.description}")
            self.stdout.write(f"URL: {config.source_url}")
            self.stdout.write(f"类型: {'RSS' if config.crawler_type == 1 else '网页'}")
            self.stdout.write(f"状态: {'启用' if config.status == 1 else '禁用'}")
            self.stdout.write(f"间隔: {config.interval}分钟")
            
        except CrawlerConfig.DoesNotExist:
            self.stdout.write(f"错误: 找不到名为{name}的爬虫配置")
        except Exception as e:
            self.stdout.write(f"更新{name}爬虫配置失败: {str(e)}") 