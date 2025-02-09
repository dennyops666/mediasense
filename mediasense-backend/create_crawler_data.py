import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediasense.settings')
django.setup()

from django.utils import timezone
from crawler.models import CrawlerConfig, CrawlerTask, NewsArticle
import requests
import feedparser
from datetime import datetime
import pytz
from time import mktime
from urllib.parse import urljoin

def create_rss_configs():
    """创建 RSS 数据源配置"""
    rss_sources = [
        {
            'name': 'OSChina 资讯',
            'description': 'OSChina 资讯 RSS 源',
            'source_url': 'https://www.oschina.net/news/rss',
            'crawler_type': 1,  # RSS
            'config_data': {
                'item_selector': 'item',
                'title_selector': 'title',
                'link_selector': 'link',
                'description_selector': 'description',
                'pub_date_selector': 'pubDate'
            },
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            },
            'interval': 30,  # 30分钟
            'status': 1  # 启用
        },
        {
            'name': '掘金专栏',
            'description': '掘金专栏 RSS 源',
            'source_url': 'https://juejin.cn/rss',
            'crawler_type': 1,  # RSS
            'config_data': {
                'item_selector': 'item',
                'title_selector': 'title',
                'link_selector': 'link',
                'description_selector': 'description',
                'pub_date_selector': 'pubDate'
            },
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            },
            'interval': 30,  # 30分钟
            'status': 1  # 启用
        },
        {
            'name': 'Stack Overflow Blog',
            'description': 'Stack Overflow 官方博客',
            'source_url': 'https://stackoverflow.blog/feed/',
            'crawler_type': 1,  # RSS
            'config_data': {
                'item_selector': 'item',
                'title_selector': 'title',
                'link_selector': 'link',
                'description_selector': 'description',
                'pub_date_selector': 'pubDate'
            },
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            },
            'interval': 60,  # 60分钟
            'status': 1  # 启用
        },
        {
            'name': 'Reddit Programming',
            'description': 'Reddit Programming 子版块',
            'source_url': 'https://www.reddit.com/r/programming/.rss',
            'crawler_type': 1,  # RSS
            'config_data': {
                'item_selector': 'entry',
                'title_selector': 'title',
                'link_selector': 'link',
                'description_selector': 'content',
                'pub_date_selector': 'updated'
            },
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            },
            'interval': 30,  # 30分钟
            'status': 1  # 启用
        },
        {
            'name': '知乎专栏 - 技术',
            'description': '知乎技术专栏',
            'source_url': 'https://www.zhihu.com/rss',
            'crawler_type': 1,  # RSS
            'config_data': {
                'item_selector': 'item',
                'title_selector': 'title',
                'link_selector': 'link',
                'description_selector': 'description',
                'pub_date_selector': 'pubDate'
            },
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            },
            'interval': 30,  # 30分钟
            'status': 1  # 启用
        },
        {
            'name': 'Medium Engineering',
            'description': 'Medium Engineering Blog',
            'source_url': 'https://medium.engineering/feed',
            'crawler_type': 1,  # RSS
            'config_data': {
                'item_selector': 'item',
                'title_selector': 'title',
                'link_selector': 'link',
                'description_selector': 'description',
                'pub_date_selector': 'pubDate'
            },
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            },
            'interval': 60,  # 60分钟
            'status': 1  # 启用
        },
        {
            'name': 'AWS 中文博客',
            'description': 'AWS 中文官方博客',
            'source_url': 'https://aws.amazon.com/cn/blogs/china/feed/',
            'crawler_type': 1,  # RSS
            'config_data': {
                'item_selector': 'item',
                'title_selector': 'title',
                'link_selector': 'link',
                'description_selector': 'description',
                'pub_date_selector': 'pubDate'
            },
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            },
            'interval': 60,  # 60分钟
            'status': 1  # 启用
        },
        {
            'name': 'Microsoft 开发者博客',
            'description': 'Microsoft 开发者官方博客',
            'source_url': 'https://devblogs.microsoft.com/feed/',
            'crawler_type': 1,  # RSS
            'config_data': {
                'item_selector': 'item',
                'title_selector': 'title',
                'link_selector': 'link',
                'description_selector': 'description',
                'pub_date_selector': 'pubDate'
            },
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            },
            'interval': 60,  # 60分钟
            'status': 1  # 启用
        }
    ]

    for source in rss_sources:
        config = CrawlerConfig.objects.create(**source)
        test_rss_source(config)
    
    print("RSS 数据源配置创建完成")

