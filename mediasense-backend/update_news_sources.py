import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediasense.settings')
django.setup()

from crawler.models import CrawlerConfig

# 定义新的数据源
NEW_SOURCES = [
    {
        "name": "人民网新闻",
        "description": "人民网RSS新闻源",
        "source_url": "https://www.people.com.cn/rss/politics.xml",
        "crawler_type": 1,
        "config_data": {
            "title_path": "title",
            "content_path": "description",
            "link_path": "link",
            "pub_date_path": "pubDate"
        },
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        },
        "interval": 3600,
        "max_retries": 3,
        "retry_delay": 300,
        "status": 1,
        "is_active": True
    },
    {
        "name": "新华网新闻",
        "description": "新华网RSS新闻源",
        "source_url": "https://www.xinhuanet.com/politics/news_politics.xml",
        "crawler_type": 1,
        "config_data": {
            "title_path": "title",
            "content_path": "description",
            "link_path": "link",
            "pub_date_path": "pubDate"
        },
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        },
        "interval": 3600,
        "max_retries": 3,
        "retry_delay": 300,
        "status": 1,
        "is_active": True
    },
    {
        "name": "中国科技网新闻",
        "description": "中国科技网科技新闻RSS源",
        "source_url": "https://www.stdaily.com/rss/zhxw.xml",
        "crawler_type": 1,
        "config_data": {
            "title_path": "title",
            "content_path": "description",
            "link_path": "link",
            "pub_date_path": "pubDate"
        },
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        },
        "interval": 3600,
        "max_retries": 3,
        "retry_delay": 300,
        "status": 1,
        "is_active": True
    },
    {
        "name": "科学网新闻",
        "description": "科学网科技新闻RSS源",
        "source_url": "https://www.sciencenet.cn/xml/news.aspx?di=0",
        "crawler_type": 1,
        "config_data": {
            "title_path": "title",
            "content_path": "description",
            "link_path": "link",
            "pub_date_path": "pubDate"
        },
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        },
        "interval": 3600,
        "max_retries": 3,
        "retry_delay": 300,
        "status": 1,
        "is_active": True
    },
    {
        "name": "中国新闻网",
        "description": "中国新闻网RSS新闻源",
        "source_url": "https://www.chinanews.com.cn/rss/scroll-news.xml",
        "crawler_type": 1,
        "config_data": {
            "title_path": "title",
            "content_path": "description",
            "link_path": "link",
            "pub_date_path": "pubDate"
        },
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        },
        "interval": 3600,
        "max_retries": 3,
        "retry_delay": 300,
        "status": 1,
        "is_active": True
    }
]

def update_sources():
    """更新数据源"""
    try:
        # 清除现有配置
        CrawlerConfig.objects.all().delete()
        print("已清除现有配置")

        # 添加新配置
        for source in NEW_SOURCES:
            CrawlerConfig.objects.create(**source)
            print(f"已添加新数据源: {source['name']}")

        print("数据源更新完成!")
    except Exception as e:
        print(f"更新失败: {str(e)}")

if __name__ == "__main__":
    update_sources() 