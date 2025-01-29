import os
import sys
import django
from datetime import datetime

# 添加项目根目录到Python路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediasense.settings')
django.setup()

from crawler.models import CrawlerConfig
from crawler.services import CrawlerService

def run_crawlers():
    """运行所有启用的爬虫"""
    print("开始运行爬虫任务...")
    
    # 获取所有启用的爬虫配置
    configs = CrawlerConfig.objects.filter(is_active=True)
    print(f"找到{len(configs)}个启用的爬虫配置")
    
    # 创建爬虫服务
    crawler_service = CrawlerService()
    
    # 统计信息
    total_stats = {
        'total': 0,
        'success': 0,
        'failed': 0,
        'articles': 0
    }
    
    # 遍历每个爬虫配置
    for config in configs:
        try:
            print(f"\n开始处理爬虫: {config.name}")
            result = crawler_service.crawl_website(config)
            
            if result['status'] == 'success':
                total_stats['success'] += 1
                total_stats['articles'] += result.get('stats', {}).get('saved', 0)
                print(f"爬取成功: {config.name}")
                print(f"统计信息:")
                print(f"- 总文章数: {result.get('stats', {}).get('total', 0)}")
                print(f"- 新增文章: {result.get('stats', {}).get('saved', 0)}")
                print(f"- 重复文章: {result.get('stats', {}).get('duplicated', 0)}")
                print(f"- 过滤文章: {result.get('stats', {}).get('filtered', 0)}")
                print(f"- 错误数: {result.get('stats', {}).get('errors', 0)}")
            else:
                total_stats['failed'] += 1
                print(f"爬取失败: {config.name}")
                print(f"错误信息: {result.get('message', '未知错误')}")
                
        except Exception as e:
            total_stats['failed'] += 1
            print(f"处理爬虫时出错: {config.name}")
            print(f"错误信息: {str(e)}")
            
        total_stats['total'] += 1
    
    # 打印总体统计信息
    print("\n爬虫任务完成!")
    print(f"总统计信息:")
    print(f"- 总爬虫数: {total_stats['total']}")
    print(f"- 成功数: {total_stats['success']}")
    print(f"- 失败数: {total_stats['failed']}")
    print(f"- 总新增文章: {total_stats['articles']}")

if __name__ == '__main__':
    run_crawlers() 