def create_api_configs():
    """创建 API 数据源配置"""
    api_sources = [
        {
            'name': 'HackerNews API',
            'description': 'HackerNews 最新故事 API',
            'source_url': 'https://hacker-news.firebaseio.com/v0/newstories.json',
            'crawler_type': 2,  # API
            'config_data': {
                'response_type': 'json',
                'items_path': '',  # 直接使用返回的列表
                'item_url_template': 'https://hacker-news.firebaseio.com/v0/item/{}.json',
                'mapping': {
                    'title': 'title',
                    'url': 'url',
                    'description': 'text',  # 可选字段
                    'author': 'by',
                    'pub_time': 'time'
                },
                'optional_fields': ['description']  # 标记可选字段
            },
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            },
            'interval': 60,  # 60分钟
            'status': 1  # 启用
        },
        {
            'name': 'GitHub Trending API',
            'description': 'GitHub 趋势项目 API',
            'source_url': 'https://api.github.com/search/repositories',
            'crawler_type': 2,  # API
            'config_data': {
                'params': {
                    'q': 'stars:>1000',
                    'sort': 'stars',
                    'order': 'desc',
                    'per_page': 5
                },
                'response_type': 'json',
                'items_path': 'items',
                'mapping': {
                    'title': 'full_name',
                    'url': 'html_url',
                    'description': 'description',
                    'author': 'owner.login'
                }
            },
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/vnd.github.v3+json'
            },
            'interval': 120,  # 120分钟
            'status': 1  # 启用
        },
        {
            'name': 'DEV.to API',
            'description': 'DEV.to 最新文章 API',
            'source_url': 'https://dev.to/api/articles',
            'crawler_type': 2,  # API
            'config_data': {
                'params': {
                    'per_page': 5,
                    'state': 'fresh'
                },
                'response_type': 'json',
                'mapping': {
                    'title': 'title',
                    'url': 'url',
                    'description': 'description',
                    'author': 'user.name',
                    'pub_time': 'published_at'
                }
            },
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            },
            'interval': 60,  # 60分钟
            'status': 1  # 启用
        },
        {
            'name': 'ReadHub API',
            'description': 'ReadHub 科技动态 API',
            'source_url': 'https://api.readhub.cn/news',
            'crawler_type': 2,  # API
            'config_data': {
                'params': {
                    'type': 'tech',
                    'limit': 5
                },
                'response_type': 'json',
                'items_path': 'data',
                'mapping': {
                    'title': 'title',
                    'url': 'url',
                    'description': 'summary',
                    'pub_time': 'publishDate'
                }
            },
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            },
            'interval': 30,  # 30分钟
            'status': 1  # 启用
        },
        {
            'name': 'Product Hunt API',
            'description': 'Product Hunt 最新科技产品',
            'source_url': 'https://api.producthunt.com/v2/api/graphql',
            'crawler_type': 2,  # API
            'config_data': {
                'query': """
                query {
                    posts(first: 5) {
                        edges {
                            node {
                                name
                                tagline
                                url
                                description
                                user {
                                    name
                                }
                                createdAt
                            }
                        }
                    }
                }
                """,
                'response_type': 'json',
                'items_path': 'data.posts.edges',
                'mapping': {
                    'title': 'node.name',
                    'url': 'node.url',
                    'description': 'node.tagline',
                    'author': 'node.user.name',
                    'pub_time': 'node.createdAt'
                }
            },
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Authorization': 'Bearer YOUR_API_KEY'  # 需要申请 API Key
            },
            'interval': 60,  # 60分钟
            'status': 0  # 暂时禁用，等待配置 API Key
        }
    ]

    for source in api_sources:
        config = CrawlerConfig.objects.create(**source)
        test_api_source(config)
    
    print("API 数据源配置创建完成")

