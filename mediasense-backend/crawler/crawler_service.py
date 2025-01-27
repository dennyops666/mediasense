import uuid
import logging
import requests
import re
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import datetime
from django.utils import timezone
import feedparser
from django.utils.dateparse import parse_datetime
import time
import pytz
from news.models import NewsArticle
from news.serializers import NewsArticleCreateSerializer
import json

logger = logging.getLogger(__name__)


class CrawlerService:
    """爬虫服务"""

    @classmethod
    def get_crawler(cls, config):
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
    def create_task(cls, config):
        """
        创建爬虫任务
        :param config: 爬虫配置
        :return: 爬虫任务
        """
        from .models import CrawlerTask

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
    def run_task(cls, task):
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
    def get_pending_configs(cls):
        """
        获取待执行的爬虫配置
        :return: 配置列表
        """
        from .models import CrawlerConfig
        from django.db import models

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
                result = CrawlerService._parse_rss(response.content)
                items = result if isinstance(result, list) else []
            elif config.crawler_type == 2:  # API
                logger.info(f"使用API解析器: {config.name}")
                try:
                    # 尝试解析为JSON
                    data = response.json()
                except:
                    # 如果JSON解析失败，可能是JSONP格式
                    data = response.text
                logger.debug(f"API响应: {data}")
                items = CrawlerService._parse_api(data, config)
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
            stats = {
                'total': len(items),
                'cleaned': len(cleaned_items),
                'saved': 0,
                'duplicated': 0,
                'filtered': len(items) - len(cleaned_items),
                'errors': 0
            }

            for item in cleaned_items:
                try:
                    source_url = item.get('source_url')
                    if NewsArticle.objects.filter(source_url=source_url).exists():
                        logger.info(f"文章已存在: {source_url}")
                        stats['duplicated'] += 1
                        continue

                    article_data = {
                        'title': item.get('title'),
                        'source_url': source_url,
                        'content': item.get('content', ''),
                        'summary': item.get('description', ''),
                        'author': item.get('author', ''),
                        'source': item.get('source', ''),
                        'publish_time': item.get('pub_time', timezone.now()),
                        'crawler': config.id if config else None,
                        'status': NewsArticle.Status.DRAFT,
                    }
                    
                    # 保存文章
                    serializer = NewsArticleCreateSerializer(data=article_data)
                    if serializer.is_valid():
                        try:
                            serializer.save()
                            stats['saved'] += 1
                            logger.info(f'成功保存文章: {source_url}')
                        except Exception as e:
                            logger.error(f'保存文章时发生错误: {source_url}, 错误信息: {str(e)}')
                            stats['errors'] += 1
                    else:
                        logger.error(f'文章数据验证失败: {source_url}, 错误信息: {serializer.errors}')
                        stats['errors'] += 1
                except Exception as e:
                    logger.error(f'处理文章时发生错误: {str(e)}')
                    stats['errors'] += 1

            logger.info(f"保存完成: {config.name}, 成功保存{stats['saved']}条数据")
                
            return {
                'status': 'success',
                'task_id': task.task_id if task else None,
                'items_count': stats['saved'],
                'total': len(cleaned_items),
                'cleaned': len(cleaned_items),
                'saved': stats['saved'],
                'filtered': stats['filtered'],
                'error': stats['errors'],
                'duplicate': stats['duplicated'],
                'invalid_time': 0
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
                        'source_url': entry.get('link', '').strip(),
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
    def _parse_api(response_data: Dict, config) -> List[Dict]:
        """解析API响应"""
        logger = logging.getLogger(__name__)

        # 获取数据路径
        data_path = config.config_data.get('data_path', '')
        if not data_path:
            logger.error(f'数据路径未配置: {config.name}')
            return []

        # 根据数据路径获取新闻列表
        news_list = response_data
        try:
            for key in data_path.split('.'):
                if key.startswith('[') and key.endswith(']'):
                    # 处理数组索引
                    index = int(key[1:-1])
                    if not isinstance(news_list, (list, tuple)) or index >= len(news_list):
                        logger.error(f'无效的数组索引: {key}, 当前值: {news_list}')
                        return []
                    news_list = news_list[index]
                else:
                    # 处理字典键
                    if not isinstance(news_list, dict):
                        logger.error(f'无效的数据路径: {data_path}, 当前值: {news_list}')
                        return []
                    news_list = news_list.get(key, {})

            if not isinstance(news_list, list):
                logger.error(f'无效的新闻列表: {news_list}')
                return []

            # 解析每条新闻
            parsed_items = []
            for item in news_list:
                try:
                    # 获取字段值
                    title = CrawlerService._get_field_value(item, config.config_data.get('title_path'))
                    url = CrawlerService._get_field_value(item, config.config_data.get('link_path'))
                    author = CrawlerService._get_field_value(item, config.config_data.get('author_path'))
                    source = CrawlerService._get_field_value(item, config.config_data.get('source_path'))
                    pub_date = CrawlerService._get_field_value(item, config.config_data.get('pub_date_path'))
                    
                    logger.debug(f'原始数据: {item}')
                    logger.debug(f'解析结果: title={title}, url={url}, author={author}, source={source}, pub_date={pub_date}')
                    
                    # 获取新闻详情URL
                    detail_url = CrawlerService._get_field_value(item, 'link.url')
                    if detail_url:
                        try:
                            # 请求新闻详情
                            headers = config.headers or {
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                            }
                            detail_response = requests.get(detail_url, headers=headers, timeout=30)
                            detail_response.raise_for_status()
                            detail_data = detail_response.json()
                            
                            # 从详情中获取内容
                            content = detail_data.get('body', {}).get('text', '')
                            description = detail_data.get('body', {}).get('summary', '')
                            logger.debug(f'获取到新闻详情: content长度={len(content)}, description长度={len(description)}')
                        except Exception as e:
                            logger.error(f'获取新闻详情失败: {str(e)}')
                            content = ''
                            description = ''
                    else:
                        content = ''
                        description = item.get('description', '')

                    # 构建新闻数据
                    news_item = {
                        'title': title,
                        'source_url': url or item.get('link', {}).get('weburl', ''),  # 尝试直接从原始数据获取URL
                        'content': content or '暂无内容',  # 确保内容不为空
                        'description': description,
                        'author': author,
                        'source': source,
                        'pub_date': pub_date,
                        'crawler': config
                    }
                    logger.debug(f'构建的新闻数据: {news_item}')
                    parsed_items.append(news_item)

                except Exception as e:
                    logger.error(f'解析新闻失败: {str(e)}')
                    continue

            logger.info(f'解析完成: {config.name}, 获取{len(parsed_items)}条数据')
            return parsed_items
        except Exception as e:
            logger.error(f'解析API响应失败: {str(e)}')
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
                    'source_url': link_elem['href'],
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
        logger = logging.getLogger(__name__)
        logger.debug(f"开始过滤新闻条目: {item}")
        
        # 检查必要字段
        if not item.get('title') or not item.get('source_url'):
            logger.warning(f"缺少必要字段: title={item.get('title')}, source_url={item.get('source_url')}")
            return False
            
        # 检查标题长度
        if len(item['title']) < 2:
            logger.warning(f"标题长度不足: {item['title']}")
            return False
            
        # 检查链接格式
        if not item['source_url'].startswith(('http://', 'https://')):
            logger.warning(f"链接格式错误: {item['source_url']}")
            return False
            
        logger.info(f"通过过滤: title={item['title']}, source_url={item['source_url']}")
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
    def _get_field_value(item, path):
        """获取字段值"""
        if not path:
            return None
            
        try:
            value = item
            for key in path.split('.'):
                if isinstance(value, dict):
                    value = value.get(key)
                else:
                    return None
            return value
        except Exception as e:
            logger.error(f'获取字段值失败: {str(e)}')
            return None

    @staticmethod
    def _clean_data(item):
        """清洗数据"""
        try:
            # 检查输入类型
            if not isinstance(item, (dict, int, float, str)):
                logger.error(f"不支持的数据类型: {type(item)}")
                return None
                
            # 如果是数字类型，转换为字符串
            if isinstance(item, (int, float)):
                item = {'title': str(item), 'url': 'https://example.com'}
                
            # 如果是字符串，尝试解析为JSON
            if isinstance(item, str):
                try:
                    item = json.loads(item)
                except json.JSONDecodeError:
                    logger.error("无法将字符串解析为JSON")
                    return None
                    
            # 确保item是字典类型
            if not isinstance(item, dict):
                logger.error(f"数据必须是字典类型: {type(item)}")
                return None
                
            # 检查必要字段
            if not item.get('title') or not item.get('url'):
                logger.warning(f"缺少必要字段: {item}")
                return None
                
            # 清理标题
            title = str(item['title']).strip()
            if len(title) < 2:
                logger.warning(f"标题长度不足: {title}")
                return None
                
            # 清理URL
            url = str(item['url']).strip()
            if not url.startswith(('http://', 'https://')):
                logger.warning(f"无效的URL: {url}")
                return None
                
            # 清理内容
            content = str(item.get('content', '')).strip()
            if not content and item.get('description'):
                content = str(item['description']).strip()
                
            # 清理描述
            description = str(item.get('description', '')).strip()
            if not description and content:
                description = content[:200]
                
            # 清理作者
            author = str(item.get('author', '')).strip()
            
            # 清理来源
            source = str(item.get('source', '')).strip()
            
            # 清理发布时间
            pub_time = item.get('pub_time')
            if not pub_time:
                pub_time = timezone.now()
            elif isinstance(pub_time, str):
                try:
                    pub_time = parse_datetime(pub_time)
                    if not pub_time:
                        pub_time = timezone.now()
                except:
                    pub_time = timezone.now()
            elif pub_time.tzinfo:
                pub_time = pub_time.astimezone(pytz.UTC)
                    
            # 清理标签
            tags = item.get('tags', [])
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
            elif not isinstance(tags, list):
                tags = []
                
            # 清理图片
            images = item.get('images', [])
            if isinstance(images, str):
                images = [img.strip() for img in images.split(',') if img.strip()]
            elif not isinstance(images, list):
                images = []
                
            # 构建清洗后的数据
            cleaned_item = {
                'title': title,
                'url': url,
                'content': content,
                'description': description,
                'author': author,
                'source': source,
                'pub_time': pub_time,
                'tags': tags,
                'images': images
            }
            
            return cleaned_item
            
        except Exception as e:
            logger.error(f"数据清洗失败: {str(e)}")
            return None 