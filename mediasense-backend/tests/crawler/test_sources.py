"""
爬虫数据源测试模块
"""
import os
import sys
import django
import requests
from datetime import datetime
import pytz
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediasense.settings')
django.setup()

from crawler.models import CrawlerConfig, CrawlerTask
from news.models import NewsArticle

def test_rss_source(config):
    """测试 RSS 数据源"""
    print(f"\n开始测试 RSS 源: {config.name}")
    try:
        response = requests.get(config.source_url, headers=config.headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'xml')
        items = soup.select(config.config_data['item_selector'])
        
        if not items:
            print(f"❌ 错误: 未找到任何文章")
            return False
            
        print(f"✅ 成功: 找到 {len(items)} 篇文章")
        print(f"✅ 示例文章标题: {items[0].select_one(config.config_data['title_selector']).text.strip()}")
        return True
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return False

def test_api_source(config):
    """测试 API 数据源"""
    print(f"\n开始测试 API 源: {config.name}")
    try:
        params = config.config_data.get('params', {})
        response = requests.get(
            config.source_url,
            params=params,
            headers=config.headers,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        # 获取文章列表
        items_path = config.config_data.get('items_path', '')
        items = data
        if items_path:
            for key in items_path.split('.'):
                if key:
                    items = items.get(key, [])
        elif isinstance(data, list):
            items = data
        else:
            items = [data]
            
        if not items:
            print(f"❌ 错误: 未找到任何文章")
            return False
            
        print(f"✅ 成功: API 响应正常")
        print(f"✅ 数据示例: {items[0] if isinstance(items[0], (str, int)) else '(复杂数据结构)'}")
        return True
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return False

def test_web_source(config):
    """测试网页数据源"""
    print(f"\n开始测试网页源: {config.name}")
    try:
        response = requests.get(config.source_url, headers=config.headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        items = soup.select(config.config_data['list_selector'])
        
        if not items:
            print(f"❌ 错误: 未找到任何文章")
            return False
            
        print(f"✅ 成功: 找到 {len(items)} 篇文章")
        title = items[0].select_one(config.config_data['item_selectors']['title']).text.strip()
        print(f"✅ 示例文章标题: {title}")
        return True
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("=== 开始全面数据源测试 ===")
    
    # 测试统计
    total_sources = 0
    successful_sources = 0
    
    # 测试 RSS 源
    print("\n=== RSS 源测试 ===")
    rss_configs = CrawlerConfig.objects.filter(crawler_type=1, status=1)
    total_sources += rss_configs.count()
    for config in rss_configs:
        if test_rss_source(config):
            successful_sources += 1
    
    # 测试 API 源
    print("\n=== API 源测试 ===")
    api_configs = CrawlerConfig.objects.filter(crawler_type=2, status=1)
    total_sources += api_configs.count()
    for config in api_configs:
        if test_api_source(config):
            successful_sources += 1
    
    # 测试网页源
    print("\n=== 网页源测试 ===")
    web_configs = CrawlerConfig.objects.filter(crawler_type=3, status=1)
    total_sources += web_configs.count()
    for config in web_configs:
        if test_web_source(config):
            successful_sources += 1
    
    # 打印测试结果摘要
    print("\n=== 测试结果摘要 ===")
    print(f"总数据源数量: {total_sources}")
    print(f"成功数量: {successful_sources}")
    print(f"失败数量: {total_sources - successful_sources}")
    if total_sources > 0:
        print(f"成功率: {(successful_sources / total_sources * 100):.1f}%")
    else:
        print("成功率: N/A (没有数据源)")

if __name__ == '__main__':
    main() 