def create_web_configs():
    """创建网页数据源配置"""
    web_sources = [
        {
            'name': 'V2EX 最新主题',
            'description': 'V2EX 最新主题列表',
            'source_url': 'https://v2ex.com/?tab=all',
            'crawler_type': 3,  # 网页
            'config_data': {
                'list_selector': 'div.cell.item',
                'item_selectors': {
                    'title': 'span.item_title a',
                    'url': 'span.item_title a',
                    'node': 'a.node',
                    'author': 'strong a'
                }
            },
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            },
            'interval': 60,  # 60分钟
            'status': 1  # 启用
        }
    ]

    for source in web_sources:
        config = CrawlerConfig.objects.create(**source)
        test_web_source(config)
    
    print("网页数据源配置创建完成")

def test_rss_source(config):
    """测试 RSS 数据源"""
    try:
        # 创建测试任务
        task = CrawlerTask.objects.create(
            config=config,
            is_test=True
        )
        task.start()

        # 获取 RSS 内容
        response = requests.get(config.source_url, headers=config.headers, timeout=10)
        feed = feedparser.parse(response.content)
        
        # 处理结果
        articles = []
        for entry in feed.entries[:5]:  # 只处理前5条
            pub_time = datetime.fromtimestamp(
                mktime(entry.published_parsed)
            ).replace(tzinfo=pytz.UTC)
            
            article = {
                'title': entry.title,
                'url': entry.link,
                'description': entry.description,
                'pub_time': pub_time,
                'source': config.name,
                'config': config
            }
            articles.append(article)

        # 保存文章
        NewsArticle.save_news_articles(articles)
        
        # 更新任务状态
        task.complete(result={
            'total': len(articles),
            'success': True,
            'message': f'成功获取 {len(articles)} 条数据'
        })
        print(f"RSS源 {config.name} 测试成功")
        
    except Exception as e:
        task.fail(str(e))
        print(f"RSS源 {config.name} 测试失败: {str(e)}")

def test_api_source(config):
    """测试 API 数据源"""
    try:
        # 创建测试任务
        task = CrawlerTask.objects.create(
            config=config,
            is_test=True
        )
        task.start()

        # 发送 API 请求
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
                if key:  # 只处理非空路径
                    items = items.get(key, [])
        elif isinstance(data, list):
            items = data
        else:
            items = [data]
        
        # 处理每个项目
        articles = []
        item_url_template = config.config_data.get('item_url_template')
        
        # 如果是 HackerNews API，需要特殊处理
        if item_url_template and config.name == 'HackerNews API':
            story_ids = items[:5]  # 只获取前5个故事ID
            items = []
            for story_id in story_ids:
                try:
                    item_url = item_url_template.format(story_id)
                    item_response = requests.get(item_url, headers=config.headers, timeout=10)
                    item_response.raise_for_status()
                    items.append(item_response.json())
                except Exception as e:
                    print(f"获取故事 {story_id} 详情失败: {str(e)}")
                    continue
        else:
            items = items[:5]  # 只处理前5条
            
        for item in items:
            try:
                # 映射字段
                mapping = config.config_data['mapping']
                optional_fields = config.config_data.get('optional_fields', [])
                
                # 必需字段
                article = {
                    'title': get_nested_value(item, mapping['title']),
                    'url': get_nested_value(item, mapping['url']),
                    'source': config.name,
                    'config': config
                }
                
                # 可选字段
                if 'description' in mapping:
                    value = get_nested_value(item, mapping['description'])
                    if value or 'description' not in optional_fields:
                        article['description'] = value or ''  # 如果是必需字段但值为空，使用空字符串
                
                if 'author' in mapping:
                    value = get_nested_value(item, mapping['author'])
                    if value or 'author' not in optional_fields:
                        article['author'] = value or ''
                
                if 'pub_time' in mapping:
                    pub_time = get_nested_value(item, mapping['pub_time'])
                    if pub_time:
                        try:
                            if isinstance(pub_time, (int, float)):
                                article['pub_time'] = datetime.fromtimestamp(pub_time).replace(tzinfo=pytz.UTC)
                            else:
                                article['pub_time'] = datetime.fromisoformat(pub_time.replace('Z', '+00:00'))
                        except:
                            article['pub_time'] = timezone.now()
                else:
                    article['pub_time'] = timezone.now()
                
                if article['title'] and article['url']:
                    articles.append(article)
                
            except Exception as e:
                print(f"处理文章时出错: {str(e)}")
                continue

        # 保存文章
        if articles:
            NewsArticle.save_news_articles(articles)
            
            # 更新任务状态
            task.complete(result={
                'total': len(articles),
                'success': True,
                'message': f'成功获取 {len(articles)} 条数据'
            })
            print(f"API源 {config.name} 测试成功")
        else:
            raise Exception("未找到任何文章")
        
    except Exception as e:
        task.fail(str(e))
        print(f"API源 {config.name} 测试失败: {str(e)}")

