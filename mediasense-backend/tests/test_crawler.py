import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from unittest.mock import patch, Mock, MagicMock
from django.test import TestCase
from django.utils import timezone
from celery.result import AsyncResult
import uuid
import json
import environ
import feedparser

# 初始化环境变量
env = environ.Env()
environ.Env.read_env()

from crawler.models import CrawlerConfig, CrawlerTask
from crawler.services import CrawlerService
from crawler.crawlers.rss_crawler import RSSCrawler
from crawler.tasks import run_crawler, schedule_crawlers
from news.models import NewsArticle
from tests.factories import UserFactory, CrawlerConfigFactory, CrawlerTaskFactory

pytestmark = pytest.mark.django_db

class TestCrawlerService(TestCase):
    """爬虫服务单元测试"""
    
    databases = {'default'}
    
    def setUp(self):
        # 创建测试用的爬虫配置
        self.config = CrawlerConfig.objects.create(
            name='测试源',
            crawler_type=1,  # RSS类型
            source_url='https://test.com/rss',
            status=1,
            is_active=True,
            interval=60
        )
        
        # 创建测试用的爬虫任务
        self.task = CrawlerTask.objects.create(
            config=self.config,
            status=0  # pending状态
        )

    def test_get_crawler(self):
        """测试获取爬虫实例"""
        crawler = CrawlerService.get_crawler(self.config)
        self.assertIsInstance(crawler, RSSCrawler)

    @patch('feedparser.parse')
    @patch('requests.Session.get')
    def test_crawl_website(self, mock_get, mock_parse):
        """测试爬取网站"""
        # 清理数据库
        NewsArticle.objects.all().delete()
        CrawlerConfig.objects.all().delete()

        # 创建一个测试源
        source = CrawlerConfig.objects.create(
            name="测试源",
            description="测试源",
            source_url="http://test.com",
            crawler_type=1,
            headers={},
            interval=30,
            status=1
        )

        # Mock HTTP响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"></rss>'
        mock_get.return_value = mock_response

        # Mock RSS数据
        mock_entry = {
            'title': 'Test Title',
            'url': 'http://test.com/article/1',
            'content': 'Test Content',
            'description': 'Test Description',
            'author': 'Test Author',
            'source': '测试源',
            'pub_time': timezone.now(),
            'tags': ['test'],
            'images': ['http://test.com/image.jpg']
        }

        # Mock RSSCrawler的run方法
        with patch('crawler.crawlers.rss_crawler.RSSCrawler.run') as mock_run:
            mock_run.return_value = {
                'status': 'success',
                'message': '成功获取并解析RSS数据',
                'data': [mock_entry]
            }

            # 执行爬虫任务
            service = CrawlerService()
            result = service.crawl_website(source)

            # 验证结果
            self.assertEqual(result['status'], 'success')
            self.assertEqual(NewsArticle.objects.count(), 1)

            # 验证文章内容
            article = NewsArticle.objects.first()
            self.assertEqual(article.title, 'Test Title')
            self.assertEqual(article.source_url, 'http://test.com/article/1')
            self.assertEqual(article.content, 'Test Content')
            self.assertEqual(article.summary, 'Test Description')
            self.assertEqual(article.author, 'Test Author')
            self.assertEqual(article.source, '测试源')

    def test_clean_data(self):
        """测试数据清理功能"""
        test_data = {
            'title': '测试文章',
            'url': 'https://test.com/article/1',
            'description': '测试描述',
            'pub_time': timezone.now(),
            'source': '测试源'
        }
        
        cleaned_data = CrawlerService._clean_data(test_data)
        self.assertIsNotNone(cleaned_data)
        self.assertEqual(cleaned_data['title'], '测试文章')

    def test_invalid_data_cleaning(self):
        """测试无效数据的清理"""
        test_data = {
            'title': '',  # 空标题
            'url': 'invalid-url',  # 无效URL
            'description': None,  # 空描述
        }
        
        cleaned_data = CrawlerService._clean_data(test_data)
        self.assertIsNone(cleaned_data)

    def test_duplicate_article(self):
        """测试重复文章检测"""
        test_data = {
            'title': '测试文章',
            'url': 'https://test.com/article/1',
            'content': '测试内容',
            'description': '测试描述',
            'pub_time': timezone.now(),
            'source': '测试源'
        }
        
        # 第一次保存
        result1 = CrawlerService._save_article(test_data, self.config)
        self.assertEqual(result1, 'saved')
        
        # 尝试保存相同的文章
        result2 = CrawlerService._save_article(test_data, self.config)
        self.assertEqual(result2, 'duplicated') 