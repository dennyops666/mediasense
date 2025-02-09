import uuid
import logging
import requests
import re
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
import datetime
from django.db import models
from .models import CrawlerConfig, CrawlerTask
from news.models import NewsArticle
import feedparser
from django.utils.dateparse import parse_datetime
import time
from datetime import timedelta
import json
import pytz
import subprocess
from django.db import IntegrityError
from django.utils import timezone
from rest_framework import serializers
from .serializers.article import NewsArticleCreateSerializer
from urllib.parse import urljoin
from crawler.crawlers.rss_crawler import RSSCrawler
from crawler.crawlers.api_crawler import APICrawler
from crawler.crawlers.web_crawler import WebCrawler
from crawler.crawlers.base import BaseCrawler
from crawler.crawlers.infoq_crawler import InfoQCrawler

# 设置日志级别为DEBUG
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# 添加控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s %(asctime)s %(name)s %(process)d %(thread)d %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# 添加文件处理器
file_handler = logging.FileHandler('logs/crawler_service.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

class CrawlerService:
    """爬虫服务"""

    @classmethod
    def get_crawler(cls, config: CrawlerConfig) -> Optional[BaseCrawler]:
        """
        根据配置获取爬虫实例
        :param config: 爬虫配置
        :return: 爬虫实例
        """
        logger.info(f"开始创建爬虫实例: {config.name} (类型: {config.crawler_type})")
        
        if not config.status:
            logger.warning(f"爬虫 {config.name} 未启用")
            return None

        if config.crawler_type not in [1, 2, 3]:
            logger.error(f"不支持的爬虫类型: {config.crawler_type}")
            return None

        try:
            # 创建爬虫实例
            if config.name == "InfoQ":
                crawler = InfoQCrawler(config)
            else:
                crawler_map = {
                    1: RSSCrawler,    # RSS类型
                    2: APICrawler,    # API类型
                    3: WebCrawler     # HTML类型
                }
                
                crawler_class = crawler_map.get(config.crawler_type)
                if not crawler_class:
                    raise ValueError(f"未知的爬虫类型: {config.crawler_type}")
                    
                crawler = crawler_class(config)
                
            logger.info(f"成功创建爬虫实例: {config.name} ({crawler.__class__.__name__})")
            return crawler
            
        except Exception as e:
            logger.error(f"创建爬虫实例失败: {config.name} - {str(e)}", exc_info=True)
            return None

    @classmethod
    def create_task(cls, config: CrawlerConfig) -> Optional[CrawlerTask]:
        """
        创建爬虫任务
        :param config: 爬虫配置
        :return: 爬虫任务
        """
        logger.info(f"开始创建爬虫任务: {config.name}")
        
        try:
            # 检查是否有运行中的任务
            running_tasks = CrawlerTask.objects.filter(
                config=config,
                status__in=[0, 1]  # 未开始或运行中
            )
            
            if running_tasks.exists():
                logger.warning(f"存在运行中的任务: {config.name}")
                return None
                
            # 创建新任务
            task = CrawlerTask.objects.create(
                config=config,
                task_id=str(uuid.uuid4()),  # 使用UUID作为任务ID
                status=0,  # 未开始状态
                start_time=timezone.now()
            )
            
            logger.info(f"成功创建爬虫任务: {config.name} (任务ID: {task.task_id})")
            return task
            
        except Exception as e:
            logger.error(f"创建爬虫任务失败: {config.name} - {str(e)}", exc_info=True)
            return None

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
                task.start_time = timezone.now()
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
                task.end_time = timezone.now()
                task.result = {
                    'status': result['status'],
                    'total': result.get('total', 0),
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
                task.end_time = timezone.now()
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
        now = timezone.now()
        return (
            CrawlerConfig.objects.filter(status=1)  # 启用状态
            .filter(
                # 从未运行或已到达下次运行时间
                models.Q(last_run_time__isnull=True)
                | models.Q(last_run_time__lte=now - models.F("interval"))
            )
            .order_by("last_run_time")
        )

    @classmethod
    def crawl_website(cls, config, task=None):
        """
        爬取网站
        :param config: 爬虫配置
        :param task: 爬虫任务
        :return: 爬取结果
        """
        # 初始化统计信息
        stats = {
            'total': 0,
            'saved': 0,
            'filtered': 0,
            'errors': 0,
            'duplicated': 0
        }
        
        try:
            # 获取爬虫实例
            crawler = cls.get_crawler(config)
            if not crawler:
                error_msg = f"无法创建爬虫实例: {config.name}"
                logger.error(error_msg)
                return {
                    'status': 'error',
                    'message': error_msg,
                    'total': 0,
                    **stats
                }
                
            # 执行爬虫
            logger.info(f"开始执行爬虫: {config.name}")
            result = crawler.run()
            
            if result['status'] != 'success':
                logger.warning(f"爬虫执行失败: {result['message']}")
                return {
                    'status': 'error',
                    'message': result['message'],
                    'total': 0,
                    **stats
                }
                
            # 获取文章列表
            items = result.get('data', [])
            if not items:
                logger.warning(f"未获取到任何数据: {config.name}")
                return {
                    'status': 'success',
                    'message': '未获取到数据',
                    'total': 0,
                    **stats
                }
                
            logger.info(f"解析完成: {config.name}, 获取{len(items)}条数据")
            
            # 清洗数据
            cleaned_items = []
            for item in items:
                try:
                    cleaned_item = cls._clean_data(item)
                    if cleaned_item:
                        cleaned_items.append(cleaned_item)
                    else:
                        stats['filtered'] += 1
                except Exception as e:
                    logger.error(f"数据清洗失败: {str(e)}")
                    stats['errors'] += 1
                    
            logger.info(f"数据清洗完成: 原始数据{len(items)}条, 清洗后{len(cleaned_items)}条")
            
            # 保存数据
            for item in cleaned_items:
                try:
                    result = cls._save_article(item, config)
                    if result == 'saved':
                        stats['saved'] += 1
                    elif result == 'duplicated':
                        stats['duplicated'] += 1
                except Exception as e:
                    logger.error(f"保存文章失败: {str(e)}")
                    stats['errors'] += 1
                    
            logger.info(f"爬取完成: {config.name}, 统计信息: {json.dumps(stats, ensure_ascii=False)}")
            
            return {
                'status': 'success',
                'message': '爬取成功',
                'total': len(items),
                **stats
            }
            
        except Exception as e:
            error_msg = f"爬取网站失败: {config.name} - {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'status': 'error',
                'message': error_msg,
                'total': 0,
                **stats
            }
    
    @staticmethod
    def _clean_data(item):
        """清洗数据项"""
        try:
            # 检查输入类型
            if not isinstance(item, (dict, int, float, str)):
                logger.error(f"不支持的数据类型: {type(item)}")
                return None
                
            # 如果是数字类型,转换为字典格式
            if isinstance(item, (int, float)):
                    item = {
                    'title': str(item),
                    'url': '',
                    'content': str(item),
                    'description': str(item),
                    'author': '',
                    'source': '',
                    'pub_time': None,
                    'tags': [],
                    'images': []
                }
                
            # 如果是字符串,尝试解析为JSON
            if isinstance(item, str):
                try:
                    item = json.loads(item)
                except json.JSONDecodeError:
                    logger.error(f"JSON解析失败: {item}")
                    return None

            # 验证必要字段
            if not item.get('title') or not item.get('url'):
                logger.warning(f"缺少必要字段: {item}")
                return None

            # 清洗各个字段
            cleaned_item = {
                'title': item.get('title', '').strip(),
                'url': item.get('url', '').strip(),
                'content': item.get('content', '').strip(),
                'description': item.get('description', '').strip(),
                'author': item.get('author', '').strip(),
                'source': item.get('source', '').strip(),
                'pub_time': item.get('pub_time'),
                'tags': item.get('tags', []),
                'images': item.get('images', [])
            }

            return cleaned_item
        except Exception as e:
            logger.error(f"数据清洗失败: {str(e)}")
            return None

    @staticmethod
    def _save_article(item: Dict, config) -> str:
        """保存文章
        
        Args:
            item: 文章数据
            config: 爬虫配置
            
        Returns:
            str: 保存结果
                'saved': 保存成功
                'filtered': 被过滤
                'duplicated': 重复文章
        """
        try:
            # 检查是否已存在
            source_url = item.get('source_url', item.get('url', ''))
            if not source_url:
                logger.warning(f"缺少URL: {item}")
                return 'filtered'
                
            if NewsArticle.objects.filter(source_url=source_url).exists():
                logger.info(f"文章已存在: {item['title']}")
                return 'duplicated'
                
            # 创建文章对象
            article_data = {
                'title': item['title'],
                'source_url': source_url,
                'content': item.get('content', ''),
                'summary': item.get('summary', item.get('description', '')),
                'author': item.get('author', ''),
                'source': item.get('source', config.name),
                'publish_time': item.get('publish_time', item.get('pub_time', timezone.now())),
                'crawler': config.id,
                'status': item.get('status', NewsArticle.Status.DRAFT)
            }
            
            # 使用序列化器保存
            serializer = NewsArticleCreateSerializer(data=article_data)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"保存文章成功: {item['title']}")
                return 'saved'
            else:
                logger.error(f"保存文章失败: {serializer.errors}")
                return 'filtered'
            
        except Exception as e:
            logger.error(f"保存文章失败: {str(e)}")
            raise

    def save_news_articles(self, source_name, items, stats, config=None):
        """保存新闻文章"""
        logger = logging.getLogger(__name__)
        logger.info(f"开始保存{len(items)}条新闻")

        for item in items:
            source_url = item.get('url')
            if not source_url:
                stats['filtered'] += 1
                logger.warning(f"source_url为空: {item}")
                continue

            try:
                # 检查重复
                if NewsArticle.objects.filter(source_url=source_url).exists():
                    stats['duplicated'] += 1
                    logger.info(f"文章已存在: {source_url}")
                    continue

                # 创建新闻文章
                article_data = {
                    'title': item.get('title'),
                    'source_url': source_url,
                    'content': item.get('content', ''),
                    'summary': item.get('description', ''),
                    'author': item.get('author', ''),
                    'source': item.get('source', source_name),
                    'publish_time': item.get('pub_time', timezone.now()),
                    'crawler': config.id if config else None,
                    'status': NewsArticle.Status.DRAFT,
                }

                logger.debug(f"准备保存文章: {article_data}")
                    
                serializer = NewsArticleCreateSerializer(data=article_data)
                if serializer.is_valid():
                    serializer.save()
                    stats['saved'] += 1
                    logger.info(f"成功保存文章: {source_url}")
                else:
                    stats['errors'] += 1
                    logger.error(f"保存文章失败: {serializer.errors}")
                    logger.error(f"文章数据: {article_data}")

            except Exception as e:
                stats['errors'] += 1
                logger.error(f"保存文章失败: {str(e)}", exc_info=True)
                logger.error(f"文章数据: {article_data}")

        logger.info(f"新闻保存完成，共处理{len(items)}条新闻，成功保存{stats['saved']}条，重复{stats['duplicated']}条，过滤{stats['filtered']}条，错误{stats['errors']}条")
        return stats