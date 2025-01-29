from django.core.management.base import BaseCommand
from crawler.models import CrawlerConfig
from crawler.services import CrawlerService

class Command(BaseCommand):
    help = '运行指定的爬虫任务'

    def add_arguments(self, parser):
        parser.add_argument('crawler_name', type=str, help='爬虫名称')

    def handle(self, *args, **options):
        crawler_name = options['crawler_name']
        
        try:
            # 获取爬虫配置
            config = CrawlerConfig.objects.get(name=crawler_name)
            
            # 创建并执行任务
            task = CrawlerService.create_task(config)
            if not task:
                self.stdout.write(self.style.ERROR(f'创建任务失败: {crawler_name}'))
                return
                
            result = CrawlerService.run_task(task)
            if result:
                self.stdout.write(self.style.SUCCESS(f'爬虫任务执行成功: {crawler_name}'))
            else:
                self.stdout.write(self.style.ERROR(f'爬虫任务执行失败: {crawler_name}'))
                
        except CrawlerConfig.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'找不到爬虫配置: {crawler_name}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'执行出错: {str(e)}')) 