def get_nested_value(obj, path):
    """获取嵌套字典中的值"""
    try:
        for key in path.split('.'):
            obj = obj[key]
        return obj
    except:
        return None

def test_web_source(config):
    """测试网页数据源"""
    try:
        # 创建测试任务
        task = CrawlerTask.objects.create(
            config=config,
            is_test=True
        )
        task.start()

        # 发送请求
        response = requests.get(config.source_url, headers=config.headers, timeout=10)
        response.raise_for_status()
        
        # 使用 BeautifulSoup 解析页面
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 获取文章列表
        articles = []
        items = soup.select(config.config_data['list_selector'])
        for item in items[:5]:  # 只处理前5条
            selectors = config.config_data['item_selectors']
            try:
                title_elem = item.select_one(selectors['title'])
                url_elem = item.select_one(selectors['url'])
                
                if not title_elem or not url_elem:
                    continue
                    
                title = title_elem.get_text().strip()
                url = url_elem.get('href')
                
                # 处理相对 URL
                if url and not url.startswith(('http://', 'https://')):
                    url = urljoin(config.source_url, url)
                
                article = {
                    'title': title,
                    'url': url,
                    'pub_time': timezone.now(),  # 简化处理
                    'source': config.name,
                    'config': config,
                    'description': ''  # 默认空字符串
                }
                
                # 获取可选字段
                if 'description' in selectors:
                    desc_elem = item.select_one(selectors['description'])
                    if desc_elem:
                        article['description'] = desc_elem.get_text().strip()
                
                if 'author' in selectors:
                    author_elem = item.select_one(selectors['author'])
                    if author_elem:
                        article['author'] = author_elem.get_text().strip()
                
                articles.append(article)
                
            except Exception as e:
                print(f"处理文章时出错: {str(e)}")
                continue

        # 保存文章
        if articles:
            NewsArticle.save_news_articles(articles)
            
            # 更新任务状态
            task.complete(result={
                'total': len(articles),
                'success': True,
                'message': f'成功获取 {len(articles)} 条数据'
            })
            print(f"网页源 {config.name} 测试成功")
        else:
            raise Exception("未找到任何文章")
        
    except Exception as e:
        task.fail(str(e))
        print(f"网页源 {config.name} 测试失败: {str(e)}")

def main():
    """主函数"""
    # 清理现有数据
    CrawlerConfig.objects.all().delete()
    CrawlerTask.objects.all().delete()
    NewsArticle.objects.all().delete()
    print("现有数据清理完成")

    # 创建各类数据源配置
    create_rss_configs()
    create_api_configs()
    create_web_configs()

if __name__ == '__main__':
    main() 