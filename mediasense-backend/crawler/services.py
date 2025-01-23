import uuid
import logging
import requests
import re
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import datetime
from django.db import models
from .models import CrawlerConfig, CrawlerTask, NewsArticle
import feedparser
from django.utils.dateparse import parse_datetime
import time
from datetime import timedelta
import json
import pytz
import subprocess
from django.db import IntegrityError
from news.serializers import NewsArticleCreateSerializer

logger = logging.getLogger(__name__)


class CrawlerService:
    """爬虫服务"""

    @classmethod
    def get_crawler(cls, config: CrawlerConfig) -> Optional[Dict]:
        """
        根据配置获取爬虫实例
        :param config: 爬虫配置
        :return: 爬虫配置字典
        """
        if config.crawler_type not in [1, 2, 3]:
            logger.error(f"不支持的爬虫类型: {config.crawler_type}")
            return None

        return {
                "source_url": config.source_url,
                "headers": config.headers,
                "source_name": config.name,
                **config.config_data,
            }

    @classmethod
    def create_task(cls, config: CrawlerConfig) -> Optional[CrawlerTask]:
        """
        创建爬虫任务
        :param config: 爬虫配置
        :return: 爬虫任务
        """
        # 检查是否有运行中的任务
        if CrawlerTask.objects.filter(
            config=config,
            status__in=[0, 1]  # 未开始或运行中
        ).exists():
            return None
            
        # 创建新任务
        return CrawlerTask.objects.create(
            config=config,
            task_id=str(uuid.uuid4()),  # 使用UUID作为任务ID
            status=0,  # 未开始状态
            start_time=datetime.datetime.now()
        )

    @classmethod
    def run_task(cls, task: CrawlerTask) -> bool:
        """
        执行爬虫任务
        :param task: 爬虫任务
        :return: 是否执行成功
        """
        MAX_RETRIES = 3  # 最大重试次数
        RETRY_INTERVAL = 60  # 重试间隔（秒）
        
        for retry_count in range(MAX_RETRIES):
            try:
                if retry_count > 0:
                    logger.info(f"第{retry_count}次重试任务: {task.task_id}")
                    
                # 更新任务状态为运行中
                task.status = 1
                task.start_time = datetime.datetime.now()
                task.retry_count = retry_count
                task.save()

                # 获取爬虫配置
                crawler = cls.get_crawler(task.config)
                if not crawler:
                    raise ValueError(f"无法创建爬虫实例: {task.config.name}")

                # 执行爬虫
                result = cls.crawl_website(task.config, task)

                # 更新任务状态为已完成
                task.status = 2
                task.end_time = datetime.datetime.now()
                task.result = {
                    'status': result['status'],
                    'items_count': result.get('items_count', 0),
                    'crawl_time': task.end_time.isoformat(),
                    'retry_count': retry_count,
                    'stats': {
                        'total': result.get('total', 0),
                        'saved': result.get('saved', 0),
                        'filtered': result.get('filtered', 0),
                        'error': result.get('error', 0),
                        'duplicate': result.get('duplicate', 0),
                        'invalid_time': result.get('invalid_time', 0)
                    }
                }
                task.save()

                # 更新配置最后运行时间
                task.config.last_run_time = task.end_time
                task.config.save()

                return result['status'] == 'success'

            except Exception as e:
                logger.error(f"执行爬虫任务失败 (重试 {retry_count + 1}/{MAX_RETRIES}): {str(e)}", exc_info=True)
                
                if retry_count < MAX_RETRIES - 1:
                    # 等待一段时间后重试
                    time.sleep(RETRY_INTERVAL)
                    continue
                    
                # 最后一次重试失败，更新任务状态为出错
                task.status = 4
                task.end_time = datetime.datetime.now()
                task.error_message = str(e)
                task.retry_count = retry_count
                task.save()
                
                return False

    @classmethod
    def get_pending_configs(cls) -> List[CrawlerConfig]:
        """
        获取待执行的爬虫配置
        :return: 配置列表
        """
        now = datetime.datetime.now()
        return (
            CrawlerConfig.objects.filter(status=1)  # 启用状态
            .filter(
                # 从未运行或已到达下次运行时间
                models.Q(last_run_time__isnull=True)
                | models.Q(last_run_time__lte=now - models.F("interval"))
            )
            .order_by("last_run_time")
        )

    @staticmethod
    def crawl_website(config, task=None):
        """
        爬取网站内容
        """
        try:
            logger.info(f"开始爬取网站: {config.name}")
            # 发送HTTP请求
            headers = config.headers or {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            response = requests.get(config.source_url, headers=headers, timeout=60)  # 增加超时时间到60秒
            response.raise_for_status()
            
            logger.info(f"成功获取响应: {config.name}, status_code={response.status_code}")
            
            # 根据爬虫类型解析内容
            items = []
            if config.crawler_type == 1:  # RSS
                logger.info(f"使用RSS解析器: {config.name}")
                items = CrawlerService._parse_rss(response.content)
            elif config.crawler_type == 2:  # API
                logger.info(f"使用API解析器: {config.name}")
                try:
                    # 尝试解析为JSON
                    data = response.json()
                except:
                    # 如果JSON解析失败，可能是JSONP格式
                    data = response.text
                logger.debug(f"API响应: {data}")
                items = CrawlerService._parse_api(data)
            else:  # HTML
                logger.info(f"使用HTML解析器: {config.name}")
                items = CrawlerService._parse_html(response.text)
                
            logger.info(f"解析完成: {config.name}, 获取{len(items)}条数据")
            
            # 清洗数据
            cleaned_items = []
            for item in items:
                if item.get('description'):
                    item['description'] = CrawlerService._clean_text(item['description'])
                if item.get('title'):
                    item['title'] = CrawlerService._clean_text(item['title'])
                if CrawlerService._filter_item(item):
                    cleaned_items.append(item)
                    
            logger.info(f"数据清洗完成: 原始数据={len(items)}条, 清洗后={len(cleaned_items)}条")
                
            # 保存到数据库
            stats = CrawlerService.save_news_articles(config.name, cleaned_items, {'total': len(cleaned_items), 'saved': 0, 'filtered': 0, 'duplicated': 0, 'errors': 0})
            logger.info(f"保存完成: {config.name}, 成功保存{stats['saved']}条数据")
                
            return {
                'status': 'success',
                'task_id': task.task_id if task else None,
                'items_count': stats['saved'],
                'total': len(cleaned_items),
                'cleaned': len(cleaned_items),
                'saved': stats['saved'],
                'filtered': len(cleaned_items) - len(cleaned_items),
                'error': stats['errors'],
                'duplicate': stats['duplicated'],
                'invalid_time': stats['filtered']
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求失败: {str(e)}"
            logger.error(error_msg)
            return {'status': 'error', 'message': error_msg}
        except ValueError as e:
            error_msg = f"数据解析失败: {str(e)}"
            logger.error(error_msg)
            return {'status': 'error', 'message': error_msg}
        except Exception as e:
            error_msg = f"爬取失败 {config.name}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {'status': 'error', 'message': error_msg}
    
    @staticmethod
    def _parse_rss(content):
        """解析RSS内容"""
        try:
            logger.info("开始解析RSS内容")
            feed = feedparser.parse(content)
            
            if feed.bozo:  # 检查是否有解析错误
                logger.error(f"RSS解析错误: {feed.bozo_exception}")
                return []
                
            if not hasattr(feed, 'entries'):
                logger.error("RSS源没有entries属性")
                return []
                
            items = []
            for entry in feed.entries:
                try:
                    # 提取必要字段
                    item = {
                        'title': entry.get('title', '').strip(),
                        'link': entry.get('link', '').strip(),
                        'description': entry.get('description', '').strip(),
                        'pub_date': entry.get('published', entry.get('pubDate', '')),
                        'author': entry.get('author', '').strip(),
                        'source': feed.feed.get('title', '未知来源'),
                        'category': [tag.term for tag in entry.get('tags', [])] if hasattr(entry, 'tags') else [],
                        'guid': entry.get('id', entry.get('guid', '')).strip()
                    }
                    
                    # 提取图片URL
                    if 'media_content' in entry:
                        media_urls = [media['url'] for media in entry.media_content if 'url' in media]
                        item['images'] = media_urls
                    elif 'enclosures' in entry:
                        image_urls = [enc['href'] for enc in entry.enclosures if enc.get('type', '').startswith('image/')]
                        item['images'] = image_urls
                        
                    logger.debug(f"解析RSS条目: {item}")
                    items.append(item)
                    
                except Exception as e:
                    logger.error(f"处理RSS条目时出错: {str(e)}", exc_info=True)
                    continue
                    
            logger.info(f"RSS解析完成，共获取{len(items)}条数据")
            return items
            
        except Exception as e:
            logger.error(f"RSS解析失败: {str(e)}", exc_info=True)
            return []
        
    @staticmethod
    def _parse_api(data: dict) -> List[dict]:
        """
        解析API响应数据
        """
        try:
            # 新浪新闻格式
            if isinstance(data, dict) and 'result' in data and 'data' in data['result']:
                items = []
                for article in data['result']['data']:
                    try:
                        # 解析时间戳
                        pub_time = None
                        if 'ctime' in article:
                            try:
                                timestamp = int(article['ctime'])
                                pub_time = datetime.datetime.fromtimestamp(timestamp)
                            except (ValueError, TypeError):
                                pub_time = datetime.datetime.now()
                        else:
                            pub_time = datetime.datetime.now()
                            
                        item = {
                            'title': article.get('title', ''),
                            'url': article.get('url', ''),
                            'content': article.get('intro', ''),
                            'summary': article.get('intro', ''),
                            'author': article.get('author', ''),
                            'category': article.get('categoryid', ''),
                            'pub_date': pub_time
                        }
                        if item['title'] and item['url'] and item['content']:
                            items.append(item)
                    except Exception as e:
                        logger.error(f"解析新浪新闻数据失败: {str(e)}")
                        continue
                return items
                
            # 网易新闻格式 (JSONP)
            elif isinstance(data, str) and data.startswith('artiList('):
                try:
                    json_str = data[9:-1]  # 移除 artiList( 和 )
                    json_data = json.loads(json_str)
                    
                    # 获取新闻列表
                    news_list = []
                    for key, articles in json_data.items():
                        if isinstance(articles, list):
                            for article in articles:
                                try:
                                    # 解析时间戳
                                    pub_time = None
                                    if 'ptime' in article:
                                        try:
                                            pub_time = datetime.datetime.strptime(article['ptime'], '%Y-%m-%d %H:%M:%S')
                                        except (ValueError, TypeError):
                                            pub_time = datetime.datetime.now()
                                    else:
                                        pub_time = datetime.datetime.now()
                                        
                                    item = {
                                        'title': article.get('title', ''),
                                        'url': article.get('url', ''),
                                        'content': article.get('digest', ''),
                                        'summary': article.get('digest', ''),
                                        'author': article.get('source', ''),
                                        'pub_date': pub_time
                                    }
                                    if item['title'] and item['url'] and item['content']:
                                        news_list.append(item)
                                except Exception as e:
                                    logger.error(f"解析网易新闻数据失败: {str(e)}")
                                    continue
                    return news_list
                except Exception as e:
                    logger.error(f"解析JSONP数据失败: {str(e)}")
                    return []
                    
            # 凤凰新闻格式
            elif isinstance(data, list):
                items = []
                for section in data:
                    if isinstance(section.get('item'), list):
                        for article in section['item']:
                            try:
                                # 解析时间戳
                                pub_time = None
                                if 'updateTime' in article:
                                    try:
                                        pub_time = datetime.datetime.strptime(article['updateTime'], '%Y-%m-%d %H:%M:%S')
                                    except (ValueError, TypeError):
                                        pub_time = datetime.datetime.now()
                                else:
                                    pub_time = datetime.datetime.now()
                                    
                                item = {
                                    'title': article.get('title', ''),
                                    'url': article.get('link', {}).get('url', ''),
                                    'content': article.get('description', ''),
                                    'summary': article.get('description', ''),
                                    'author': article.get('source', ''),
                                    'pub_date': pub_time
                                }
                                if item['title'] and item['url'] and item['content']:
                                    items.append(item)
                            except Exception as e:
                                logger.error(f"解析凤凰新闻数据失败: {str(e)}")
                                continue
                return items
                
            logger.error("不支持的API响应格式")
            return []
            
        except Exception as e:
            logger.error(f"解析API数据失败: {str(e)}")
            return []
        
    @staticmethod
    def _parse_html(html):
        """解析HTML内容"""
        soup = BeautifulSoup(html, 'html.parser')
        items = []
        
        # 查找新闻列表
        news_items = soup.find_all('div', class_='news-item')
        for item in news_items:
            title_elem = item.find('h3')
            link_elem = item.find('a')
            desc_elem = item.find('p', class_='description')
            date_elem = item.find('span', class_='date')
            
            if title_elem and link_elem:
                items.append({
                    'title': title_elem.text.strip(),
                    'link': link_elem['href'],
                    'description': desc_elem.text.strip() if desc_elem else '',
                    'pub_date': date_elem.text.strip() if date_elem else '',
                    'author': '',
                    'category': [],
                    'image_url': '',
                    'guid': link_elem['href']
                })
                
        return items

    @staticmethod
    def _clean_text(text: str) -> str:
        """清理文本内容"""
        if not text:
            return ""
            
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        # 移除特殊字符
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        return text.strip()

    @staticmethod
    def _filter_item(item: Dict) -> bool:
        """过滤新闻条目"""
        logger.debug(f"开始过滤新闻条目: {item}")
        
        # 检查必要字段
        if not item.get('title') or not item.get('link'):
            logger.warning(f"缺少必要字段: title={item.get('title')}, link={item.get('link')}")
            return False
            
        # 检查标题长度
        if len(item['title']) < 2:
            logger.warning(f"标题长度不足: {item['title']}")
            return False
            
        # 检查链接格式
        if not item['link'].startswith(('http://', 'https://')):
            logger.warning(f"链接格式错误: {item['link']}")
            return False
            
        logger.info(f"通过过滤: title={item['title']}, link={item['link']}")
        return True

    @staticmethod
    def _parse_datetime(date_str: str) -> Optional[datetime.datetime]:
        """解析日期时间字符串"""
        if not date_str:
            return None
            
        try:
            # 尝试直接解析
            dt = parse_datetime(date_str)
            if dt:
                return dt
                
            # 尝试常见的日期格式
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M',
                '%Y-%m-%d',
                '%Y年%m月%d日 %H:%M:%S',
                '%Y年%m月%d日 %H:%M',
                '%Y年%m月%d日',
                '%a, %d %b %Y %H:%M:%S %z',  # RSS常用格式
                '%a, %d %b %Y %H:%M:%S %Z',
                '%Y-%m-%dT%H:%M:%S%z',       # ISO格式
                '%Y-%m-%dT%H:%M:%S.%f%z'
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.datetime.strptime(date_str, fmt)
                    if not dt.tzinfo:
                        dt = dt.replace(tzinfo=pytz.UTC)
                    return dt
                except ValueError:
                    continue
                    
            return None
            
        except Exception as e:
            logger.error(f"日期解析失败: {date_str}, 错误: {str(e)}")
            return None

    @staticmethod
    def _get_system_time() -> datetime.datetime:
        """
        获取系统当前时间
        """
        try:
            # 直接返回当前时间，不带时区信息
            return datetime.datetime.now()
        except Exception as e:
            logger.error(f"获取系统时间出错: {e}")
            return datetime.datetime.now()

    @staticmethod
    def save_news_articles(source: str, items: List[Dict], stats: Dict) -> Dict:
        """保存新闻文章列表."""
        logger.info(f"开始保存{len(items)}条新闻")

        for item in items:
            title = item.get('title', '')
            url = item.get('url', '') or item.get('link', '')  # 同时支持url和link字段
            
            if not title or not url:
                logger.warning(f"标题或URL为空，跳过: {title}")
                stats['filtered'] += 1
                continue

            # 检查新闻是否已存在
            if NewsArticle.objects.filter(url=url).exists():
                logger.info(f"新闻已存在: {title}")
                stats['duplicated'] += 1
                continue

            try:
                # 准备数据
                data = {
                    'title': title,
                    'content': item.get('content', '') or item.get('description', ''),  # 同时支持content和description字段
                    'summary': item.get('summary', '') or item.get('description', ''),  # 同时支持summary和description字段
                    'source': source,
                    'author': item.get('author', ''),
                    'url': url,
                    'publish_time': item.get('pub_date') or item.get('pubDate', '')  # 同时支持pub_date和pubDate字段
                }
                
                # 使用序列化器创建文章
                serializer = NewsArticleCreateSerializer(data=data)
                if serializer.is_valid():
                    serializer.save()
                    stats['saved'] += 1
                    logger.info(f"保存新闻成功: {title}")
                else:
                    logger.error(f"保存新闻失败: {title}, 错误: {serializer.errors}")
                    stats['errors'] += 1
            except Exception as e:
                logger.error(f"保存新闻失败: {title}, 错误: {str(e)}")
                stats['errors'] += 1

        # 打印保存结果
        logger.info(f"新闻保存完成，共处理{len(items)}条新闻，成功保存{stats['saved']}条，"
                    f"重复{stats['duplicated']}条，过滤{stats['filtered']}条，错误{stats['errors']}条")

        return stats

    @classmethod
    def cleanup_old_articles(cls, days=30):
        """
        清理旧的新闻文章
        :param days: 保留最近几天的文章
        :return: 清理的文章数量
        """
        import datetime
        
        try:
            # 计算截止日期
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
            
            # 获取要删除的文章数量
            to_delete_count = NewsArticle.objects.filter(
                pub_time__lt=cutoff_date
            ).count()
            
            if to_delete_count == 0:
                logger.info("没有需要清理的旧文章")
                return 0
                
            # 删除旧文章
            deleted_count = NewsArticle.objects.filter(
                pub_time__lt=cutoff_date
            ).delete()[0]
            
            logger.info(f"成功清理 {deleted_count} 篇旧文章")
            return deleted_count
            
        except Exception as e:
            logger.error(f"清理旧文章失败: {str(e)}", exc_info=True)
            return 0

    @staticmethod
    def _is_duplicate(url: str) -> bool:
        """检查新闻是否重复"""
        import datetime
        start_time = datetime.datetime.now() - datetime.timedelta(days=1)
        return NewsArticle.objects.filter(
            url=url,
            created_at__gte=start_time
        ).exists()
