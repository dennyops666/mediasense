import json
import requests

# 示例爬虫配置
sample_configs = [
    {
        "name": "科技新闻RSS",
        "description": "科技新闻RSS爬虫",
        "source_url": "http://example.com/tech/rss",
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
        "name": "环境新闻API",
        "description": "环境新闻API爬虫",
        "source_url": "http://example.com/env/api",
        "crawler_type": 2,
        "config_data": {
            "title_path": "data.title",
            "content_path": "data.content",
            "link_path": "data.url",
            "pub_date_path": "data.published_at"
        },
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json"
        },
        "interval": 1800,
        "max_retries": 3,
        "retry_delay": 300,
        "status": 1,
        "is_active": True
    },
    {
        "name": "科技博客网页",
        "description": "科技博客网页爬虫",
        "source_url": "http://example.com/tech/blog",
        "crawler_type": 3,
        "config_data": {
            "title_selector": "h1.post-title",
            "content_selector": "div.post-content",
            "link_selector": "a.post-link",
            "pub_date_selector": "span.post-date"
        },
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        },
        "interval": 7200,
        "max_retries": 3,
        "retry_delay": 300,
        "status": 1,
        "is_active": True
    }
]

# 获取访问令牌
auth_response = requests.post(
    'http://localhost:8000/api/auth/token/',
    json={'username': 'admin', 'password': 'admin@123456'}
)
auth_data = auth_response.json()
access_token = auth_data['access']

# 创建爬虫配置
response = requests.post(
    'http://localhost:8000/api/crawler/configs/bulk_create/',
    headers={
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    },
    json=sample_configs
)

print(f"Status Code: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}") 