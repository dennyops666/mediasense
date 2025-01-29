import os
import sys
import requests
import feedparser
from datetime import datetime
import json

# 添加项目根目录到Python路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediasense.settings')

import django
django.setup()

from crawler.models import CrawlerConfig
from crawler.services import CrawlerService

def test_rss_source(config):
    """测试RSS数据源"""
    print(f"\n测试RSS源: {config.name}")
    try:
        # 发送HTTP请求
        headers = config.headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(config.source_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # 解析RSS
        feed = feedparser.parse(response.content)
        
        if hasattr(feed, 'status') and feed.status != 200:
            print(f"RSS解析失败: status={feed.status}")
            return False
            
        if not hasattr(feed, 'entries') or len(feed.entries) == 0:
            print("RSS源没有文章")
            return False
            
        # 打印第一篇文章信息
        first_entry = feed.entries[0]
        print(f"最新文章:")
        print(f"- 标题: {first_entry.title if hasattr(first_entry, 'title') else 'N/A'}")
        print(f"- 链接: {first_entry.link if hasattr(first_entry, 'link') else 'N/A'}")
        print(f"- 发布时间: {first_entry.published if hasattr(first_entry, 'published') else 'N/A'}")
        
        return True
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return False

def test_all_sources():
    """测试所有数据源"""
    print("开始测试所有数据源...")
    
    # 获取所有启用的爬虫配置
    configs = CrawlerConfig.objects.filter(status=1)
    print(f"找到 {configs.count()} 个启用的爬虫配置")
    
    results = []
    for config in configs:
        if config.crawler_type == 1:  # RSS类型
            success = test_rss_source(config)
            results.append({
                'name': config.name,
                'url': config.source_url,
                'success': success
            })
    
    # 打印测试结果
    print("\n测试结果汇总:")
    success_count = sum(1 for r in results if r['success'])
    print(f"总数: {len(results)}")
    print(f"成功: {success_count}")
    print(f"失败: {len(results) - success_count}")
    
    print("\n详细结果:")
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"{status} {result['name']}: {result['url']}")

if __name__ == '__main__':
    test_all_sources() 